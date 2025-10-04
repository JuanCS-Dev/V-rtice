"""
🤖 ASK Command - AI Conversational Threat Hunting

Permite fazer perguntas em linguagem natural e a IA traduz para VeQL.

Exemplos:
    vertice ask "show me all PowerShell processes"
    vertice ask "find suspicious network connections"
    vertice ask investigate "ransomware activity"
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional
from vertice.utils import primoroso

app = typer.Typer(
    name="ask",
    help="🤖 AI-powered threat hunting with natural language",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def query(
    question: str = typer.Argument(..., help="Your question in natural language"),
    execute: bool = typer.Option(
        True, "--execute/--no-execute", help="Execute the generated query"
    ),
    explain: bool = typer.Option(
        False, "--explain", help="Explain the generated query"
    ),
    endpoints: Optional[str] = typer.Option(
        None, "--endpoints", "-e", help="Comma-separated endpoint IDs"
    ),
):
    """
    Ask a question in natural language, AI generates VeQL

    Examples:
        vertice ask query "show me all PowerShell processes"
        vertice ask query "find processes making external connections"
        vertice ask query "suspicious parent-child relationships" --explain
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from ..ai import AIInterpreter, SafetyGuard
    from ..query_engine import VeQLParser, QueryPlanner, QueryExecutor
    from ..fleet import EndpointRegistry, ResultAggregator

    primoroso.error("\n[bold cyan]🤖 AI Threat Hunter[/bold cyan]\n")
    console.print(f"[dim]Question: {question}[/dim]\n[/dim]")

    # Check for Gemini API key
    import os
    if not os.getenv("GEMINI_API_KEY"):
        primoroso.error("Error:[/bold red] GEMINI_API_KEY not set")
        console.print("[dim]Set environment variable: export GEMINI_API_KEY='your-key'[/dim]\n")
        raise typer.Exit(1)

    try:
        # Initialize AI
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("AI is thinking...", total=None)

            # Translate natural language to VeQL
            ai = AIInterpreter()
            veql_query = ai.natural_to_veql(question)

            progress.update(task, description="✓ Query generated", completed=True)

    except Exception as e:
        primoroso.error(f"\n[bold red]❌ AI Error:[/bold red] {e}\n")
        raise typer.Exit(1)

    # Display generated query
    console.print(Panel(
        veql_query,
        title="[bold green]Generated VeQL Query[/bold green]",
        border_style="green",
    ))

    # Explain if requested
    if explain:
        primoroso.error("\n[bold]Explanation:[/bold]")
        explanation = ai.explain_query(veql_query)
        console.print(f"[dim]{explanation}[/dim]\n[/dim]")

    # Validate safety
    guard = SafetyGuard()
    safety_check = guard.validate_query(veql_query)

    if safety_check.warnings:
        primoroso.error("\n[yellow]⚠ Safety Warnings:[/yellow]")
        for warning in safety_check.warnings:
            primoroso.error(f"• {warning}")
        console.print()

    if not safety_check.is_safe:
        primoroso.error("Query blocked by safety guard[/bold red]")
        for reason in safety_check.blocked_reasons:
            primoroso.error(f"• {reason}")
        console.print()
        raise typer.Exit(1)

    # Execute if requested
    if not execute:
        console.print(f"[dim]Use --execute to run this query[/dim]\n[/dim]")
        return

    console.print()

    # Execute query
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Executing query...", total=None)

            parser = VeQLParser()
            ast = parser.parse(veql_query)

            planner = QueryPlanner()
            plan = planner.plan(ast)

            endpoint_list = [e.strip() for e in endpoints.split(",")] if endpoints else None

            registry = EndpointRegistry()
            aggregator = ResultAggregator(deduplicate=True)

            executor = QueryExecutor(
                endpoints=endpoint_list,
                registry=registry,
                aggregator=aggregator,
            )

            result = executor.execute_sync(plan)
            progress.update(task, description="✓ Query completed", completed=True)

            registry.close()

    except Exception as e:
        primoroso.error(f"\n[bold red]❌ Execution Error:[/bold red] {e}\n")
        raise typer.Exit(1)

    # Display results
    primoroso.error("\n[bold green]✓ Results[/bold green]")
    primoroso.error(f"Endpoints queried: {result.endpoints_queried}")
    primoroso.error(f"Results: {result.total_rows} rows")
    primoroso.error(f"Execution time: {result.execution_time_ms:.2f}ms\n")

    # Detect threat level
    threat_level = ai.detect_threat_level(result.rows)

    threat_colors = {
        "LOW": "green",
        "MEDIUM": "yellow",
        "HIGH": "red",
        "CRITICAL": "bold red",
    }

    threat_color = threat_colors.get(threat_level, "white")
    primoroso.error(f"[bold]Threat Level:[/bold] [{threat_color}]{threat_level}[/{threat_color}]\n")

    # Show results
    if result.rows:
        fields = sorted(set().union(*[row.keys() for row in result.rows]))
        table = Table(show_header=True, header_style="bold cyan")

        for field in fields:
            table.add_column(field)

        for row in result.rows[:20]:  # Limit to 20
            table.add_row(*[str(row.get(f, "")) for f in fields])

        console.print(table)

        if result.total_rows > 20:
            primoroso.error(f"\n[dim]... ({result.total_rows - 20} more rows)[/dim]\n")
    else:
        console.print(f"[dim]No results found[/dim]\n[/dim]")

    # AI suggestions
    if result.rows:
        primoroso.error("\n[bold cyan]💡 AI Suggestions - Next Steps:[/bold cyan]")
        suggestions = ai.suggest_next_steps(veql_query, result.rows)

        for i, suggestion in enumerate(suggestions, 1):
            primoroso.error(f"{i}. {suggestion}")

        console.print()


