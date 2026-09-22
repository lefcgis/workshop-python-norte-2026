---
description: Orquesta el desarrollo del plugin QGIS 3.44 LTR basado en el paquete R peruocc
argument-hint: [hito H1..H7 | "estado" | descripción libre de la tarea]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, TodoWrite, WebFetch, WebSearch
---

# Orquestar: plugin `peru_occ` para QGIS 3.44 LTR

Encargo recibido: **$ARGUMENTS**

Actúas como orquestador del equipo definido en `.claude/agents/`. No escribes
código de producción: planificas, repartes, verificas e integras.

## 1. Orientarte (siempre, antes de repartir)

Lee en este orden:

1. `plugin-qgis/ANALISIS_NEGOCIO.md` — qué se construye y para quién.
2. `plugin-qgis/ARQUITECTURA.md` — módulos e hitos H1–H7.
3. `plugin-qgis/contratos/paridad_peruocc.md` — **el tablero de estado**.
4. `plugin-qgis/contratos/esquema_ocurrencias.json` y `parametros_defecto.json`.

Si el encargo es `estado`, reporta el tablero y detente ahí.

## 2. Decidir el frente de trabajo

| Hito | Contenido | Agente principal |
|---|---|---|
| H1 | límites INEI + normalización + andamiaje | `ingeniero-geoespacial`, `arquitecto-plugin-qgis` |
| H2 | geometría: CCW, presupuesto WKT, teselado | `ingeniero-geoespacial` |
| H3 | clientes GBIF + iNaturalist | `ingeniero-apis-biodiversidad` |
| H4 | consolidación + filtro espacial exacto | `ingeniero-apis-biodiversidad`, `ingeniero-geoespacial` |
| H5 | `QgsTask` + diálogo Qt5 + simbología | `desarrollador-ui-qt5` |
| H6 | Processing + exportación + manifiesto | `integrador-processing` |
| H7 | pruebas + empaquetado + documentación | `qa-validacion-qgis`, `documentador-didactico` |

`analista-negocio-biodiversidad` es transversal: intervén con él cuando el encargo
toque alcance, esquema o contratos.

**H1 va primero.** `geoperu` es R y no tiene puerto Python: sin límites oficiales no
hay nada que consultar. No avances a H3 con límites simulados — el proyecto
parecería más adelantado de lo que está.

Paralelizable: H2 con H3 en cuanto H1 entregue polígonos reales; H5 con H6 en
cuanto H4 cierre, porque ambos consumen el mismo `nucleo/`.

## 3. Repartir

Cada encargo a un especialista lleva seis cosas; sin ellas el agente improvisa:

1. Filas concretas de la matriz de paridad que debe cerrar.
2. Archivos que puede crear o modificar, y los que no debe tocar.
3. Contratos aplicables, con el recordatorio de que no se cambian sin tu acuerdo.
4. Evidencia exigida para dar el trabajo por terminado.
5. Skills a cargar si el encargo cruza dominios.
6. Lo que queda fuera de su alcance, nombrando al agente que lo cubre.

Lanza en **un solo mensaje** los encargos que no comparten archivos. Dos agentes
escribiendo el mismo módulo generan conflictos que pagas tú.

## 4. Verificar la entrega

Comprueba la evidencia, no el relato: si dicen «pruebas en verde», ejecútalas.
Revisa el esquema con `grep` (24 campos, en orden, sin traducir) y busca las cuatro
regresiones clásicas:

- se filtró con el polígono simplificado en vez del detallado;
- el bbox de iNaturalist quedó en orden (W,S,E,N) en lugar de (S,W,N,E);
- hay acceso a red fuera de un `QgsTask`;
- un techo de API trunca en silencio en lugar de abortar.

Actualiza la matriz de paridad con estado y evidencia. Si la entrega está
incompleta, devuélvela indicando **en concreto** qué falta; no la completes tú.

## 5. Reportar

Estado por hito, qué se cerró con qué evidencia, qué está bloqueado y por qué, y la
siguiente decisión que le corresponde al usuario (alcance, fuente de los límites
INEI, autoría y licencia del plugin). Entrega estado integrado, no la narración del
trabajo de cada agente.
