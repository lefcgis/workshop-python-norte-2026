"""Pruebas del lector WKB. Ninguna toca la red."""

import struct

import pytest

from geoperu.errores import ErrorGeometria
from geoperu.wkb import bbox_de_geojson, geojson_a_wkt, wkb_a_geojson, wkb_a_wkt


def punto_wkb(x, y, little=True, tipo=1):
    orden = "<" if little else ">"
    marca = b"\x01" if little else b"\x00"
    return marca + struct.pack(orden + "I", tipo) + struct.pack(orden + "dd", x, y)


def test_punto_little_endian():
    assert wkb_a_geojson(punto_wkb(-77.03, -12.11)) == {
        "type": "Point", "coordinates": [-77.03, -12.11]
    }


def test_punto_big_endian():
    # El orden de bytes se declara por geometría, no una vez por búfer.
    assert wkb_a_geojson(punto_wkb(-77.03, -12.11, little=False))["coordinates"] == [
        -77.03, -12.11
    ]


def test_punto_con_z_iso():
    cuerpo = b"\x01" + struct.pack("<I", 1001) + struct.pack("<ddd", 1.0, 2.0, 3.0)
    assert wkb_a_geojson(cuerpo)["coordinates"] == [1.0, 2.0, 3.0]


def test_punto_con_m_descarta_la_medida():
    # GeoJSON no representa M: se lee para no descuadrar el búfer y se descarta.
    cuerpo = b"\x01" + struct.pack("<I", 2001) + struct.pack("<ddd", 1.0, 2.0, 9.0)
    assert wkb_a_geojson(cuerpo)["coordinates"] == [1.0, 2.0]


def test_ewkb_con_srid_no_descuadra_las_coordenadas():
    # Regresión: la bandera 0x20000000 mete 4 bytes de SRID entre el tipo y
    # las coordenadas. Sin consumirlos, todo sale corrido.
    cuerpo = (
        b"\x01"
        + struct.pack("<I", 1 | 0x20000000)
        + struct.pack("<I", 4326)
        + struct.pack("<dd", -77.03, -12.11)
    )
    assert wkb_a_geojson(cuerpo)["coordinates"] == [-77.03, -12.11]


def test_poligono_con_anillo_interior():
    exterior = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]
    interior = [(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)]
    cuerpo = b"\x01" + struct.pack("<I", 3) + struct.pack("<I", 2)
    for anillo in (exterior, interior):
        cuerpo += struct.pack("<I", len(anillo))
        cuerpo += b"".join(struct.pack("<dd", x, y) for x, y in anillo)
    geom = wkb_a_geojson(cuerpo)
    assert geom["type"] == "Polygon"
    assert len(geom["coordinates"]) == 2
    assert geom["coordinates"][1][0] == [1.0, 1.0]


def test_multipunto_lee_el_orden_de_cada_parte():
    cuerpo = b"\x01" + struct.pack("<I", 4) + struct.pack("<I", 2)
    cuerpo += punto_wkb(1, 2, little=True)
    cuerpo += punto_wkb(3, 4, little=False)   # parte con orden distinto
    geom = wkb_a_geojson(cuerpo)
    assert geom == {"type": "MultiPoint", "coordinates": [[1.0, 2.0], [3.0, 4.0]]}


def test_coleccion_de_geometrias():
    cuerpo = b"\x01" + struct.pack("<I", 7) + struct.pack("<I", 2)
    cuerpo += punto_wkb(1, 2)
    cuerpo += b"\x01" + struct.pack("<I", 2) + struct.pack("<I", 2)
    cuerpo += struct.pack("<dd", 0, 0) + struct.pack("<dd", 1, 1)
    geom = wkb_a_geojson(cuerpo)
    assert geom["type"] == "GeometryCollection"
    assert [g["type"] for g in geom["geometries"]] == ["Point", "LineString"]


def test_wkb_truncado_da_error_claro():
    with pytest.raises(ErrorGeometria, match="truncado"):
        wkb_a_geojson(b"\x01" + struct.pack("<I", 1) + b"\x00\x00")


def test_orden_de_bytes_invalido():
    with pytest.raises(ErrorGeometria, match="Orden de bytes"):
        wkb_a_geojson(b"\x07" + struct.pack("<I", 1) + struct.pack("<dd", 0, 0))


def test_tipo_desconocido():
    with pytest.raises(ErrorGeometria, match="desconocido"):
        wkb_a_geojson(b"\x01" + struct.pack("<I", 42) + struct.pack("<dd", 0, 0))


def test_wkb_vacio():
    with pytest.raises(ErrorGeometria, match="vacío"):
        wkb_a_geojson(b"")


class TestWkt:
    def test_punto(self):
        assert geojson_a_wkt({"type": "Point", "coordinates": [-77.03, -12.11]}) == (
            "POINT (-77.03 -12.11)"
        )

    def test_poligono(self):
        geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        assert geojson_a_wkt(geom) == "POLYGON ((0 0, 1 0, 1 1, 0 0))"

    def test_marca_la_z(self):
        geom = {"type": "Point", "coordinates": [1.0, 2.0, 3.0]}
        assert geojson_a_wkt(geom) == "POINT Z (1 2 3)"

    def test_vacia(self):
        assert geojson_a_wkt({"type": "Polygon", "coordinates": []}) == "POLYGON EMPTY"

    def test_ida_y_vuelta_desde_wkb(self):
        assert wkb_a_wkt(punto_wkb(-77.03, -12.11)) == "POINT (-77.03 -12.11)"

    def test_sin_notacion_cientifica_en_grados(self):
        # Un WKT con 1e-05 lo rechazan varios servicios; .15g lo evita en el
        # rango de los grados decimales.
        texto = geojson_a_wkt({"type": "Point", "coordinates": [-77.0300000001, -12.11]})
        assert "e" not in texto.lower()


class TestBbox:
    def test_de_poligono(self):
        geom = {"type": "Polygon", "coordinates": [[[-77.05, -12.13], [-77.01, -12.09],
                                                    [-77.05, -12.13]]]}
        assert bbox_de_geojson(geom) == (-77.05, -12.13, -77.01, -12.09)

    def test_de_coleccion(self):
        geom = {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "Point", "coordinates": [0, 0]},
                {"type": "Point", "coordinates": [5, 7]},
            ],
        }
        assert bbox_de_geojson(geom) == (0, 0, 5, 7)

    def test_sin_coordenadas(self):
        with pytest.raises(ErrorGeometria):
            bbox_de_geojson({"type": "Point", "coordinates": []})
