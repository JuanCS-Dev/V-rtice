"""
🧠 MEMORY Command - Maximus Memory System
==========================================

Manage Maximus AI memory system.

Commands:
    status - Memory system status
    recall - Recall past conversation
    similar - Find similar investigations
    stats - Tool usage statistics

Examples:
    vcli memory status
    vcli memory recall session_abc123
    vcli memory similar "example.com"
    vcli memory stats threat_intel --days 30
"""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from typing_extensions import Annotated

from ..connectors.maximus_universal import MaximusUniversalConnector
from ..utils.output import output_json, print_error, print_success
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="memory",
    help="🧠 Maximus Memory System management",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def status(
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Get memory system status.

    Shows:
    - Total conversations stored
    - Total messages
    - Total investigations
    - Memory usage

    Examples:
        vcli memory status
    """
    require_auth()

    async def _execute():
        connector = MaximusUniversalConnector()
        try:
            primoroso.info("[bold]Fetching memory system status...[/bold]")
            result = await connector.get_memory_stats()

            if result:
                if json:
                    output_json(result)
                else:
                    # Display as table
                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="green")

                    for key, value in result.items():
                        table.add_row(key, str(value))

                    console.print()
                    console.print(Panel(
                        table,
                        title="[green]🧠 Memory System Status[/green]",
                        border_style="green"
                    ))
                    console.print()
                print_success("Status retrieved")
            else:
                print_error("Failed to get status")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def recall(
    session_id: Annotated[str, typer.Argument(help="Session ID to recall")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Recall past conversation from memory.

    Examples:
        vcli memory recall session_abc123
    """
    require_auth()

    async def _execute():
        connector = MaximusUniversalConnector()
        try:
            primoroso.info(f"[bold]Recalling session:[/bold] {session_id}")
            result = await connector.recall_conversation(session_id)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print()
                    console.print(Panel(
                        Markdown(f"""
**Session ID:** {result.get('session_id')}
**User ID:** {result.get('user_id')}
**Messages:** {result.get('message_count')}
**Created:** {result.get('created_at')}
**Last Activity:** {result.get('last_activity')}
                        """),
                        title=f"[cyan]Session: {session_id}[/cyan]",
                        border_style="cyan"
                    ))

                    # Display recent messages
                    messages = result.get('messages', [])
                    if messages:
                        console.print("\n[bold]Recent Messages:[/bold]")
                        for msg in messages[-10:]:  # Last 10
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')[:200]
                            console.print(f"\n[cyan]{role}:[/cyan] {content}...")

                    console.print()
                print_success("Session recalled")
            else:
                print_error("Session not found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def similar(
    target: Annotated[str, typer.Argument(help="Target to search similar investigations")],
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Number of results")
    ] = 5,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Find similar past investigations (semantic search).

    Uses embeddings to find related investigations.

    Examples:
        vcli memory similar example.com --limit 10
        vcli memory similar "malware_hash_abc123"
    """
    require_auth()

    async def _execute():
        connector = MaximusUniversalConnector()
        try:
            primoroso.info(f"[bold]Searching similar investigations:[/bold] {target}")
            result = await connector.find_similar_investigations(target, limit)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print()
                    console.print(f"[bold]Found {len(result)} similar investigations:[/bold]")
                    console.print()

                    for inv in result:
                        console.print(Panel(
                            f"[bold]Investigation ID:[/bold] {inv.get('investigation_id')}\n"
                            f"[bold]Target:[/bold] {inv.get('target')}\n"
                            f"[bold]Summary:[/bold] {inv.get('summary', 'N/A')[:200]}...\n"
                            f"[bold]Similarity:[/bold] {inv.get('similarity_score', 'N/A')}",
                            border_style="cyan"
                        ))
                    console.print()
                print_success("Search complete")
            else:
                print_error("No similar investigations found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def stats(
    tool_name: Annotated[str, typer.Argument(help="Tool name to get stats")],
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Last N days of data")
    ] = 30,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Get tool usage statistics.

    Shows:
    - Total executions
    - Success rate
    - Average execution time
    - Error types

    Examples:
        vcli memory stats threat_intel --days 30
        vcli memory stats nmap_scan --days 7
    """
    require_auth()

    async def _execute():
        connector = MaximusUniversalConnector()
        try:
            primoroso.info(f"[bold]Fetching stats for:[/bold] {tool_name}")
            result = await connector.get_tool_stats(tool_name, days)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print()
                    console.print(Panel(
                        Markdown(f"""
**Tool:** {tool_name}
**Period:** Last {days} days
**Total Executions:** {result.get('total_executions', 0)}
**Success Rate:** {result.get('success_rate', 0):.1f}%
**Avg Execution Time:** {result.get('avg_execution_time_ms', 0):.0f}ms
                        """),
                        title=f"[green]Tool Stats: {tool_name}[/green]",
                        border_style="green"
                    ))

                    # Error types
                    error_types = result.get('error_types', {})
                    if error_types:
                        console.print("\n[bold]Error Types:[/bold]")
                        error_table = Table()
                        error_table.add_column("Error", style="red")
                        error_table.add_column("Count", style="yellow")

                        for error, count in error_types.items():
                            error_table.add_row(error, str(count))

                        console.print(error_table)

                    console.print()
                print_success("Stats retrieved")
            else:
                print_error("Tool not found or no data")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def clear(
    confirm: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
):
    """
    Clear memory system (DANGEROUS).

    This will delete all conversations, investigations, and memory.

    Examples:
        vcli memory clear --yes
    """
    require_auth()

    if not confirm:
        primoroso.warning("[bold red]⚠️  WARNING: This will delete all memory![/bold red]")
        console.print("\nThis action cannot be undone. Use --yes to confirm.\n")
        raise typer.Exit(0)

    primoroso.error("[bold red]Memory clear not yet implemented for safety[/bold red]")
    console.print("[dim]Contact system administrator to clear memory[/dim]\n")


if __name__ == "__main__":
    app()
