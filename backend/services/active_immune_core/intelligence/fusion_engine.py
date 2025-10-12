"""Threat Intelligence Fusion Engine

Multi-source threat intelligence correlation and enrichment.
Aggregates IoCs from multiple sources to build complete threat context.

Biological Inspiration:
- Dendritic cells: Aggregate pathogen information from multiple sites
- Cross-presentation: Correlate signals from different immune sensors
- Memory formation: Build threat knowledge base

IIT Integration:
- Φ (Phi) maximization through source correlation
- Integrated information creates threat narrative
- Temporal binding enables attack chain reconstruction

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


class IOCType(Enum):
    """Types of Indicators of Compromise."""

    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    CVE = "cve"
    MUTEX = "mutex"
    REGISTRY_KEY = "registry_key"


@dataclass
class IOC:
    """Indicator of Compromise.

    Represents single piece of threat intelligence that can be
    used to identify malicious activity.

    Attributes:
        value: IOC value (IP, domain, hash, etc.)
        ioc_type: Type of IOC
        first_seen: When IOC was first observed
        last_seen: When IOC was last observed
        source: Original source of IOC
        confidence: Confidence in IOC validity (0.0-1.0)
        tags: Descriptive tags (e.g., malware family)
        context: Additional contextual data
    """

    value: str
    ioc_type: IOCType
    first_seen: datetime
    last_seen: datetime
    source: str
    confidence: float
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

    def normalize(self) -> str:
        """Normalize IOC value for comparison."""
        normalized = self.value.lower().strip()
        
        if self.ioc_type == IOCType.IP_ADDRESS:
            # Remove leading zeros from IP octets
            parts = normalized.split(".")
            normalized = ".".join(str(int(p)) for p in parts if p.isdigit())
        elif self.ioc_type in (IOCType.DOMAIN, IOCType.URL):
            # Remove protocol and trailing slashes
            normalized = normalized.replace("http://", "").replace("https://", "")
            normalized = normalized.rstrip("/")
        
        return normalized


@dataclass
class ThreatActor:
    """Known threat actor profile.

    Represents adversary group with known TTPs and campaigns.

    Attributes:
        actor_id: Unique actor identifier
        names: Known aliases
        country: Country of origin (if known)
        motivation: Primary motivation (financial, espionage, etc.)
        sophistication: Technical sophistication level
        ttps: Known MITRE ATT&CK techniques
        campaigns: Associated campaigns
    """

    actor_id: str
    names: List[str]
    country: Optional[str] = None
    motivation: str = "unknown"
    sophistication: str = "unknown"
    ttps: List[str] = field(default_factory=list)
    campaigns: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class EnrichedThreat:
    """Enriched threat with multi-source correlation.

    Result of fusion process containing complete threat context.

    Attributes:
        threat_id: Unique threat identifier
        primary_ioc: Main IOC that triggered enrichment
        related_iocs: Correlated IOCs from multiple sources
        threat_actor: Attributed threat actor (if known)
        campaigns: Associated campaigns
        ttps: MITRE ATT&CK techniques
        attack_chain_stage: Current kill chain stage
        severity: Threat severity (1-10)
        confidence: Overall confidence in assessment
        narrative: Human-readable threat description
        recommendations: Suggested defensive actions
        sources: Data sources used in enrichment
        enriched_at: Enrichment timestamp
    """

    threat_id: str
    primary_ioc: IOC
    related_iocs: List[IOC]
    threat_actor: Optional[ThreatActor]
    campaigns: List[str]
    ttps: List[str]
    attack_chain_stage: str
    severity: int
    confidence: float
    narrative: str
    recommendations: List[str]
    sources: List[str]
    enriched_at: datetime

    def __post_init__(self):
        """Validate severity range."""
        if not 1 <= self.severity <= 10:
            raise ValueError(f"Severity must be 1-10, got {self.severity}")


class ThreatIntelSource(Enum):
    """Threat intelligence source identifiers."""

    INTERNAL_HONEYPOT = "internal_honeypot"
    INTERNAL_HISTORY = "internal_history"
    OSINT_SHODAN = "osint_shodan"
    OSINT_CENSYS = "osint_censys"
    OSINT_GREYNOISE = "osint_greynoise"
    EXTERNAL_MISP = "external_misp"
    EXTERNAL_OTX = "external_otx"
    ABUSE_IP_DB = "abuse_ipdb"
    VIRUSTOTAL = "virustotal"
    THREAT_FOX = "threat_fox"


class ThreatIntelConnector:
    """Base class for threat intelligence source connectors.

    Subclasses implement specific API integrations.
    """

    def __init__(self, source_type: ThreatIntelSource, api_key: Optional[str] = None):
        """Initialize connector.

        Args:
            source_type: Source identifier
            api_key: API key for authenticated sources
        """
        self.source_type = source_type
        self.api_key = api_key

    async def lookup(self, ioc: IOC) -> Dict[str, Any]:
        """Look up IOC in threat intel source.

        Args:
            ioc: IOC to look up

        Returns:
            Dict with source data

        Raises:
            NotImplementedError: Subclasses must implement
        """
        raise NotImplementedError("Subclasses must implement lookup()")


class ThreatIntelFusionEngine:
    """Multi-source threat intelligence correlation engine.

    Aggregates and correlates IoCs from multiple sources to build
    complete threat context with LLM-generated narrative.

    Capabilities:
    1. IoC normalization across sources
    2. Cross-source correlation
    3. Threat actor attribution
    4. Attack chain reconstruction
    5. LLM-based narrative generation

    Sources:
    - Internal: Honeypots, historical attacks
    - OSINT: Shodan, Censys, GreyNoise
    - External feeds: MISP, AlienVault OTX
    - Commercial: VirusTotal, ThreatFox

    Fusion Process:
    1. Ingest IoCs from all sources
    2. Normalize and deduplicate
    3. Build correlation graph
    4. LLM analyzes patterns
    5. Generate enriched threat context

    Example:
        >>> from openai import AsyncOpenAI
        >>> llm = AsyncOpenAI()
        >>> sources = {
        ...     ThreatIntelSource.ABUSE_IP_DB: AbuseIPDBConnector(api_key="...")
        ... }
        >>> fusion = ThreatIntelFusionEngine(
        ...     sources=sources,
        ...     llm_client=llm
        ... )
        >>> ioc = IOC(
        ...     value="192.168.1.100",
        ...     ioc_type=IOCType.IP_ADDRESS,
        ...     first_seen=datetime.now(),
        ...     last_seen=datetime.now(),
        ...     source="firewall",
        ...     confidence=0.9
        ... )
        >>> enriched = await fusion.correlate_indicators([ioc])
        >>> print(enriched.narrative)
    """

    def __init__(
        self,
        sources: Dict[ThreatIntelSource, ThreatIntelConnector],
        llm_client: Any,  # openai.AsyncOpenAI
        model: str = "gpt-4o",
        max_related_iocs: int = 50,
    ):
        """Initialize fusion engine.

        Args:
            sources: Dict mapping source type to connector
            llm_client: LLM client for narrative generation
            model: LLM model to use
            max_related_iocs: Max related IoCs to include
        """
        self.sources = sources
        self.llm = llm_client
        self.model = model
        self.max_related_iocs = max_related_iocs

        # Metrics
        self.enrichments_total = Counter(
            "threat_enrichments_total", "Total threat enrichments performed"
        )
        self.correlation_score = Histogram(
            "threat_correlation_score", "Correlation confidence score"
        )
        self.source_queries = Counter(
            "threat_intel_source_queries_total",
            "Queries to threat intel sources",
            ["source", "status"],
        )

        logger.info(
            f"Fusion engine initialized with {len(sources)} sources, "
            f"model={model}"
        )

    async def correlate_indicators(self, indicators: List[IOC]) -> EnrichedThreat:
        """Correlate IoCs from multiple sources.

        Main enrichment method. Takes list of IoCs and produces
        comprehensive threat assessment with multi-source correlation.

        Process:
        1. Normalize indicators
        2. Query all sources for each IoC
        3. Build correlation graph
        4. LLM analyzes patterns
        5. Generate enriched threat

        Args:
            indicators: List of IoCs to correlate

        Returns:
            EnrichedThreat with complete context

        Raises:
            ValueError: If indicators list is empty
            ThreatIntelError: If enrichment fails
        """
        if not indicators:
            raise ValueError("indicators list cannot be empty")

        try:
            # 1. Normalize IoCs
            normalized = [self._normalize_ioc(ioc) for ioc in indicators]

            # 2. Query all sources
            enriched_iocs = []
            for ioc in normalized:
                source_data = await self._query_all_sources(ioc)
                merged = self._merge_source_data(ioc, source_data)
                enriched_iocs.append(merged)

            # Limit related IoCs
            if len(enriched_iocs) > self.max_related_iocs:
                logger.warning(
                    f"Limiting related IoCs from {len(enriched_iocs)} "
                    f"to {self.max_related_iocs}"
                )
                enriched_iocs = enriched_iocs[: self.max_related_iocs]

            # 3. Build correlation graph
            correlation_graph = self._build_correlation_graph(enriched_iocs)

            # 4. LLM analysis
            narrative = await self._generate_threat_narrative(correlation_graph)

            # 5. Assemble enriched threat
            enriched = EnrichedThreat(
                threat_id=self._generate_threat_id(indicators),
                primary_ioc=indicators[0],
                related_iocs=enriched_iocs,
                threat_actor=self._attribute_actor(correlation_graph),
                campaigns=self._identify_campaigns(correlation_graph),
                ttps=self._extract_ttps(correlation_graph),
                attack_chain_stage=self._determine_chain_stage(indicators),
                severity=self._calculate_severity(correlation_graph),
                confidence=self._calculate_confidence(correlation_graph),
                narrative=narrative,
                recommendations=await self._generate_recommendations(
                    correlation_graph
                ),
                sources=[s.value for s in self.sources.keys()],
                enriched_at=datetime.utcnow(),
            )

            # Record metrics
            self.enrichments_total.inc()
            self.correlation_score.observe(enriched.confidence)

            logger.info(
                f"Threat {enriched.threat_id} enriched: "
                f"severity={enriched.severity}, "
                f"confidence={enriched.confidence:.2f}, "
                f"related_iocs={len(enriched.related_iocs)}"
            )

            return enriched

        except Exception as e:
            logger.error(f"Threat enrichment failed: {e}")
            raise ThreatIntelError(f"Failed to correlate indicators: {str(e)}") from e

    async def build_attack_graph(self, threat: EnrichedThreat) -> Dict[str, Any]:
        """Build attack graph showing probable attack paths.

        Uses LLM to predict attack progression based on threat context.

        Attack graph shows:
        - Entry points
        - Lateral movement paths
        - Target assets
        - Probable next steps

        Args:
            threat: Enriched threat

        Returns:
            Attack graph dict with nodes and edges

        Raises:
            ThreatIntelError: If graph generation fails
        """
        try:
            # LLM prompt for attack path prediction
            prompt = f"""Build attack graph for this threat:

