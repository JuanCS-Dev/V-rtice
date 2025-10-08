"""
Threat Hunting Commands - PRODUCTION READY
Uses real threat_intel_service backend
UI/UX Blueprint v1.2 - Gemini-style refinado
"""

import typer
from rich.console import Console
from typing_extensions import Annotated
from typing import Optional
from ..utils.output import (
    print_json,
    spinner_task,
    print_error,
    GeminiStyleTable,
    PrimordialPanel,
)
from ..connectors.threat_intel import ThreatIntelConnector
from ..utils.decorators import with_connector
from vertice.utils import primoroso

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
        typer.Option("--type", help="IOC type: ip, domain, hash, email, url"),
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
        if "threat_data" in result and result["threat_data"]:
            threat = result["threat_data"]

            # Métricas principais em painel primoroso
            metrics = {
                "IOC": query,
                "Type": threat.get('type', 'Unknown'),
                "Reputation": threat.get('reputation', 'Unknown'),
            }

            if "risk_score" in threat:
                risk = threat["risk_score"]
                metrics["Risk Score"] = f"{risk}/100"

            PrimordialPanel.metrics_panel(
                metrics,
                title="🎯 Threat Hunt Results",
                console=console
            )

            # Associated IOCs em tabela primorosa
            if "associated_iocs" in threat and threat["associated_iocs"]:
                console.print()
                table = GeminiStyleTable(
                    title="Associated IOCs",
                    console=console
                )
                table.add_column("IOC", width=40)
                table.add_column("Type", alignment="center", width=15)
                table.add_column("Relation", width=25)

                for ioc in threat["associated_iocs"][:10]:  # Limit to 10
                    table.add_row(
                        ioc.get("value", "N/A"),
                        ioc.get("type", "N/A"),
                        ioc.get("relation", "N/A"),
                    )

                table.render()

            # Threat sources
            if "sources" in threat and threat["sources"]:
                console.print()
                sources_text = "\n".join([f"• {source}" for source in threat["sources"]])
                PrimordialPanel.info(
                    sources_text,
                    title="📊 Threat Intelligence Sources",
                    console=console
                )

        else:
            PrimordialPanel.warning(
                f"No threat intelligence found for: {query}",
                console=console
            )


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
        # Header com contexto
        PrimordialPanel.success(
            f"Incident: {incident_id}\nTimeframe: Last {last}",
            title="✓ Timeline Generated",
            console=console
        )

        if "events" in result and result["events"]:
            console.print()
            table = GeminiStyleTable(
                title="Threat Activity Timeline",
                console=console
            )
            table.add_column("Timestamp", width=20)
            table.add_column("Event Type", width=20)
            table.add_column("Description", width=50)
            table.add_column("Severity", alignment="center", width=12)

            for event in result["events"]:
                severity = event.get("severity", "medium").lower()

                # Mapeia severity para status do builder
                status_map = {
                    "critical": "error",
                    "high": "error",
                    "medium": "warning",
                    "low": "info",
                }

                desc = event.get("description", "No description")
                truncated_desc = desc[:50] + "..." if len(desc) > 50 else desc

                table.add_row_with_status(
                    event.get("timestamp", "N/A"),
                    event.get("event_type", "Unknown"),
                    truncated_desc,
                    severity.upper(),
                    status=status_map.get(severity, "info"),
                )

            table.render()

            console.print(f"\n[grey70]Total events: {len(result['events'])}[/grey70]")
        else:
            PrimordialPanel.warning(
                f"No timeline data found for incident {incident_id}",
                console=console
            )


