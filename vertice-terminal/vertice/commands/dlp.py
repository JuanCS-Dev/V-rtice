"""
🔒 DLP Command - Data Loss Prevention

Commands:
  vcli dlp inspect <file>               - Inspect file for sensitive data
  vcli dlp classify <file>              - Classify file
  vcli dlp policies list                - List DLP policies
  vcli dlp policies eval                - Evaluate policies
  vcli dlp alerts list                  - List alerts
  vcli dlp alerts ack                   - Acknowledge alert
  vcli dlp alerts resolve               - Resolve alert
  vcli dlp stats                        - Show DLP statistics

Examples:
  vcli dlp inspect /path/to/file.txt
  vcli dlp classify /path/to/document.pdf
  vcli dlp policies list --scope email
  vcli dlp alerts list --severity critical
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from pathlib import Path
from typing import Optional
import logging
from vertice.utils import primoroso

app = typer.Typer(
    name="dlp",
    help="🔒 Data Loss Prevention",
)

console = Console()
logger = logging.getLogger(__name__)

# Lazy imports
_content_inspector = None
_data_classifier = None
_policy_engine = None
_alert_system = None


def get_content_inspector():
    """Lazy load content inspector"""
    global _content_inspector
    if _content_inspector is None:
        from vertice.dlp import ContentInspector
        _content_inspector = ContentInspector()
    return _content_inspector


def get_data_classifier():
    """Lazy load data classifier"""
    global _data_classifier
    if _data_classifier is None:
        from vertice.dlp import DataClassifier
        _data_classifier = DataClassifier()
    return _data_classifier


def get_policy_engine():
    """Lazy load policy engine"""
    global _policy_engine
    if _policy_engine is None:
        from vertice.dlp import PolicyEngine
        _policy_engine = PolicyEngine()
    return _policy_engine


def get_alert_system():
    """Lazy load alert system"""
    global _alert_system
    if _alert_system is None:
        from vertice.dlp import AlertSystem
        _alert_system = AlertSystem()
    return _alert_system


# ==================== Inspect Command ====================

@app.command()
def inspect(
    file_path: str = typer.Argument(..., help="File path to inspect"),
    mask: bool = typer.Option(True, "--mask/--no-mask", help="Mask detected values"),
):
    """
    🔍 Inspect file for sensitive data

    Example:
        vcli dlp inspect /path/to/file.txt
    """
    path = Path(file_path)

    if not path.exists():
        primoroso.error(f"File not found: {file_path}[/red]")
        raise typer.Exit(1)

    inspector = get_content_inspector()

    primoroso.info(f"Inspecting file: {path.name}[/cyan]\n")

    result = inspector.inspect_file(path, mask_values=mask)

    # Display result
    if result.has_sensitive_data:
        # Risk color
        risk_colors = {
            range(0, 30): "green",
            range(30, 60): "yellow",
            range(60, 80): "orange",
            range(80, 101): "red",
        }

        risk_color = "white"
        for r, color in risk_colors.items():
            if result.risk_score in r:
                risk_color = color
                break

        console.print(Panel(
            f"[bold {risk_color}]SENSITIVE DATA DETECTED[/bold {risk_color}]\n\n"
            f"[bold]Risk Score:[/bold] {result.risk_score}/100\n"
            f"[bold]Matches:[/bold] {len(result.matches)}\n"
            f"[bold]Data Types:[/bold] {', '.join(dt.value for dt in result.data_types_found)}\n\n"
            f"{result.summary}",
            title="Inspection Result",
            border_style=risk_color,
        ))

        # Show matches
        if result.matches:
            primoroso.error("\n[bold]Sensitive Data Detected:[/bold]")

            table = Table(box=box.ROUNDED)
            table.add_column("Type", style="cyan")
            table.add_column("Value", style="yellow")
            table.add_column("Confidence", style="magenta")
            table.add_column("Position", style="dim")

            for match in result.matches[:10]:  # Show first 10
                table.add_row(
                    match.data_type.value,
                    match.value,
                    match.confidence.value,
                    f"{match.start_position}-{match.end_position}",
                )

            console.print(table)

            if len(result.matches) > 10:
                console.print(f"\n[dim]... and {len(result.matches) - 10} more matches[/dim]")

    else:
        primoroso.success("No sensitive data detected")


# ==================== Classify Command ====================

@app.command()
def classify(
    file_path: str = typer.Argument(..., help="File path to classify"),
):
    """
    🏷️ Classify file

    Example:
        vcli dlp classify /path/to/document.pdf
    """
    path = Path(file_path)

    if not path.exists():
        primoroso.error(f"File not found: {file_path}[/red]")
        raise typer.Exit(1)

    classifier = get_data_classifier()

    primoroso.info(f"Classifying file: {path.name}[/cyan]\n")

    classification = classifier.classify_file(path)

    # Display result
    level_colors = {
        "public": "green",
        "internal": "blue",
        "confidential": "yellow",
        "restricted": "orange",
        "top_secret": "red",
    }

    level_color = level_colors.get(classification.level.value, "white")

    console.print(Panel(
        f"[bold {level_color}]Classification: {classification.level.value.upper()}[/bold {level_color}]\n\n"
        f"[bold]Method:[/bold] {classification.method.value}\n"
        f"[bold]Confidence:[/bold] {classification.confidence}%\n"
        f"[bold]Classified By:[/bold] {classification.classified_by}\n"
        f"[bold]Classified At:[/bold] {classification.classified_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"[bold]Reason:[/bold] {classification.reason}\n"
        f"[bold]Rules Matched:[/bold] {len(classification.rules_matched)}",
        title="Classification Result",
        border_style=level_color,
    ))


# ==================== Policies Commands ====================

policies_app = typer.Typer(help="📜 DLP policies management")
app.add_typer(policies_app, name="policies")


@policies_app.command("list")
def policies_list(
    scope: Optional[str] = typer.Option(None, "--scope", help="Filter by scope"),
    action: Optional[str] = typer.Option(None, "--action", help="Filter by action"),
    enabled_only: bool = typer.Option(False, "--enabled", help="Only enabled policies"),
):
    """
    📋 List DLP policies

    Example:
        vcli dlp policies list --scope email --enabled
    """
    from vertice.dlp import PolicyScope, PolicyAction

    engine = get_policy_engine()

    # Parse filters
    scope_enum = None
    if scope:
        try:
            scope_enum = PolicyScope(scope)
        except ValueError:
            primoroso.error(f"Invalid scope: {scope}[/red]")
            raise typer.Exit(1)

    action_enum = None
    if action:
        try:
            action_enum = PolicyAction(action)
        except ValueError:
            primoroso.error(f"Invalid action: {action}[/red]")
            raise typer.Exit(1)

    policies = engine.list_policies(
        scope=scope_enum,
        action=action_enum,
        enabled_only=enabled_only,
    )

    # Display
    table = Table(title=f"DLP Policies ({len(policies)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Scope", style="blue")
    table.add_column("Action", style="magenta")
    table.add_column("Priority", justify="right", style="yellow")
    table.add_column("Status", style="green")

    for policy in policies:
        status = "✅ Enabled" if policy.enabled else "❌ Disabled"

        table.add_row(
            policy.id,
            policy.name[:40] + "..." if len(policy.name) > 40 else policy.name,
            policy.scope.value,
            policy.action.value,
            str(policy.priority),
            status,
        )

    console.print(table)


@policies_app.command("eval")
def policies_eval(
    scope: str = typer.Option(..., "--scope", help="Policy scope (email, file_upload, etc)"),
    classification: str = typer.Option("public", "--classification", help="Classification level"),
    data_types: str = typer.Option("", "--data-types", help="Comma-separated data types"),
):
    """
    🔍 Evaluate policies

    Example:
        vcli dlp policies eval --scope email --classification restricted --data-types credit_card
    """
    from vertice.dlp import PolicyScope

    try:
        scope_enum = PolicyScope(scope)
    except ValueError:
        primoroso.error(f"Invalid scope: {scope}[/red]")
        raise typer.Exit(1)

    engine = get_policy_engine()

    # Build context
    context = {
        "classification_level": classification,
    }

    if data_types:
        context["sensitive_data_type"] = data_types.split(",")

    primoroso.info(f"Evaluating policies for scope: {scope}[/cyan]\n")

    results = engine.evaluate_policies(scope_enum, context)

    if not results:
        primoroso.success("✅ No policies matched - Action allowed")
        return

    # Display results
    for result in results:
        policy = engine.get_policy(result.policy_id)

        if not policy:
            continue

        action_colors = {
            "allow": "green",
            "block": "red",
            "alert": "yellow",
            "quarantine": "orange",
        }

        action_color = action_colors.get(result.action.value, "white")

        console.print(Panel(
            f"[bold]Policy:[/bold] {policy.name}\n"
            f"[bold {action_color}]Action:[/bold {action_color}] {result.action.value.upper()}\n"
            f"[bold]Reason:[/bold] {result.reason}\n"
            f"[bold]Conditions Matched:[/bold] {len(result.conditions_matched)}\n"
            f"[bold]Requires Approval:[/bold] {'Yes' if result.requires_approval else 'No'}",
            title=f"Policy Match: {result.policy_id}",
            border_style=action_color,
        ))


# ==================== Alerts Commands ====================

alerts_app = typer.Typer(help="🚨 DLP alerts management")
app.add_typer(alerts_app, name="alerts")


@alerts_app.command("list")
def alerts_list(
    severity: Optional[str] = typer.Option(None, "--severity", help="Filter by severity"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    user: Optional[str] = typer.Option(None, "--user", help="Filter by user"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
):
    """
    📋 List DLP alerts

    Example:
        vcli dlp alerts list --severity critical --status new
    """
    from vertice.dlp import AlertSeverity, AlertStatus

    alert_system = get_alert_system()

    # Parse filters
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            primoroso.error(f"Invalid severity: {severity}[/red]")
            raise typer.Exit(1)

    status_enum = None
    if status:
        try:
            status_enum = AlertStatus(status)
        except ValueError:
            primoroso.error(f"Invalid status: {status}[/red]")
            raise typer.Exit(1)

    alerts = alert_system.list_alerts(
        severity=severity_enum,
        status=status_enum,
        user=user,
        limit=limit,
    )

    # Display
    table = Table(title=f"DLP Alerts ({len(alerts)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Severity", style="magenta")
    table.add_column("Status", style="yellow")
    table.add_column("User", style="blue")
    table.add_column("Created", style="dim")

    for alert in alerts:
        # Severity symbol
        severity_symbols = {
            "info": "ℹ️",
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴",
        }

        sev_symbol = severity_symbols.get(alert.severity.value, "")

        table.add_row(
            alert.id,
            alert.title[:40] + "..." if len(alert.title) > 40 else alert.title,
            f"{sev_symbol} {alert.severity.value}",
            alert.status.value,
            alert.user or "N/A",
            alert.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@alerts_app.command("ack")
def alerts_ack(
    alert_id: str = typer.Argument(..., help="Alert ID"),
    user: str = typer.Option("current-user", "--user", help="Acknowledging user"),
    notes: str = typer.Option("", "--notes", help="Acknowledgment notes"),
):
    """
    ✅ Acknowledge alert

    Example:
        vcli dlp alerts ack ALERT-20250103-abc123 --user john.doe
    """
    alert_system = get_alert_system()

    success = alert_system.acknowledge_alert(alert_id, user, notes)

    if success:
        primoroso.success(f"✅ Alert acknowledged: {alert_id}")
    else:
        primoroso.error(f"Alert not found: {alert_id}[/red]")
        raise typer.Exit(1)


@alerts_app.command("resolve")
def alerts_resolve(
    alert_id: str = typer.Argument(..., help="Alert ID"),
    user: str = typer.Option("current-user", "--user", help="Resolving user"),
    notes: str = typer.Option("", "--notes", help="Resolution notes"),
    false_positive: bool = typer.Option(False, "--fp", help="Mark as false positive"),
):
    """
    ✔️  Resolve alert

    Example:
        vcli dlp alerts resolve ALERT-20250103-abc123 --user john.doe --notes "Issue fixed"
    """
    alert_system = get_alert_system()

    success = alert_system.resolve_alert(alert_id, user, notes, false_positive)

    if success:
        status = "false positive" if false_positive else "resolved"
        primoroso.success(f"✅ Alert {status}: {alert_id}")
    else:
        primoroso.error(f"Alert not found: {alert_id}[/red]")
        raise typer.Exit(1)


# ==================== Stats Command ====================

@app.command()
def stats():
    """
    📊 Show DLP statistics

    Example:
        vcli dlp stats
    """
    inspector = get_content_inspector()
    classifier = get_data_classifier()
    engine = get_policy_engine()
    alert_system = get_alert_system()

    # Get statistics
    inspector_stats = inspector.get_statistics()
    classifier_stats = classifier.get_statistics()
    engine_stats = engine.get_statistics()
    alert_stats = alert_system.get_statistics()

    console.print(Panel(
        "[bold cyan]Data Loss Prevention Statistics[/bold cyan]",
        border_style="cyan",
    ))

    # Content Inspector
    primoroso.error("\n[bold]Content Inspector:[/bold]")
    console.print(f"  Pattern Categories: {inspector_stats['total_pattern_categories']}")
    console.print(f"  Total Patterns: {inspector_stats['total_patterns']}")
    console.print(f"  Custom Patterns: {inspector_stats['custom_patterns']}")

    # Data Classifier
    primoroso.error("\n[bold]Data Classifier:[/bold]")
    console.print(f"  Total Classifications: {classifier_stats['total_classifications']}")
    console.print(f"  Classification Rules: {classifier_stats['total_rules']}")
    console.print(f"  High Sensitivity Resources: {classifier_stats['high_sensitivity_resources']}")

    # Policy Engine
    primoroso.error("\n[bold]Policy Engine:[/bold]")
    console.print(f"  Total Policies: {engine_stats['total_policies']}")
    console.print(f"  Enabled Policies: {engine_stats['enabled_policies']}")
    console.print(f"  Policy Executions: {engine_stats['total_executions']}")

    # Alert System
    primoroso.error("\n[bold]Alert System:[/bold]")
    console.print(f"  Total Alerts: {alert_stats['total_alerts']}")
    console.print(f"  Avg Resolution Time: {alert_stats['avg_resolution_time_minutes']} min")
    console.print(f"  Total Recipients: {alert_stats['total_recipients']}")


# ==================== Main Command ====================

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    🔒 Data Loss Prevention (DLP) System

    Prevent sensitive data leakage with deep content inspection,
    automated classification, policy enforcement, and real-time alerts.

    Features:
    - Content inspection (PII, PCI, PHI, credentials)
    - Automatic data classification
    - Policy-based enforcement
    - Real-time alerts and escalation
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
