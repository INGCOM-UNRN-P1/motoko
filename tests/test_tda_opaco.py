"""Ola 17: encapsulamiento de TDAs opacos (campos privados, MOT004), sugerencias con la función
pública que corresponde y el plugin de ripley con la misma clasificación que la CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from motoko.cli import app
from motoko.plugins.ripley_plugin import MotokoPlugin

HEADER = """#ifndef LISTA_H
#define LISTA_H
typedef struct s_lista lista_t;
lista_t *lista_crear(void);
int lista_obtener_primero(const lista_t *lista);
void lista_establecer_primero(lista_t *lista, int valor);
int lista_cantidad(const lista_t *lista);
int *lista_datos(lista_t *lista);
#endif
"""
IMPL = """#include <stdlib.h>
#include "lista.h"
struct s_lista
{
    int primero;
    int cantidad;
    int *datos;
};
lista_t *lista_crear(void) { return calloc(1, sizeof(lista_t)); }
int lista_obtener_primero(const lista_t *lista) { return lista->primero; }
void lista_establecer_primero(lista_t *lista, int valor) { lista->primero = valor; }
int lista_cantidad(const lista_t *lista) { return lista->cantidad; }
int *lista_datos(lista_t *lista) { return lista->datos; }
"""
CLIENTE = """#include <stdio.h>
#include "lista.h"
struct s_lista
{
    int primero;
    int cantidad;
    int *datos;
};
typedef struct { int primero; } par_t;
int main(void)
{
    lista_t *lista = lista_crear();
    par_t par = {1};
    lista->primero = 4;
    printf("%d %d %d\\n", lista->primero, lista->cantidad, par.primero);
    return 0;
}
"""


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    ej = tmp_path / "ejercicios" / "ejercicio1"
    ej.mkdir(parents=True)
    (ej / "lista.h").write_text(HEADER, encoding="utf-8")
    (ej / "lista.c").write_text(IMPL, encoding="utf-8")
    (ej / "main.c").write_text(CLIENTE, encoding="utf-8")
    lib = tmp_path / "libs" / "p1_test"
    lib.mkdir(parents=True)
    (lib / "p1.h").write_text("typedef struct { int x; } p1_publico_t;\n", encoding="utf-8")
    return tmp_path


def _reporte(proyecto: Path) -> dict:
    res = CliRunner().invoke(app, ["check", str(proyecto), "--json"])
    assert res.exit_code == 1, res.output  # hay errores: la entrega no pasa
    return json.loads(res.output)


def test_campos_privados_del_tda_opaco_salen_de_la_implementacion(proyecto):
    tdas = _reporte(proyecto)["tdas_analyzed"]
    assert [(t["name"], t["is_opaque"], t["struct_tag"], t["private_fields"]) for t in tdas] == [
        ("lista_t", True, "s_lista", ["primero", "cantidad", "datos"])]  # libs/ no es del estudiante


def test_accesos_al_tda_opaco_y_struct_redefinido(proyecto):
    violaciones = _reporte(proyecto)["violations"]
    por_codigo = {}
    for v in violaciones:
        por_codigo.setdefault(v["code"], []).append(v)
    assert [(v["line_number"], v["severity"]) for v in por_codigo["MOT004"]] == [(3, "ERROR")]
    accesos = [(v["line_number"], v["line_content"]) for v in por_codigo["MOT002"]]
    assert accesos == [(14, "lista->primero"), (15, "lista->primero"), (15, "lista->cantidad")]
    assert all("par.primero" not in v["line_content"] for v in violaciones)  # un struct propio del cliente


def test_sugerencia_con_la_funcion_publica(proyecto):
    sugerencias = [v["suggestion"] for v in _reporte(proyecto)["violations"] if v["code"] == "MOT002"]
    assert sugerencias == [
        "Usá la función lista_establecer_primero(lista, 4) provista por lista.h en lugar de acceder "
        "directamente al campo privado 'primero'.",
        "Usá la función lista_obtener_primero(lista) provista por lista.h en lugar de acceder directamente "
        "al campo privado 'primero'.",
        "Usá la función lista_cantidad(lista) provista por lista.h en lugar de acceder directamente al campo "
        "privado 'cantidad'.",
    ]


def test_sin_funcion_para_el_campo_lista_las_del_tda(tmp_path):
    (tmp_path / "pila.h").write_text("typedef struct { int tope; int *datos; } pila_t;\n"
                                     "void pila_apilar(pila_t *p, int x);\nint pila_desapilar(pila_t *p);\n",
                                     encoding="utf-8")
    (tmp_path / "main.c").write_text('#include "pila.h"\nint f(pila_t *p) { return p->tope; }\n', encoding="utf-8")
    datos = json.loads(CliRunner().invoke(app, ["check", str(tmp_path), "--json"]).output)
    mot002 = next(v for v in datos["violations"] if v["code"] == "MOT002")
    assert "pila_apilar, pila_desapilar" in mot002["suggestion"] and "'tope'" in mot002["suggestion"]


def test_plugin_de_ripley_informa_el_struct_redefinido(proyecto):
    codigos = [(o["codigo"], o["file"]) for o in MotokoPlugin().run({"source_dir": str(proyecto)})["observaciones"]]
    assert ("MOT004", "ejercicios/ejercicio1/main.c") in codigos