@app.command()
def artifact(
    artifact_name: str = typer.Argument(..., help="Artifact name to execute"),
    endpoints: Optional[str] = typer.Option(
        None, "--endpoints", help="Comma-separated endpoint IDs"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json"
    ),
    list_artifacts: bool = typer.Option(
        False, "--list", "-l", help="List all available artifacts"
    ),
):
    """
    Execute pre-built artifact query (NEW!)

    Examples:
        vertice hunt artifact suspicious_network
        vertice hunt artifact powershell_execution
        vertice hunt artifact lateral_movement --endpoints HOST-01,HOST-02
        vertice hunt artifact --list
    """
    from ..artifacts import get_library

    library = get_library()

    # List artifacts
    if list_artifacts:
        artifacts = library.list()

        primoroso.error(f"\n[bold cyan]📚 Available Artifacts ({len(artifacts)})[/bold cyan]\n")

        for art in artifacts:
            severity_color = {
                "critical": "bold red",
                "high": "red",
                "medium": "yellow",
                "low": "green",
            }.get(art.severity, "white")

            primoroso.error(f"[bold]{art.name}[/bold]")
            primoroso.error(f"ID: [cyan]{artifact_name}[/cyan]")
            primoroso.error(f"Description: {art.description}")
            primoroso.error(f"Severity: [{severity_color}]{art.severity.upper()}[/{severity_color}]")
            console.print(f"  Tags: {', '.join(art.tags)}\n")

        return

    # Execute artifact
    artifact = library.get(artifact_name)

    if not artifact:
        primoroso.error(f"\n[bold red]❌ Artifact not found:[/bold red] {artifact_name}")
        primoroso.error("\n[dim]Use --list to see available artifacts[/dim]\n")
        raise typer.Exit(1)

    primoroso.error(f"\n[bold cyan]📚 Executing Artifact: {artifact.name}[/bold cyan]\n")
    console.print(f"[dim]Description: {artifact.description}[/dim]")
    console.print(f"[dim]Severity: {artifact.severity.upper()}[/dim]\n[/dim]")

    # Execute artifact query using hunt query command
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from ..query_engine import VeQLParser, QueryPlanner, QueryExecutor
    from ..fleet import EndpointRegistry, ResultAggregator

    endpoint_list = [e.strip() for e in endpoints.split(",")] if endpoints else None

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Executing artifact...", total=None)

            parser = VeQLParser()
            ast = parser.parse(artifact.query)

            planner = QueryPlanner()
            plan = planner.plan(ast)

            registry = EndpointRegistry()
            aggregator = ResultAggregator(deduplicate=True)

            executor = QueryExecutor(
                endpoints=endpoint_list,
                registry=registry,
                aggregator=aggregator,
            )

            result = executor.execute_sync(plan)
            progress.update(task, description="✓ Artifact completed", completed=True)

            registry.close()

    except Exception as e:
        primoroso.error(f"\n[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(1)

    # Display results
    primoroso.error("\n[bold green]✓ Artifact Completed[/bold green]")
    primoroso.error(f"Results: {result.total_rows} rows")
    primoroso.error(f"Execution time: {result.execution_time_ms:.2f}ms\n")

    # Show remediation if findings
    if result.total_rows > 0 and artifact.remediation:
        primoroso.error("[bold yellow]⚠ Remediation Steps:[/bold yellow]")
        for step in artifact.remediation:
            primoroso.error(f"• {step}")
        console.print()

    # Output results
    if output_format == "table" and result.rows:
        fields = artifact.output_fields or sorted(set().union(*[row.keys() for row in result.rows]))
        table = Table(show_header=True, header_style="bold cyan")

        for field in fields:
            table.add_column(field)

        for row in result.rows[:50]:
            table.add_row(*[str(row.get(f, "")) for f in fields])

        console.print(table)

        if result.total_rows > 50:
            primoroso.error(f"\n[dim]... ({result.total_rows - 50} more rows)[/dim]")

    elif output_format == "json":
        import json
        console.print(json.dumps(result.rows, indent=2))


@app.command()
@with_connector(ThreatIntelConnector)
async def pivot(
    ioc: Annotated[str, typer.Argument(help="IOC to perform pivot analysis on")],
    depth: Annotated[int, typer.Option("--depth", help="Pivot depth (1-3)")] = 1,
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
        primoroso.error("\n[bold green]✓ Pivot Analysis Complete[/bold green]\n")
        primoroso.info(f"IOC:[/cyan] {ioc}")
        primoroso.info(f"Pivot Depth:[/cyan] {depth}\n")

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
            primoroso.warning(f"No related entities found for: {ioc}")


@app.command()
def query(
    veql_query: str = typer.Argument(..., help="VeQL query to execute"),
    endpoints: Optional[str] = typer.Option(
        None, "--endpoints", help="Comma-separated endpoint IDs (default: all online)"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json, csv"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Limit number of results"
    ),
    deduplicate: bool = typer.Option(
        True, "--deduplicate/--no-deduplicate", help="Remove duplicate results"
    ),
):
    """
    Execute VeQL query across fleet (NEW!)

    Examples:
        vertice hunt query "SELECT process.name FROM endpoints WHERE process.parent = 'powershell.exe'"
        vertice hunt query "SELECT * FROM endpoints" --limit 100
        vertice hunt query "SELECT network.remote_ip FROM endpoints" --format json
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from ..query_engine import VeQLParser, QueryPlanner, QueryExecutor
    from ..fleet import EndpointRegistry, ResultAggregator

    primoroso.error("\n[bold cyan]🎯 Executing VeQL Query[/bold cyan]\n")

    # Parse endpoints
    endpoint_list = [e.strip() for e in endpoints.split(",")] if endpoints else None

    if endpoint_list:
        console.print(f"[dim]Target endpoints: {', '.join(endpoint_list)}[/dim]")
    else:
        console.print(f"[dim]Target: All online endpoints[/dim]")

    console.print(f"[dim]Query: {veql_query}[/dim]\n[/dim]")

    # Parse and execute
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Parsing query...", total=None)

            parser = VeQLParser()
            ast = parser.parse(veql_query)

            if limit and not ast.limit:
                ast.limit = limit

            progress.update(task, description="Planning execution...")
            planner = QueryPlanner()
            plan = planner.plan(ast)

            progress.update(task, description="Executing query...")

            registry = EndpointRegistry()
            aggregator = ResultAggregator(deduplicate=deduplicate) if deduplicate else None

            executor = QueryExecutor(
                endpoints=endpoint_list,
                registry=registry,
                aggregator=aggregator,
            )

            result = executor.execute_sync(plan)
            progress.update(task, description="✓ Query completed", completed=True)

            registry.close()

    except Exception as e:
        primoroso.error(f"\n[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(1)

    # Display results
    primoroso.error("\n[bold green]✓ Query Completed[/bold green]")
    primoroso.error(f"Endpoints queried: {result.endpoints_queried}")
    primoroso.error(f"Results: {result.total_rows} rows")
    primoroso.error(f"Execution time: {result.execution_time_ms:.2f}ms\n")

    if result.errors:
        primoroso.warning(f"⚠ Errors: {len(result.errors)}[/yellow]\n")

    # Output
    if output_format == "table":
        if result.rows:
            from rich.table import Table

            fields = sorted(set().union(*[row.keys() for row in result.rows]))
            table = Table(show_header=True, header_style="bold cyan")

            for field in fields:
                table.add_column(field)

            for row in result.rows[:50]:
                table.add_row(*[str(row.get(f, "")) for f in fields])

            console.print(table)

            if result.total_rows > 50:
                primoroso.error(f"\n[dim]... ({result.total_rows - 50} more rows)[/dim]")

    elif output_format == "json":
        import json
        console.print(json.dumps(result.rows, indent=2))

    elif output_format == "csv":
        from ..fleet import AggregatedResult
        agg_result = AggregatedResult(rows=result.rows, total_rows=result.total_rows)
        csv_output = ResultAggregator().export_csv(agg_result)
        console.print(csv_output)


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
        primoroso.error("\n[bold green]✓ Correlation Analysis Complete[/bold green]\n")
        primoroso.info(f"IOC 1:[/cyan] {ioc1}")
        primoroso.info(f"IOC 2:[/cyan] {ioc2}\n")

        if "correlation" in result:
            corr = result["correlation"]

            if "relationship" in corr:
                console.print(f"[bold]Relationship:[/bold] {corr['relationship']}")

            if "common_infrastructure" in corr and corr["common_infrastructure"]:
                primoroso.error("\n[bold]Common Infrastructure:[/bold]")
                for infra in corr["common_infrastructure"]:
                    primoroso.error(f"• {infra}")

            if "correlation_score" in corr:
                score = corr["correlation_score"]
                score_color = (
                    "red" if score >= 70 else "yellow" if score >= 40 else "green"
                )
                console.print(
                    f"\n[cyan]Correlation Score:[/cyan] [{score_color}]{score}/100[/{score_color}]"
                )
        else:
            primoroso.warning("No correlation found between the IOCs.")
