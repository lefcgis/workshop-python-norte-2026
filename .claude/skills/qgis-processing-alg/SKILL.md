---
name: qgis-processing-alg
description: Implementación de QgsProcessingProvider y QgsProcessingAlgorithm para QGIS 3.44, de modo que la búsqueda de ocurrencias funcione en batch, en modelos gráficos y desde qgis_process. Úsala al tocar plugin-qgis/peru_occ/processing/, al definir parámetros y salidas de un algoritmo, o al integrar el núcleo con la Caja de herramientas. Actívala ante Processing, QgsProcessingAlgorithm, processAlgorithm, initAlgorithm, feedback, batch, modelo gráfico, qgis_process, provider.
---

# Algoritmo Processing para `peru_occ`

## Por qué existe esta superficie

El diálogo sirve para una consulta. El algoritmo Processing sirve para **cuarenta
distritos de una provincia**, dentro de un modelo gráfico, o desde la línea de
comandos con `qgis_process`. Es la capacidad que en R exige escribir un bucle, y
el argumento más fuerte para migrar el flujo a QGIS.

**Comparten el mismo `nucleo/`.** Si el algoritmo reimplementa lógica del diálogo,
las dos superficies divergirán y el usuario obtendrá cifras distintas según por
dónde entre.

## Proveedor

```python
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

class ProveedorPeruOcc(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(BuscarOcurrenciasAlg())

    def id(self):            return "peru_occ"
    def name(self):          return "Peru OCC"
    def longName(self):      return "Peru OCC — ocurrencias de biodiversidad"
    def icon(self):          return QIcon(RUTA_ICONO)
```

Registro y baja en el ciclo de vida del plugin (`metadata.txt` necesita
`hasProcessingProvider=yes`):

```python
def _registrar_processing(self):
    self.proveedor = ProveedorPeruOcc()
    QgsApplication.processingRegistry().addProvider(self.proveedor)
# y en unload(): removeProvider(self.proveedor)
```

## Algoritmo

```python
from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterEnum,
                       QgsProcessingParameterString, QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination, QgsProcessingException,
                       QgsProcessing)

class BuscarOcurrenciasAlg(QgsProcessingAlgorithm):
    NIVEL, NOMBRE, DEPARTAMENTO, PROVINCIA = "NIVEL", "NOMBRE", "DEPARTAMENTO", "PROVINCIA"
    AMBITO, TAXON, GRUPO, LIMITE = "AMBITO", "TAXON", "GRUPO", "LIMITE"
    SALIDA, MANIFIESTO = "SALIDA", "MANIFIESTO"

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterEnum(
            self.NIVEL, "Nivel", options=["distrito", "provincia", "polígono de capa"],
            defaultValue=0))
        self.addParameter(QgsProcessingParameterString(
            self.NOMBRE, "Nombre de la unidad", optional=True))
        self.addParameter(QgsProcessingParameterString(
            self.DEPARTAMENTO, "Departamento", optional=True))
        self.addParameter(QgsProcessingParameterString(
            self.PROVINCIA, "Provincia", optional=True))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.AMBITO, "Capa de ámbito (si nivel = polígono)",
            types=[QgsProcessing.TypeVectorPolygon], optional=True))
        self.addParameter(QgsProcessingParameterString(
            self.TAXON, "Nombre científico", optional=True))
        self.addParameter(QgsProcessingParameterEnum(
            self.GRUPO, "Grupo", options=["ambos", "flora", "fauna"], defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(
            self.LIMITE, "Límite por API (0 = completo)",
            type=QgsProcessingParameterNumber.Integer, defaultValue=500, minValue=0))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.SALIDA, "Ocurrencias"))
        self.addParameter(QgsProcessingParameterFileDestination(
            self.MANIFIESTO, "Manifiesto de reproducibilidad",
            fileFilter="JSON (*.json)", optional=True, createByDefault=False))

    def processAlgorithm(self, parameters, context, feedback):
        params = self._leer_parametros(parameters, context, feedback)
        try:
            resultado = ejecutar_busqueda(params, cancelado=feedback.isCanceled,
                                          progreso=feedback.setProgress,
                                          informar=feedback.pushInfo)
        except ErrorTechoApi as exc:
            # Techo de API: no truncar en silencio, abortar con instrucción
            raise QgsProcessingException(str(exc)) from exc

        sink, sink_id = self.parameterAsSink(
            parameters, self.SALIDA, context,
            campos_del_esquema(), QgsWkbTypes.Point,
            QgsCoordinateReferenceSystem("EPSG:4326"))
        for rasgo in rasgos_desde(resultado):
            if feedback.isCanceled():
                break
            sink.addFeature(rasgo, QgsFeatureSink.FastInsert)

        ruta_manifiesto = self.parameterAsFileOutput(parameters, self.MANIFIESTO, context)
        if ruta_manifiesto:
            escribir_manifiesto(resultado, ruta_manifiesto)

        return {self.SALIDA: sink_id, self.MANIFIESTO: ruta_manifiesto}

    def name(self):            return "buscarocurrencias"
    def displayName(self):     return "Buscar ocurrencias de biodiversidad"
    def group(self):           return "Consulta"
    def groupId(self):         return "consulta"
    def shortHelpString(self):  return AYUDA_HTML
    def createInstance(self):  return BuscarOcurrenciasAlg()
```

## Reglas del contexto Processing

1. **`feedback`, no `iface`.** En Processing no hay barra de mensajes ni diálogos:
   `feedback.pushInfo()`, `feedback.reportError()`, `feedback.setProgress()`,
   `feedback.isCanceled()`. Un `QMessageBox` en modo batch cuelga la ejecución
   esperando un clic que nadie dará.
2. **`createInstance()` devuelve una instancia nueva.** Processing clona el
   algoritmo por ejecución; devolver `self` rompe el modo batch de forma sutil.
3. **Sin estado de instancia entre corridas.** El estado vive en variables locales
   de `processAlgorithm`.
4. **Errores como `QgsProcessingException`.** Es lo que Processing sabe mostrar y
   lo que detiene la corrida limpiamente.
5. **`name()` en minúsculas, sin espacios ni acentos** — es el identificador para
   `qgis_process`.
6. **`shortHelpString()` no es opcional.** Es la única documentación que el usuario
   ve en la Caja de herramientas.

## Rendimiento en batch

Cuarenta distritos son cuarenta corridas: la caché compartida (límites y consultas)
es lo que hace la diferencia entre minutos y horas. Respetar
`pausa_entre_lotes_s = 0.2` también en batch, e informar por `feedback.pushInfo()`
cuando una unidad se resuelve desde caché — si no, el usuario cree que el plugin
se colgó.
