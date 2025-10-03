"""
Network and Port Scanning Commands - PRODUCTION READY
Uses real nmap_service and vuln_scanner_service backends
"""

import typer
import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from typing import Optional
from ..utils.output import (
    print_json,
    spinner_task,
    print_error,
    print_success,
    print_info,
)
from ..utils.auth import require_auth
from ..connectors.nmap import NmapConnector
from ..connectors.vuln_scanner import VulnScannerConnector
from ..config.context_manager import get_context_manager, ContextError

console = Console()

app = typer.Typer(
    name="scan", help="🌐 Network and port scanning operations", rich_markup_mode="rich"
)


def save_scan_result(result: dict, scan_type: str, target: str):
    """
    Salva resultado do scan no contexto ativo (se houver)

    Args:
        result: Resultado do scan
        scan_type: Tipo de scan (port, vuln, network)
        target: Alvo do scan
    """
    try:
        ctx_manager = get_context_manager()
        context = ctx_manager.get_current()

        if context is None:
            # Sem contexto ativo, não salva
            return

        # Criar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = (
            f"{scan_type}_{target.replace('/', '_').replace(':', '_')}_{timestamp}.json"
        )

        # Caminho do arquivo
        output_dir = Path(context.output_dir) / "scans"
        output_file = output_dir / filename

        # Salvar resultado
        with open(output_file, "w") as f:
            json.dump(
                {
                    "scan_type": scan_type,
                    "target": target,
                    "timestamp": datetime.now().isoformat(),
                    "context": context.name,
                    "result": result,
                },
                f,
                indent=2,
            )

        print_info(f"💾 Resultado salvo em: {output_file}")

    except ContextError:
        # Sem contexto, ignora
        pass
    except Exception as e:
        console.print(
            f"[dim yellow]Aviso: Não foi possível salvar resultado: {e}[/dim yellow]"
        )


from ..utils.decorators import with_connector


