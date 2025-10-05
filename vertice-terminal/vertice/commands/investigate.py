"""
🔍 INVESTIGATE Command - AI-Orchestrated Investigation
=======================================================

Investigação completa orquestrada por Maximus AI.

Maximus decide autonomamente:
    - Quais tools usar baseado no target
    - Executa em paralelo (Tool Orchestrator)
    - Consolida findings com reasoning engine
    - Retorna relatório acionável com confidence scores

Examples:
    vcli investigate example.com --type defensive
    vcli investigate 1.2.3.4 --type offensive --depth deep
    vcli investigate user@email.com --type osint
"""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from typing_extensions import Annotated
from enum import Enum

from ..connectors.maximus_universal import MaximusUniversalConnector
from ..utils.output import output_json, print_error, print_success
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="investigate",
    help="🔍 AI-orchestrated investigation via Maximus AI",
    rich_markup_mode="rich",
)

console = Console()


class InvestigationType(str, Enum):
    auto = "auto"
    defensive = "defensive"
    offensive = "offensive"
    osint = "osint"
    full = "full"


class DepthLevel(str, Enum):
    quick = "quick"
    medium = "medium"
    deep = "deep"
    comprehensive = "comprehensive"


async def _execute_investigation(
    target: str,
    investigation_type: InvestigationType,
    depth: DepthLevel,
    json_output: bool,
    tools: list = None
):
    """Executa investigação orquestrada via Maximus."""
    connector = MaximusUniversalConnector()

    try:
        with Live(
            Spinner(
                "dots",
                text=f"[bold bright_magenta]Maximus AI investigando '{target}'...[/bold bright_magenta]",
            ),
            console=console,
            transient=True,
            refresh_per_second=20,
        ):
            # Health check
            if not await connector.health_check():
                print_error(
                    f"Maximus AI Core está offline ou inacessível"
                )
                raise typer.Exit(code=1)

            # Build investigation query
            query = f"Execute investigação {investigation_type.value} completa do target: {target}"

            if depth == DepthLevel.comprehensive:
                query += ". Use análise profunda e exaustiva."
            elif depth == DepthLevel.deep:
                query += ". Use análise detalhada."
            elif depth == DepthLevel.quick:
                query += ". Use análise rápida focada em high-level findings."

            if tools:
                query += f" Utilize as seguintes tools: {', '.join(tools)}"

            # Execute investigation
            response_data = await connector.intelligent_query(
                query=query,
                mode="deep" if depth in [DepthLevel.deep, DepthLevel.comprehensive] else "autonomous",
                context={
                    "target": target,
                    "investigation_type": investigation_type.value,
                    "depth": depth.value
                }
            )

        # Process response
        if response_data:
            if json_output:
                output_json(response_data)
            else:
                _display_investigation_results(response_data, target, investigation_type)
                print_success("Investigação concluída.")
        else:
            print_error("Não foi possível obter resposta da Maximus AI.")
            raise typer.Exit(code=1)

    except Exception as e:
        print_error(f"Erro durante investigação: {e}")
        raise typer.Exit(code=1)
    finally:
        await connector.close()


