# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado semántico; la versión del **catálogo de datos** es independiente de
la del paquete y sigue el esquema `AÑO.revisión`.

## [0.1.0] — 2026-09-22

Primera versión. Puerto a Python del paquete R `geoperu`.

### Añadido

- `obtener_geo_peru()` y `obtener_anp_peru()`, equivalentes a
  `get_geo_peru()` y `get_anp_peru()`.
- Conveniencias orientadas al caso de uso real: `obtener_distritos()`,
  `obtener_distrito()`, `obtener_provincia()`, `obtener_departamento()`.
- Lector de GeoPackage con `sqlite3` de la biblioteca estándar, incluido el
  desempacado del encabezado binario de geometría GPKG.
- Lector de WKB propio: WKB estándar, variante ISO con Z/M y banderas de
  EWKB. Salida como GeoJSON, WKT o WKB crudo.
- Catálogo congelado dentro del paquete: 444 entradas de límites y 272 áreas
  naturales protegidas (versión `2026.1`).
- Caché en disco con escritura atómica y huella SHA-256.
- Procedencia por colección (URL, versión de catálogo, huella, fecha), para
  manifiestos de reproducibilidad.
- Transporte HTTP inyectable con `establecer_transporte()`, para usar
  `QgsBlockingNetworkRequest` dentro de QGIS y respetar el proxy del usuario.
- Excepciones tipadas, con sugerencias ante nombres mal escritos y error
  explícito ante unidades homónimas.
- Interfaz de línea de comandos: `info`, `listar`, `descargar`, `catalogo`,
  `limpiar-cache`.
- 123 pruebas sin red y 4 pruebas marcadas contra los servidores reales.

### Divergencias respecto al paquete de R

- **Diéresis.** `normalizar_texto()` de `peruocc` traduce «Ü» a «D» por un
  desliz en su tabla de reemplazo; aquí se normaliza a «U». Ninguna unidad
  administrativa del Perú lleva diéresis, así que no afecta ningún resultado.
- **URLs normalizadas.** El catálogo de origen publica rutas
  `github.com/…/raw/…`, que responden con una redirección. El catálogo
  congelado las guarda ya apuntando a `raw.githubusercontent.com`: ahorra un
  salto y funciona en entornos donde la redirección se bloquea.
- **Homónimos.** Ante un nombre que corresponde a varias unidades se lanza
  `UnidadAmbigua` en lugar de devolver la primera coincidencia.
- **Sin operaciones geométricas.** No hay unión, intersección ni
  reproyección: exigirían GEOS o PROJ. El origen ya publica los polígonos
  disueltos, que es para lo que `geoperu` usaba `st_union()`.
