import json

import pytest

from geoperu.catalogo import Catalogo, guardar
from geoperu.errores import ErrorCatalogo, GeografiaNoEncontrada


@pytest.fixture
def cat(catalogo_falso):
    return Catalogo.desde_dict(catalogo_falso)


class TestConsultas:
    def test_departamentos(self, cat):
        assert cat.departamentos() == ("AMAZONAS", "CUSCO")

    def test_provincias_de_un_departamento(self, cat):
        assert cat.provincias("cusco") == ("ANTA",)

    def test_todas_las_provincias(self, cat):
        assert cat.provincias() == ("ANTA", "CHACHAPOYAS")

    def test_busca_por_nombre_sin_importar_formato(self, cat):
        for forma in ("AMAZONAS", "Amazonas", "amazonas", " amazonas "):
            entradas = cat.buscar(forma, nivel="dep", simplificado=True)
            assert len(entradas) == 1

    def test_simplificado_y_completo_son_archivos_distintos(self, cat):
        simple = cat.buscar("AMAZONAS", nivel="dep", simplificado=True)[0]
        completo = cat.buscar("AMAZONAS", nivel="dep", simplificado=False)[0]
        assert simple.url != completo.url
        assert simple.simplificado and not completo.simplificado

    def test_acepta_los_codigos_de_r_y_los_nombres_en_espanol(self, cat):
        # El código escrito contra geoperu en R debe seguir leyéndose igual.
        assert cat.buscar("AMAZONAS", nivel="dep") == cat.buscar("AMAZONAS", nivel="departamento")
        assert cat.buscar("all", nivel="all") == cat.buscar("all", nivel="nacional")

    def test_all_devuelve_todo_el_nivel(self, cat):
        assert len(cat.buscar("all", nivel="dep", simplificado=True)) == 2

    def test_lista_de_geografias(self, cat):
        entradas = cat.buscar(["AMAZONAS", "CUSCO"], nivel="dep", simplificado=True)
        assert len(entradas) == 2

    def test_nivel_provincia_filtra_por_provincia(self, cat):
        entradas = cat.buscar("ANTA", nivel="prov", simplificado=True)
        assert entradas[0].provincia == "ANTA"
        assert entradas[0].departamento == "CUSCO"

    def test_nombre_inexistente_sugiere(self, cat):
        with pytest.raises(GeografiaNoEncontrada) as info:
            cat.buscar("AMAZONA", nivel="dep", simplificado=True)
        assert "AMAZONAS" in info.value.sugerencias

    def test_nivel_invalido(self, cat):
        with pytest.raises(ErrorCatalogo, match="Nivel"):
            cat.buscar("AMAZONAS", nivel="distrito")

    def test_nombre_de_archivo_desde_la_url(self, cat):
        entrada = cat.buscar("AMAZONAS", nivel="dep", simplificado=False)[0]
        assert entrada.nombre_archivo == "dep_amazonas.gpkg"


class TestAnp:
    def test_coincidencia_exacta(self, cat):
        assert cat.buscar_anp("manu")[0].categoria == "PARQUE NACIONAL"

    def test_coincidencia_parcial(self, cat):
        assert cat.buscar_anp("TAMBO")[0].nombre == "TAMBOPATA"

    def test_sin_coincidencia(self, cat):
        with pytest.raises(GeografiaNoEncontrada):
            cat.buscar_anp("PARQUE INEXISTENTE")


class TestSerializacion:
    def test_ida_y_vuelta(self, cat):
        assert Catalogo.desde_dict(cat.a_dict()) == cat

    def test_guardar_y_cargar(self, cat, tmp_path):
        ruta = guardar(cat, tmp_path / "c.json")
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert datos["version"] == "2026.1"
        assert len(datos["entradas"]) == 6

    def test_formato_inesperado(self):
        with pytest.raises(ErrorCatalogo, match="formato inesperado"):
            Catalogo.desde_dict({"version": "1", "generado_en_utc": "x"})


class TestCatalogoEmpaquetado:
    """El catálogo congelado que viaja dentro del paquete."""

    def test_carga_y_cubre_todo_el_pais(self):
        from geoperu import catalogo as modulo
        real = modulo.cargar()
        assert len(real.departamentos()) == 25
        assert len(real.provincias()) == 196

    def test_cada_departamento_tiene_ambos_tipos(self):
        from geoperu import catalogo as modulo
        real = modulo.cargar()
        for dep in real.departamentos():
            assert real.buscar(dep, nivel="dep", simplificado=True)
            assert real.buscar(dep, nivel="dep", simplificado=False)

    def test_todas_las_urls_apuntan_al_host_de_contenido_crudo(self):
        # Normalizadas al generar el catálogo: la forma github.com/.../raw/
        # responde con una redirección que algunos entornos bloquean.
        from geoperu import catalogo as modulo
        real = modulo.cargar()
        assert all(e.url.startswith("https://raw.githubusercontent.com/")
                   for e in real.entradas)
