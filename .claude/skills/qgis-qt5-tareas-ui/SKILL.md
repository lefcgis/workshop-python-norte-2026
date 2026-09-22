---
name: qgis-qt5-tareas-ui
description: Trabajo en segundo plano con QgsTask y construcción de interfaces Qt5/PyQt5 en plugins QGIS 3.44 — progreso, cancelación real, señales entre hilos, creación de capas en memoria, simbología QML y mensajes en la barra de QGIS. Úsala al tocar tareas/ o gui/, o cuando la UI se congele, una tarea muera silenciosamente o una capa no aparezca. Actívala ante QgsTask, QgsTaskManager, setProgress, isCanceled, hilo, thread, congelada, freeze, pyqtSignal, iface.messageBar, capa en memoria, QML, simbología.
---

# `QgsTask` y UI Qt5 en QGIS 3.44

## La regla de los hilos

| Corre en el hilo de fondo | Corre en el hilo principal |
|---|---|
| `run()`: red, geometría, consolidación | `finished()`: crear/cargar capas, tocar la UI |
| `QgsBlockingNetworkRequest` | `iface.messageBar()`, diálogos, `QgsProject.instance().addMapLayer()` |

Crear una capa o tocar un widget desde `run()` provoca cierres inesperados de QGIS
difíciles de diagnosticar, porque a veces funciona.

## Esqueleto de tarea

```python
from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal

class TareaBusqueda(QgsTask):
    # Señal para resultados intermedios. Las señales sí cruzan hilos con seguridad.
    lote_terminado = pyqtSignal(int, int)

    def __init__(self, parametros):
        super().__init__("Peru OCC: buscando ocurrencias", QgsTask.CanCancel)
        self.parametros = parametros
        self.resultado = None
        self.excepcion = None

    def run(self) -> bool:
        try:
            poligono, nombres = resolver_limite(self.parametros)
            lotes = preparar_lotes(poligono)
            registros = []

            for i, (tile_id, lote) in enumerate(lotes, start=1):
                if self.isCanceled():        # punto de cancelación: ENTRE lotes
                    return False
                registros += consultar_gbif(lote, self.parametros)
                registros += consultar_inat(lote, self.parametros)
                self.setProgress(i / len(lotes) * 90.0)
                self.lote_terminado.emit(i, len(lotes))

            if self.isCanceled():
                return False

            # El filtro exacto va contra el polígono DETALLADO, no contra los lotes
            registros = filtrar_dentro(registros, poligono)
            self.resultado = consolidar(registros, nombres, self.parametros)
            self.setProgress(100.0)
            return True

        except Exception as exc:             # noqa: BLE001 — la tarea no debe morir muda
            self.excepcion = exc
            QgsMessageLog.logMessage(f"{exc}", "Peru OCC", Qgis.Critical)
            return False

    def finished(self, resultado_ok: bool) -> None:
        # Hilo principal. Aquí sí se puede tocar la UI y el proyecto.
        if self.isCanceled():
            avisar("Búsqueda cancelada.", Qgis.Info)
            return
        if not resultado_ok:
            avisar(mensaje_accionable(self.excepcion), Qgis.Critical)
            return
        capa = crear_capa_puntos(self.resultado)
        aplicar_estilo(capa, "por_fuente.qml")
        QgsProject.instance().addMapLayer(capa)
        avisar(f"{self.resultado.resumen['total_registros']} registros cargados.",
               Qgis.Success)
```

Cuatro errores que este esqueleto evita:

1. **Guardar una referencia a la tarea.** `QgsApplication.taskManager().addTask(t)`
   no toma posesión de la referencia de Python; sin `self.tarea = t` el recolector
   de basura la destruye a mitad de corrida y la tarea «desaparece».
2. **Excepción tragada.** Si `run()` lanza y nadie captura, la tarea falla sin
   mensaje. Capturar, guardar y reportar en `finished()`.
3. **Cancelación cosmética.** `CanCancel` habilita el botón; solo `isCanceled()`
   consultado periódicamente lo hace efectivo. Y al cancelar **no se crea capa
   parcial**.
4. **Progreso que salta de 0 a 100.** Reservar el último 10 % para filtrado y
   consolidación, que en una provincia no son instantáneos.

```python
self.tarea = TareaBusqueda(parametros)      # ← la referencia es obligatoria
QgsApplication.taskManager().addTask(self.tarea)
```

## Capa de puntos en memoria con los 24 campos

```python
from qgis.core import QgsVectorLayer, QgsFields, QgsField, QgsFeature, QgsGeometry, QgsPointXY
from qgis.PyQt.QtCore import QVariant

def crear_capa_puntos(resultado) -> QgsVectorLayer:
    capa = QgsVectorLayer("Point?crs=EPSG:4326", resultado.nombre_capa, "memory")
    campos = QgsFields()
    for campo in ESQUEMA:                      # orden estricto del contrato
        campos.append(QgsField(campo.nombre, campo.tipo_qvariant))
    capa.dataProvider().addAttributes(campos.toList())
    capa.updateFields()

    rasgos = []
    for reg in resultado.ocurrencias:
        lon, lat = reg["decimalLongitude"], reg["decimalLatitude"]
        if lon is None or lat is None:
            continue                           # el CSV la conserva; la capa no
        f = QgsFeature(capa.fields())
        for campo in ESQUEMA:
            f[campo.nombre] = reg.get(campo.nombre)
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        rasgos.append(f)

    capa.dataProvider().addFeatures(rasgos)    # en bloque, no uno por uno
    capa.updateExtents()
    return capa
```

Agregar *features* de una en una en una capa grande es órdenes de magnitud más
lento. Acumular y hacer un solo `addFeatures`.

## Simbología

`graficar_ocurrencias(color_por = "source")` se sustituye por `.qml` precocinados
en `recursos/estilos/`: por `source`, por `kingdom`, por `family`.

```python
capa.loadNamedStyle(os.path.join(dir_estilos, "por_fuente.qml"))
capa.triggerRepaint()
```

Además: configurar `sourceURL` como campo de tipo URL en el formulario de
atributos, para que el registro sea clicable desde el panel de identificación.
Es la mejora concreta sobre el PNG estático de R.

## Mensajes

```python
iface.messageBar().pushMessage("Peru OCC", texto, level=Qgis.Success, duration=6)
QgsMessageLog.logMessage(detalle, "Peru OCC", Qgis.Info)   # traza completa
```

La barra de mensajes lleva una frase accionable en español; el detalle técnico va
al log. Paridad con `cli::cli_abort`: el mensaje dice **qué pasó y qué hacer**
(«iNaturalist reporta 42 000 registros: acote el área o divida por periodos»), no
solo que algo falló.

## Diálogo: validar antes de lanzar

Antes de crear la tarea, replicar `validar_entrada_busqueda()`: nombre no vacío,
`grupo` en {flora, fauna, vacío}, límite entero positivo o vacío, `nivel` válido.
Validar en el diálogo evita lanzar una tarea que morirá en el primer paso, y
permite señalar el campo culpable.

Ante homónimos (un distrito que existe en varios departamentos), **preguntar**;
no elegir el primero en silencio.
