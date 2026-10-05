"""Funciones públicas del TDA que devuelven punteros a su memoria interna (QoL #670), y el resumen
de la auditoría por TDA en el lenguaje de la consigna.

Un TDA opaco sigue roto si `char *pila_datos(Pila *p) { return p->datos; }` le entrega al cliente
el arreglo interno: puede escribirlo sin pasar por las primitivas. Se marca la función pública
(declarada en un .h) que devuelve un puntero no `const` a:

- la dirección de un campo (`return &p->tope;`): error;
- un campo arreglo o puntero del struct (`return p->datos;`): advertencia, porque a veces es
  deliberado (en ese caso, que devuelva `const`).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

from tree_sitter import Node

from motoko.core.models import EncapsulationViolation, TdaAuditReport
from motoko.core.preprocesador import enmascarar_bloques_inactivos


def _arbol(ruta: Path, parser) -> Node:
    contenido = enmascarar_bloques_inactivos(ruta.read_text(encoding="utf-8", errors="replace"))
    return parser.parse(contenido.encode("utf-8")).root_node


def _recorrer(node: Node):
    yield node
    for hijo in node.children:
        yield from _recorrer(hijo)


def _nombre_funcion(declarador: Node) -> str:
    for n in _recorrer(declarador):
        if n.type == "function_declarator":
            ident = n.child_by_field_name("declarator")
            if ident is not None and ident.type == "identifier":
                return ident.text.decode("utf-8", errors="replace")
    return ""


def funciones_publicas(headers: List[Path], parser) -> Set[str]:
    nombres: Set[str] = set()
    for h in headers:
        for n in _recorrer(_arbol(h, parser)):
            if n.type == "declaration":
                decl = n.child_by_field_name("declarator")
                if decl is not None:
                    nombre = _nombre_funcion(decl)
                    if nombre:
                        nombres.add(nombre)
    return nombres


def campos_por_tipo(archivos: List[Path], parser) -> Dict[str, str]:
    """Campo → `arreglo` o `puntero`, de los structs definidos en los archivos."""
    campos: Dict[str, str] = {}
    for a in archivos:
        for n in _recorrer(_arbol(a, parser)):
            if n.type == "field_declaration":
                decl = n.child_by_field_name("declarator")
                if decl is None:
                    continue
                tipos = {x.type for x in _recorrer(decl)}
                ident = next((x for x in _recorrer(decl) if x.type == "field_identifier"), None)
                if ident is None:
                    continue
                if "array_declarator" in tipos:
                    campos[ident.text.decode("utf-8", errors="replace")] = "arreglo"
                elif "pointer_declarator" in tipos:
                    campos[ident.text.decode("utf-8", errors="replace")] = "puntero"
    return campos


def punteros_internos(headers: List[Path], impls: List[Path], parser) -> List[EncapsulationViolation]:
    publicas = funciones_publicas(headers, parser)
    campos = campos_por_tipo(headers + impls, parser)
    violaciones: List[EncapsulationViolation] = []
    for impl in impls:
        for fn in _recorrer(_arbol(impl, parser)):
            if fn.type != "function_definition":
                continue
            decl = fn.child_by_field_name("declarator")
            tipo = fn.child_by_field_name("type")
            nombre = _nombre_funcion(decl) if decl is not None else ""
            if nombre not in publicas or decl is None or decl.type != "pointer_declarator":
                continue
            if any(c.type == "type_qualifier" and c.text == b"const" for c in fn.children) or (
                    tipo is not None and b"const" in tipo.text):
                continue
            for ret in _recorrer(fn):
                if ret.type != "return_statement" or len(ret.children) < 2:
                    continue
                expr = ret.children[1]
                texto = expr.text.decode("utf-8", errors="replace")
                campo = None
                severidad = "WARNING"
                if expr.type == "pointer_expression" and expr.children and expr.children[0].type == "&":
                    arg = expr.child_by_field_name("argument")
                    if arg is not None and arg.type == "field_expression":
                        campo, severidad = arg.child_by_field_name("field"), "ERROR"
                elif expr.type == "field_expression":
                    f = expr.child_by_field_name("field")
                    if f is not None and campos.get(f.text.decode("utf-8", errors="replace")) in ("arreglo", "puntero"):
                        campo = f
                if campo is None:
                    continue
                nombre_campo = campo.text.decode("utf-8", errors="replace")
                violaciones.append(EncapsulationViolation(
                    code="MOT003",
                    severity=severidad,
                    tda_name=nombre,
                    file_path=str(impl),
                    line_number=ret.start_point.row + 1,
                    line_content=f"return {texto};",
                    message=(f"La función pública '{nombre}' devuelve un puntero a la memoria interna del TDA "
                             f"(el campo '{nombre_campo}'): el cliente puede modificarla sin pasar por las primitivas."),
                    suggestion=("Devolvé una copia del dato, o un puntero a const si solo se va a leer "
                                f"(const ... *{nombre}(...))."),
                ))
    return violaciones


def resumen_para_el_estudiante(report: TdaAuditReport) -> List[str]:
    """Una oración por TDA, en el lenguaje de la consigna: qué expone y quién lo usa."""
    accesos: Dict[str, List[str]] = defaultdict(list)
    internos: Dict[str, List[str]] = defaultdict(list)
    for v in report.violations:
        if v.code == "MOT002":
            accesos[v.tda_name].append(f"{Path(v.file_path).name}:{v.line_number}")
        elif v.code == "MOT003":
            internos[v.tda_name].append(f"{Path(v.file_path).name}:{v.line_number}")
    lineas = []
    for tda in report.tdas_analyzed:
        if tda.is_opaque:
            lineas.append(f"Tu TDA {tda.name} es opaco: el .h no expone sus campos.")
            continue
        n = len(tda.declared_fields)
        frase = (f"Tu TDA {tda.name} expone {n} campo{'s' if n != 1 else ''} en {Path(tda.header_path).name} "
                 f"({', '.join(tda.declared_fields)})")
        if accesos.get(tda.name):
            frase += f" y el código cliente los usa directamente en {', '.join(accesos[tda.name])}"
        lineas.append(frase + ".")
    for funcion, lugares in internos.items():
        lineas.append(f"La función {funcion} entrega memoria interna del TDA ({', '.join(lugares)}).")
    return lineas
