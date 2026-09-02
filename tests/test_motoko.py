"""Tests unitarios y de integración para MOTOKO."""

from pathlib import Path
from typer.testing import CliRunner
from motoko.cli import app
from motoko.core.tda_verifier import extract_tdas_from_header, audit_tda_encapsulation
from motoko.plugins.ripley_plugin import MotokoPlugin

runner = CliRunner()


def test_extract_opaque_and_transparent_tdas(tmp_path):
    h = tmp_path / "pila.h"
    h.write_text("""
    typedef struct s_pila t_pila;
    typedef struct {
        int tamanio;
        int* elementos;
    } t_vector_expuesto;
    """)
    tdas = extract_tdas_from_header(h)
    names = {t.name: t.is_opaque for t in tdas}
    assert names.get("t_pila") is True
    assert names.get("t_vector_expuesto") is False


def test_audit_tda_violation(tmp_path):
    h = tmp_path / "lista.h"
    h.write_text("typedef struct { int cantidad; void* primero; } t_lista;\n")

    client = tmp_path / "main.c"
    client.write_text("""
    #include "lista.h"
    void f(t_lista* l) {
        int c = l->cantidad;
    }
    """)

    report = audit_tda_encapsulation([h], [client], [])
    assert any(v.code == "MOT002" for v in report.violations)
    assert report.passed is False


def test_cli_verify_json(tmp_path):
    h = tmp_path / "tda.h"
    h.write_text("typedef struct s_tda t_tda;\n")
    res = runner.invoke(app, ["verify", str(h), "--json"])
    assert res.exit_code == 0
    assert '"passed": true' in res.output


def test_cli_version():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "MOTOKO" in res.output


def test_ripley_plugin(tmp_path):
    h = tmp_path / "cola.h"
    h.write_text("typedef struct s_cola t_cola;\n")
    plugin = MotokoPlugin()
    res = plugin.run({"source_dir": str(tmp_path)})
    assert res["passed"] is True
    assert "violations" in res
    assert "observaciones" in res


def test_cli_check_directory_without_headers(tmp_path):
    # Un directorio con sólo código C sin cabeceras no debe fallar
    c_file = tmp_path / "main.c"
    c_file.write_text("int main(void) { return 0; }\n")
    res = runner.invoke(app, ["check", str(tmp_path), "--json"])
    assert res.exit_code == 0
    assert '"passed": true' in res.output
    assert '"violations": []' in res.output


def test_cli_check_directory_with_headers_and_clients(tmp_path):
    h = tmp_path / "pila.h"
    h.write_text("typedef struct s_pila t_pila;\n")
    c = tmp_path / "main.c"
    c.write_text("#include \"pila.h\"\nint main(void) { return 0; }\n")
    res = runner.invoke(app, ["check", str(tmp_path), "--json"])
    assert res.exit_code == 0
    assert '"passed": true' in res.output

