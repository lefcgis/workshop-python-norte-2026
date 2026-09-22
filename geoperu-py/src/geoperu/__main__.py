"""Interfaz de línea de comandos.

    python -m geoperu info
    python -m geoperu listar --nivel prov --departamento Cusco
    python -m geoperu descargar --geografia Amazonas --nivel dep --completo -s salida.geojson
    python -m geoperu catalogo --refrescar --guardar src/geoperu/datos/catalogo_2027.json
    python -m geoperu limpiar-cache
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import (
    __version__,
    cargar_catalogo,
    directorio_cache,
    limpiar_cache,
    obtener_anp_peru,
    obtener_geo_peru,
    refrescar_catalogo,
)
from .catalogo import guardar
from .errores import ErrorGeoperu


def _cmd_info(_args: argparse.Namespace) -> int:
    cat = cargar_catalogo()
    print(f"geoperu-py {__version__}")
    print(f"catálogo    {cat.version} (generado {cat.generado_en_utc})")
    print(f"entradas    {len(cat.entradas)} límites, {len(cat.anp)} áreas protegidas")
    print(
        f"cobertura   {len(cat.departamentos())} departamentos, "
        f"{len(cat.provincias())} provincias"
    )
    print(f"caché       {directorio_cache()}")
    return 0


def _cmd_listar(args: argparse.Namespace) -> int:
    cat = cargar_catalogo()
    if args.nivel in ("dep", "departamento"):
        for nombre in cat.departamentos():
            print(nombre)
    elif args.nivel in ("prov", "provincia"):
        for nombre in cat.provincias(args.departamento):
            print(nombre)
    elif args.nivel == "anp":
        for entrada in sorted(cat.anp, key=lambda a: a.nombre):
            print(f"{entrada.nombre}\t{entrada.categoria}")
    else:
        print("Nivel no listable. Use dep, prov o anp.", file=sys.stderr)
        return 2
    return 0


def _cmd_descargar(args: argparse.Namespace) -> int:
    if args.anp:
        coleccion = obtener_anp_peru(args.anp, forzar_descarga=args.forzar)
    else:
        coleccion = obtener_geo_peru(
            geografia=args.geografia,
            nivel=args.nivel,
            simplificado=not args.completo,
            forzar_descarga=args.forzar,
        )
    print(
        f"{len(coleccion)} rasgo(s), CRS {coleccion.crs}, campos: "
        f"{', '.join(coleccion.campos)}",
        file=sys.stderr,
    )
    if args.salida:
        destino = Path(args.salida)
        destino.write_text(
            json.dumps(coleccion.a_geojson(), ensure_ascii=False), encoding="utf-8"
        )
        print(f"escrito {destino}", file=sys.stderr)
    else:
        json.dump(coleccion.a_geojson(), sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


def _cmd_catalogo(args: argparse.Namespace) -> int:
    cat = refrescar_catalogo(version=args.version) if args.refrescar else cargar_catalogo()
    if args.refrescar:
        print(
            f"catálogo {cat.version}: {len(cat.entradas)} límites, "
            f"{len(cat.anp)} áreas protegidas",
            file=sys.stderr,
        )
    if args.guardar:
        ruta = guardar(cat, Path(args.guardar))
        print(f"escrito {ruta}", file=sys.stderr)
    elif not args.refrescar:
        json.dump(cat.a_dict(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    return 0


def _cmd_limpiar(_args: argparse.Namespace) -> int:
    print(f"{limpiar_cache()} archivo(s) eliminados de {directorio_cache()}")
    return 0


def construir_analizador() -> argparse.ArgumentParser:
    principal = argparse.ArgumentParser(
        prog="geoperu",
        description="Límites administrativos y áreas protegidas del Perú.",
    )
    principal.add_argument("--version", action="version", version=f"geoperu-py {__version__}")
    subs = principal.add_subparsers(dest="comando", required=True)

    subs.add_parser("info", help="versión, catálogo y cobertura").set_defaults(func=_cmd_info)

    listar = subs.add_parser("listar", help="lista unidades disponibles")
    listar.add_argument("--nivel", default="dep", help="dep, prov o anp")
    listar.add_argument("--departamento", help="filtra provincias por departamento")
    listar.set_defaults(func=_cmd_listar)

    descargar = subs.add_parser("descargar", help="descarga y emite GeoJSON")
    descargar.add_argument("--geografia", default="all", help="nombre de la unidad, o 'all'")
    descargar.add_argument("--nivel", default="dep", help="all, dep o prov")
    descargar.add_argument(
        "--completo", action="store_true",
        help="devuelve los distritos en lugar del polígono disuelto",
    )
    descargar.add_argument("--anp", help="nombre de un área natural protegida")
    descargar.add_argument("-s", "--salida", help="archivo GeoJSON de destino")
    descargar.add_argument("--forzar", action="store_true", help="ignora la caché")
    descargar.set_defaults(func=_cmd_descargar)

    cat = subs.add_parser("catalogo", help="muestra o regenera el catálogo")
    cat.add_argument("--refrescar", action="store_true", help="regenera desde el origen")
    cat.add_argument("--version", dest="version", help="etiqueta de versión, p. ej. 2027.1")
    cat.add_argument("--guardar", help="ruta del JSON a escribir")
    cat.set_defaults(func=_cmd_catalogo)

    subs.add_parser("limpiar-cache", help="borra la caché local").set_defaults(func=_cmd_limpiar)
    return principal


def main(argv=None) -> int:
    args = construir_analizador().parse_args(argv)
    try:
        return args.func(args)
    except ErrorGeoperu as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # La salida se canalizó a algo que cerró antes de leerla toda
        # (`| head`, por ejemplo). No es un fallo del programa.
        #
        # Se redirige el descriptor a /dev/null SIN cerrar sys.stdout: al
        # terminar, Python hace flush del búfer, y si el descriptor sigue
        # apuntando a la tubería rota eso provoca un segundo BrokenPipeError
        # que sí llega al usuario como traza.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except KeyboardInterrupt:
        print("interrumpido", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
