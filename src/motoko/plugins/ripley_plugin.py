"""Plugin de MOTOKO para el microkernel RIPLEY."""

from pathlib import Path
from typing import Dict, Any
from motoko.core.tda_verifier import audit_tda_encapsulation


class MotokoPlugin:
    """Plugin de verificación de encapsulamiento de TDAs para Ripley."""

    name = "tda_encapsulation"
    description = "Verificador de encapsulamiento estricto y opacidad de TDAs en C"

    def execute(self, workspace: Path, manifest_config: Dict[str, Any]) -> Dict[str, Any]:
        return self.run({
            "source_dir": str(workspace),
            "workspace": workspace,
            "manifest_config": manifest_config,
        })

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raw_source = Path(context.get("source_dir") or context.get("workspace") or ".")
        source_dir = raw_source.parent if raw_source.is_file() else raw_source

        headers = list(source_dir.glob("**/*.h"))
        c_files = list(source_dir.glob("**/*.c"))

        report = audit_tda_encapsulation(headers, c_files, [])

        observaciones = [
            {
                "codigo": v.code,
                "rule_code": v.code,
                "rule_name": f"Violación de Encapsulamiento TDA: {v.tda_name}",
                "severidad": v.severity,
                "severity": v.severity,
                "archivo": Path(v.file_path).name,
                "file": Path(v.file_path).name,
                "linea": v.line_number,
                "line": v.line_number,
                "columna": 0,
                "column": 0,
                "mensaje": v.message,
                "message": v.message,
                "sugerencia": v.suggestion,
                "suggestion": v.suggestion,
                "source_plugin": "motoko",
            }
            for v in report.violations
        ]

        return {
            "ok": report.passed,
            "passed": report.passed,
            "tdas_count": len(report.tdas_analyzed),
            "violations_count": len(report.violations),
            "observaciones": observaciones,
            "issues": observaciones,
            "violations": [
                {
                    "code": v.code,
                    "severity": v.severity,
                    "tda": v.tda_name,
                    "file": Path(v.file_path).name,
                    "line": v.line_number,
                    "message": v.message,
                    "suggestion": v.suggestion,
                }
                for v in report.violations
            ],
        }

