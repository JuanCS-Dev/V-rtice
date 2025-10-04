"""
📋 Compliance Command - Multi-framework compliance management

Commands:
  vcli compliance assess <framework>       - Run compliance assessment
  vcli compliance controls list           - List all controls
  vcli compliance controls update         - Update control status
  vcli compliance gaps <framework>        - Show gap analysis
  vcli compliance audit query             - Query audit trail
  vcli compliance audit verify            - Verify audit chain integrity
  vcli compliance report generate         - Generate compliance report
  vcli compliance metrics show            - Show KPIs and metrics
  vcli compliance metrics export          - Export metrics to CSV

Supported Frameworks:
  - PCI-DSS (Payment Card Industry)
  - HIPAA (Healthcare)
  - ISO27001 (Information Security)
  - NIST CSF (Cybersecurity Framework)
  - LGPD (Brazilian Data Protection)
  - GDPR (EU Data Protection)
  - SOC2 (Service Organization Control)

Examples:
  vcli compliance assess pci_dss
  vcli compliance gaps lgpd
  vcli compliance audit query --event-type login_failed --limit 50
  vcli compliance report generate --type assessment --framework iso27001
  vcli compliance metrics show --kpi-group security
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from datetime import datetime, timedelta
from typing import Optional
import logging
from vertice.utils import primoroso

app = typer.Typer(
    name="compliance",
    help="📋 Multi-framework compliance management",
)

console = Console()
logger = logging.getLogger(__name__)

# Lazy imports
_compliance_engine = None
_audit_logger = None
_report_generator = None
_metrics_collector = None


def get_compliance_engine():
    """Lazy load compliance engine"""
    global _compliance_engine
    if _compliance_engine is None:
        from vertice.compliance import ComplianceEngine
        _compliance_engine = ComplianceEngine()
    return _compliance_engine


def get_audit_logger():
    """Lazy load audit logger"""
    global _audit_logger
    if _audit_logger is None:
        from vertice.compliance import AuditLogger
        _audit_logger = AuditLogger()
    return _audit_logger


def get_report_generator():
    """Lazy load report generator"""
    global _report_generator
    if _report_generator is None:
        from vertice.compliance import ReportGenerator
        _report_generator = ReportGenerator()
    return _report_generator


def get_metrics_collector():
    """Lazy load metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        from vertice.compliance import MetricsCollector
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# ==================== Assessment Commands ====================

@app.command()
def assess(
    framework: str = typer.Argument(..., help="Compliance framework (pci_dss, hipaa, iso27001, nist_csf, lgpd, gdpr, soc2)"),
    assessor: str = typer.Option("system", "--assessor", help="Assessor name"),
):
    """
    🔍 Run compliance assessment

    Executes comprehensive assessment of compliance framework,
    evaluating all controls and generating compliance score.

    Example:
        vcli compliance assess pci_dss --assessor "John Doe"
    """
    from vertice.compliance import ComplianceFramework

    try:
        # Parse framework
        framework_enum = ComplianceFramework(framework)

        primoroso.error(f"[bold cyan]Running compliance assessment: {framework_enum.value.upper()}[/bold cyan]\n")

        engine = get_compliance_engine()

        # Run assessment
        assessment = engine.assess_framework(
            framework=framework_enum,
            assessor=assessor,
        )

        # Display results
        console.print(Panel(
            f"[bold green]Compliance Score: {assessment.compliance_score:.1f}%[/bold green]",
            title="Assessment Result",
            border_style="green",
        ))

        # Summary table
        table = Table(title="Control Summary", box=box.ROUNDED)
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right", style="magenta")

        table.add_row("✅ Implemented", str(assessment.implemented))
        table.add_row("⚠️  Partially Implemented", str(assessment.partially_implemented))
        table.add_row("❌ Not Implemented", str(assessment.not_implemented))
        table.add_row("➖ Not Applicable", str(assessment.not_applicable))
        table.add_row("[bold]Total[/bold]", f"[bold]{assessment.total_controls}[/bold]")

        console.print(table)

        # Show gaps
        if assessment.gaps:
            primoroso.error(f"\n[yellow]⚠️  {len(assessment.gaps)} gaps identified[/yellow]")

            for gap in assessment.gaps[:5]:  # Show first 5
                primoroso.error(f"• {gap}")

            if len(assessment.gaps) > 5:
                primoroso.error(f"... and {len(assessment.gaps) - 5} more")

        # Show recommendations
        if assessment.recommendations:
            primoroso.error("\n[blue]💡 Top Recommendations:[/blue]")

            for rec in assessment.recommendations[:5]:
                primoroso.error(f"• {rec}")

        primoroso.error(f"\n[dim]Assessment ID: {assessment.id}[/dim]")

    except ValueError:
        primoroso.error(f"Invalid framework: {framework}[/red]")
        primoroso.warning("Valid frameworks: pci_dss, hipaa, iso27001, nist_csf, lgpd, gdpr, soc2")
        raise typer.Exit(1)

    except Exception as e:
        primoroso.error(f"Assessment failed: {e}[/red]")
        logger.exception("Assessment error")
        raise typer.Exit(1)


