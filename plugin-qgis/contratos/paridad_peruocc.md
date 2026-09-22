# Matriz de paridad `peruocc` (R) → plugin QGIS

Contrato de equivalencia funcional. Cada fila tiene **un agente responsable**.
Una fila no se marca resuelta sin la evidencia indicada en la última columna.

Leyenda de estado: `pendiente` · `en curso` · `hecho` · `divergente (justificado)`

---

## A. Resolución del ámbito espacial

| # | `peruocc` | Equivalente QGIS | Responsable | Evidencia exigida | Estado |
|---|---|---|---|---|---|
| A1 | `obtener_poligono_distrito(distrito, departamento, provincia)` | `ProveedorLimites.distrito()` | ingeniero-geoespacial | Geometría idéntica (área ±0.01 %) para 5 distritos de prueba | pendiente |
| A2 | `obtener_poligono_provincia(provincia, departamento)` — disuelve distritos con `st_union` | `ProveedorLimites.provincia()` con disolución | ingeniero-geoespacial | La provincia disuelta no tiene huecos internos entre distritos | pendiente |
| A3 | `obtener_poligono_unidad(nombre, nivel, ...)` | Despachador único por `nivel` | ingeniero-geoespacial | Test de despacho distrito/provincia | pendiente |
| A4 | `preparar_poligono_usuario(poligono, nombre)` — lee `sf`/`.shp`/`.geojson` | Capa QGIS activa, o *features seleccionados*, reproyectada a EPSG:4326 | ingeniero-geoespacial | Ámbito con CRS de origen distinto a 4326 produce el mismo resultado | pendiente |
| A5 | `cargar_mapa_departamental()` + caché `.rds` + caché en memoria | Caché GeoPackage en disco + caché en memoria por sesión | ingeniero-geoespacial | Segunda consulta al mismo departamento sin tráfico de red | pendiente |
| A6 | `normalizar_texto()` y `departamentos_oficiales()` (25 departamentos) | Normalizador equivalente + catálogo oficial | ingeniero-geoespacial | «MADRE DE DIOS», «Madre de Dios» y «madre de dios» resuelven igual | pendiente |

## B. Preparación geométrica para las APIs

| # | `peruocc` | Equivalente QGIS | Responsable | Evidencia exigida | Estado |
|---|---|---|---|---|---|
| B1 | `asegurar_orientacion_antihoraria()` / `corregir_poligono_ccw()` | Forzar anillos CCW antes de enviar WKT a GBIF | ingeniero-geoespacial | WKT emitido es CCW para un polígono de entrada CW | pendiente |
| B2 | `simplificar_para_api(max_char = 1500, tol = 100)` — escala ×3 hasta 6 veces, luego *bbox* | Misma cascada, mismos números | ingeniero-geoespacial | Distrito complejo (p. ej. Tambopata) entra en ≤1500 caracteres | pendiente |
| B3 | `simplificar_poligono()` en UTM (no en grados) | Simplificación en la zona UTM del centroide, no en EPSG:4326 | ingeniero-geoespacial | La tolerancia se aplica en metros reales | pendiente |
| B4 | `dividir_poligono_por_area(max_area_ha = 1000, max_lotes = 16)`, lado `sqrt(area_lote_ha*10000)` | Teselado adaptativo idéntico, con `tile_id` | ingeniero-geoespacial | Nº de lotes coincide con R para la misma unidad | pendiente |
| B5 | `poligono_a_wkt()` | WKT sin SRID embebido, compatible con el parámetro `geometry` de GBIF | ingeniero-apis-biodiversidad | GBIF acepta el WKT sin error 400 | pendiente |

**Regla no negociable (B6):** la simplificación se usa **solo** para consultar la
API. El filtro final se hace contra el polígono **detallado original**.

## C. Consulta a repositorios

