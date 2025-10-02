import click
import asyncio
from rich.console import Console
from rich.table import Table
from ..connectors.threat_intel import ThreatIntelConnector
from ..utils.output import print_json, spinner_task, print_error, print_table

console = Console()

@click.group()
def threat():
    """Threat intelligence operations."""
    pass

@threat.command()
@click.argument('indicator')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def lookup(indicator, output_json_flag, verbose):
    """Lookup threat indicator.

    Example:
        vertice threat lookup malicious.com
    """
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

            if output_json_flag:
                print_json(result)
            else:
                if result:
                    # Assuming result is a dict, convert to list of dicts for print_table
                    # Or format it nicely with Rich Panel/Table if a specific format is defined
                    console.print(f"[bold green]Threat Lookup Result for {indicator}:[/bold green]")
                    # For now, just print the dictionary as a simple table
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

@threat.command()
@click.argument('target')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def check(target, output_json_flag, verbose):
    """Check a target for known threats.

    Example:
        vertice threat check malware.exe
    """
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
                # Assuming a generic check endpoint for now
                result = await connector.lookup_threat(target) # Reusing lookup for simplicity

            if output_json_flag:
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

@threat.command()
@click.argument('file_path')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def scan(file_path, output_json_flag, verbose):
    """Scan a file for threats.

    Example:
        vertice threat scan /path/to/suspicious.zip
    """
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
                # Assuming a file scan endpoint, for now, reuse lookup_threat
                # In a real scenario, this would involve sending the file content
                result = await connector.lookup_threat(file_path) # Reusing lookup for simplicity

            if output_json_flag:
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