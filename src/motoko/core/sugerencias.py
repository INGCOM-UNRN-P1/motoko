"""Qué función pública del TDA reemplaza un acceso directo a un campo (Ola 17).

Ante `lista->primero` en el código cliente, en lugar de «usá las primitivas» se nombra la función
que corresponde: `Usá la función lista_obtener_primero(lista) provista por lista.h en lugar de
acceder directamente al campo privado`. Se buscan, en las cabeceras, las funciones que reciben el
TDA (por su nombre o por la etiqueta del struct) y cuyo nombre contiene el del campo; para una
escritura (`p->tope = 0;`, `p->tope++`) se prefieren las que cambian el valor y para una lectura,
las que lo devuelven.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tree_sitter import Node

from motoko.core.models import TdaDefinition

_LECTURA = {"obtener", "get", "ver", "leer", "consultar", "dame", "devolver"}
_ESCRITURA = {"set", "establecer", "cambiar", "modificar", "fijar", "asignar", "poner", "actualizar"}


def _recorrer(node: Node):
    yield node
    for hijo in node.children:
        yield from _recorrer(hijo)


def _tipo_base(texto: str) -> str:
    return re.sub(r"\b(const|struct|volatile)\b|\*", " ", texto).strip()


def funciones_por_tda(headers: List[Path], tdas: List[TdaDefinition], parser) -> Dict[str, List[Tuple[str, str]]]:
    """TDA → [(función, cabecera)] de las funciones públicas que reciben ese TDA."""
    from motoko.core.preprocesador import enmascarar_bloques_inactivos

    nombres = {}
    for tda in tdas:
        nombres[tda.name] = tda.name
        if tda.struct_tag:
            nombres[tda.struct_tag] = tda.name
    resultado: Dict[str, List[Tuple[str, str]]] = {}
    for h in headers:
        texto = enmascarar_bloques_inactivos(Path(h).read_text(encoding="utf-8", errors="replace"))
        for n in _recorrer(parser.parse(texto.encode("utf-8")).root_node):
            if n.type != "function_declarator":
                continue
            ident = n.child_by_field_name("declarator")
            params = n.child_by_field_name("parameters")
            if ident is None or ident.type != "identifier" or params is None:
                continue
            tipos_param: Set[str] = set()
            for p in params.children:
                if p.type == "parameter_declaration" and p.child_by_field_name("type") is not None:
                    tipos_param.add(_tipo_base(p.child_by_field_name("type").text.decode("utf-8", errors="replace")))
            for tipo in tipos_param:
                if tipo in nombres:
                    resultado.setdefault(nombres[tipo], []).append(
                        (ident.text.decode("utf-8", errors="replace"), Path(h).name))
    return resultado


def es_escritura(acceso: Node) -> bool:
    """Si el acceso a campo es el destino de una asignación o de un ++/--."""
    padre = acceso.parent
    if padre is None:
        return False
    if padre.type == "assignment_expression" and padre.child_by_field_name("left") == acceso:
        return True
    return padre.type == "update_expression"


def valor_asignado(acceso: Node) -> Optional[str]:
    """`4` en `p->campo = 4;` (None si no es una asignación simple)."""
    padre = acceso.parent
    if padre is None or padre.type != "assignment_expression" or padre.child_by_field_name("left") != acceso:
        return None
    operador = padre.child_by_field_name("operator")
    derecho = padre.child_by_field_name("right")
    if operador is None or operador.text != b"=" or derecho is None:
        return None
    return (derecho.text or b"").decode("utf-8", errors="replace")


def elegir(funciones: List[Tuple[str, str]], campo: str, escritura: bool) -> Optional[Tuple[str, str]]:
    """La función cuyo nombre contiene todas las palabras del campo, prefiriendo las de lectura o
    escritura según el acceso."""
    palabras = set(campo.lower().split("_"))
    candidatas = [(f, h) for f, h in funciones if palabras <= set(f.lower().split("_"))]
    if not candidatas:
        return None
    preferidas = _ESCRITURA if escritura else _LECTURA
    contrarias = _LECTURA if escritura else _ESCRITURA

    def puntaje(par: Tuple[str, str]) -> Tuple[int, int, int]:
        partes = set(par[0].lower().split("_"))
        return (-len(partes & preferidas), len(partes & contrarias), len(partes))

    return min(candidatas, key=puntaje)


def sugerencia(tda: str, campo: str, operador: str, argumento: str, escritura: bool,
               funciones: Dict[str, List[Tuple[str, str]]], valor: Optional[str] = None) -> str:
    propias = funciones.get(tda, [])
    elegida = elegir(propias, campo, escritura)
    arg = argumento if operador == "->" else f"&{argumento}"
    if valor is not None:
        arg = f"{arg}, {valor}"
    if elegida:
        funcion, cabecera = elegida
        return (f"Usá la función {funcion}({arg}) provista por {cabecera} en lugar de acceder directamente "
                f"al campo privado '{campo}'.")
    if propias:
        lista = ", ".join(sorted({f for f, _ in propias})[:6])
        return (f"No hay una función de {tda} para '{campo}': usá las que ofrece su .h ({lista}) o, si hace "
                f"falta, agregá una al TDA en lugar de acceder directamente al campo.")
    return f"Usá las primitivas públicas del TDA {tda} en lugar de acceder directamente al campo '{campo}'."
