"""
📜 POLICY Command - Policy-as-Code Automation

Gerencia políticas de resposta automatizada baseadas em eventos.

Exemplos:
    vertice policy list
    vertice policy load policies/ransomware_block.yaml
    vertice policy test ransomware_block --event file_encryption_detected
    vertice policy trigger file_encryption_detected --data '{"process": {"name": "malware.exe"}}'
    vertice policy history --policy ransomware_block
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
from pathlib import Path
from typing import Optional
import json
from vertice.utils import primoroso

app = typer.Typer(
    name="policy",
    help="📜 Policy-as-Code automated response",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def list(
    enabled_only: bool = typer.Option(
        False, "--enabled", help="Show only enabled policies"
    ),
    show_details: bool = typer.Option(
        False, "--details", "-d", help="Show full policy details"
    ),
):
    """
    Lista policies carregadas no engine

    Examples:
        vertice policy list
        vertice policy list --enabled
        vertice policy list --details
    """
    from ..policy import PolicyEngine

    engine = PolicyEngine()

    # TODO: Load policies from default directory
    # For now, show example

    policies = engine.list_policies(enabled_only=enabled_only)

    if not policies:
        console.print("[yellow]No policies loaded. Use 'policy load' to load policies.[/yellow]")
        return

    # Table view
    table = Table(title=f"📜 Policies ({len(policies)} loaded)")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Triggers", style="magenta")
    table.add_column("Actions", style="green")
    table.add_column("Description")

    for policy in policies:
        status = "✅ Enabled" if policy.enabled else "❌ Disabled"

        triggers_str = ", ".join([t.value for t in policy.triggers[:2]])
        if len(policy.triggers) > 2:
            triggers_str += f" +{len(policy.triggers) - 2}"

        actions_str = ", ".join([a.name for a in policy.actions[:2]])
        if len(policy.actions) > 2:
            actions_str += f" +{len(policy.actions) - 2}"

        table.add_row(
            policy.name,
            status,
            triggers_str,
            actions_str,
            policy.description[:50] if policy.description else "—",
        )

    console.print(table)

    # Show details if requested
    if show_details:
        for policy in policies:
            console.print()
            _show_policy_details(policy)


@app.command()
def load(
    policy_path: str = typer.Argument(..., help="Path to YAML policy file"),
    validate_only: bool = typer.Option(
        False, "--validate", help="Validate without loading"
    ),
):
    """
    Carrega policy de arquivo YAML

    Examples:
        vertice policy load policies/ransomware_block.yaml
        vertice policy load policies/lateral_movement.yaml --validate
    """
    from ..policy import PolicyEngine, PolicyParser

    path = Path(policy_path)

    if not path.exists():
        primoroso.error(f"Error: Policy file not found: {policy_path}[/red]")
        raise typer.Exit(code=1)

    try:
        # Parse policy
        policy = PolicyParser.parse_file(path)

        # Validate
        errors = PolicyParser.validate(policy)
        if errors:
            primoroso.error("Policy validation failed:[/red]")
            for error in errors:
                primoroso.error(f"• {error}")
            raise typer.Exit(code=1)

        console.print(f"[green]✅ Policy '{policy.name}' is valid[/green]")

        if validate_only:
            _show_policy_details(policy)
            return

        # Load into engine
        engine = PolicyEngine()
        engine.load_policy(path)

        console.print(f"[green]✅ Policy '{policy.name}' loaded successfully[/green]")
        _show_policy_details(policy)

    except Exception as e:
        primoroso.error(f"Error loading policy: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def trigger(
    event_name: str = typer.Argument(..., help="Event name to trigger"),
    data: str = typer.Option(
        "{}", "--data", help="JSON event data"
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run/--execute", help="Dry run (no real actions)"
    ),
):
    """
    Triggera evento para testar policies

    Examples:
        vertice policy trigger file_encryption_detected --data '{"process": {"name": "malware.exe"}}'
        vertice policy trigger shadow_copy_deletion --dry-run
        vertice policy trigger lateral_movement --data '{"source_ip": "10.0.0.5"}' --execute
    """
    from ..policy import PolicyEngine

    try:
        event_data = json.loads(data)
    except json.JSONDecodeError as e:
        primoroso.error(f"Invalid JSON data: {e}[/red]")
        raise typer.Exit(code=1)

    engine = PolicyEngine(dry_run=dry_run)

    # Load policies from default dir
    # TODO: Make this configurable
    policies_dir = Path.home() / ".vertice" / "policies"
    if policies_dir.exists():
        engine.load_policies_from_dir(policies_dir)

    primoroso.info(f"🎯 Triggering event:[/cyan] {event_name}")
    if dry_run:
        primoroso.warning("⚠️  DRY RUN MODE - No real actions will be executed")

    # Trigger event
    executions = engine.trigger_event(event_name, event_data)

    if not executions:
        primoroso.warning("No policies matched this event")
        return

    primoroso.error(f"\n[green]✅ Triggered {len(executions)} policies[/green]\n")

    # Show execution results
    for execution in executions:
        _show_execution_result(execution)


@app.command()
def test(
    policy_name: str = typer.Argument(..., help="Policy name to test"),
    event: str = typer.Option(..., "--event", help="Event name to simulate"),
    data: str = typer.Option(
        "{}", "--data", help="JSON event data"
    ),
):
    """
    Testa policy com evento simulado (sempre dry-run)

    Examples:
        vertice policy test ransomware_block --event file_encryption_detected
        vertice policy test lateral_movement --event smb_connection --data '{"source_ip": "10.0.0.5"}'
    """
    from ..policy import PolicyEngine

    try:
        event_data = json.loads(data)
    except json.JSONDecodeError as e:
        primoroso.error(f"Invalid JSON data: {e}[/red]")
        raise typer.Exit(code=1)

    engine = PolicyEngine(dry_run=True)  # Always dry-run for tests

    # Load policies
    policies_dir = Path.home() / ".vertice" / "policies"
    if policies_dir.exists():
        engine.load_policies_from_dir(policies_dir)

    policy = engine.get_policy(policy_name)

    if not policy:
        primoroso.error(f"Policy not found: {policy_name}[/red]")
        raise typer.Exit(code=1)

    primoroso.info(f"🧪 Testing policy:[/cyan] {policy.name}")
    primoroso.info(f"Event:[/cyan] {event}")
    primoroso.warning("⚠️  TEST MODE (dry-run)[/yellow]\n")

    # Trigger
    executions = engine.trigger_event(event, event_data)

    matching_exec = next((ex for ex in executions if ex.policy_name == policy_name), None)

    if matching_exec:
        _show_execution_result(matching_exec)
    else:
        console.print(f"[yellow]Policy '{policy_name}' was not triggered by event '{event}'[/yellow]")


@app.command()
def history(
    policy: Optional[str] = typer.Option(
        None, "--policy", "-p", help="Filter by policy name"
    ),
    limit: int = typer.Option(
        20, "--limit", "-n", help="Number of executions to show"
    ),
    show_details: bool = typer.Option(
        False, "--details", "-d", help="Show full execution details"
    ),
):
    """
    Mostra histórico de execuções de policies

    Examples:
        vertice policy history
        vertice policy history --policy ransomware_block
        vertice policy history --limit 50 --details
    """
    from ..policy import PolicyEngine

    engine = PolicyEngine()

    # Load policies to get history
    # TODO: Persist history to database
    policies_dir = Path.home() / ".vertice" / "policies"
    if policies_dir.exists():
        engine.load_policies_from_dir(policies_dir)

    executions = engine.get_execution_history(policy_name=policy, limit=limit)

    if not executions:
        primoroso.warning("No execution history found")
        return

    table = Table(title=f"📋 Policy Execution History ({len(executions)} records)")
    table.add_column("Time", style="dim")
    table.add_column("Policy", style="cyan")
    table.add_column("Event", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Conditions", justify="center")
    table.add_column("Actions", justify="center")

    for execution in executions:
        status_emoji = {
            "triggered": "🎯",
            "conditions_met": "✅",
            "conditions_failed": "❌",
            "actions_executed": "⚡",
            "failed": "💥",
            "skipped": "⏭️",
        }.get(execution.status.value, "❓")

        conditions_str = f"{execution.conditions_passed}/{execution.conditions_evaluated}"
        actions_str = str(len(execution.actions_executed))

        table.add_row(
            execution.triggered_at.strftime("%H:%M:%S"),
            execution.policy_name,
            execution.trigger_event,
            f"{status_emoji} {execution.status.value}",
            conditions_str,
            actions_str,
        )

    console.print(table)

    if show_details:
        primoroso.error("\n[bold]Detailed Execution Logs:[/bold]\n")
        for execution in executions[:5]:  # Show top 5 in detail
            _show_execution_result(execution)


@app.command()
def create(
    output: str = typer.Option(
        "policy.yaml", "--output", "-o", help="Output file path"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--template", help="Interactive mode or template"
    ),
):
    """
    Cria nova policy (interativo ou template)

    Examples:
        vertice policy create --output ransomware_block.yaml
        vertice policy create --template
    """
    if interactive:
        primoroso.info("📝 Interactive Policy Creator[/cyan]\n")

        name = typer.prompt("Policy name")
        description = typer.prompt("Description", default="")

        # Triggers
        primoroso.error("\n[cyan]Triggers (comma-separated event names):[/cyan]")
        triggers_str = typer.prompt("Events")
        triggers = [t.strip() for t in triggers_str.split(",")]

        # Conditions
        primoroso.error("\n[cyan]Conditions (one per line, empty to finish):[/cyan]")
        conditions = []
        while True:
            cond = typer.prompt("Condition", default="")
            if not cond:
                break
            conditions.append(cond)

        # Actions
        primoroso.error("\n[cyan]Actions (comma-separated):[/cyan]")
        primoroso.error("Available: isolate_endpoint, kill_process, block_ip, create_incident, send_alert")
        actions_str = typer.prompt("Actions")
        actions = [a.strip() for a in actions_str.split(",")]

        # Generate YAML
        yaml_content = f"""name: {name}