@app.command()
@with_connector(NmapConnector)
def ports(
    target: Annotated[str, typer.Argument(help="Target IP or hostname to scan")],
    ports_range: Annotated[
        Optional[str],
        typer.Option("--ports", "-p", help="Port range (e.g., 1-1000, 22,80,443)"),
    ] = None,
    scan_type: Annotated[
        str, typer.Option("--type", "-t", help="Scan type: quick, full, stealth")
    ] = "quick",
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Scan target for open ports using Nmap.

    Examples:
        vertice scan ports example.com
        vertice scan ports 192.168.1.1 --ports 1-1000 --type full
        vertice scan ports scanme.nmap.org -j
    """
    # Perform scan
    if verbose:
        console.print(f"[dim]Scanning ports on: {target}...[/dim]")

    with spinner_task(f"Scanning ports on {target}..."):
        result = connector.scan_ports(target, ports=ports_range, scan_type=scan_type)

    if not result:
        return

    # Save result to context (if active)
    save_scan_result(result, "port", target)

    # Display results
    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Port Scan Complete[/bold green]\n")
        console.print(f"[cyan]Target:[/cyan] {result.get('target', target)}")
        console.print(f"[cyan]Status:[/cyan] {result.get('status', 'completed')}\n")

        if "open_ports" in result and result["open_ports"]:
            table = Table(
                title="Open Ports", show_header=True, header_style="bold magenta"
            )
            table.add_column("Port", style="cyan", justify="right")
            table.add_column("State", style="green")
            table.add_column("Service", style="yellow")
            table.add_column("Version", style="dim")

            for port_info in result["open_ports"]:
                if isinstance(port_info, dict):
                    table.add_row(
                        str(port_info.get("port", "")),
                        port_info.get("state", "open"),
                        port_info.get("service", "unknown"),
                        port_info.get("version", ""),
                    )
                else:
                    table.add_row(str(port_info), "open", "unknown", "")

            console.print(table)
        else:
            console.print("[yellow]No open ports found.[/yellow]")


@app.command()
@with_connector(NmapConnector)
def nmap(
    target: Annotated[str, typer.Argument(help="Target for nmap scan")],
    arguments: Annotated[
        Optional[str], typer.Option("--args", "-a", help="Custom nmap arguments")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Perform custom Nmap scan with arguments.

    Examples:
        vertice scan nmap example.com
        vertice scan nmap 192.168.1.1 --args "-sV -sC"
        vertice scan nmap scanme.nmap.org --args "-O -T4" -j
    """
    if verbose:
        console.print(f"[dim]Performing Nmap scan on: {target}...[/dim]")

    with spinner_task(f"Running Nmap scan on {target}..."):
        result = connector.scan_nmap(target, arguments=arguments)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Nmap Scan Complete[/bold green]\n")
        if "output" in result:
            console.print(result["output"])
        else:
            console.print(f"[cyan]Target:[/cyan] {result.get('target', target)}")
            console.print(f"[cyan]Status:[/cyan] {result.get('status', 'completed')}")


@app.command()
@with_connector(VulnScannerConnector)
def vulns(
    target: Annotated[str, typer.Argument(help="Target to scan for vulnerabilities")],
    scan_type: Annotated[
        str, typer.Option("--type", "-t", help="Scan type: quick, full, intensive")
    ] = "full",
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Scan target for vulnerabilities.

    Examples:
        vertice scan vulns example.com
        vertice scan vulns 192.168.1.1 --type intensive
        vertice scan vulns target.com -j
    """
    if verbose:
        console.print(f"[dim]Scanning vulnerabilities on: {target}...[/dim]")

    with spinner_task(
        f"Scanning for vulnerabilities on {target}... (this may take a while)"
    ):
        result = connector.scan_vulnerabilities(target, scan_type=scan_type)

    if not result:
        return

    # Save result to context (if active)
    save_scan_result(result, "vuln", target)

    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Vulnerability Scan Complete[/bold green]\n")
        console.print(f"[cyan]Target:[/cyan] {result.get('target', target)}")
        console.print(f"[cyan]Status:[/cyan] {result.get('status', 'completed')}\n")

        if "vulnerabilities" in result and result["vulnerabilities"]:
            table = Table(
                title="Vulnerabilities Found", show_header=True, header_style="bold red"
            )
            table.add_column("CVE", style="cyan")
            table.add_column("Severity", style="red", justify="center")
            table.add_column("Description", style="white")
            table.add_column("CVSS", style="yellow", justify="right")

            for vuln in result["vulnerabilities"]:
                severity = vuln.get("severity", "unknown").upper()
                severity_color = {
                    "CRITICAL": "bold red",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "green",
                }.get(severity, "white")

                table.add_row(
                    vuln.get("id", vuln.get("cve", "N/A")),
                    f"[{severity_color}]{severity}[/{severity_color}]",
                    vuln.get("description", "No description")[:50] + "...",
                    str(vuln.get("cvss", "N/A")),
                )

            console.print(table)
            console.print(
                f"\n[bold]Total vulnerabilities found:[/bold] {len(result['vulnerabilities'])}"
            )
        else:
            console.print("[green]✓ No vulnerabilities found.[/green]")


@app.command()
@with_connector(NmapConnector)
async def network(
    network: Annotated[
        str, typer.Option("--network", "-n", help="Network CIDR to scan")
    ] = "192.168.1.0/24",
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """
    Network discovery scan.

    Examples:
        vertice scan network
        vertice scan network --network 10.0.0.0/24
        vertice scan network -n 172.16.0.0/16 -j
    """
    with spinner_task(f"Discovering hosts on {network}..."):
        result = await connector.scan_network(network)

    if not result:
        return

    # Save result to context (if active)
    save_scan_result(result, "network", network)

    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Network Discovery Complete[/bold green]\n")
        console.print(f"[cyan]Network:[/cyan] {result.get('network', network)}\n")

        if "hosts" in result and result["hosts"]:
            table = Table(
                title="Discovered Hosts", show_header=True, header_style="bold cyan"
            )
            table.add_column("IP Address", style="cyan")
            table.add_column("Hostname", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("MAC", style="dim")

            for host in result["hosts"]:
                table.add_row(
                    host.get("ip", "N/A"),
                    host.get("hostname", "Unknown"),
                    host.get("status", "up"),
                    host.get("mac", "N/A"),
                )

            console.print(table)
            console.print(f"\n[bold]Total hosts found:[/bold] {len(result['hosts'])}")
        else:
            console.print("[yellow]No hosts discovered.[/yellow]")
