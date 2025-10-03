"""
Threat Hunting Commands - PRODUCTION READY
Uses real threat_intel_service backend
"""

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from typing import Optional
from ..utils.output import print_json, spinner_task, print_error
from ..connectors.threat_intel import ThreatIntelConnector
from ..utils.decorators import with_connector

console = Console()

app = typer.Typer(
    name="hunt", help="🔎 Threat hunting operations", rich_markup_mode="rich"
)


@app.command()
@with_connector(ThreatIntelConnector)
async def search(
    query: Annotated[
        str, typer.Argument(help="IOC query to hunt for (IP, domain, hash, etc.)")
    ],
    ioc_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="IOC type: ip, domain, hash, email, url"),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """
    Hunt for IOCs (Indicators of Compromise) in threat intelligence databases.

    Examples:
        vertice hunt search malicious.com
        vertice hunt search 1.2.3.4 --type ip
        vertice hunt search "a1b2c3d4..." --type hash -j
    """
    if verbose:
        console.print(f"[dim]Searching for IOC: {query}...[/dim]")

    with spinner_task(f"Hunting for IOC: {query}..."):
        result = await connector.search_threat(query)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Threat Hunt Complete[/bold green]\n")

        if "threat_data" in result and result["threat_data"]:
            threat = result["threat_data"]

            console.print(f"[cyan]IOC:[/cyan] {query}")
            console.print(f"[cyan]Type:[/cyan] {threat.get('type', 'Unknown')}")
            console.print(
                f"[cyan]Reputation:[/cyan] {threat.get('reputation', 'Unknown')}"
            )

            if "risk_score" in threat:
                risk = threat["risk_score"]
                risk_color = (
                    "red" if risk >= 70 else "yellow" if risk >= 40 else "green"
                )
                console.print(
                    f"[cyan]Risk Score:[/cyan] [{risk_color}]{risk}/100[/{risk_color}]\n"
                )

            # Associated IOCs
            if "associated_iocs" in threat and threat["associated_iocs"]:
                table = Table(title="Associated IOCs", show_header=True)
                table.add_column("IOC", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Relation", style="white")

                for ioc in threat["associated_iocs"][:10]:  # Limit to 10
                    table.add_row(
                        ioc.get("value", "N/A"),
                        ioc.get("type", "N/A"),
                        ioc.get("relation", "N/A"),
                    )

                console.print(table)

            # Threat sources
            if "sources" in threat and threat["sources"]:
                console.print(f"\n[bold]Threat Intelligence Sources:[/bold]")
                for source in threat["sources"]:
                    console.print(f"  • {source}")

        else:
            console.print(f"[yellow]No threat intelligence found for: {query}[/yellow]")


@app.command()
@with_connector(ThreatIntelConnector)
async def timeline(
    incident_id: Annotated[
        str, typer.Argument(help="Incident ID to generate timeline for")
    ],
    last: Annotated[
        str, typer.Option("--last", help="Timeframe (e.g., 1h, 24h, 7d)")
    ] = "24h",
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """
    Generate a timeline of threat activity for an incident.

    Examples:
        vertice hunt timeline INC001
        vertice hunt timeline INC001 --last 48h
        vertice hunt timeline INC999 --last 7d -j
    """
    if verbose:
        console.print(f"[dim]Generating timeline for incident {incident_id}...[/dim]")

    with spinner_task(f"Building threat timeline for {incident_id}..."):
        result = await connector.get_threat_timeline(incident_id, timeframe=last)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Timeline Generated[/bold green]\n")
        console.print(f"[cyan]Incident ID:[/cyan] {incident_id}")
        console.print(f"[cyan]Timeframe:[/cyan] Last {last}\n")

        if "events" in result and result["events"]:
            table = Table(title="Threat Activity Timeline", show_header=True)
            table.add_column("Timestamp", style="cyan")
            table.add_column("Event Type", style="yellow")
            table.add_column("Description", style="white")
            table.add_column("Severity", style="red", justify="center")

            for event in result["events"]:
                severity = event.get("severity", "medium").upper()
                sev_color = {
                    "CRITICAL": "bold red",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "green",
                }.get(severity, "white")

                table.add_row(
                    event.get("timestamp", "N/A"),
                    event.get("event_type", "Unknown"),
                    event.get("description", "No description")[:50] + "...",
                    f"[{sev_color}]{severity}[/{sev_color}]",
                )

            console.print(table)
            console.print(f"\n[bold]Total events:[/bold] {len(result['events'])}")
        else:
            console.print(
                f"[yellow]No timeline data found for incident {incident_id}[/yellow]"
            )


@app.command()
@with_connector(ThreatIntelConnector)
async def pivot(
    ioc: Annotated[str, typer.Argument(help="IOC to perform pivot analysis on")],
    depth: Annotated[int, typer.Option("--depth", "-d", help="Pivot depth (1-3)")] = 1,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """
    Perform pivot analysis on an IOC to find related entities and threats.

    Examples:
        vertice hunt pivot malicious.com
        vertice hunt pivot 1.2.3.4 --depth 2
        vertice hunt pivot "hash123..." -d 3 -j
    """
    if verbose:
        console.print(f"[dim]Performing pivot analysis on: {ioc}...[/dim]")

    with spinner_task(f"Pivoting on IOC: {ioc} (depth={depth})..."):
        result = await connector.pivot_analysis(ioc, depth=depth)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Pivot Analysis Complete[/bold green]\n")
        console.print(f"[cyan]IOC:[/cyan] {ioc}")
        console.print(f"[cyan]Pivot Depth:[/cyan] {depth}\n")

        if "related_entities" in result and result["related_entities"]:
            table = Table(title="Related Entities", show_header=True)
            table.add_column("Entity", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Relation", style="white")
            table.add_column("Confidence", style="yellow", justify="right")

            for entity in result["related_entities"]:
                confidence = entity.get("confidence", 0)
                conf_color = (
                    "green"
                    if confidence >= 80
                    else "yellow" if confidence >= 50 else "red"
                )

                table.add_row(
                    entity.get("value", "N/A"),
                    entity.get("type", "N/A"),
                    entity.get("relation", "N/A"),
                    f"[{conf_color}]{confidence}%[/{conf_color}]",
                )

            console.print(table)
            console.print(
                f"\n[bold]Total related entities:[/bold] {len(result['related_entities'])}"
            )
        else:
            console.print(f"[yellow]No related entities found for: {ioc}[/yellow]")


@app.command()
@with_connector(ThreatIntelConnector)
async def correlate(
    ioc1: Annotated[str, typer.Argument(help="First IOC")],
    ioc2: Annotated[str, typer.Argument(help="Second IOC")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    connector=None,
):
    """
    Correlate two IOCs to find relationships and common infrastructure.

    Examples:
        vertice hunt correlate malicious.com 1.2.3.4
        vertice hunt correlate domain1.com domain2.com -j
    """
    with spinner_task(f"Correlating {ioc1} with {ioc2}..."):
        result = await connector.correlate_threats(ioc1, ioc2)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        console.print(f"\n[bold green]✓ Correlation Analysis Complete[/bold green]\n")
        console.print(f"[cyan]IOC 1:[/cyan] {ioc1}")
        console.print(f"[cyan]IOC 2:[/cyan] {ioc2}\n")

        if "correlation" in result:
            corr = result["correlation"]

            if "relationship" in corr:
                console.print(f"[bold]Relationship:[/bold] {corr['relationship']}")

            if "common_infrastructure" in corr and corr["common_infrastructure"]:
                console.print(f"\n[bold]Common Infrastructure:[/bold]")
                for infra in corr["common_infrastructure"]:
                    console.print(f"  • {infra}")

            if "correlation_score" in corr:
                score = corr["correlation_score"]
                score_color = (
                    "red" if score >= 70 else "yellow" if score >= 40 else "green"
                )
                console.print(
                    f"\n[cyan]Correlation Score:[/cyan] [{score_color}]{score}/100[/{score_color}]"
                )
        else:
            console.print("[yellow]No correlation found between the IOCs.[/yellow]")
