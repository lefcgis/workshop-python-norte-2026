"""Pruebas de la API pública, con el transporte inyectado (sin red)."""

import pytest

import geoperu
from geoperu import descarga
from geoperu.errores import GeografiaNoEncontrada, UnidadAmbigua

from conftest import crear_gpkg


@pytest.fixture
def entorno(tmp_path, monkeypatch, catalogo_falso):
    """Catálogo falso + transporte que sirve GeoPackages sintéticos."""
    import json

    from geoperu import catalogo as modulo_catalogo

    monkeypatch.setenv("GEOPERU_CACHE", str(tmp_path / "cache"))

    ruta_catalogo = tmp_path / "catalogo.json"
    ruta_catalogo.write_text(json.dumps(catalogo_falso), encoding="utf-8")
    cat = modulo_catalogo.Catalogo.desde_dict(catalogo_falso)
    monkeypatch.setattr(modulo_catalogo, "_cache_catalogo", cat, raising=False)
    monkeypatch.setattr(modulo_catalogo, "cargar", lambda **k: cat)

    # Un GPKG con distritos y otro con el polígono disuelto.
    completo = crear_gpkg(
        tmp_path / "completo.gpkg",
        [
            {"departamento": "AMAZONAS", "provincia": "CHACHAPOYAS", "distrito": "CHACHAPOYAS"},
            {"departamento": "AMAZONAS", "provincia": "LUYA", "distrito": "SAN JUAN"},
            {"departamento": "AMAZONAS", "provincia": "BONGARA", "distrito": "SAN JUAN"},
        ],
    )
    disuelto = crear_gpkg(
        tmp_path / "disuelto.gpkg", [{"departamento": "AMAZONAS"}], campos=("departamento",)
    )
    cusco_disuelto = crear_gpkg(
        tmp_path / "cusco.gpkg", [{"departamento": "CUSCO"}], campos=("departamento",)
    )
    prov = crear_gpkg(
        tmp_path / "prov.gpkg", [{"provincia": "CHACHAPOYAS"}], campos=("provincia",)
    )

    cuerpos = {
        "dep_amazonas.gpkg": completo.read_bytes(),
        "dep_amazonas_s.gpkg": disuelto.read_bytes(),
        "dep_cusco_s.gpkg": cusco_disuelto.read_bytes(),
        "prov_chachapoyas_s.gpkg": prov.read_bytes(),
        "prov_anta_s.gpkg": prov.read_bytes(),
        "peru_s.gpkg": disuelto.read_bytes(),
        "anp_manu.gpkg": disuelto.read_bytes(),
    }
    pedidos = []

    def transporte(url, tiempo_limite):
        nombre = url.rsplit("/", 1)[-1]
        pedidos.append(nombre)
        if nombre not in cuerpos:
            import urllib.error
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return cuerpos[nombre]

    descarga.establecer_transporte(transporte)
    yield pedidos
    descarga.establecer_transporte(None)


class TestObtenerGeoPeru:
    def test_departamento_simplificado_es_un_solo_poligono(self, entorno):
        col = geoperu.obtener_geo_peru("AMAZONAS", nivel="dep", simplificado=True)
        assert len(col) == 1

    def test_departamento_completo_trae_los_distritos(self, entorno):
        col = geoperu.obtener_geo_peru("AMAZONAS", nivel="dep", simplificado=False)
        assert len(col) == 3
        assert "distrito" in col.campos

    def test_crs_es_4326(self, entorno):
        assert geoperu.obtener_geo_peru("AMAZONAS", nivel="dep").crs == "EPSG:4326"

    def test_registra_la_procedencia(self, entorno):
        col = geoperu.obtener_geo_peru("AMAZONAS", nivel="dep")
        assert len(col.procedencia) == 1
        p = col.procedencia[0]
        assert p.sha256 and p.bytes_archivo and p.version_catalogo == "2026.1"

    def test_varias_geografias_se_concatenan(self, entorno):
        col = geoperu.obtener_geo_peru(["AMAZONAS", "CUSCO"], nivel="dep", simplificado=True)
        assert len(col) == 2
        assert len(col.procedencia) == 2

    def test_la_cache_evita_la_segunda_descarga(self, entorno):
        geoperu.obtener_geo_peru("AMAZONAS", nivel="dep", simplificado=True)
        geoperu.obtener_geo_peru("AMAZONAS", nivel="dep", simplificado=True)
        assert entorno.count("dep_amazonas_s.gpkg") == 1

    def test_geografia_inexistente_sugiere(self, entorno):
        with pytest.raises(GeografiaNoEncontrada) as info:
            geoperu.obtener_geo_peru("AMAZONA", nivel="dep")
        assert "AMAZONAS" in info.value.sugerencias


