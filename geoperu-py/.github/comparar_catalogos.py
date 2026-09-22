"""Compara dos catálogos y emite el resultado como salidas de GitHub Actions.

Se comparan los conjuntos de URL, no los archivos completos: el campo
``generado_en_utc`` cambia en cada ejecución y compararlo produciría un
*pull request* vacío todos los años.

Uso: ``python .github/comparar_catalogos.py <anterior.json> <nuevo.json>``
"""

from __future__ import annotations

import json
import pathlib
import sys


def urls(ruta: pathlib.Path) -> set[str]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return {e["url"] for e in datos["entradas"]} | {a["url"] for a in datos.get("anp", ())}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    anterior, nuevo = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    nuevas = urls(nuevo)

    if not anterior.exists():
        # Primer catálogo del repositorio: todo es alta.
        print("cambio=si")
        print(f"altas={len(nuevas)}")
        print("bajas=0")
        return 0

    viejas = urls(anterior)
    altas, bajas = nuevas - viejas, viejas - nuevas
    print(f"cambio={'si' if altas or bajas else 'no'}")
    print(f"altas={len(altas)}")
    print(f"bajas={len(bajas)}")

    for url in sorted(bajas):
        print(f"::warning::desapareció del origen: {url}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
