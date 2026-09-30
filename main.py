import json
import time
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.checker import check_api
from src.storage import append_result, load_history, get_summary
from src.reporter import generate_report

app = typer.Typer(help="API Health Monitor — Monitorea APIs y genera reporte HTML")
console = Console()


def load_apis(apis_file: str = "apis.json") -> list:
    path = Path(apis_file)
    if not path.exists():
        console.print(f"[red]No se encontró {apis_file}[/red]")
        raise typer.Exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_checks(apis: list, silent: bool = False):
    """Corre todos los checks y guarda los resultados."""
    if not silent:
        console.print(f"\n[bold blue]🔍 Chequeando {len(apis)} APIs...[/bold blue]")

    for api in apis:
        result = check_api(api)
        append_result(result)

        if not silent:
            status = "[green]✅ UP[/green]" if result["is_up"] else "[red]❌ DOWN[/red]"
            latency = f"{result['latency_ms']} ms" if result["latency_ms"] else "—"
            error = f" [yellow]({result['error']})[/yellow]" if result.get("error") else ""
            console.print(f"  {status}  {api['name']:<30} {latency}{error}")


@app.command()
def check(
    open_report: bool = typer.Option(True, help="Abrir el reporte HTML en el navegador"),
    apis_file: str = typer.Option("apis.json", help="Archivo con la lista de APIs"),
):
    """Corre un chequeo único y genera el reporte HTML."""
    apis = load_apis(apis_file)
    run_checks(apis)

    history = load_history()
    summaries = get_summary(history)
    path = generate_report(summaries, open_browser=open_report)

    console.print(f"\n[bold green]📄 Reporte generado:[/bold green] {path}")


@app.command()
def monitor(
    interval: int = typer.Option(5, help="Intervalo en minutos entre chequeos"),
    apis_file: str = typer.Option("apis.json", help="Archivo con la lista de APIs"),
    open_report: bool = typer.Option(True, help="Abrir el reporte al iniciar"),
):
    """Monitorea las APIs continuamente cada X minutos."""
    apis = load_apis(apis_file)

    console.print(Panel.fit(
        f"📡 API Health Monitor\n"
        f"APIs: [cyan]{len(apis)}[/cyan]  |  "
        f"Intervalo: [cyan]{interval} min[/cyan]  |  "
        f"Presioná [bold]Ctrl+C[/bold] para detener",
        style="bold blue"
    ))

    first_run = True
    try:
        while True:
            run_checks(apis, silent=not first_run)

            history = load_history()
            summaries = get_summary(history)
            generate_report(summaries, open_browser=(first_run and open_report))

            if first_run:
                console.print(f"\n[green]✅ Monitoreo activo. Próximo chequeo en {interval} minutos.[/green]")
                first_run = False
            else:
                from datetime import datetime
                console.print(f"[dim]🔄 Chequeo completado — {datetime.now().strftime('%H:%M:%S')} — próximo en {interval} min[/dim]")

            time.sleep(interval * 60)

    except KeyboardInterrupt:
        console.print("\n[yellow]⏹  Monitoreo detenido.[/yellow]")


@app.command()
def status(
    apis_file: str = typer.Option("apis.json", help="Archivo con la lista de APIs"),
):
    """Muestra el estado actual en la terminal sin generar HTML."""
    history = load_history()
    summaries = get_summary(history)

    if not summaries:
        console.print("[yellow]No hay datos todavía. Corré primero: python main.py check[/yellow]")
        return

    table = Table(title="📡 Estado de APIs", show_header=True, header_style="bold magenta")
    table.add_column("API")
    table.add_column("Estado")
    table.add_column("Latencia")
    table.add_column("Uptime")
    table.add_column("Caídas", justify="right")
    table.add_column("Cambios", justify="right")

    for s in summaries:
        estado = "[green]✅ UP[/green]" if s["is_up"] else "[red]❌ DOWN[/red]"
        latencia = f"{s['latency_ms']} ms" if s["latency_ms"] else "—"
        uptime = f"{s['uptime_pct']}%"
        table.add_row(s["name"], estado, latencia, uptime, str(s["downtime_events"]), str(s["content_changes"]))

    console.print(table)


if __name__ == "__main__":
    app()
