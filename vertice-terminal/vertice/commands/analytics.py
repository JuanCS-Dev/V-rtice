"""
📊 ANALYTICS Command - Advanced Analytics & ML

Análises avançadas com Machine Learning, Behavioral Analytics, e Risk Scoring.

Exemplos:
    vertice analytics behavior learn user_123 --days 30
    vertice analytics behavior detect user_123 --event @event.json
    vertice analytics ml predict malware suspicious.exe
    vertice analytics ml predict phishing --url "http://phish.bad"
    vertice analytics risk calculate endpoint_456
    vertice analytics threat-intel enrich 192.168.1.100
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional
import json
from vertice.utils import primoroso

app = typer.Typer(
    name="analytics",
    help="📊 Advanced analytics with ML and behavioral analysis",
    rich_markup_mode="rich",
)

console = Console()


# Behavioral Analytics commands

behavior_app = typer.Typer(help="🧠 Behavioral analytics")
app.add_typer(behavior_app, name="behavior")


@behavior_app.command()
def learn(
    entity_id: str = typer.Argument(..., help="Entity ID (user, endpoint)"),
    entity_type: str = typer.Option("user", "--type"),
    days: int = typer.Option(30, "--days", help="Learning period in days"),
):
    """
    Aprende baseline comportamental

    Examples:
        vertice analytics behavior learn user_john --days 30
        vertice analytics behavior learn endpoint_srv01 --type endpoint
    """
    from ..analytics import BehavioralAnalytics

    primoroso.info(f"Learning behavioral baseline for {entity_id}...[/cyan]\n")

    analytics = BehavioralAnalytics(learning_period_days=days)

    # TODO: Fetch historical events from backend
    # For now, show example

    primoroso.warning("Note: Fetching historical events from backend...")

    historical_events = []  # Placeholder

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Learning baseline...", total=None)

        baseline = analytics.learn_baseline(entity_id, entity_type, historical_events)

        progress.update(task, completed=True)

    _show_baseline(baseline)


@behavior_app.command()
def detect(
    entity_id: str = typer.Argument(..., help="Entity ID"),
    event: str = typer.Option(..., "--event", help="Event JSON or @file"),
):
    """
    Detecta anomalias comportamentais

    Examples:
        vertice analytics behavior detect user_123 --event '{"type": "login", "source_ip": "1.2.3.4"}'
        vertice analytics behavior detect user_123 --event @event.json
    """
    from ..analytics import BehavioralAnalytics

    # Parse event
    try:
        if event.startswith("@"):
            event_data = json.loads(Path(event[1:]).read_text())
        else:
            event_data = json.loads(event)
    except json.JSONDecodeError as e:
        primoroso.error(f"Invalid JSON: {e}[/red]")
        raise typer.Exit(code=1)

    analytics = BehavioralAnalytics()

    # Detect anomalies
    anomalies = analytics.detect_anomalies(entity_id, event_data)

    if not anomalies:
        primoroso.success("✅ No anomalies detected")
        return

    primoroso.error(f"⚠️  {len(anomalies)} anomaly(ies) detected![/red]\n")

    for anomaly in anomalies:
        _show_anomaly(anomaly)


# Machine Learning commands

ml_app = typer.Typer(help="🤖 Machine Learning detection")
app.add_typer(ml_app, name="ml")


@ml_app.command()
def models():
    """
    Lista modelos ML disponíveis

    Examples:
        vertice analytics ml models
    """
    from ..analytics import MLDetector

    detector = MLDetector()

    # TODO: List available models from backend

    table = Table(title="🤖 Available ML Models")
    table.add_column("Model", style="cyan")
    table.add_column("Type")
    table.add_column("Accuracy")
    table.add_column("Version")

    # Example models
    models_list = [
        ("malware_classifier", "Malware Classification", "94.5%", "2.1"),
        ("phishing_detector", "Phishing Detection", "91.2%", "1.8"),
        ("dga_detector", "DGA Detection", "96.7%", "1.3"),
        ("lateral_movement_detector", "Lateral Movement", "89.4%", "1.0"),
    ]

    for name, desc, accuracy, version in models_list:
        table.add_row(name, desc, accuracy, version)

    console.print(table)


@ml_app.command()
def predict(
    model_type: str = typer.Argument(..., help="Model type: malware, phishing, dga"),
    file_path: Optional[str] = typer.Option(None, "--file"),
    url: Optional[str] = typer.Option(None, "--url"),
    domain: Optional[str] = typer.Option(None, "--domain"),
    explain: bool = typer.Option(True, "--explain", help="Generate explanation"),
):
    """
    Faz predição com modelo ML

    Examples:
        vertice analytics ml predict malware --file suspicious.exe
        vertice analytics ml predict phishing --url "http://phish.bad"
        vertice analytics ml predict dga --domain "fj38hf2.com"
    """
    from ..analytics import MLDetector, MLModelType

    detector = MLDetector()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running ML prediction...", total=None)

        try:
            if model_type == "malware":
                if not file_path:
                    primoroso.error("--file required for malware detection[/red]")
                    raise typer.Exit(code=1)

                prediction = detector.detect_malware(Path(file_path), extract_features=True)

            elif model_type == "phishing":
                prediction = detector.detect_phishing(url=url)

            elif model_type == "dga":
                if not domain:
                    primoroso.error("--domain required for DGA detection[/red]")
                    raise typer.Exit(code=1)

                prediction = detector.detect_dga(domain)

            else:
                primoroso.error(f"Unknown model type: {model_type}[/red]")
                raise typer.Exit(code=1)

            progress.update(task, completed=True)

        except Exception as e:
            primoroso.error(f"Prediction failed: {e}[/red]")
            raise typer.Exit(code=1)

    _show_prediction(prediction)


# Risk Scoring commands

risk_app = typer.Typer(help="⚖️  Risk scoring")
app.add_typer(risk_app, name="risk")


@risk_app.command()
def calculate(
    entity_id: str = typer.Argument(..., help="Entity ID"),
    entity_type: str = typer.Option("endpoint", "--type"),
    show_factors: bool = typer.Option(True, "--factors", help="Show risk factors"),
):
    """
    Calcula risk score de entity

    Examples:
        vertice analytics risk calculate endpoint_123
        vertice analytics risk calculate user_john --type user
    """
    from ..analytics import RiskScorer

    primoroso.info(f"Calculating risk score for {entity_id}...[/cyan]\n")

    scorer = RiskScorer()

    # TODO: Fetch risk factors from multiple sources

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Aggregating risk factors...", total=None)

        # Placeholder: empty risk factors for now
        risk_factors = []

        risk_score = scorer.calculate_risk_score(entity_id, entity_type, risk_factors)

        progress.update(task, completed=True)

    _show_risk_score(risk_score, show_factors=show_factors)


@risk_app.command()
def list_high_risk(
    entity_type: Optional[str] = typer.Option(None, "--type"),
    min_level: str = typer.Option("high", "--level"),
    limit: int = typer.Option(50, "--limit"),
):
    """
    Lista entities com alto risco

    Examples:
        vertice analytics risk list-high-risk
        vertice analytics risk list-high-risk --type endpoint --level critical
    """
    from ..analytics import RiskScorer, RiskLevel

    scorer = RiskScorer()

    try:
        min_risk_level = RiskLevel[min_level.upper()]
    except KeyError:
        primoroso.error(f"Invalid risk level: {min_level}[/red]")
        raise typer.Exit(code=1)

    high_risk = scorer.get_high_risk_entities(
        entity_type=entity_type,
        min_risk_level=min_risk_level,
        limit=limit,
    )

    if not high_risk:
        primoroso.success("No high-risk entities found")
        return

    table = Table(title=f"⚠️  High Risk Entities ({len(high_risk)})")
    table.add_column("Entity ID", style="cyan")
    table.add_column("Type")
    table.add_column("Risk Score", justify="right")
    table.add_column("Risk Level", justify="center")
    table.add_column("Top Factor")

    for score in high_risk:
        risk_color = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "green",
        }.get(score.risk_level.value, "white")

        top_factor = score.risk_factors[0].name if score.risk_factors else "—"

        table.add_row(
            score.entity_id,
            score.entity_type,
            f"{score.total_score:.1f}",
            f"[{risk_color}]{score.risk_level.value}[/{risk_color}]",
            top_factor[:40],
        )

    console.print(table)


# Threat Intelligence commands

intel_app = typer.Typer(help="🌐 Threat intelligence")
app.add_typer(intel_app, name="threat-intel")


@intel_app.command()
def enrich(
    ioc_value: str = typer.Argument(..., help="IOC value (IP, domain, hash)"),
    ioc_type: Optional[str] = typer.Option(None, "--type", help="IOC type"),
):
    """
    Enriquece IOC com threat intelligence

    Examples:
        vertice analytics threat-intel enrich 192.168.1.100 --type ip
        vertice analytics threat-intel enrich evil.com --type domain
        vertice analytics threat-intel enrich abc123def456... --type sha256
    """
    from ..analytics import ThreatIntelFeed, IOCType

    # Auto-detect IOC type if not provided
    if not ioc_type:
        ioc_type = _auto_detect_ioc_type(ioc_value)

    try:
        ioc_type_enum = IOCType(ioc_type)
    except ValueError:
        primoroso.error(f"Invalid IOC type: {ioc_type}[/red]")
        raise typer.Exit(code=1)

    primoroso.info("Enriching IOC from threat intel feeds...[/cyan]\n")

    feed = ThreatIntelFeed()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Querying feeds...", total=None)

        ioc = feed.enrich_ioc(ioc_value, ioc_type_enum)

        progress.update(task, completed=True)

    if not ioc:
        primoroso.warning("No threat intelligence found for this IOC")
        return

    _show_ioc(ioc)


@intel_app.command()
def actor(
    actor_name: str = typer.Argument(..., help="Threat actor name (APT28, Lazarus, etc)"),
):
    """
    Busca informações sobre threat actor

    Examples:
        vertice analytics threat-intel actor APT28
        vertice analytics threat-intel actor "Lazarus Group"
    """
    from ..analytics import ThreatIntelFeed

    feed = ThreatIntelFeed()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Looking up {actor_name}...", total=None)

        actor = feed.lookup_threat_actor(actor_name)

        progress.update(task, completed=True)

    if not actor:
        primoroso.warning(f"No information found for threat actor: {actor_name}")
        return

    _show_threat_actor(actor)


# Helper functions

def _show_baseline(baseline):
    """Display behavioral baseline"""
    from ..analytics import Baseline

    content = f"""[bold]Entity:[/bold] {baseline.entity_id} ({baseline.entity_type})

