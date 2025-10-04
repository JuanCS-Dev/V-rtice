"""
💼 Workspace Command - AI-Powered Workspace Intelligence
=========================================================

Commands:
  vcli workspace query <question>           - Natural language queries
  vcli workspace correlate <service> <ver>  - CVE/ExploitDB correlation
  vcli workspace suggest                    - Context-aware suggestions
  vcli workspace report [--format md]       - Generate reports

Examples:
  vcli workspace query "show all web servers"
  vcli workspace query "what hosts have critical vulns?"
  vcli workspace correlate Apache 2.4.41
  vcli workspace suggest
  vcli workspace report --format markdown
  vcli workspace report --format pdf --output report.pdf
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
from pathlib import Path
import json

from vertice.ai import MaximusAssistant
from vertice.utils import primoroso

app = typer.Typer(
    name="workspace",
    help="💼 AI-Powered Workspace Intelligence",
    rich_markup_mode="markdown"
)

console = Console()

# Lazy-loaded assistant
_assistant = None


def get_assistant() -> MaximusAssistant:
    """Get or create Maximus Assistant instance."""
    global _assistant
    if _assistant is None:
        # TODO: Pass actual WorkspaceManager instance
        _assistant = MaximusAssistant(workspace_manager=None)
    return _assistant


@app.command()
def query(
    question: str = typer.Argument(..., help="Natural language question"),
    limit: int = typer.Option(20, "--limit", help="Max results to show"),
):
    """
    🔍 Natural Language Workspace Queries

    Ask questions about your workspace in plain English.

    Examples:
        vcli workspace query "show all web servers"
        vcli workspace query "what hosts have critical vulns?"
        vcli workspace query "find SSH with weak auth"
        vcli workspace query "how many hosts are up?"
        vcli workspace query "list all vulnerabilities"
    """
    assistant = get_assistant()

    primoroso.info(f"Processing query: {question}")
    primoroso.newline()

    # Execute NL query
    with primoroso.spinner("Analyzing query..."):
        result = assistant.query_nl(question)

    # Display results
    if "error" in result:
        primoroso.error(
            result["error"],
            suggestion="Try one of these formats:\n" + "\n".join(result.get("suggestions", []))
        )
        raise typer.Exit(1)

    # Show parsed query
    primoroso.success(f"Understood: {result['question']}")

    console.print("\n[bold]Parsed Query:[/bold]")
    parsed = result["parsed_query"]
    for key, value in parsed.items():
        console.print(f"  • {key}: [cyan]{value}[/cyan]")

    # Show results
    results = result.get("results", [])
    count = result.get("count", 0)

    console.print(f"\n[bold]Results:[/bold] {count} found")

    if results:
        # Display as table
        table = Table(box=box.ROUNDED)

        # Add columns based on result keys
        if results:
            for key in results[0].keys():
                table.add_column(key.title(), style="cyan")

        # Add rows
        for item in results[:limit]:
            table.add_row(*[str(v) for v in item.values()])

        console.print(table)

    elif count == 0:
        primoroso.warning("No results found")


@app.command()
def correlate(
    service: str = typer.Argument(..., help="Service name (e.g., Apache, OpenSSH)"),
    version: str = typer.Argument(..., help="Version string (e.g., 2.4.41, 8.2p1)"),
    show_exploits: bool = typer.Option(True, "--exploits/--no-exploits", help="Show exploits"),
):
    """
    🔗 CVE/ExploitDB Correlation

    Automatically lookup CVEs and exploits for service versions.

    Examples:
        vcli workspace correlate Apache 2.4.41
        vcli workspace correlate OpenSSH 8.2p1
        vcli workspace correlate "Microsoft IIS" 10.0
    """
    assistant = get_assistant()

    primoroso.info(f"Correlating vulnerabilities for {service} {version}...")
    primoroso.newline()

    # Correlate vulnerabilities
    with primoroso.spinner("Searching CVE database..."):
        vulns = assistant.correlate_vulns(service, version)

    if not vulns:
        primoroso.warning(f"No known CVEs found for {service} {version}")
        return

    # Display results
    primoroso.success(f"Found {len(vulns)} CVE(s)")
    primoroso.newline()

    for vuln in vulns:
        # CVE header
        cve_id = vuln.get("cve_id", "N/A")
        severity = vuln.get("severity", "unknown")
        cvss = vuln.get("cvss", "N/A")

        # Severity color
        severity_colors = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "green",
            "info": "blue"
        }
        severity_style = severity_colors.get(severity, "white")

        console.print(Panel(
            f"[bold]{cve_id}[/bold]\n\n"
            f"[bold]Severity:[/bold] [{severity_style}]{severity.upper()}[/{severity_style}]\n"
            f"[bold]CVSS:[/bold] {cvss}\n"
            f"[bold]Published:[/bold] {vuln.get('published', 'N/A')}\n\n"
            f"{vuln.get('description', 'No description available')}",
            title=f"[bold cyan]CVE Details[/bold cyan]",
            border_style="cyan"
        ))

        # Show exploits
        if show_exploits and "exploits" in vuln:
            exploits = vuln["exploits"]

            if exploits:
                console.print("\n[bold]Available Exploits:[/bold]")

                table = Table(box=box.SIMPLE)
                table.add_column("Source", style="cyan")
                table.add_column("ID/Module", style="yellow")
                table.add_column("Details", style="white")

                for exploit in exploits:
                    source = exploit.get("source", "Unknown")
                    id_or_module = exploit.get("id") or exploit.get("module", "N/A")
                    details = exploit.get("title") or exploit.get("rank", "")

                    table.add_row(source, id_or_module, details)

                console.print(table)

        console.print()


@app.command()
def suggest(
    show_reasoning: bool = typer.Option(True, "--reasoning/--no-reasoning", help="Show reasoning"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Filter by priority (high/medium/low)"),
):
    """
    💡 Context-Aware Suggestions

    Get intelligent next-step recommendations based on workspace analysis.

    Examples:
        vcli workspace suggest
        vcli workspace suggest --priority high
        vcli workspace suggest --no-reasoning
    """
    assistant = get_assistant()

    primoroso.info("Analyzing workspace and generating suggestions...")
    primoroso.newline()

    # Get suggestions
    with primoroso.spinner("Analyzing context..."):
        suggestions = assistant.suggest_next_steps()

    if not suggestions:
        primoroso.warning("No suggestions available")
        primoroso.info("Try running some scans first to populate the workspace")
        return

    # Filter by priority
    if priority:
        suggestions = [s for s in suggestions if s.get("priority") == priority.lower()]

    # Display suggestions
    primoroso.success(f"Generated {len(suggestions)} suggestion(s)")
    primoroso.newline()

    for i, suggestion in enumerate(suggestions, 1):
        priority_val = suggestion.get("priority", "medium")
        priority_icons = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        priority_icon = priority_icons.get(priority_val, "⚪")

        console.print(f"\n[bold]{i}. {priority_icon} {suggestion.get('action', 'N/A')}[/bold]")

        if show_reasoning:
            console.print(f"   [dim]Reason:[/dim] {suggestion.get('reason', 'N/A')}")

        console.print(f"   [dim]Priority:[/dim] {priority_val}")
        console.print(f"   [dim]Est. Time:[/dim] {suggestion.get('estimated_time', 'Unknown')}")


@app.command()
def report(
    format: str = typer.Option("markdown", "--format", "-f", help="Output format (markdown, html, pdf, json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    sections: Optional[List[str]] = typer.Option(None, "--sections", help="Sections to include"),
):
    """
    📄 Generate Reports

    Automatically generate reports from workspace data.

    Examples:
        vcli workspace report
        vcli workspace report --format html --output report.html
        vcli workspace report --format pdf --output pentest-report.pdf
        vcli workspace report --format json --sections summary,findings
    """
    assistant = get_assistant()

    primoroso.info(f"Generating {format.upper()} report...")
    primoroso.newline()

    # Generate report
    with primoroso.spinner(f"Generating {format} report..."):
        report_content = assistant.generate_report(
            format=format,
            include_sections=sections
        )

    # Save or display
    if output:
        output_path = Path(output)

        try:
            with open(output_path, 'w') as f:
                f.write(report_content)

            primoroso.success(
                f"Report saved",
                details={
                    "Format": format.upper(),
                    "File": str(output_path),
                    "Size": f"{len(report_content)} bytes"
                }
            )

        except Exception as e:
            primoroso.error(f"Failed to save report: {e}")
            raise typer.Exit(1)

    else:
        # Display in console
        console.print(Panel(
            report_content if format != "json" else Syntax(report_content, "json", theme="monokai"),
            title=f"[bold cyan]{format.upper()} Report[/bold cyan]",
            border_style="cyan"
        ))


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    💼 AI-Powered Workspace Intelligence

    Maximus Assistant provides intelligent workspace analysis:
    - Natural language queries: "show all web servers"
    - CVE correlation: Automatic vulnerability lookup
    - Smart suggestions: Context-aware next-step recommendations
    - Report generation: Markdown, HTML, PDF, JSON

    Features:
    - Query workspace data in plain English
    - Automatically correlate services with known CVEs
    - Get intelligent suggestions for next actions
    - Generate professional reports
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
