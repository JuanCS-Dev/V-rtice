import typer
import asyncio
from rich.console import Console
from typing_extensions import Annotated
from ..connectors.adr_core import ADRCoreConnector
from ..utils.output import print_json, spinner_task, print_error, print_table
from ..utils.auth import require_auth

console = Console()

app = typer.Typer(
    name="adr",
    help="⚔️ ADR (Ameaça Digital em Redes) detection and response",
    rich_markup_mode="rich"
)

@app.command()
def status(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Check ADR system status.

    Example:
        vertice adr status
    """
    require_auth()

    async def _status():
        connector = ADRCoreConnector()
        try:
            if verbose:
                console.print("[dim]Checking ADR Core service status...[/dim]")
            with spinner_task("Checking ADR Core service status..."):
                if not await connector.health_check():
                    print_error("ADR Core service is offline")
                    return

            if verbose:
                console.print("[dim]Getting ADR system status...[/dim]")
            with spinner_task("Getting ADR system status..."):
                result = await connector.get_status()

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print("[bold green]ADR System Status:[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print("[yellow]Could not retrieve ADR system status.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_status())

@app.command()
def metrics(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Get ADR metrics (MTTR, detection rate).

    Example:
        vertice adr metrics
    """
    require_auth()

    async def _metrics():
        connector = ADRCoreConnector()
        try:
            if verbose:
                console.print("[dim]Checking ADR Core service status...[/dim]")
            with spinner_task("Checking ADR Core service status..."):
                if not await connector.health_check():
                    print_error("ADR Core service is offline")
                    return

            if verbose:
                console.print("[dim]Getting ADR metrics...[/dim]")
            with spinner_task("Getting ADR metrics..."):
                result = await connector._get("/api/adr/metrics")

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print("[bold green]ADR Metrics:[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print("[yellow]Could not retrieve ADR metrics.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_metrics())

# Subcommand group for analyze
analyze_app = typer.Typer(
    name="analyze",
    help="Manual analysis operations for ADR",
    rich_markup_mode="rich"
)
app.add_typer(analyze_app, name="analyze")

from ..utils.file_validator import sanitize_file_path, ValidationError

@analyze_app.command(name="file")
def analyze_file(
    path: Annotated[str, typer.Argument(help="File path to analyze")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Analyze a file for ADR.

    Example:
        vertice adr analyze file /path/to/suspicious.log
    """
    require_auth()

    async def _file_analyze():
        connector = ADRCoreConnector()
        try:
            try:
                safe_path = sanitize_file_path(path)
                filename = safe_path.name
            except ValidationError as e:
                print_error(f"Invalid file path: {e}")
                return

            if verbose:
                console.print("[dim]Checking ADR Core service status...[/dim]")
            with spinner_task("Checking ADR Core service status..."):
                if not await connector.health_check():
                    print_error("ADR Core service is offline")
                    return

            if verbose:
                console.print(f"[dim]Analyzing file: {filename}...[/dim]")
            with spinner_task(f"Analyzing file: {filename}..."):
                result = await connector._post("/api/adr/analyze/file", json={"filename": filename})

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print(f"[bold green]ADR File Analysis Result for {path}:[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print(f"[yellow]No ADR analysis result for {path}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_file_analyze())

@analyze_app.command(name="network")
def analyze_network(
    ip: Annotated[str, typer.Argument(help="IP address to analyze network traffic")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Analyze network traffic for an IP for ADR.

    Example:
        vertice adr analyze network 192.168.1.1
    """
    require_auth()

    async def _network_analyze():
        connector = ADRCoreConnector()
        try:
            if verbose:
                console.print("[dim]Checking ADR Core service status...[/dim]")
            with spinner_task("Checking ADR Core service status..."):
                if not await connector.health_check():
                    print_error("ADR Core service is offline")
                    return

            if verbose:
                console.print(f"[dim]Analyzing network traffic for IP: {ip}...[/dim]")
            with spinner_task(f"Analyzing network traffic for IP: {ip}..."):
                result = await connector._post("/api/adr/analyze/network", json={"ip_address": ip})

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print(f"[bold green]ADR Network Analysis Result for {ip}:[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print(f"[yellow]No ADR network analysis result for {ip}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_network_analyze())


ALLOWED_COMMANDS = {
    'ps': ['ps', 'aux'],
    'netstat': ['netstat', '-an'],
    'top': ['top', '-b', '-n', '1'],
    'df': ['df', '-h'],
    'free': ['free', '-m']
}

def sanitize_process_command(cmd: str) -> list:
    """
    Converte comando string em lista segura.
    Apenas comandos whitelisted são permitidos.
    """
    cmd = cmd.strip()
    
    # Verifica se está na whitelist
    if cmd not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {cmd}")
    
    return ALLOWED_COMMANDS[cmd]

@analyze_app.command(name="process")
def analyze_process(
    cmd: Annotated[str, typer.Argument(help="Command/process to analyze")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Analyze a process for ADR.

    Example:
        vertice adr analyze process "ps"
    """
    require_auth()

    async def _process_analyze():
        connector = ADRCoreConnector()
        try:
            try:
                safe_cmd_list = sanitize_process_command(cmd)
            except ValueError as e:
                print_error(str(e))
                console.print("\n[yellow]Allowed commands:[/yellow]")
                for cmd_name in ALLOWED_COMMANDS:
                    console.print(f"  - {cmd_name}")
                return

            if verbose:
                console.print("[dim]Checking ADR Core service status...[/dim]")
            with spinner_task("Checking ADR Core service status..."):
                if not await connector.health_check():
                    print_error("ADR Core service is offline")
                    return

            if verbose:
                console.print(f"[dim]Analyzing process: {safe_cmd_list}...[/dim]")
            with spinner_task(f"Analyzing process: {safe_cmd_list}..."):
                result = await connector._post("/api/adr/analyze/process", json={"command": safe_cmd_list})

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print(f"[bold green]ADR Process Analysis Result for '{cmd}':[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print(f"[yellow]No ADR process analysis result for '{cmd}'.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_process_analyze())