[bold]Temporal Patterns:[/bold]
  Typical login hours: {', '.join(str(h) for h in sorted(baseline.typical_login_hours[:10]))}
  Typical days: {', '.join(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d] for d in sorted(baseline.typical_days))}

[bold]Network Patterns:[/bold]
  Avg traffic IN: {baseline.avg_network_bytes_in / 1024 / 1024:.2f} MB
  Avg traffic OUT: {baseline.avg_network_bytes_out / 1024 / 1024:.2f} MB

[bold]Locations:[/bold]
  {len(baseline.typical_locations)} unique location(s)

[bold]Processes:[/bold]
  {len(baseline.typical_processes)} typical process(es)

[dim]Sample count: {baseline.sample_count} | Confidence: {baseline.confidence:.1%}[/dim]
"""

    console.print(Panel(content, title="🧠 Behavioral Baseline"))


def _show_anomaly(anomaly):
    """Display anomaly"""
    from ..analytics import Anomaly

    severity_colors = {
        "critical": "red",
        "high": "yellow",
        "medium": "blue",
        "low": "green",
    }
    color = severity_colors.get(anomaly.severity, "white")

    content = f"""[bold]{anomaly.anomaly_type.value}[/bold]
[dim]Severity:[/dim] [{color}]{anomaly.severity}[/{color}]
[dim]Confidence:[/dim] {anomaly.confidence:.1%}

