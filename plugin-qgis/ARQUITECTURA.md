# Arquitectura objetivo: `peru_occ` para QGIS 3.44 LTR (Qt5)

Documento de referencia compartido. Los agentes escriben código dentro de esta
estructura; cambiarla requiere acuerdo del orquestador.

---

## Entorno objetivo

| Parámetro | Valor | Consecuencia práctica |
|---|---|---|
| QGIS | 3.44 LTR (última LTR de la serie 3.x) | `qgisMinimumVersion=3.44` en `metadata.txt` |
| Qt | Qt5 / PyQt5 | `from qgis.PyQt.QtWidgets import ...` — **nunca** `import PyQt5` directo |
| Python | 3.12 | `match`, `|` en anotaciones y `dataclasses` disponibles |
| Dependencias externas | **ninguna** | stdlib + API de QGIS. Sin `requests`, `shapely`, `geopandas`, `pandas` |
| Siguiente serie | QGIS 4.0 (Qt6) | No usar API marcada como *deprecated* en 3.44 |

> `qgis.PyQt` es la capa de compatibilidad de QGIS. Importar por ahí es lo que
> hará que este plugin sobreviva al salto a Qt6 sin reescritura.

---

## Estructura de archivos

```
plugin-qgis/peru_occ/
├── metadata.txt                  # identidad del plugin, qgisMinimumVersion=3.44
├── __init__.py                   # classFactory(iface)
├── plugin.py                     # PeruOccPlugin: initGui / unload, acciones, menú
├── recursos/
│   ├── iconos/                   # SVG/PNG
│   ├── estilos/                  # .qml: por source, por kingdom, por family
│   └── limites/                  # GeoPackage de límites INEI (si se empaqueta)
├── nucleo/                       # Lógica pura: sin Qt, sin iface. Testeable a solas.
│   ├── esquema.py                # los 24 campos, tipos QVariant, orden estricto
│   ├── config.py                 # defaults desde contratos/parametros_defecto.json
│   ├── normalizacion.py          # normalizar_texto(), catálogo de departamentos
│   ├── limites.py                # envoltorio de geoperu-py (transporte QGIS + caché)
│   ├── vendor/
│   │   └── geoperu/              # copia de geoperu-py: sin dependencias, no editar aquí
│   ├── geometria.py              # CCW, simplificación UTM, presupuesto WKT, teselado
│   ├── clientes/
│   │   ├── base.py               # reintentos, backoff, User-Agent, cancelación
│   │   ├── gbif.py               # occurrence/search + species/match
│   │   └── inaturalist.py        # v1/observations
│   ├── consolidacion.py          # unión de fuentes, deduplicación, mapeo a esquema
│   ├── validacion_espacial.py    # filtro exacto con QgsSpatialIndex
│   ├── manifiesto.py             # run_id + JSON de reproducibilidad
│   └── exportacion.py            # CSV / GeoJSON / capa de puntos
├── tareas/
│   └── tarea_busqueda.py         # QgsTask: orquesta núcleo, reporta progreso, cancela
├── gui/
│   ├── dialogo_busqueda.py       # diálogo principal
│   ├── dialogo_busqueda.ui       # Qt Designer (Qt5)
│   └── panel_resultados.py       # resumen de corrida y accesos a exportación
├── processing/
│   ├── proveedor.py              # QgsProcessingProvider
│   └── alg_buscar_ocurrencias.py # QgsProcessingAlgorithm (batch y modelos)
├── i18n/                         # traducciones (es por defecto, pt-BR objetivo)
└── test/
    ├── test_nucleo_*.py          # unitarios sin QGIS donde sea posible
    ├── test_integracion_*.py     # con pytest-qgis
    └── fixtures/                 # CSV/GeoJSON de peruocc como referencia
```

### La regla que sostiene todo: `nucleo/` no conoce Qt

`nucleo/` no importa `QtWidgets`, no toca `iface` y no muestra diálogos. Recibe
datos, devuelve datos y lanza excepciones tipadas. Esto permite que:

- el mismo núcleo alimente el diálogo **y** el algoritmo Processing sin duplicar
  lógica (es la causa más común de divergencia entre ambas superficies);
- los tests unitarios corran sin instanciar una aplicación Qt;
- `tareas/` sea una capa delgada de progreso y cancelación, no de negocio.

