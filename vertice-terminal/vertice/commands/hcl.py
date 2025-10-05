"""
📝 HCL Command - Human-Centric Language
=======================================

HCL (Human-Centric Language) operations.

Commands:
    execute - Execute HCL workflow
    plan - Generate execution plan
    analyze - Analyze HCL intent
    query - Query knowledge base

Examples:
    vcli hcl execute workflow.hcl
    vcli hcl plan "Perform security audit of web application"
    vcli hcl analyze "Scan network and report vulnerabilities"
    vcli hcl query "API security best practices"
"""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing_extensions import Annotated

from ..connectors.hcl import HCLConnector
from ..utils.output import output_json, print_error, print_success
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="hcl",
    help="📝 Human-Centric Language operations",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def execute(
    workflow_file: Annotated[str, typer.Argument(help="Path to HCL workflow file")],
    context_file: Annotated[
        str,
        typer.Option("--context", "-c", help="Path to context JSON file")
    ] = None,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Execute HCL workflow.

    Examples:
        vcli hcl execute security_audit.hcl
        vcli hcl execute workflow.hcl --context vars.json
    """
    require_auth()

    async def _execute():
        # Load workflow
        try:
            with open(workflow_file, 'r') as f:
                hcl_code = f.read()
        except Exception as e:
            print_error(f"Failed to load workflow: {e}")
            raise typer.Exit(1)

        # Load context if provided
        context = None
        if context_file:
            try:
                import json as json_lib
                with open(context_file, 'r') as f:
                    context = json_lib.load(f)
            except Exception as e:
                print_error(f"Failed to load context: {e}")
                raise typer.Exit(1)

        connector = HCLConnector()
        try:
            primoroso.info(f"[bold]Executing HCL workflow:[/bold] {workflow_file}")
            result = await connector.execute_workflow(hcl_code, context)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[green]HCL Execution: {workflow_file}[/green]",
                        border_style="green"
                    ))
                print_success("Execution complete")
            else:
                print_error("Execution failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def plan(
    objective: Annotated[str, typer.Argument(help="Objective in natural language")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Generate HCL execution plan from objective.

    Examples:
        vcli hcl plan "Perform comprehensive security assessment"
        vcli hcl plan "Scan network 10.0.0.0/8 and analyze vulnerabilities"
    """
    require_auth()

    async def _execute():
        connector = HCLConnector()
        try:
            primoroso.info(f"[bold]Generating plan for:[/bold] {objective}")
            result = await connector.generate_plan(objective)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title="[cyan]HCL Plan[/cyan]",
                        border_style="cyan"
                    ))
                print_success("Plan generated")
            else:
                print_error("Plan generation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def analyze(
    intent: Annotated[str, typer.Argument(help="Intent or HCL code to analyze")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Analyze HCL intent.

    Examples:
        vcli hcl analyze "Scan network and report vulnerabilities"
        vcli hcl analyze "workflow { scan; analyze; report }"
    """
    require_auth()

    async def _execute():
        connector = HCLConnector()
        try:
            primoroso.info("[bold]Analyzing intent...[/bold]")
            result = await connector.analyze_intent(intent)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title="[yellow]HCL Analysis[/yellow]",
                        border_style="yellow"
                    ))
                print_success("Analysis complete")
            else:
                print_error("Analysis failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def query(
    search_query: Annotated[str, typer.Argument(help="Search query for knowledge base")],
    category: Annotated[
        str,
        typer.Option("--category", "-c", help="Category filter")
    ] = None,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Query HCL knowledge base.

    Examples:
        vcli hcl query "API security best practices"
        vcli hcl query "web application vulnerabilities" --category security
    """
    require_auth()

    async def _execute():
        connector = HCLConnector()
        try:
            primoroso.info(f"[bold]Querying KB:[/bold] {search_query}")
            result = await connector.query_knowledge_base(search_query, category)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title="[green]HCL Knowledge Base[/green]",
                        border_style="green"
                    ))
                print_success("Query complete")
            else:
                print_error("No results found")
        finally:
            await connector.close()

    asyncio.run(_execute())


if __name__ == "__main__":
    app()