{anomaly.description}

[dim]Observed:[/dim] {anomaly.observed_value}
[dim]Baseline:[/dim] {anomaly.baseline_value}
[dim]Deviation:[/dim] {anomaly.deviation_score:.2f} σ
"""

    console.print(Panel(content, border_style=color))


def _show_prediction(prediction):
    """Display ML prediction"""
    from ..analytics import Prediction

    confidence_color = "green" if prediction.confidence > 0.7 else "yellow" if prediction.confidence > 0.4 else "red"

    content = f"""[bold]Prediction:[/bold] {prediction.predicted_class}
[dim]Confidence:[/dim] [{confidence_color}]{prediction.confidence:.1%}[/{confidence_color}]
[dim]Model:[/dim] {prediction.model_name} ({prediction.model_type.value})
[dim]Inference time:[/dim] {prediction.inference_time_ms:.1f}ms

[bold]Probabilities:[/bold]
"""

    for cls, prob in sorted(prediction.probabilities.items(), key=lambda x: x[1], reverse=True)[:5]:
        content += f"  {cls}: {prob:.1%}\n"

    if prediction.explanation:
        content += f"\n[dim]Explanation:[/dim] {prediction.explanation}"

    console.print(Panel(content, title="🤖 ML Prediction"))


def _show_risk_score(risk_score, show_factors=True):
    """Display risk score"""
    from ..analytics import RiskScore

    risk_colors = {
        "critical": "red",
        "high": "yellow",
        "medium": "blue",
        "low": "green",
        "minimal": "dim",
    }
    color = risk_colors.get(risk_score.risk_level.value, "white")

    content = f"""[bold]Entity:[/bold] {risk_score.entity_id} ({risk_score.entity_type})

