"""
Vértice Project Management - Workspace Operations
==================================================

Persistent state management for security engagements.
Create projects, manage findings, query workspace.

Examples:
    vcli project create pentest-acme --scope "10.10.1.0/24"
    vcli project add-host 10.10.1.5 --hostname target.local
    vcli project add-port 22 --host-id 1 --service ssh
    vcli project stats
"""

import typer
from typing import Optional, List
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

from ..workspace import WorkspaceManager, ProjectExistsError, ProjectNotFoundError, WorkspaceError
from ..utils import primoroso
from ..utils.output import print_json, print_error

console = Console()

app = typer.Typer(
    name="project",
    help="📁 Project workspace management - persistent state for security engagements",
    rich_markup_mode="rich",
)

# Global workspace manager instance
workspace = WorkspaceManager()


@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Project name (unique identifier)")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Project description")] = "",
    scope: Annotated[Optional[List[str]], typer.Option("--scope", "-s", help="Target scope (CIDRs/domains)")] = None,
):
    """Create new project workspace.

    Creates SQLite database, evidence directory, and Git repository.

    Examples:
        vcli project create pentest-acme
        vcli project create bug-bounty --desc "Acme Corp Bug Bounty" --scope "acme.com" --scope "*.acme.com"
        vcli project create internal-audit --scope "10.0.0.0/8" --scope "192.168.0.0/16"
    """
    try:
        project = workspace.create_project(name, description, scope or [])

        primoroso.success(f"Project '{name}' created successfully")
        console.print(f"  [dim]Location:[/dim] {workspace.workspace_root / name}")
        console.print(f"  [dim]Database:[/dim] state.db")
        console.print(f"  [dim]Evidence:[/dim] evidence/")

        if scope:
            console.print(f"  [dim]Scope:[/dim] {', '.join(scope)}")

    except ProjectExistsError as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def list(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """List all projects with statistics.

    Examples:
        vcli project list
        vcli project list --json
    """
    projects = workspace.list_projects()

    if not projects:
        primoroso.warning("No projects found. Create one with: vcli project create <name>")
        return

    if json_output:
        print_json({"projects": projects, "count": len(projects)})
        return

    # Rich table
    table = Table(title="📁 Vértice Projects", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Hosts", justify="right")
    table.add_column("Vulns", justify="right")
    table.add_column("Created", style="dim")

    for proj in projects:
        status_icon = {
            "active": "🟢",
            "completed": "✅",
            "archived": "📦"
        }.get(proj["status"], "❓")

        table.add_row(
            proj["name"],
            f"{status_icon} {proj['status']}",
            str(proj["hosts"]),
            str(proj["vulns"]),
            proj["created_at"].strftime("%Y-%m-%d") if hasattr(proj["created_at"], "strftime") else str(proj["created_at"])
        )

    console.print(table)


@app.command()
def switch(
    name: Annotated[str, typer.Argument(help="Project name to switch to")],
):
    """Switch active project.

    Examples:
        vcli project switch pentest-acme
    """
    try:
        workspace.switch_project(name)
        primoroso.success(f"Switched to project: {name}")
    except ProjectNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def delete(
    name: Annotated[str, typer.Argument(help="Project name to delete")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
):
    """Delete project (requires confirmation).

    WARNING: This permanently deletes all project data.

    Examples:
        vcli project delete old-project
        vcli project delete old-project --yes
    """
    if not yes:
        confirm = typer.confirm(f"⚠️  Delete project '{name}' and all its data?")
        if not confirm:
            primoroso.info("Deletion cancelled")
            return

    try:
        workspace.delete_project(name, confirm=True)
        primoroso.success(f"Project '{name}' deleted")
    except (ProjectNotFoundError, WorkspaceError) as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def status(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Show current project status and statistics.

    Examples:
        vcli project status
        vcli project status --json
    """
    project = workspace.get_current_project()

    if not project:
        primoroso.warning("No active project. Use: vcli project switch <name>")
        return

    stats = workspace.get_stats()

    if json_output:
        print_json({
            "project": project.name,
            "status": project.status,
            "description": project.description,
            "scope": project.scope,
            **stats
        })
        return

    # Rich panel display
    content = f"""[bold]Project:[/bold] {project.name}
[bold]Status:[/bold] {project.status}
[bold]Description:[/bold] {project.description or '[dim]None[/dim]'}
[bold]Scope:[/bold] {', '.join(project.scope) if project.scope else '[dim]None[/dim]'}

[bold cyan]Statistics:[/bold cyan]
  • Hosts: {stats['hosts']}
  • Ports: {stats['ports']}
  • Vulnerabilities: {stats['vulns']} ([red]Critical: {stats['vulns_critical']}[/red], [yellow]High: {stats['vulns_high']}[/yellow])
  • Credentials: {stats['credentials']}"""

    panel = Panel(content, title="📊 Project Status", border_style="cyan")
    console.print(panel)


@app.command()
def add_host(
    ip_address: Annotated[str, typer.Argument(help="IP address")],
    hostname: Annotated[Optional[str], typer.Option("--hostname", "-h", help="Hostname")] = None,
    os_family: Annotated[Optional[str], typer.Option("--os", help="OS family (Linux, Windows, etc.)")] = None,
    state: Annotated[str, typer.Option("--state", help="Host state (up/down/unknown)")] = "up",
):
    """Add host to current project.

    Examples:
        vcli project add-host 10.10.1.5
        vcli project add-host 10.10.1.5 --hostname target.local --os Linux
        vcli project add-host 192.168.1.100 --hostname dc01 --os Windows --state up
    """
    try:
        kwargs = {"state": state}
        if os_family:
            kwargs["os_family"] = os_family

        host = workspace.add_host(ip_address, hostname, **kwargs)

        primoroso.success(f"Host added: {ip_address}")
        console.print(f"  [dim]ID:[/dim] {host.id}")
        if hostname:
            console.print(f"  [dim]Hostname:[/dim] {hostname}")
        if os_family:
            console.print(f"  [dim]OS:[/dim] {os_family}")

    except WorkspaceError as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def add_port(
    host_id: Annotated[int, typer.Argument(help="Host ID")],
    port: Annotated[int, typer.Argument(help="Port number")],
    protocol: Annotated[str, typer.Option("--protocol", "-p", help="Protocol (tcp/udp/sctp)")] = "tcp",
    service: Annotated[Optional[str], typer.Option("--service", "-s", help="Service name (http, ssh, etc.)")] = None,
    version: Annotated[Optional[str], typer.Option("--version", "-v", help="Service version")] = None,
    state: Annotated[str, typer.Option("--state", help="Port state (open/closed/filtered)")] = "open",
):
    """Add port to host.

    Examples:
        vcli project add-port 1 22 --service ssh --version "OpenSSH 7.4"
        vcli project add-port 1 80 --service http --state open
        vcli project add-port 2 445 --protocol tcp --service smb
    """
    try:
        kwargs = {"state": state}
        if service:
            kwargs["service"] = service
        if version:
            kwargs["version"] = version

        port_obj = workspace.add_port(host_id, port, protocol, **kwargs)

        primoroso.success(f"Port added: {port}/{protocol}")
        console.print(f"  [dim]ID:[/dim] {port_obj.id}")
        console.print(f"  [dim]Host ID:[/dim] {host_id}")
        if service:
            console.print(f"  [dim]Service:[/dim] {service}")
        if version:
            console.print(f"  [dim]Version:[/dim] {version}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def add_vuln(
    host_id: Annotated[int, typer.Argument(help="Host ID")],
    title: Annotated[str, typer.Argument(help="Vulnerability title")],
    severity: Annotated[str, typer.Argument(help="Severity (critical/high/medium/low/info)")],
    cve_id: Annotated[Optional[str], typer.Option("--cve", help="CVE ID")] = None,
    description: Annotated[Optional[str], typer.Option("--desc", "-d", help="Description")] = None,
    cvss_score: Annotated[Optional[float], typer.Option("--cvss", help="CVSS score")] = None,
):
    """Add vulnerability to host.

    Examples:
        vcli project add-vuln 1 "SQL Injection" high --desc "Login form vulnerable"
        vcli project add-vuln 2 "EternalBlue" critical --cve CVE-2017-0144 --cvss 9.8
    """
    try:
        kwargs = {}
        if cve_id:
            kwargs["cve_id"] = cve_id
        if description:
            kwargs["description"] = description
        if cvss_score:
            kwargs["cvss_score"] = cvss_score

        vuln = workspace.add_vulnerability(host_id, title, severity, **kwargs)

        primoroso.success(f"Vulnerability added: {title}")
        console.print(f"  [dim]ID:[/dim] {vuln.id}")
        console.print(f"  [dim]Severity:[/dim] {severity}")
        if cve_id:
            console.print(f"  [dim]CVE:[/dim] {cve_id}")
        if cvss_score:
            console.print(f"  [dim]CVSS:[/dim] {cvss_score}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def stats(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Show detailed project statistics.

    Examples:
        vcli project stats
        vcli project stats --json
    """
    project = workspace.get_current_project()

    if not project:
        primoroso.warning("No active project. Use: vcli project switch <name>")
        return

    stats = workspace.get_stats()

    if json_output:
        print_json(stats)
        return

    # Rich display
    table = Table(title=f"📊 Statistics: {project.name}", show_header=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="green")

    table.add_row("Hosts", str(stats["hosts"]))
    table.add_row("Ports", str(stats["ports"]))
    table.add_row("Total Vulnerabilities", str(stats["vulns"]))
    table.add_row("  🔴 Critical", str(stats["vulns_critical"]))
    table.add_row("  🟠 High", str(stats["vulns_high"]))
    table.add_row("Credentials", str(stats["credentials"]))

    console.print(table)


@app.command()
def commit(
    message: Annotated[str, typer.Argument(help="Commit message")],
):
    """Commit current project state to Git.

    Creates versioned snapshot for audit trail and rollback capability.

    Examples:
        vcli project commit "Initial reconnaissance complete"
        vcli project commit "Added 5 critical vulns"
    """
    try:
        workspace.commit(message)
        primoroso.success(f"Committed: {message}")
    except WorkspaceError as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def query(
    question: Annotated[str, typer.Argument(help="Natural language question")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Query workspace using natural language (Maximus AI integration).

    Examples:
        vcli project query "show all web servers"
        vcli project query "what hosts have critical vulns?"
        vcli project query "find SSH servers with weak auth"

    Note: Full NL query integration with Maximus AI coming in Phase 1.4
    """
    result = workspace.query_nl(question)

    if json_output:
        print_json(result)
    else:
        primoroso.warning("Natural language queries not yet fully implemented")
        console.print(f"  [dim]Question:[/dim] {question}")
        console.print(f"  [dim]Status:[/dim] Integration with Maximus AI pending (Phase 1.4)")


@app.command()
def hosts(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    state: Annotated[Optional[str], typer.Option("--state", help="Filter by state (up/down/unknown)")] = None,
):
    """List all hosts in current project.

    Examples:
        vcli project hosts
        vcli project hosts --state up
        vcli project hosts --json
    """
    try:
        filters = {"state": state} if state else None
        hosts_list = workspace.query_hosts(filters)

        if not hosts_list:
            primoroso.info("No hosts found in current project")
            return

        if json_output:
            hosts_data = [
                {
                    "id": h.id,
                    "ip_address": h.ip_address,
                    "hostname": h.hostname,
                    "os_family": h.os_family,
                    "state": h.state,
                    "discovered_at": h.discovered_at.isoformat() if h.discovered_at else None
                }
                for h in hosts_list
            ]
            print_json({"hosts": hosts_data, "count": len(hosts_data)})
            return

        # Rich table
        table = Table(title="🖥️  Hosts", show_header=True, header_style="bold cyan")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("IP Address", style="green")
        table.add_column("Hostname", style="yellow")
        table.add_column("OS", style="blue")
        table.add_column("State")

        for host in hosts_list:
            state_icon = {"up": "🟢", "down": "🔴", "unknown": "❓"}.get(host.state, "❓")

            table.add_row(
                str(host.id),
                host.ip_address,
                host.hostname or "[dim]N/A[/dim]",
                host.os_family or "[dim]N/A[/dim]",
                f"{state_icon} {host.state}"
            )

        console.print(table)

    except WorkspaceError as e:
        print_error(str(e))
        raise typer.Exit(code=1)


@app.command()
def vulns(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    severity: Annotated[Optional[str], typer.Option("--severity", "-s", help="Filter by severity")] = None,
):
    """List all vulnerabilities in current project.

    Examples:
        vcli project vulns
        vcli project vulns --severity critical
        vcli project vulns --json
    """
    try:
        vulns_list = workspace.query_vulnerabilities(severity=severity)

        if not vulns_list:
            primoroso.info("No vulnerabilities found")
            return

        if json_output:
            vulns_data = [
                {
                    "id": v.id,
                    "title": v.title,
                    "severity": v.severity,
                    "cve_id": v.cve_id,
                    "cvss_score": v.cvss_score,
                    "exploitable": v.exploitable,
                    "host_id": v.host_id
                }
                for v in vulns_list
            ]
            print_json({"vulnerabilities": vulns_data, "count": len(vulns_data)})
            return

        # Rich table
        table = Table(title="🔓 Vulnerabilities", show_header=True, header_style="bold cyan")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Title", style="yellow", no_wrap=False)
        table.add_column("Severity")
        table.add_column("CVE", style="cyan")
        table.add_column("CVSS", justify="right")
        table.add_column("Exploitable")

        for vuln in vulns_list:
            severity_style = {
                "critical": "[red bold]🔴 CRITICAL[/red bold]",
                "high": "[red]🟠 HIGH[/red]",
                "medium": "[yellow]🟡 MEDIUM[/yellow]",
                "low": "[green]🟢 LOW[/green]",
                "info": "[dim]ℹ️  INFO[/dim]"
            }.get(vuln.severity, vuln.severity)

            exploit_icon = "✅" if vuln.exploitable else "❌"

            table.add_row(
                str(vuln.id),
                vuln.title[:50] + "..." if len(vuln.title) > 50 else vuln.title,
                severity_style,
                vuln.cve_id or "[dim]N/A[/dim]",
                str(vuln.cvss_score) if vuln.cvss_score else "[dim]N/A[/dim]",
                exploit_icon
            )

        console.print(table)

    except WorkspaceError as e:
        print_error(str(e))
        raise typer.Exit(code=1)
