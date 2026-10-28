"""La CLI y el plugin de ripley clasifican igual los archivos de un proyecto (Ola 17)."""

from pathlib import Path

import pytest

from motoko.core.descubrimiento import clasificar
from motoko.plugins.ripley_plugin import MotokoPlugin


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    ej = tmp_path / "ejercicios" / "ejercicio1"
    ej.mkdir(parents=True)
    (ej / "pila.h").write_text("typedef struct s_pila pila_t;\nint *pila_datos(pila_t *p);\n", encoding="utf-8")
    (ej / "pila.c").write_text('#include "pila.h"\nstruct s_pila { int tope; int *datos; };\n'
                               "int *pila_datos(pila_t *p) { return p->datos; }\n", encoding="utf-8")
    (ej / "main.c").write_text('#include "pila.h"\nint main(void) { return 0; }\n', encoding="utf-8")
    lib = tmp_path / "libs" / "p1_test"
    lib.mkdir(parents=True)
    (lib / "p1.h").write_text("typedef struct { int x; } p1_publico_t;\n", encoding="utf-8")
    return tmp_path


def test_clasificar_empareja_y_excluye_libs(proyecto):
    headers, clientes, impls = clasificar([proyecto])
    assert [h.name for h in headers] == ["pila.h"]
    assert [c.name for c in clientes] == ["main.c"] and [i.name for i in impls] == ["pila.c"]


def test_plugin_de_ripley_ve_la_implementacion_y_mot003(proyecto):
    salida = MotokoPlugin().run({"source_dir": str(proyecto)})
    codigos = [(o["codigo"], o["file"]) for o in salida["observaciones"]]
    # pila_datos entrega el arreglo interno: antes el plugin no pasaba implementaciones y no lo veía.
    assert codigos == [("MOT003", "ejercicios/ejercicio1/pila.c")]