| # | `peruocc` | Equivalente QGIS | Responsable | Evidencia exigida | Estado |
|---|---|---|---|---|---|
| C1 | `rgbif::occ_search(geometry, hasCoordinate, taxonKey, kingdomKey, scientificName, limit)` | Cliente REST propio sobre `occurrence/search` | ingeniero-apis-biodiversidad | Mismo conteo que `rgbif` para los mismos filtros | pendiente |
| C2 | `rgbif::name_backbone(name)` → `usageKey` | `species/match` → `usageKey`; sin coincidencia ⇒ *fallback* a `scientificName` | ingeniero-apis-biodiversidad | «Polylepis» resuelve a su `usageKey`; texto basura cae al *fallback* | pendiente |
| C3 | `grupo = "flora"` ⇒ `kingdomKey = 6`; `"fauna"` ⇒ `kingdomKey = 1` | Mismos códigos, sin recalcularlos | ingeniero-apis-biodiversidad | Test de mapeo de constantes | pendiente |
| C4 | `rinat::get_inat_obs(bounds = c(ymin, xmin, ymax, xmax), geo, quality, taxon_name, maxresults)` | `v1/observations` con `swlat/swlng/nelat/nelng`, `geo`, `quality_grade`, `taxon_name` | ingeniero-apis-biodiversidad | **Orden del bbox**: `bounds` de `rinat` es (S,W,N,E), no (W,S,E,N) | pendiente |
| C5 | `grupo` ⇒ `taxon_name = "Plantae"` / `"Animalia"` en iNat | Mismo mapeo | ingeniero-apis-biodiversidad | Test de mapeo | pendiente |
| C6 | `ejecutar_con_reintentos(reintentos = 3, pausa_inicial = 0.5)` con *backoff* | Reintentos con *backoff* exponencial y respeto de `Retry-After` | ingeniero-apis-biodiversidad | Un 429 simulado reintenta y no aborta la corrida | pendiente |
| C7 | `limite = NULL` ⇒ conteo previo obligatorio; aborta si GBIF >100 000 o iNat >10 000 | Idéntico: **abortar con mensaje accionable, nunca truncar en silencio** | ingeniero-apis-biodiversidad | Consulta a un departamento entero produce el aviso, no un CSV incompleto | pendiente |
| C8 | Caché de consultas por lote (`nombre_seguro_cache`, `cache_dir`) | Caché en disco por clave de ejecución + `tile_id` | ingeniero-apis-biodiversidad | Reejecución idéntica sin tráfico de red | pendiente |
| C9 | `pausa_entre_lotes_s = 0.2` | Misma pausa; `User-Agent` identificable del plugin | ingeniero-apis-biodiversidad | Inspección de cabeceras | pendiente |

## D. Validación y consolidación

| # | `peruocc` | Equivalente QGIS | Responsable | Evidencia exigida | Estado |
|---|---|---|---|---|---|
| D1 | `sf::st_intersects()` contra el polígono detallado | `QgsGeometry.intersects` acelerado con `QgsSpatialIndex` | ingeniero-geoespacial | **Cero** puntos fuera del límite en las 3 unidades de fixture | pendiente |
| D2 | `consolidar_ocurrencias()` — une fuentes y deduplica | Consolidador equivalente, criterio de deduplicación documentado | ingeniero-apis-biodiversidad | Registro presente en ambas fuentes no se duplica | pendiente |
| D3 | `schema_ocurrencias()` — 24 campos en orden | `contratos/esquema_ocurrencias.json`, orden estricto | analista-negocio-biodiversidad | `head -1` del CSV idéntico al de `peruocc` | pendiente |
| D4 | `resumen`: `total_registros`, `registros_gbif`, `registros_inat`, `lotes_espaciales`, `fallos_lotes`, totales reportados por API | Mismo diccionario de resumen | integrador-processing | El resumen del manifiesto contiene todas las claves | pendiente |

## E. Salida y trazabilidad

