---
name: qgis-plugin-scaffold
description: Estructura, empaquetado y ciclo de vida de un plugin QGIS 3.44 LTR con Qt5/PyQt5 y Python 3.12. Úsala al crear o modificar metadata.txt, __init__.py, classFactory, initGui/unload, registro de acciones y menús, recursos e iconos, i18n, o al armar el ZIP instalable. Actívala ante plugin QGIS, metadata.txt, classFactory, initGui, unload, qgisMinimumVersion, pb_tool, empaquetar plugin, instalar plugin.
---

# Andamiaje de plugin QGIS 3.44 LTR (Qt5)

## Regla de importación que decide la vida del plugin

```python
# CORRECTO: capa de compatibilidad de QGIS. Sobrevive al salto a Qt6 (QGIS 4.0).
from qgis.PyQt.QtWidgets import QDialog, QAction
from qgis.PyQt.QtCore import Qt, QThread
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt import uic

# INCORRECTO: rompe en QGIS 4.0 y no respeta el binding activo.
from PyQt5.QtWidgets import QDialog
```

Todo `import` de Qt pasa por `qgis.PyQt`. Sin excepciones.

## `metadata.txt` mínimo válido

```ini
[general]
name=Peru OCC
qgisMinimumVersion=3.44
qgisMaximumVersion=3.99
description=Consulta y estandariza ocurrencias de biodiversidad en unidades administrativas del Perú (GBIF + iNaturalist).
about=Puerto a QGIS del paquete R peruocc. Resuelve límites oficiales INEI, consulta GBIF e iNaturalist, valida espacialmente los registros y los estandariza a Darwin Core con manifiesto de reproducibilidad.
version=0.1.0
author=<autor>
email=<correo>
tracker=<url>/issues
repository=<url>
homepage=<url>
category=Vector
icon=recursos/iconos/peru_occ.svg
experimental=True
deprecated=False
tags=biodiversity,gbif,inaturalist,peru,occurrence,darwin core,inei
hasProcessingProvider=yes
```

Detalles que hacen fallar la instalación: `version` debe subir en cada release;
`icon` es una ruta **relativa** dentro del ZIP; `hasProcessingProvider=yes` es
obligatorio si se registra un `QgsProcessingProvider`; el ZIP debe contener **una
sola carpeta raíz** con el nombre del plugin.

## Ciclo de vida

```python
# __init__.py
def classFactory(iface):
    from .plugin import PeruOccPlugin
    return PeruOccPlugin(iface)
```

```python
# plugin.py
class PeruOccPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.acciones = []
        self.proveedor = None

    def initGui(self):
        icono = QIcon(os.path.join(os.path.dirname(__file__),
                                   "recursos", "iconos", "peru_occ.svg"))
        accion = QAction(icono, "Buscar ocurrencias…", self.iface.mainWindow())
        accion.triggered.connect(self.abrir_dialogo)
        self.iface.addPluginToVectorMenu("&Peru OCC", accion)
        self.iface.addToolBarIcon(accion)
        self.acciones.append(accion)
        self._registrar_processing()

    def unload(self):
        # Simétrico y completo: lo que no se desregistra queda duplicado
        # al recargar el plugin y sobrevive como referencia colgante.
        for accion in self.acciones:
            self.iface.removePluginVectorMenu("&Peru OCC", accion)
            self.iface.removeToolBarIcon(accion)
        self.acciones.clear()
        if self.proveedor is not None:
            QgsApplication.processingRegistry().removeProvider(self.proveedor)
            self.proveedor = None
```

`unload()` debe ser el espejo exacto de `initGui()`. Un `unload` incompleto es la
causa número uno de acciones duplicadas y *crashes* al recargar con Plugin Reloader.

## Carga de `.ui` de Qt Designer

```python
FORM, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "dialogo_busqueda.ui")
)

class DialogoBusqueda(QDialog, FORM):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.setupUi(self)
```

Los `.ui` se editan con el **Qt Designer que trae QGIS** (Qt5). Un `.ui` guardado
con Qt6 Designer puede no cargar.

## Prohibiciones de empaquetado

- **Sin dependencias externas.** Nada de `requests`, `shapely`, `geopandas`,
  `pandas`. Solo stdlib de Python 3.12 y la API de QGIS/Qt. Un `pip install` dentro
  de QGIS es inviable en entornos institucionales (permisos, red restringida) y es
  la razón principal por la que un plugin no se adopta.
- **Sin `sys.path` hacks** ni `.pyc` ni `__pycache__` en el ZIP.
- **Sin recursos binarios grandes** sin justificarlo: si se empaqueta el GeoPackage
  de límites INEI, debe ir simplificado y su peso documentado.

## Estructura del ZIP

```
peru_occ.zip
└── peru_occ/            ← una sola carpeta raíz, nombre = nombre del plugin
    ├── metadata.txt
    ├── __init__.py
    └── …
```

Validación mínima antes de entregar: instalar el ZIP en un perfil **limpio** de
QGIS 3.44, abrir el diálogo, correr una consulta, recargar con Plugin Reloader y
confirmar que no se duplican acciones.
