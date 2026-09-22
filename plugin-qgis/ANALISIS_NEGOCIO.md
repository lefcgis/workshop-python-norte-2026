# Análisis de negocio: de `peruocc` (R) a un plugin QGIS 3.44 LTR

> Base analizada: paquete **`peruocc` 0.1.0**, *Query and Standardize Biodiversity
> Occurrences in Peru* (Paul E. Santos Andrade, ORCID 0000-0002-6635-0375).
> Artefacto de referencia: <https://paulesantos.github.io/peruocc/>.
> Fuente leída para este análisis: código del paquete (`R/`, `NAMESPACE`,
> `DESCRIPTION`, vignettes y datos de ejemplo en `data/`).

---

## 1. ¿Qué negocio resuelve `peruocc`?

`peruocc` no es un descargador de datos. Es un **ensamblador de evidencia de
biodiversidad con trazabilidad administrativa**. Su valor no está en el acceso a
GBIF o iNaturalist —eso ya existe— sino en resolver cuatro fricciones que
aparecen siempre que alguien necesita responder *«qué especies hay registradas
en este distrito»*:

| Fricción real | Cómo la resuelve `peruocc` |
|---|---|
| **El límite administrativo no es trivial.** Los nombres de distrito se repiten entre departamentos, y las APIs no entienden «distrito de Cusco». | Resuelve la geometría oficial INEI vía `geoperu`, desambigua por departamento/provincia y cachea el resultado en `.rds`. |
| **Las APIs no aceptan geometrías reales.** GBIF limita la longitud del WKT; iNaturalist solo acepta *bounding box*. | Simplificación métrica adaptativa en UTM hasta entrar en presupuesto (≤1500 caracteres), teselado adaptativo por área, y *bbox* como último recurso. |
| **Lo que devuelven las APIs no es lo que se pidió.** Un *bbox* trae falsos positivos fuera del distrito. | **Doble filtro**: consulta laxa a la API, intersección espacial exacta en memoria contra el polígono detallado original. |
| **Dos fuentes, dos esquemas.** GBIF e iNaturalist nombran los mismos conceptos distinto. | Normalización a un esquema único alineado a **Darwin Core** (24 campos) con el campo `source` como procedencia. |

A eso se suma el diferenciador que convierte el paquete en herramienta de
gestión y no solo de exploración: **el manifiesto de reproducibilidad**. Cada
corrida escribe un JSON con `run_id`, parámetros, WKT del polígono, resumen de
resultados, archivos generados y versiones de paquetes. Es lo que permite que un
expediente técnico, una línea base ambiental o una tesis sostengan *cómo* se
obtuvo la cifra que reportan.

### Cadena de valor (6 eslabones)

```
(1) Unidad administrativa  →  (2) Geometría oficial + caché
                                      ↓
                        (3) Consulta a repositorios vivos
                            GBIF (WKT + taxonomía)
                            iNaturalist (bbox + taxón)
                                      ↓
                    (4) Validación espacial exacta en memoria
                                      ↓
                  (5) Estandarización Darwin Core + deduplicación
                                      ↓
              (6) Exportación trazable (CSV / GeoJSON / PNG / manifiesto)
```

El plugin debe reproducir **los seis eslabones**. Si se omite el (4), el
producto deja de ser confiable; si se omite el (6), deja de ser defendible.

---

## 2. Quién usa esto y por qué el canal R no le alcanza

| Segmento | Necesidad | Por qué R es una barrera |
|---|---|---|
| **Consultoras ambientales** (EIA, líneas base, DIA) | Listado de flora/fauna registrada por distrito, con fuente y licencia citables | El entregable se arma en QGIS; salir a R y volver rompe el flujo y la auditoría |
| **Gobiernos regionales y locales, ARA, SERFOR** | Caracterización biológica de un ámbito de intervención | Personal técnico formado en QGIS, no en R |
| **Áreas naturales protegidas (SERNANP)** | Inventario dentro de ANP y zonas de amortiguamiento | El ámbito no es administrativo: es un polígono propio |
| **Academia y docencia** (caso de este repositorio) | Enseñar el flujo completo dato → validación → mapa | Enseñar R *y* SIG en el mismo taller duplica la carga cognitiva |
| **Tesistas de biología/geografía** | Datos reproducibles y defendibles ante jurado | Instalar la cadena R + `sf` + GDAL es la primera causa de abandono |

**El insight de producto:** el usuario de `peruocc` ya tiene QGIS abierto. El
polígono del que quiere saber está cargado como capa. El mapa final se hará en
QGIS. R es un desvío en un viaje que empieza y termina en QGIS.

---

## 3. Qué gana el plugin que el paquete no puede dar

Un puerto literal sería un desperdicio. Lo que QGIS agrega sobre R:

1. **El polígono ya está en el proyecto.** `buscar_especies_poligono()` exige leer
   un `.shp` o `.geojson` del disco. En QGIS, el ámbito de interés es *la capa
   seleccionada*, o incluso *los features seleccionados* de esa capa.