# ==================== Controls Commands ====================

controls_app = typer.Typer(help="🔒 Manage compliance controls")
app.add_typer(controls_app, name="controls")


@controls_app.command("list")
def controls_list(
    framework: Optional[str] = typer.Option(None, "--framework", help="Filter by framework"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
):
    """
    📋 List compliance controls

    Example:
        vcli compliance controls list --framework pci_dss --status not_implemented
    """
    from vertice.compliance import ComplianceFramework, ControlStatus

    engine = get_compliance_engine()

    # Parse filters
    framework_enum = None
    if framework:
        try:
            framework_enum = ComplianceFramework(framework)
        except ValueError:
            primoroso.error(f"Invalid framework: {framework}[/red]")
            raise typer.Exit(1)

    status_enum = None
    if status:
        try:
            status_enum = ControlStatus(status)
        except ValueError:
            primoroso.error(f"Invalid status: {status}[/red]")
            raise typer.Exit(1)

    # Get controls
    if framework_enum:
        controls = engine.get_controls_by_framework(framework_enum, status=status_enum)
    else:
        controls = list(engine.controls.values())

        if status_enum:
            controls = [c for c in controls if c.status == status_enum]

    controls = controls[:limit]

    # Display
    table = Table(title=f"Compliance Controls ({len(controls)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Framework", style="blue")
    table.add_column("Title", style="white")
    table.add_column("Status", style="magenta")
    table.add_column("Priority", style="yellow")

    for control in controls:
        # Status symbol
        status_map = {
            "implemented": "✅",
            "partially_implemented": "⚠️",
            "not_implemented": "❌",
            "not_applicable": "➖",
            "needs_review": "🔍",
        }

        status_symbol = status_map.get(control.status.value, "?")

        table.add_row(
            control.id,
            control.framework.value.upper(),
            control.title[:50] + "..." if len(control.title) > 50 else control.title,
            f"{status_symbol} {control.status.value}",
            control.priority,
        )

    console.print(table)


@controls_app.command("update")
def controls_update(
    control_id: str = typer.Argument(..., help="Control ID"),
    status: str = typer.Option(..., "--status", help="New status (implemented, partially_implemented, not_implemented, not_applicable)"),
    notes: str = typer.Option("", "--notes", help="Implementation notes"),
):
    """
    ✏️  Update control status

    Example:
        vcli compliance controls update PCI-DSS-1.1 --status implemented --notes "Firewall rules configured"
    """
    from vertice.compliance import ControlStatus

    try:
        status_enum = ControlStatus(status)
    except ValueError:
        primoroso.error(f"Invalid status: {status}[/red]")
        primoroso.warning("Valid statuses: implemented, partially_implemented, not_implemented, not_applicable, needs_review")
        raise typer.Exit(1)

    engine = get_compliance_engine()

    success = engine.update_control_status(
        control_id=control_id,
        status=status_enum,
        implementation_notes=notes,
    )

    if success:
        primoroso.success(f"✅ Control {control_id} updated to: {status_enum.value}")
    else:
        primoroso.error(f"Control not found: {control_id}[/red]")
        raise typer.Exit(1)


# ==================== Gap Analysis Commands ====================

@app.command()
def gaps(
    framework: str = typer.Argument(..., help="Compliance framework"),
):
    """
    🔍 Show gap analysis

    Identifies compliance gaps and critical issues requiring attention.

    Example:
        vcli compliance gaps lgpd
    """
    from vertice.compliance import ComplianceFramework

    try:
        framework_enum = ComplianceFramework(framework)
    except ValueError:
        primoroso.error(f"Invalid framework: {framework}[/red]")
        raise typer.Exit(1)

    engine = get_compliance_engine()

    gap_analysis = engine.get_gap_analysis(framework_enum)

    # Display
    console.print(Panel(
        f"[bold yellow]{gap_analysis['total_gaps']} total gaps\n"
        f"{gap_analysis['critical_gaps']} critical gaps[/bold yellow]",
        title=f"Gap Analysis: {framework_enum.value.upper()}",
        border_style="yellow",
    ))

    # Critical gaps
    if gap_analysis['critical_gaps_list']:
        primoroso.error("\n[bold red]🔴 Critical Gaps:[/bold red]")

        for gap in gap_analysis['critical_gaps_list']:
            console.print(
                f"  [red]•[/red] [bold]{gap['control_id']}[/bold]: {gap['title']}\n"
                f"    Status: {gap['status']} | Priority: {gap['priority']}"
            )

    # All gaps
    if gap_analysis['gaps']:
        console.print(f"\n[bold yellow]⚠️  All Gaps ({len(gap_analysis['gaps'])}):[/bold yellow]")

        for gap in gap_analysis['gaps'][:10]:
            console.print(
                f"  • {gap['control_id']}: {gap['title']} ({gap['status']})"
            )

        if len(gap_analysis['gaps']) > 10:
            console.print(f"  ... and {len(gap_analysis['gaps']) - 10} more")


# ==================== Audit Commands ====================

audit_app = typer.Typer(help="🔍 Audit trail management")
app.add_typer(audit_app, name="audit")


@audit_app.command("query")
def audit_query(
    event_type: Optional[str] = typer.Option(None, "--event-type", help="Filter by event type"),
    actor: Optional[str] = typer.Option(None, "--actor", help="Filter by actor"),
    resource: Optional[str] = typer.Option(None, "--resource", help="Filter by resource"),
    result: Optional[str] = typer.Option(None, "--result", help="Filter by result (success/failure)"),
    hours: int = typer.Option(24, "--hours", help="Time window in hours"),
    limit: int = typer.Option(100, "--limit", help="Max results"),
):
    """
    🔍 Query audit trail

    Search and filter audit events.

    Example:
        vcli compliance audit query --event-type login_failed --hours 24
    """
    from vertice.compliance import AuditEventType, AuditSeverity

    audit_logger = get_audit_logger()

    # Parse event type
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            primoroso.error(f"Invalid event type: {event_type}[/red]")
            raise typer.Exit(1)

    # Query
    start_time = datetime.now() - timedelta(hours=hours)

    events = audit_logger.query(
        event_type=event_type_enum,
        actor=actor,
        resource=resource,
        result=result,
        start_time=start_time,
        limit=limit,
    )

    # Display
    table = Table(title=f"Audit Trail ({len(events)} events)", box=box.ROUNDED)
    table.add_column("Timestamp", style="cyan")
    table.add_column("Event Type", style="blue")
    table.add_column("Actor", style="yellow")
    table.add_column("Resource", style="white")
    table.add_column("Result", style="magenta")

    for event in events:
        # Result color
        result_color = "green" if event.result == "success" else "red"

        table.add_row(
            event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            event.event_type.value,
            event.actor,
            event.resource[:30] + "..." if len(event.resource) > 30 else event.resource,
            f"[{result_color}]{event.result}[/{result_color}]",
        )

    console.print(table)

    # Statistics
    stats = audit_logger.get_statistics(start_time=start_time)

    console.print(f"\n[dim]Total events in {hours}h: {stats['total_events']}[/dim]")


@audit_app.command("verify")
def audit_verify():
    """
    ✅ Verify audit chain integrity

    Verifies cryptographic integrity of audit trail using hash chaining.

    Example:
        vcli compliance audit verify
    """
    audit_logger = get_audit_logger()

    primoroso.info("Verifying audit chain integrity...[/cyan]\n")

    is_valid = audit_logger.verify_chain_integrity()

    if is_valid:
        console.print(Panel(
            f"[bold green]✅ Audit chain integrity VERIFIED[/bold green]\n"
            f"Total events: {len(audit_logger.event_chain)}",
            title="Integrity Check",
            border_style="green",
        ))
    else:
        console.print(Panel(
            "[bold red]❌ Audit chain integrity COMPROMISED[/bold red]\n"
            "Tampering detected!",
            title="Integrity Check",
            border_style="red",
        ))
        raise typer.Exit(1)


# ==================== Report Commands ====================

report_app = typer.Typer(help="📊 Report generation")
app.add_typer(report_app, name="report")


@report_app.command("generate")
def report_generate(
    report_type: str = typer.Option(..., "--type", help="Report type (assessment, gap, audit, metrics, executive)"),
    framework: Optional[str] = typer.Option(None, "--framework", help="Framework (for assessment/gap reports)"),
    format: str = typer.Option("html", "--format", help="Output format (html, json, markdown, csv)"),
    hours: int = typer.Option(24, "--hours", help="Time window in hours (for audit reports)"),
):
    """
    📊 Generate compliance report

    Creates formatted reports in multiple formats.

    Example:
        vcli compliance report generate --type assessment --framework pci_dss --format html
    """
    from vertice.compliance import ComplianceFramework, ReportFormat

    try:
        format_enum = ReportFormat(format)
    except ValueError:
        primoroso.error(f"Invalid format: {format}[/red]")
        raise typer.Exit(1)

    report_gen = get_report_generator()

    primoroso.info(f"Generating {report_type} report...[/cyan]\n")

    # Generate based on type
    if report_type == "assessment":
        if not framework:
            primoroso.error("--framework required for assessment reports[/red]")
            raise typer.Exit(1)

        try:
            framework_enum = ComplianceFramework(framework)
        except ValueError:
            primoroso.error(f"Invalid framework: {framework}[/red]")
            raise typer.Exit(1)

        # Run assessment
        engine = get_compliance_engine()
        assessment = engine.assess_framework(framework_enum)

        # Generate report
        report = report_gen.generate_compliance_assessment_report(
            assessment=assessment,
            format=format_enum,
        )

    elif report_type == "gap":
        if not framework:
            primoroso.error("--framework required for gap reports[/red]")
            raise typer.Exit(1)

        try:
            framework_enum = ComplianceFramework(framework)
        except ValueError:
            primoroso.error(f"Invalid framework: {framework}[/red]")
            raise typer.Exit(1)

        # Get gap analysis
        engine = get_compliance_engine()
        gap_analysis = engine.get_gap_analysis(framework_enum)

        # Generate report
        report = report_gen.generate_gap_analysis_report(
            gap_analysis=gap_analysis,
            framework=framework_enum.value,
            format=format_enum,
        )

    elif report_type == "audit":
        # Get audit events
        audit_logger = get_audit_logger()

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        events = audit_logger.query(
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )

        # Generate report
        report = report_gen.generate_audit_trail_report(
            events=events,
            period_start=start_time,
            period_end=end_time,
            format=format_enum,
        )

    else:
        primoroso.error(f"Invalid report type: {report_type}[/red]")
        primoroso.warning("Valid types: assessment, gap, audit, metrics, executive")
        raise typer.Exit(1)

    # Display result
    console.print(Panel(
        f"[bold green]✅ Report generated successfully[/bold green]\n\n"
        f"Report ID: {report.id}\n"
        f"Type: {report.report_type.value}\n"
        f"Format: {report.format.value}\n"
        f"Output: {report.output_path}",
        title="Report Generated",
        border_style="green",
    ))


# ==================== Metrics Commands ====================

metrics_app = typer.Typer(help="📊 Metrics and KPIs")
app.add_typer(metrics_app, name="metrics")


@metrics_app.command("show")
def metrics_show(
    kpi_group: str = typer.Option("all", "--group", help="KPI group (security, compliance, operational, all)"),
):
    """
    📊 Show KPIs and metrics

    Displays key performance indicators and security metrics.

    Example:
        vcli compliance metrics show --group security
    """
    metrics = get_metrics_collector()

    primoroso.info("Calculating KPIs...[/cyan]\n")

    # Get KPIs based on group
    if kpi_group == "security":
        kpis = metrics.get_security_kpis()
    elif kpi_group == "compliance":
        kpis = metrics.get_compliance_kpis()
    elif kpi_group == "operational":
        kpis = metrics.get_operational_kpis()
    elif kpi_group == "all":
        kpis = metrics.get_all_kpis()
    else:
        primoroso.error(f"Invalid group: {kpi_group}[/red]")
        primoroso.warning("Valid groups: security, compliance, operational, all")
        raise typer.Exit(1)

    # Display KPIs
    table = Table(title=f"KPI Dashboard ({kpi_group.upper()})", box=box.ROUNDED)
    table.add_column("KPI", style="cyan")
    table.add_column("Current", justify="right", style="magenta")
    table.add_column("Target", justify="right", style="blue")
    table.add_column("Trend", justify="center", style="yellow")
    table.add_column("Status", justify="center")

    for kpi in kpis.values():
        # Status symbol
        status_map = {
            "ok": "✅",
            "warning": "⚠️",
            "critical": "🔴",
        }

        status_symbol = status_map.get(kpi.status, "?")

        # Trend symbol
        trend_map = {
            "up": "📈",
            "down": "📉",
            "stable": "➡️",
        }

        trend_symbol = trend_map.get(kpi.trend, "?")

        table.add_row(
            kpi.name,
            f"{kpi.current_value:.2f} {kpi.unit}",
            f"{kpi.target_value:.2f} {kpi.unit}",
            f"{trend_symbol} {kpi.trend}",
            f"{status_symbol} {kpi.status}",
        )

    console.print(table)


@metrics_app.command("export")
def metrics_export(
    output: str = typer.Option("metrics.csv", "--output", help="Output CSV file"),
    hours: int = typer.Option(24, "--hours", help="Time window in hours"),
):
    """
    💾 Export metrics to CSV

    Example:
        vcli compliance metrics export --output metrics.csv --hours 24
    """
    metrics = get_metrics_collector()

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    success = metrics.export_metrics_csv(
        output_path=output,
        start_time=start_time,
        end_time=end_time,
    )

    if success:
        primoroso.success(f"✅ Metrics exported to: {output}")
    else:
        primoroso.error("Export failed[/red]")
        raise typer.Exit(1)


# ==================== Main Command ====================

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    📋 Multi-framework compliance management

    Manage compliance across PCI-DSS, HIPAA, ISO27001, LGPD, GDPR, SOC2, and NIST CSF.

    Features:
    - Compliance assessments and scoring
    - Control management
    - Gap analysis
    - Tamper-proof audit logging
    - Report generation (HTML, PDF, JSON, CSV)
    - Metrics and KPI tracking
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
