# Convenciones del repositorio

Aula virtual de geoprocesamiento en la Amazonía (`estudiantes/`, `docentes/`,
`dados/`) más un sistema de agentes para construir un plugin de QGIS
(`plugin-qgis/`, `.claude/`).

## Idioma

- Documentación, comentarios de código, mensajes de interfaz y de error: **español
  latinoamericano**. El material existente incluye portugués de Brasil; al tocar un
  archivo, respeta el idioma en que ya está escrito.
- **Los nombres de campo del esquema de ocurrencias no se traducen.** Son Darwin
  Core, un estándar internacional: `scientificName`, `decimalLatitude`,
  `basisOfRecord`. Se explica el estándar, no se oculta.
- Los identificadores de código van en español sin tildes ni eñes
  (`preparar_lotes`, `filtrar_dentro`), salvo cuando replican un nombre de la API
  externa.

## Plugin QGIS (`plugin-qgis/`)

Puerto a QGIS del paquete R **`peruocc`** de Paul E. Santos Andrade
(ORCID 0000-0002-6635-0375). Antes de tocar nada:

| Archivo | Qué contiene |
|---|---|
| `plugin-qgis/ANALISIS_NEGOCIO.md` | qué se construye, para quién, y los riesgos R1–R7 |
| `plugin-qgis/ARQUITECTURA.md` | módulos, flujo de una corrida, hitos H1–H7 |
| `plugin-qgis/contratos/paridad_peruocc.md` | matriz de paridad: dueño y evidencia por fila |
| `plugin-qgis/contratos/esquema_ocurrencias.json` | los 24 campos, tipos y orden estricto |
| `plugin-qgis/contratos/parametros_defecto.json` | valores por defecto y techos de API |

Los archivos de `contratos/` **no se modifican sin acuerdo del orquestador**.

### Reglas técnicas no negociables

1. **Entorno objetivo**: QGIS 3.44 LTR, Qt5/PyQt5, Python 3.12.
2. **Cero dependencias externas**: solo la biblioteca estándar de Python y la API
   de QGIS/Qt. Sin `requests`, `shapely`, `geopandas`, `pandas`. Un `pip install`
   dentro de QGIS es inviable en entornos institucionales.
3. **Todo `import` de Qt pasa por `qgis.PyQt.*`**, nunca `import PyQt5` directo:
   es lo que permitirá sobrevivir al salto a Qt6 de QGIS 4.0.
4. **`nucleo/` no conoce Qt Widgets ni `iface`.** Así el diálogo y el algoritmo
   Processing comparten una sola implementación y no divergen en sus resultados.
5. **Nada de red ni de geometría pesada en el hilo principal**: siempre dentro de
   un `QgsTask`.
6. **El doble filtro**: se consulta a la API con el polígono simplificado y se
   filtra contra el **polígono detallado original**. Nunca al revés.
7. **Nunca truncar en silencio**: al superar el techo de una API se aborta con un
   mensaje que dice qué hacer.

## Sistema de agentes (`.claude/`)

- `.claude/agents/` — 1 orquestador + 8 especialistas.
- `.claude/skills/` — 8 paquetes de conocimiento reutilizable.
- `.claude/commands/peruocc-qgis.md` — punto de entrada: `/peruocc-qgis <hito|estado>`.

Detalle del reparto y del protocolo de trabajo en `.claude/README.md`.

## Créditos y fuentes

Paquete `peruocc` (MIT) de Paul E. Santos Andrade. Datos de GBIF, iNaturalist e
INEI (vía `geoperu`). Cualquier material derivado mantiene estos créditos: es
honestidad académica y es lo que el usuario necesita para citar.
