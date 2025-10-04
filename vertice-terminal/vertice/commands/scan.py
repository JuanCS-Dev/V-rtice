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
from vertice.utils import primoroso


@app.command()
@with_connector(NmapConnector)
def ports(
    target: Annotated[str, typer.Argument(help="Target IP or hostname to scan")],
    ports_range: Annotated[
        Optional[str],
        typer.Option("--ports", help="Port range (e.g., 1-1000, 22,80,443)"),
    ] = None,
    scan_type: Annotated[
        str, typer.Option("--type", help="Scan type: quick, full, stealth")
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
        primoroso.error("\n[bold green]✓ Port Scan Complete[/bold green]\n")
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
            primoroso.warning("No open ports found.")


@app.command()
def nmap(
    target: Annotated[str, typer.Argument(help="Target for nmap scan")],
    scan_type: Annotated[
        str, typer.Option("--type", help="Scan type: quick, full, vuln, service, os")
    ] = "quick",
    ports: Annotated[
        Optional[str], typer.Option("--ports", "-p", help="Port specification (e.g., '22,80,443' or '1-1000')")
    ] = None,
    timing: Annotated[
        Optional[str], typer.Option("--timing", "-T", help="Timing template (T0-T5)")
    ] = None,
    os_detection: Annotated[
        bool, typer.Option("--os", help="Enable OS detection")
    ] = False,
    workspace: Annotated[
        bool, typer.Option("--workspace", "-w", help="Auto-populate active workspace")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Execute Nmap scan using orchestration engine.

    🎯 Zero Context Switch - executes Nmap, parses results, optionally populates workspace.

    Scan Types:
      quick   - Fast scan (top 100 ports)
      full    - Comprehensive (all ports + version detection)
      vuln    - Vulnerability scan (NSE vuln scripts)
      service - Service/version detection only
      os      - OS detection

    Examples:
        vcli scan nmap 10.10.1.5
        vcli scan nmap 192.168.1.0/24 --type full
        vcli scan nmap target.com --type vuln --workspace
        vcli scan nmap scanme.nmap.org --ports "22,80,443" --os
        vcli scan nmap example.com --timing T4 -j
    """
    from ..core import NmapExecutor, NmapParser, ToolNotFoundError, ToolExecutionError
    from ..core.workspace_integration import populate_from_nmap
    from ..workspace import WorkspaceManager, WorkspaceError

    try:
        # Execute Nmap
        if verbose:
            console.print(f"[dim]Executing Nmap {scan_type} scan on: {target}...[/dim]")

        executor = NmapExecutor()

        with spinner_task(f"Running Nmap {scan_type} scan on {target}..."):
            result = executor.execute(
                target=target,
                scan_type=scan_type,
                ports=ports,
                os_detection=os_detection,
                timing=timing
            )

        if not result.success:
            primoroso.error(f"Nmap scan failed: {result.stderr[:200]}")
            return

        # Parse output
        parser = NmapParser()
        try:
            parsed = parser.parse(result.stdout)
        except ValueError as e:
            primoroso.error(f"Failed to parse Nmap output: {e}")
            if verbose:
                console.print(f"[dim]Raw output:\n{result.stdout[:500]}[/dim]")
            return

        # Auto-populate workspace if requested
        if workspace:
            try:
                ws = WorkspaceManager()
                current_project = ws.get_current_project()

                if not current_project:
                    primoroso.warning(
                        "No active workspace project. "
                        "Use 'vcli project create <name>' or 'vcli project switch <name>'"
                    )
                else:
                    with spinner_task("Populating workspace..."):
                        stats = populate_from_nmap(ws, parsed)

                    primoroso.success(
                        f"Workspace updated: {stats['hosts_added']} hosts, "
                        f"{stats['ports_added']} ports added to project '{current_project.name}'"
                    )

            except WorkspaceError as e:
                primoroso.warning(f"Workspace update failed: {e}")

        # Display results
        if json_output:
            print_json({
                "execution": {
                    "command": " ".join(result.command),
                    "duration": result.duration,
                    "success": result.success
                },
                "scan": parsed
            })
        else:
            primoroso.success("\n✓ Nmap Scan Complete\n")
            console.print(f"[cyan]Target:[/cyan] {target}")
            console.print(f"[cyan]Type:[/cyan] {scan_type}")
            console.print(f"[cyan]Duration:[/cyan] {result.duration:.2f}s\n")

            scan_info = parsed.get("scan_info", {})
            console.print(f"[dim]Hosts scanned: {scan_info.get('total_hosts', 0)} "
                         f"(up: {scan_info.get('up_hosts', 0)})[/dim]\n")

            if parsed.get("hosts"):
                for host_data in parsed["hosts"]:
                    console.print(f"[bold green]Host:[/bold green] {host_data['ip']}")

                    if host_data.get("hostname"):
                        console.print(f"  [cyan]Hostname:[/cyan] {host_data['hostname']}")

                    if host_data.get("os_family"):
                        console.print(f"  [cyan]OS:[/cyan] {host_data.get('os_family')}")
                        if host_data.get("os_version"):
                            console.print(f"      {host_data.get('os_version')}")

                    if host_data.get("ports"):
                        table = Table(show_header=True, header_style="bold magenta")
                        table.add_column("Port", style="cyan", justify="right")
                        table.add_column("State", style="green")
                        table.add_column("Service", style="yellow")
                        table.add_column("Version", style="dim")

                        for port in host_data["ports"]:
                            table.add_row(
                                f"{port['port']}/{port.get('protocol', 'tcp')}",
                                port.get("state", "unknown"),
                                port.get("service", "unknown"),
                                port.get("version", "")[:50]
                            )

                        console.print(table)
                    else:
                        primoroso.info("  No open ports detected")

                    console.print()  # Blank line between hosts

            else:
                primoroso.warning("No hosts found or all hosts are down")

    except ToolNotFoundError as e:
        primoroso.error(str(e))
        console.print("\n[dim]Install Nmap: sudo apt install nmap[/dim]")
    except ToolExecutionError as e:
        primoroso.error(f"Execution error: {e}")
    except Exception as e:
        primoroso.error(f"Unexpected error: {e}")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


@app.command()
def nuclei(
    target: Annotated[str, typer.Argument(help="Target URL for Nuclei scan")],
    scan_type: Annotated[
        str, typer.Option("--type", help="Scan type: quick, full, web, network, cve, custom")
    ] = "quick",
    templates: Annotated[
        Optional[str], typer.Option("--templates", "-t", help="Custom template path (for scan_type=custom)")
    ] = None,
    severity: Annotated[
        Optional[str], typer.Option("--severity", "-s", help="Severity filter (e.g., 'critical,high')")
    ] = None,
    rate_limit: Annotated[
        int, typer.Option("--rate-limit", help="Max requests per second")
    ] = 150,
    workspace: Annotated[
        bool, typer.Option("--workspace", "-w", help="Auto-populate active workspace")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Execute Nuclei vulnerability scan using orchestration engine.

    🎯 Zero Context Switch - executes Nuclei, parses results, optionally populates workspace.

    Scan Types:
      quick   - Critical and high severity only (fast)
      full    - All severity levels (comprehensive)
      web     - Web vulnerabilities + exposures
      network - Network-level vulnerabilities
      cve     - Known CVE checks only
      custom  - Custom template path (requires --templates)

    Examples:
        vcli scan nuclei https://example.com
        vcli scan nuclei http://10.10.1.5:8080 --type web
        vcli scan nuclei https://target.com --type cve --workspace
        vcli scan nuclei https://example.com --severity critical,high
        vcli scan nuclei https://example.com --type custom --templates /path/to/templates/
    """
    from ..core import NucleiExecutor, NucleiParser, ToolNotFoundError, ToolExecutionError
    from ..core.workspace_integration import populate_from_nuclei
    from ..workspace import WorkspaceManager, WorkspaceError

    try:
        # Execute Nuclei
        if verbose:
            console.print(f"[dim]Executing Nuclei {scan_type} scan on: {target}...[/dim]")

        executor = NucleiExecutor()

        # Parse severity if provided
        severity_list = None
        if severity:
            severity_list = [s.strip() for s in severity.split(",")]

        with spinner_task(f"Running Nuclei {scan_type} scan on {target}..."):
            result = executor.execute(
                target=target,
                scan_type=scan_type,
                templates=templates,
                severity=severity_list,
                rate_limit=rate_limit
            )

        if not result.success:
            primoroso.error(f"Nuclei scan failed: {result.stderr[:200]}")
            return

        # Parse output
        parser = NucleiParser()
        try:
            parsed = parser.parse(result.stdout)
        except ValueError as e:
            primoroso.error(f"Failed to parse Nuclei output: {e}")
            if verbose:
                console.print(f"[dim]Raw output:\n{result.stdout[:500]}[/dim]")
            return

        # Auto-populate workspace if requested
        if workspace:
            try:
                ws = WorkspaceManager()
                current_project = ws.get_current_project()

                if not current_project:
                    primoroso.warning(
                        "No active workspace project. "
                        "Use 'vcli project create <name>' or 'vcli project switch <name>'"
                    )
                else:
                    with spinner_task("Populating workspace..."):
                        stats = populate_from_nuclei(ws, parsed)

                    primoroso.success(
                        f"Workspace updated: {stats['hosts_added']} hosts, "
                        f"{stats['vulns_added']} vulnerabilities added to project '{current_project.name}'"
                    )

            except WorkspaceError as e:
                primoroso.warning(f"Workspace update failed: {e}")

        # Display results
        if json_output:
            print_json({
                "execution": {
                    "command": " ".join(result.command),
                    "duration": result.duration,
                    "success": result.success
                },
                "scan": parsed
            })
        else:
            primoroso.success("\n✓ Nuclei Scan Complete\n")
            console.print(f"[cyan]Target:[/cyan] {target}")
            console.print(f"[cyan]Type:[/cyan] {scan_type}")
            console.print(f"[cyan]Duration:[/cyan] {result.duration:.2f}s\n")

            scan_info = parsed.get("scan_info", {})
            console.print(
                f"[dim]Total findings: {scan_info.get('total_findings', 0)} "
                f"(critical: {scan_info.get('critical', 0)}, "
                f"high: {scan_info.get('high', 0)}, "
                f"medium: {scan_info.get('medium', 0)}, "
                f"low: {scan_info.get('low', 0)})[/dim]\n"
            )

            if parsed.get("vulnerabilities"):
                table = Table(show_header=True, header_style="bold red")
                table.add_column("Template ID", style="cyan", width=25)
                table.add_column("Severity", style="red", justify="center", width=10)
                table.add_column("Name", style="white", width=35)
                table.add_column("Matched At", style="dim", width=40)

                for vuln in parsed["vulnerabilities"]:
                    severity_val = vuln.get("severity", "info").upper()
                    severity_color = {
                        "CRITICAL": "bold red",
                        "HIGH": "red",
                        "MEDIUM": "yellow",
                        "LOW": "green",
                        "INFO": "blue"
                    }.get(severity_val, "white")

                    # Truncate long URLs
                    matched_at = vuln.get("matched_at", "")
                    if len(matched_at) > 40:
                        matched_at = matched_at[:37] + "..."

                    table.add_row(
                        vuln.get("template_id", "unknown")[:25],
                        f"[{severity_color}]{severity_val}[/{severity_color}]",
                        vuln.get("name", "Unknown")[:35],
                        matched_at
                    )

                console.print(table)
            else:
                primoroso.success("✓ No vulnerabilities found")

    except ToolNotFoundError as e:
        primoroso.error(str(e))
        console.print("\n[dim]Install Nuclei: https://github.com/projectdiscovery/nuclei[/dim]")
    except ToolExecutionError as e:
        primoroso.error(f"Execution error: {e}")
    except Exception as e:
        primoroso.error(f"Unexpected error: {e}")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


@app.command()
@with_connector(VulnScannerConnector)
def vulns(
    target: Annotated[str, typer.Argument(help="Target to scan for vulnerabilities")],
    scan_type: Annotated[
        str, typer.Option("--type", help="Scan type: quick, full, intensive")
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
        primoroso.error("\n[bold green]✓ Vulnerability Scan Complete[/bold green]\n")
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
            primoroso.success("✓ No vulnerabilities found.")


@app.command()
@with_connector(NmapConnector)
async def network(
    network: str = typer.Argument("192.168.1.0/24", help="Network CIDR to scan"),
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
        primoroso.error("\n[bold green]✓ Network Discovery Complete[/bold green]\n")
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
            primoroso.warning("No hosts discovered.")
