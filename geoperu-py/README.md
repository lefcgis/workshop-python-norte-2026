# geoperu-py

Límites administrativos y áreas naturales protegidas del Perú, en Python,
**sin dependencias externas**.

Puerto del paquete R [`geoperu`](https://github.com/PaulESantos/geoperu) de
Paul E. Santos Andrade. Entrega los mismos datos oficiales —INEI para límites
administrativos, SERNANP para áreas protegidas— usando solo la biblioteca
estándar de Python.

## Por qué existe

`geoperu` resuelve muy bien un problema real: obtener el polígono oficial de
un distrito peruano sin pelearse con descargas ni con formatos. Pero está en
R, y hay flujos donde R no puede entrar: un plugin de QGIS, un servidor sin
GDAL, un cuaderno de Python.

La restricción de **cero dependencias** es el punto del paquete, no un
capricho. Un GeoPackage es una base SQLite con convenciones OGC, así que
`sqlite3` alcanza para leerlo; lo único no obvio es el encabezado binario de
las geometrías, y eso son cien líneas. A cambio, el paquete se puede copiar
dentro de un plugin de QGIS y funcionar sin pedirle a nadie un `pip install`
—que en entornos institucionales, con permisos y redes restringidas, es la
razón principal por la que una herramienta no se adopta.

## Instalación

```bash
pip install geoperu-py
```

O, para incrustarlo en un plugin, copiar `src/geoperu/` dentro del proyecto.
No hay nada más que instalar.

## Uso

```python
import geoperu

# Los 84 distritos de Amazonas, con geometría completa
distritos = geoperu.obtener_distritos("Amazonas")
print(len(distritos), distritos.campos)
# 84 ('departamento', 'provincia', 'distrito', 'capital')

# Un distrito, ya desambiguado
rasgo = geoperu.obtener_distrito("Chachapoyas", departamento="Amazonas")
print(rasgo.a_wkt()[:40])      # 'MULTIPOLYGON (((-77.8382227 -6.2102007…'
print(rasgo.bbox())            # (-77.94, -6.30, -77.76, -6.18)

# El polígono provincial disuelto
provincia = geoperu.obtener_provincia("Chachapoyas", departamento="Amazonas")

# Área natural protegida
manu = geoperu.obtener_anp_peru("Manu")

# Escribir a GeoJSON
import json
json.dump(distritos.a_geojson(), open("amazonas.geojson", "w"))
```

### Equivalencia con el paquete de R

```python
geoperu.obtener_geo_peru(geografia="ANTA", nivel="prov", simplificado=True)
```

```r
geoperu::get_geo_peru(geography = "ANTA", level = "prov", simplified = TRUE)
```

Los niveles aceptan tanto los códigos de R (`all`, `dep`, `prov`) como sus
nombres en español (`nacional`, `departamento`, `provincia`), para que el
código escrito contra el paquete original siga leyéndose igual.

### `simplificado` no significa «de menor calidad»

Es la distinción más importante de la API, y viene del origen de los datos:

| | qué devuelve | filas | campos |
|---|---|---|---|
| `simplificado=True` | el polígono **disuelto** de la unidad | 1 | el nombre de la unidad |
| `simplificado=False` | los **distritos** que la componen | *n* | `departamento`, `provincia`, `distrito`, `capital` |

Gracias a eso el paquete nunca necesita disolver geometrías: el polígono
provincial ya viene disuelto desde el origen. Es lo que permite no depender
de GEOS.

## Interfaz de línea de comandos

```bash
geoperu info                                        # versión, catálogo, cobertura
geoperu listar --nivel dep                          # los 25 departamentos
geoperu listar --nivel prov --departamento Cusco    # provincias de Cusco
geoperu listar --nivel anp                          # áreas protegidas
geoperu descargar --geografia Amazonas --nivel dep --completo -s amazonas.geojson
geoperu limpiar-cache
```

## Uso dentro de QGIS

Dos ajustes y funciona igual:

```python
from qgis.core import QgsBlockingNetworkRequest, QgsGeometry
from qgis.PyQt.QtCore import QUrl, QByteArray
from qgis.PyQt.QtNetwork import QNetworkRequest
import geoperu

def transporte_qgis(url, tiempo_limite):
    """Usa la pila de red de QGIS para respetar el proxy del usuario."""
    peticion = QNetworkRequest(QUrl(url))
    peticion.setRawHeader(b"User-Agent", b"mi-plugin/1.0")
    bloqueante = QgsBlockingNetworkRequest()
    if bloqueante.get(peticion) != QgsBlockingNetworkRequest.NoError:
        raise geoperu.ErrorDescarga(bloqueante.errorMessage())
    return bytes(bloqueante.reply().content())

geoperu.establecer_transporte(transporte_qgis)   # respeta el proxy configurado
geoperu.directorio_cache()                        # o fijar GEOPERU_CACHE

rasgo = geoperu.obtener_distrito("Miraflores", departamento="Lima")
geometria = QgsGeometry()
geometria.fromWkb(QByteArray(rasgo.wkb))          # sin reconvertir a texto
```

`QgsBlockingNetworkRequest` bloquea, así que va dentro de un `QgsTask`, nunca
en el hilo principal de la interfaz.

El paquete entrega el **WKB crudo** además de GeoJSON y WKT precisamente para
esto: `QgsGeometry.fromWkb()` no paga ninguna conversión intermedia.

## Trazabilidad

Cada colección trae la procedencia de sus datos, lista para un manifiesto de
reproducibilidad:

```python
col = geoperu.obtener_distritos("Amazonas")
col.procedencia[0].a_dict()
# {'url': 'https://raw.githubusercontent.com/…/dep_amazonas.gpkg',
#  'version_catalogo': '2026.1',
#  'sha256': '455475075191…',
#  'bytes_archivo': 618496,
#  'descargado_en_utc': '2026-09-22T03:22:02+00:00',
#  'desde_cache': False}
```

Quien arme un expediente técnico, una línea base ambiental o una tesis
necesita poder declarar de dónde salió cada cifra. Por eso la procedencia no
es un extra opcional.

## El catálogo y la revisión anual

El paquete lleva un **catálogo congelado** (`src/geoperu/datos/catalogo_*.json`)
con las 444 entradas de límites y las 272 áreas protegidas, y sus URLs ya
normalizadas al host de contenido crudo.

Está congelado a propósito. Los límites oficiales cambian poco, mientras que
resolver el catálogo remoto en cada ejecución haría que un cambio ajeno
rompiera a todos los consumidores a la vez y sin aviso.

La revisión anual es deliberadamente simple:

```bash
python -m geoperu catalogo --refrescar --version 2027.1 \
    --guardar src/geoperu/datos/catalogo_2027.json
pytest -m red          # confirma que el origen sigue vigente
```

El paquete usa siempre el catálogo más reciente de los que incluye. La acción
`.github/workflows/actualizar-catalogo.yml` corre esa comprobación cada año y
abre un *pull request* si algo cambió.

## Caché

Los archivos se guardan una sola vez en disco. La ubicación se controla con
`GEOPERU_CACHE`; por omisión usa el directorio de caché del sistema
(`~/.cache/geoperu`, `%LOCALAPPDATA%\geoperu`, `~/Library/Caches/geoperu`).

La escritura es atómica —se baja a un temporal y se renombra— para que una
descarga interrumpida no deje un archivo truncado que la siguiente ejecución
lea como si estuviera completo.

## Pruebas

```bash
pytest                 # 123 pruebas, ninguna toca la red
pytest -m red          # 4 pruebas contra los servidores reales
```

La suite por defecto no usa la red por decisión explícita: una prueba que
dependa de un servidor externo falla los días que ese servidor está lento, y
una prueba que falla por motivos ajenos al código se acaba ignorando —y con
ella, toda la suite. Los GeoPackages de prueba se construyen con `sqlite3` en
el momento.

Una de las pruebas recorre el árbol del paquete con `ast` y falla si algún
módulo importa algo fuera de la biblioteca estándar. Es la guardia de la
restricción que da sentido al proyecto.

## Alcance

**Sí:** descargar límites administrativos (nacional, departamento, provincia,
distrito) y áreas naturales protegidas; leerlos; entregarlos como WKB,
GeoJSON o WKT; filtrar por atributos; caché; trazabilidad.

**No:** operaciones geométricas (unión, intersección, simplificación,
reproyección). Eso necesita GEOS o PROJ y rompería la premisa de cero
dependencias. Quien las necesite las tiene en QGIS, en `shapely` o en GDAL;
este paquete entrega geometría en formatos que todos ellos leen directamente.

## Créditos

- Paquete original en R: [`geoperu`](https://github.com/PaulESantos/geoperu),
  de **Paul E. Santos Andrade** (ORCID
  [0000-0002-6635-0375](https://orcid.org/0000-0002-6635-0375)), MIT.
- Datos de límites: **INEI** — <https://ide.inei.gob.pe/>, distribuidos a
  través de [`perugeopkg`](https://github.com/PaulESantos/perugeopkg).
- Áreas naturales protegidas: **SERNANP**.

Este paquete no redistribuye los datos: los descarga del mismo origen que el
paquete de R y conserva la atribución.

## Licencia

MIT. Ver [LICENSE](LICENSE).
