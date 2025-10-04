"""
🔍 DETECT Command - Threat Detection & Response

Gerencia detecção de ameaças com YARA/Sigma rules e alertas.

Exemplos:
    vertice detect scan /path/to/file
    vertice detect scan-dir /malware/samples --parallel
    vertice detect log-analyze '{"EventID": 4104, "ScriptBlockText": "IEX ..."}'
    vertice detect alerts list --status new
    vertice detect rules list --type yara
    vertice detect stream --live
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from pathlib import Path
from typing import Optional
import json
import asyncio
from vertice.utils import primoroso

app = typer.Typer(
    name="detect",
    help="🔍 Threat detection with YARA/Sigma rules",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def scan(
    file_path: str = typer.Argument(..., help="File to scan"),
    rules_dir: Optional[str] = typer.Option(
        None, "--rules", help="YARA rules directory"
    ),
    backend: bool = typer.Option(
        True, "--backend/--local", help="Use backend for scanning"
    ),
):
    """
    Escaneia arquivo com regras YARA

    Examples:
        vertice detect scan suspicious.exe
        vertice detect scan malware.dll --rules ./rules/yara
        vertice detect scan file.bin --local
    """
    from ..detection import YARAScanner, DetectionEngine
    from ..policy import PolicyEngine

    path = Path(file_path)

    if not path.exists():
        primoroso.error(f"Error: File not found: {file_path}[/red]")
        raise typer.Exit(code=1)

    # Setup detection engine
    policy_engine = PolicyEngine(dry_run=False)
    detection_engine = DetectionEngine(
        auto_response=True,
        policy_engine=policy_engine,
    )

    # Load YARA rules
    if rules_dir:
        rules_path = Path(rules_dir)
    else:
        rules_path = Path(__file__).parent.parent.parent / "rules" / "yara"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading YARA rules...", total=None)

        count = detection_engine.load_yara_rules(rules_path)
        progress.update(task, completed=True, description=f"Loaded {count} YARA rules")

        # Scan file
        task = progress.add_task(f"Scanning {path.name}...", total=None)

        detections = detection_engine.scan_file(path)
        progress.update(task, completed=True)

    # Display results
    if not detections:
        primoroso.success(f"✅ No threats detected in {path.name}")
        return

    primoroso.error(f"\n[red]⚠️  {len(detections)} threat(s) detected![/red]\n")

    for detection in detections:
        _show_detection(detection)


@app.command()
def scan_dir(
    directory: str = typer.Argument(..., help="Directory to scan"),
    pattern: str = typer.Option("*", "--pattern", help="File pattern (glob)"),
    parallel: bool = typer.Option(True, "--parallel", help="Parallel scanning"),
    rules_dir: Optional[str] = typer.Option(None, "--rules"),
):
    """
    Escaneia diretório com YARA rules

    Examples:
        vertice detect scan-dir /suspicious/files
        vertice detect scan-dir /malware --pattern "*.exe"
        vertice detect scan-dir /samples --parallel
    """
    from ..detection import YARAScanner, DetectionEngine

    dir_path = Path(directory)

    if not dir_path.exists():
        primoroso.error(f"Error: Directory not found: {directory}[/red]")
        raise typer.Exit(code=1)

    # Find files
    files = list(dir_path.glob(f"**/{pattern}"))

    if not files:
        primoroso.warning(f"No files found matching pattern: {pattern}")
        return

    primoroso.info(f"Found {len(files)} files to scan[/cyan]\n")

    # Setup scanner
    scanner = YARAScanner(use_backend=parallel)

    # Load rules
    if rules_dir:
        rules_path = Path(rules_dir)
    else:
        rules_path = Path(__file__).parent.parent.parent / "rules" / "yara"

    scanner.load_rules(rules_path)

    # Scan
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        if parallel:
            # Bulk scan
            task = progress.add_task("Scanning files...", total=len(files))

            results = scanner.bulk_scan(files, parallel=True)

            progress.update(task, completed=len(files))

            # Show results
            total_detections = sum(len(matches) for matches in results.values())

            primoroso.error(f"\n[cyan]Scan complete: {total_detections} detections[/cyan]\n")

            for file_path, matches in results.items():
                if matches:
                    primoroso.error(f"🚨 {file_path}[/red]")
                    for match in matches:
                        console.print(f"  • {match.rule_name} ({', '.join(match.tags)})")

        else:
            # Sequential scan
            task = progress.add_task("Scanning files...", total=len(files))

            total_detections = 0

            for file_path in files:
                matches = scanner.scan_file(file_path)

                if matches:
                    total_detections += len(matches)
                    primoroso.error(f"🚨 {file_path}[/red]")
                    for match in matches:
                        primoroso.error(f"• {match.rule_name}")

                progress.advance(task)

            primoroso.error(f"\n[cyan]Total detections: {total_detections}[/cyan]")


@app.command()
def log_analyze(
    log_entry: str = typer.Argument(..., help="Log entry JSON"),
    rules_dir: Optional[str] = typer.Option(None, "--rules"),
    backend: bool = typer.Option(True, "--backend/--local", help="Use backend (otherwise local)"),
):
    """
    Analisa log entry com regras Sigma

    Examples:
        vertice detect log-analyze '{"EventID": 4104, "ScriptBlockText": "IEX ..."}'
        vertice detect log-analyze @event.json --rules ./rules/sigma
    """
    from ..detection import SigmaParser, DetectionEngine

    # Parse JSON
    try:
        if log_entry.startswith("@"):
            # File path
            log_data = json.loads(Path(log_entry[1:]).read_text())
        else:
            log_data = json.loads(log_entry)
    except json.JSONDecodeError as e:
        primoroso.error(f"Invalid JSON: {e}[/red]")
        raise typer.Exit(code=1)

    # Setup detection engine
    detection_engine = DetectionEngine()

    # Load Sigma rules
    if rules_dir:
        rules_path = Path(rules_dir)
    else:
        rules_path = Path(__file__).parent.parent.parent / "rules" / "sigma"

    count = detection_engine.load_sigma_rules(rules_path)
    console.print(f"[dim]Loaded {count} Sigma rules[/dim]\n[/dim]")

    # Analyze
    detections = detection_engine.analyze_log(log_data)

    if not detections:
        primoroso.success("✅ No threats detected")
        return

    primoroso.error(f"⚠️  {len(detections)} detection(s)![/red]\n")

    for detection in detections:
        _show_detection(detection)


@app.command()
def alerts(
    action: str = typer.Argument(..., help="Action: list, show, update, escalate"),
    alert_id: Optional[str] = typer.Argument(None, help="Alert ID"),
    status: Optional[str] = typer.Option(None, "--status"),
    limit: int = typer.Option(50, "--limit"),
):
    """
    Gerencia alertas

    Examples:
        vertice detect alerts list
        vertice detect alerts list --status new
        vertice detect alerts show alert_123
        vertice detect alerts update alert_123 --status investigating
        vertice detect alerts escalate alert_123
    """
    from ..detection import AlertManager, AlertStatus

    manager = AlertManager()

    if action == "list":
        # List alerts
        status_filter = None
        if status:
            try:
                status_filter = AlertStatus[status.upper()]
            except KeyError:
                primoroso.error(f"Invalid status: {status}[/red]")
                raise typer.Exit(code=1)

        alerts_list = manager.list_alerts(status=status_filter, limit=limit)

        if not alerts_list:
            primoroso.warning("No alerts found")
            return

        table = Table(title=f"🚨 Alerts ({len(alerts_list)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title")
        table.add_column("Severity", justify="center")
        table.add_column("Priority", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Source")
        table.add_column("Count", justify="center")

        for alert in alerts_list:
            severity_colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "green",
            }
            sev_color = severity_colors.get(alert.severity, "white")

            table.add_row(
                alert.id[:12] + "...",
                alert.title[:40],
                f"[{sev_color}]{alert.severity}[/{sev_color}]",
                alert.priority.value,
                alert.status.value,
                alert.source,
                str(alert.occurrence_count),
            )

        console.print(table)

    elif action == "show":
        if not alert_id:
            primoroso.error("Alert ID required[/red]")
            raise typer.Exit(code=1)

        alert = manager.get_alert(alert_id)

        if not alert:
            primoroso.error(f"Alert not found: {alert_id}[/red]")
            raise typer.Exit(code=1)

        _show_alert_detail(alert)

    elif action == "escalate":
        if not alert_id:
            primoroso.error("Alert ID required[/red]")
            raise typer.Exit(code=1)

        # Escalate to SOAR
        from ..soar.splunk_soar import SplunkSOARConnector
        import os

        soar_url = os.getenv("SPLUNK_SOAR_URL")
        soar_key = os.getenv("SPLUNK_SOAR_API_KEY")

        if not soar_url or not soar_key:
            primoroso.warning("SOAR credentials not configured")
            primoroso.error("Set SPLUNK_SOAR_URL and SPLUNK_SOAR_API_KEY env vars")
            raise typer.Exit(code=1)

        soar = SplunkSOARConnector(soar_url, soar_key)

        primoroso.info(f"Escalating alert {alert_id} to SOAR...")

        incident_id = manager.escalate_to_soar(alert_id, soar)

        if incident_id:
            primoroso.success(f"✅ Created SOAR incident: {incident_id}")
        else:
            primoroso.error("Failed to escalate alert[/red]")


@app.command()
def rules(
    action: str = typer.Argument(..., help="Action: list, info, validate"),
    rule_type: Optional[str] = typer.Option(None, "--type", help="yara or sigma"),
    rule_name: Optional[str] = typer.Argument(None, help="Rule name"),
):
    """
    Gerencia regras de detecção

    Examples:
        vertice detect rules list
        vertice detect rules list --type yara
        vertice detect rules info Ransomware_Generic
        vertice detect rules validate
    """
    rules_base = Path(__file__).parent.parent.parent / "rules"

    if action == "list":
        # List rules
        table = Table(title="📋 Detection Rules")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Severity")
        table.add_column("Tags")

        # YARA rules
        if not rule_type or rule_type == "yara":
            yara_dir = rules_base / "yara"
            if yara_dir.exists():
                for rule_file in yara_dir.glob("*.yar*"):
                    # Parse basic info (quick)
                    content = rule_file.read_text()
                    rule_names = [
                        line.split()[1]
                        for line in content.split("\n")
                        if line.strip().startswith("rule ")
                    ]

                    for rule_name in rule_names:
                        table.add_row(rule_name, "YARA", "—", "—")

        # Sigma rules
        if not rule_type or rule_type == "sigma":
            sigma_dir = rules_base / "sigma"
            if sigma_dir.exists():
                for rule_file in sigma_dir.glob("*.yml"):
                    import yaml

                    data = yaml.safe_load(rule_file.read_text())

                    table.add_row(
                        data.get("title", rule_file.stem),
                        "Sigma",
                        data.get("level", "—"),
                        ", ".join(data.get("tags", [])[:2]),
                    )

        console.print(table)

    elif action == "validate":
        primoroso.info("Validating rules...[/cyan]\n")

        errors = 0

        # Validate YARA
        from ..detection import YARAScanner

        scanner = YARAScanner(use_backend=False)
        yara_dir = rules_base / "yara"

        if yara_dir.exists():
            try:
                count = scanner.load_rules(yara_dir)
                primoroso.success(f"✅ YARA: {count} rules valid")
            except Exception as e:
                primoroso.error(f"YARA validation failed: {e}[/red]")
                errors += 1

        # Validate Sigma
        from ..detection import SigmaParser

        parser = SigmaParser(use_backend=False)
        sigma_dir = rules_base / "sigma"

        if sigma_dir.exists():
            valid_count = 0
            for rule_file in sigma_dir.glob("*.yml"):
                try:
                    parser.load_rule(rule_file)
                    valid_count += 1
                except Exception as e:
                    primoroso.error(f"{rule_file.name}: {e}[/red]")
                    errors += 1

            primoroso.success(f"✅ Sigma: {valid_count} rules valid")

        if errors == 0:
            primoroso.error("\n[green]All rules validated successfully![/green]")
        else:
            primoroso.error(f"\n[red]{errors} validation error(s)[/red]")


@app.command()
def stream(
    live: bool = typer.Option(False, "--live", help="Live streaming mode"),
    event_type: Optional[str] = typer.Option(None, "--type"),
    duration: int = typer.Option(60, "--duration", help="Duration in seconds"),
):
    """
    Monitora event stream em tempo real

    Examples:
        vertice detect stream --live
        vertice detect stream --type detection --duration 30
    """
    from ..detection import EventStream, EventType

    primoroso.info("Connecting to event stream...")

    stream = EventStream()

    # Connect
    async def run_stream():
        connected = await stream.connect()

        if not connected:
            primoroso.error("Failed to connect to event stream[/red]")
            return

        primoroso.success("✅ Connected![/green]\n")

        # Set filter
        if event_type:
            try:
                et = EventType[event_type.upper()]
                stream.set_filter(event_types=[et])
            except KeyError:
                primoroso.warning(f"Unknown event type: {event_type}")

        # Live display
        event_count = 0

        def on_event(event):
            nonlocal event_count
            event_count += 1

            severity_colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "green",
                "info": "dim",
            }
            color = severity_colors.get(event.severity, "white")

            console.print(
                f"[{color}][{event.timestamp.strftime('%H:%M:%S')}] "
                f"{event.event_type.value}: {event.data.get('title', event.id)}[/{color}]"
            )

        stream.subscribe(on_event)

        # Wait for duration
        console.print(f"[dim]Listening for {duration} seconds...[/dim]\n[/dim]")

        await asyncio.sleep(duration)

        await stream.disconnect()

        primoroso.error(f"\n[cyan]Received {event_count} events[/cyan]")

    asyncio.run(run_stream())


# Helper functions

def _show_detection(detection):
    """Display detection details"""
    from ..detection import Detection

    severity_colors = {
        "critical": "red",
        "high": "yellow",
        "medium": "blue",
        "low": "green",
        "info": "dim",
    }
    color = severity_colors.get(detection.severity.value, "white")

    content = f"""[bold]{detection.rule_name}[/bold]
