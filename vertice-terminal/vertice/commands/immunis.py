"""
🛡️ IMMUNIS Command - AI Immune System
======================================

AI Immune System operations.

FASE 4 Commands (Basic Immune System):
    status - System status
    detect - Detect threat
    respond - Respond to threat
    patrol - Activate NK cell patrol
    memory - Query immune memory

FASE 9 Commands (Immune Enhancement):
    suppress-fp - Suppress false positive alerts (Regulatory T-Cells)
    tolerance - Get tolerance profile for entity
    consolidate - Trigger memory consolidation (STM → LTM)
    ltm - Query long-term immunological memory
    antibodies - Initialize antibody repertoire (V(D)J recombination)
    mature - Run affinity maturation (somatic hypermutation)

Examples:
    vcli immunis status
    vcli immunis detect threat_data.json
    vcli immunis respond threat_123 --type eliminate
    vcli immunis patrol network --targets "192.168.1.0/24"
    vcli immunis suppress-fp alerts.json --threshold 0.7
    vcli immunis tolerance 192.168.1.50 --type ip
    vcli immunis consolidate --manual --threshold 0.7
    vcli immunis ltm "ransomware campaigns" --limit 10
    vcli immunis antibodies samples.json --size 150
    vcli immunis mature feedback.json
"""

import typer
import asyncio
from rich.console import Console
from rich.markdown import Markdown
from typing_extensions import Annotated

