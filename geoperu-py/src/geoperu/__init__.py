"""geoperu-py — límites administrativos y áreas protegidas del Perú.

Puerto a Python del paquete R `geoperu <https://github.com/PaulESantos/geoperu>`_
de Paul E. Santos Andrade. Entrega los mismos datos oficiales (INEI para
límites administrativos, SERNANP para áreas naturales protegidas) **sin
dependencias externas**: solo la biblioteca estándar.

Esa restricción es el punto del paquete. Permite incrustarlo dentro de un
plugin de QGIS, o usarlo en un servidor sin GDAL, sin pedirle a nadie un
``pip install``.

Uso típico::

    import geoperu

    # Los 84 distritos de Amazonas, con geometría completa
    distritos = geoperu.obtener_distritos("Amazonas")

    # El polígono de un distrito, ya desambiguado
    rasgo = geoperu.obtener_distrito("Chachapoyas", departamento="Amazonas")
    wkt = rasgo.a_wkt()

    # El polígono provincial disuelto
    provincia = geoperu.obtener_provincia("Chachapoyas", departamento="Amazonas")

Los niveles aceptan tanto los códigos del paquete de R (``all``, ``dep``,
``prov``) como sus nombres en español (``nacional``, ``departamento``,
``provincia``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from . import catalogo as _catalogo
from . import descarga as _descarga
from . import gpkg as _gpkg
from .errores import (
    ErrorCatalogo,
    ErrorDescarga,
    ErrorGeometria,
    ErrorGeoPackage,
    ErrorGeoperu,
    GeografiaNoEncontrada,
    UnidadAmbigua,
)
from .modelos import ColeccionEspacial, Procedencia, Rasgo, unir
from .normalizacion import DEPARTAMENTOS, normalizar, sugerir
from .wkb import bbox_de_geojson, geojson_a_wkt, wkb_a_geojson, wkb_a_wkt

__version__ = "0.1.0"

__all__ = [
    "obtener_geo_peru",
    "obtener_anp_peru",
    "obtener_distritos",
    "obtener_distrito",
    "obtener_provincia",
    "obtener_departamento",
    "cargar_catalogo",
    "refrescar_catalogo",
    "ColeccionEspacial",
    "Rasgo",
    "Procedencia",
    "DEPARTAMENTOS",
    "normalizar",
    "sugerir",
    "wkb_a_geojson",
    "wkb_a_wkt",
    "geojson_a_wkt",
    "bbox_de_geojson",
    "unir",
    "establecer_transporte",
    "directorio_cache",
    "limpiar_cache",
    "ErrorGeoperu",
    "ErrorCatalogo",
    "ErrorDescarga",
    "ErrorGeoPackage",
    "ErrorGeometria",
    "GeografiaNoEncontrada",
    "UnidadAmbigua",
    "__version__",
]

# Reexportados para que integrar el paquete en QGIS no exija importar submódulos.
establecer_transporte = _descarga.establecer_transporte
directorio_cache = _descarga.directorio_cache
limpiar_cache = _descarga.limpiar_cache


def cargar_catalogo(ruta: Optional[Path] = None, recargar: bool = False) -> _catalogo.Catalogo:
    """Catálogo de datos disponibles (congelado dentro del paquete).

    Se llama ``cargar_catalogo`` y no ``catalogo`` a propósito: ``geoperu.catalogo``
    es el submódulo, y una función con ese nombre lo dejaría inalcanzable.
    """
    return _catalogo.cargar(ruta=ruta, recargar=recargar)


def refrescar_catalogo(version: Optional[str] = None) -> _catalogo.Catalogo:
    """Regenera el catálogo desde el origen. Requiere red.

    Es la operación de la revisión anual; no hace falta para el uso normal.
    """
    return _catalogo.refrescar(version=version)


def _coleccion(entradas: Sequence[_catalogo.Entrada], forzar: bool = False) -> ColeccionEspacial:
    """Descarga las entradas, las lee y arma una colección con su procedencia."""
    partes = []
    for entrada in entradas:
        ruta, meta = _descarga.descargar_a_cache(
            entrada.url, nombre=entrada.nombre_archivo, forzar=forzar
        )
        campos, filas, srs_id = _gpkg.leer(str(ruta))
        rasgos = tuple(
            Rasgo(
                atributos={k: v for k, v in fila.items() if k != "__wkb__"},
                wkb=fila["__wkb__"],
            )
            for fila in filas
        )
        partes.append(
            ColeccionEspacial(
                rasgos=rasgos,
                campos=tuple(campos),
                crs=f"EPSG:{srs_id}",
                procedencia=(
                    Procedencia(
                        url=meta["url"],
                        version_catalogo=cargar_catalogo().version,
                        sha256=meta["sha256"],
                        bytes_archivo=meta["bytes_archivo"],
                        descargado_en_utc=meta["descargado_en_utc"],
                        desde_cache=meta["desde_cache"],
                    ),
                ),
            )
        )
    return unir(partes)


def obtener_geo_peru(
    geografia: Sequence[str] | str = "all",
    nivel: str = "all",
    simplificado: bool = True,
    forzar_descarga: bool = False,
) -> ColeccionEspacial:
    """Descarga datos espaciales del Perú en EPSG:4326.

    Equivale a ``geoperu::get_geo_peru()`` en R.

    :param geografia: nombre de la unidad, lista de nombres, o ``"all"``.
    :param nivel: ``"all"``/``"nacional"``, ``"dep"``/``"departamento"`` o
        ``"prov"``/``"provincia"``.
    :param simplificado: ``True`` devuelve el polígono **disuelto** de la
        unidad (una fila). ``False`` devuelve los **distritos** que la
        componen, con los campos ``departamento``, ``provincia``, ``distrito``
        y ``capital``. Esta asimetría es del origen de datos, no del paquete,
        y es justamente lo que evita tener que disolver geometrías.
    :param forzar_descarga: ignora la caché y vuelve a bajar los archivos.
    """
    entradas = cargar_catalogo().buscar(geografia=geografia, nivel=nivel, simplificado=simplificado)
    return _coleccion(entradas, forzar=forzar_descarga)


def obtener_anp_peru(anp: str, forzar_descarga: bool = False) -> ColeccionEspacial:
    """Descarga áreas naturales protegidas (SERNANP) por nombre.

    Equivale a ``geoperu::get_anp_peru()``. Busca coincidencia exacta y, si no
    la hay, parcial.
    """
    entradas = cargar_catalogo().buscar_anp(anp)
    partes = []
    for entrada in entradas:
        ruta, meta = _descarga.descargar_a_cache(
            entrada.url, nombre=entrada.nombre_archivo, forzar=forzar_descarga
        )
        campos, filas, srs_id = _gpkg.leer(str(ruta))
        rasgos = tuple(
            Rasgo({k: v for k, v in f.items() if k != "__wkb__"}, f["__wkb__"])
            for f in filas
        )
        partes.append(ColeccionEspacial(
            rasgos, tuple(campos), f"EPSG:{srs_id}",
            (Procedencia(meta["url"], cargar_catalogo().version, meta["sha256"],
                         meta["bytes_archivo"], meta["descargado_en_utc"],
                         meta["desde_cache"]),),
        ))
    return unir(partes)


def obtener_distritos(departamento: str, forzar_descarga: bool = False) -> ColeccionEspacial:
    """Todos los distritos de un departamento, con geometría completa.

    Es la consulta que necesita un flujo de ocurrencias de biodiversidad:
    devuelve los campos ``departamento``, ``provincia``, ``distrito`` y
    ``capital``.
    """
    return obtener_geo_peru(
        geografia=departamento, nivel="departamento",
        simplificado=False, forzar_descarga=forzar_descarga,
    )


def obtener_departamento(
    departamento: str, disuelto: bool = True, forzar_descarga: bool = False
) -> ColeccionEspacial:
    """Polígono de un departamento: disuelto, o sus distritos."""
    return obtener_geo_peru(
        geografia=departamento, nivel="departamento",
        simplificado=disuelto, forzar_descarga=forzar_descarga,
    )


def obtener_provincia(
    provincia: str,
    departamento: Optional[str] = None,
    disuelta: bool = True,
    forzar_descarga: bool = False,
) -> ColeccionEspacial:
    """Polígono de una provincia: disuelta, o sus distritos.

    ``departamento`` desambigua provincias homónimas, que existen: hay más de
    una provincia «Huancavelica» o «Cusco» según el nivel que se compare.
    """
    entradas = cargar_catalogo().buscar(
        geografia=provincia, nivel="provincia", simplificado=disuelta
    )
    if departamento is not None:
        objetivo = normalizar(departamento)
        filtradas = tuple(e for e in entradas if normalizar(e.departamento) == objetivo)
        if not filtradas:
            disponibles = sorted({e.departamento for e in entradas if e.departamento})
            raise GeografiaNoEncontrada(
                f"{provincia} ({departamento})", "provincia", tuple(disponibles)
            )
        entradas = filtradas
    elif len(entradas) > 1:
        raise UnidadAmbigua(
            provincia, [(e.departamento or "?", e.provincia or "?") for e in entradas]
        )
    return _coleccion(entradas, forzar=forzar_descarga)


def obtener_distrito(
    distrito: str,
    departamento: Optional[str] = None,
    provincia: Optional[str] = None,
    forzar_descarga: bool = False,
) -> Rasgo:
    """Un distrito, ya desambiguado, como :class:`Rasgo`.

    Si se omite ``departamento`` hay que revisar los 25 departamentos, lo que
    implica descargarlos todos la primera vez (unos 40 MB, luego en caché).
    Indicar el departamento evita ese costo.

    :raises UnidadAmbigua: si el nombre corresponde a más de un distrito. No
        se devuelve «el primero»: hay 12 distritos llamados «San Juan» y
        elegir uno al azar da un resultado incorrecto que nadie detecta.
    :raises GeografiaNoEncontrada: si no hay ninguna coincidencia.
    """
    departamentos = [departamento] if departamento else list(DEPARTAMENTOS)
    coincidencias = []
    for dep in departamentos:
        try:
            coleccion = obtener_distritos(dep, forzar_descarga=forzar_descarga)
        except (GeografiaNoEncontrada, ErrorDescarga):
            continue
        elegidos = coleccion.filtrar(distrito=distrito, provincia=provincia)
        coincidencias.extend(elegidos.rasgos)

    if not coincidencias:
        # Sugerencias tomadas del primer departamento consultado: pedir los 25
        # solo para redactar un mensaje de error no vale la descarga.
        candidatos: list = []
        try:
            candidatos = list(obtener_distritos(departamentos[0]).valores("distrito"))
        except ErrorGeoperu:
            pass
        raise GeografiaNoEncontrada(distrito, "distrito", sugerir(distrito, candidatos))

    if len(coincidencias) > 1:
        raise UnidadAmbigua(
            distrito,
            [
                (r.get("departamento", "?"), r.get("provincia", "?"), r.get("distrito", "?"))
                for r in coincidencias
            ],
        )
    return coincidencias[0]
