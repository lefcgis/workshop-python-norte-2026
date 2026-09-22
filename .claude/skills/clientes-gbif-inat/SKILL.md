---
name: clientes-gbif-inat
description: Clientes REST en Python puro (sin requests) para la API de ocurrencias de GBIF y la API v1 de iNaturalist, replicando lo que hacen rgbif y rinat en el paquete peruocc. Úsala al implementar paginación, conteo previo, resolución taxonómica, reintentos con backoff, rate limiting, User-Agent, caché de consultas o el mapeo de campos crudos al esquema Darwin Core. Actívala ante GBIF, occ_search, name_backbone, taxonKey, kingdomKey, iNaturalist, get_inat_obs, quality_grade, bbox, paginación, 429, Retry-After.
---

# Clientes GBIF e iNaturalist sin dependencias externas

## Transporte: `QgsBlockingNetworkRequest`, no `urllib`

Se usa la pila de red de QGIS porque respeta el **proxy configurado por el
usuario** en las opciones de QGIS — condición indispensable en redes
institucionales, que es donde vive el usuario objetivo.

```python
from qgis.core import QgsBlockingNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
from qgis.PyQt.QtNetwork import QNetworkRequest
import json

def _get_json(url_base: str, params: dict) -> dict:
    consulta = QUrlQuery()
    for clave, valor in params.items():
        if valor is None:
            continue                      # no enviar parámetros vacíos
        if isinstance(valor, bool):
            valor = "true" if valor else "false"
        consulta.addQueryItem(clave, str(valor))

    url = QUrl(url_base)
    url.setQuery(consulta)

    peticion = QNetworkRequest(url)
    peticion.setRawHeader(b"User-Agent", b"QGIS-peru_occ/0.1.0 (+<url del repo>)")
    peticion.setRawHeader(b"Accept", b"application/json")

    bloqueante = QgsBlockingNetworkRequest()
    codigo = bloqueante.get(peticion)
    if codigo != QgsBlockingNetworkRequest.NoError:
        raise ErrorRed(bloqueante.errorMessage())
    return json.loads(bytes(bloqueante.reply().content()).decode("utf-8"))
```

`QgsBlockingNetworkRequest` **bloquea**: solo puede llamarse desde el hilo de un
`QgsTask`, nunca desde el hilo principal de la UI.

El `User-Agent` identificable no es cortesía: iNaturalist limita o bloquea
clientes anónimos.

## GBIF

### Resolución taxonómica (equivale a `rgbif::name_backbone`)

```
GET https://api.gbif.org/v1/species/match?name=<nombre>
→ { "usageKey": 3084370, "scientificName": "...", "rank": "GENUS",
    "matchType": "EXACT" | "FUZZY" | "HIGHERRANK" | "NONE" }
```

Lógica de `peruocc`, a replicar exactamente:
`matchType != "NONE"` ⇒ usar `taxonKey = usageKey`. Si es `"NONE"` ⇒ **no abortar**:
caer a `scientificName = <texto libre>` en la consulta de ocurrencias. Si el
resolutor no responde ⇒ advertir y continuar por texto libre.

### Ocurrencias (equivale a `rgbif::occ_search`)

```
GET https://api.gbif.org/v1/occurrence/search
    geometry=<WKT>            # polígono CCW, ≤1500 caracteres
    hasCoordinate=true
    taxonKey=<usageKey>       # si se resolvió
    kingdomKey=<6|1>          # flora=6 (Plantae), fauna=1 (Animalia)
    scientificName=<texto>    # solo como fallback si no hubo taxonKey
    limit=<≤300>              # 300 es el máximo por página
    offset=<n>                # offset + limit ≤ 100000
→ { "count": 1234, "endOfRecords": false, "results": [ … ] }
```

**Conteo previo.** Con `limit=0` la respuesta trae `count` sin registros. Es lo que
`peruocc` usa cuando `limite = NULL`: si `count > 100000`, **aborta** e indica que
corresponde una descarga citable (`occurrence/download`), no paginación.

**Paginación.** Acumular por `offset` hasta `endOfRecords` o hasta alcanzar el
límite pedido. Comprobar cancelación **entre páginas**.

### Mapeo GBIF → esquema

