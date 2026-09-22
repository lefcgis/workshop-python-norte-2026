---
name: exportacion-trazable
description: Exportación y trazabilidad de una corrida de peru_occ — CSV y GeoJSON diff-comparables contra peruocc, manifiesto JSON de reproducibilidad, generación de run_id y resumen de resultados. Úsala al tocar nucleo/exportacion.py, nucleo/manifiesto.py o nucleo/esquema.py. Actívala ante exportar, CSV, GeoJSON, manifiesto, run_id, schema_version, reproducibilidad, trazabilidad, resumen, esquema de 24 campos.
---

# Exportación y trazabilidad

## El esquema es un contrato, no una sugerencia

Los 24 campos, sus tipos y **su orden** están en
`plugin-qgis/contratos/esquema_ocurrencias.json`. El criterio de aceptación es que

```bash
head -1 salida_plugin.csv
head -1 ocurrencias_miraflores_flora_20260817.csv   # referencia de peruocc
```

produzcan la **misma línea**. Nombres Darwin Core en inglés, aunque la UI esté en
español.

Dos campos merecen cuidado al escribir DDL o acceder por atributo: `class` es
palabra reservada de Python, y `order` lo es de SQL (hay que citarla en un
GeoPackage).

## Los tres formatos y su asimetría deliberada

| Formato | Contenido | Regla |
|---|---|---|
| CSV | **todas** las filas | Conserva registros sin coordenadas: son evidencia taxonómica válida |
| GeoJSON | solo filas con lat/lon finitos | Un *feature* sin geometría no es representable |
| Manifiesto JSON | metadatos de la corrida | Nunca contiene las ocurrencias |

Esa asimetría es de `peruocc` y se replica: si CSV y GeoJSON tienen distinto número
de filas, **no es un error**, y el manifiesto debe dejarlo explícito.

## `run_id`

Patrón de `peruocc`: `%Y%m%dT%H%M%SZ_<nivel>_<unidad>_<grupo>`, en UTC.

```python
def generar_run_id(nivel: str, unidad: str, grupo: str | None) -> str:
    sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    u = normalizar_texto(unidad).lower().replace(" ", "_")
    g = (grupo or "biodiversidad").lower()
    return f"{sello}_{nivel}_{u}_{g}"
```

UTC, no hora local: dos corridas en husos distintos deben ordenarse
correctamente. Los tres archivos de una corrida comparten el mismo `run_id` como
prefijo — es lo que los mantiene juntos en un directorio con cien salidas.

## Manifiesto

Estructura de `escribir_manifiesto()`, replicada llave por llave:

```json
{
  "schema_version": "1.0",
  "run_id": "20260922T143012Z_distrito_miraflores_flora",
  "executed_at_utc": "2026-09-22 14:30:12 UTC",
  "parameters": {
    "nivel": "distrito", "nombre": "Miraflores", "departamento": "Lima",
    "provincia": "Lima", "nombre_cientifico": null, "grupo": "flora",
    "limite_por_api": 500, "tolerancia_simplificacion": 100,
    "estrategia_espacial": "auto", "max_area_ha": 1000, "max_lotes": 16
  },
  "spatial": {
    "crs": "EPSG:4326",
    "polygon_wkt": "POLYGON ((…))",
    "estrategia_wkt": "simplificada",
    "lotes_espaciales": 3
  },
  "result_summary": {
    "nivel": "distrito", "unidad": "MIRAFLORES",
    "distrito": "MIRAFLORES", "provincia": "LIMA", "department": "LIMA",
    "total_registros": 412, "registros_gbif": 388, "registros_inat": 24,
    "limite_por_api": 500,
    "gbif_total_reportado_api": 401, "inat_total_reportado_api": 26,
    "gbif_descarga_completa_api": false, "inat_descarga_completa_api": false,
    "lotes_espaciales": 3, "fallos_lotes": 0,
    "descartados_fuera_del_limite": 15
  },
  "files": { "csv": "…", "geojson": "…", "manifiesto": "…" },
  "runtime": {
    "qgis_version": "3.44.1-Solothurn",
    "python_version": "3.12.x",
    "plugin_version": "0.1.0",
    "plataforma": "…"
  }
}
```

Diferencias legítimas respecto a R, y por qué:

- `runtime` reporta versiones de QGIS/Python/plugin en lugar de `r_version` y
  paquetes de R. Es la misma intención: identificar el entorno que produjo la cifra.
- `spatial.estrategia_wkt` y `result_summary.descartados_fuera_del_limite` son
  **añadidos**. El primero avisa de que se consultó por bbox (más falsos positivos);
  el segundo cuantifica cuántos eliminó el filtro exacto. Ambos hacen auditable el
  paso que da confiabilidad al producto, y `peruocc` no los expone.

Todo añadido al manifiesto se documenta aquí y en la matriz de paridad. Un campo
nuevo sin explicar es lo que convierte un manifiesto en ruido.

## Escritura del CSV

```python
import csv

with open(ruta, "w", newline="", encoding="utf-8") as fh:
    escritor = csv.DictWriter(fh, fieldnames=[c.nombre for c in ESQUEMA],
                              extrasaction="raise")   # falla si aparece un campo intruso
    escritor.writeheader()
    escritor.writerows(resultado.ocurrencias)
```

`newline=""` evita las líneas en blanco intercaladas en Windows, que es donde está
la mayoría de los usuarios de QGIS en el sector público. `encoding="utf-8"` sin BOM,
como R. `extrasaction="raise"` convierte una divergencia de esquema en un error
inmediato en lugar de una columna perdida.

## Directorio de salidas

`peruocc_data_dir()` se traduce a una preferencia persistente:

```python
from qgis.core import QgsSettings
QgsSettings().setValue("peru_occ/directorio_datos", ruta)
```

Subdirectorios como en el paquete: `cache/` para límites y respuestas crudas,
`processed/` para las salidas de cada corrida.
