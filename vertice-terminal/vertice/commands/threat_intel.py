"""
🌐 Threat Intel Command - Threat intelligence platform

Commands:
  vcli threat-intel feeds list              - List threat feeds
  vcli threat-intel feeds update            - Update feeds
  vcli threat-intel ioc enrich              - Enrich IOC
  vcli threat-intel ioc search              - Search IOC
  vcli threat-intel actors list             - List threat actors
  vcli threat-intel actors profile          - Show actor profile
  vcli threat-intel ttp list                - List MITRE techniques
  vcli threat-intel ttp search              - Search techniques
  vcli threat-intel stats                   - Show statistics

Examples:
  vcli threat-intel feeds update --all
  vcli threat-intel ioc enrich --value 8.8.8.8 --type ip_address
  vcli threat-intel actors profile APT28
  vcli threat-intel ttp search credential
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from typing import Optional
import logging
from vertice.utils import primoroso

app = typer.Typer(
    name="threat-intel",
    help="🌐 Threat intelligence platform",
)

console = Console()
logger = logging.getLogger(__name__)

# Lazy imports
_feed_aggregator = None
_ioc_enricher = None
_actor_profiler = None
_ttp_mapper = None


def get_feed_aggregator():
    """Lazy load feed aggregator"""
    global _feed_aggregator
    if _feed_aggregator is None:
        from vertice.threat_intel import ThreatFeedAggregator
        _feed_aggregator = ThreatFeedAggregator()
    return _feed_aggregator


def get_ioc_enricher():
    """Lazy load IOC enricher"""
    global _ioc_enricher
    if _ioc_enricher is None:
        from vertice.threat_intel import IOCEnricher
        _ioc_enricher = IOCEnricher()
    return _ioc_enricher


def get_actor_profiler():
    """Lazy load actor profiler"""
    global _actor_profiler
    if _actor_profiler is None:
        from vertice.threat_intel import ThreatActorProfiler
        _actor_profiler = ThreatActorProfiler()
    return _actor_profiler


def get_ttp_mapper():
    """Lazy load TTP mapper"""
    global _ttp_mapper
    if _ttp_mapper is None:
        from vertice.threat_intel import TTPMapper
        _ttp_mapper = TTPMapper()
    return _ttp_mapper


# ==================== Feeds Commands ====================

feeds_app = typer.Typer(help="📡 Threat feed management")
app.add_typer(feeds_app, name="feeds")


@feeds_app.command("list")
def feeds_list(
    source: Optional[str] = typer.Option(None, "--source", help="Filter by source"),
    enabled_only: bool = typer.Option(False, "--enabled", help="Only enabled feeds"),
):
    """
    📋 List threat feeds

    Example:
        vcli threat-intel feeds list --enabled
    """
    from vertice.threat_intel import FeedSource

    aggregator = get_feed_aggregator()

    # Parse source filter
    source_enum = None
    if source:
        try:
            source_enum = FeedSource(source)
        except ValueError:
            primoroso.error(f"Invalid source: {source}[/red]")
            raise typer.Exit(1)

    feeds = aggregator.list_feeds(
        source=source_enum,
        enabled_only=enabled_only,
    )

    # Display
    table = Table(title=f"Threat Feeds ({len(feeds)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Source", style="blue")
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Indicators", justify="right", style="green")

    for feed in feeds:
        status_symbol = "✅" if feed.status.value == "active" else "❌"

        table.add_row(
            feed.id,
            feed.name[:40] + "..." if len(feed.name) > 40 else feed.name,
            feed.source.value,
            feed.feed_type.value,
            f"{status_symbol} {feed.status.value}",
            str(feed.indicators_count),
        )

    console.print(table)


@feeds_app.command("update")
def feeds_update(
    feed_id: Optional[str] = typer.Option(None, "--feed", help="Specific feed ID"),
    all_feeds: bool = typer.Option(False, "--all", help="Update all feeds"),
):
    """
    🔄 Update threat feeds

    Example:
        vcli threat-intel feeds update --all
    """
    aggregator = get_feed_aggregator()

    if all_feeds:
        primoroso.info("Updating all threat feeds...[/cyan]\n")

        results = aggregator.update_all_feeds()

        # Display results
        table = Table(title="Update Results", box=box.ROUNDED)
        table.add_column("Feed", style="cyan")
        table.add_column("Indicators Fetched", justify="right", style="green")

        for feed_id, count in results.items():
            feed = aggregator.get_feed(feed_id)
            if feed:
                table.add_row(feed.name, str(count))

        console.print(table)

        total = sum(results.values())
        primoroso.error(f"\n[green]✅ Updated {len(results)} feeds, fetched {total} indicators[/green]")

    elif feed_id:
        primoroso.info(f"Updating feed: {feed_id}...[/cyan]\n")

        count = aggregator.update_feed(feed_id)

        if count > 0:
            primoroso.success(f"✅ Fetched {count} indicators")
        else:
            primoroso.warning("⚠️  No indicators fetched")

    else:
        primoroso.error("Specify --feed <id> or --all[/red]")
        raise typer.Exit(1)


# ==================== IOC Commands ====================

ioc_app = typer.Typer(help="🔍 IOC enrichment and search")
app.add_typer(ioc_app, name="ioc")


@ioc_app.command("enrich")
def ioc_enrich(
    value: str = typer.Option(..., "--value", help="IOC value"),
    ioc_type: str = typer.Option(..., "--type", help="IOC type (ip_address, domain, url, file_hash_sha256)"),
):
    """
    🔍 Enrich IOC with threat intelligence

    Example:
        vcli threat-intel ioc enrich --value 8.8.8.8 --type ip_address
    """
    from vertice.threat_intel import IOCType

    try:
        ioc_type_enum = IOCType(ioc_type)
    except ValueError:
        primoroso.error(f"Invalid IOC type: {ioc_type}[/red]")
        primoroso.warning("Valid types: ip_address, domain, url, file_hash_md5, file_hash_sha1, file_hash_sha256")
        raise typer.Exit(1)

    enricher = get_ioc_enricher()

    primoroso.info(f"Enriching IOC: {value}...[/cyan]\n")

    result = enricher.enrich(value, ioc_type_enum)

    if result.enriched:
        # Threat level color
        level_colors = {
            "benign": "green",
            "suspicious": "yellow",
            "malicious": "red",
            "critical": "bright_red",
            "unknown": "white",
        }

        level_color = level_colors.get(result.threat_level.value, "white")

        console.print(Panel(
            f"[{level_color}]Threat Level: {result.threat_level.value.upper()}[/{level_color}]\n"
            f"Confidence: {result.confidence}%\n"
            f"Sources: {', '.join(result.enrichment_sources)}",
            title="Enrichment Result",
            border_style=level_color,
        ))

        # Verdicts
        if result.verdicts:
            primoroso.error("\n[bold]Verdicts:[/bold]")
            for source, verdict in result.verdicts.items():
                primoroso.info(f"{source}:[/cyan] {verdict}")

        # Context
        if result.context:
            console.print(f"\n[dim]Enriched at: {result.enriched_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

    else:
        primoroso.warning("⚠️  No enrichment data available")


@ioc_app.command("search")
def ioc_search(
    indicator: str = typer.Argument(..., help="Indicator value to search"),
):
    """
    🔎 Search for IOC in threat feeds

    Example:
        vcli threat-intel ioc search 192.168.1.1
    """
    aggregator = get_feed_aggregator()

    result = aggregator.search_indicator(indicator)

    if result:
        console.print(Panel(
            f"[bold]Indicator:[/bold] {result.indicator}\n"
            f"[bold]Type:[/bold] {result.indicator_type}\n"
            f"[bold]Threat Type:[/bold] {result.threat_type}\n"
            f"[bold]Confidence:[/bold] {result.confidence}%\n"
            f"[bold]Source:[/bold] {result.source}\n"
            f"[bold]First Seen:[/bold] {result.first_seen.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"[bold]Last Seen:[/bold] {result.last_seen.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"[bold]Tags:[/bold] {', '.join(result.tags)}",
            title="IOC Found",
            border_style="yellow",
        ))
    else:
        primoroso.warning(f"⚠️  IOC not found in threat feeds: {indicator}")


# ==================== Actors Commands ====================

actors_app = typer.Typer(help="👥 Threat actor profiling")
app.add_typer(actors_app, name="actors")


@actors_app.command("list")
def actors_list(
    actor_type: Optional[str] = typer.Option(None, "--type", help="Filter by type"),
    active_only: bool = typer.Option(False, "--active", help="Only active actors"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
):
    """
    📋 List threat actors

    Example:
        vcli threat-intel actors list --type nation_state --active
    """
    from vertice.threat_intel import ActorType

    profiler = get_actor_profiler()

    # Parse type filter
    type_enum = None
    if actor_type:
        try:
            type_enum = ActorType(actor_type)
        except ValueError:
            primoroso.error(f"Invalid actor type: {actor_type}[/red]")
            raise typer.Exit(1)

    actors = profiler.list_actors(
        actor_type=type_enum,
        active_only=active_only,
        limit=limit,
    )

    # Display
    table = Table(title=f"Threat Actors ({len(actors)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Type", style="blue")
    table.add_column("Sophistication", style="magenta")
    table.add_column("Origin", style="yellow")
    table.add_column("Status", style="green")

    for actor in actors:
        status = "🟢 Active" if actor.is_active else "🔴 Inactive"

        table.add_row(
            actor.id,
            actor.name,
            actor.actor_type.value,
            actor.sophistication.value,
            actor.origin_country or "Unknown",
            status,
        )

    console.print(table)


@actors_app.command("profile")
def actors_profile(
    actor_id: str = typer.Argument(..., help="Actor ID"),
):
    """
    👤 Show detailed actor profile

    Example:
        vcli threat-intel actors profile APT28
    """
    profiler = get_actor_profiler()

    profile = profiler.get_actor_profile(actor_id)

    if not profile:
        primoroso.error(f"Actor not found: {actor_id}[/red]")
        raise typer.Exit(1)

    # Display profile
    console.print(Panel(
        f"[bold cyan]{profile['name']}[/bold cyan]\n"
        f"[dim]Aliases: {', '.join(profile['aliases'])}[/dim]\n\n"
        f"{profile['description']}\n\n"
        f"[bold]Type:[/bold] {profile['type']}\n"
        f"[bold]Sophistication:[/bold] {profile['sophistication']}\n"
        f"[bold]Motivation:[/bold] {profile['motivation']}\n"
        f"[bold]Origin:[/bold] {profile['origin_country']}\n"
        f"[bold]Active:[/bold] {'Yes' if profile['is_active'] else 'No'}",
        title=f"Threat Actor: {actor_id}",
        border_style="cyan",
    ))

    # Targets
    if profile['target_sectors']:
        primoroso.error("\n[bold]Target Sectors:[/bold]")
        console.print(f"  {', '.join(profile['target_sectors'])}")

    if profile['target_countries']:
        primoroso.error("\n[bold]Target Countries:[/bold]")
        console.print(f"  {', '.join(profile['target_countries'])}")

    # Tools
    if profile['tools']:
        primoroso.error("\n[bold]Known Tools:[/bold]")
        for tool in profile['tools'][:5]:
            primoroso.error(f"• {tool}")

    # Campaigns
    if profile['campaigns']:
        console.print(f"\n[bold]Campaigns ({len(profile['campaigns'])}):[/bold]")
        for campaign in profile['campaigns'][:5]:
            console.print(f"  • {campaign['name']} ({campaign['start_date'][:10]})")

    # IOCs
    console.print(f"\n[bold]IOCs:[/bold] {profile['iocs_count']}")


# ==================== TTP Commands ====================

ttp_app = typer.Typer(help="🎯 MITRE ATT&CK TTPs")
app.add_typer(ttp_app, name="ttp")


@ttp_app.command("list")
def ttp_list(
    tactic: Optional[str] = typer.Option(None, "--tactic", help="Filter by tactic"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
):
    """
    📋 List MITRE ATT&CK techniques

    Example:
        vcli threat-intel ttp list --tactic INITIAL_ACCESS
    """
    from vertice.threat_intel import MITRETactic

    mapper = get_ttp_mapper()

    # Parse tactic filter
    tactic_enum = None
    if tactic:
        try:
            tactic_enum = MITRETactic[tactic.upper()]
        except KeyError:
            primoroso.error(f"Invalid tactic: {tactic}[/red]")
            raise typer.Exit(1)

    techniques = mapper.list_techniques(
        tactic=tactic_enum,
        limit=limit,
    )

    # Display
    table = Table(title=f"MITRE ATT&CK Techniques ({len(techniques)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Tactic", style="blue")
    table.add_column("Platforms", style="yellow")

    for technique in techniques:
        platforms = ", ".join(technique.platforms[:3])
        if len(technique.platforms) > 3:
            platforms += "..."

        table.add_row(
            technique.technique_id,
            technique.name[:50] + "..." if len(technique.name) > 50 else technique.name,
            technique.tactic.name,
            platforms,
        )

    console.print(table)


@ttp_app.command("search")
def ttp_search(
    query: str = typer.Argument(..., help="Search query"),
):
    """
    🔍 Search MITRE techniques

    Example:
        vcli threat-intel ttp search phishing
    """
    mapper = get_ttp_mapper()

    techniques = mapper.search_techniques(query)

    if not techniques:
        primoroso.warning(f"⚠️  No techniques found for: {query}")
        raise typer.Exit(0)

    # Display
    table = Table(title=f"Search Results ({len(techniques)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Tactic", style="blue")
    table.add_column("Description", style="dim")

    for technique in techniques:
        desc = technique.description[:60] + "..." if len(technique.description) > 60 else technique.description

        table.add_row(
            technique.technique_id,
            technique.name,
            technique.tactic.name,
            desc,
        )

    console.print(table)


# ==================== Stats Command ====================

@app.command()
def stats():
    """
    📊 Show threat intelligence statistics

    Example:
        vcli threat-intel stats
    """
    aggregator = get_feed_aggregator()
    profiler = get_actor_profiler()
    mapper = get_ttp_mapper()

    # Get statistics
    feed_stats = aggregator.get_statistics()
    actor_stats = profiler.get_statistics()
    ttp_stats = mapper.get_statistics()

    console.print(Panel(
        "[bold cyan]Threat Intelligence Platform Statistics[/bold cyan]",
        border_style="cyan",
    ))

    # Feeds
    primoroso.error("\n[bold]Threat Feeds:[/bold]")
    console.print(f"  Total Feeds: {feed_stats['total_feeds']}")
    console.print(f"  Active Feeds: {feed_stats['active_feeds']}")
    console.print(f"  Total Indicators: {feed_stats['total_indicators']}")

    # Actors
    primoroso.error("\n[bold]Threat Actors:[/bold]")
    console.print(f"  Total Actors: {actor_stats['total_actors']}")
    console.print(f"  Active Actors: {actor_stats['active_actors']}")
    console.print(f"  Total Campaigns: {actor_stats['total_campaigns']}")

    # TTPs
    primoroso.error("\n[bold]MITRE ATT&CK:[/bold]")
    console.print(f"  Total Techniques: {ttp_stats['total_techniques']}")
    console.print(f"  Total Observations: {ttp_stats['total_observations']}")


# ==================== Main Command ====================

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    🌐 Threat intelligence platform

    Aggregate OSINT feeds, enrich IOCs, profile threat actors, map TTPs.

    Features:
    - Multi-source threat feeds (AlienVault OTX, Abuse.ch, CIRCL)
    - IOC enrichment (VirusTotal, AbuseIPDB, Shodan)
    - Threat actor database (APT28, Lazarus, FIN7, etc)
    - MITRE ATT&CK TTP mapping
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
