"""Lector de WKB (Well-Known Binary) en biblioteca estándar.

Convierte geometrías WKB a diccionarios GeoJSON y a WKT. Reemplaza a GDAL y
a ``shapely``: no hay dependencias externas, que es la condición para poder
incrustar este paquete dentro de un plugin de QGIS.

Soporta WKB estándar (OGC), la variante ISO con sufijos Z/M/ZM, y las
banderas de alto orden de EWKB (PostGIS), que aparecen en archivos generados
por distintas herramientas.
"""

from __future__ import annotations

import struct
from typing import Any, Dict, List, Tuple

from .errores import ErrorGeometria

_TIPOS = {
    1: "Point",
    2: "LineString",
    3: "Polygon",
    4: "MultiPoint",
    5: "MultiLineString",
    6: "MultiPolygon",
    7: "GeometryCollection",
}

# Banderas de alto orden de EWKB.
_EWKB_Z = 0x80000000
_EWKB_M = 0x40000000
_EWKB_SRID = 0x20000000


class _Lector:
    """Cursor sobre el búfer WKB.

    Cada geometría anidada trae su propio indicador de orden de bytes, así que
    el orden se resuelve por geometría y no una sola vez para todo el búfer.
    """

    __slots__ = ("datos", "pos")

    def __init__(self, datos: bytes, pos: int = 0):
        self.datos = datos
        self.pos = pos

    def _tomar(self, n: int) -> bytes:
        fin = self.pos + n
        if fin > len(self.datos):
            raise ErrorGeometria(
                f"WKB truncado: se pidieron {n} bytes en la posición {self.pos} "
                f"de un búfer de {len(self.datos)}."
            )
        trozo = self.datos[self.pos:fin]
        self.pos = fin
        return trozo

    def orden(self) -> str:
        marca = self._tomar(1)[0]
        if marca == 1:
            return "<"
        if marca == 0:
            return ">"
        raise ErrorGeometria(
            f"Orden de bytes WKB inválido: {marca} (se esperaba 0 o 1)."
        )

    def entero(self, orden: str) -> int:
        return struct.unpack(orden + "I", self._tomar(4))[0]

    def dobles(self, orden: str, cuantos: int) -> Tuple[float, ...]:
        return struct.unpack(orden + f"{cuantos}d", self._tomar(8 * cuantos))


def _decodificar_tipo(bruto: int) -> Tuple[int, bool, bool, bool]:
    """Separa el tipo base de las banderas Z/M/SRID, en ISO y en EWKB.

    Devuelve ``(tipo, tiene_z, tiene_m, trae_srid)``. ``trae_srid`` importa
    porque en EWKB el SRID va entre el tipo y las coordenadas: si no se
    consume, todas las coordenadas salen corridas cuatro bytes.
    """
    tiene_z = bool(bruto & _EWKB_Z)
    tiene_m = bool(bruto & _EWKB_M)
    trae_srid = bool(bruto & _EWKB_SRID)
    tipo = bruto & 0x0FFFFFFF if (tiene_z or tiene_m or trae_srid) else bruto

    # Variante ISO: 1000 = Z, 2000 = M, 3000 = ZM.
    if tipo >= 3000:
        tipo, tiene_z, tiene_m = tipo - 3000, True, True
    elif tipo >= 2000:
        tipo, tiene_m = tipo - 2000, True
    elif tipo >= 1000:
        tipo, tiene_z = tipo - 1000, True

    if tipo not in _TIPOS:
        raise ErrorGeometria(f"Tipo de geometría WKB desconocido: {tipo}.")
    return tipo, tiene_z, tiene_m, trae_srid


def _leer_punto(lec: _Lector, orden: str, z: bool, m: bool) -> List[float]:
    # GeoJSON no representa la medida M, así que se lee y se descarta.
    valores = lec.dobles(orden, 2 + int(z) + int(m))
    return [valores[0], valores[1], valores[2]] if z else [valores[0], valores[1]]


def _leer_puntos(lec: _Lector, orden: str, z: bool, m: bool) -> List[List[float]]:
    cuantos = lec.entero(orden)
    return [_leer_punto(lec, orden, z, m) for _ in range(cuantos)]


