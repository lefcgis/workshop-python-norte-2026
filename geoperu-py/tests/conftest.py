"""Utilidades compartidas. Ninguna prueba de la suite por defecto usa la red.

Una prueba que dependa de un servidor externo falla los días que ese servidor
está lento, y una prueba que falla por motivos ajenos al código se acaba
ignorando — y con ella, toda la suite.
"""

import sqlite3
import struct

import pytest


def blob_gpkg(wkb: bytes, srs_id: int = 4326, con_envelope: bool = False,
              vacia: bool = False, little: bool = True) -> bytes:
    """Arma un blob de geometría GeoPackage alrededor de un WKB."""
    banderas = 0
    if little:
        banderas |= 0x01
    if con_envelope:
        banderas |= (1 << 1)          # indicador 1 = envelope xy, 32 bytes
    if vacia:
        banderas |= 0x10
    orden = "<" if little else ">"
    cabecera = b"GP" + bytes([0, banderas]) + struct.pack(orden + "i", srs_id)
    if con_envelope:
        cabecera += struct.pack(orden + "4d", 0.0, 1.0, 0.0, 1.0)
    return cabecera + (b"" if vacia else wkb)


def poligono_wkb(x0=0.0, y0=0.0, x1=1.0, y1=1.0) -> bytes:
    anillo = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    cuerpo = b"\x01" + struct.pack("<I", 3) + struct.pack("<I", 1)
    cuerpo += struct.pack("<I", len(anillo))
    cuerpo += b"".join(struct.pack("<dd", x, y) for x, y in anillo)
    return cuerpo


def crear_gpkg(ruta, filas, tabla="distritos", campos=("departamento", "provincia", "distrito"),
               srs_id=4326, con_envelope=False):
    """Crea un GeoPackage mínimo pero conforme, con sqlite3 a secas."""
    con = sqlite3.connect(str(ruta))
    con.execute(
        "CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT, "
        "identifier TEXT, description TEXT, last_change TEXT, "
        "min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER)"
    )
    con.execute(
        "CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT, "
        "geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT)"
    )
    columnas = ", ".join(f'"{c}" TEXT' for c in campos)
    con.execute(
        f'CREATE TABLE "{tabla}" (fid INTEGER PRIMARY KEY AUTOINCREMENT, '
        f'geom BLOB, {columnas})'
    )
    con.execute(
        "INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) "
        "VALUES (?, 'features', ?, ?)", (tabla, tabla, srs_id)
    )
    con.execute(
        "INSERT INTO gpkg_geometry_columns VALUES (?, 'geom', 'POLYGON', ?, 0, 0)",
        (tabla, srs_id),
    )
    marcadores = ", ".join("?" for _ in campos)
    for i, fila in enumerate(filas):
        geom = fila.get("geom", blob_gpkg(poligono_wkb(i, i, i + 1, i + 1),
                                          srs_id=srs_id, con_envelope=con_envelope))
        con.execute(
            f'INSERT INTO "{tabla}" (geom, {", ".join(chr(34)+c+chr(34) for c in campos)}) '
            f'VALUES (?, {marcadores})',
            [geom] + [fila.get(c) for c in campos],
        )
    con.commit()
    con.close()
    return ruta


@pytest.fixture
def gpkg_distritos(tmp_path):
    """GeoPackage con tres distritos, dos de ellos homónimos."""
    return crear_gpkg(
        tmp_path / "prueba.gpkg",
        [
            {"departamento": "AMAZONAS", "provincia": "CHACHAPOYAS", "distrito": "CHACHAPOYAS"},
            {"departamento": "AMAZONAS", "provincia": "LUYA", "distrito": "SAN JUAN"},
            {"departamento": "AMAZONAS", "provincia": "BONGARA", "distrito": "SAN JUAN"},
        ],
    )


@pytest.fixture
def catalogo_falso():
    """Diccionario de catálogo mínimo y válido."""
    return {
        "version": "2026.1",
        "generado_en_utc": "2026-01-01T00:00:00+00:00",
        "entradas": [
            {"departamento": "AMAZONAS", "provincia": None, "nivel": "departamento",
             "tipo": "complete", "url": "https://ejemplo.org/dep_amazonas.gpkg"},
            {"departamento": "AMAZONAS", "provincia": None, "nivel": "departamento",
             "tipo": "simplified", "url": "https://ejemplo.org/dep_amazonas_s.gpkg"},
            {"departamento": "CUSCO", "provincia": None, "nivel": "departamento",
             "tipo": "simplified", "url": "https://ejemplo.org/dep_cusco_s.gpkg"},
            {"departamento": "AMAZONAS", "provincia": "CHACHAPOYAS", "nivel": "provincia",
             "tipo": "simplified", "url": "https://ejemplo.org/prov_chachapoyas_s.gpkg"},
            {"departamento": "CUSCO", "provincia": "ANTA", "nivel": "provincia",
             "tipo": "simplified", "url": "https://ejemplo.org/prov_anta_s.gpkg"},
            {"departamento": None, "provincia": None, "nivel": "nacional",
             "tipo": "simplified", "url": "https://ejemplo.org/peru_s.gpkg"},
        ],
        "anp": [
            {"nombre": "MANU", "categoria": "PARQUE NACIONAL",
             "url": "https://ejemplo.org/anp_manu.gpkg"},
            {"nombre": "TAMBOPATA", "categoria": "RESERVA NACIONAL",
             "url": "https://ejemplo.org/anp_tambopata.gpkg"},
        ],
    }
