# Sistema multiagente: plugin QGIS 3.44 LTR desde `peruocc`

Equipo de agentes para portar el paquete R **`peruocc`** — *Query and Standardize
Biodiversity Occurrences in Peru* — a un plugin de QGIS 3.44 LTR (Qt5).

## Cómo se usa

```
/peruocc-qgis estado      → reporta el tablero de paridad y se detiene
/peruocc-qgis H1          → arranca el hito de límites INEI + andamiaje
/peruocc-qgis "<tarea>"   → el orquestador decide el frente y reparte
```

También se puede invocar un especialista directo cuando ya se sabe qué hace falta:
«usa el agente `ingeniero-geoespacial` para…».

## Arquitectura del equipo

```
                        /peruocc-qgis
                              │
                    orquestador-peruqgis
            (planifica · reparte · verifica · integra)
                              │
    ┌──────────────┬──────────┴───────┬──────────────┬─────────────┐
    │              │                  │              │             │
analista-      arquitecto-      ingeniero-      ingeniero-   desarrollador-
negocio-        plugin-        geoespacial       apis-          ui-qt5
biodiversidad    qgis                         biodiversidad
    │              │                  │              │             │
    └──────────────┴──────────┬───────┴──────────────┴─────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
          integrador-   qa-validacion-  documentador-
          processing        qgis          didactico
```

El orquestador no escribe código de producción. Los contratos en
`plugin-qgis/contratos/` son el mecanismo que evita que nueve agentes deriven en
nueve interpretaciones del mismo producto.

## Reparto de responsabilidades

| Agente | Dueño de | Filas de paridad | Hitos |
|---|---|---|---|
| `orquestador-peruqgis` | plan, reparto, verificación, contratos | todas (verifica) | todos |
| `analista-negocio-biodiversidad` | `contratos/`, alcance, requisitos | D3 | transversal |
| `arquitecto-plugin-qgis` | andamiaje, `metadata.txt`, ciclo de vida, ZIP | E6, F5 | H1, H7 |
| `ingeniero-geoespacial` | `nucleo/limites.py`, `geometria.py`, `validacion_espacial.py` | A1–A6, B1–B4, D1 | H1, H2, H4 |
| `ingeniero-apis-biodiversidad` | `nucleo/clientes/`, `consolidacion.py` | B5, C1–C9, D2 | H3, H4 |
| `desarrollador-ui-qt5` | `tareas/`, `gui/`, `.qml` | E1, F1–F3 | H5 |
| `integrador-processing` | `processing/`, `exportacion.py`, `manifiesto.py` | D4, E2–E5, F4 | H6 |
| `qa-validacion-qgis` | `test/`, integración continua, ZIP | verifica todas | H7 |
| `documentador-didactico` | documentación, catálogo de mensajes, material de taller | F6 | H7 |

## Skills

Paquetes de conocimiento que los agentes cargan según la tarea. Varios agentes
comparten una misma skill: es lo que evita que cada uno resuelva por su cuenta el
orden del bbox de iNaturalist o el presupuesto de caracteres del WKT.

| Skill | Contenido | La cargan |
|---|---|---|
| `peruocc-dominio` | negocio, seis eslabones, mapa R→Python, valores por defecto, trampas del dominio | todos |
| `qgis-plugin-scaffold` | estructura, `metadata.txt`, `classFactory`, `initGui`/`unload`, empaquetado | arquitecto |
| `geometria-peruocc` | CCW, simplificación en UTM, presupuesto WKT, teselado, filtro exacto | geoespacial |
| `clientes-gbif-inat` | endpoints, parámetros, paginación, techos, reintentos, mapeo de campos | apis |
| `qgis-qt5-tareas-ui` | `QgsTask`, hilos, cancelación real, capas en memoria, simbología | ui-qt5 |
| `qgis-processing-alg` | proveedor y algoritmo Processing, batch, `feedback` | processing |
| `exportacion-trazable` | esquema, CSV/GeoJSON, manifiesto, `run_id` | processing, analista |
| `qgis-plugin-testing` | unitarios, `pytest-qgis`, dobles, fixtures, integración continua, ZIP | qa |

## Orden de los hitos

```
H1  límites INEI + normalización + andamiaje   ← riesgo R1, va primero
H2  geometría (CCW, WKT, teselado)
H3  clientes GBIF + iNaturalist                ← paralelizable con H2
H4  consolidación + filtro espacial exacto
H5  QgsTask + diálogo + simbología             ← primera demo usable
H6  Processing + exportación + manifiesto      ← paralelizable con H5
H7  pruebas + empaquetado + documentación
```

H1 primero porque `geoperu` es R y no tiene puerto Python: es el único eslabón sin
equivalente directo, y sin límites oficiales no hay nada que consultar.

## Las cuatro regresiones que el orquestador busca en cada entrega

1. Se filtró con el polígono **simplificado** en vez del detallado.
2. El bbox de iNaturalist quedó en orden (W,S,E,N) en lugar de **(S,W,N,E)**.
3. Hay acceso a red fuera de un `QgsTask`.
4. Un techo de API **trunca en silencio** en lugar de abortar.

Ninguna de las cuatro lanza una excepción. Todas producen resultados que parecen
correctos y no lo son, y por eso se revisan explícitamente en cada entrega.

## Dependencia propia: `geoperu-py`

El riesgo R1 —«`geoperu` es R y no tiene puerto Python»— está **resuelto**.
El repositorio incluye `geoperu-py/`, puerto a Python del paquete, sin
dependencias externas (lee GeoPackage con `sqlite3` y trae su propio lector de
WKB), con catálogo congelado, caché con huella SHA-256, CLI y 127 pruebas.

El plugin lo **incrusta** en `nucleo/vendor/geoperu/` en lugar de declararlo
como dependencia: así el usuario no necesita ejecutar ningún `pip install`,
que es el requisito R2. Los arreglos van al paquete, nunca a la copia.

## Estado actual

Sistema de agentes, skills y contratos: **listos**. Dependencia de límites
INEI (`geoperu-py`): **lista y probada**. Código del plugin: **no iniciado**
— todas las filas de la matriz de paridad están en `pendiente`.
Punto de partida: `/peruocc-qgis H1`.
