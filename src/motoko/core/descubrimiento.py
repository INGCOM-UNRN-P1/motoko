"""Qué archivos de un proyecto son cabeceras, implementaciones y clientes de los TDAs.

Lo usan la CLI y el plugin de ripley (antes sólo la CLI emparejaba `pila.h` con `pila.c`: el
plugin auditaba `pila.c` como cliente y no veía la memoria interna que entregan sus funciones).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

# Carpetas que no son del estudiante: la biblioteca de la cátedra (libs/p1_test expone sus structs a
# propósito), lo compilado y la plantilla de referencia.
EXCLUIDAS = frozenset({"libs", "lib", "build", "_baseline", "node_modules"})


def _visible(ruta: Path, raiz: Path) -> bool:
    try:
        partes = ruta.relative_to(raiz).parts
    except ValueError:
        partes = ruta.parts
    return not any(p.startswith(".") or p in EXCLUIDAS for p in partes[:-1])


def _buscar(raiz: Path, patron: str) -> List[Path]:
    return sorted(p for p in raiz.glob(patron) if _visible(p, raiz))


def clasificar(rutas: Iterable[Path], clientes: Sequence[Path] = (),
               impls: Sequence[Path] = ()) -> Tuple[List[Path], List[Path], List[Path]]:
    """(cabeceras, clientes, implementaciones). Un directorio aporta sus .h y .c (sin `libs/`, `build/`
    ni carpetas ocultas); un .c suelto, los .h de su carpeta. Sin `impls`, la implementación de un TDA
    es el .c con el nombre de un .h (`pila.h` + `pila.c`); los demás .c son clientes."""
    headers: List[Path] = []
    encontrados: List[Path] = list(clientes)
    for item in rutas:
        item = Path(item)
        if item.is_dir():
            headers.extend(_buscar(item, "**/*.h"))
            if not clientes:
                encontrados.extend(_buscar(item, "**/*.c"))
        elif item.is_file():
            if item.suffix in (".h", ".hpp"):
                headers.append(item)
            elif item.suffix in (".c", ".cpp"):
                if not clientes:
                    encontrados.append(item)
                headers.extend(sorted(item.parent.glob("*.h")))
    if not encontrados:
        for h in headers:
            encontrados.extend(sorted(h.parent.glob("*.c")))
    implementaciones = list(impls)
    if not implementaciones:
        nombres = {h.stem for h in headers}
        implementaciones = [c for c in encontrados if c.stem in nombres]
    encontrados = [c for c in encontrados if c not in implementaciones]
    unicos = lambda xs: list(dict.fromkeys(xs))  # noqa: E731
    return unicos(headers), unicos(encontrados), unicos(implementaciones)
