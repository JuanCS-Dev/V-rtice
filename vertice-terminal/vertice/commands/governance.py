"""
Governance Commands - Human-in-the-Loop Decision Review

CLI commands for accessing the Ethical AI Governance Workspace.
Allows operators to review and approve AI decisions in real-time.

Commands:
- governance start: Launch the Governance Workspace TUI
- governance stats: Show operator statistics
- governance health: Check backend health

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import typer
import asyncio
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from typing import Optional
from typing_extensions import Annotated
import sys

from vertice.workspaces.governance import GovernanceWorkspace

console = Console()

# Create Typer app
app = typer.Typer(
    name="governance",
    help="🏛️  Ethical AI Governance Workspace - Human-in-the-Loop (HITL) decision review",
    rich_markup_mode="rich",
)


@app.command(name="start")
def start_workspace(
    operator_id: Annotated[
        Optional[str],
        typer.Option(help="Operator identifier (auto-generated if not provided)"),
    ] = None,
    backend_url: Annotated[
        str,
        typer.Option(help="MAXIMUS backend URL"),
    ] = "http://localhost:8001",
    auto_create_session: Annotated[
        bool,
        typer.Option(help="Automatically create operator session"),
    ] = True,
):
    """
    🚀 Launch the Governance Workspace TUI.

    Opens a full-screen interactive workspace for reviewing AI ethical decisions.

    The workspace provides:
    - Real-time SSE streaming of pending decisions
    - Three-panel layout for pending, active, and resolved decisions
    - Interactive approve/reject/escalate actions
    - SLA countdown timers and warnings
    - Decision history and audit trail

    **Example:**

        $ vertice governance start
        $ vertice governance start --operator-id alice@security.com
        $ vertice governance start --backend-url http://localhost:8001
    """
    console.print("\n[bold cyan]🏛️  Governance Workspace Starting...[/bold cyan]\n")

    # Generate operator ID if not provided
    if not operator_id:
        import getpass
        import socket

        username = getpass.getuser()
        hostname = socket.gethostname()
        operator_id = f"{username}@{hostname}"
        console.print(f"[dim]Auto-generated operator ID: {operator_id}[/dim]")

    # Create session if needed
    session_id = None
    if auto_create_session:
        console.print(f"[yellow]Creating operator session...[/yellow]")
        try:
            session_id = asyncio.run(_create_session(backend_url, operator_id))
            console.print(f"[green]✓ Session created: {session_id[:16]}...[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Failed to create session: {e}[/red]")
            console.print("[yellow]Attempting to continue without session...[/yellow]\n")

    if not session_id:
        console.print("[red]✗ No session available - cannot start workspace[/red]")
        console.print("[dim]Backend may not be accessible[/dim]")
        raise typer.Exit(code=1)

    # Launch Textual app
    try:
        from textual.app import App

        class GovernanceApp(App):
            """Textual app wrapper for GovernanceWorkspace."""

            def on_mount(self) -> None:
                workspace = GovernanceWorkspace(
                    operator_id=operator_id,
                    session_id=session_id,
                    backend_url=backend_url,
                )
                self.push_screen(workspace)

        app_instance = GovernanceApp()
        app_instance.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Workspace closed by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Workspace error: {e}[/red]")
        import traceback

        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(name="stats")
def show_stats(
    operator_id: Annotated[
        Optional[str],
        typer.Option(help="Operator identifier (current user if not provided)"),
    ] = None,
    backend_url: Annotated[
        str,
        typer.Option(help="MAXIMUS backend URL"),
    ] = "http://localhost:8001",
):
    """
    📊 Show operator performance statistics.

    Displays metrics about your governance decisions:
    - Total decisions reviewed
    - Approval rate
    - Rejection rate
    - Escalation rate
    - Average review time

    **Example:**

        $ vertice governance stats
        $ vertice governance stats --operator-id alice@security.com
    """
    # Generate operator ID if not provided
    if not operator_id:
        import getpass
        import socket

        username = getpass.getuser()
        hostname = socket.gethostname()
        operator_id = f"{username}@{hostname}"

    console.print(f"\n[bold cyan]📊 Operator Statistics[/bold cyan]\n")
    console.print(f"[dim]Operator: {operator_id}[/dim]\n")

    try:
        stats = asyncio.run(_get_operator_stats(backend_url, operator_id))

        # Create stats table
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="bold white")

        table.add_row("Total Sessions", str(stats.get("total_sessions", 0)))
        table.add_row("Decisions Reviewed", str(stats.get("total_decisions_reviewed", 0)))
        table.add_row("✓ Approved", f"[green]{stats.get('total_approved', 0)}[/green]")
        table.add_row("✗ Rejected", f"[red]{stats.get('total_rejected', 0)}[/red]")
        table.add_row("⬆ Escalated", f"[yellow]{stats.get('total_escalated', 0)}[/yellow]")
        table.add_row("Approval Rate", f"{stats.get('approval_rate', 0):.1%}")
        table.add_row("Rejection Rate", f"{stats.get('rejection_rate', 0):.1%}")
        table.add_row("Escalation Rate", f"{stats.get('escalation_rate', 0):.1%}")
        table.add_row(
            "Avg Review Time", f"{stats.get('average_review_time', 0):.1f}s"
        )

        console.print(table)
        console.print()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[yellow]No statistics found for operator {operator_id}[/yellow]")
            console.print("[dim]Start reviewing decisions to see stats[/dim]")
        else:
            console.print(f"[red]✗ HTTP Error: {e.response.status_code}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Failed to retrieve stats: {e}[/red]")
        raise typer.Exit(code=1)


@app.command(name="health")
def check_health(
    backend_url: Annotated[
        str,
        typer.Option(help="MAXIMUS backend URL"),
    ] = "http://localhost:8001",
):
    """
    🏥 Check MAXIMUS Governance backend health.

    Shows:
    - Backend status
    - Active operator connections
    - Queue size
    - Decisions streamed

    **Example:**

        $ vertice governance health
        $ vertice governance health --backend-url http://localhost:8001
    """
    console.print(f"\n[bold cyan]🏥 Governance Backend Health[/bold cyan]\n")
    console.print(f"[dim]Backend: {backend_url}[/dim]\n")

    try:
        health = asyncio.run(_get_health(backend_url))

        status = health.get("status", "unknown")
        status_color = "green" if status == "healthy" else "red"

        # Create health panel
        health_text = f"""[bold {status_color}]Status:[/bold {status_color}] {status}