description: {description}
enabled: true

trigger:
"""
        for trigger in triggers:
            yaml_content += f"  - event: {trigger}\n"

        yaml_content += "\nconnections:\n"
        for condition in conditions:
            yaml_content += f"  - {condition}\n"

        yaml_content += "\nactions:\n"
        for action in actions:
            yaml_content += f"  - {action}\n"

        # Save
        Path(output).write_text(yaml_content)
        primoroso.error(f"\n[green]✅ Policy created: {output}[/green]")

        # Show preview
        primoroso.error("\n[cyan]Preview:[/cyan]")
        syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)

    else:
        # Template mode
        template = """name: My Policy
description: Description of what this policy does
enabled: true

trigger:
  - event: event_name_here
  # - schedule: "0 */6 * * *"  # Cron expression

conditions:
  - process.name IN ['cmd.exe', 'powershell.exe']
  - network.remote_ip NOT IN ["127.0.0.1"]
  # field operator value

actions:
  - isolate_endpoint
  - kill_process:
      process_name: malware.exe
  - block_ip:
      ip_address: 192.168.1.100
  - create_incident:
      severity: critical
      title: Automated Incident
  - send_alert:
      message: Policy triggered!
      channel: slack

tags:
  - ransomware
  - automated

metadata:
  author: Security Team
  version: "1.0"
