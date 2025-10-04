"""
🔍 SIEM Command - Security Information & Event Management

Commands:
  vcli siem logs collect <source>          - Collect logs from source
  vcli siem logs parse <file>              - Parse log file
  vcli siem logs query <search>            - Query logs
  vcli siem correlate list                 - List correlations
  vcli siem correlate rules                - List correlation rules
  vcli siem connectors list                - List SIEM connectors
  vcli siem connectors send                - Send events to SIEM
  vcli siem connectors query               - Query SIEM
  vcli siem stats                          - Show SIEM statistics

Examples:
  vcli siem logs collect syslog --host 0.0.0.0 --port 514
  vcli siem logs parse /var/log/syslog
  vcli siem logs query "failed password"
  vcli siem correlate list --severity critical
  vcli siem connectors send --siem splunk --events events.json
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
from pathlib import Path
from typing import Optional
import logging
import json

from vertice.utils import primoroso

app = typer.Typer(
    name="siem",
    help="🔍 SIEM Integration & Log Management",
)

console = Console()
logger = logging.getLogger(__name__)

# Lazy imports
_log_aggregator = None
_log_parser = None
_correlation_engine = None
_siem_connectors = {}


def get_log_aggregator():
    """Lazy load log aggregator"""
    global _log_aggregator
    if _log_aggregator is None:
        from vertice.siem import LogAggregator
        _log_aggregator = LogAggregator()
    return _log_aggregator


def get_log_parser():
    """Lazy load log parser"""
    global _log_parser
    if _log_parser is None:
        from vertice.siem import LogParser
        _log_parser = LogParser()
    return _log_parser


def get_correlation_engine():
    """Lazy load correlation engine"""
    global _correlation_engine
    if _correlation_engine is None:
        from vertice.siem import CorrelationEngine
        _correlation_engine = CorrelationEngine()
    return _correlation_engine


def get_siem_connector(name: str):
    """Lazy load SIEM connector"""
    global _siem_connectors

    if name not in _siem_connectors:
        from vertice.siem import SIEMConnector, SIEMConfig, SIEMType

        # Example configs (should be loaded from config file in production)
        if name == "splunk":
            config = SIEMConfig(
                siem_type=SIEMType.SPLUNK,
                name="Splunk Dev",
                host="localhost",
                port=8088,
                api_key="YOUR-SPLUNK-HEC-TOKEN",
                index="main",
            )
        elif name == "elastic":
            config = SIEMConfig(
                siem_type=SIEMType.ELASTIC,
                name="Elasticsearch Dev",
                host="localhost",
                port=9200,
                username="elastic",
                password="changeme",
                index="logs",
            )
        else:
            return None

        _siem_connectors[name] = SIEMConnector(config)

    return _siem_connectors[name]


# ==================== Logs Commands ====================

logs_app = typer.Typer(help="📋 Log management")
app.add_typer(logs_app, name="logs")


@logs_app.command("collect")
def logs_collect(
    source_type: str = typer.Argument(..., help="Source type (syslog, file, docker)"),
    host: str = typer.Option("0.0.0.0", "--host", help="Listen host"),
    port: int = typer.Option(514, "--port", help="Listen port"),
    file_path: Optional[str] = typer.Option(None, "--file", help="File path"),
):
    """
    📥 Collect logs from source

    Example:
        vcli siem logs collect syslog --host 0.0.0.0 --port 514
        vcli siem logs collect file --file /var/log/syslog
    """
    from vertice.siem import LogSource, LogSourceType

    aggregator = get_log_aggregator()

    # Create source
    try:
        source_type_enum = LogSourceType(source_type)
    except ValueError:
        primoroso.error(
            f"Invalid source type: {source_type}",
            suggestion=f"Valid types: {', '.join([t.value for t in LogSourceType])}"
        )
        raise typer.Exit(1)

    import uuid
    source_id = f"source-{uuid.uuid4().hex[:8]}"

    source = LogSource(
        id=source_id,
        name=f"{source_type} source",
        source_type=source_type_enum,
        host=host if source_type == "syslog" else None,
        port=port if source_type == "syslog" else None,
        file_path=file_path if source_type == "file" else None,
    )

    aggregator.add_source(source)

    primoroso.info(f"Collecting logs from {source_type}...")
    primoroso.newline()

    # Collect
    if source_type_enum == LogSourceType.SYSLOG:
        collected = aggregator.collect_from_syslog(source_id, host, port)
    elif source_type_enum == LogSourceType.FILE:
        if not file_path:
            primoroso.error("File path required for file source")
            raise typer.Exit(1)
        collected = aggregator.collect_from_file(source_id, Path(file_path))
    elif source_type_enum == LogSourceType.DOCKER:
        primoroso.warning("Docker collection not fully implemented")
        collected = 0
    else:
        primoroso.warning(f"{source_type} collection not implemented")
        collected = 0

    primoroso.success(f"Collected {collected} logs from {source_type}")


@logs_app.command("parse")
def logs_parse(
    file_path: str = typer.Argument(..., help="Log file path"),
    format_hint: Optional[str] = typer.Option(None, "--format", help="Log format hint"),
    limit: int = typer.Option(10, "--limit", help="Max logs to parse"),
):
    """
    🔧 Parse log file

    Example:
        vcli siem logs parse /var/log/syslog
        vcli siem logs parse access.log --format apache_combined
    """
    from vertice.siem import LogFormat

    path = Path(file_path)

    if not path.exists():
        primoroso.error(f"File not found: {file_path}")
        raise typer.Exit(1)

    parser = get_log_parser()

    # Parse format hint
    format_enum = None
    if format_hint:
        try:
            format_enum = LogFormat(format_hint)
        except ValueError:
            primoroso.error(
                f"Invalid format: {format_hint}",
                suggestion=f"Valid formats: {', '.join([f.value for f in LogFormat])}"
            )
            raise typer.Exit(1)

    primoroso.info(f"Parsing logs from: {path.name}")
    primoroso.newline()

    # Parse file
    parsed_logs = []

    try:
        with primoroso.spinner(f"Parsing {path.name}...") as s:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break

                    if not line.strip():
                        continue

                    parsed = parser.parse(line.strip(), format_hint=format_enum)
                    parsed_logs.append(parsed)

    except Exception as e:
        primoroso.error(f"Failed to parse file: {e}")
        raise typer.Exit(1)

    # Display results
    success_count = len([p for p in parsed_logs if p.parse_success])

    primoroso.success(
        f"Parsed {len(parsed_logs)} logs",
        details={
            "Successfully Parsed": success_count,
            "Parse Rate": f"{(success_count/len(parsed_logs)*100):.1f}%"
        }
    )

    # Show parsed logs
    if parsed_logs:
        console.print("\n[bold]Parsed Logs:[/bold]")

        table = Table(box=box.ROUNDED)
        table.add_column("Timestamp", style="cyan")
        table.add_column("Level", style="magenta")
        table.add_column("Host", style="blue")
        table.add_column("Application", style="yellow")
        table.add_column("Message", style="white")

        for parsed in parsed_logs[:10]:
            table.add_row(
                parsed.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                parsed.level,
                parsed.host or "N/A",
                parsed.application or "N/A",
                parsed.message[:60] + "..." if len(parsed.message) > 60 else parsed.message,
            )

        console.print(table)


@logs_app.command("query")
def logs_query(
    search: str = typer.Argument(..., help="Search query"),
    level: Optional[str] = typer.Option(None, "--level", help="Filter by level"),
    limit: int = typer.Option(100, "--limit", help="Max results"),
):
    """
    🔍 Query logs

    Example:
        vcli siem logs query "failed password"
        vcli siem logs query "error" --level error
    """
    from vertice.siem import LogLevel

    aggregator = get_log_aggregator()

    # Parse level
    level_enum = None
    if level:
        try:
            level_enum = LogLevel(level)
        except ValueError:
            primoroso.error(f"Invalid level: {level}")
            raise typer.Exit(1)

    primoroso.info(f"Searching logs: '{search}'")
    primoroso.newline()

    logs = aggregator.query_logs(
        search=search,
        level=level_enum,
        limit=limit,
    )

    # Display results
    primoroso.info(f"Results Found: {len(logs)}")

    if logs:
        table = Table(box=box.ROUNDED)
        table.add_column("Timestamp", style="cyan")
        table.add_column("Level", style="magenta")
        table.add_column("Source", style="blue")
        table.add_column("Message", style="white")

        for log in logs[:20]:  # Show first 20
            table.add_row(
                log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                log.level.value,
                log.source_id,
                log.message[:80] + "..." if len(log.message) > 80 else log.message,
            )

        console.print(table)


# ==================== Correlate Commands ====================

correlate_app = typer.Typer(help="🔗 Event correlation")
app.add_typer(correlate_app, name="correlate")


@correlate_app.command("list")
def correlate_list(
    severity: Optional[str] = typer.Option(None, "--severity", help="Filter by severity"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
):
    """
    📋 List correlated events

    Example:
        vcli siem correlate list --severity critical
        vcli siem correlate list --status active
    """
    from vertice.siem import CorrelationSeverity, CorrelationStatus

    engine = get_correlation_engine()

    # Parse filters
    severity_enum = None
    if severity:
        try:
            severity_enum = CorrelationSeverity(severity)
        except ValueError:
            primoroso.error(f"Invalid severity: {severity}")
            raise typer.Exit(1)

    status_enum = None
    if status:
        try:
            status_enum = CorrelationStatus(status)
        except ValueError:
            primoroso.error(f"Invalid status: {status}")
            raise typer.Exit(1)

    correlations = engine.list_correlations(
        severity=severity_enum,
        status=status_enum,
        limit=limit,
    )

    # Display
    table = Table(title=f"Correlated Events ({len(correlations)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Severity", style="magenta")
    table.add_column("Status", style="yellow")
    table.add_column("Events", justify="right", style="blue")
    table.add_column("Created", style="dim")

    for corr in correlations:
        # Severity symbol
        severity_symbols = {
            "info": "ℹ️",
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴",
        }

        sev_symbol = severity_symbols.get(corr.severity.value, "")

        table.add_row(
            corr.id,
            corr.name[:40] + "..." if len(corr.name) > 40 else corr.name,
            f"{sev_symbol} {corr.severity.value}",
            corr.status.value,
            str(corr.event_count),
            corr.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@correlate_app.command("rules")
def correlate_rules(
    correlation_type: Optional[str] = typer.Option(None, "--type", help="Filter by type"),
    enabled_only: bool = typer.Option(False, "--enabled", help="Only enabled rules"),
):
    """
    📜 List correlation rules

    Example:
        vcli siem correlate rules --type frequency --enabled
    """
    from vertice.siem import CorrelationType

    engine = get_correlation_engine()

    # Parse type
    type_enum = None
    if correlation_type:
        try:
            type_enum = CorrelationType(correlation_type)
        except ValueError:
            primoroso.error(f"Invalid type: {correlation_type}")
            raise typer.Exit(1)

    rules = engine.list_rules(
        correlation_type=type_enum,
        enabled_only=enabled_only,
    )

    # Display
    table = Table(title=f"Correlation Rules ({len(rules)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Type", style="blue")
    table.add_column("Severity", style="magenta")
    table.add_column("Matches", justify="right", style="yellow")
    table.add_column("Status", style="green")

    for rule in rules:
        status = "✅ Enabled" if rule.enabled else "❌ Disabled"

        table.add_row(
            rule.id,
            rule.name[:40] + "..." if len(rule.name) > 40 else rule.name,
            rule.correlation_type.value,
            rule.severity.value,
            str(rule.matches),
            status,
        )

    console.print(table)


# ==================== Connectors Commands ====================

connectors_app = typer.Typer(help="🔌 SIEM connectors")
app.add_typer(connectors_app, name="connectors")


@connectors_app.command("list")
def connectors_list():
    """
    📋 List configured SIEM connectors

    Example:
        vcli siem connectors list
    """
    from vertice.siem import SIEMType

    # Example connectors (should load from config in production)
    connectors_config = [
        {"name": "splunk", "type": "Splunk", "host": "localhost:8088", "status": "configured"},
        {"name": "elastic", "type": "Elasticsearch", "host": "localhost:9200", "status": "configured"},
        {"name": "qradar", "type": "IBM QRadar", "host": "qradar.example.com", "status": "not configured"},
    ]

    table = Table(title="SIEM Connectors", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Host", style="blue")
    table.add_column("Status", style="green")

    for conn in connectors_config:
        status_icon = "✅" if conn["status"] == "configured" else "⚠️"
        table.add_row(
            conn["name"],
            conn["type"],
            conn["host"],
            f"{status_icon} {conn['status']}",
        )

    console.print(table)


@connectors_app.command("test")
def connectors_test(
    siem_type: str = typer.Argument(..., help="SIEM type: splunk, elasticsearch"),
    host: str = typer.Option(..., "--host", help="SIEM server hostname"),
    port: int = typer.Option(None, "--port", help="SIEM server port"),
    token: Optional[str] = typer.Option(None, "--token", help="Authentication token (Splunk HEC)"),
    username: Optional[str] = typer.Option(None, "--username", help="Username (Elasticsearch)"),
    password: Optional[str] = typer.Option(None, "--password", help="Password (Elasticsearch)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key (Elasticsearch)"),
    ssl: bool = typer.Option(True, "--ssl/--no-ssl", help="Use SSL/TLS"),
    verify_ssl: bool = typer.Option(False, "--verify-ssl/--no-verify-ssl", help="Verify SSL certificates"),
):
    """
    🧪 Test SIEM connectivity

    Examples:
        vcli siem connectors test splunk --host splunk.example.com --token YOUR-HEC-TOKEN
        vcli siem connectors test elasticsearch --host elastic.example.com --username elastic --password changeme
    """
    from vertice.siem_integration import SplunkConnector, ElasticsearchConnector

    primoroso.info(f"Testing connection to {siem_type} at {host}...")
    primoroso.newline()

    try:
        # Create connector
        if siem_type.lower() == "splunk":
            if not port:
                port = 8088
            if not token:
                primoroso.error("Splunk requires --token parameter")
                raise typer.Exit(1)

            connector = SplunkConnector(
                host=host,
                port=port,
                token=token,
                ssl=ssl,
                verify_ssl=verify_ssl
            )

        elif siem_type.lower() == "elasticsearch":
            if not port:
                port = 9200

            connector = ElasticsearchConnector(
                host=host,
                port=port,
                username=username,
                password=password,
                api_key=api_key,
                ssl=ssl,
                verify_ssl=verify_ssl
            )

        else:
            primoroso.error(
                f"Unsupported SIEM type: {siem_type}",
                suggestion="Supported types: splunk, elasticsearch"
            )
            raise typer.Exit(1)

        # Test connection
        with primoroso.spinner(f"Testing connection to {siem_type}..."):
            success = connector.test_connection()

        if success:
            primoroso.success(
                f"Successfully connected to {siem_type}",
                details={
                    "Host": host,
                    "Port": port,
                    "SSL": "Enabled" if ssl else "Disabled"
                }
            )
        else:
            primoroso.error(f"Connection test failed for {siem_type}")
            raise typer.Exit(1)

    except Exception as e:
        primoroso.error(f"Connection failed: {e}")
        raise typer.Exit(1)


@connectors_app.command("send")
def connectors_send(
    siem_type: str = typer.Argument(..., help="SIEM type: splunk, elasticsearch"),
    host: str = typer.Option(..., "--host", help="SIEM server hostname"),
    port: int = typer.Option(None, "--port", help="SIEM server port"),
    event_type: str = typer.Option("security_event", "--event-type", help="Event type"),
    severity: str = typer.Option("info", "--severity", help="Severity: critical, high, medium, low, info"),
    description: str = typer.Option(..., "--description", help="Event description"),
    source_ip: Optional[str] = typer.Option(None, "--source-ip", help="Source IP address"),
    destination_ip: Optional[str] = typer.Option(None, "--dest-ip", help="Destination IP address"),
    token: Optional[str] = typer.Option(None, "--token", help="Authentication token (Splunk)"),
    username: Optional[str] = typer.Option(None, "--username", help="Username (Elasticsearch)"),
    password: Optional[str] = typer.Option(None, "--password", help="Password (Elasticsearch)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key (Elasticsearch)"),
    ssl: bool = typer.Option(True, "--ssl/--no-ssl", help="Use SSL/TLS"),
):
    """
    📤 Send single event to SIEM

    Examples:
        vcli siem connectors send splunk --host splunk.example.com --token TOKEN \\
            --description "SQL Injection detected" --severity high --source-ip 10.10.1.5

        vcli siem connectors send elasticsearch --host elastic.example.com \\
            --username elastic --password changeme --description "Port scan detected"
    """
    from vertice.siem_integration import SplunkConnector, ElasticsearchConnector
    from datetime import datetime

    # Build event
    event = {
        "event_type": event_type,
        "severity": severity,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    }

    if source_ip:
        event["source_ip"] = source_ip
    if destination_ip:
        event["destination_ip"] = destination_ip

    primoroso.info(f"Sending event to {siem_type}...")
    primoroso.newline()

    try:
        # Create connector
        if siem_type.lower() == "splunk":
            if not port:
                port = 8088
            if not token:
                primoroso.error("Splunk requires --token parameter")
                raise typer.Exit(1)

            connector = SplunkConnector(
                host=host,
                port=port,
                token=token,
                ssl=ssl,
                verify_ssl=False
            )

        elif siem_type.lower() == "elasticsearch":
            if not port:
                port = 9200

            connector = ElasticsearchConnector(
                host=host,
                port=port,
                username=username,
                password=password,
                api_key=api_key,
                ssl=ssl,
                verify_ssl=False
            )

        else:
            primoroso.error(f"Unsupported SIEM type: {siem_type}")
            raise typer.Exit(1)

        # Send event
        with primoroso.spinner(f"Sending to {siem_type}..."):
            success = connector.send_event(event)

        if success:
            primoroso.success(
                f"Event sent to {siem_type}",
                details={
                    "Event Type": event_type,
                    "Severity": severity,
                    "Description": description
                }
            )
        else:
            primoroso.error("Failed to send event")
            raise typer.Exit(1)

    except Exception as e:
        primoroso.error(f"Send failed: {e}")
        raise typer.Exit(1)


@connectors_app.command("sync")
def connectors_sync(
    siem_type: str = typer.Argument(..., help="SIEM type: splunk, elasticsearch"),
    host: str = typer.Option(..., "--host", help="SIEM server hostname"),
    port: int = typer.Option(None, "--port", help="SIEM server port"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace name"),
    severity_filter: Optional[str] = typer.Option(None, "--severity", help="Filter by severity"),
    limit: int = typer.Option(100, "--limit", help="Max events to sync"),
    token: Optional[str] = typer.Option(None, "--token", help="Authentication token (Splunk)"),
    username: Optional[str] = typer.Option(None, "--username", help="Username (Elasticsearch)"),
    password: Optional[str] = typer.Option(None, "--password", help="Password (Elasticsearch)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key (Elasticsearch)"),
    ssl: bool = typer.Option(True, "--ssl/--no-ssl", help="Use SSL/TLS"),
):
    """
    🔄 Sync workspace findings to SIEM

    Examples:
        vcli siem connectors sync splunk --host splunk.example.com --token TOKEN --workspace web-pentest
        vcli siem connectors sync elasticsearch --host elastic.example.com --username elastic --password changeme
    """
    from vertice.siem_integration import SplunkConnector, ElasticsearchConnector
    from vertice.workspace import WorkspaceManager
    from datetime import datetime

    # Get workspace
    ws_manager = WorkspaceManager()

    if workspace:
        ws = ws_manager.get_workspace(workspace)
        if not ws:
            primoroso.error(f"Workspace not found: {workspace}")
            raise typer.Exit(1)
    else:
        ws = ws_manager.get_active_workspace()
        if not ws:
            primoroso.error("No active workspace. Use --workspace to specify one.")
            raise typer.Exit(1)

    primoroso.info(f"Syncing workspace '{ws.name}' to {siem_type}...")
    primoroso.newline()

    try:
        # Create connector
        if siem_type.lower() == "splunk":
            if not port:
                port = 8088
            if not token:
                primoroso.error("Splunk requires --token parameter")
                raise typer.Exit(1)

            connector = SplunkConnector(
                host=host,
                port=port,
                token=token,
                ssl=ssl,
                verify_ssl=False
            )

        elif siem_type.lower() == "elasticsearch":
            if not port:
                port = 9200

            connector = ElasticsearchConnector(
                host=host,
                port=port,
                username=username,
                password=password,
                api_key=api_key,
                ssl=ssl,
                verify_ssl=False
            )

        else:
            primoroso.error(f"Unsupported SIEM type: {siem_type}")
            raise typer.Exit(1)

        # Get findings from workspace
        findings = ws.get_vulnerabilities(limit=limit)

        if severity_filter:
            findings = [f for f in findings if f.severity.lower() == severity_filter.lower()]

        if not findings:
            primoroso.warning("No findings to sync")
            return

        # Convert findings to events
        events = []
        for finding in findings:
            event = {
                "event_type": "vulnerability",
                "severity": finding.severity,
                "description": finding.description,
                "host": finding.host,
                "port": finding.port,
                "cve_id": finding.cve_id if hasattr(finding, 'cve_id') else None,
                "timestamp": datetime.utcnow().isoformat(),
                "workspace": ws.name
            }
            events.append(event)

        # Send batch
        with primoroso.spinner(f"Syncing {len(events)} findings to {siem_type}..."):
            stats = connector.send_batch(events)

        primoroso.success(
            f"Sync complete",
            details={
                "Workspace": ws.name,
                "Sent": stats["sent"],
                "Failed": stats["failed"],
                "Success Rate": f"{(stats['sent']/len(events)*100):.1f}%"
            }
        )

    except Exception as e:
        primoroso.error(f"Sync failed: {e}")
        raise typer.Exit(1)


@connectors_app.command("format")
def connectors_format(
    format_type: str = typer.Argument(..., help="Format type: cef, leef, json"),
    event_type: str = typer.Option("vulnerability", "--event-type", help="Event type"),
    severity: str = typer.Option("high", "--severity", help="Severity level"),
    description: str = typer.Option("SQL Injection vulnerability found", "--description", help="Event description"),
    source_ip: Optional[str] = typer.Option("10.10.1.5", "--source-ip", help="Source IP address"),
    destination_ip: Optional[str] = typer.Option("192.168.1.10", "--dest-ip", help="Destination IP address"),
    source_port: Optional[int] = typer.Option(3306, "--source-port", help="Source port"),
):
    """
    🎨 Show event formatting examples

    Examples:
        vcli siem connectors format cef
        vcli siem connectors format leef --severity critical
        vcli siem connectors format json --event-type threat_detected
    """
    from vertice.siem_integration import CEFFormatter, LEEFFormatter, JSONFormatter
    from datetime import datetime

    # Build sample event
    event = {
        "event_type": event_type,
        "severity": severity,
        "description": description,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "source_port": source_port,
        "timestamp": datetime.utcnow().isoformat()
    }

    primoroso.info(f"Event Format: {format_type.upper()}")
    primoroso.newline()

    try:
        # Format event
        if format_type.lower() == "cef":
            formatter = CEFFormatter()
            formatted = formatter.format(event)

            console.print(Panel(
                formatted,
                title="[bold cyan]CEF Format[/bold cyan]",
                subtitle="Common Event Format (ArcSight, Splunk)",
                border_style="cyan"
            ))

            console.print("\n[bold]CEF Format Structure:[/bold]")
            console.print("CEF:Version|Vendor|Product|Version|SignatureID|Name|Severity|Extension")
            console.print("\n[bold]Extension Fields:[/bold]")
            console.print("  src    = Source IP address")
            console.print("  dst    = Destination IP address")
            console.print("  spt    = Source port")
            console.print("  dpt    = Destination port")
            console.print("  msg    = Message")
            console.print("  rt     = Receipt time")

        elif format_type.lower() == "leef":
            formatter = LEEFFormatter()
            formatted = formatter.format(event)

            console.print(Panel(
                formatted,
                title="[bold magenta]LEEF Format[/bold magenta]",
                subtitle="Log Event Extended Format (QRadar)",
                border_style="magenta"
            ))

            console.print("\n[bold]LEEF Format Structure:[/bold]")
            console.print("LEEF:Version|Vendor|Product|Version|EventID|<TAB>Key1=Value1<TAB>Key2=Value2")

        elif format_type.lower() == "json":
            formatter = JSONFormatter()
            formatted = formatter.format(event)

            syntax = Syntax(formatted, "json", theme="monokai", line_numbers=False)
            console.print(Panel(
                syntax,
                title="[bold green]JSON Format[/bold green]",
                subtitle="Splunk HEC, Elasticsearch",
                border_style="green"
            ))

        else:
            primoroso.error(
                f"Unsupported format: {format_type}",
                suggestion="Supported formats: cef, leef, json"
            )
            raise typer.Exit(1)

    except Exception as e:
        primoroso.error(f"Formatting failed: {e}")
        raise typer.Exit(1)


# ==================== Stats Command ====================

@app.command()
def stats():
    """
    📊 Show SIEM statistics

    Example:
        vcli siem stats
    """
    aggregator = get_log_aggregator()
    parser = get_log_parser()
    engine = get_correlation_engine()

    # Get statistics
    agg_stats = aggregator.get_statistics()
    parser_stats = parser.get_statistics()
    corr_stats = engine.get_statistics()

    primoroso.panel(
        "SIEM System Statistics",
        title="📊 Statistics",
        gradient_title=True,
        border_style="cyan"
    )

    # Log Aggregator
    primoroso.newline()
    primoroso.info("Log Aggregator")
    console.print(f"  Total Sources: {agg_stats['total_sources']}")
    console.print(f"  Active Sources: {agg_stats['active_sources']}")
    console.print(f"  Total Logs Collected: {agg_stats['total_logs_collected']}")
    console.print(f"  Buffer Size: {agg_stats['buffer_size']}")

    # Log Parser
    primoroso.newline()
    primoroso.info("Log Parser")
    console.print(f"  Total Patterns: {parser_stats['total_patterns']}")
    console.print(f"  Custom Patterns: {parser_stats['custom_patterns']}")
    console.print(f"  Supported Formats: {len(parser_stats['supported_formats'])}")

    # Correlation Engine
    primoroso.newline()
    primoroso.info("Correlation Engine")
    console.print(f"  Total Rules: {corr_stats['total_rules']}")
    console.print(f"  Enabled Rules: {corr_stats['enabled_rules']}")
    console.print(f"  Events Processed: {corr_stats['total_events_processed']}")
    console.print(f"  Total Correlations: {corr_stats['total_correlations']}")
    console.print(f"  Active Correlations: {corr_stats['active_correlations']}")


# ==================== Main Command ====================

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    🔍 SIEM Integration & Log Management

    Aggregate, parse, correlate, and analyze security logs from
    multiple sources. Integrate with enterprise SIEMs like Splunk,
    Elastic, QRadar, and more.

    Features:
    - Multi-source log aggregation (syslog, file, docker, cloud)
    - Multi-format log parsing (syslog, JSON, CEF, Apache, etc)
    - Event correlation & attack chain detection
    - SIEM integration (Splunk, Elastic, QRadar)
    - MITRE ATT&CK mapping
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
