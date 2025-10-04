"""
🌐 Threat Intelligence Platform
Agregação, enrichment e análise de threat intelligence

Componentes:
- ThreatFeedAggregator: Agregação de feeds OSINT
- IOCEnricher: Enrichment de IOCs com contexto
- ThreatActorProfiler: Profiling de threat actors
- TTPMapper: Mapeamento de TTPs no MITRE ATT&CK
"""

from .feed_aggregator import (
    ThreatFeedAggregator,
    ThreatFeed,
    FeedSource,
    FeedType,
)
from .ioc_enricher import (
    IOCEnricher,
    IOC,
    IOCType,
    EnrichmentResult,
)
from .threat_actor import (
    ThreatActorProfiler,
    ThreatActor,
    ActorSophistication,
    ActorMotivation,
)
from .ttp_mapper import (
    TTPMapper,
    TTP,
    MITRETactic,
    MITRETechnique,
)

__all__ = [
    "ThreatFeedAggregator",
    "ThreatFeed",
    "FeedSource",
    "FeedType",
    "IOCEnricher",
    "IOC",
    "IOCType",
    "EnrichmentResult",
    "ThreatActorProfiler",
    "ThreatActor",
    "ActorSophistication",
    "ActorMotivation",
    "TTPMapper",
    "TTP",
    "MITRETactic",
    "MITRETechnique",
]
