"""MOT003: funciones públicas que devuelven memoria interna (QoL #670) y resumen por TDA."""

import shutil
from pathlib import Path

from motoko.core.tda_verifier import audit_tda_encapsulation

DATOS = Path(__file__).parent / "datos_internos"


def test_punteros_a_memoria_interna():
    r = audit_tda_encapsulation([DATOS / "pila.h"], [DATOS / "main.c"], [DATOS / "pila.c"])
    mot003 = {(v.tda_name, v.severity) for v in r.violations if v.code == "MOT003"}
    # &p->tope: error; p->nombre (puntero): advertencia; la versión const y la static no cuentan.
    assert mot003 == {("pila_tope", "ERROR"), ("pila_nombre", "WARNING")}
    assert not r.passed


def test_resumen_para_el_estudiante(tmp_path):
    for f in DATOS.iterdir():
        shutil.copy(f, tmp_path / f.name)
    (tmp_path / "pila.h").write_text(
        "typedef struct { int tope; int datos[10]; } Pila;\nint pila_cantidad(const Pila *p);\n", encoding="utf-8")
    (tmp_path / "pila.c").write_text('#include "pila.h"\nint pila_cantidad(const Pila *p) { return p->tope; }\n', encoding="utf-8")
    (tmp_path / "main.c").write_text('#include "pila.h"\nint main(void) { Pila p; p.tope = 0; return p.tope; }\n', encoding="utf-8")
    r = audit_tda_encapsulation([tmp_path / "pila.h"], [tmp_path / "main.c"], [tmp_path / "pila.c"])
    assert r.resumen[0].startswith("Tu TDA Pila expone 2 campos en pila.h (tope, datos)")
    assert "main.c:2" in r.resumen[0]
