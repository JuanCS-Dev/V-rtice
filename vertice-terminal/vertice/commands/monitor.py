"""
Network Monitoring Commands - PRODUCTION READY
Uses real network_monitor_service backend
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from typing_extensions import Annotated
from typing import Optional
import time
from ..utils.output import print_json, spinner_task, print_error
from ..connectors.network_monitor import NetworkMonitorConnector
from ..utils.decorators import with_connector
from vertice.utils import primoroso

console = Console()

app = typer.Typer(
    name="monitor", help="📊 Network monitoring operations", rich_markup_mode="rich"
)


@app.command()
@with_connector(NetworkMonitorConnector)
async def start(
    interface: Annotated[
        Optional[str],
        typer.Option("--interface", "-i", help="Network interface to monitor"),
    ] = None,
    filter_type: Annotated[
        Optional[str],
        typer.Option("--filter", "-f", help="Packet filter (tcp, udp, icmp, all)"),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """
    Start network monitoring session.

    Examples:
        vertice monitor start
        vertice monitor start --interface eth0
        vertice monitor start -i wlan0 --filter tcp
    """
    filters = {}
    if filter_type:
        filters["type"] = filter_type

    with spinner_task("Starting network monitoring..."):
        result = await connector.start_monitoring(interface=interface, filters=filters)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.error("\n[bold green]✓ Network Monitoring Started[/bold green]\n")
        console.print(f"[cyan]Session ID:[/cyan] {result.get('session_id', 'N/A')}")
        console.print(f"[cyan]Interface:[/cyan] {result.get('interface', 'auto')}")
        console.print(f"[cyan]Status:[/cyan] {result.get('status', 'active')}\n")
        console.print("[dim]Use 'vertice monitor events' to view network events[/dim]")
        console.print(
            "[dim]Use 'vertice monitor stop <session_id>' to stop monitoring[/dim]"
        )


@app.command()
@with_connector(NetworkMonitorConnector)
async def stop(
    session_id: Annotated[str, typer.Argument(help="Monitoring session ID to stop")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """
    Stop active network monitoring session.

    Examples:
        vertice monitor stop abc123
        vertice monitor stop abc123 -j
    """
    with spinner_task(f"Stopping monitoring session {session_id}..."):
        result = await connector.stop_monitoring(session_id)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.error("\n[bold green]✓ Monitoring Session Stopped[/bold green]\n")
        primoroso.info(f"Session ID:[/cyan] {session_id}")
        console.print(f"[cyan]Status:[/cyan] {result.get('status', 'stopped')}")


@app.command()
@with_connector(NetworkMonitorConnector)
async def events(
    session_id: Annotated[
        Optional[str], typer.Option("--session", "-s", help="Session ID (optional)")
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum events to show")
    ] = 50,
    event_type: Annotated[
        Optional[str], typer.Option("--type", "-t", help="Filter by event type")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    follow: Annotated[
        bool, typer.Option("--follow", "-f", help="Follow events in real-time")
    ] = False,
    connector=None,
):
    """
    View network monitoring events.

    Examples:
        vertice monitor events
        vertice monitor events --session abc123
        vertice monitor events --type suspicious --limit 100
        vertice monitor events --follow
    """
    if follow:
        console.print(
            "[cyan]Following network events... (Press Ctrl+C to stop)[/cyan]\n"
        )
        try:
            while True:
                result = await connector.get_events(
                    session_id=session_id, limit=10, event_type=event_type
                )

                if "events" in result and result["events"]:
                    for event in result["events"]:
                        timestamp = event.get("timestamp", "N/A")
                        evt_type = event.get("event_type", "unknown")
                        source = event.get("source_ip", "N/A")
                        dest = event.get("dest_ip", "N/A")
                        desc = event.get("description", "")

                        console.print(
                            f"[dim]{timestamp}[/dim] "
                            f"[yellow]{evt_type}[/yellow] "
                            f"[cyan]{source}[/cyan] → [magenta]{dest}[/magenta] "
                            f"{desc}"
                        )

                time.sleep(2)  # Poll every 2 seconds

        except KeyboardInterrupt:
            primoroso.error("\n[dim]Stopped following events.[/dim]")
            return

    else:
        with spinner_task("Fetching network events..."):
            result = await connector.get_events(
                session_id=session_id, limit=limit, event_type=event_type
            )

        if not result:
            return

        if json_output:
            print_json(result)
        else:
            primoroso.error("\n[bold green]✓ Network Events Retrieved[/bold green]\n")

            if "events" in result and result["events"]:
                table = Table(
                    title="Network Events", show_header=True, header_style="bold cyan"
                )
                table.add_column("Timestamp", style="dim")
                table.add_column("Type", style="yellow")
                table.add_column("Source", style="cyan")
                table.add_column("Destination", style="magenta")
                table.add_column("Protocol", style="green")
                table.add_column("Details", style="white")

                for event in result["events"]:
                    table.add_row(
                        event.get("timestamp", "N/A"),
                        event.get("event_type", "unknown"),
                        event.get("source_ip", "N/A"),
                        event.get("dest_ip", "N/A"),
                        event.get("protocol", "N/A"),
                        event.get("description", "")[:30] + "...",
                    )

                console.print(table)
                console.print(f"\n[bold]Total events:[/bold] {len(result['events'])}")
            else:
                primoroso.warning("No network events found.")


@app.command()
@with_connector(NetworkMonitorConnector)
async def stats(
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """
    Display network monitoring statistics.

    Examples:
        vertice monitor stats
        vertice monitor stats -j
    """
    with spinner_task("Fetching network statistics..."):
        result = await connector.get_statistics()

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.error("\n[bold green]✓ Network Statistics[/bold green]\n")

        if "statistics" in result:
            stats = result["statistics"]

            summary = f"""