def _display_investigation_results(response_data: dict, target: str, inv_type: InvestigationType):
    """Exibe resultados da investigação de forma primorosa."""
    # Header
    console.print()
    console.print(Panel(
        f"[bold cyan]Target:[/bold cyan] {target}\n"
        f"[bold cyan]Type:[/bold cyan] {inv_type.value}",
        title="[bold green]🔍 Investigation Report[/bold green]",
        border_style="green"
    ))
    console.print()

    # Main response
    response_text = response_data.get("response", "No response")
    console.print(Panel(
        Markdown(response_text),
        title="[bold cyan]Findings[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    # Tools used
    tools_used = response_data.get("tools_used", [])
    if tools_used:
        console.print("[bold]Tools Executed:[/bold]")
        tools_table = Table(show_header=True, header_style="bold magenta")
        tools_table.add_column("Tool", style="cyan")
        tools_table.add_column("Status", style="green")

        for tool in tools_used:
            tool_name = tool.get("tool_name", "unknown")
            status = "✓ Success" if tool.get("result") else "✗ Failed"
            tools_table.add_row(tool_name, status)

        console.print(tools_table)
        console.print()

    # Reasoning trace (if available)
    reasoning = response_data.get("reasoning_trace", {})
    if reasoning:
        confidence = reasoning.get("confidence", 0)
        thoughts_count = reasoning.get("total_thoughts", 0)

        console.print(Panel(
            f"[bold]Confidence:[/bold] {confidence:.1f}%\n"
            f"[bold]Reasoning Steps:[/bold] {thoughts_count}\n"
            f"[bold]Duration:[/bold] {reasoning.get('duration', 'N/A')}",
            title="[bold yellow]⚡ Maximus Reasoning[/bold yellow]",
            border_style="yellow"
        ))
        console.print()


@app.command()
def target(
    target: Annotated[
        str,
        typer.Argument(help="Target to investigate (IP, domain, hash, email, username)")
    ],
    type: Annotated[
        InvestigationType,
        typer.Option("--type", "-t", help="Type of investigation")
    ] = InvestigationType.auto,
    depth: Annotated[
        DepthLevel,
        typer.Option("--depth", "-d", help="Depth of analysis")
    ] = DepthLevel.medium,
    tools: Annotated[
        str,
        typer.Option("--tools", help="Comma-separated list of specific tools to use")
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output in JSON format")
    ] = False,
):
    """
    Investigate a target using Maximus AI orchestration.

    Maximus will autonomously:
    - Identify target type (IP, domain, hash, etc)
    - Select relevant tools (OSINT, Cyber, Cognitive, etc)
    - Execute tools in parallel
    - Consolidate findings with reasoning
    - Provide actionable recommendations

    Examples:
        vcli investigate example.com --type defensive
        vcli investigate 1.2.3.4 --type offensive --depth deep
        vcli investigate user@email.com --type osint
        vcli investigate malware_hash --depth comprehensive
    """
    require_auth()

    tools_list = [t.strip() for t in tools.split(",")] if tools else None

    asyncio.run(_execute_investigation(
        target=target,
        investigation_type=type,
        depth=depth,
        json_output=json_output,
        tools=tools_list
    ))


@app.command()
def multi(
    targets: Annotated[
        str,
        typer.Argument(help="Comma-separated targets to investigate")
    ],
    type: Annotated[
        InvestigationType,
        typer.Option("--type", "-t", help="Type of investigation")
    ] = InvestigationType.auto,
    parallel: Annotated[
        bool,
        typer.Option("--parallel/--sequential", help="Investigate targets in parallel")
    ] = True,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output in JSON format")
    ] = False,
):
    """
    Investigate multiple targets.

    Examples:
        vcli investigate multi "example.com,test.com,sample.org" --parallel
        vcli investigate multi "1.2.3.4,5.6.7.8" --type defensive
    """
    require_auth()

    target_list = [t.strip() for t in targets.split(",")]

    primoroso.info(f"[bold]Investigating {len(target_list)} targets[/bold]")
    primoroso.info(f"Mode: {'Parallel' if parallel else 'Sequential'}")
    console.print()

    if parallel:
        # TODO: Implement parallel investigation
        primoroso.warning("Parallel mode not yet implemented. Running sequentially...")

    for target in target_list:
        asyncio.run(_execute_investigation(
            target=target,
            investigation_type=type,
            depth=DepthLevel.quick,  # Quick for multi-target
            json_output=json_output
        ))


@app.command()
def history(
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Number of recent investigations to show")
    ] = 10,
):
    """
    Show investigation history from Maximus memory.

    Examples:
        vcli investigate history
        vcli investigate history --limit 20
    """
    require_auth()

    async def _get_history():
        connector = MaximusUniversalConnector()
        try:
            # Query Maximus memory for recent investigations
            query = f"Liste as últimas {limit} investigações executadas"

            response = await connector.intelligent_query(query, mode="guided")

            if response:
                console.print()
                console.print(Panel(
                    Markdown(response.get("response", "No history found")),
                    title="[bold green]📚 Investigation History[/bold green]",
                    border_style="green"
                ))
                console.print()
            else:
                primoroso.warning("No investigation history found")

        finally:
            await connector.close()

    asyncio.run(_get_history())


@app.command()
def similar(
    target: Annotated[
        str,
        typer.Argument(help="Find investigations similar to this target")
    ],
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Number of similar investigations to show")
    ] = 5,
):
    """
    Find similar past investigations (semantic search).

    Examples:
        vcli investigate similar example.com
        vcli investigate similar "malware_hash" --limit 10
    """
    require_auth()

    async def _find_similar():
        connector = MaximusUniversalConnector()
        try:
            similar_invs = await connector.find_similar_investigations(target, limit)

            if similar_invs:
                console.print()
                console.print(f"[bold]Found {len(similar_invs)} similar investigations:[/bold]")
                console.print()

                for inv in similar_invs:
                    console.print(Panel(
                        f"[bold]Target:[/bold] {inv.get('target', 'N/A')}\n"
                        f"[bold]Findings:[/bold] {inv.get('summary', 'N/A')[:200]}...",
                        title=f"[cyan]{inv.get('investigation_id', 'unknown')}[/cyan]",
                        border_style="cyan"
                    ))
                console.print()
            else:
                primoroso.warning(f"No similar investigations found for '{target}'")

        finally:
            await connector.close()

    asyncio.run(_find_similar())


if __name__ == "__main__":
    app()
