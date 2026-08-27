"""CLI principal de MOTOKO."""

import json
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from motoko.core.models import TdaAuditReport
from motoko.core.tda_verifier import audit_tda_encapsulation

app = typer.Typer(
    name="motoko",
    help="Verificador de encapsulamiento estricto y opacidad de TDAs en C",
    add_completion=True
)
console = Console()


@app.command()
def verify(
    headers: List[Path] = typer.Argument(..., help="Archivos de cabecera (.h) que definen TDAs"),
    clients: List[Path] = typer.Option([], "--client", "-c", help="Archivos cliente (.c) que usan el TDA"),
    impls: List[Path] = typer.Option([], "--impl", "-i", help="Archivos de implementación (.c) del TDA"),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado")
):
    """Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos."""
    # Si no se pasan clientes explícitos, buscar .c en los directorios de los headers
    if not clients:
        for h in headers:
            parent = h.parent
            clients.extend(list(parent.glob("*.c")))

    report = audit_tda_encapsulation(headers, clients, impls)

    if json_output:
        print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
        if not report.passed:
            raise typer.Exit(code=1)
        return

    if not report.violations:
        console.print(Panel(
            f"[bold green]✓ Encapsulamiento 100% Estricto[/bold green]\n"
            f"• TDAs analizados: {len(report.tdas_analyzed)}\n"
            f"• Ningún archivo cliente desreferencia campos internos de forma indebida.",
            title="[bold green]MOTOKO TDA Verifier[/bold green]"
        ))
        return

    table = Table(title="Auditoría de Encapsulamiento y Opacidad de TDAs", show_header=True, header_style="bold magenta")
    table.add_column("Código", style="cyan", width=8)
    table.add_column("Sev", style="bold", width=8)
    table.add_column("TDA", style="yellow")
    table.add_column("Ubicación", style="blue")
    table.add_column("Diagnóstico y Sugerencia", style="white")

    for v in report.violations:
        sev_color = "red" if v.severity == "ERROR" else "yellow"
        table.add_row(
            v.code,
            f"[{sev_color}]{v.severity}[/{sev_color}]",
            v.tda_name,
            f"{Path(v.file_path).name}:{v.line_number}",
            f"{v.message}\n[dim]↳ Sugerencia: {v.suggestion}[/dim]"
        )

    console.print(table)
    if not report.passed:
        raise typer.Exit(code=1)


@app.command()
def version():
    """Muestra la versión de MOTOKO."""
    from motoko import __version__
    console.print(f"[bold cyan]MOTOKO[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
