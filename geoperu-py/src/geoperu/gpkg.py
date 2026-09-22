"""Lector de GeoPackage con biblioteca estándar.

Un GeoPackage es una base SQLite con convenciones OGC, así que ``sqlite3``
alcanza para leerlo. La única parte no obvia es el blob de geometría, que
lleva un encabezado propio de GPKG antes del WKB estándar.

Referencia del encabezado (OGC GeoPackage 1.x, sección «BLOB format»):

    byte 0-1  magia, siempre b"GP"
    byte 2    versión del formato
    byte 3    banderas
    byte 4-7  srs_id (entero, en el orden que indican las banderas)
    ...       envelope opcional, de tamaño variable
    resto     geometría en WKB

Banderas del byte 3:
    bit 0     orden de bytes del encabezado (1 = little endian)
    bits 1-3  indicador de envelope: 0 = ninguno, 1 = xy (32 bytes),
              2 = xyz (48), 3 = xym (48), 4 = xyzm (64)
    bit 4     geometría vacía
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from .errores import ErrorGeoPackage, ErrorGeometria

#: Tamaño del envelope según el indicador de las banderas.
_TAMANO_ENVELOPE = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def desempacar_blob(blob: bytes) -> Tuple[int, Optional[bytes]]:
    """Separa un blob de geometría GPKG en ``(srs_id, wkb)``.

    Devuelve ``wkb = None`` cuando el blob marca geometría vacía.
    """
    if len(blob) < 8:
        raise ErrorGeometria(
            f"Blob de geometría GPKG demasiado corto: {len(blob)} bytes."
        )
    if blob[:2] != b"GP":
        raise ErrorGeometria(
            "El blob no lleva la magia 'GP' de GeoPackage; "
            f"empieza con {blob[:2]!r}."
        )

    banderas = blob[3]
    indicador = (banderas >> 1) & 0x07
    if indicador not in _TAMANO_ENVELOPE:
        raise ErrorGeometria(
            f"Indicador de envelope GPKG inválido: {indicador} (válidos 0-4)."
        )
    vacia = bool(banderas & 0x10)
    orden = "<" if banderas & 0x01 else ">"

    import struct

    srs_id = struct.unpack(orden + "i", blob[4:8])[0]
    inicio = 8 + _TAMANO_ENVELOPE[indicador]
    if vacia:
        return srs_id, None
    if inicio >= len(blob):
        raise ErrorGeometria(
            "El blob GPKG no contiene WKB después del encabezado."
        )
    return srs_id, blob[inicio:]


def tabla_de_rasgos(conexion: sqlite3.Connection) -> str:
    """Nombre de la primera tabla de rasgos declarada en ``gpkg_contents``."""
    try:
        filas = conexion.execute(
            "SELECT table_name FROM gpkg_contents WHERE data_type = 'features' "
            "ORDER BY table_name"
        ).fetchall()
    except sqlite3.DatabaseError as exc:
        raise ErrorGeoPackage(
            f"El archivo no parece un GeoPackage válido: {exc}"
        ) from exc
    if not filas:
        raise ErrorGeoPackage(
            "El GeoPackage no declara ninguna tabla de rasgos en gpkg_contents."
        )
    return filas[0][0]


def columna_de_geometria(conexion: sqlite3.Connection, tabla: str) -> str:
    fila = conexion.execute(
        "SELECT column_name FROM gpkg_geometry_columns WHERE table_name = ?",
        (tabla,),
    ).fetchone()
    if fila is None:
        raise ErrorGeoPackage(
            f"La tabla {tabla!r} no tiene columna de geometría registrada."
        )
    return fila[0]


def leer(ruta: str, tabla: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]], int]:
    """Lee un GeoPackage y devuelve ``(campos, filas, srs_id)``.

    Cada fila es un diccionario con los atributos más la clave ``__wkb__``
    con la geometría en WKB (o ``None`` si está vacía). Se devuelve el WKB
    crudo, sin convertirlo: quien consuma decide si lo pasa a
    ``QgsGeometry.fromWkb()``, a GeoJSON o a WKT, y así no se paga una
    conversión que quizá no haga falta.
    """
    conexion = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    try:
        nombre_tabla = tabla or tabla_de_rasgos(conexion)
        col_geom = columna_de_geometria(conexion, nombre_tabla)

        info = conexion.execute(f'PRAGMA table_info("{nombre_tabla}")').fetchall()
        if not info:
            raise ErrorGeoPackage(f"La tabla {nombre_tabla!r} no existe.")
        columnas = [c[1] for c in info]
        # 'fid' es la clave interna del GeoPackage, no un atributo del dato.
        campos = [c for c in columnas if c not in (col_geom, "fid")]

        srs_id = 4326
        fila_srs = conexion.execute(
            "SELECT srs_id FROM gpkg_contents WHERE table_name = ?", (nombre_tabla,)
        ).fetchone()
        if fila_srs and fila_srs[0] is not None:
            srs_id = int(fila_srs[0])

        seleccion = ", ".join(f'"{c}"' for c in campos + [col_geom])
        filas: List[Dict[str, Any]] = []
        for cruda in conexion.execute(f'SELECT {seleccion} FROM "{nombre_tabla}"'):
            registro: Dict[str, Any] = dict(zip(campos, cruda[:-1]))
            blob = cruda[-1]
            if blob is None:
                registro["__wkb__"] = None
            else:
                srs_geom, wkb = desempacar_blob(blob)
                registro["__wkb__"] = wkb
                if srs_geom > 0:
                    srs_id = srs_geom
            filas.append(registro)
        return campos, filas, srs_id
    finally:
        conexion.close()