[bold]Active Connections:[/bold] {health.get('active_connections', 0)}
[bold]Total Connections:[/bold] {health.get('total_connections', 0)}
[bold]Decisions Streamed:[/bold] {health.get('decisions_streamed', 0)}
[bold]Queue Size:[/bold] {health.get('queue_size', 0)}
[bold]Timestamp:[/bold] {health.get('timestamp', 'N/A')}"""

        panel = Panel(health_text, title="Health Status", border_style=status_color)
        console.print(panel)
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to check health: {e}[/red]")
        console.print(f"[dim]Is MAXIMUS running at {backend_url}?[/dim]")
        raise typer.Exit(code=1)


# ============================================================================
# Helper Functions
# ============================================================================


async def _create_session(backend_url: str, operator_id: str) -> str:
    """
    Create operator session via backend API.

    Args:
        backend_url: Backend URL
        operator_id: Operator identifier

    Returns:
        Session ID

    Raises:
        httpx.HTTPError: On HTTP errors
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{backend_url}/api/v1/governance/session/create",
            json={
                "operator_id": operator_id,
                "operator_name": operator_id.split("@")[0],
                "operator_role": "soc_operator",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["session_id"]


async def _get_operator_stats(backend_url: str, operator_id: str) -> dict:
    """Get operator statistics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{backend_url}/api/v1/governance/session/{operator_id}/stats"
        )
        response.raise_for_status()
        return response.json()


async def _get_health(backend_url: str) -> dict:
    """Get backend health."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{backend_url}/api/v1/governance/health")
        response.raise_for_status()
        return response.json()