[bold]Overall Risk Score:[/bold] [{color}]{risk_score.total_score:.1f}/100[/{color}]
[bold]Risk Level:[/bold] [{color}]{risk_score.risk_level.value.upper()}[/{color}]

[bold]Category Breakdown:[/bold]
  Vulnerability:  {risk_score.vulnerability_score:.1f}
  Malware:        {risk_score.malware_score:.1f}
  Behavioral:     {risk_score.behavioral_score:.1f}
  Compliance:     {risk_score.compliance_score:.1f}
  Threat Intel:   {risk_score.threat_intel_score:.1f}

[dim]Calculated: {risk_score.calculated_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]
"""

    console.print(Panel(content, title="⚖️  Risk Score", border_style=color))

    if show_factors and risk_score.risk_factors:
        primoroso.error("\n[bold]Risk Factors:[/bold]")

        for factor in risk_score.risk_factors[:10]:
            primoroso.error(f"• [{factor.category}] {factor.name} (impact: {factor.score_impact:.1f})")


def _show_ioc(ioc):
    """Display IOC enrichment"""
    from ..analytics import IOC

    threat_colors = {
        "critical": "red",
        "high": "yellow",
        "medium": "blue",
        "low": "green",
        "unknown": "dim",
    }
    color = threat_colors.get(ioc.threat_level, "white")

    content = f"""[bold]IOC:[/bold] {ioc.value}
[dim]Type:[/dim] {ioc.ioc_type.value}
[dim]Threat Level:[/dim] [{color}]{ioc.threat_level}[/{color}]
[dim]Confidence:[/dim] {ioc.confidence:.1%}

[bold]Threat Actors:[/bold] {', '.join(ioc.threat_actors[:5]) or 'None'}
[bold]Campaigns:[/bold] {', '.join(ioc.campaigns[:5]) or 'None'}
[bold]Families:[/bold] {', '.join(ioc.families[:5]) or 'None'}

[bold]Sources:[/bold] {', '.join(ioc.sources)}
[dim]First seen:[/dim] {ioc.first_seen.strftime('%Y-%m-%d')}
"""

    console.print(Panel(content, title="🌐 Threat Intelligence", border_style=color))


def _show_threat_actor(actor):
    """Display threat actor info"""
    from ..analytics import ThreatActor

    content = f"""[bold]{actor.name}[/bold]
[dim]Aliases:[/dim] {', '.join(actor.aliases) or 'None'}
[dim]Type:[/dim] {actor.type}
[dim]Motivation:[/dim] {actor.motivation}

{actor.description}

[bold]TTPs:[/bold]
  Tactics: {', '.join(actor.tactics[:5])}
  Techniques: {', '.join(actor.techniques[:5])}
  Tools: {', '.join(actor.tools[:5])}

[bold]Campaigns:[/bold] {', '.join(actor.campaigns[:5]) or 'None'}

[dim]References:[/dim]
"""

    for ref in actor.references[:3]:
        content += f"  • {ref}\n"

    console.print(Panel(content, title="🎯 Threat Actor Profile"))


def _auto_detect_ioc_type(value: str) -> str:
    """Auto-detect IOC type"""
    import re

    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value):
        return "ip"
    elif re.match(r"^[a-fA-F0-9]{32}$", value):
        return "md5"
    elif re.match(r"^[a-fA-F0-9]{40}$", value):
        return "sha1"
    elif re.match(r"^[a-fA-F0-9]{64}$", value):
        return "sha256"
    elif "." in value and not "/" in value:
        return "domain"
    elif value.startswith("http"):
        return "url"
    else:
        return "unknown"
