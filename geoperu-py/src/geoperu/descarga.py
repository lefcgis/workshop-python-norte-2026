"""Descarga de archivos con caché en disco, reintentos y huella SHA-256.

Usa ``urllib`` de la biblioteca estándar. Quien integre esto en QGIS puede
inyectar su propio transporte (``QgsBlockingNetworkRequest``) con
``establecer_transporte()`` para respetar el proxy configurado por el usuario
—en redes institucionales, sin proxy no hay salida a internet.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Tuple

from .errores import ErrorDescarga

AGENTE = "geoperu-py/0.1.0 (+https://github.com/lefcgis/geoperu-py)"

REINTENTOS = 3
PAUSA_INICIAL_S = 0.5
TIEMPO_LIMITE_S = 120

#: Códigos que vale la pena reintentar. Un 404 o un 403 no se reintentan:
#: son respuestas definitivas y reintentar solo retrasa el diagnóstico.
CODIGOS_REINTENTABLES = frozenset({408, 425, 429, 500, 502, 503, 504})

#: Transporte inyectable. Recibe ``(url, tiempo_limite)`` y devuelve bytes.
_transporte: Optional[Callable[[str, int], bytes]] = None


def establecer_transporte(funcion: Optional[Callable[[str, int], bytes]]) -> None:
    """Reemplaza el transporte HTTP. ``None`` restaura ``urllib``."""
    global _transporte
    _transporte = funcion


def directorio_cache() -> Path:
    """Directorio de caché, configurable con la variable ``GEOPERU_CACHE``."""
    desde_entorno = os.environ.get("GEOPERU_CACHE")
    if desde_entorno:
        base = Path(desde_entorno)
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "geoperu"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches" / "geoperu"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "geoperu"
    base.mkdir(parents=True, exist_ok=True)
    return base


def normalizar_url(url: str) -> str:
    """Convierte una URL de GitHub de tipo ``blob``/``raw`` a ``raw.githubusercontent``.

    El catálogo de origen publica rutas ``github.com/<u>/<r>/raw/<ref>/<ruta>``,
    que responden con una redirección. Apuntar directo al host de contenido
    crudo ahorra ese salto y funciona en entornos donde la redirección se
    bloquea.

    >>> normalizar_url("https://github.com/a/b/raw/master/geo/x.gpkg")
    'https://raw.githubusercontent.com/a/b/master/geo/x.gpkg'
    >>> normalizar_url("https://ejemplo.org/x.gpkg")
    'https://ejemplo.org/x.gpkg'
    """
    for marca in ("/raw/", "/blob/"):
        prefijo = "https://github.com/"
        if url.startswith(prefijo) and marca in url:
            resto = url[len(prefijo):]
            izquierda, _, derecha = resto.partition(marca)
            return f"https://raw.githubusercontent.com/{izquierda}/{derecha}"
    return url


def _traer_con_urllib(url: str, tiempo_limite: int) -> bytes:
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(peticion, timeout=tiempo_limite) as respuesta:
        return respuesta.read()


def traer(url: str, tiempo_limite: int = TIEMPO_LIMITE_S, reintentos: int = REINTENTOS) -> bytes:
    """Descarga una URL a memoria, con reintentos y retroceso exponencial."""
    url = normalizar_url(url)
    transporte = _transporte or _traer_con_urllib
    pausa = PAUSA_INICIAL_S
    ultimo: Optional[Exception] = None

    for intento in range(1, reintentos + 1):
        try:
            contenido = transporte(url, tiempo_limite)
            if not contenido:
                raise ErrorDescarga(f"El servidor devolvió un archivo vacío: {url}")
            return contenido
        except urllib.error.HTTPError as exc:
            ultimo = exc
            if exc.code not in CODIGOS_REINTENTABLES:
                raise ErrorDescarga(
                    f"HTTP {exc.code} al descargar {url}. "
                    "El recurso no existe o el acceso está denegado; no se reintenta."
                ) from exc
            espera = _segundos_de_retry_after(exc) or pausa
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            ultimo = exc
            espera = pausa
        except ErrorDescarga as exc:
            ultimo = exc
            espera = pausa

        if intento < reintentos:
            time.sleep(espera)
            pausa *= 2

    raise ErrorDescarga(
        f"No se pudo descargar {url} tras {reintentos} intentos. Último error: {ultimo}"
    ) from ultimo


def _segundos_de_retry_after(exc: urllib.error.HTTPError) -> Optional[float]:
    """Respeta la cabecera ``Retry-After`` cuando el servidor la envía."""
    valor = exc.headers.get("Retry-After") if exc.headers else None
    if not valor:
        return None
    try:
        return max(0.0, float(valor))
    except (TypeError, ValueError):
        return None


def descargar_a_cache(
    url: str,
    nombre: Optional[str] = None,
    forzar: bool = False,
    tiempo_limite: int = TIEMPO_LIMITE_S,
) -> Tuple[Path, dict]:
    """Descarga ``url`` a la caché y devuelve ``(ruta, metadatos)``.

    Si el archivo ya está en caché no se vuelve a pedir, salvo ``forzar=True``.
    La escritura es atómica: se baja a un temporal y se renombra al final, de
    modo que una descarga interrumpida no deja un archivo truncado en la caché
    que luego se lea como si estuviera completo.
    """
    url = normalizar_url(url)
    destino = directorio_cache() / (nombre or url.rsplit("/", 1)[-1])

    if destino.exists() and destino.stat().st_size > 0 and not forzar:
        datos = destino.read_bytes()
        return destino, {
            "url": url,
            "sha256": hashlib.sha256(datos).hexdigest(),
            "bytes_archivo": len(datos),
            "descargado_en_utc": datetime.fromtimestamp(
                destino.stat().st_mtime, tz=timezone.utc
            ).isoformat(timespec="seconds"),
            "desde_cache": True,
        }

    contenido = traer(url, tiempo_limite=tiempo_limite)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destino.parent, delete=False) as temporal:
        temporal.write(contenido)
        parcial = Path(temporal.name)
    shutil.move(str(parcial), str(destino))

    return destino, {
        "url": url,
        "sha256": hashlib.sha256(contenido).hexdigest(),
        "bytes_archivo": len(contenido),
        "descargado_en_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "desde_cache": False,
    }


def limpiar_cache() -> int:
    """Borra la caché. Devuelve cuántos archivos se eliminaron."""
    cache = directorio_cache()
    borrados = 0
    for hijo in cache.iterdir():
        if hijo.is_file():
            hijo.unlink()
            borrados += 1
    return borrados