[cyan]Total Packets:[/cyan] {stats.get('total_packets', 0):,}
[cyan]TCP Packets:[/cyan] {stats.get('tcp_packets', 0):,}
[cyan]UDP Packets:[/cyan] {stats.get('udp_packets', 0):,}
[cyan]ICMP Packets:[/cyan] {stats.get('icmp_packets', 0):,}

[cyan]Suspicious Events:[/cyan] [yellow]{stats.get('suspicious_events', 0)}[/yellow]
[cyan]Blocked IPs:[/cyan] [red]{stats.get('blocked_ips', 0)}[/red]
[cyan]Active Sessions:[/cyan] [green]{stats.get('active_sessions', 0)}[/green]
"""
            console.print(
                Panel(summary, title="Network Statistics", border_style="cyan")
            )

            if "top_talkers" in stats:
                table = Table(title="Top Talkers", show_header=True)
                table.add_column("IP Address", style="cyan")
                table.add_column("Packets", style="yellow", justify="right")
                table.add_column("Bytes", style="green", justify="right")

                for talker in stats["top_talkers"][:10]:
                    table.add_row(
                        talker.get("ip", "N/A"),
                        str(talker.get("packets", 0)),
                        str(talker.get("bytes", 0)),
                    )

                console.print(table)


@app.command()
@with_connector(NetworkMonitorConnector)
async def alerts(
    severity: Annotated[
        Optional[str],
        typer.Option(
            "--severity", "-s", help="Filter by severity (critical, high, medium, low)"
        ),
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum alerts to show")
    ] = 50,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """
    Display network security alerts.

    Examples:
        vertice monitor alerts
        vertice monitor alerts --severity critical
        vertice monitor alerts -s high --limit 100 -j
    """
    with spinner_task("Fetching network alerts..."):
        result = await connector.get_alerts(severity=severity, limit=limit)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.error("\n[bold green]✓ Network Alerts Retrieved[/bold green]\n")

        if "alerts" in result and result["alerts"]:
            table = Table(title="Network Security Alerts", show_header=True)
            table.add_column("Timestamp", style="dim")
            table.add_column("Severity", style="red", justify="center")
            table.add_column("Alert Type", style="yellow")
            table.add_column("Source", style="cyan")
            table.add_column("Description", style="white")

            for alert in result["alerts"]:
                severity_val = alert.get("severity", "medium").upper()
                sev_color = {
                    "CRITICAL": "bold red",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "green",
                }.get(severity_val, "white")

                table.add_row(
                    alert.get("timestamp", "N/A"),
                    f"[{sev_color}]{severity_val}[/{sev_color}]",
                    alert.get("alert_type", "unknown"),
                    alert.get("source_ip", "N/A"),
                    alert.get("description", "")[:40] + "...",
                )

            console.print(table)
            console.print(f"\n[bold]Total alerts:[/bold] {len(result['alerts'])}")
        else:
            primoroso.success("✓ No alerts found. System is clean.")


@app.command()
@with_connector(NetworkMonitorConnector)
async def block(
    ip_address: Annotated[str, typer.Argument(help="IP address to block")],
    duration: Annotated[
        Optional[int],
        typer.Option(
            "--duration", "-d", help="Block duration in seconds (omit for permanent)"
        ),
    ] = None,
    reason: Annotated[
        Optional[str], typer.Option("--reason", "-r", help="Reason for blocking")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """
    Block an IP address from network access.

    Examples:
        vertice monitor block 1.2.3.4
        vertice monitor block 1.2.3.4 --duration 3600
        vertice monitor block 1.2.3.4 -d 7200 --reason "Malicious activity"
    """
    with spinner_task(f"Blocking IP address {ip_address}..."):
        result = await connector.block_ip(ip_address, duration=duration)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.error("\n[bold green]✓ IP Address Blocked[/bold green]\n")
        primoroso.info(f"IP Address:[/cyan] {ip_address}")
        console.print(
            f"[cyan]Duration:[/cyan] {'Permanent' if not duration else f'{duration} seconds'}"
        )
        console.print(f"[cyan]Status:[/cyan] {result.get('status', 'blocked')}")
        if reason:
            primoroso.info(f"Reason:[/cyan] {reason}")
