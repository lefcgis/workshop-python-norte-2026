import urllib.error

import pytest

from geoperu import descarga
from geoperu.errores import ErrorDescarga


@pytest.fixture(autouse=True)
def cache_aislada(tmp_path, monkeypatch):
    monkeypatch.setenv("GEOPERU_CACHE", str(tmp_path / "cache"))
    yield
    descarga.establecer_transporte(None)


class TestNormalizarUrl:
    def test_forma_raw_de_github(self):
        assert descarga.normalizar_url(
            "https://github.com/a/b/raw/master/geo/x.gpkg"
        ) == "https://raw.githubusercontent.com/a/b/master/geo/x.gpkg"

    def test_forma_blob_de_github(self):
        assert descarga.normalizar_url(
            "https://github.com/a/b/blob/main/x.csv"
        ) == "https://raw.githubusercontent.com/a/b/main/x.csv"

    def test_deja_intactas_las_demas(self):
        for url in ("https://ejemplo.org/x.gpkg",
                    "https://raw.githubusercontent.com/a/b/master/x.gpkg"):
            assert descarga.normalizar_url(url) == url


class TestTraer:
    def test_transporte_inyectado(self):
        descarga.establecer_transporte(lambda url, t: b"contenido")
        assert descarga.traer("https://ejemplo.org/x") == b"contenido"

    def test_reintenta_y_termina_bien(self):
        intentos = []

        def transporte(url, t):
            intentos.append(url)
            if len(intentos) < 3:
                raise urllib.error.URLError("red caída")
            return b"ok"

        descarga.establecer_transporte(transporte)
        assert descarga.traer("https://ejemplo.org/x") == b"ok"
        assert len(intentos) == 3

    def test_no_reintenta_un_404(self):
        # Un 404 es definitivo: reintentar solo retrasa el diagnóstico.
        intentos = []

        def transporte(url, t):
            intentos.append(url)
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        descarga.establecer_transporte(transporte)
        with pytest.raises(ErrorDescarga, match="no se reintenta"):
            descarga.traer("https://ejemplo.org/x")
        assert len(intentos) == 1

    def test_si_reintenta_un_503(self):
        intentos = []

        def transporte(url, t):
            intentos.append(url)
            raise urllib.error.HTTPError(url, 503, "Unavailable", {}, None)

        descarga.establecer_transporte(transporte)
        with pytest.raises(ErrorDescarga, match="3 intentos"):
            descarga.traer("https://ejemplo.org/x")
        assert len(intentos) == 3

    def test_archivo_vacio_es_error(self):
        descarga.establecer_transporte(lambda url, t: b"")
        with pytest.raises(ErrorDescarga):
            descarga.traer("https://ejemplo.org/x")


class TestCache:
    def test_descarga_una_vez_y_luego_sirve_de_cache(self):
        llamadas = []
        descarga.establecer_transporte(
            lambda url, t: (llamadas.append(url), b"datos")[1]
        )
        ruta1, meta1 = descarga.descargar_a_cache("https://ejemplo.org/x.gpkg")
        ruta2, meta2 = descarga.descargar_a_cache("https://ejemplo.org/x.gpkg")
        assert ruta1 == ruta2
        assert len(llamadas) == 1
        assert meta1["desde_cache"] is False
        assert meta2["desde_cache"] is True

    def test_forzar_vuelve_a_descargar(self):
        llamadas = []
        descarga.establecer_transporte(
            lambda url, t: (llamadas.append(url), b"datos")[1]
        )
        descarga.descargar_a_cache("https://ejemplo.org/x.gpkg")
        descarga.descargar_a_cache("https://ejemplo.org/x.gpkg", forzar=True)
        assert len(llamadas) == 2

    def test_calcula_la_huella(self):
        import hashlib
        descarga.establecer_transporte(lambda url, t: b"datos")
        _, meta = descarga.descargar_a_cache("https://ejemplo.org/x.gpkg")
        assert meta["sha256"] == hashlib.sha256(b"datos").hexdigest()
        assert meta["bytes_archivo"] == 5

    def test_la_huella_es_igual_desde_la_cache(self):
        descarga.establecer_transporte(lambda url, t: b"datos")
        _, primera = descarga.descargar_a_cache("https://ejemplo.org/x.gpkg")
        _, segunda = descarga.descargar_a_cache("https://ejemplo.org/x.gpkg")
        assert primera["sha256"] == segunda["sha256"]

    def test_una_descarga_fallida_no_deja_archivo_a_medias(self):
        # La escritura es atómica: si falla, no queda un archivo truncado que
        # la siguiente ejecución lea como si estuviera completo.
        def transporte(url, t):
            raise urllib.error.URLError("cortado")

        descarga.establecer_transporte(transporte)
        with pytest.raises(ErrorDescarga):
            descarga.descargar_a_cache("https://ejemplo.org/x.gpkg")
        assert not (descarga.directorio_cache() / "x.gpkg").exists()

    def test_limpiar(self):
        descarga.establecer_transporte(lambda url, t: b"datos")
        descarga.descargar_a_cache("https://ejemplo.org/a.gpkg")
        descarga.descargar_a_cache("https://ejemplo.org/b.gpkg")
        assert descarga.limpiar_cache() == 2
        assert descarga.limpiar_cache() == 0
