import sqlite3

import pytest

from geoperu import gpkg
from geoperu.errores import ErrorGeoPackage, ErrorGeometria
from geoperu.wkb import wkb_a_geojson

from conftest import blob_gpkg, crear_gpkg, poligono_wkb


class TestDesempacarBlob:
    def test_sin_envelope(self):
        srs, wkb = gpkg.desempacar_blob(blob_gpkg(poligono_wkb()))
        assert srs == 4326
        assert wkb_a_geojson(wkb)["type"] == "Polygon"

    def test_con_envelope_salta_los_32_bytes(self):
        # Si no se salta el envelope, el WKB empieza en el byte equivocado y
        # la geometría sale ilegible o, peor, legible y errónea.
        srs, wkb = gpkg.desempacar_blob(blob_gpkg(poligono_wkb(), con_envelope=True))
        assert wkb_a_geojson(wkb)["coordinates"][0][0] == [0.0, 0.0]

    def test_big_endian_en_el_encabezado(self):
        srs, wkb = gpkg.desempacar_blob(blob_gpkg(poligono_wkb(), srs_id=32718, little=False))
        assert srs == 32718

    def test_geometria_vacia_devuelve_none(self):
        srs, wkb = gpkg.desempacar_blob(blob_gpkg(b"", vacia=True))
        assert wkb is None

    def test_sin_magia_gp(self):
        with pytest.raises(ErrorGeometria, match="magia"):
            gpkg.desempacar_blob(b"XX" + b"\x00" * 10)

    def test_demasiado_corto(self):
        with pytest.raises(ErrorGeometria, match="corto"):
            gpkg.desempacar_blob(b"GP\x00\x01")

    def test_indicador_de_envelope_invalido(self):
        malo = bytearray(blob_gpkg(poligono_wkb()))
        malo[3] = 0x01 | (5 << 1)      # 5 no es un indicador válido
        with pytest.raises(ErrorGeometria, match="envelope"):
            gpkg.desempacar_blob(bytes(malo))


class TestLeer:
    def test_campos_filas_y_crs(self, gpkg_distritos):
        campos, filas, srs = gpkg.leer(str(gpkg_distritos))
        assert campos == ["departamento", "provincia", "distrito"]
        assert len(filas) == 3
        assert srs == 4326

    def test_excluye_el_fid_interno(self, gpkg_distritos):
        # 'fid' es la clave del GeoPackage, no un atributo del dato.
        campos, _, _ = gpkg.leer(str(gpkg_distritos))
        assert "fid" not in campos

    def test_entrega_wkb_crudo(self, gpkg_distritos):
        _, filas, _ = gpkg.leer(str(gpkg_distritos))
        assert isinstance(filas[0]["__wkb__"], bytes)
        assert wkb_a_geojson(filas[0]["__wkb__"])["type"] == "Polygon"

    def test_geometria_nula(self, tmp_path):
        ruta = crear_gpkg(tmp_path / "nula.gpkg", [{"departamento": "X", "provincia": None,
                                                    "distrito": None, "geom": None}])
        _, filas, _ = gpkg.leer(str(ruta))
        assert filas[0]["__wkb__"] is None

    def test_respeta_un_crs_no_4326(self, tmp_path):
        ruta = crear_gpkg(tmp_path / "utm.gpkg",
                          [{"departamento": "X", "provincia": "Y", "distrito": "Z"}],
                          srs_id=32718)
        _, _, srs = gpkg.leer(str(ruta))
        assert srs == 32718

    def test_archivo_que_no_es_geopackage(self, tmp_path):
        falso = tmp_path / "falso.gpkg"
        falso.write_bytes(b"no soy una base de datos")
        with pytest.raises(ErrorGeoPackage, match="GeoPackage válido"):
            gpkg.leer(str(falso))

    def test_sqlite_sin_tabla_de_rasgos(self, tmp_path):
        ruta = tmp_path / "vacio.gpkg"
        con = sqlite3.connect(str(ruta))
        con.execute("CREATE TABLE gpkg_contents (table_name TEXT, data_type TEXT)")
        con.commit()
        con.close()
        with pytest.raises(ErrorGeoPackage, match="ninguna tabla de rasgos"):
            gpkg.leer(str(ruta))

    def test_abre_en_solo_lectura(self, gpkg_distritos):
        # Se abre con mode=ro: leer datos de referencia nunca debe poder
        # modificar el archivo en caché.
        antes = gpkg_distritos.stat().st_mtime_ns
        gpkg.leer(str(gpkg_distritos))
        assert gpkg_distritos.stat().st_mtime_ns == antes
