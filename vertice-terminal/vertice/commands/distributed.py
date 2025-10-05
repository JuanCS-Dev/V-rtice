"""
🌐 DISTRIBUTED Command - Distributed Organism Operations
=========================================================

Distributed organism edge + cloud operations.

FASE 10 Commands (Distributed Organism):
    edge - Get edge agent status and metrics
    scan - Coordinate multi-edge scan with load balancing
    metrics - Get aggregated global metrics
    topology - View distributed organism topology

Examples:
    vcli distributed edge
    vcli distributed edge --agent edge-001
    vcli distributed scan targets.json --type comprehensive
    vcli distributed metrics --time-range 30
    vcli distributed topology
"""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing_extensions import Annotated

from ..connectors.distributed import DistributedConnector
from ..utils.output import output_json, print_error, print_success
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="distributed",
    help="🌐 Distributed organism operations (edge + cloud)",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def edge(
    agent_id: Annotated[str, typer.Option("--agent", "-a", help="Specific agent ID")] = None,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Get edge agent status and metrics.

    Examples:
        vcli distributed edge
        vcli distributed edge --agent edge-001
    """
    require_auth()

    async def _execute():
        connector = DistributedConnector()
        try:
            if agent_id:
                primoroso.info(f"[bold]Fetching edge status:[/bold] {agent_id}")
            else:
                primoroso.info("[bold]Fetching all edge agents status...[/bold]")

            result = await connector.get_edge_status(agent_id)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[cyan]Edge Status{' - ' + agent_id if agent_id else ''}[/cyan]",
                        border_style="cyan"
                    ))
                print_success("Status retrieved")
            else:
                print_error("Status retrieval failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def scan(
    targets_file: Annotated[str, typer.Argument(help="Path to targets JSON file")],
    scan_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Scan type: comprehensive, quick, deep")
    ] = "comprehensive",
    distribute: Annotated[bool, typer.Option("--distribute/--no-distribute", help="Enable load distribution")] = True,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Coordinate scan across multiple edge agents.

    Provide JSON file with:
    ["192.168.1.0/24", "10.0.0.0/16", "example.com"]

    Examples:
        vcli distributed scan targets.json --type comprehensive
        vcli distributed scan networks.json --type quick --no-distribute
    """
    require_auth()

    async def _execute():
        import json as json_lib

        try:
            with open(targets_file, 'r') as f:
                targets = json_lib.load(f)
        except Exception as e:
            print_error(f"Failed to load targets file: {e}")
            raise typer.Exit(1)

        connector = DistributedConnector()
        try:
            primoroso.info(f"[bold]Coordinating scan:[/bold] {len(targets)} targets ({scan_type})")
            if distribute:
                primoroso.info("[green]Load distribution enabled[/green]")

            result = await connector.coordinate_multi_edge_scan(targets, scan_type, distribute)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[yellow]Multi-Edge Scan ({scan_type})[/yellow]",
                        border_style="yellow"
                    ))
                print_success("Scan coordination complete")
            else:
                print_error("Scan coordination failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def metrics(
    time_range: Annotated[int, typer.Option("--time-range", "-t", help="Time range in minutes")] = 60,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Get aggregated global metrics from all edge agents.

    Examples:
        vcli distributed metrics --time-range 30
        vcli distributed metrics --time-range 120
    """
    require_auth()

    async def _execute():
        connector = DistributedConnector()
        try:
            primoroso.info(f"[bold]Fetching global metrics:[/bold] last {time_range} minutes")
            result = await connector.get_global_metrics(time_range)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[magenta]Global Metrics ({time_range}m)[/magenta]",
                        border_style="magenta"
                    ))
                print_success("Metrics retrieved")
            else:
                print_error("Metrics retrieval failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def topology(
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    View distributed organism topology.

    Shows edge agents, health status, connections, and regions.

    Examples:
        vcli distributed topology
        vcli distributed topology --json
    """
    require_auth()

    async def _execute():
        connector = DistributedConnector()
        try:
            primoroso.info("[bold]Fetching topology...[/bold]")
            result = await connector.get_topology()

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title="[bright_blue]Distributed Organism Topology[/bright_blue]",
                        border_style="bright_blue"
                    ))
                print_success("Topology retrieved")
            else:
                print_error("Topology retrieval failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


if __name__ == "__main__":
    app()
