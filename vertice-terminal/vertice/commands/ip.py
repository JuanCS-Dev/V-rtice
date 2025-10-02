import click
import asyncio
from rich.console import Console
from rich.table import Table
from ..connectors.ip_intel import IPIntelConnector
from ..utils.output import format_ip_analysis, print_json, spinner_task, print_error

console = Console()

@click.group()
def ip():
    """IP Intelligence commands"""
    pass

@ip.command()
@click.argument('ip_address')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(ip_address, output_json_flag, quiet, verbose):
    """Analyze an IP address

    Example:
        vertice ip analyze 8.8.8.8
        vertice ip analyze 8.8.8.8 --json
    """
    async def _analyze():
        connector = IPIntelConnector()

        try:
            # Health check
            if verbose:
                console.print("[dim]Checking service health...[/dim]")

            with spinner_task("Checking IP Intelligence service status..."):
                if not await connector.health_check():
                    print_error("IP Intelligence service is offline")
                    return # Exit if service is offline

            # Analyze
            if verbose:
                console.print(f"[dim]Analyzing {ip_address}...[/dim]")

            with spinner_task(f"Analyzing IP: {ip_address}..."):
                result = await connector.analyze_ip(ip_address)

            # Output
            if output_json_flag:
                print_json(result)
            elif quiet:
                # Apenas threat status
                threat_level = result.get('reputation', {}).get('threat_level', 'unknown')
                print(threat_level.upper())
            else:
                # Rich table formatado
                format_ip_analysis(result, console)

        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_analyze())


@ip.command()
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
def my_ip(output_json_flag):
    """Detect your public IP

    Example:
        vertice ip my-ip
    """
    async def _my_ip():
        connector = IPIntelConnector()
        try:
            with spinner_task("Detecting public IP..."):
                ip = await connector.get_my_ip()
            if output_json_flag:
                print_json({"ip": ip})
            else:
                console.print(f"[green]Your IP:[/green] {ip}")
        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            await connector.close()

    asyncio.run(_my_ip())


@ip.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def bulk(file, output_json_flag, verbose):
    """Perform bulk IP analysis from a file.

    The file should contain one IP address per line.

    Example:
        vertice ip bulk ips.txt
    """
    async def _bulk():
        connector = IPIntelConnector()
        results = []
        try:
            with open(file, 'r') as f:
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
                    results.append(result)

            if output_json_flag:
                print_json(results)
            else:
                # For bulk, a simple table or summary might be better, or iterate and print each
                console.print("[bold green]Bulk IP Analysis Results:[/bold green]")
                for result in results:
                    format_ip_analysis(result, console)
                    console.print("\n" + "-"*80 + "\n") # Separator

        except Exception as e:
            print_error(f"An error occurred during bulk analysis: {e}")
        finally:
            await connector.close()

    asyncio.run(_bulk())
