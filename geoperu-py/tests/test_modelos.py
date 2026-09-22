import pytest

from geoperu.errores import ErrorGeometria
from geoperu.modelos import ColeccionEspacial, Procedencia, Rasgo, unir

from conftest import poligono_wkb


def rasgo(dep="AMAZONAS", prov="LUYA", dist="SAN JUAN", i=0):
    return Rasgo(
        {"departamento": dep, "provincia": prov, "distrito": dist},
        poligono_wkb(i, i, i + 1, i + 1),
    )


@pytest.fixture
def coleccion():
    return ColeccionEspacial(
        rasgos=(
            rasgo("AMAZONAS", "CHACHAPOYAS", "CHACHAPOYAS", 0),
            rasgo("AMAZONAS", "LUYA", "SAN JUAN", 1),
            rasgo("AMAZONAS", "BONGARA", "SAN JUAN", 2),
        ),
        campos=("departamento", "provincia", "distrito"),
    )


class TestRasgo:
    def test_acceso_a_atributos(self):
        r = rasgo()
        assert r["distrito"] == "SAN JUAN"
        assert r.get("inexistente", "defecto") == "defecto"

    def test_geometria_y_wkt(self):
        r = rasgo()
        assert r.geometria()["type"] == "Polygon"
        assert r.a_wkt().startswith("POLYGON ((")

    def test_bbox(self):
        assert rasgo(i=0).bbox() == (0.0, 0.0, 1.0, 1.0)

    def test_sin_geometria(self):
        with pytest.raises(ErrorGeometria, match="no tiene geometría"):
            Rasgo({"a": 1}, None).geometria()


class TestColeccion:
    def test_protocolo_de_secuencia(self, coleccion):
        assert len(coleccion) == 3
        assert coleccion[0]["provincia"] == "CHACHAPOYAS"
        assert len(list(coleccion)) == 3
        assert bool(coleccion)

    def test_coleccion_vacia_es_falsa(self):
        assert not ColeccionEspacial(rasgos=(), campos=())

    def test_filtrar_normaliza_los_nombres(self, coleccion):
        # "chachapoyas", "Chachapoyas" y "CHACHAPOYAS" deben dar lo mismo.
        for forma in ("chachapoyas", "Chachapoyas", "CHACHAPOYAS"):
            assert len(coleccion.filtrar(distrito=forma)) == 1

    def test_filtrar_por_varios_campos_desambigua(self, coleccion):
        # Hay dos distritos "SAN JUAN": solo la provincia los separa.
        assert len(coleccion.filtrar(distrito="SAN JUAN")) == 2
        assert len(coleccion.filtrar(distrito="SAN JUAN", provincia="LUYA")) == 1

    def test_filtrar_ignora_criterios_nulos(self, coleccion):
        assert len(coleccion.filtrar(distrito="SAN JUAN", provincia=None)) == 2

    def test_filtrar_devuelve_una_coleccion(self, coleccion):
        assert isinstance(coleccion.filtrar(provincia="LUYA"), ColeccionEspacial)

    def test_valores_unicos_ordenados(self, coleccion):
        assert coleccion.valores("provincia") == ("BONGARA", "CHACHAPOYAS", "LUYA")
        assert coleccion.valores("distrito") == ("CHACHAPOYAS", "SAN JUAN")

    def test_bbox_abarca_todos_los_rasgos(self, coleccion):
        assert coleccion.bbox() == (0.0, 0.0, 3.0, 3.0)

    def test_bbox_sin_geometrias(self):
        vacia = ColeccionEspacial((Rasgo({"a": 1}, None),), ("a",))
        with pytest.raises(ErrorGeometria):
            vacia.bbox()

    def test_geojson_valido(self, coleccion):
        gj = coleccion.a_geojson()
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) == 3
        assert gj["features"][0]["properties"]["distrito"] == "CHACHAPOYAS"
        assert "EPSG::4326" in gj["crs"]["properties"]["name"]

    def test_geojson_omite_los_rasgos_sin_geometria(self):
        mezcla = ColeccionEspacial(
            (rasgo(i=0), Rasgo({"departamento": "X"}, None)), ("departamento",)
        )
        assert len(mezcla.a_geojson()["features"]) == 1


class TestUnir:
    def test_concatena_y_acumula_procedencia(self):
        a = ColeccionEspacial((rasgo(i=0),), ("departamento",),
                              procedencia=(Procedencia("u1", "2026.1"),))
        b = ColeccionEspacial((rasgo(i=1),), ("provincia",),
                              procedencia=(Procedencia("u2", "2026.1"),))
        junta = unir([a, b])
        assert len(junta) == 2
        assert junta.campos == ("departamento", "provincia")
        assert [p.url for p in junta.procedencia] == ["u1", "u2"]

    def test_sin_colecciones(self):
        assert len(unir([])) == 0

    def test_no_duplica_campos(self):
        a = ColeccionEspacial((rasgo(),), ("departamento", "provincia"))
        b = ColeccionEspacial((rasgo(),), ("provincia", "distrito"))
        assert unir([a, b]).campos == ("departamento", "provincia", "distrito")


class TestProcedencia:
    def test_serializa_lo_necesario_para_un_manifiesto(self):
        p = Procedencia("https://ejemplo.org/x.gpkg", "2026.1", sha256="abc",
                        bytes_archivo=10, descargado_en_utc="2026-01-01T00:00:00+00:00")
        d = p.a_dict()
        assert set(d) == {"url", "version_catalogo", "sha256", "bytes_archivo",
                          "descargado_en_utc", "desde_cache"}
        assert d["sha256"] == "abc"
