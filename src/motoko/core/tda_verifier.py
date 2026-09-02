"""Verificación de opacidad y encapsulamiento de Tipos Abstractos de Datos en C usando Tree-Sitter AST."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Set, Optional

import tree_sitter_c as tsc
from tree_sitter import Language, Parser, Node

from motoko.core.models import TdaDefinition, EncapsulationViolation, TdaAuditReport

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
        return node.text.decode("utf-8", errors="replace")
    for child in node.children:
        if child.type in ("identifier", "type_identifier", "field_identifier"):
            return child.text.decode("utf-8", errors="replace")
        elif child.type in ("pointer_declarator", "array_declarator", "parenthesized_declarator"):
            res = _find_identifier(child)
            if res:
                return res
    return None


def extract_tdas_from_header(header_path: Path) -> List[TdaDefinition]:
    """Extrae las definiciones de TDAs en una cabecera, catalogándolos como opacos o transparentes con AST."""
    if not Path(header_path).is_file():
        return []
    tdas: List[TdaDefinition] = []
    content = Path(header_path).read_text(encoding="utf-8", errors="replace")
    source_bytes = content.encode("utf-8")
    parser = get_c_parser()
    tree = parser.parse(source_bytes)

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
                        declared_fields=fields
                    ))
                else:
                    tdas.append(TdaDefinition(
                        name=ident,
                        is_opaque=True,
                        header_path=str(header_path),
                        declared_fields=[]
                    ))

        for child in node.children:
            _traverse(child)

    _traverse(tree.root_node)
    return tdas


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

    violations: List[EncapsulationViolation] = []

    # MOT001: TDAs definidos de forma transparente en cabecera pública
    for tda in all_tdas:
        if not tda.is_opaque:
            violations.append(EncapsulationViolation(
                code="MOT001",
                severity="WARNING",
                tda_name=tda.name,
                file_path=tda.header_path,
                line_number=1,
                line_content=f"typedef struct {{ ... }} {tda.name};",
                message=f"El TDA '{tda.name}' expone sus campos internos en la cabecera pública {Path(tda.header_path).name}.",
                suggestion=f"Hacé el TDA opaco: declará 'typedef struct s_{tda.name} t_{tda.name};' en el .h y definí el struct completo dentro del .c de implementación."
            ))

    # MOT002: Acceso directo a campos del struct en archivos cliente mediante AST
    impl_names = {f.name for f in valid_impls}
    parser = get_c_parser()

    for client in valid_clients:
        if client.name in impl_names:
            continue

        content = client.read_text(encoding="utf-8", errors="replace")
        source_bytes = content.encode("utf-8")
        tree = parser.parse(source_bytes)

        def _traverse_client(node: Node) -> None:
            if node.type == "field_expression":
                field_node = node.child_by_field_name("field")
                if field_node:
                    field_name = field_node.text.decode("utf-8", errors="replace")
                    for tda in all_tdas:
                        if field_name in tda.declared_fields:
                            line_no = node.start_point.row + 1
                            raw_expr = node.text.decode("utf-8", errors="replace")
                            violations.append(EncapsulationViolation(
                                code="MOT002",
                                severity="ERROR",
                                tda_name=tda.name,
                                file_path=str(client),
                                line_number=line_no,
                                line_content=raw_expr,
                                message=f"Violación de encapsulamiento: Acceso directo al campo '{field_name}' del TDA '{tda.name}' en archivo cliente {client.name}.",
                                suggestion=f"Utilizá las primitivas públicas del TDA en lugar de desreferenciar campos internos directamente ('{raw_expr}')."
                            ))

            for child in node.children:
                _traverse_client(child)

        _traverse_client(tree.root_node)

    opaque_count = sum(1 for t in all_tdas if t.is_opaque)
    transparent_count = sum(1 for t in all_tdas if not t.is_opaque)
    passed = not any(v.severity == "ERROR" for v in violations)

    return TdaAuditReport(
        passed=passed,
        tdas_analyzed=all_tdas,
        opaque_tdas_count=opaque_count,
        transparent_tdas_count=transparent_count,
        violations_count=len(violations),
        violations=violations
    )
