"""Pruebas contra los servidores reales.

Quedan FUERA de la suite por defecto y fuera de integración continua: se
corren con ``pytest -m red``. Su propósito es distinto al del resto —
confirmar que el origen de datos sigue vigente y con el formato esperado— y
conviene ejecutarlas antes de cada versión y en la revisión anual.
"""

import pytest

import geoperu

pytestmark = pytest.mark.red


def test_el_origen_sigue_publicando_el_catalogo():
    cat = geoperu.refrescar_catalogo()
    assert len(cat.departamentos()) == 25, "el INEI cambió la división departamental"
    assert len(cat.provincias()) == 196, "cambió el número de provincias"
    assert cat.anp, "el catálogo de áreas protegidas quedó vacío"


def test_el_catalogo_congelado_coincide_con_el_origen():
    """Si esto falla, toca correr la actualización anual."""
    congelado = geoperu.cargar_catalogo()
    vivo = geoperu.refrescar_catalogo()
    assert {e.url for e in congelado.entradas} == {e.url for e in vivo.entradas}


def test_descarga_y_lectura_de_punta_a_punta():
    distritos = geoperu.obtener_distritos("Amazonas")
    assert len(distritos) == 84
    assert distritos.campos == ("departamento", "provincia", "distrito", "capital")
    assert distritos.crs == "EPSG:4326"

    xmin, ymin, xmax, ymax = distritos.bbox()
    # Amazonas está en el norte del Perú: comprobación gruesa de que las
    # coordenadas no salieron invertidas ni desplazadas.
    assert -79 < xmin < -76 and -8 < ymin < -2


def test_un_distrito_concreto():
    rasgo = geoperu.obtener_distrito("Chachapoyas", departamento="Amazonas")
    assert rasgo["provincia"] == "CHACHAPOYAS"
    assert rasgo.a_wkt().startswith(("POLYGON", "MULTIPOLYGON"))
