"""Regresión de MOTOKO-D0301/D0302/D0304.

D0301: el modo directorio sin `--impl` auditaba el `.c` del propio TDA como
si fuera un cliente, así que sus accesos legítimos `p->tope` dentro de `pila.c`
se reportaban como MOT002.
D0302: MOT002 comparaba solo el NOMBRE del campo contra todos los TDA, sin
mirar de qué tipo era la variable accedida.
D0304: MOT001 reportaba siempre la línea 1.
"""

from pathlib import Path

from typer.testing import CliRunner

from motoko.cli import app
from motoko.core.tda_verifier import audit_tda_encapsulation, extract_tdas_from_header

runner = CliRunner()

PILA_H = "typedef struct { int tope; int datos[10]; } Pila;\nvoid push(Pila *p, int v);\n"
PILA_C = '#include "pila.h"\nvoid push(Pila *p, int v) { p->datos[p->tope] = v; p->tope++; }\n'
CLIENTE_C = (
    '#include "pila.h"\n'
    "typedef struct { int tope; } Contador;\n"
    "void mal_uso(Pila *p) { p->tope = 0; }\n"
    "void uso_correcto(Contador *c) { c->tope = 0; }\n"
)


def _proyecto(tmp_path: Path) -> Path:
    (tmp_path / "pila.h").write_text(PILA_H, encoding="utf-8")
    (tmp_path / "pila.c").write_text(PILA_C, encoding="utf-8")
    (tmp_path / "otro.c").write_text(CLIENTE_C, encoding="utf-8")
    return tmp_path


def test_la_implementacion_no_se_audita_como_cliente(tmp_path):
    """D0301: `pila.c` accede legítimamente a los campos internos."""
    proyecto = _proyecto(tmp_path)
    res = runner.invoke(app, ["verify", str(proyecto), "--json"])
    import json

    violaciones = json.loads(res.output)["violations"]
    en_impl = [v for v in violaciones if v["file_path"].endswith("pila.c")]
    assert en_impl == []


def test_un_campo_homonimo_de_otro_tipo_no_es_violacion(tmp_path):
    """D0302: `c->tope` con `c: Contador` (struct local) no es del TDA Pila."""
    proyecto = _proyecto(tmp_path)
    res = runner.invoke(app, ["verify", str(proyecto), "--json"])
    import json

    mot002 = [v for v in json.loads(res.output)["violations"] if v["code"] == "MOT002"]
    lineas = {v["line_number"] for v in mot002}
    assert 3 in lineas, "la violación real (p->tope con p: Pila) debe detectarse"
    assert 4 not in lineas, "c->tope con c: Contador no pertenece al TDA"


def test_la_violacion_real_sigue_detectandose(tmp_path):
    (tmp_path / "pila.h").write_text(PILA_H, encoding="utf-8")
    cliente = tmp_path / "cli.c"
    cliente.write_text('#include "pila.h"\nvoid f(Pila *p) { p->tope = 0; }\n', encoding="utf-8")
    reporte = audit_tda_encapsulation([tmp_path / "pila.h"], [cliente], [])
    assert any(v.code == "MOT002" and v.tda_name == "Pila" for v in reporte.violations)


def test_mot001_reporta_la_linea_real_de_la_definicion(tmp_path):
    """D0304: el struct se define en la línea 3, no en la 1."""
    h = tmp_path / "texto.h"
    h.write_text("/* cabecera */\n\ntypedef struct { char *s; } Texto;\n", encoding="utf-8")
    tdas = extract_tdas_from_header(h)
    assert tdas[0].line_number == 3
    reporte = audit_tda_encapsulation([h], [], [])
    mot001 = next(v for v in reporte.violations if v.code == "MOT001")
    assert mot001.line_number == 3
