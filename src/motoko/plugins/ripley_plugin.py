"""Plugin de MOTOKO para el microkernel RIPLEY."""

from pathlib import Path
from typing import Dict, Any
from motoko.core.tda_verifier import audit_tda_encapsulation


class MotokoPlugin:
    """Plugin de verificación de encapsulamiento de TDAs para Ripley."""

    name = "tda_encapsulation"
    description = "Verificador de encapsulamiento estricto y opacidad de TDAs en C"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        source_dir = Path(context.get("source_dir", "."))
        headers = list(source_dir.glob("**/*.h"))
        c_files = list(source_dir.glob("**/*.c"))

        report = audit_tda_encapsulation(headers, c_files, [])

        return {
            "passed": report.passed,
            "tdas_count": len(report.tdas_analyzed),
            "violations_count": len(report.violations),
            "violations": [
                {
                    "code": v.code,
                    "severity": v.severity,
                    "tda": v.tda_name,
                    "file": Path(v.file_path).name,
                    "line": v.line_number,
                    "message": v.message,
                    "suggestion": v.suggestion
                }
                for v in report.violations
            ]
        }
