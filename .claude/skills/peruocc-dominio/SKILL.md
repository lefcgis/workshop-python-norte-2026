---
name: peruocc-dominio
description: Referencia de dominio del paquete R peruocc (ocurrencias de biodiversidad en unidades administrativas del Perú) y su traducción al plugin QGIS. Úsala al decidir QUÉ debe hacer el plugin, al mapear una función de R a Python, al tocar el esquema Darwin Core de 24 campos, los valores por defecto, los techos de GBIF/iNaturalist, o al actualizar la matriz de paridad. Actívala ante peruocc, GBIF, iNaturalist, Darwin Core, occurrence, ocurrencias, distrito, provincia, INEI, geoperu, manifiesto de reproducibilidad.
---

# Dominio `peruocc` → plugin QGIS

## Qué es el negocio

`peruocc` ensambla **evidencia de biodiversidad con trazabilidad administrativa**:
dado un distrito, provincia o polígono del Perú, entrega las ocurrencias de flora
y fauna registradas en GBIF e iNaturalist, validadas espacialmente, normalizadas
a Darwin Core y acompañadas de un manifiesto que permite defender la cifra.

Análisis completo en `plugin-qgis/ANALISIS_NEGOCIO.md`. **Léelo antes de discutir
alcance.**

## Los seis eslabones (ninguno es opcional)

1. Unidad administrativa → 2. Geometría oficial INEI + caché → 3. Consulta a GBIF
(WKT + taxonomía) e iNaturalist (bbox + taxón) → 4. **Validación espacial exacta
en memoria** → 5. Estandarización Darwin Core + deduplicación → 6. Exportación
trazable (CSV / GeoJSON / manifiesto).

Quitar el (4) hace el producto poco confiable. Quitar el (6) lo hace indefendible.

## Contratos de obligado cumplimiento

Antes de escribir código, lee:

- `plugin-qgis/contratos/esquema_ocurrencias.json` — los 24 campos, en orden.
- `plugin-qgis/contratos/parametros_defecto.json` — defaults y techos de API.
- `plugin-qgis/contratos/paridad_peruocc.md` — tu fila y tu evidencia exigida.
- `plugin-qgis/ARQUITECTURA.md` — dónde va tu archivo.

Si tu trabajo exige cambiar un contrato, **pídelo al orquestador**; no lo cambies
por tu cuenta ni lo eludas en el código.

## Mapa de funciones R → módulos Python

| `peruocc` (R) | Destino | Notas |
|---|---|---|
| `buscar_especies_distrito/provincia/poligono/peru` | `tareas/tarea_busqueda.py` + `nucleo/` | Cuatro entradas, un solo motor |
| `obtener_poligono_distrito/provincia/unidad` | `nucleo/limites.py` | `geoperu` no tiene puerto Python: riesgo R1 |
| `preparar_poligono_usuario` | `nucleo/limites.py` | En QGIS: capa activa o *features seleccionados* |
| `cargar_mapa_departamental` + caché `.rds` | `nucleo/limites.py` | Caché en GeoPackage, no `.rds` |
| `normalizar_texto`, `departamentos_oficiales` | `nucleo/normalizacion.py` | 25 departamentos |
| `asegurar_orientacion_antihoraria`, `simplificar_para_api`, `dividir_poligono_por_area`, `poligono_a_wkt` | `nucleo/geometria.py` | Ver skill `geometria-peruocc` |
| `buscar_gbif_por_poligono`, `buscar_inat_por_poligono` | `nucleo/clientes/` | Ver skill `clientes-gbif-inat` |
| `consolidar_ocurrencias`, `schema_ocurrencias` | `nucleo/consolidacion.py`, `nucleo/esquema.py` | |
| `ejecutar_con_reintentos` | `nucleo/clientes/base.py` | *Backoff* exponencial |
| `exportar_resultados`, `escribir_manifiesto` | `nucleo/exportacion.py`, `nucleo/manifiesto.py` | |
| `graficar_ocurrencias` | `recursos/estilos/*.qml` | El PNG estático se sustituye por simbología viva |
| `peruocc_data_dir` | `QgsSettings` | Preferencia persistente |

## Valores que no se reinventan

```
limite_por_api ............. 500     (null = descarga completa con conteo previo)
tolerancia_simplificacion .. 100 m
wkt_max_char ............... 1500    → escalar tolerancia ×3, hasta 6 veces, luego bbox
max_area_ha_por_lote ....... 1000
max_lotes_espaciales ....... 16
umbral_macro_bloques_ha .... 50000
reintentos_api ............. 3
pausa_entre_lotes_s ........ 0.2
kingdomKey GBIF ............ Plantae=6, Animalia=1
taxon_name iNat ............ flora→"Plantae", fauna→"Animalia"
calidad iNat ............... "research"
techo GBIF ................. 100000 registros (occurrence/search)
techo iNaturalist .......... 10000 registros por consulta
```

## Las cuatro trampas del dominio

1. **El bbox de iNaturalist trae falsos positivos.** El `bounds` de `rinat` es
   `(ymin, xmin, ymax, xmax)` — es decir (S, W, N, E), no (W, S, E, N). Confundir
   el orden devuelve datos de otro lugar del país, silenciosamente.
2. **Simplificar es para consultar, no para filtrar.** El filtro final va contra
   el polígono detallado original. Siempre.
3. **Nunca truncar en silencio.** Al superar el techo de una API, `peruocc` aborta
   con un mensaje que dice qué hacer (descarga citable en GBIF, partición temporal
   en iNaturalist). El plugin hace lo mismo. Un CSV incompleto que parece completo
   es el peor resultado posible.
4. **Los nombres de campo son Darwin Core, en inglés.** La UI va en español; el
   esquema **no se traduce**. `scientificName` no es `nombreCientifico`.

## Fixtures de referencia

En `data/` del paquete `peruocc`: Miraflores/flora, Tambopata/fauna,
Tarma/biodiversidad (CSV + GeoJSON, 2026-08-17). GBIF e iNaturalist son bases
vivas, así que **la comparación es estructural** (columnas, orden, tipos, CRS,
cero puntos fuera del límite), no de conteo. El conteo solo se compara entre
plugin y `peruocc` corridos el mismo día.
