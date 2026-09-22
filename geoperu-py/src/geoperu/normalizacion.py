"""Normalización de nombres de unidades administrativas.

Replica ``normalizar_texto()`` de ``peruocc`` para que «MADRE DE DIOS»,
«Madre de Dios» y «madre de dios» resuelvan a la misma unidad.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Iterable

#: Los 25 departamentos, en la forma oficial del INEI.
#: Coincide con ``peruocc::departamentos_oficiales()`` y con el catálogo de datos.
DEPARTAMENTOS = (
    "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO",
    "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO",
    "ICA", "JUNIN", "LA LIBERTAD", "LAMBAYEQUE", "LIMA",
    "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA",
    "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI",
)

_NO_ALFANUMERICO = re.compile(r"[^A-Z0-9 ]")
_ESPACIOS = re.compile(r"\s+")


def normalizar(texto: str | None) -> str | None:
    """Pasa a mayúsculas, quita tildes y puntuación, y colapsa espacios.

    >>> normalizar("Madre de Dios")
    'MADRE DE DIOS'
    >>> normalizar("  Áncash ")
    'ANCASH'

    Divergencia deliberada respecto a ``peruocc``: su ``chartr()`` traduce
    «Ü» a «D» por un desliz en la tabla de reemplazo. Aquí «Ü» se normaliza a
    «U», que es lo correcto. No afecta la paridad porque ningún departamento,
    provincia ni distrito del Perú lleva «Ü».
    """
    if texto is None:
        return None
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", str(texto).upper())
        if unicodedata.category(c) != "Mn"
    )
    limpio = _NO_ALFANUMERICO.sub("", sin_tildes)
    return _ESPACIOS.sub(" ", limpio).strip()


def sugerir(nombre: str, candidatos: Iterable[str], maximo: int = 5) -> tuple[str, ...]:
    """Devuelve los nombres más parecidos, para acompañar un error."""
    objetivo = normalizar(nombre) or ""
    unicos = {normalizar(c) or "": c for c in candidatos}
    cercanos = difflib.get_close_matches(objetivo, list(unicos), n=maximo, cutoff=0.6)
    return tuple(unicos[c] for c in cercanos)


def es_departamento(nombre: str) -> bool:
    return normalizar(nombre) in DEPARTAMENTOS