class TestConveniencias:
    def test_obtener_distritos(self, entorno):
        col = geoperu.obtener_distritos("amazonas")
        assert len(col) == 3
        assert col.campos == ("departamento", "provincia", "distrito")

    def test_obtener_distrito_unico(self, entorno):
        r = geoperu.obtener_distrito("Chachapoyas", departamento="Amazonas")
        assert r["provincia"] == "CHACHAPOYAS"
        assert r.a_wkt().startswith("POLYGON")

    def test_distrito_homonimo_exige_desambiguar(self, entorno):
        # Nunca se devuelve "el primero": hay dos SAN JUAN en el fixture y 12
        # en el Perú real. Elegir uno al azar da un resultado incorrecto que
        # nadie detecta.
        with pytest.raises(UnidadAmbigua) as info:
            geoperu.obtener_distrito("SAN JUAN", departamento="Amazonas")
        assert len(info.value.coincidencias) == 2
        assert "desambiguar" in str(info.value)

    def test_homonimo_se_resuelve_con_la_provincia(self, entorno):
        r = geoperu.obtener_distrito("SAN JUAN", departamento="Amazonas", provincia="LUYA")
        assert r["provincia"] == "LUYA"

    def test_distrito_inexistente(self, entorno):
        with pytest.raises(GeografiaNoEncontrada):
            geoperu.obtener_distrito("NO EXISTE", departamento="Amazonas")

    def test_provincia_disuelta(self, entorno):
        col = geoperu.obtener_provincia("CHACHAPOYAS", departamento="AMAZONAS")
        assert len(col) == 1

    def test_provincia_con_departamento_equivocado(self, entorno):
        with pytest.raises(GeografiaNoEncontrada):
            geoperu.obtener_provincia("CHACHAPOYAS", departamento="CUSCO")

    def test_departamento_disuelto_o_en_distritos(self, entorno):
        assert len(geoperu.obtener_departamento("AMAZONAS", disuelto=True)) == 1
        assert len(geoperu.obtener_departamento("AMAZONAS", disuelto=False)) == 3


class TestAnp:
    def test_por_nombre(self, entorno):
        assert len(geoperu.obtener_anp_peru("MANU")) == 1

    def test_inexistente(self, entorno):
        with pytest.raises(GeografiaNoEncontrada):
            geoperu.obtener_anp_peru("PARQUE QUE NO EXISTE")


class TestSuperficiePublica:
    def test_el_submodulo_catalogo_no_queda_sombreado(self):
        # Regresión: una función llamada `catalogo` en __init__ dejaba
        # inalcanzable al submódulo `geoperu.catalogo`.
        import types
        assert isinstance(geoperu.catalogo, types.ModuleType)
        assert callable(geoperu.cargar_catalogo)

    def test_todo_lo_exportado_existe(self):
        faltantes = [n for n in geoperu.__all__ if not hasattr(geoperu, n)]
        assert faltantes == []

    def test_sin_dependencias_externas(self):
        """Ningún módulo del paquete importa algo fuera de la biblioteca estándar.

        Es la condición que permite incrustar el paquete en un plugin de QGIS.
        """
        import ast
        import pathlib
        import sys

        raiz = pathlib.Path(geoperu.__file__).parent
        permitidos = set(sys.stdlib_module_names) | {"geoperu"}
        externos = set()
        for archivo in raiz.rglob("*.py"):
            arbol = ast.parse(archivo.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Import):
                    for alias in nodo.names:
                        externos.add(alias.name.split(".")[0])
                elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
                    externos.add(nodo.module.split(".")[0])
        assert externos <= permitidos, f"dependencias externas: {externos - permitidos}"