[dim]Type:[/dim] {detection.detection_type.value}
[dim]Severity:[/dim] [{color}]{detection.severity.value}[/{color}]
[dim]Source:[/dim] {detection.source}
[dim]Description:[/dim] {detection.description}
"""

    if detection.iocs:
        content += f"\n[dim]IOCs:[/dim] {', '.join(detection.iocs[:5])}"

    if detection.mitre_tactics:
        content += f"\n[dim]MITRE ATT&CK:[/dim] {', '.join(detection.mitre_tactics)}"

    console.print(Panel(content, border_style=color))


def _show_alert_detail(alert):
    """Display alert details"""
    from ..detection import Alert

    content = f"""[bold]{alert.title}[/bold]

[dim]ID:[/dim] {alert.id}
[dim]Status:[/dim] {alert.status.value}
[dim]Priority:[/dim] {alert.priority.value}
[dim]Severity:[/dim] {alert.severity}
[dim]Source:[/dim] {alert.source}

[dim]First Seen:[/dim] {alert.first_seen.strftime("%Y-%m-%d %H:%M:%S")}
[dim]Last Seen:[/dim] {alert.last_seen.strftime("%Y-%m-%d %H:%M:%S")}
[dim]Occurrences:[/dim] {alert.occurrence_count}

{alert.description}
"""

    if alert.iocs:
        content += f"\n[bold]IOCs:[/bold]\n  • " + "\n  • ".join(alert.iocs)

    if alert.soar_incident_id:
        content += f"\n\n[dim]SOAR Incident:[/dim] {alert.soar_incident_id}"

    console.print(Panel(content, title="🚨 Alert Details"))
