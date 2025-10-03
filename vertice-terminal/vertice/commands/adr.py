import typer
from rich.console import Console
from typing_extensions import Annotated
from ..connectors.adr_core import ADRCoreConnector
from ..utils.output import print_json, spinner_task, print_error, print_table
from ..utils.decorators import with_connector
from ..utils.file_validator import sanitize_file_path, ValidationError

console = Console()

app = typer.Typer(
    name="adr",
    help="⚔️ ADR (Ameaça Digital em Redes) detection and response",
    rich_markup_mode="rich",
)


@app.command()
@with_connector(ADRCoreConnector)
async def status(
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Check ADR system status.

    Example:
        vertice adr status
    """
    if verbose:
        console.print("[dim]Getting ADR system status...[/dim]")
    with spinner_task("Getting ADR system status..."):
        result = await connector.get_status()

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print("[bold green]ADR System Status:[/bold green]")
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)


@app.command()
@with_connector(ADRCoreConnector)
async def metrics(
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Get ADR metrics (MTTR, detection rate).

    Example:
        vertice adr metrics
    """
    if verbose:
        console.print("[dim]Getting ADR metrics...[/dim]")
    with spinner_task("Getting ADR metrics..."):
        result = await connector._get("/api/adr/metrics")

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print("[bold green]ADR Metrics:[/bold green]")
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)


# Subcommand group for analyze
analyze_app = typer.Typer(
    name="analyze", help="Manual analysis operations for ADR", rich_markup_mode="rich"
)
app.add_typer(analyze_app, name="analyze")


@analyze_app.command(name="file")
@with_connector(ADRCoreConnector)
async def analyze_file(
    path: Annotated[str, typer.Argument(help="File path to analyze")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Analyze a file for ADR.

    Example:
        vertice adr analyze file /path/to/suspicious.log
    """
    try:
        safe_path = sanitize_file_path(path)
        filename = safe_path.name
    except ValidationError as e:
        print_error(f"Invalid file path: {e}")
        return

    if verbose:
        console.print(f"[dim]Analyzing file: {filename}...[/dim]")
    with spinner_task(f"Analyzing file: {filename}..."):
        result = await connector._post(
            "/api/adr/analyze/file", json={"filename": filename}
        )

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(f"[bold green]ADR File Analysis Result for {path}:[/bold green]")
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)


@analyze_app.command(name="network")
@with_connector(ADRCoreConnector)
async def analyze_network(
    ip: Annotated[str, typer.Argument(help="IP address to analyze network traffic")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Analyze network traffic for an IP for ADR.

    Example:
        vertice adr analyze network 192.168.1.1
    """
    if verbose:
        console.print(f"[dim]Analyzing network traffic for IP: {ip}...[/dim]")
    with spinner_task(f"Analyzing network traffic for IP: {ip}..."):
        result = await connector._post(
            "/api/adr/analyze/network", json={"ip_address": ip}
        )

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(f"[bold green]ADR Network Analysis Result for {ip}:[/bold green]")
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)


ALLOWED_COMMANDS = {
    "ps": ["ps", "aux"],
    "netstat": ["netstat", "-an"],
    "top": ["top", "-b", "-n", "1"],
    "df": ["df", "-h"],
    "free": ["free", "-m"],
}


def sanitize_process_command(cmd: str) -> list:
    """
    Converte comando string em lista segura.
    Apenas comandos whitelisted são permitidos.
    """
    cmd = cmd.strip()

    if cmd not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {cmd}")

    return ALLOWED_COMMANDS[cmd]


@analyze_app.command(name="process")
@with_connector(ADRCoreConnector)
async def analyze_process(
    cmd: Annotated[str, typer.Argument(help="Command/process to analyze")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Analyze a process for ADR.

    Example:
        vertice adr analyze process "ps"
    """
    try:
        safe_cmd_list = sanitize_process_command(cmd)
    except ValueError as e:
        print_error(str(e))
        console.print("\n[yellow]Allowed commands:[/yellow]")
        for cmd_name in ALLOWED_COMMANDS:
            console.print(f"  - {cmd_name}")
        return

    if verbose:
        console.print(f"[dim]Analyzing process: {safe_cmd_list}...[/dim]")
    with spinner_task(f"Analyzing process: {safe_cmd_list}..."):
        result = await connector._post(
            "/api/adr/analyze/process", json={"command": safe_cmd_list}
        )

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(
            f"[bold green]ADR Process Analysis Result for '{cmd}':[/bold green]"
        )
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)
