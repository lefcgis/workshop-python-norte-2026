---
name: geometria-peruocc
description: Operaciones geométricas del flujo peruocc reimplementadas con PyQGIS sin shapely ni geopandas — orientación CCW de anillos, simplificación métrica adaptativa en UTM, presupuesto de caracteres del WKT para GBIF, teselado adaptativo por área en hectáreas, disolución de provincias y filtro espacial exacto con índice espacial. Úsala al tocar nucleo/geometria.py, nucleo/limites.py o nucleo/validacion_espacial.py. Actívala ante CCW, WKT, simplificar, tolerancia, UTM, EPSG 32718, teselado, tile, st_intersects, QgsSpatialIndex, disolver, bounding box, área en hectáreas.
---

# Geometría del flujo `peruocc` en PyQGIS

Reemplaza `sf` por `QgsGeometry`. Sin `shapely`, sin `geopandas`.

## 1. Zona UTM automática (clave: medir en metros, no en grados)

`peruocc` calcula la zona UTM desde el centroide y trabaja allí. Simplificar o
medir áreas en EPSG:4326 da resultados sin sentido físico.

```python
def epsg_utm_desde_centroide(centroide_4326) -> int:
    lon, lat = centroide_4326.x(), centroide_4326.y()
    zona = max(1, min(60, int((lon + 180) // 6) + 1))
    return (32700 if lat < 0 else 32600) + zona   # 327xx = sur, 326xx = norte
```

Perú es hemisferio sur, zonas 17S/18S/19S ⇒ EPSG:32717 / 32718 / 32719.
La fórmula se mantiene genérica para replicar exactamente la de R.

```python
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject

def transformar(geom, epsg_origen: int, epsg_destino: int):
    tr = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem(f"EPSG:{epsg_origen}"),
        QgsCoordinateReferenceSystem(f"EPSG:{epsg_destino}"),
        QgsProject.instance().transformContext(),
    )
    g = QgsGeometry(geom)
    g.transform(tr)
    return g
```

## 2. Orientación CCW (OGC / GBIF)

GBIF interpreta un polígono con anillo horario como su complemento: en lugar del
distrito, «todo el planeta menos el distrito». El síntoma no es un error, es un
conteo absurdamente alto.

```python
def forzar_ccw(geom: QgsGeometry) -> QgsGeometry:
    g = QgsGeometry(geom)
    g.normalize()                 # QGIS ≥3.20: anillo exterior CCW, interiores CW
    return g
```

Verificación explícita cuando haga falta: el área firmada del anillo exterior
(fórmula del zapatero) debe ser **positiva**; si es negativa, invertir el orden de
los vértices. Aplicar **siempre** antes de emitir el WKT hacia GBIF.

## 3. Presupuesto de WKT (equivale a `simplificar_para_api`)

GBIF rechaza geometrías demasiado largas. La cascada de `peruocc`:

```python
WKT_MAX_CHAR = 1500
TOL_INICIAL_M = 100
FACTOR = 3
MAX_ITER = 6

def wkt_para_api(geom_4326: QgsGeometry) -> tuple[str, str]:
    """Devuelve (wkt, estrategia) con estrategia en {'directa','simplificada','bbox'}."""
    wkt = geom_4326.asWkt()
    if len(wkt) <= WKT_MAX_CHAR:
        return forzar_ccw(geom_4326).asWkt(), "directa"

    epsg = epsg_utm_desde_centroide(geom_4326.centroid().asPoint())
    tol = TOL_INICIAL_M
    for _ in range(MAX_ITER):
        en_utm = transformar(geom_4326, 4326, epsg)
        simplificada = transformar(en_utm.simplify(tol), epsg, 4326)  # tolerancia EN METROS
        wkt_s = forzar_ccw(simplificada).asWkt()
        if len(wkt_s) <= WKT_MAX_CHAR:
            return wkt_s, "simplificada"
        tol *= FACTOR                     # 100 → 300 → 900 → 2700 → 8100 → 24300
    # Último recurso, igual que peruocc: el bounding box
    return forzar_ccw(QgsGeometry.fromRect(geom_4326.boundingBox())).asWkt(), "bbox"
```

Registrar la estrategia usada en el manifiesto: `"bbox"` significa que la consulta
trajo falsos positivos que el filtro exacto tuvo que eliminar, y eso es información
que el usuario necesita para interpretar su corrida.

