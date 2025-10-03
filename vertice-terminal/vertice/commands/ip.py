import typer
import asyncio
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from ..connectors.ip_intel import IPIntelConnector
from ..utils.output import format_ip_analysis, print_json, spinner_task, print_error
from ..utils.auth import require_auth, require_permission

console = Console()

app = typer.Typer(
    name="ip",
    help="🔍 IP Intelligence and analysis operations",
    rich_markup_mode="rich",
)

from ..utils.decorators import with_connector


@app.command()
@with_connector(IPIntelConnector)
async def analyze(
    ip_address: Annotated[str, typer.Argument(help="IP address to analyze")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet mode")] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Analyze an IP address

    Example:
        vertice ip analyze 8.8.8.8
        vertice ip analyze 8.8.8.8 --json
    """
    if verbose:
        console.print(f"[dim]Analyzing {ip_address}...[/dim]")

    with spinner_task(f"Analyzing IP: {ip_address}..."):
        result = await connector.analyze_ip(ip_address)

    if not result:
        return

    # Output
    if json_output:
        print_json(result)
    elif quiet:
        # Apenas threat status
        threat_level = result.get("reputation", {}).get("threat_level", "unknown")
        print(threat_level.upper())
    else:
        # Rich table formatado
        format_ip_analysis(result, console)


@app.command()
@with_connector(IPIntelConnector)
async def my_ip(
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """Detect your public IP

    Example:
        vertice ip my-ip
    """
    with spinner_task("Detecting public IP..."):
        ip = await connector.get_my_ip()

    if ip:
        if json_output:
            print_json({"ip": ip})
        else:
            console.print(f"[green]Your IP:[/green] {ip}")


@app.command()
@with_connector(IPIntelConnector)
async def bulk(
    file: Annotated[
        str, typer.Argument(help="File containing IP addresses (one per line)")
    ],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Perform bulk IP analysis from a file.

    The file should contain one IP address per line.

    Example:
        vertice ip bulk ips.txt
    """
    results = []
    try:
        with open(file, "r") as f:
            ips = [line.strip() for line in f if line.strip()]

        if not ips:
            console.print("[yellow]No IP addresses found in the file.[/yellow]")
            return

        console.print(f"[dim]Analyzing {len(ips)} IP addresses from {file}...[/dim]")

        for ip_address in ips:
            if verbose:
                console.print(f"[dim]Analyzing {ip_address}...[/dim]")
            with spinner_task(f"Analyzing IP: {ip_address}..."):
                result = await connector.analyze_ip(ip_address)
                if result:
                    results.append(result)

        if json_output:
            # Convert to dict for json output
            results_dict = {"results": results, "count": len(results)}
            print_json(results_dict)
        else:
            # For bulk, a simple table or summary might be better, or iterate and print each
            console.print("[bold green]Bulk IP Analysis Results:[/bold green]")
            for result in results:
                if isinstance(result, dict):
                    format_ip_analysis(result, console)
                    console.print("\n" + "-" * 80 + "\n")  # Separator

    except Exception as e:
        print_error(f"An error occurred during bulk analysis: {e}")
