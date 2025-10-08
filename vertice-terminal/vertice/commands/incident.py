"""
🚨 INCIDENT Command - Incident Response & Orchestration

Gerenciamento completo de incidentes, cases, playbooks e evidências.

Exemplos:
    vertice incident create --title "Ransomware detected" --severity sev0
    vertice incident list --status investigating
    vertice incident update INC-123 --status contained
    vertice incident playbook run ransomware_response --incident INC-123
    vertice incident case create --title "APT Investigation"
    vertice incident timeline create --incident INC-123
    vertice incident evidence collect memory_dump --system srv-web-01
"""

import typer
from rich.console import Console
from rich.tree import Tree
from pathlib import Path
from typing import Optional
from datetime import datetime
import asyncio
from vertice.utils import primoroso
from vertice.utils.output import GeminiStyleTable, PrimordialPanel

app = typer.Typer(
    name="incident",
    help="🚨 Incident response and orchestration",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def create(
    title: str = typer.Option(..., "--title"),
    description: str = typer.Option("", "--description"),
    severity: str = typer.Option("sev2_medium", "--severity"),
    category: str = typer.Option("other", "--category"),
):
    """
    Cria novo incidente

    Examples:
        vertice incident create --title "Ransomware on srv-01" --severity sev0_critical --category ransomware
        vertice incident create -t "Phishing campaign" -s sev1_high -c phishing
    """
    from ..incident import IncidentManager, Incident, IncidentSeverity, IncidentCategory, IncidentStatus

    try:
        severity_enum = IncidentSeverity[severity.upper()]
        category_enum = IncidentCategory[category.upper()]
    except KeyError as e:
        primoroso.error(f"Invalid severity or category: {e}[/red]")
        raise typer.Exit(code=1)

    manager = IncidentManager()

    incident = Incident(
        id="",  # Will be auto-generated
        title=title,
        description=description,
        severity=severity_enum,
        status=IncidentStatus.NEW,
        category=category_enum,
        discovered_at=datetime.now(),
    )

    incident_id = manager.create_incident(incident)

    primoroso.error(f"\n[green]✅ Incident created: {incident_id}[/green]\n")

    _show_incident(manager.get_incident(incident_id))


@app.command()
def list(
    status: Optional[str] = typer.Option(None, "--status"),
    severity: Optional[str] = typer.Option(None, "--severity"),
    limit: int = typer.Option(50, "--limit"),
):
    """
    Lista incidentes

    Examples:
        vertice incident list
        vertice incident list --status investigating
        vertice incident list --severity sev0_critical
    """
    from ..incident import IncidentManager, IncidentStatus, IncidentSeverity

    manager = IncidentManager()

    # Parse filters
    status_filter = None
    if status:
        try:
            status_filter = IncidentStatus[status.upper()]
        except KeyError:
            primoroso.error(f"Invalid status: {status}[/red]")
            raise typer.Exit(code=1)

    severity_filter = None
    if severity:
        try:
            severity_filter = IncidentSeverity[severity.upper()]
        except KeyError:
            primoroso.error(f"Invalid severity: {severity}[/red]")
            raise typer.Exit(code=1)

    incidents = manager.list_incidents(
        status=status_filter,
        severity=severity_filter,
        limit=limit,
    )

    if not incidents:
        primoroso.warning("No incidents found")
        return

    table = GeminiStyleTable(title=f"🚨 Incidents ({len(incidents)})", console=console)
    table.add_column("ID", no_wrap=True)
    table.add_column("Title")
    table.add_column("Severity", alignment="center")
    table.add_column("Status", alignment="center")
    table.add_column("Category")
    table.add_column("Reported")

    for incident in incidents:
        sev_colors = {
            "sev0_critical": "red",
            "sev1_high": "yellow",
            "sev2_medium": "blue",
            "sev3_low": "green",
        }
        sev_color = sev_colors.get(incident.severity.value, "white")

        table.add_row(
            incident.id[:20],
            incident.title[:40],
            f"[{sev_color}]{incident.severity.value}[/{sev_color}]",
            incident.status.value,
            incident.category.value,
            incident.reported_at.strftime("%m-%d %H:%M"),
        )

    table.render()


@app.command()
def show(
    incident_id: str = typer.Argument(..., help="Incident ID"),
    show_updates: bool = typer.Option(False, "--updates", "-u"),
):
    """
    Mostra detalhes de incidente

    Examples:
        vertice incident show INC-20251003-abc123
        vertice incident show INC-123 --updates
    """
    from ..incident import IncidentManager

    manager = IncidentManager()
    incident = manager.get_incident(incident_id)

    if not incident:
        primoroso.error(f"Incident not found: {incident_id}[/red]")
        raise typer.Exit(code=1)

    _show_incident(incident)

    if show_updates and incident.updates:
        primoroso.error("\n[bold]Updates:[/bold]")
        for update in incident.updates[-10:]:
            console.print(
                f"[dim]{update.timestamp.strftime('%Y-%m-%d %H:%M')}[/dim] "
                f"[cyan]{update.author}:[/cyan] {update.content}"
            )


@app.command()
def update(
    incident_id: str = typer.Argument(..., help="Incident ID"),
    status: Optional[str] = typer.Option(None, "--status"),
    assigned_to: Optional[str] = typer.Option(None, "--assign"),
    note: Optional[str] = typer.Option(None, "--note"),
):
    """
    Atualiza incidente

    Examples:
        vertice incident update INC-123 --status investigating
        vertice incident update INC-123 --assign john@company.com
        vertice incident update INC-123 --note "Isolated affected systems"
    """
    from ..incident import IncidentManager, IncidentStatus

    manager = IncidentManager()

    updates = {}

    if status:
        try:
            updates["status"] = IncidentStatus[status.upper()]
        except KeyError:
            primoroso.error(f"Invalid status: {status}[/red]")
            raise typer.Exit(code=1)

    if assigned_to:
        updates["assigned_to"] = assigned_to

    if updates:
        success = manager.update_incident(incident_id, updates)
        if success:
            primoroso.success(f"✅ Incident updated: {incident_id}")
        else:
            primoroso.error(f"Failed to update incident: {incident_id}[/red]")
            raise typer.Exit(code=1)

    if note:
        manager.add_update(incident_id, note, author="cli_user")
        primoroso.success(f"✅ Note added to {incident_id}")


# Playbook commands

playbook_app = typer.Typer(help="📖 Playbook automation")
app.add_typer(playbook_app, name="playbook")


@playbook_app.command()
def run(
    playbook_name: str = typer.Argument(..., help="Playbook name"),
    incident_id: Optional[str] = typer.Option(None, "--incident"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Dry run (no actual execution)"),
):
    """
    Executa playbook

    Examples:
        vertice incident playbook run ransomware_response --incident INC-123 --dry-run
        vertice incident playbook run phishing_response --execute
    """
    from ..incident import PlaybookEngine

    engine = PlaybookEngine(dry_run=dry_run)

    # Load playbook
    playbook_path = Path(__file__).parent.parent.parent / "playbooks" / f"{playbook_name}.yaml"

    if not playbook_path.exists():
        primoroso.error(f"Playbook not found: {playbook_name}[/red]")
        raise typer.Exit(code=1)

    engine.load_playbook(playbook_path)

    primoroso.info(f"Executing playbook: {playbook_name}")
    if dry_run:
        primoroso.warning("DRY RUN MODE - No real actions will be executed[/yellow]\n")

    # Build context
    context = {}
    if incident_id:
        context["incident_id"] = incident_id

    # Execute async
    async def execute():
        return await engine.execute_playbook(playbook_name, context, incident_id)

    execution = asyncio.run(execute())

    # Show results
    primoroso.error(f"\n[green]✅ Playbook execution completed: {execution.id}[/green]\n")

    table = GeminiStyleTable(title="Execution Summary", console=console)
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Success", str(execution.success_count))
    table.add_row("Failed", str(execution.failed_count))
    table.add_row("Skipped", str(execution.skipped_count))
    table.add_row("Status", execution.status.value)

    table.render()


# Case commands

case_app = typer.Typer(help="🔎 Case management")
app.add_typer(case_app, name="case")


@case_app.command()
def create(
    title: str = typer.Option(..., "--title"),
    description: str = typer.Option("", "--description"),
    priority: str = typer.Option("medium", "--priority"),
    incident_id: Optional[str] = typer.Option(None, "--incident"),
):
    """
    Cria novo case de investigação

    Examples:
        vertice incident case create --title "APT28 Investigation" --priority critical
        vertice incident case create -t "Data exfiltration analysis" -i INC-123
    """
    from ..incident import CaseManager, Case, CasePriority, CaseStatus

    try:
        priority_enum = CasePriority[priority.upper()]
    except KeyError:
        primoroso.error(f"Invalid priority: {priority}[/red]")
        raise typer.Exit(code=1)

    manager = CaseManager()

    case = Case(
        id="",
        title=title,
        description=description,
        priority=priority_enum,
        status=CaseStatus.OPEN,
    )

    if incident_id:
        case.related_incidents.append(incident_id)

    case_id = manager.create_case(case)

    primoroso.success(f"✅ Case created: {case_id}")


@case_app.command()
def list(
    status: Optional[str] = typer.Option(None, "--status"),
    limit: int = typer.Option(50, "--limit"),
):
    """Lista cases"""
    from ..incident import CaseManager, CaseStatus

    manager = CaseManager()

    status_filter = None
    if status:
        try:
            status_filter = CaseStatus[status.upper()]
        except KeyError:
            primoroso.error(f"Invalid status: {status}[/red]")
            raise typer.Exit(code=1)

    cases = manager.list_cases(status=status_filter, limit=limit)

    if not cases:
        primoroso.warning("No cases found")
        return

    table = GeminiStyleTable(title=f"🔎 Cases ({len(cases)})", console=console)
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Priority", alignment="center")
    table.add_column("Status")
    table.add_column("Findings", alignment="center")

    for case in cases:
        table.add_row(
            case.id[:20],
            case.title[:40],
            case.priority.value,
            case.status.value,
            str(len(case.findings)),
        )

    table.render()


# Timeline commands

timeline_app = typer.Typer(help="⏱️  Timeline reconstruction")
app.add_typer(timeline_app, name="timeline")


@timeline_app.command()
def create(
    timeline_id: str = typer.Argument(..., help="Timeline ID"),
):
    """Cria nova timeline"""
    from ..incident import TimelineBuilder

    builder = TimelineBuilder()
    builder.create_timeline(timeline_id)

    primoroso.success(f"✅ Timeline created: {timeline_id}")


@timeline_app.command()
def export(
    timeline_id: str = typer.Argument(..., help="Timeline ID"),
    output: str = typer.Option("timeline.json", "--output"),
    format: str = typer.Option("json", "--format", help="json or csv"),
):
    """Exporta timeline"""
    from ..incident import TimelineBuilder

    builder = TimelineBuilder()

    exported = builder.export_timeline(timeline_id, format)

    if exported:
        Path(output).write_text(exported)
        primoroso.success(f"✅ Timeline exported: {output}")
    else:
        primoroso.error("Export failed[/red]")


# Evidence commands

evidence_app = typer.Typer(help="🔐 Evidence collection")
app.add_typer(evidence_app, name="evidence")


@evidence_app.command()
def collect(
    evidence_type: str = typer.Argument(..., help="Evidence type"),
    system: str = typer.Option(..., "--system", help="Source system"),
    source_path: Optional[str] = typer.Option(None, "--path"),
    description: str = typer.Option("", "--description"),
    case_id: Optional[str] = typer.Option(None, "--case"),
):
    """
    Coleta evidência

    Examples:
        vertice incident evidence collect memory_dump --system srv-web-01
        vertice incident evidence collect log_file --system srv-db-01 --path /var/log/auth.log
        vertice incident evidence collect disk_image --system workstation-05 --case CASE-123
    """
    from ..incident import EvidenceCollector, EvidenceType

    try:
        type_enum = EvidenceType[evidence_type.upper()]
    except KeyError:
        primoroso.error(f"Invalid evidence type: {evidence_type}[/red]")
        primoroso.error("\nAvailable types:")
        for et in EvidenceType:
            primoroso.error(f"• {et.value}")
        raise typer.Exit(code=1)

    collector = EvidenceCollector()

    primoroso.info(f"Collecting evidence from {system}...[/cyan]\n")

    evidence = collector.collect_evidence(
        evidence_type=type_enum,
        source_system=system,
        source_path=source_path,
        description=description,
        collected_by="cli_user",
        case_id=case_id,
    )

    primoroso.success(f"✅ Evidence collected: {evidence.id}")
    console.print(f"[dim]Status: {evidence.status.value}[/dim]")
    console.print(f"[dim]Storage: {evidence.storage_path}[/dim]")


@evidence_app.command()
def list(
    case_id: Optional[str] = typer.Option(None, "--case"),
    evidence_type: Optional[str] = typer.Option(None, "--type"),
):
    """Lista evidências coletadas"""
    from ..incident import EvidenceCollector, EvidenceType

    collector = EvidenceCollector()

    type_filter = None
    if evidence_type:
        try:
            type_filter = EvidenceType[evidence_type.upper()]
        except KeyError:
            primoroso.error(f"Invalid evidence type: {evidence_type}[/red]")
            raise typer.Exit(code=1)

    evidence_list = collector.list_evidence(
        case_id=case_id,
        evidence_type=type_filter,
    )

    if not evidence_list:
        primoroso.warning("No evidence found")
        return

    table = GeminiStyleTable(title=f"🔐 Evidence ({len(evidence_list)})", console=console)
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Collected")
    table.add_column("SHA256")

    for evidence in evidence_list:
        table.add_row(
            evidence.id[:20],
            evidence.evidence_type.value,
            evidence.source_system,
            evidence.status.value,
            evidence.collected_at.strftime("%m-%d %H:%M"),
            evidence.sha256_hash[:16] + "..." if evidence.sha256_hash else "—",
        )

    table.render()


@evidence_app.command()
def verify(
    evidence_id: str = typer.Argument(..., help="Evidence ID"),
):
    """Verifica integridade de evidência"""
    from ..incident import EvidenceCollector

    collector = EvidenceCollector()

    evidence = collector.get_evidence(evidence_id)

    if not evidence:
        primoroso.error(f"Evidence not found: {evidence_id}[/red]")
        raise typer.Exit(code=1)

    primoroso.info(f"Verifying integrity of {evidence_id}...")

    is_valid = collector.verify_integrity(evidence)

    if is_valid:
        primoroso.success("✅ Evidence integrity VALID")
    else:
        primoroso.error("Evidence integrity COMPROMISED[/red]")


# Helper functions

def _show_incident(incident):
    """Display incident details"""
    if not incident:
        return

    sev_colors = {
        "sev0_critical": "red",
        "sev1_high": "yellow",
        "sev2_medium": "blue",
        "sev3_low": "green",
    }
    color = sev_colors.get(incident.severity.value, "white")

    content = f"""[bold]{incident.title}[/bold]

[dim]ID:[/dim] {incident.id}
[dim]Severity:[/dim] [{color}]{incident.severity.value}[/{color}]
[dim]Status:[/dim] {incident.status.value}
[dim]Category:[/dim] {incident.category.value}

[dim]Discovered:[/dim] {incident.discovered_at.strftime("%Y-%m-%d %H:%M:%S")}
[dim]Reported:[/dim] {incident.reported_at.strftime("%Y-%m-%d %H:%M:%S")}

{incident.description}

[dim]Affected Systems:[/dim] {len(incident.affected_systems)}
[dim]IOCs:[/dim] {len(incident.iocs)}
[dim]Updates:[/dim] {len(incident.updates)}
"""

    panel = PrimordialPanel(content, title="🚨 Incident Details", console=console)
    # Map severity to status
    status_map = {"sev0_critical": "error", "sev1_high": "warning", "sev2_medium": "info", "sev3_low": "info"}
    panel.with_status(status_map.get(incident.severity.value, "info")).render()