2. **Simbología y exploración viva.** `graficar_ocurrencias()` produce un PNG
   estático. QGIS entrega un `.qml` categorizado por `source`/`kingdom`/`family`,
   identificación de registros, y el enlace `sourceURL` clicable desde el panel
   de atributos.
3. **Batch y modelado.** Un `QgsProcessingAlgorithm` corre sobre **una tabla de
   distritos** o dentro de un modelo gráfico. En R eso es un `for` que el usuario
   debe escribir.
4. **Caché nativa y consultable.** Los `.rds` de `peruocc` solo los lee R. Un
   **GeoPackage** de caché es a la vez formato de caché y capa arrastrable al
   lienzo.
5. **Interoperabilidad de salida.** QGIS exporta a los formatos que el usuario ya
   necesita (GPKG, SHP, XLSX, atlas de impresión) sin código adicional.

---

## 4. Riesgos de negocio y decisiones que hay que tomar temprano

| # | Riesgo | Decisión tomada |
|---|---|---|
| R1 | ~~**`geoperu` es R.** No hay puerto Python del proveedor de límites INEI.~~ **RESUELTO.** | Se escribió **`geoperu-py`** (ver `geoperu-py/`), puerto a Python del paquete, sin dependencias externas: lee GeoPackage con `sqlite3` y trae su propio lector de WKB. El plugin lo incrusta en `nucleo/limites.py`. El catálogo de datos va congelado dentro del paquete y se revisa una vez al año. |
| R2 | **Sin dependencias externas.** Un `pip install` dentro de QGIS es inaceptable para el usuario institucional. | Solo stdlib de Python 3.12 + API de QGIS/Qt5. Geometría con `QgsGeometry`, red con `QgsBlockingNetworkRequest` (respeta el proxy configurado en QGIS). Nada de `geopandas`, `shapely`, `requests`, `rgbif`. |
| R3 | **Las APIs cambian y tienen techos duros.** GBIF corta en 100 000 registros; iNaturalist en 10 000 por consulta. | Los techos viven en `contratos/parametros_defecto.json`. Al excederlos el plugin **no trunca en silencio**: informa y propone descarga citable o partición temporal, igual que hace `peruocc`. |
| R4 | **Congelar la UI de QGIS mata la adopción.** Una consulta provincial son decenas de llamadas HTTP. | Toda I/O dentro de `QgsTask`. Ningún acceso a red en el hilo principal. Cancelación real, no cosmética. |
| R5 | **Divergencia silenciosa respecto a `peruocc`.** Si el plugin devuelve otra cifra que el paquete, ambos pierden credibilidad. | **Matriz de paridad** (`contratos/paridad_peruocc.md`) + fixtures de regresión contra los CSV de ejemplo del paquete (Miraflores/flora, Tambopata/fauna, Tarma). |
| R6 | **Nombres oficiales vs. nombres escritos.** «Madre de Dios» / «MADRE DE DIOS» / «madre de dios». | Normalización de texto (mayúsculas, tildes, espacios) replicando `normalizar_texto()`, y desambiguación explícita ante homónimos en lugar de elegir el primero. |
| R7 | **Licencias heterogéneas.** No todo registro de GBIF es reutilizable. | `license` es campo de primera clase del esquema y se muestra en la UI. El plugin no decide por el usuario, pero no le oculta el dato. |

---

## 5. Alcance funcional del plugin (MVP y más allá)

**MVP (paridad con `peruocc`):**
- Búsqueda por **distrito**, **provincia** y **polígono de usuario** (capa QGIS activa o selección).
- Filtros: taxón (`nombre_cientifico`) y grupo (`flora` / `fauna`).
- Consulta dual GBIF + iNaturalist, consolidada y deduplicada.
- Validación espacial exacta contra el polígono detallado.
- Salida: capa de puntos en memoria con los 24 campos, `.qml` categorizado,
  exportación CSV / GeoJSON / manifiesto JSON.
- Algoritmo Processing equivalente, usable en batch y en modelos.

**Fuera del MVP, en el backlog (valor incremental que R no cubre):**
- Curvas de acumulación de especies y métricas de riqueza por unidad.
- Detección de registros sospechosos (centroide de distrito, coordenadas
  invertidas, año ausente) — lo que en R haría `CoordinateCleaner`.
- Cruce con ANP, ecorregiones y listas de especies amenazadas (D.S. 004-2014-MINAGRI).
- Comparación temporal entre dos corridas del mismo `run_id` base.

---

## 6. Criterios de aceptación del negocio

El plugin está listo cuando un profesional que **no sabe R**:

1. Instala el ZIP en QGIS 3.44 LTR sin instalar nada más.
2. Obtiene, para «Miraflores, Lima, flora», **el mismo conteo de registros** que
   `peruocc` para los mismos parámetros (tolerancia documentada por la
   naturaleza viva de las APIs).
3. Ve los puntos simbolizados por fuente sobre el límite distrital, sin un solo
   punto fuera del límite.
4. Exporta un CSV cuyas columnas son **diff-comparables** contra el CSV de `peruocc`.
5. Obtiene un manifiesto JSON que le permite justificar la cifra ante un revisor.
6. Puede repetir todo lo anterior para los 40 distritos de una provincia sin
   escribir código.
