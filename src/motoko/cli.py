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


def generar_seccion_markdown(report: TdaAuditReport) -> str:
    """Genera sección de auditoría de encapsulamiento de TDAs para Dredd."""
    lines = ["## Encapsulamiento y Opacidad de TDAs (Motoko)\n"]
    lines.append(f"- **TDAs analizados:** {len(report.tdas_analyzed)}")
    lines.append(f"- **Violaciones de encapsulamiento:** {len(report.violations)}\n")
    if report.passed:
        lines.append("> [!TIP]\n> **Encapsulamiento Estricto:** Los Tipos de Datos Abstractos respetan la opacidad y no exponen su estructura interna a los clientes.\n")
    else:
        lines.append("> [!WARNING]\n> **Ruptura de Encapsulamiento:** Se detectaron accesos directos a campos privados de structs fuera de su módulo de implementación.\n")
        lines.append("| TDA | Ubicación | Código | Severidad | Diagnóstico | Sugerencia |")
        lines.append("| :--- | :--- | :---: | :---: | :--- | :--- |")
        for v in report.violations:
            loc = f"`{Path(v.file_path).name}:{v.line_number}`"
            lines.append(f"| `{v.tda_name}` | {loc} | `{v.code}` | **{v.severity}** | {v.message} | {v.suggestion} |")
        lines.append("")
    return "\n".join(lines)


@app.command("verify")
@app.command("check")
def verify(
    headers: List[Path] = typer.Argument(..., help="Archivos de cabecera (.h) o directorios a analizar"),
    clients: List[Path] = typer.Option([], "--client", "-c", help="Archivos cliente (.c) que usan el TDA"),
    impls: List[Path] = typer.Option([], "--impl", "-i", help="Archivos de implementación (.c) del TDA"),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado"),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
):
    """Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos."""
    actual_headers: List[Path] = []
    discovered_clients: List[Path] = list(clients)
    discovered_impls: List[Path] = list(impls)

    for item in headers:
        if item.is_dir():
            actual_headers.extend(sorted(item.glob("**/*.h")))
            if not clients:
                discovered_clients.extend(sorted(item.glob("**/*.c")))
        elif item.is_file():
            if item.suffix in (".h", ".hpp"):
                actual_headers.append(item)
            elif item.suffix in (".c", ".cpp"):
                if not clients:
                    discovered_clients.append(item)
                actual_headers.extend(sorted(item.parent.glob("*.h")))

    # Si no se pasaron clientes explícitos y tenemos headers, buscar .c en los directorios de los headers
    if not discovered_clients:
        for h in actual_headers:
            parent = h.parent
            discovered_clients.extend(list(parent.glob("*.c")))

    # Desduplicar manteniendo orden
    actual_headers = list(dict.fromkeys(actual_headers))
    discovered_clients = list(dict.fromkeys(discovered_clients))

    if not actual_headers:
        report = TdaAuditReport(tdas_analyzed=[], violations=[], passed=True)
    else:
        report = audit_tda_encapsulation(actual_headers, discovered_clients, discovered_impls)

    if output_md:
        md_text = generar_seccion_markdown(report)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[bold green]✓ Sección Markdown generada en:[/bold green] {output_md}")
        raise typer.Exit(code=0 if report.passed else 1)

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


@app.command("report")
def report_cmd(
    headers: List[Path] = typer.Argument(..., help="Archivos de cabecera (.h) que definen TDAs"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
    clients: List[Path] = typer.Option([], "--client", "-c", help="Archivos cliente (.c) que usan el TDA"),
    impls: List[Path] = typer.Option([], "--impl", "-i", help="Archivos de implementación (.c) del TDA"),
):
    """Genera directamente la sección de reporte Markdown de MOTOKO para Dredd."""
    if not clients:
        for h in headers:
            parent = h.parent
            clients.extend(list(parent.glob("*.c")))

    report = audit_tda_encapsulation(headers, clients, impls)
    md_content = generar_seccion_markdown(report)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] {output}")
    else:
        print(md_content)


@app.command()
def version():
    """Muestra la versión de MOTOKO."""
    from motoko import __version__
    console.print(f"[bold cyan]MOTOKO[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
