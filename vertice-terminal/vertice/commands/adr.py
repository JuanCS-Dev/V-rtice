import click
import asyncio
from rich.console import Console
from rich.table import Table
from ..connectors.adr_core import ADRCoreConnector
from ..utils.output import print_json, spinner_task, print_error, print_table

console = Console()

@click.group()
def adr():
    """ADR detection and response."""
    pass

@adr.command()
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def status(output_json_flag, verbose):
    """Check ADR system status.

    Example:
        vertice adr status
    """
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

            if output_json_flag:
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

@adr.command()
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def metrics(output_json_flag, verbose):
    """Get ADR metrics (MTTR, detection rate).

    Example:
        vertice adr metrics
    """
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
                # Assuming an endpoint for metrics
                result = await connector._get("/api/adr/metrics") # Using _get directly for now

            if output_json_flag:
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

@adr.group()
def analyze():
    """Manual analysis operations for ADR.

    Example:
        vertice adr analyze file /path/to/suspicious.log
    """
    pass

@analyze.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def file(path, output_json_flag, verbose):
    """Analyze a file for ADR.

    Example:
        vertice adr analyze file /path/to/suspicious.log
    """
    async def _file_analyze():
        connector = ADRCoreConnector()
        try:
            if verbose:
                console.print("[dim]Checking ADR Core service status...[/dim]")
            with spinner_task("Checking ADR Core service status..."):
                if not await connector.health_check():
                    print_error("ADR Core service is offline")
                    return

            if verbose:
                console.print(f"[dim]Analyzing file: {path}...[/dim]")
            with spinner_task(f"Analyzing file: {path}..."):
                # Assuming an endpoint for file analysis
                result = await connector._post("/api/adr/analyze/file", json={"file_path": path}) # Using _post directly for now

            if output_json_flag:
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

@analyze.command()
@click.argument('ip')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def network(ip, output_json_flag, verbose):
    """Analyze network traffic for an IP for ADR.

    Example:
        vertice adr analyze network 192.168.1.1
    """
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
                # Assuming an endpoint for network analysis
                result = await connector._post("/api/adr/analyze/network", json={"ip_address": ip}) # Using _post directly for now

            if output_json_flag:
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

@analyze.command()
@click.argument('cmd')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def process(cmd, output_json_flag, verbose):
    """Analyze a process for ADR.

    Example:
        vertice adr analyze process "ls -la"
    """
    async def _process_analyze():
        connector = ADRCoreConnector()
        try:
            if verbose:
                console.print("[dim]Checking ADR Core service status...[/dim]")
            with spinner_task("Checking ADR Core service status..."):
                if not await connector.health_check():
                    print_error("ADR Core service is offline")
                    return

            if verbose:
                console.print(f"[dim]Analyzing process: {cmd}...[/dim]")
            with spinner_task(f"Analyzing process: {cmd}..."):
                # Assuming an endpoint for process analysis
                result = await connector._post("/api/adr/analyze/process", json={"command": cmd}) # Using _post directly for now

            if output_json_flag:
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