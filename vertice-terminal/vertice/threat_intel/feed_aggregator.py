"""
🌐 Threat Feed Aggregator - Agregação de feeds de threat intelligence

Fontes OSINT suportadas:
- AlienVault OTX (Open Threat Exchange)
- Abuse.ch (URLhaus, MalwareBazaar, ThreatFox)
- CIRCL (MISP feeds)
- VirusTotal Intelligence
- IBM X-Force Exchange
- Talos Intelligence
- Custom STIX/TAXII feeds

Feed Types:
- IP reputation feeds
- Domain/URL blocklists
- Malware hashes (MD5, SHA1, SHA256)
- CVE feeds
- Botnet C2 servers
- Phishing campaigns
- APT indicators
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FeedSource(Enum):
    """Fontes de threat intelligence"""
    ALIENVAULT_OTX = "alienvault_otx"
    ABUSE_CH_URLHAUS = "abuse_ch_urlhaus"
    ABUSE_CH_MALWAREBAZAAR = "abuse_ch_malwarebazaar"
    ABUSE_CH_THREATFOX = "abuse_ch_threatfox"
    CIRCL_MISP = "circl_misp"
    VIRUSTOTAL = "virustotal"
    IBM_XFORCE = "ibm_xforce"
    TALOS = "talos"
    CUSTOM_STIX = "custom_stix"
    CUSTOM_TAXII = "custom_taxii"


class FeedType(Enum):
    """Tipos de feed"""
    IP_REPUTATION = "ip_reputation"
    DOMAIN_BLOCKLIST = "domain_blocklist"
    URL_BLOCKLIST = "url_blocklist"
    MALWARE_HASH = "malware_hash"
    CVE = "cve"
    C2_SERVER = "c2_server"
    PHISHING = "phishing"
    APT_INDICATOR = "apt_indicator"


class FeedStatus(Enum):
    """Status do feed"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DEPRECATED = "deprecated"


@dataclass
class ThreatIndicator:
    """
    Indicador de ameaça individual

    Attributes:
        indicator: O indicador (IP, domain, hash, etc)
        indicator_type: Tipo do indicador
        confidence: Confidence score (0-100)
        threat_type: Tipo de ameaça
        first_seen: Primeira vez visto
        last_seen: Última vez visto
        tags: Tags de classificação
        source: Fonte do indicador
        metadata: Metadados adicionais
    """
    indicator: str
    indicator_type: str
    confidence: int  # 0-100
    threat_type: str

    first_seen: datetime
    last_seen: datetime

    # Classification
    tags: List[str] = field(default_factory=list)
    source: str = ""

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Related indicators
    related_indicators: List[str] = field(default_factory=list)


@dataclass
class ThreatFeed:
    """
    Feed de threat intelligence

    Attributes:
        id: Unique feed ID
        name: Feed name
        source: Feed source
        feed_type: Type of feed
        url: Feed URL
        status: Feed status
        last_updated: Last update timestamp
        update_frequency_hours: Update frequency
        indicators_count: Number of indicators
        enabled: If feed is enabled
    """
    id: str
    name: str
    source: FeedSource
    feed_type: FeedType
    url: str

    status: FeedStatus = FeedStatus.ACTIVE
    last_updated: Optional[datetime] = None
    update_frequency_hours: int = 24

    # Statistics
    indicators_count: int = 0
    error_count: int = 0

    # Configuration
    enabled: bool = True
    api_key: Optional[str] = None

    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)