"""
        Path(output).write_text(template)
        primoroso.success(f"✅ Template created: {output}")


# Helper functions

def _show_policy_details(policy):
    """Mostra detalhes de uma policy"""
    from ..policy import Policy

    tree = Tree(f"[bold cyan]📜 {policy.name}[/bold cyan]")

    if policy.description:
        tree.add(f"[dim]{policy.description}[/dim]")

    tree.add(f"Status: {'✅ Enabled' if policy.enabled else '❌ Disabled'}")

    # Triggers
    triggers_branch = tree.add("[magenta]🎯 Triggers[/magenta]")
    for trigger in policy.triggers:
        triggers_branch.add(f"{trigger.type.value}: {trigger.value}")

    # Conditions
    if policy.conditions:
        conditions_branch = tree.add("[yellow]⚖️  Conditions[/yellow]")
        for condition in policy.conditions:
            conditions_branch.add(condition.expression)

    # Actions
    actions_branch = tree.add("[green]⚡ Actions[/green]")
    for action in policy.actions:
        if action.parameters:
            params_str = ", ".join([f"{k}={v}" for k, v in action.parameters.items()])
            actions_branch.add(f"{action.name}({params_str})")
        else:
            actions_branch.add(action.name)

    # Tags
    if policy.tags:
        tree.add(f"[dim]Tags: {', '.join(policy.tags)}[/dim]")

    console.print(tree)


def _show_execution_result(execution):
    """Mostra resultado de execução"""
    from ..policy import PolicyExecution, PolicyStatus

    status_colors = {
        PolicyStatus.TRIGGERED: "cyan",
        PolicyStatus.CONDITIONS_MET: "green",
        PolicyStatus.CONDITIONS_FAILED: "yellow",
        PolicyStatus.ACTIONS_EXECUTED: "green",
        PolicyStatus.FAILED: "red",
        PolicyStatus.SKIPPED: "dim",
    }

    color = status_colors.get(execution.status, "white")

    panel_title = f"[{color}]⚡ {execution.policy_name}[/{color}]"

    content = f"""[dim]Triggered:[/dim] {execution.triggered_at.strftime("%Y-%m-%d %H:%M:%S")}
[dim]Event:[/dim] {execution.trigger_event}
[dim]Status:[/dim] [{color}]{execution.status.value}[/{color}]
[dim]Conditions:[/dim] {execution.conditions_passed}/{execution.conditions_evaluated} passed
"""

    if execution.actions_executed:
        content += f"\n[bold]Actions Executed:[/bold]\n"
        for action_result in execution.actions_executed:
            status_emoji = "✅" if action_result.status.value == "success" else "❌"
            content += f"  {status_emoji} {action_result.action_name}: {action_result.message}\n"

    if execution.error:
        content += f"\n[red]Error:[/red] {execution.error}"

    console.print(Panel(content, title=panel_title, border_style=color))
