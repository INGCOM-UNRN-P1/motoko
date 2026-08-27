"""Verificación de opacidad y encapsulamiento de Tipos Abstractos de Datos en C."""

import re
from pathlib import Path
from typing import List, Dict, Set
from motoko.core.models import TdaDefinition, EncapsulationViolation, TdaAuditReport

# Patrones para detectar TDAs opacos vs transparentes en cabeceras
OPAQUE_TYPEDEF_PATTERN = re.compile(
    r'typedef\s+struct\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;|'
    r'typedef\s+struct\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*;'
)
TRANSPARENT_STRUCT_PATTERN = re.compile(
    r'typedef\s+struct\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?\s*\{([^}]+)\}\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*;'
)


def extract_tdas_from_header(header_path: Path) -> List[TdaDefinition]:
    """Extrae las definiciones de TDAs en una cabecera, catalogándolos como opacos o transparentes."""
    tdas = []
    content = header_path.read_text(encoding="utf-8", errors="replace")

    # 1. Buscar structs con cuerpo expuesto (transparente)
    for match in TRANSPARENT_STRUCT_PATTERN.finditer(content):
        fields_raw = match.group(1)
        name = match.group(2)
        fields = []
        for decl in fields_raw.split(";"):
            parts = decl.strip().split()
            if parts:
                field_name = parts[-1].replace("*", "").strip()
                if field_name:
                    fields.append(field_name)
        tdas.append(TdaDefinition(
            name=name,
            is_opaque=False,
            header_path=str(header_path),
            declared_fields=fields
        ))

    # 2. Buscar structs opacos (solo declaración forward)
    for match in OPAQUE_TYPEDEF_PATTERN.finditer(content):
        name = match.group(2) or match.group(4)
        if name and not any(t.name == name for t in tdas):
            tdas.append(TdaDefinition(
                name=name,
                is_opaque=True,
                header_path=str(header_path),
                declared_fields=[]
            ))

    return tdas


def audit_tda_encapsulation(
    headers: List[Path],
    client_files: List[Path],
    implementation_files: List[Path]
) -> TdaAuditReport:
    """Verifica que el código cliente no viole el encapsulamiento de los TDAs."""
    all_tdas: List[TdaDefinition] = []
    for h in headers:
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
                suggestion="Hacé el TDA opaco: declará 'typedef struct s_{name} t_{name};' en el .h y definí el struct completo dentro del .c de implementación."
            ))

    # MOT002: Acceso directo a campos del struct en archivos cliente
    # Por ejemplo, si el cliente hace `tda->campo` o `puntero->primero`
    impl_names = {f.name for f in implementation_files}
    for client in client_files:
        if client.name in impl_names:
            continue

        content = client.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            for tda in all_tdas:
                for f in tda.declared_fields:
                    # Detectar variable->campo
                    if re.search(rf'->\s*{re.escape(f)}\b', line):
                        violations.append(EncapsulationViolation(
                            code="MOT002",
                            severity="ERROR",
                            tda_name=tda.name,
                            file_path=str(client),
                            line_number=idx,
                            line_content=stripped,
                            message=f"Violación de encapsulamiento: acceso directo al campo '{f}' del TDA '{tda.name}'.",
                            suggestion=f"Utilizá las primitivas públicas del TDA (getters/métodos) provistas en la cabecera en lugar de desreferenciar campos directamente."
                        ))

    has_errors = any(v.severity == "ERROR" for v in violations)
    return TdaAuditReport(
        tdas_analyzed=all_tdas,
        violations=violations,
        passed=not has_errors
    )
