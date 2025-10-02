import click
import asyncio
from rich.console import Console
from rich.table import Table
from ..utils.output import print_json, spinner_task, print_error, print_table

console = Console()

@click.group()
def hunt():
    """Threat hunting operations."""
    pass

@hunt.command()
@click.argument('query')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def search(query, output_json_flag, verbose):
    """Hunt for IOCs based on a query.

    Example:
        vertice hunt search "malicious.com"
    """
    async def _search():
        try:
            if verbose:
                console.print(f"[dim]Searching for IOCs with query: {query}...[/dim]")
            with spinner_task(f"Searching for IOCs with query: {query}..."):
                # Simulate API call to a threat hunting service
                await asyncio.sleep(2) # Simulate search time
                results = [
                    {"ioc": query, "type": "Domain", "reputation": "Malicious", "last_seen": "2025-09-30"},
                    {"ioc": "1.2.3.4", "type": "IP Address", "reputation": "Suspicious", "last_seen": "2025-09-29"}
                ]

            if output_json_flag:
                print_json(results)
            else:
                if results:
                    console.print(f"[bold green]Threat Hunt Results for '{query}':[/bold green]")
                    table = Table(title=f"IOCs for '{query}'")
                    table.add_column("IOC", style="cyan")
                    table.add_column("Type", style="magenta")
                    table.add_column("Reputation", style="yellow")
                    table.add_column("Last Seen", style="white")
                    for item in results:
                        table.add_row(item["ioc"], item["type"], item["reputation"], item["last_seen"])
                    console.print(table)
                else:
                    console.print(f"[yellow]No IOCs found for query: {query}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")

    asyncio.run(_search())

@hunt.command()
@click.argument('incident_id')
@click.option('--last', default='24h', help='Timeframe (e.g., 1h, 24h, 7d)')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def timeline(incident_id, last, output_json_flag, verbose):
    """Generate a timeline of activity for an incident.

    Example:
        vertice hunt timeline INC001 --last 48h
    """
    async def _timeline():
        try:
            if verbose:
                console.print(f"[dim]Generating timeline for incident {incident_id} for the last {last}...[/dim]")
            with spinner_task(f"Generating timeline for incident {incident_id}..."):
                # Simulate API call
                await asyncio.sleep(3) # Simulate timeline generation
                results = [
                    {"timestamp": "2025-10-01T08:00:00Z", "event": "Alert triggered", "source": "EDR"},
                    {"timestamp": "2025-10-01T08:15:00Z", "event": "User login", "source": "Auth Logs"},
                    {"timestamp": "2025-10-01T08:30:00Z", "event": "File modification", "source": "Filesystem"}
                ]

            if output_json_flag:
                print_json(results)
            else:
                if results:
                    console.print(f"[bold green]Timeline for Incident {incident_id} (Last {last}):[/bold green]")
                    table = Table(title=f"Incident {incident_id} Timeline")
                    table.add_column("Timestamp", style="cyan")
                    table.add_column("Event", style="magenta")
                    table.add_column("Source", style="white")
                    for item in results:
                        table.add_row(item["timestamp"], item["event"], item["source"])
                    console.print(table)
                else:
                    console.print(f"[yellow]No timeline data found for incident {incident_id}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")

    asyncio.run(_timeline())

@hunt.command()
@click.argument('ioc')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def pivot(ioc, output_json_flag, verbose):
    """Perform pivot analysis on an IOC to find related entities.

    Example:
        vertice hunt pivot "malicious.com"
    """
    async def _pivot():
        try:
            if verbose:
                console.print(f"[dim]Performing pivot analysis on IOC: {ioc}...[/dim]")
            with spinner_task(f"Performing pivot analysis on IOC: {ioc}..."):
                # Simulate API call
                await asyncio.sleep(2) # Simulate pivot analysis
                results = [
                    {"entity": "1.2.3.4", "type": "IP Address", "relation": "Connected to"},
                    {"entity": "user@example.com", "type": "Email", "relation": "Associated with"}
                ]

            if output_json_flag:
                print_json(results)
            else:
                if results:
                    console.print(f"[bold green]Pivot Analysis for IOC '{ioc}':[/bold green]")
                    table = Table(title=f"Related Entities for '{ioc}'")
                    table.add_column("Entity", style="cyan")
                    table.add_column("Type", style="magenta")
                    table.add_column("Relation", style="white")
                    for item in results:
                        table.add_row(item["entity"], item["type"], item["relation"])
                    console.print(table)
                else:
                    console.print(f"[yellow]No related entities found for IOC: {ioc}.[/yellow]")

        except Exception as e:
            print_error(f"An error occurred: {e}")

    asyncio.run(_pivot())