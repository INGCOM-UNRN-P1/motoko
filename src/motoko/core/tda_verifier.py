"""Verificación de opacidad y encapsulamiento de Tipos Abstractos de Datos en C usando Tree-Sitter AST."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Set, Optional

import tree_sitter_c as tsc
from tree_sitter import Language, Parser, Node

from motoko.core.models import TdaDefinition, EncapsulationViolation, TdaAuditReport
from motoko.core.preprocesador import enmascarar_bloques_inactivos

_C_LANGUAGE: Optional[Language] = None
_PARSER: Optional[Parser] = None


def get_c_parser() -> Parser:
    global _C_LANGUAGE, _PARSER
    if _PARSER is None:
        _C_LANGUAGE = Language(tsc.language())
        _PARSER = Parser(_C_LANGUAGE)
    return _PARSER


def _find_identifier(node: Node) -> Optional[str]:
    """Encuentra el identificador dentro de un declarador AST."""
    if node.type in ("identifier", "type_identifier", "field_identifier"):
        return (node.text or b"").decode("utf-8", errors="replace")
    for child in node.children:
        if child.type in ("identifier", "type_identifier", "field_identifier"):
            return (child.text or b"").decode("utf-8", errors="replace")
        elif child.type in ("pointer_declarator", "array_declarator", "parenthesized_declarator"):
            res = _find_identifier(child)
            if res:
                return res
    return None


def _tipo_base(texto: str) -> str:
    """Limpia calificadores y punteros para quedarse con el nombre del tipo."""
    for palabra in ("const", "struct", "volatile"):
        texto = texto.replace(palabra, "")
    return texto.replace("*", "").strip()


def _recolectar_tipos_de_variables(root: Node) -> Dict[str, str]:
    """Mapea cada variable/parámetro a su tipo declarado, para saber a qué TDA
    pertenece realmente un `->campo` en vez de asumirlo por el nombre del campo.
    """
    tipos: Dict[str, str] = {}

    def _registrar(type_node: Optional[Node], declarador: Optional[Node]) -> None:
        if type_node is None or declarador is None:
            return
        if declarador.type == "init_declarator":
            declarador = declarador.child_by_field_name("declarator")
        if declarador is None:
            return
        nombre = _find_identifier(declarador)
        tipo = _tipo_base((type_node.text or b"").decode("utf-8", errors="replace"))
        if nombre and tipo:
            tipos[nombre] = tipo

    def _traverse(node: Node) -> None:
        if node.type == "parameter_declaration":
            _registrar(node.child_by_field_name("type"), node.child_by_field_name("declarator"))
        elif node.type == "declaration":
            type_node = node.child_by_field_name("type")
            for hijo in node.children:
                if hijo is type_node or hijo.type in (";", ","):
                    continue
                _registrar(type_node, hijo)

        for child in node.children:
            _traverse(child)

    _traverse(root)
    return tipos


def extract_tdas_from_header(header_path: Path) -> List[TdaDefinition]:
    """Extrae las definiciones de TDAs en una cabecera, catalogándolos como opacos o transparentes con AST."""
    if not Path(header_path).is_file():
        return []
    try:
        content = Path(header_path).read_text(encoding="utf-8", errors="replace")
        content = enmascarar_bloques_inactivos(content)
        source_bytes = content.encode("utf-8")
        parser = get_c_parser()
        tree = parser.parse(source_bytes)
    except Exception:
        return []

    tdas: List[TdaDefinition] = []

    def _traverse(node: Node) -> None:
        if node.type == "type_definition":
            type_node = node.child_by_field_name("type")
            decl_node = node.child_by_field_name("declarator")
            ident = _find_identifier(decl_node) if decl_node else None

            if ident and type_node and type_node.type == "struct_specifier":
                body = type_node.child_by_field_name("body")
                if body:
                    fields = []
                    for f in body.children:
                        if f.type == "field_declaration":
                            f_decl = f.child_by_field_name("declarator")
                            if f_decl:
                                f_name = _find_identifier(f_decl)
                                if f_name:
                                    fields.append(f_name)
                    tdas.append(TdaDefinition(
                        name=ident,
                        is_opaque=False,
                        header_path=str(header_path),
                        declared_fields=fields,
                        line_number=node.start_point.row + 1,
                    ))
                else:
                    etiqueta = type_node.child_by_field_name("name")
                    tdas.append(TdaDefinition(
                        name=ident,
                        is_opaque=True,
                        header_path=str(header_path),
                        declared_fields=[],
                        line_number=node.start_point.row + 1,
                        struct_tag=(etiqueta.text or b"").decode("utf-8", errors="replace") if etiqueta else None,
                    ))

        for child in node.children:
            _traverse(child)

    _traverse(tree.root_node)
    return tdas


def _structs_con_cuerpo(root: Node) -> List[tuple]:
    """(etiqueta o nombre del typedef, campos, línea) de cada struct definido con sus campos."""
    encontrados = []
    for node in _recorrer(root):
        if node.type != "struct_specifier" or node.child_by_field_name("body") is None:
            continue
        nombre = node.child_by_field_name("name")
        etiqueta = (nombre.text or b"").decode("utf-8", errors="replace") if nombre else None
        if etiqueta is None and node.parent is not None and node.parent.type == "type_definition":
            decl = node.parent.child_by_field_name("declarator")
            etiqueta = _find_identifier(decl) if decl is not None else None
        campos = []
        for f in node.child_by_field_name("body").children:
            if f.type == "field_declaration" and f.child_by_field_name("declarator") is not None:
                campo = _find_identifier(f.child_by_field_name("declarator"))
                if campo:
                    campos.append(campo)
        if etiqueta:
            encontrados.append((etiqueta, campos, node.start_point.row + 1))
    return encontrados


def _recorrer(node: Node):
    yield node
    for hijo in node.children:
        yield from _recorrer(hijo)


def _parsear(ruta: Path, parser) -> Optional[Node]:
    try:
        contenido = enmascarar_bloques_inactivos(ruta.read_text(encoding="utf-8", errors="replace"))
        return parser.parse(contenido.encode("utf-8")).root_node
    except Exception:
        return None


def completar_campos_privados(tdas: List[TdaDefinition], impls: List[Path], parser) -> None:
    """Los campos de cada TDA opaco, de la definición del struct en su implementación (Ola 17)."""
    por_etiqueta = {t.struct_tag: t for t in tdas if t.is_opaque and t.struct_tag}
    for impl in impls:
        raiz = _parsear(impl, parser)
        if raiz is None:
            continue
        for etiqueta, campos, _ in _structs_con_cuerpo(raiz):
            tda = por_etiqueta.get(etiqueta)
            if tda is not None and not tda.private_fields:
                tda.private_fields = campos
                tda.impl_path = str(impl)


def audit_tda_encapsulation(
    headers: List[Path],
    client_files: List[Path],
    implementation_files: List[Path]
) -> TdaAuditReport:
    """Verifica que el código cliente no viole el encapsulamiento de los TDAs usando Tree-Sitter AST."""
    valid_headers = [Path(h) for h in headers if Path(h).is_file()]
    valid_clients = [Path(c) for c in client_files if Path(c).is_file()]
    valid_impls = [Path(i) for i in implementation_files if Path(i).is_file()]

    all_tdas: List[TdaDefinition] = []
    for h in valid_headers:
        all_tdas.extend(extract_tdas_from_header(h))
    parser = get_c_parser()
    completar_campos_privados(all_tdas, valid_impls, parser)
    from motoko.core.sugerencias import es_escritura, funciones_por_tda, sugerencia, valor_asignado

    funciones = funciones_por_tda(valid_headers, all_tdas, parser)
    opacos_por_etiqueta = {t.struct_tag: t for t in all_tdas if t.is_opaque and t.struct_tag and t.private_fields}

    violations: List[EncapsulationViolation] = []

    # MOT001: TDAs definidos de forma transparente en cabecera pública
    for tda in all_tdas:
        if not tda.is_opaque:
            violations.append(EncapsulationViolation(
                code="MOT001",
                severity="WARNING",
                tda_name=tda.name,
                file_path=tda.header_path,
                line_number=tda.line_number,
                line_content=f"typedef struct {{ ... }} {tda.name};",
                message=f"El TDA '{tda.name}' expone sus campos internos en la cabecera pública {Path(tda.header_path).name}.",
                suggestion=f"Hacé el TDA opaco: declará 'typedef struct s_{tda.name} t_{tda.name};' en el .h y definí el struct completo dentro del .c de implementación."
            ))

    # MOT002: Acceso directo a campos del struct en archivos cliente mediante AST
    impl_names = {f.name for f in valid_impls}

    for client in valid_clients:
        if client.name in impl_names:
            continue

        try:
            content = client.read_text(encoding="utf-8", errors="replace")
            content = enmascarar_bloques_inactivos(content)
            source_bytes = content.encode("utf-8")
            tree = parser.parse(source_bytes)
        except Exception:
            continue

        tipos_variables = _recolectar_tipos_de_variables(tree.root_node)
        # MOT004: el cliente copia la definición privada del struct para poder tocar sus campos.
        campos_propios: Set[str] = set()
        for etiqueta, campos, linea in _structs_con_cuerpo(tree.root_node):
            tda_opaco = opacos_por_etiqueta.get(etiqueta)
            if tda_opaco is None:
                campos_propios.update(campos)
                continue
            violations.append(EncapsulationViolation(
                code="MOT004",
                severity="ERROR",
                tda_name=tda_opaco.name,
                file_path=str(client),
                line_number=linea,
                line_content=f"struct {etiqueta} {{ ... }}",
                message=(f"El archivo cliente {client.name} redefine el struct privado '{etiqueta}' del TDA opaco "
                         f"'{tda_opaco.name}' (se define en {Path(tda_opaco.impl_path or '').name}) para acceder a sus campos."),
                suggestion=(f"Borrá esa definición e incluí sólo {Path(tda_opaco.header_path).name}: el cliente usa "
                            f"{tda_opaco.name} a través de sus funciones públicas."),
            ))

        def _traverse_client(node: Node, client: Path = client, tipos_variables: dict = tipos_variables,
                             campos_propios: Set[str] = campos_propios) -> None:
            if node.type == "field_expression":
                field_node = node.child_by_field_name("field")
                arg_node = node.child_by_field_name("argument")
                # Si el argumento es un identificador simple y se conoce su
                # tipo declarado, la coincidencia de nombre de campo solo
                # cuenta cuando el tipo es EL de este TDA. Sin esto, `c->tope`
                # con `c: Contador` se marcaba como violación de un TDA
                # "Pila" no relacionado, por la sola coincidencia de nombre
                # de campo. Cuando el argumento es una expresión más compleja
                # (llamada, member chain) y no se puede resolver el tipo, se
                # conserva el chequeo por nombre para no perder detecciones.
                tipo_arg = tipos_variables.get((arg_node.text or b"").decode("utf-8", errors="replace")) if arg_node and arg_node.type == "identifier" else None
                if field_node:
                    field_name = (field_node.text or b"").decode("utf-8", errors="replace")
                    for tda in all_tdas:
                        campos = tda.private_fields if tda.is_opaque else tda.declared_fields
                        if field_name not in campos:
                            continue
                        if tipo_arg is not None and tipo_arg not in (tda.name, tda.struct_tag):
                            continue
                        # Con un TDA opaco y el tipo sin resolver, un campo homónimo de un struct del
                        # propio cliente no es un acceso al TDA.
                        if tipo_arg is None and tda.is_opaque and field_name in campos_propios:
                            continue

                        line_no = node.start_point.row + 1
                        raw_expr = (node.text or b"").decode("utf-8", errors="replace")
                        operador = node.child_by_field_name("operator")
                        donde = (f"privado (se define en {Path(tda.impl_path or '').name})" if tda.is_opaque
                                 else "interno")
                        violations.append(EncapsulationViolation(
                            code="MOT002",
                            severity="ERROR",
                            tda_name=tda.name,
                            file_path=str(client),
                            line_number=line_no,
                            line_content=raw_expr,
                            message=f"Violación de encapsulamiento: acceso directo al campo {donde} '{field_name}' del TDA '{tda.name}' en el archivo cliente {client.name} ('{raw_expr}').",
                            suggestion=sugerencia(tda.name, field_name,
                                                  (operador.text or b"->").decode() if operador is not None else "->",
                                                  (arg_node.text or b"").decode("utf-8", errors="replace") if arg_node else "",
                                                  es_escritura(node), funciones, valor_asignado(node)),
                        ))

            for child in node.children:
                _traverse_client(child)

        _traverse_client(tree.root_node)

    # MOT003: funciones públicas que devuelven punteros a la memoria interna (QoL #670)
    from motoko.core.interna import punteros_internos

    violations.extend(punteros_internos(valid_headers, valid_impls, parser))

    opaque_count = sum(1 for t in all_tdas if t.is_opaque)
    transparent_count = sum(1 for t in all_tdas if not t.is_opaque)
    passed = not any(v.severity == "ERROR" for v in violations)

    report = TdaAuditReport(
        passed=passed,
        tdas_analyzed=all_tdas,
        opaque_tdas_count=opaque_count,
        transparent_tdas_count=transparent_count,
        violations_count=len(violations),
        violations=violations
    )
    from motoko.core.interna import resumen_para_el_estudiante

    report.resumen = resumen_para_el_estudiante(report)
    return report