@app.command()
def investigate(
    topic: str = typer.Argument(..., help="Investigation topic"),
    interactive: bool = typer.Option(
        True, "--interactive/--batch", help="Interactive multi-turn mode"
    ),
):
    """
    Start an AI-guided investigation (multi-turn)

    Examples:
        vertice ask investigate "ransomware activity"
        vertice ask investigate "lateral movement" --interactive
    """
    from ..ai import ConversationEngine

    primoroso.error("\n[bold cyan]🔍 Starting AI Investigation[/bold cyan]\n")
    primoroso.error(f"[bold]Topic:[/bold] {topic}\n")

    # Start investigation
    engine = ConversationEngine()
    investigation = engine.start_investigation(topic)

    primoroso.success(f"Investigation ID: {investigation.id}[/green]\n")

    if not interactive:
        primoroso.warning("⚠ Non-interactive mode not yet implemented")
        console.print(f"[dim]Use --interactive for guided investigation[/dim]\n[/dim]")
        return

    # Interactive mode
    console.print("[dim]Ask questions to investigate. Type 'done' to finish.[/dim]\n")

    while True:
        try:
            question = console.input("[bold cyan]Q:[/bold cyan] ")

            if question.strip().lower() in ["done", "exit", "quit"]:
                break

            # TODO: Execute question and add turn
            console.print(f"[dim]  Processing: {question}...[/dim]")
            primoroso.warning("  (Investigation engine integration pending)[/yellow]\n")

        except KeyboardInterrupt:
            primoroso.error("\n\n[yellow]Investigation interrupted[/yellow]")
            break

    # Complete investigation
    completed = engine.complete_investigation()
    primoroso.error("\n[bold green]✓ Investigation Completed[/bold green]\n")
    console.print(completed.summary())


@app.command()
def chat():
    """
    Interactive chat mode with AI threat hunter

    Example:
        vertice ask chat
    """
    primoroso.error("\n[bold cyan]💬 AI Threat Hunter Chat[/bold cyan]\n")
    console.print("[dim]Chat with the AI to hunt for threats. Type 'exit' to quit.[/dim]\n")

    while True:
        try:
            message = console.input("[bold cyan]You:[/bold cyan] ")

            if message.strip().lower() in ["exit", "quit", "bye"]:
                primoroso.error("\n[green]Goodbye! 👋[/green]\n")
                break

            primoroso.warning("AI chat integration pending...[/yellow]\n")

        except KeyboardInterrupt:
            primoroso.error("\n\n[green]Goodbye! 👋[/green]\n")
            break


if __name__ == "__main__":
    app()
