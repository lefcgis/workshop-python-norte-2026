---
name: qgis-plugin-testing
description: Estrategia de pruebas y validación para el plugin peru_occ — unitarios del núcleo sin QGIS, integración con pytest-qgis, dobles de prueba para GBIF e iNaturalist, fixtures de regresión contra los CSV de peruocc y verificación del ZIP instalable. Úsala al escribir o arreglar tests, al montar CI, o al verificar una fila de la matriz de paridad. Actívala ante test, pytest, pytest-qgis, fixture, mock, regresión, paridad, CI, cobertura, validar plugin.
---

# Pruebas del plugin `peru_occ`

## Tres niveles, tres propósitos

| Nivel | Qué cubre | Con QGIS | Red |
|---|---|---|---|
| Unitario | `nucleo/` puro: normalización, esquema, mapeos, `run_id`, cascada de WKT | no | no |
| Integración | geometría con `QgsGeometry`, capas, algoritmo Processing | `pytest-qgis` | dobles |
| Paridad / humo | estructura de salida contra fixtures de `peruocc`; ZIP instalable | sí | real, marcado |

Los tests de nivel 1 y 2 **no tocan la red**. Un test que dependa de GBIF falla los
días que GBIF está lento, y un test que falla por motivos ajenos al código se acaba
ignorando — y con él, toda la suite.

## Los tests que realmente protegen el producto

Ordenados por valor:

1. **Cero puntos fuera del límite.** Fixture con un límite conocido y registros
   sintéticos dentro, fuera y **sobre el borde**; ninguno de fuera sobrevive.
   Protege el eslabón que da confiabilidad al producto.
2. **Orden del bbox de iNaturalist.** `(ymin, xmin, ymax, xmax)` → `swlat/swlng/
   nelat/nelng`. Un test de una línea que evita consultar la región equivocada del país.
3. **Cabecera del CSV idéntica** a la del fixture de `peruocc`. Detecta cualquier
   deriva del esquema en el acto.
4. **Cascada del presupuesto de WKT.** Polígono simple → `directa`; complejo →
   `simplificada` con ≤1500 caracteres; patológico → `bbox`. Verificar las tres ramas.
5. **Techo de API aborta, no trunca.** Doble que reporta `count = 200000`; debe
   lanzar la excepción tipada, nunca devolver un resultado parcial.
6. **CCW.** Polígono horario de entrada ⇒ WKT emitido antihorario.
7. **Nº de lotes** para una unidad conocida coincide con el que produce la lógica de R.
8. **Normalización de nombres.** «MADRE DE DIOS», «Madre de Dios», «madre de dios»
   resuelven a la misma unidad.
9. **Reintentos.** Un doble que devuelve 429 y luego 200 completa la corrida; un 400
   **no** se reintenta.
10. **Asimetría CSV/GeoJSON.** Fixture con una fila sin coordenadas: aparece en el
    CSV, no en el GeoJSON.

## Unitarios sin QGIS

```python
def test_bbox_inat_respeta_orden_sur_oeste_norte_este():
    # rinat: bounds = c(ymin, xmin, ymax, xmax)
    params = parametros_inat(bbox=(-12.13, -77.05, -12.09, -77.01))
    assert params["swlat"] == -12.13 and params["swlng"] == -77.05
    assert params["nelat"] == -12.09 and params["nelng"] == -77.01


def test_cabecera_csv_es_diff_comparable_con_peruocc():
    esperada = Path("test/fixtures/ocurrencias_miraflores_flora_20260817.csv") \
        .read_text(encoding="utf-8").splitlines()[0]
    assert ",".join(c.nombre for c in ESQUEMA) == esperada
```

## Integración con `pytest-qgis`

