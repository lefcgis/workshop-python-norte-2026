"""Estructuras de datos devueltas por el paquete.

Son deliberadamente simples —dataclasses y diccionarios GeoJSON— para que
funcionen igual dentro de QGIS, en un cuaderno o en un script sin QGIS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple

from .errores import ErrorGeometria
from .normalizacion import normalizar
from .wkb import bbox_de_geojson, geojson_a_wkt, wkb_a_geojson


@dataclass(frozen=True)
class Procedencia:
    """De dónde salió un conjunto de datos.

    No es adorno: quien consuma esta biblioteca para armar un expediente
    técnico necesita poder declarar el origen, la fecha y la huella del
    archivo que produjo sus cifras.
    """

    url: str
    version_catalogo: str
    sha256: Optional[str] = None
    bytes_archivo: Optional[int] = None
    descargado_en_utc: Optional[str] = None
    desde_cache: bool = False

    def a_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "version_catalogo": self.version_catalogo,
            "sha256": self.sha256,
            "bytes_archivo": self.bytes_archivo,
            "descargado_en_utc": self.descargado_en_utc,
            "desde_cache": self.desde_cache,
        }


@dataclass(frozen=True)
class Rasgo:
    """Una unidad espacial: sus atributos y su geometría."""

    atributos: Mapping[str, Any]
    wkb: Optional[bytes]

    def geometria(self) -> Dict[str, Any]:
        """Geometría como diccionario GeoJSON."""
        if self.wkb is None:
            raise ErrorGeometria("El rasgo no tiene geometría.")
        return wkb_a_geojson(self.wkb)

    def a_wkt(self) -> str:
        """Geometría en WKT. Útil para APIs que piden texto, como GBIF."""
        return geojson_a_wkt(self.geometria())

    def bbox(self) -> Tuple[float, float, float, float]:
        """Caja delimitadora ``(xmin, ymin, xmax, ymax)``."""
        return bbox_de_geojson(self.geometria())

    def __getitem__(self, clave: str) -> Any:
        return self.atributos[clave]

    def get(self, clave: str, defecto: Any = None) -> Any:
        return self.atributos.get(clave, defecto)


@dataclass(frozen=True)
class ColeccionEspacial:
    """Conjunto de rasgos con un CRS y su procedencia."""

    rasgos: Tuple[Rasgo, ...]
    campos: Tuple[str, ...]
    crs: str = "EPSG:4326"
    procedencia: Tuple[Procedencia, ...] = field(default_factory=tuple)

    def __len__(self) -> int:
        return len(self.rasgos)

    def __iter__(self) -> Iterator[Rasgo]:
        return iter(self.rasgos)

    def __getitem__(self, indice: int) -> Rasgo:
        return self.rasgos[indice]

    def __bool__(self) -> bool:
        return bool(self.rasgos)

    def filtrar(self, **criterios: str) -> "ColeccionEspacial":
        """Filtra por atributos, comparando nombres normalizados.

        >>> # coleccion.filtrar(distrito="miraflores", provincia="Lima")
        """
        objetivos = {c: normalizar(v) for c, v in criterios.items() if v is not None}
        seleccion = tuple(
            r for r in self.rasgos
            if all(normalizar(r.get(c)) == v for c, v in objetivos.items())
        )
        return ColeccionEspacial(seleccion, self.campos, self.crs, self.procedencia)

    def valores(self, campo: str) -> Tuple[str, ...]:
        """Valores únicos de un campo, en orden alfabético."""
        return tuple(sorted({r.get(campo) for r in self.rasgos if r.get(campo)}))

    def bbox(self) -> Tuple[float, float, float, float]:
        cajas = [r.bbox() for r in self.rasgos if r.wkb is not None]
        if not cajas:
            raise ErrorGeometria("La colección no tiene geometrías.")
        return (
            min(c[0] for c in cajas), min(c[1] for c in cajas),
            max(c[2] for c in cajas), max(c[3] for c in cajas),
        )

    def a_geojson(self) -> Dict[str, Any]:
        """FeatureCollection GeoJSON, lista para escribir a disco."""
        rasgos = []
        for r in self.rasgos:
            if r.wkb is None:
                continue
            rasgos.append({
                "type": "Feature",
                "properties": dict(r.atributos),
                "geometry": r.geometria(),
            })
        nombre_crs = f"urn:ogc:def:crs:{self.crs.replace(':', '::')}"
        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": nombre_crs}},
            "features": rasgos,
        }

    def __repr__(self) -> str:
        return (
            f"ColeccionEspacial({len(self.rasgos)} rasgos, crs={self.crs!r}, "
            f"campos={self.campos!r})"
        )


def unir(colecciones: Sequence[ColeccionEspacial]) -> ColeccionEspacial:
    """Concatena colecciones conservando toda la procedencia."""
    utiles = [c for c in colecciones if c is not None]
    if not utiles:
        return ColeccionEspacial(rasgos=(), campos=())
    campos: Tuple[str, ...] = ()
    for c in utiles:
        for campo in c.campos:
            if campo not in campos:
                campos += (campo,)
    rasgos = tuple(r for c in utiles for r in c.rasgos)
    procedencia = tuple(p for c in utiles for p in c.procedencia)
    return ColeccionEspacial(rasgos, campos, utiles[0].crs, procedencia)