class ThreatFeedAggregator:
    """
    Threat Feed Aggregation System

    Features:
    - Multi-source feed aggregation
    - Automatic feed updates
    - Indicator deduplication
    - Confidence scoring
    - Backend integration
    - STIX/TAXII support
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        storage_path: Optional[Path] = None,
    ):
        """
        Args:
            backend_url: URL do threat_intel_service
            use_backend: Se True, usa backend
            storage_path: Local storage path
        """
        self.backend_url = backend_url or "http://localhost:8018"
        self.use_backend = use_backend

        # Storage
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".vertice" / "threat_intel"

        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Feed registry
        self.feeds: Dict[str, ThreatFeed] = {}

        # Indicators cache
        self.indicators: Dict[str, ThreatIndicator] = {}

        # Load default feeds
        self._load_default_feeds()

    def _load_default_feeds(self):
        """Carrega feeds padrão"""

        default_feeds = [
            ThreatFeed(
                id="otx-malware-hashes",
                name="AlienVault OTX - Malware Hashes",
                source=FeedSource.ALIENVAULT_OTX,
                feed_type=FeedType.MALWARE_HASH,
                url="https://otx.alienvault.com/api/v1/pulses/subscribed",
                description="AlienVault OTX malware hash indicators",
                tags=["malware", "hashes"],
            ),
            ThreatFeed(
                id="urlhaus-urls",
                name="Abuse.ch URLhaus",
                source=FeedSource.ABUSE_CH_URLHAUS,
                feed_type=FeedType.URL_BLOCKLIST,
                url="https://urlhaus.abuse.ch/downloads/csv_recent/",
                description="URLhaus malicious URL feed",
                tags=["malware", "urls"],
            ),
            ThreatFeed(
                id="malwarebazaar-samples",
                name="Abuse.ch MalwareBazaar",
                source=FeedSource.ABUSE_CH_MALWAREBAZAAR,
                feed_type=FeedType.MALWARE_HASH,
                url="https://mb-api.abuse.ch/api/v1/",
                description="MalwareBazaar malware samples",
                tags=["malware", "samples"],
            ),
            ThreatFeed(
                id="threatfox-iocs",
                name="Abuse.ch ThreatFox",
                source=FeedSource.ABUSE_CH_THREATFOX,
                feed_type=FeedType.APT_INDICATOR,
                url="https://threatfox-api.abuse.ch/api/v1/",
                description="ThreatFox IOC feed",
                tags=["ioc", "apt"],
            ),
        ]

        for feed in default_feeds:
            self.feeds[feed.id] = feed

        logger.info(f"Loaded {len(default_feeds)} default threat feeds")

    def add_feed(
        self,
        name: str,
        source: FeedSource,
        feed_type: FeedType,
        url: str,
        description: str = "",
        api_key: Optional[str] = None,
        update_frequency_hours: int = 24,
    ) -> ThreatFeed:
        """
        Adiciona feed customizado

        Args:
            name: Feed name
            source: Feed source
            feed_type: Feed type
            url: Feed URL
            description: Description
            api_key: API key (if required)
            update_frequency_hours: Update frequency

        Returns:
            ThreatFeed object
        """
        import uuid

        feed = ThreatFeed(
            id=f"feed-{uuid.uuid4().hex[:8]}",
            name=name,
            source=source,
            feed_type=feed_type,
            url=url,
            description=description,
            api_key=api_key,
            update_frequency_hours=update_frequency_hours,
        )

        self.feeds[feed.id] = feed

        logger.info(f"Added custom feed: {name} ({feed.id})")

        return feed

    def update_feed(self, feed_id: str) -> int:
        """
        Atualiza feed específico

        Args:
            feed_id: Feed ID

        Returns:
            Number of indicators fetched
        """
        feed = self.feeds.get(feed_id)

        if not feed:
            logger.warning(f"Feed not found: {feed_id}")
            return 0

        if not feed.enabled:
            logger.info(f"Feed disabled, skipping: {feed.name}")
            return 0

        logger.info(f"Updating feed: {feed.name} ({feed.source.value})")

        try:
            # Fetch indicators based on source
            if feed.source == FeedSource.ALIENVAULT_OTX:
                indicators = self._fetch_otx_feed(feed)

            elif feed.source == FeedSource.ABUSE_CH_URLHAUS:
                indicators = self._fetch_urlhaus_feed(feed)

            elif feed.source == FeedSource.ABUSE_CH_MALWAREBAZAAR:
                indicators = self._fetch_malwarebazaar_feed(feed)

            elif feed.source == FeedSource.ABUSE_CH_THREATFOX:
                indicators = self._fetch_threatfox_feed(feed)

            else:
                logger.warning(f"Feed source not implemented: {feed.source.value}")
                indicators = []

            # Store indicators
            for indicator in indicators:
                self.indicators[indicator.indicator] = indicator

            # Update feed metadata
            feed.last_updated = datetime.now()
            feed.indicators_count = len(indicators)
            feed.status = FeedStatus.ACTIVE
            feed.error_count = 0

            logger.info(
                f"Feed updated: {feed.name} - {len(indicators)} indicators"
            )

            return len(indicators)

        except Exception as e:
            logger.error(f"Feed update failed: {feed.name} - {e}")
            feed.status = FeedStatus.ERROR
            feed.error_count += 1
            return 0

    def _fetch_otx_feed(self, feed: ThreatFeed) -> List[ThreatIndicator]:
        """Fetch AlienVault OTX feed"""
        import httpx

        indicators = []

        try:
            headers = {}
            if feed.api_key:
                headers["X-OTX-API-KEY"] = feed.api_key

            with httpx.Client(timeout=30.0) as client:
                response = client.get(feed.url, headers=headers)
                response.raise_for_status()

                data = response.json()

                # Parse OTX pulses
                for pulse in data.get("results", []):
                    for indicator_data in pulse.get("indicators", []):
                        indicator = ThreatIndicator(
                            indicator=indicator_data.get("indicator", ""),
                            indicator_type=indicator_data.get("type", "unknown"),
                            confidence=80,  # OTX is high confidence
                            threat_type=pulse.get("name", "unknown"),
                            first_seen=datetime.now(),
                            last_seen=datetime.now(),
                            source="AlienVault OTX",
                            tags=pulse.get("tags", []),
                            metadata={
                                "pulse_id": pulse.get("id"),
                                "description": pulse.get("description", ""),
                            }
                        )

                        indicators.append(indicator)

        except Exception as e:
            logger.error(f"OTX feed fetch failed: {e}")

        return indicators

    def _fetch_urlhaus_feed(self, feed: ThreatFeed) -> List[ThreatIndicator]:
        """Fetch URLhaus feed"""
        import httpx

        indicators = []

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(feed.url)
                response.raise_for_status()

                # Parse CSV
                lines = response.text.split('\n')

                for line in lines:
                    if line.startswith('#') or not line.strip():
                        continue

                    parts = line.split(',')

                    if len(parts) >= 7:
                        url = parts[2].strip('"')
                        threat_type = parts[4].strip('"')

                        indicator = ThreatIndicator(
                            indicator=url,
                            indicator_type="url",
                            confidence=90,  # URLhaus is high confidence
                            threat_type=threat_type,
                            first_seen=datetime.now(),
                            last_seen=datetime.now(),
                            source="Abuse.ch URLhaus",
                            tags=["malware", "url"],
                        )

                        indicators.append(indicator)

        except Exception as e:
            logger.error(f"URLhaus feed fetch failed: {e}")

        return indicators

    def _fetch_malwarebazaar_feed(self, feed: ThreatFeed) -> List[ThreatIndicator]:
        """Fetch MalwareBazaar feed"""
        import httpx

        indicators = []

        try:
            with httpx.Client(timeout=30.0) as client:
                # Get recent samples
                response = client.post(
                    feed.url,
                    json={"query": "get_recent", "selector": 100}
                )
                response.raise_for_status()

                data = response.json()

                for sample in data.get("data", []):
                    indicator = ThreatIndicator(
                        indicator=sample.get("sha256_hash", ""),
                        indicator_type="file_hash",
                        confidence=95,
                        threat_type=sample.get("signature", "unknown"),
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        source="Abuse.ch MalwareBazaar",
                        tags=sample.get("tags", []),
                        metadata={
                            "file_type": sample.get("file_type"),
                            "file_name": sample.get("file_name"),
                        }
                    )

                    indicators.append(indicator)

        except Exception as e:
            logger.error(f"MalwareBazaar feed fetch failed: {e}")

        return indicators

    def _fetch_threatfox_feed(self, feed: ThreatFeed) -> List[ThreatIndicator]:
        """Fetch ThreatFox feed"""
        import httpx

        indicators = []

        try:
            with httpx.Client(timeout=30.0) as client:
                # Get recent IOCs
                response = client.post(
                    feed.url,
                    json={"query": "get_iocs", "days": 7}
                )
                response.raise_for_status()

                data = response.json()

                for ioc in data.get("data", []):
                    indicator = ThreatIndicator(
                        indicator=ioc.get("ioc", ""),
                        indicator_type=ioc.get("ioc_type", "unknown"),
                        confidence=int(ioc.get("confidence_level", 50)),
                        threat_type=ioc.get("threat_type", "unknown"),
                        first_seen=datetime.fromisoformat(ioc.get("first_seen", datetime.now().isoformat())),
                        last_seen=datetime.fromisoformat(ioc.get("last_seen", datetime.now().isoformat())),
                        source="Abuse.ch ThreatFox",
                        tags=ioc.get("tags", []),
                        metadata={
                            "malware": ioc.get("malware"),
                            "malware_alias": ioc.get("malware_alias"),
                        }
                    )

                    indicators.append(indicator)

        except Exception as e:
            logger.error(f"ThreatFox feed fetch failed: {e}")

        return indicators

    def update_all_feeds(self) -> Dict[str, int]:
        """
        Atualiza todos os feeds ativos

        Returns:
            Dict mapping feed_id to indicator count
        """
        results = {}

        for feed_id, feed in self.feeds.items():
            if not feed.enabled:
                continue

            # Check if update is needed
            if feed.last_updated:
                hours_since_update = (
                    datetime.now() - feed.last_updated
                ).total_seconds() / 3600

                if hours_since_update < feed.update_frequency_hours:
                    logger.debug(
                        f"Feed {feed.name} updated recently, skipping"
                    )
                    continue

            count = self.update_feed(feed_id)
            results[feed_id] = count

        logger.info(
            f"Updated {len(results)} feeds, "
            f"total indicators: {sum(results.values())}"
        )

        return results

    def search_indicator(self, indicator: str) -> Optional[ThreatIndicator]:
        """
        Busca indicador no cache

        Args:
            indicator: Indicator value

        Returns:
            ThreatIndicator if found
        """
        return self.indicators.get(indicator)

    def search_by_type(
        self,
        indicator_type: str,
        limit: int = 100,
    ) -> List[ThreatIndicator]:
        """
        Busca indicadores por tipo

        Args:
            indicator_type: Type of indicator
            limit: Max results

        Returns:
            List of ThreatIndicator
        """
        results = [
            ind for ind in self.indicators.values()
            if ind.indicator_type == indicator_type
        ]

        # Sort by last_seen (most recent first)
        results = sorted(results, key=lambda x: x.last_seen, reverse=True)

        return results[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos feeds

        Returns:
            Statistics dict
        """
        # Count by type
        by_type = {}
        for indicator in self.indicators.values():
            by_type[indicator.indicator_type] = by_type.get(
                indicator.indicator_type, 0
            ) + 1

        # Count by source
        by_source = {}
        for indicator in self.indicators.values():
            by_source[indicator.source] = by_source.get(
                indicator.source, 0
            ) + 1

        # Feed statistics
        active_feeds = len([f for f in self.feeds.values() if f.enabled])
        error_feeds = len([
            f for f in self.feeds.values()
            if f.status == FeedStatus.ERROR
        ])

        return {
            "total_indicators": len(self.indicators),
            "total_feeds": len(self.feeds),
            "active_feeds": active_feeds,
            "error_feeds": error_feeds,
            "by_indicator_type": by_type,
            "by_source": by_source,
        }

    def get_feed(self, feed_id: str) -> Optional[ThreatFeed]:
        """Retorna feed por ID"""
        return self.feeds.get(feed_id)

    def list_feeds(
        self,
        source: Optional[FeedSource] = None,
        feed_type: Optional[FeedType] = None,
        enabled_only: bool = False,
    ) -> List[ThreatFeed]:
        """
        Lista feeds com filtros

        Args:
            source: Filter by source
            feed_type: Filter by type
            enabled_only: Only enabled feeds

        Returns:
            List of ThreatFeed
        """
        feeds = list(self.feeds.values())

        if source:
            feeds = [f for f in feeds if f.source == source]

        if feed_type:
            feeds = [f for f in feeds if f.feed_type == feed_type]

        if enabled_only:
            feeds = [f for f in feeds if f.enabled]

        return feeds