```python
import pytest
from qgis.core import QgsGeometry, QgsPointXY

pytest_plugins = ("pytest_qgis",)   # aporta la fixture qgis_app

@pytest.fixture
def limite_cuadrado():
    return QgsGeometry.fromWkt("POLYGON((-77.05 -12.13, -77.01 -12.13, "
                               "-77.01 -12.09, -77.05 -12.09, -77.05 -12.13))")

def test_filtro_espacial_descarta_todo_lo_de_fuera(qgis_app, limite_cuadrado):
    registros = [
        {"decimalLongitude": -77.03, "decimalLatitude": -12.11},  # dentro
        {"decimalLongitude": -77.30, "decimalLatitude": -12.11},  # fuera
        {"decimalLongitude": -77.05, "decimalLatitude": -12.13},  # sobre el vértice
        {"decimalLongitude": None,   "decimalLatitude": -12.11},  # sin coordenada
    ]
    dentro = filtrar_dentro(registros, limite_cuadrado)
    assert len(dentro) == 2                      # el de dentro y el del borde
    assert all(r["decimalLongitude"] != -77.30 for r in dentro)
```

El caso del borde se decide y se documenta una vez: `intersects` lo incluye,
`contains` lo excluye. `peruocc` usa `st_intersects`, así que **el borde cuenta**.

## Dobles para las APIs

No se hacen peticiones reales en la suite. Se guardan respuestas JSON recortadas
—2 o 3 registros, todos los campos— en `test/fixtures/respuestas/` y se inyecta el
transporte:

```python
class TransporteFalso:
    def __init__(self, respuestas): self.respuestas, self.llamadas = respuestas, []
    def get_json(self, url, params):
        self.llamadas.append((url, params))
        return self.respuestas.pop(0)
```

Inyectar el transporte por constructor (no parchear módulos) es lo que permite
verificar **qué parámetros se enviaron** además de qué se recibió — y los errores de
este flujo están casi siempre en los parámetros.

## Tests con red: opcionales y marcados

```python
@pytest.mark.red
def test_gbif_responde_al_wkt_de_miraflores(): ...
```

```ini
# pytest.ini
markers = red: requiere acceso a internet y APIs vivas
```

Se ejecutan con `pytest -m red`, **fuera** de la suite por defecto y fuera de CI.
Su valor es distinto: confirman que los endpoints y los techos documentados siguen
vigentes. Conviene correrlos antes de cada release y anotar el resultado.

## Comparación contra fixtures de `peruocc`

GBIF e iNaturalist son bases vivas: el conteo del 2026-08-17 **no se reproduce**.
Por eso la comparación es **estructural**:

- nombres y orden de columnas idénticos;
- tipos por columna compatibles;
- CRS EPSG:4326 en el GeoJSON;
- `source` solo con valores `GBIF` / `iNaturalist`;
- ningún punto fuera del límite de la unidad;
- CSV ⊇ GeoJSON en número de filas.

Comparar conteos solo tiene sentido entre plugin y `peruocc` ejecutados **el mismo
día** con los mismos parámetros. Un test de conteo contra un CSV histórico es un
test que fallará y se acabará desactivando.

## CI

```yaml
# .github/workflows/test-plugin.yml
jobs:
  test:
    runs-on: ubuntu-latest
    container: qgis/qgis:release-3_44     # misma serie LTR que el objetivo
    steps:
      - uses: actions/checkout@v4
      - run: pip install pytest pytest-qgis pytest-cov
      - run: xvfb-run -a pytest plugin-qgis/peru_occ/test -m "not red" --cov
```

`xvfb-run` es necesario aunque no se abran ventanas: instanciar `QgsApplication`
requiere un display. Fijar la imagen en la serie 3.44 evita que CI valide contra una
versión distinta a la del objetivo.

## Verificación del ZIP antes de entregar

1. Construir el ZIP: una sola carpeta raíz, sin `__pycache__` ni `.pyc`.
2. Instalar en un **perfil limpio** de QGIS 3.44 (`--profile prueba`).
3. Confirmar que el plugin carga sin trazas en el log.
4. Correr una consulta distrital de punta a punta.
5. Comprobar que el algoritmo aparece en la Caja de herramientas.
6. Recargar con Plugin Reloader: las acciones **no** se duplican (prueba de `unload`).
7. Desinstalar: no quedan menús ni barras huérfanas.