Threat Context:
{threat.narrative}

TTPs Observed:
{', '.join(threat.ttps)}

Current Stage: {threat.attack_chain_stage}

Task: Predict likely attack paths including:
1. Entry points (which assets attacker can reach)
2. Lateral movement options
3. High-value targets
4. Required privileges/credentials
5. Probable next 3 techniques

Output as JSON graph:
{{
    "nodes": [
        {{"id": "node1", "type": "asset|technique", "label": "...", "risk": 1-10}},
        ...
    ],
    "edges": [
        {{"from": "node1", "to": "node2", "relationship": "...", "probability": 0.0-1.0}},
        ...
    ],
    "critical_paths": [
        {{"path": ["node1", "node2", "node3"], "risk": 1-10}}
    ]
}}"""

            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert specializing in attack path analysis.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            graph = json.loads(response.choices[0].message.content)

            logger.info(
                f"Attack graph generated for {threat.threat_id}: "
                f"{len(graph.get('nodes', []))} nodes, "
                f"{len(graph.get('edges', []))} edges"
            )

            return graph

        except Exception as e:
            logger.error(f"Attack graph generation failed: {e}")
            raise ThreatIntelError(f"Failed to build attack graph: {str(e)}") from e

    # Private methods

    def _normalize_ioc(self, ioc: IOC) -> IOC:
        """Normalize IOC for consistent comparison."""
        normalized_value = ioc.normalize()
        return IOC(
            value=normalized_value,
            ioc_type=ioc.ioc_type,
            first_seen=ioc.first_seen,
            last_seen=ioc.last_seen,
            source=ioc.source,
            confidence=ioc.confidence,
            tags=ioc.tags,
            context=ioc.context,
        )

    async def _query_all_sources(self, ioc: IOC) -> Dict[ThreatIntelSource, Dict]:
        """Query all configured sources for IoC."""
        results = {}

        for source_type, connector in self.sources.items():
            try:
                data = await connector.lookup(ioc)
                results[source_type] = data
                self.source_queries.labels(
                    source=source_type.value, status="success"
                ).inc()
            except Exception as e:
                logger.warning(f"Source {source_type.value} query failed: {e}")
                self.source_queries.labels(
                    source=source_type.value, status="error"
                ).inc()

        return results

    def _merge_source_data(
        self, ioc: IOC, source_data: Dict[ThreatIntelSource, Dict]
    ) -> IOC:
        """Merge data from multiple sources into single IOC."""
        merged_tags = set(ioc.tags)
        merged_context = dict(ioc.context)
        confidences = [ioc.confidence]

        for source, data in source_data.items():
            # Aggregate tags
            if "tags" in data:
                merged_tags.update(data["tags"])

            # Merge context
            merged_context[source.value] = data

            # Collect confidence scores
            if "confidence" in data:
                confidences.append(float(data["confidence"]))

        # Average confidence across sources
        avg_confidence = sum(confidences) / len(confidences)

        return IOC(
            value=ioc.value,
            ioc_type=ioc.ioc_type,
            first_seen=ioc.first_seen,
            last_seen=ioc.last_seen,
            source=f"{ioc.source}+{len(source_data)}_sources",
            confidence=avg_confidence,
            tags=list(merged_tags),
            context=merged_context,
        )

    def _build_correlation_graph(self, iocs: List[IOC]) -> Dict[str, Any]:
        """Build correlation graph from IoCs."""
        graph = {
            "iocs": iocs,
            "relationships": [],
            "clusters": [],
            "actors": [],
            "campaigns": [],
        }

        # Find relationships (co-occurrence, temporal proximity)
        for i, ioc1 in enumerate(iocs):
            for ioc2 in iocs[i + 1 :]:
                relationship = self._find_relationship(ioc1, ioc2)
                if relationship:
                    graph["relationships"].append(relationship)

        # Cluster related IoCs
        graph["clusters"] = self._cluster_iocs(iocs)

        return graph

    def _find_relationship(self, ioc1: IOC, ioc2: IOC) -> Optional[Dict]:
        """Find relationship between two IoCs."""
        # Check tag overlap
        common_tags = set(ioc1.tags) & set(ioc2.tags)
        if common_tags:
            return {
                "ioc1": ioc1.value,
                "ioc2": ioc2.value,
                "relationship": "common_tags",
                "details": list(common_tags),
            }

        # Check temporal proximity (within 1 hour)
        time_delta = abs((ioc1.last_seen - ioc2.last_seen).total_seconds())
        if time_delta < 3600:
            return {
                "ioc1": ioc1.value,
                "ioc2": ioc2.value,
                "relationship": "temporal_proximity",
                "details": f"{time_delta}s apart",
            }

        return None

    def _cluster_iocs(self, iocs: List[IOC]) -> List[List[str]]:
        """Cluster related IoCs (simplified implementation)."""
        # Group by common tags
        tag_groups: Dict[str, List[str]] = {}
        for ioc in iocs:
            for tag in ioc.tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(ioc.value)

        return [group for group in tag_groups.values() if len(group) > 1]

    async def _generate_threat_narrative(
        self, correlation_graph: Dict[str, Any]
    ) -> str:
        """Generate human-readable threat narrative using LLM."""
        prompt = f"""Analyze this threat intelligence correlation and generate a narrative.

