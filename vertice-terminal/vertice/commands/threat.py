import typer
import asyncio
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from ..connectors.threat_intel import ThreatIntelConnector
from ..utils.output import print_json, spinner_task, print_error, print_table
from ..utils.auth import require_auth

console = Console()

app = typer.Typer(
    name="threat",
    help="🛡️ Threat intelligence operations",
    rich_markup_mode="rich"
)

@app.command()
def lookup(
    indicator: Annotated[str, typer.Argument(help="Threat indicator to lookup (IP, domain, hash)")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Lookup threat indicator.

    Example:
        vertice threat lookup malicious.com
    """
    require_auth()

    async def _lookup():
        connector = ThreatIntelConnector()
        try:
            if verbose:
                console.print("[dim]Checking Threat Intelligence service status...[/dim]")
            with spinner_task("Checking Threat Intelligence service status..."):
                if not await connector.health_check():
                    print_error("Threat Intelligence service is offline")
                    return

            if verbose:
                console.print(f"[dim]Looking up threat indicator: {indicator}...[/dim]")
            with spinner_task(f"Looking up threat indicator: {indicator}..."):
                result = await connector.lookup_threat(indicator)

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print(f"[bold green]Threat Lookup Result for {indicator}:[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print(f"[yellow]No threat information found for {indicator}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_lookup())

@app.command()
def check(
    target: Annotated[str, typer.Argument(help="Target to check for known threats")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Check a target for known threats.

    Example:
        vertice threat check malware.exe
    """
    require_auth()

    async def _check():
        connector = ThreatIntelConnector()
        try:
            if verbose:
                console.print("[dim]Checking Threat Intelligence service status...[/dim]")
            with spinner_task("Checking Threat Intelligence service status..."):
                if not await connector.health_check():
                    print_error("Threat Intelligence service is offline")
                    return

            if verbose:
                console.print(f"[dim]Checking target: {target}...[/dim]")
            with spinner_task(f"Checking target: {target}..."):
                result = await connector.lookup_threat(target)

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print(f"[bold green]Threat Check Result for {target}:[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print(f"[yellow]No threat information found for {target}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_check())

@app.command()
def scan(
    file_path: Annotated[str, typer.Argument(help="File path to scan for threats")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False
):
    """Scan a file for threats.

    Example:
        vertice threat scan /path/to/suspicious.zip
    """
    require_auth()

    async def _scan():
        connector = ThreatIntelConnector()
        try:
            if verbose:
                console.print("[dim]Checking Threat Intelligence service status...[/dim]")
            with spinner_task("Checking Threat Intelligence service status..."):
                if not await connector.health_check():
                    print_error("Threat Intelligence service is offline")
                    return

            if verbose:
                console.print(f"[dim]Scanning file: {file_path}...[/dim]")
            with spinner_task(f"Scanning file: {file_path}..."):
                result = await connector.lookup_threat(file_path)

            if json_output:
                print_json(result)
            else:
                if result:
                    console.print(f"[bold green]Threat Scan Result for {file_path}:[/bold green]")
                    table_data = []
                    for key, value in result.items():
                        table_data.append({"Field": key, "Value": str(value)})
                    print_table(table_data)
                else:
                    console.print(f"[yellow]No threats found in {file_path}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_scan())

@app.command()
def feed(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Follow threat feed in real-time")] = False
):
    """Get threat intelligence feed.

    Example:
        vertice threat feed
        vertice threat feed --follow
    """
    require_auth()

    console.print("[yellow]Threat feed functionality coming soon...[/yellow]")
    if follow:
        console.print("[dim]Real-time feed streaming will be available in next version.[/dim]")