from ..connectors.immunis import ImmunisConnector
from ..utils.output import output_json, print_error, print_success, PrimordialPanel
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="immunis",
    help="🛡️ AI Immune System operations",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def status(
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Get immune system status.

    Examples:
        vcli immunis status
    """
    require_auth()

    async def _execute():
        connector = ImmunisConnector()
        try:
            primoroso.info("[bold]Fetching immune system status...[/bold]")
            result = await connector.get_immune_status()

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(result.get("response", str(result))),
                        title="🛡️ Immunis Status",
                        console=console
                    )
                    panel.with_status("success").render()
                print_success("Status retrieved")
            else:
                print_error("Failed to get status")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def detect(
    threat_file: Annotated[str, typer.Argument(help="Path to threat data JSON")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Detect threat via immune system.

    Provide JSON file with:
    {
        "source": "...",
        "data": {...},
        "context": {...}
    }

    Examples:
        vcli immunis detect threat_data.json
    """
    require_auth()

    async def _execute():
        import json as json_lib

        # Load threat data
        try:
            with open(threat_file, 'r') as f:
                threat_data = json_lib.load(f)
        except Exception as e:
            print_error(f"Failed to load threat file: {e}")
            raise typer.Exit(1)

        connector = ImmunisConnector()
        try:
            primoroso.info(f"[bold]Detecting threat:[/bold] {threat_file}")
            result = await connector.detect_threat(threat_data)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title="Threat Detection",
                        console=console
                    )
                    panel.with_status("error").render()
                print_success("Detection complete")
            else:
                print_error("Detection failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def respond(
    threat_id: Annotated[str, typer.Argument(help="Threat ID")],
    response_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: contain, eliminate, quarantine, monitor")
    ] = "contain",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Respond to detected threat.

    Examples:
        vcli immunis respond threat_123 --type eliminate
        vcli immunis respond threat_456 --type quarantine
    """
    require_auth()

    async def _execute():
        connector = ImmunisConnector()
        try:
            primoroso.warning(f"[bold red]Responding to threat: {threat_id}[/bold red]")
            primoroso.info(f"[bold]Response type:[/bold] {response_type}")
            result = await connector.respond_to_threat(threat_id, response_type)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"Response: {threat_id}",
                        console=console
                    )
                    panel.with_status("success").render()
                print_success("Response complete")
            else:
                print_error("Response failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def patrol(
    scope: Annotated[
        str,
        typer.Argument(help="Patrol scope: network, filesystem, memory")
    ],
    targets: Annotated[
        str,
        typer.Option("--targets", "-t", help="Comma-separated targets")
    ],
    duration: Annotated[
        int,
        typer.Option("--duration", "-d", help="Duration in minutes")
    ] = 60,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Activate NK cell patrol.

    Examples:
        vcli immunis patrol network --targets "192.168.1.0/24" --duration 120
    """
    require_auth()

    async def _execute():
        connector = ImmunisConnector()
        try:
            primoroso.info("[bold]Activating NK patrol...[/bold]")

            patrol_zone = {
                "scope": scope,
                "targets": [t.strip() for t in targets.split(",")],
                "duration_minutes": duration
            }

            result = await connector.activate_nk_patrol(patrol_zone)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(result.get("response", str(result))),
                        title=f"NK Patrol: {scope}",
                        console=console
                    )
                    panel.with_status("info").render()
                print_success("Patrol activated")
            else:
                print_error("Patrol activation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def memory(
    antigen: Annotated[str, typer.Argument(help="Antigen signature to query")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Query immune memory (B-cells).

    Examples:
        vcli immunis memory malware_hash_abc123
    """
    require_auth()

    async def _execute():
        connector = ImmunisConnector()
        try:
            primoroso.info(f"[bold]Querying immune memory:[/bold] {antigen}")
            result = await connector.query_immune_memory(antigen)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(result.get("response", str(result))),
                        title=f"Immune Memory: {antigen}",
                        console=console
                    )
                    panel.with_status("warning").render()
                print_success("Memory query complete")
            else:
                print_error("No memory found")
        finally:
            await connector.close()

    asyncio.run(_execute())


# =============================================================================
# FASE 9: Immune Enhancement Commands
# =============================================================================

@app.command(name="suppress-fp")
def suppress_fp(
    alerts_file: Annotated[str, typer.Argument(help="Path to alerts JSON file")],
    threshold: Annotated[float, typer.Option("--threshold", "-t", help="Suppression threshold 0-1")] = 0.6,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Suppress false positive alerts using Regulatory T-Cells.

    Provide JSON file with:
    [
        {"id": "alert_001", "severity": "high", "entity": "192.168.1.10"},
        {"id": "alert_002", "severity": "medium", "entity": "john.doe"}
    ]

    Examples:
        vcli immunis suppress-fp alerts.json --threshold 0.7
        vcli immunis suppress-fp suspicious_alerts.json --threshold 0.8
    """
    require_auth()

    async def _execute():
        import json as json_lib

        try:
            with open(alerts_file, 'r') as f:
                alerts = json_lib.load(f)
        except Exception as e:
            print_error(f"Failed to load alerts file: {e}")
            raise typer.Exit(1)

        connector = ImmunisConnector()
        try:
            primoroso.info(f"[bold]Evaluating {len(alerts)} alerts...[/bold]")
            result = await connector.suppress_false_positives(alerts, threshold)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"FP Suppression (threshold: {threshold})",
                        console=console
                    )
                    panel.with_status("info").render()
                print_success("Evaluation complete")
            else:
                print_error("Evaluation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def tolerance(
    entity_id: Annotated[str, typer.Argument(help="Entity ID (IP, user, domain)")],
    entity_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: ip, user, domain, service")
    ] = "ip",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Get immune tolerance profile for entity.

    Examples:
        vcli immunis tolerance 192.168.1.50 --type ip
        vcli immunis tolerance john.doe --type user
        vcli immunis tolerance api.example.com --type domain
    """
    require_auth()

    async def _execute():
        connector = ImmunisConnector()
        try:
            primoroso.info(f"[bold]Fetching tolerance profile:[/bold] {entity_id} ({entity_type})")
            result = await connector.get_tolerance_profile(entity_id, entity_type)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"Tolerance Profile: {entity_id}",
                        console=console
                    )
                    panel.with_status("info").render()
                print_success("Profile retrieved")
            else:
                print_error("Profile not found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def consolidate(
    manual: Annotated[bool, typer.Option("--manual", "-m", help="Manual trigger (bypass circadian)")] = False,
    threshold: Annotated[float, typer.Option("--threshold", "-t", help="Importance threshold 0-1")] = 0.6,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Trigger memory consolidation cycle (STM → LTM).

    Examples:
        vcli immunis consolidate --manual --threshold 0.7
        vcli immunis consolidate --threshold 0.8
    """
    require_auth()

    async def _execute():
        connector = ImmunisConnector()
        try:
            primoroso.info("[bold]Triggering memory consolidation...[/bold]")
            if manual:
                primoroso.warning("[yellow]Manual trigger (bypassing circadian rhythm)[/yellow]")

            result = await connector.consolidate_memory(manual, threshold)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title="Memory Consolidation (STM → LTM)",
                        console=console
                    )
                    panel.with_status("info").render()
                print_success("Consolidation complete")
            else:
                print_error("Consolidation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def ltm(
    query: Annotated[str, typer.Argument(help="Search query")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max results")] = 10,
    min_importance: Annotated[float, typer.Option("--min-importance", "-i", help="Min importance 0-1")] = 0.5,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Query long-term immunological memory.

    Examples:
        vcli immunis ltm "ransomware campaigns targeting healthcare" --limit 5
        vcli immunis ltm "APT group tactics" --min-importance 0.8
    """
    require_auth()

    async def _execute():
        connector = ImmunisConnector()
        try:
            primoroso.info(f"[bold]Querying LTM:[/bold] {query}")
            result = await connector.query_long_term_memory(query, limit, min_importance)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"Long-Term Memory: {query[:50]}...",
                        console=console
                    )
                    panel.with_status("warning").render()
                print_success("LTM query complete")
            else:
                print_error("No memories found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def antibodies(
    samples_file: Annotated[str, typer.Argument(help="Path to threat samples JSON")],
    size: Annotated[int, typer.Option("--size", "-s", help="Repertoire size")] = 100,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Initialize antibody repertoire from threat samples (V(D)J recombination).

    Provide JSON file with:
    [
        {"type": "malware", "signature": "...", "features": {...}},
        {"type": "phishing", "url": "...", "content": "..."}
    ]

    Examples:
        vcli immunis antibodies threat_samples.json --size 150
        vcli immunis antibodies malware_corpus.json --size 200
    """
    require_auth()

    async def _execute():
        import json as json_lib

        try:
            with open(samples_file, 'r') as f:
                samples = json_lib.load(f)
        except Exception as e:
            print_error(f"Failed to load samples file: {e}")
            raise typer.Exit(1)

        connector = ImmunisConnector()
        try:
            primoroso.info(f"[bold]Diversifying antibodies:[/bold] {len(samples)} samples → {size} antibodies")
            result = await connector.diversify_antibodies(samples, size)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title="Antibody Diversification (V(D)J)",
                        console=console
                    )
                    panel.with_status("success").render()
                print_success("Antibody repertoire initialized")
            else:
                print_error("Diversification failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def mature(
    feedback_file: Annotated[str, typer.Argument(help="Path to feedback JSON")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Run affinity maturation cycle (somatic hypermutation).

    Provide JSON file with:
    {
        "antibody_001": {"sample_a": true, "sample_b": false},
        "antibody_002": {"sample_a": true, "sample_b": true}
    }

    Examples:
        vcli immunis mature antibody_feedback.json
    """
    require_auth()

    async def _execute():
        import json as json_lib

        try:
            with open(feedback_file, 'r') as f:
                feedback_data = json_lib.load(f)
        except Exception as e:
            print_error(f"Failed to load feedback file: {e}")
            raise typer.Exit(1)

        connector = ImmunisConnector()
        try:
            primoroso.info(f"[bold]Running affinity maturation:[/bold] {len(feedback_data)} antibodies")
            result = await connector.run_affinity_maturation(feedback_data)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title="Affinity Maturation (Somatic Hypermutation)",
                        console=console
                    )
                    panel.with_status("error").render()
                print_success("Maturation complete")
            else:
                print_error("Maturation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


if __name__ == "__main__":
    app()