## 4. Teselado adaptativo (equivale a `dividir_poligono_por_area`)

```python
MAX_AREA_HA = 1000
MAX_LOTES = 16

def preparar_lotes(geom_4326: QgsGeometry) -> list[tuple[int, QgsGeometry]]:
    epsg = epsg_utm_desde_centroide(geom_4326.centroid().asPoint())
    en_utm = transformar(geom_4326, 4326, epsg)
    area_ha = en_utm.area() / 10000.0

    if area_ha <= MAX_AREA_HA:
        return [(1, geom_4326)]

    # El área del lote se estira para que el total no exceda MAX_LOTES
    area_lote_ha = max(MAX_AREA_HA, area_ha / MAX_LOTES)
    lado_m = (area_lote_ha * 10000.0) ** 0.5

    lotes, indice = [], 1
    for celda in _grilla_cuadrada(en_utm.boundingBox(), lado_m):
        if not celda.intersects(en_utm):
            continue
        parte = celda.intersection(en_utm)
        if parte.isEmpty():
            continue
        # La intersección puede producir GeometryCollection: quedarse con polígonos
        parte = _extraer_poligonos(parte)
        if parte is None or parte.isEmpty():
            continue
        lotes.append((indice, transformar(parte, epsg, 4326)))
        indice += 1
    return lotes
```

Los números importan: el nº de lotes debe **coincidir con el de R** para la misma
unidad (fila B4 de la matriz de paridad). `area_lote_ha = max(MAX_AREA_HA, area_ha /
MAX_LOTES)` es lo que evita generar cientos de peticiones en una provincia amazónica.

## 5. Provincia = disolución de sus distritos

```python
from qgis.core import QgsGeometry

def disolver(geometrias: list[QgsGeometry]) -> QgsGeometry:
    unida = QgsGeometry.unaryUnion(geometrias)
    if not unida.isGeosValid():
        unida = unida.makeValid()     # equivalente a sf::st_make_valid()
    return unida
```

Validar siempre después de disolver: los límites INEI traen polígonos con nodos
duplicados y anillos que se autointersectan, y una geometría inválida hace fallar el
filtro espacial más adelante, no aquí.

## 6. Filtro espacial exacto (equivale a `sf::st_intersects`)

**El paso que da confiabilidad al producto.** Se filtra contra el polígono
**detallado original**, nunca contra el simplificado ni contra el bbox.

```python
from qgis.core import QgsSpatialIndex, QgsFeature, QgsGeometry, QgsPointXY

def filtrar_dentro(registros: list[dict], poligono_detallado: QgsGeometry) -> list[dict]:
    partes = poligono_detallado.asGeometryCollection()
    indice = QgsSpatialIndex()
    por_id = {}
    for i, parte in enumerate(partes):
        f = QgsFeature(i)
        f.setGeometry(parte)
        indice.addFeature(f)
        por_id[i] = parte

    dentro = []
    for reg in registros:
        lon, lat = reg.get("decimalLongitude"), reg.get("decimalLatitude")
        if lon is None or lat is None:
            continue
        punto = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))
        # El índice descarta por bbox; la comprobación exacta sigue siendo necesaria
        for cand in indice.intersects(punto.boundingBox()):
            if por_id[cand].intersects(punto):
                dentro.append(reg)
                break
    return dentro
```

`QgsSpatialIndex.intersects()` devuelve **candidatos por bounding box**, no
resultados exactos. Omitir la comprobación `por_id[cand].intersects(punto)` es
exactamente el error que el doble filtro pretende evitar.

Con decenas de miles de puntos, `QgsGeometry.contains` repetido sobre un polígono
amazónico es lento: preparar el polígono una vez y reutilizarlo, como arriba.

## 7. Coordenadas: el orden cambia según la fuente

| Contexto | Orden |
|---|---|
| `QgsPointXY` | (x=lon, y=lat) |
| GeoJSON `coordinates` | [lon, lat] |
| `location` de iNaturalist | "lat,lon" |
| `bounds` de `rinat` | (ymin, xmin, ymax, xmax) = (S, W, N, E) |
| `QgsRectangle` | (xmin, ymin, xmax, ymax) = (W, S, E, N) |

Confundirlos no lanza excepción: devuelve puntos en el lugar equivocado. Toda
conversión entre estos formatos merece un test.