def _leer_geometria(lec: _Lector) -> Dict[str, Any]:
    orden = lec.orden()
    tipo, z, m, trae_srid = _decodificar_tipo(lec.entero(orden))
    if trae_srid:
        lec.entero(orden)  # SRID de EWKB: se consume y se descarta
    nombre = _TIPOS[tipo]

    if tipo == 1:
        punto = _leer_punto(lec, orden, z, m)
        # Un punto vacío se codifica con NaN en algunas herramientas.
        if punto[0] != punto[0] or punto[1] != punto[1]:
            return {"type": "Point", "coordinates": []}
        return {"type": "Point", "coordinates": punto}

    if tipo == 2:
        return {"type": "LineString", "coordinates": _leer_puntos(lec, orden, z, m)}

    if tipo == 3:
        anillos = [_leer_puntos(lec, orden, z, m) for _ in range(lec.entero(orden))]
        return {"type": "Polygon", "coordinates": anillos}

    if tipo in (4, 5, 6):
        cuantas = lec.entero(orden)
        partes = [_leer_geometria(lec) for _ in range(cuantas)]
        return {"type": nombre, "coordinates": [p["coordinates"] for p in partes]}

    # GeometryCollection
    cuantas = lec.entero(orden)
    return {
        "type": "GeometryCollection",
        "geometries": [_leer_geometria(lec) for _ in range(cuantas)],
    }


def wkb_a_geojson(wkb: bytes) -> Dict[str, Any]:
    """Convierte un búfer WKB en un diccionario de geometría GeoJSON.

    >>> import struct
    >>> punto = b"\\x01" + struct.pack("<I", 1) + struct.pack("<dd", -77.03, -12.11)
    >>> wkb_a_geojson(punto)
    {'type': 'Point', 'coordinates': [-77.03, -12.11]}
    """
    if not wkb:
        raise ErrorGeometria("El búfer WKB está vacío.")
    return _leer_geometria(_Lector(wkb))


def _num(valor: float) -> str:
    # 15 cifras significativas: suficiente para grados decimales y sin la
    # cola de ruido que produce repr() en coma flotante.
    return f"{valor:.15g}"


def _coords_a_wkt(coords: Any, profundidad: int) -> str:
    if profundidad == 0:
        return " ".join(_num(c) for c in coords)
    return "(" + ", ".join(_coords_a_wkt(c, profundidad - 1) for c in coords) + ")"


def geojson_a_wkt(geometria: Dict[str, Any]) -> str:
    """Convierte una geometría GeoJSON en WKT.

    >>> geojson_a_wkt({"type": "Point", "coordinates": [-77.03, -12.11]})
    'POINT (-77.03 -12.11)'
    """
    tipo = geometria.get("type")
    if tipo == "GeometryCollection":
        partes = ", ".join(geojson_a_wkt(g) for g in geometria.get("geometries", []))
        return f"GEOMETRYCOLLECTION ({partes})" if partes else "GEOMETRYCOLLECTION EMPTY"

    coords = geometria.get("coordinates")
    if not coords:
        return f"{tipo.upper()} EMPTY" if tipo else "GEOMETRYCOLLECTION EMPTY"

    profundidad = {
        "Point": 0, "LineString": 1, "Polygon": 2,
        "MultiPoint": 1, "MultiLineString": 2, "MultiPolygon": 3,
    }.get(tipo)
    if profundidad is None:
        raise ErrorGeometria(f"Tipo GeoJSON no soportado: {tipo!r}.")

    sufijo_z = " Z" if _tiene_z(coords, profundidad) else ""
    cuerpo = _coords_a_wkt(coords, profundidad)
    nombre = {
        "Point": "POINT", "LineString": "LINESTRING", "Polygon": "POLYGON",
        "MultiPoint": "MULTIPOINT", "MultiLineString": "MULTILINESTRING",
        "MultiPolygon": "MULTIPOLYGON",
    }[tipo]
    return f"{nombre}{sufijo_z} {cuerpo}" if profundidad else f"{nombre}{sufijo_z} ({cuerpo})"


def _tiene_z(coords: Any, profundidad: int) -> bool:
    actual = coords
    for _ in range(profundidad):
        if not actual:
            return False
        actual = actual[0]
    return isinstance(actual, (list, tuple)) and len(actual) > 2


def wkb_a_wkt(wkb: bytes) -> str:
    """Atajo: WKB -> WKT."""
    return geojson_a_wkt(wkb_a_geojson(wkb))


def bbox_de_geojson(geometria: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Caja delimitadora (xmin, ymin, xmax, ymax) de una geometría GeoJSON."""
    xs: List[float] = []
    ys: List[float] = []

    def recorrer(nodo: Any) -> None:
        if isinstance(nodo, dict):
            if nodo.get("type") == "GeometryCollection":
                for g in nodo.get("geometries", []):
                    recorrer(g)
            else:
                recorrer(nodo.get("coordinates"))
        elif isinstance(nodo, (list, tuple)):
            if nodo and isinstance(nodo[0], (int, float)):
                xs.append(float(nodo[0]))
                ys.append(float(nodo[1]))
            else:
                for hijo in nodo:
                    recorrer(hijo)

    recorrer(geometria)
    if not xs:
        raise ErrorGeometria("La geometría no tiene coordenadas; no hay caja delimitadora.")
    return (min(xs), min(ys), max(xs), max(ys))
