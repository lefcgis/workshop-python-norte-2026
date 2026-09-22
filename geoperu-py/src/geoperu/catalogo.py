"""Catálogo versionado de los conjuntos de datos disponibles.

El catálogo se congela dentro del paquete (``datos/catalogo_*.json``). Eso es
deliberado: los datos oficiales del INEI cambian poco y se revisan una vez al
año, mientras que depender en cada ejecución de un archivo remoto de terceros
haría que un cambio ajeno rompiera a todos los consumidores sin aviso.

``refrescar()`` regenera el catálogo desde el origen y es lo que ejecuta la
revisión anual.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .descarga import normalizar_url, traer
from .errores import ErrorCatalogo, GeografiaNoEncontrada
from .normalizacion import normalizar, sugerir

URL_METADATOS_LIMITES = (
    "https://raw.githubusercontent.com/PaulESantos/perugeopkg/master/metadata_peru_gpkg.csv"
)
URL_METADATOS_ANP = (
    "https://raw.githubusercontent.com/PaulESantos/perugeopkg/master/metadata_anp.csv"
)

#: Equivalencias de nivel. Se aceptan los códigos de ``geoperu`` en R
#: (``all``/``dep``/``prov``) y los nombres del catálogo, para que el código
#: escrito contra el paquete de R siga leyéndose igual.
NIVELES = {
    "all": "nacional",
    "nacional": "nacional",
    "dep": "departamento",
    "departamento": "departamento",
    "prov": "provincia",
    "provincia": "provincia",
}

_COLUMNAS_LIMITES = ("dep_name", "prov_name", "level", "type", "download_path")
_COLUMNAS_ANP = ("anp_nombre", "anp_categoria", "download_path")


@dataclass(frozen=True)
class Entrada:
    """Una fila del catálogo: un archivo descargable."""

    departamento: Optional[str]
    provincia: Optional[str]
    nivel: str
    tipo: str          # "complete" o "simplified"
    url: str

    @property
    def simplificado(self) -> bool:
        return self.tipo == "simplified"

    @property
    def nombre_archivo(self) -> str:
        return self.url.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class EntradaAnp:
    nombre: str
    categoria: str
    url: str

    @property
    def nombre_archivo(self) -> str:
        return self.url.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class Catalogo:
    version: str
    generado_en_utc: str
    entradas: Tuple[Entrada, ...]
    anp: Tuple[EntradaAnp, ...]

    # -- consultas -------------------------------------------------------

    def departamentos(self) -> Tuple[str, ...]:
        return tuple(sorted({e.departamento for e in self.entradas
                             if e.nivel == "departamento" and e.departamento}))

    def provincias(self, departamento: Optional[str] = None) -> Tuple[str, ...]:
        objetivo = normalizar(departamento)
        return tuple(sorted({
            e.provincia for e in self.entradas
            if e.nivel == "provincia" and e.provincia
            and (objetivo is None or normalizar(e.departamento) == objetivo)
        }))

    def buscar(
        self,
        geografia: Sequence[str] | str = "all",
        nivel: str = "all",
        simplificado: bool = True,
    ) -> Tuple[Entrada, ...]:
        """Entradas que coinciden con la geografía, el nivel y el tipo.

        ``geografia="all"`` devuelve todas las unidades del nivel pedido.
        """
        clave_nivel = NIVELES.get(str(nivel).strip().lower())
        if clave_nivel is None:
            raise ErrorCatalogo(
                f"Nivel {nivel!r} desconocido. Use uno de: "
                + ", ".join(sorted(set(NIVELES))) + "."
            )

        tipo = "simplified" if simplificado else "complete"
        del_nivel = [e for e in self.entradas if e.nivel == clave_nivel and e.tipo == tipo]

        nombres = [geografia] if isinstance(geografia, str) else list(geografia)
        pedidos = {normalizar(n) for n in nombres}

        if "ALL" in pedidos or clave_nivel == "nacional":
            return tuple(del_nivel)

        campo = "provincia" if clave_nivel == "provincia" else "departamento"
        elegidas = tuple(
            e for e in del_nivel if normalizar(getattr(e, campo)) in pedidos
        )
        if not elegidas:
            disponibles = [getattr(e, campo) for e in del_nivel if getattr(e, campo)]
            raise GeografiaNoEncontrada(
                ", ".join(nombres), clave_nivel, sugerir(nombres[0], disponibles)
            )
        return elegidas

    def buscar_anp(self, nombre: str) -> Tuple[EntradaAnp, ...]:
        """Áreas naturales protegidas: coincidencia exacta y, si no, parcial."""
        objetivo = normalizar(nombre) or ""
        exactas = tuple(a for a in self.anp if normalizar(a.nombre) == objetivo)
        if exactas:
            return exactas
        parciales = tuple(a for a in self.anp if objetivo in (normalizar(a.nombre) or ""))
        if not parciales:
            raise GeografiaNoEncontrada(
                nombre, "anp", sugerir(nombre, [a.nombre for a in self.anp])
            )
        return parciales

    # -- serialización ---------------------------------------------------

    def a_dict(self) -> Dict:
        return {
            "version": self.version,
            "generado_en_utc": self.generado_en_utc,
            "origen": {
                "metadatos_limites": URL_METADATOS_LIMITES,
                "metadatos_anp": URL_METADATOS_ANP,
            },
            "entradas": [
                {
                    "departamento": e.departamento,
                    "provincia": e.provincia,
                    "nivel": e.nivel,
                    "tipo": e.tipo,
                    "url": e.url,
                }
                for e in self.entradas
            ],
            "anp": [
                {"nombre": a.nombre, "categoria": a.categoria, "url": a.url}
                for a in self.anp
            ],
        }

    @classmethod
    def desde_dict(cls, datos: Dict) -> "Catalogo":
        try:
            entradas = tuple(
                Entrada(
                    departamento=e.get("departamento"),
                    provincia=e.get("provincia"),
                    nivel=e["nivel"],
                    tipo=e["tipo"],
                    url=e["url"],
                )
                for e in datos["entradas"]
            )
            anp = tuple(
                EntradaAnp(nombre=a["nombre"], categoria=a.get("categoria", ""), url=a["url"])
                for a in datos.get("anp", ())
            )
            return cls(
                version=datos["version"],
                generado_en_utc=datos["generado_en_utc"],
                entradas=entradas,
                anp=anp,
            )
        except (KeyError, TypeError) as exc:
            raise ErrorCatalogo(f"Catálogo con formato inesperado: {exc}") from exc


# -- carga y refresco ----------------------------------------------------

_cache_catalogo: Optional[Catalogo] = None


def _archivo_congelado() -> str:
    """Nombre del catálogo congelado más reciente incluido en el paquete."""
    nombres = sorted(
        r.name for r in resources.files("geoperu.datos").iterdir()
        if r.name.startswith("catalogo_") and r.name.endswith(".json")
    )
    if not nombres:
        raise ErrorCatalogo(
            "El paquete no incluye ningún catálogo congelado en geoperu/datos/."
        )
    return nombres[-1]


def cargar(ruta: Optional[Path] = None, recargar: bool = False) -> Catalogo:
    """Carga el catálogo congelado del paquete, o uno desde ``ruta``."""
    global _cache_catalogo
    if ruta is not None:
        return Catalogo.desde_dict(json.loads(Path(ruta).read_text(encoding="utf-8")))
    if _cache_catalogo is None or recargar:
        texto = (
            resources.files("geoperu.datos")
            .joinpath(_archivo_congelado())
            .read_text(encoding="utf-8")
        )
        _cache_catalogo = Catalogo.desde_dict(json.loads(texto))
    return _cache_catalogo


def _leer_csv(url: str, columnas: Sequence[str]) -> List[Dict[str, str]]:
    crudo = traer(url, tiempo_limite=60).decode("utf-8-sig")
    lector = csv.DictReader(io.StringIO(crudo))
    filas = list(lector)
    if not filas:
        raise ErrorCatalogo(f"El archivo de metadatos está vacío: {url}")
    faltantes = [c for c in columnas if c not in (lector.fieldnames or ())]
    if faltantes:
        raise ErrorCatalogo(
            f"El origen cambió de formato: a {url} le faltan las columnas "
            f"{', '.join(faltantes)}. Revise el origen antes de regenerar el catálogo."
        )
    return filas


def _texto_o_nulo(valor: Optional[str]) -> Optional[str]:
    # El origen marca «sin valor» con la cadena literal "nill".
    if valor is None:
        return None
    limpio = valor.strip()
    if not limpio or limpio.lower() in ("nill", "nil", "na", "none", "all"):
        return None
    return limpio


def refrescar(version: Optional[str] = None) -> Catalogo:
    """Regenera el catálogo desde el origen. Requiere red.

    Es lo que corre la revisión anual: descarga los metadatos, valida su
    formato y devuelve un catálogo nuevo listo para guardarse con
    ``guardar()``.
    """
    limites = _leer_csv(URL_METADATOS_LIMITES, _COLUMNAS_LIMITES)
    try:
        anps = _leer_csv(URL_METADATOS_ANP, _COLUMNAS_ANP)
    except ErrorCatalogo:
        anps = []  # el catálogo de ANP es opcional: su ausencia no invalida los límites

    entradas = tuple(
        Entrada(
            departamento=_texto_o_nulo(f.get("dep_name")),
            provincia=_texto_o_nulo(f.get("prov_name")),
            nivel=(f.get("level") or "").strip().lower(),
            tipo=(f.get("type") or "").strip().lower(),
            url=normalizar_url((f.get("download_path") or "").strip()),
        )
        for f in limites
    )
    entradas = tuple(e for e in entradas if e.url and e.nivel and e.tipo)
    if not entradas:
        raise ErrorCatalogo("El origen no produjo ninguna entrada utilizable.")

    anp = tuple(
        EntradaAnp(
            nombre=(a.get("anp_nombre") or "").strip(),
            categoria=(a.get("anp_categoria") or "").strip(),
            url=normalizar_url((a.get("download_path") or "").strip()),
        )
        for a in anps
    )
    anp = tuple(a for a in anp if a.url and a.nombre)

    ahora = datetime.now(timezone.utc)
    return Catalogo(
        version=version or f"{ahora.year}.1",
        generado_en_utc=ahora.isoformat(timespec="seconds"),
        entradas=entradas,
        anp=anp,
    )


def guardar(catalogo: Catalogo, ruta: Path) -> Path:
    """Escribe un catálogo a disco en JSON ordenado y legible."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(catalogo.a_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ruta
