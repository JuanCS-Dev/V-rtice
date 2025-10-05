"""
🧠 COGNITIVE Command - ASA Cognitive Services
=============================================

ASA Cognitive and Sensory Cortex operations.

FASE 1 Commands (Sensory Systems):
    image - Visual cortex image analysis
    audio - Auditory cortex audio analysis
    decide - Prefrontal cortex decision-making

FASE 8 Commands (Enhanced Cognition):
    narrative - Narrative analysis (social engineering, propaganda, bots)
    predict - Predictive threat hunting (time-series, Bayesian)
    hunt - Proactive threat hunting recommendations
    investigate-ai - Autonomous incident investigation
    correlate - Campaign correlation (incident clustering)

Examples:
    vcli cognitive image screenshot.png --type threats
    vcli cognitive audio recording.wav
    vcli cognitive decide "security_incident.json"
    vcli cognitive narrative "tweet thread" --detect-bots
    vcli cognitive predict --time-horizon 48
    vcli cognitive hunt --assets networks.json
    vcli cognitive investigate-ai INC-2024-001 --playbook apt
    vcli cognitive correlate INC-001 INC-002 INC-005
"""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing_extensions import Annotated

from ..connectors.cognitive import CognitiveConnector
from ..utils.output import output_json, print_error, print_success
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="cognitive",
    help="🧠 ASA Cognitive and Sensory services",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def image(
    image_path: Annotated[str, typer.Argument(help="Path to image file")],
    analysis_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: full, objects, faces, ocr, threats")
    ] = "full",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Analyze image via Visual Cortex.

    Examples:
        vcli cognitive image screenshot.png --type threats
        vcli cognitive image photo.jpg --type faces
    """
    require_auth()

    async def _execute():
        connector = CognitiveConnector()
        try:
            primoroso.info(f"[bold]Analyzing image:[/bold] {image_path}")
            result = await connector.analyze_image(image_path, analysis_type)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[cyan]Visual Analysis: {image_path}[/cyan]",
                        border_style="cyan"
                    ))
                print_success("Analysis complete")
            else:
                print_error("Analysis failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def audio(
    audio_path: Annotated[str, typer.Argument(help="Path to audio file")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Analyze audio via Auditory Cortex.

    Examples:
        vcli cognitive audio recording.wav
        vcli cognitive audio call.mp3
    """
    require_auth()

    async def _execute():
        connector = CognitiveConnector()
        try:
            primoroso.info(f"[bold]Analyzing audio:[/bold] {audio_path}")
            result = await connector.analyze_audio(audio_path)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[cyan]Audio Analysis: {audio_path}[/cyan]",
                        border_style="cyan"
                    ))
                print_success("Analysis complete")
            else:
                print_error("Analysis failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def decide(
    decision_file: Annotated[str, typer.Argument(help="Path to decision request JSON")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Decision-making via Prefrontal Cortex.

    Provide a JSON file with:
    {
        "situation": "...",
        "options": [{...}],
        "constraints": {...},
        "objectives": [...]
    }

    Examples:
        vcli cognitive decide incident_response.json
    """
    require_auth()

    async def _execute():
        import json as json_lib

        # Load decision request
        try:
            with open(decision_file, 'r') as f:
                decision_request = json_lib.load(f)
        except Exception as e:
            print_error(f"Failed to load decision file: {e}")
            raise typer.Exit(1)

        connector = CognitiveConnector()
        try:
            primoroso.info(f"[bold]Processing decision:[/bold] {decision_file}")
            result = await connector.prefrontal_decision(decision_request)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title="[green]Decision Recommendation[/green]",
                        border_style="green"
                    ))
                print_success("Decision complete")
            else:
                print_error("Decision failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


# =============================================================================
# FASE 8: Enhanced Cognition Commands
# =============================================================================

@app.command()
def narrative(
    text: Annotated[str, typer.Argument(help="Text or social media content to analyze")],
    analysis_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: comprehensive, bots_only, propaganda_only, meme_tracking")
    ] = "comprehensive",
    detect_bots: Annotated[bool, typer.Option("--detect-bots")] = True,
    track_memes: Annotated[bool, typer.Option("--track-memes")] = True,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Analyze narrative for social engineering, propaganda, and bot networks.

    Examples:
        vcli cognitive narrative "Check this viral tweet thread..." --detect-bots
        vcli cognitive narrative discourse.txt --type propaganda_only
    """
    require_auth()

    async def _execute():
        connector = CognitiveConnector()
        try:
            primoroso.info(f"[bold]Analyzing narrative:[/bold] {analysis_type}")
            result = await connector.analyze_narrative(text, analysis_type, detect_bots, track_memes)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[magenta]Narrative Analysis: {analysis_type}[/magenta]",
                        border_style="magenta"
                    ))
                print_success("Narrative analysis complete")
            else:
                print_error("Analysis failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def predict(
    context_file: Annotated[str, typer.Argument(help="Path to context JSON file")],
    time_horizon: Annotated[int, typer.Option("--time-horizon", "-t", help="Hours to predict ahead")] = 24,
    min_confidence: Annotated[float, typer.Option("--min-confidence", "-c", help="Min confidence 0-1")] = 0.6,
    include_vuln: Annotated[bool, typer.Option("--include-vuln")] = True,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Predict future threats using time-series and Bayesian inference.

    Provide context JSON with:
    {
        "recent_alerts": [...],
        "historical_events": [...],
        "vuln_intel": [...]
    }

    Examples:
        vcli cognitive predict context.json --time-horizon 48
        vcli cognitive predict threat_context.json --min-confidence 0.8
    """
    require_auth()

    async def _execute():
        import json as json_lib

        try:
            with open(context_file, 'r') as f:
                context = json_lib.load(f)
        except Exception as e:
            print_error(f"Failed to load context file: {e}")
            raise typer.Exit(1)

        connector = CognitiveConnector()
        try:
            primoroso.info(f"[bold]Predicting threats:[/bold] {time_horizon}h horizon")
            result = await connector.predict_threats(
                context, time_horizon, min_confidence, include_vuln
            )

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[yellow]Threat Predictions ({time_horizon}h)[/yellow]",
                        border_style="yellow"
                    ))
                print_success("Prediction complete")
            else:
                print_error("Prediction failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def hunt(
    assets_file: Annotated[str, typer.Option("--assets", "-a", help="Assets inventory JSON")] = None,
    intel_file: Annotated[str, typer.Option("--intel", "-i", help="Threat intel JSON")] = None,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Generate proactive threat hunting recommendations.

    Examples:
        vcli cognitive hunt --assets assets.json --intel threat_intel.json
        vcli cognitive hunt --assets networks.json
    """
    require_auth()

    async def _execute():
        import json as json_lib

        asset_inventory = None
        threat_intel = None

        if assets_file:
            try:
                with open(assets_file, 'r') as f:
                    asset_inventory = json_lib.load(f)
            except Exception as e:
                print_error(f"Failed to load assets file: {e}")
                raise typer.Exit(1)

        if intel_file:
            try:
                with open(intel_file, 'r') as f:
                    threat_intel = json_lib.load(f)
            except Exception as e:
                print_error(f"Failed to load intel file: {e}")
                raise typer.Exit(1)

        connector = CognitiveConnector()
        try:
            primoroso.info("[bold]Generating hunting recommendations...[/bold]")
            result = await connector.hunt_proactively(asset_inventory, threat_intel)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title="[red]Threat Hunting Recommendations[/red]",
                        border_style="red"
                    ))
                print_success("Hunt recommendations generated")
            else:
                print_error("Hunt generation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command(name="investigate-ai")
def investigate_ai(
    incident_id: Annotated[str, typer.Argument(help="Incident ID to investigate")],
    playbook: Annotated[
        str,
        typer.Option("--playbook", "-p", help="Playbook: standard, apt, ransomware, insider")
    ] = "standard",
    actor_profiling: Annotated[bool, typer.Option("--actor-profiling")] = True,
    campaign_correlation: Annotated[bool, typer.Option("--campaign-correlation")] = True,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Launch autonomous investigation for incident.

    Examples:
        vcli cognitive investigate-ai INC-2024-001 --playbook apt
        vcli cognitive investigate-ai INC-2024-002 --playbook ransomware
    """
    require_auth()

    async def _execute():
        connector = CognitiveConnector()
        try:
            primoroso.info(f"[bold]Investigating:[/bold] {incident_id} ({playbook} playbook)")
            result = await connector.investigate_incident(
                incident_id, playbook, actor_profiling, campaign_correlation
            )

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[bright_red]Investigation: {incident_id}[/bright_red]",
                        border_style="bright_red"
                    ))
                print_success("Investigation complete")
            else:
                print_error("Investigation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def correlate(
    incidents: Annotated[list[str], typer.Argument(help="Incident IDs to correlate")],
    time_window: Annotated[int, typer.Option("--time-window", "-t", help="Days for correlation")] = 30,
    threshold: Annotated[float, typer.Option("--threshold", "-c", help="Correlation threshold 0-1")] = 0.6,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Correlate incidents into attack campaigns.

    Examples:
        vcli cognitive correlate INC-001 INC-002 INC-005 --time-window 45
        vcli cognitive correlate INC-100 INC-101 INC-102 --threshold 0.8
    """
    require_auth()

    async def _execute():
        connector = CognitiveConnector()
        try:
            primoroso.info(f"[bold]Correlating {len(incidents)} incidents...[/bold]")
            result = await connector.correlate_campaigns(incidents, time_window, threshold)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title="[orange1]Campaign Correlation[/orange1]",
                        border_style="orange1"
                    ))
                print_success("Correlation complete")
            else:
                print_error("Correlation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


if __name__ == "__main__":
    app()