Excepción admitida y necesaria: `nucleo/` **sí** usa `QgsGeometry`,
`QgsCoordinateTransform`, `QgsSpatialIndex` y `QgsBlockingNetworkRequest`. Son
API de QGIS, no de Qt Widgets, y son justamente lo que reemplaza a `sf` y a
`httr` sin dependencias externas.

---

## Flujo de una corrida

```
Diálogo / Algoritmo Processing
        │  (ParametrosBusqueda: nivel, nombre, departamento, provincia,
        │   nombre_cientifico, grupo, limite_por_api, estrategia_espacial…)
        ▼
TareaBusqueda (QgsTask, hilo de fondo)
        │
        ├─ 1. limites.resolver()            → polígono detallado, EPSG:4326, nombres oficiales
        ├─ 2. geometria.preparar_lotes()    → N lotes con tile_id (teselado adaptativo)
        │
        ├─ 3. por cada lote:                → setProgress() + isCanceled() entre lotes
        │      ├─ geometria.wkt_para_api()  → CCW + simplificación ≤1500 car. (o bbox)
        │      ├─ clientes.gbif.buscar()
        │      └─ clientes.inaturalist.buscar()
        │
        ├─ 4. validacion_espacial.filtrar() → intersects contra el polígono DETALLADO
        ├─ 5. consolidacion.consolidar()    → esquema de 24 campos + deduplicación
        └─ 6. exportacion / manifiesto      → capa de puntos + CSV/GeoJSON/JSON
        ▼
finished(): cargar capa al proyecto, aplicar .qml, mostrar resumen
```

**Los cuatro puntos donde se pierde la corrida si se implementan mal:**

1. **Paso 3 vs. paso 4.** El WKT simplificado va a la API; el filtro usa el
   polígono original. Filtrar con el simplificado introduce falsos positivos y
   falsos negativos en el borde.
2. **`isCanceled()` solo entre lotes.** Dentro de una petición HTTP no hay punto
   de cancelación limpio; el granulado correcto es el lote.
3. **Nada de UI desde el hilo de la tarea.** El `QgsTask` devuelve datos; la capa
   se crea y se carga en `finished()`, que corre en el hilo principal.
4. **Techos de API.** Superarlos aborta con mensaje accionable. Truncar en
   silencio produce un CSV que parece correcto y no lo es.

---

## Hitos

| Hito | Contenido | Desbloquea |
|---|---|---|
| **H1** | Incrustar `geoperu-py` + transporte de QGIS + caché (riesgo R1 ya resuelto) | todo lo demás |
| **H2** | `geometria` (CCW, simplificación, teselado) con tests contra la lógica de R | H3 |
| **H3** | Clientes GBIF + iNaturalist con reintentos y conteo previo | H4 |
| **H4** | `consolidacion` + `validacion_espacial` + esquema de 24 campos | H5, H6 |
| **H5** | `QgsTask` + diálogo Qt5 + `.qml` | demo usable |
| **H6** | Algoritmo Processing + exportación + manifiesto | batch y trazabilidad |
| **H7** | Suite de tests, empaquetado ZIP, documentación didáctica | publicación |

H1 primero no es arbitrario: sin límites oficiales no hay nada que consultar.
Ya no es el eslabón sin equivalente en Python —`geoperu-py` lo resolvió— pero
sigue siendo la base de la que dependen los demás hitos.

### Cómo se incrusta `geoperu-py`

`nucleo/vendor/geoperu/` es una **copia** del paquete, no un `pip install`:
así el plugin no le pide al usuario instalar nada, que es el requisito R2.
Lo que `nucleo/limites.py` agrega encima:

1. `geoperu.establecer_transporte()` con `QgsBlockingNetworkRequest`, para
   respetar el proxy configurado en QGIS.
2. `GEOPERU_CACHE` apuntando al directorio del plugin (`peruocc_data_dir()`).
3. Conversión `QgsGeometry.fromWkb(QByteArray(rasgo.wkb))` — el paquete
   entrega WKB crudo justamente para no pagar una conversión a texto.
4. Traducción de sus excepciones (`GeografiaNoEncontrada`, `UnidadAmbigua`,
   `ErrorDescarga`) a los mensajes accionables del catálogo del plugin.

La copia se actualiza trayendo una versión publicada del paquete; **no se
edita dentro del plugin**, o se pierde al siguiente refresco.
