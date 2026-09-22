"""Excepciones tipadas del paquete.

Existen para que quien consuma la biblioteca —en particular un plugin de
QGIS— pueda traducir cada falla a un mensaje distinto y accionable, en lugar
de mostrar un ``Exception`` genérico.
"""

from __future__ import annotations


class ErrorGeoperu(Exception):
    """Raíz de todos los errores del paquete."""


class ErrorCatalogo(ErrorGeoperu):
    """El catálogo de datos no se pudo leer, validar o refrescar."""


class ErrorDescarga(ErrorGeoperu):
    """Falló la descarga de un archivo y los reintentos se agotaron."""


class ErrorGeoPackage(ErrorGeoperu):
    """El archivo no es un GeoPackage válido o no tiene tabla de rasgos."""


class ErrorGeometria(ErrorGeoperu):
    """No se pudo interpretar una geometría WKB o el encabezado GPKG."""


class GeografiaNoEncontrada(ErrorGeoperu):
    """No hay datos para la geografía pedida.

    Lleva sugerencias porque el error más común de esta biblioteca es un
    nombre mal escrito o un homónimo, y decir solo «no encontrado» deja a
    quien llama sin salida.
    """

    def __init__(self, geografia: str, nivel: str, sugerencias=()):
        self.geografia = geografia
        self.nivel = nivel
        self.sugerencias = tuple(sugerencias)
        mensaje = f"No hay datos de nivel {nivel!r} para {geografia!r}."
        if self.sugerencias:
            mensaje += " ¿Quiso decir: " + ", ".join(self.sugerencias) + "?"
        super().__init__(mensaje)


class UnidadAmbigua(ErrorGeoperu):
    """El nombre corresponde a más de una unidad y hace falta desambiguar.

    Nunca se resuelve eligiendo la primera coincidencia: hay 12 distritos
    llamados «San Juan» en el Perú y devolver uno al azar produce un
    resultado incorrecto que nadie detecta.
    """

    def __init__(self, nombre: str, coincidencias):
        self.nombre = nombre
        self.coincidencias = tuple(coincidencias)
        detalle = "; ".join(" / ".join(c) for c in self.coincidencias)
        super().__init__(
            f"{nombre!r} corresponde a {len(self.coincidencias)} unidades: {detalle}. "
            "Indique el departamento (y la provincia, si hace falta) para desambiguar."
        )