| # | `peruocc` | Equivalente QGIS | Responsable | Evidencia exigida | Estado |
|---|---|---|---|---|---|
| E1 | `graficar_ocurrencias(color_por = "source")` → PNG ggplot2 | Capa de puntos + `.qml` categorizado (`source`/`kingdom`/`family`) | desarrollador-ui-qt5 | Capa cargada y simbolizada al terminar la tarea | pendiente |
| E2 | `exportar_resultados(formatos = c("csv","geojson","manifiesto"))` | Mismos tres formatos, mismos nombres de archivo | integrador-processing | Tripleta de archivos con el mismo patrón de nombre | pendiente |
| E3 | `escribir_manifiesto()`: `schema_version`, `run_id`, `executed_at_utc`, `parameters`, `spatial{crs, polygon_wkt}`, `result_summary`, `files`, `runtime` | Manifiesto con idéntica estructura; `runtime` reporta versión de QGIS/Python en lugar de R | integrador-processing | Comparación llave por llave contra un manifiesto de `peruocc` | pendiente |
| E4 | `run_id` = `%Y%m%dT%H%M%SZ_nivel_unidad_grupo` | Mismo patrón | integrador-processing | Test del generador de `run_id` | pendiente |
| E5 | GeoJSON omite filas sin coordenadas finitas; CSV las conserva | Mismo comportamiento asimétrico | integrador-processing | Fixture con fila sin coordenadas | pendiente |
| E6 | `peruocc_data_dir()` — directorio central de caché y salidas | Preferencia persistente con `QgsSettings` | arquitecto-plugin-qgis | La ruta sobrevive al reinicio de QGIS | pendiente |

## F. Superficie de interacción (sin equivalente en R)

| # | Requisito | Responsable | Evidencia exigida | Estado |
|---|---|---|---|---|
| F1 | Toda la red y la geometría pesada dentro de `QgsTask`; UI nunca bloqueada | desarrollador-ui-qt5 | Consulta provincial con la UI responsiva y cancelable | pendiente |
| F2 | Cancelación real: aborta entre lotes y no deja capas a medias | desarrollador-ui-qt5 | Cancelar a mitad de corrida no crea capa parcial | pendiente |
| F3 | Progreso por lote en la barra de mensajes de QGIS | desarrollador-ui-qt5 | Inspección visual | pendiente |
| F4 | `QgsProcessingAlgorithm` equivalente, apto para batch y modelos | integrador-processing | Ejecución batch sobre una tabla de 5 distritos | pendiente |
| F5 | `metadata.txt` válido, `qgisMinimumVersion=3.44`, ZIP instalable | arquitecto-plugin-qgis | Instalación limpia en QGIS 3.44 LTR | pendiente |
| F6 | Mensajes de error accionables en español (paridad con `cli::cli_abort`) | documentador-didactico | Revisión de catálogo de mensajes | pendiente |

---

## Fixtures de regresión

Provienen de `data/` del propio paquete y son la prueba de no divergencia:

| Fixture | Parámetros | Archivos de referencia |
|---|---|---|
| Miraflores / flora | distrito=Miraflores, departamento=Lima, grupo=flora | `ocurrencias_miraflores_flora_20260817.{csv,geojson}` |
| Tambopata / fauna | distrito=Tambopata, departamento=Madre de Dios, grupo=fauna | `ocurrencias_tambopata_fauna_20260817.{csv,geojson}` |
| Tarma / biodiversidad | distrito=Tarma, departamento=Junín, grupo=NULL | `ocurrencias_tarma_biodiversidad_20260817.{csv,geojson}` |

**Cómo se comparan.** GBIF e iNaturalist son bases vivas: el conteo de 2026-08-17
no se reproduce hoy. Por eso la comparación es **estructural, no de conteo**:
nombres y orden de columnas, tipos, CRS, ausencia de puntos fuera del límite,
dominio de `source`, y consistencia entre CSV y GeoJSON. El conteo se compara
únicamente entre plugin y `peruocc` **ejecutados el mismo día**.