Correlation Data:
- IoCs: {len(correlation_graph['iocs'])} indicators
- Relationships: {len(correlation_graph['relationships'])}
- Clusters: {len(correlation_graph['clusters'])}

Sample IoCs:
{json.dumps([ioc.__dict__ for ioc in correlation_graph['iocs'][:5]], default=str, indent=2)}

Generate a clear 2-3 paragraph narrative explaining:
1. What is this threat?
2. Who is behind it (if known)?
3. What are they trying to achieve?
4. How serious is it?
5. What should defenders do?

Write for a SOC analyst audience."""

        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cybersecurity analyst specializing in threat intelligence.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )

        return response.choices[0].message.content

    async def _generate_recommendations(
        self, correlation_graph: Dict[str, Any]
    ) -> List[str]:
        """Generate defensive recommendations."""
        # Placeholder - could use LLM for more sophisticated recommendations
        recommendations = [
            "Monitor for additional IoCs from same cluster",
            "Review logs for historical occurrences",
            "Update detection rules with new indicators",
        ]

        if len(correlation_graph["iocs"]) > 10:
            recommendations.append("Consider blocking entire IP range")

        return recommendations

    def _attribute_actor(self, correlation_graph: Dict[str, Any]) -> Optional[ThreatActor]:
        """Attempt to attribute threat to known actor."""
        # Placeholder - real implementation would query actor database
        return None

    def _identify_campaigns(self, correlation_graph: Dict[str, Any]) -> List[str]:
        """Identify associated campaigns."""
        campaigns = set()
        for ioc in correlation_graph["iocs"]:
            for tag in ioc.tags:
                if "campaign" in tag.lower():
                    campaigns.add(tag)
        return list(campaigns)

    def _extract_ttps(self, correlation_graph: Dict[str, Any]) -> List[str]:
        """Extract MITRE TTPs from IoC context."""
        ttps = set()
        for ioc in correlation_graph["iocs"]:
            if "ttps" in ioc.context:
                ttps.update(ioc.context["ttps"])
        return list(ttps)

    def _determine_chain_stage(self, indicators: List[IOC]) -> str:
        """Determine kill chain stage based on IoC types."""
        types = {ioc.ioc_type for ioc in indicators}

        if IOCType.IP_ADDRESS in types or IOCType.DOMAIN in types:
            return "reconnaissance"
        elif IOCType.FILE_HASH in types:
            return "weaponization"
        elif IOCType.CVE in types:
            return "exploitation"
        else:
            return "unknown"

    def _calculate_severity(self, correlation_graph: Dict[str, Any]) -> int:
        """Calculate threat severity (1-10)."""
        base_severity = 5

        # Increase for many related IoCs
        ioc_count = len(correlation_graph["iocs"])
        if ioc_count > 20:
            base_severity += 2
        elif ioc_count > 10:
            base_severity += 1

        # Increase for known campaigns
        if correlation_graph["campaigns"]:
            base_severity += 1

        # Increase for attributed actors
        if correlation_graph["actors"]:
            base_severity += 2

        return min(base_severity, 10)

    def _calculate_confidence(self, correlation_graph: Dict[str, Any]) -> float:
        """Calculate overall confidence in threat assessment."""
        if not correlation_graph["iocs"]:
            return 0.0

        # Average IoC confidence
        ioc_confidences = [ioc.confidence for ioc in correlation_graph["iocs"]]
        avg_confidence = sum(ioc_confidences) / len(ioc_confidences)

        # Boost for multiple sources
        source_boost = min(len(self.sources) * 0.05, 0.2)

        # Boost for relationships found
        relationship_boost = min(len(correlation_graph["relationships"]) * 0.02, 0.15)

        final_confidence = min(avg_confidence + source_boost + relationship_boost, 1.0)

        return round(final_confidence, 2)

    def _generate_threat_id(self, indicators: List[IOC]) -> str:
        """Generate unique threat ID from indicators."""
        # Hash primary IoC value + timestamp
        primary = indicators[0].value
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{primary}_{timestamp}".encode()
        return f"threat_{hashlib.sha256(hash_input).hexdigest()[:16]}"


class ThreatIntelError(Exception):
    """Raised when threat intelligence operation fails."""

    pass