| Campo del esquema | Campo GBIF |
|---|---|
| `occurrenceID`, `sourceRecordID` | `key` |
| `sourceURL` | `https://www.gbif.org/occurrence/<key>` |
| `datasetKey`, `license`, `basisOfRecord` | homónimos |
| `scientificName`, `taxonRank`, `kingdom`, `phylum`, `class`, `order`, `family`, `genus`, `species` | homónimos |
| `decimalLatitude`, `decimalLongitude` | homónimos |
| `eventDate` | `eventDate` (texto: GBIF entrega fechas parciales) |
| `recordedBy`, `coordinateUncertaintyInMeters` | homónimos |
| `source` | literal `"GBIF"` |

Los campos GBIF ausentes se rellenan con vacío/`None` según el tipo del contrato.
**Nunca** se omite una columna.

## iNaturalist

### Observaciones (equivale a `rinat::get_inat_obs`)

```
GET https://api.inaturalist.org/v1/observations
    swlat=<ymin>&swlng=<xmin>&nelat=<ymax>&nelng=<xmax>
    geo=true
    quality_grade=research          # "calidad" por defecto en peruocc
    taxon_name=<Plantae|Animalia|taxón>
    q=<texto libre>                 # opcional
    per_page=<≤200>
    page=<n>                        # page*per_page ≤ 10000
→ { "total_results": 987, "results": [ … ] }
```

**El bbox es la trampa principal.** `rinat` recibe
`bounds = c(ymin, xmin, ymax, xmax)` — (S, W, N, E). Al traducirlo:
`swlat=ymin`, `swlng=xmin`, `nelat=ymax`, `nelng=xmax`. Invertir el orden devuelve
registros de otro lugar del país **sin error visible**.

**Techo.** `total_results > 10000` ⇒ abortar con mensaje accionable (exportación
oficial de iNaturalist, o partir la consulta por periodos). Para pasar de 10 000 la
vía correcta es paginar por `id_above`, no por `page`.

**Rate limit.** ~60 peticiones/minuto. Mantener `pausa_entre_lotes_s = 0.2` y
respetar la cabecera `Retry-After` cuando llega un 429.

### Mapeo iNaturalist → esquema

| Campo del esquema | Origen en iNaturalist |
|---|---|
| `occurrenceID`, `sourceRecordID` | `id` |
| `sourceURL` | `uri`, o `https://www.inaturalist.org/observations/<id>` |
| `scientificName`, `taxonRank` | `taxon.name`, `taxon.rank` |
| `kingdom`…`species` | derivar de `taxon.ancestors[]` por `rank` |
| `decimalLatitude/Longitude` | `geojson.coordinates` **[lon, lat]** o `location` `"lat,lon"` |
| `eventDate` | `observed_on_string` / `observed_on` |
| `recordedBy` | `user.login` o `user.name` |
| `coordinateUncertaintyInMeters` | `positional_accuracy` |
| `license` | `license_code` |
| `basisOfRecord` | literal `"HUMAN_OBSERVATION"` |
| `datasetKey` | vacío |
| `source` | literal `"iNaturalist"` |

Ojo con el orden de coordenadas: `geojson.coordinates` es **[lon, lat]**,
mientras que `location` es la cadena **"lat,lon"**. Son órdenes opuestos.

Las observaciones **oscurecidas o privadas** (`geoprivacy`) traen coordenadas
desplazadas o nulas. Descartar las nulas y no tratar el desplazamiento como error.

## Reintentos (equivale a `ejecutar_con_reintentos`)

```
reintentos = 3, pausa_inicial = 0.5 s, backoff exponencial (0.5 → 1 → 2)
```

- Reintentar: errores de red, 429, 500, 502, 503, 504.
- **No** reintentar: 400 y 404 — son errores de la consulta (WKT inválido, parámetro
  mal formado) y reintentar solo pierde tiempo.
- En 429, si hay `Retry-After`, esa cabecera manda sobre el *backoff*.
- Comprobar cancelación del `QgsTask` entre intentos.

## Caché de consultas

`peruocc` cachea por lote con una clave derivada de todos los parámetros
(`nombre_seguro_cache`). Replicar: clave = hash de (nivel, nombre, departamento,
taxón, grupo, límite, área máx., lotes máx., tolerancia, estrategia) + `tile_id`.
Guardar el JSON crudo de la respuesta, no el resultado ya procesado: así un cambio
en el mapeo no obliga a volver a descargar.

## Antes de publicar

Los endpoints y techos de este documento y de
`plugin-qgis/contratos/parametros_defecto.json` deben **revalidarse contra la
documentación viva** de GBIF e iNaturalist, y el resultado de esa verificación
debe quedar por escrito en el reporte del agente.
