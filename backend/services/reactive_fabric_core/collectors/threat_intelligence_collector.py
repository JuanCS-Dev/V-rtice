"""
Threat Intelligence Collector for external threat feed integration.

This collector interfaces with various threat intelligence sources including:
- MISP (Malware Information Sharing Platform)
- VirusTotal API
- AbuseIPDB
- AlienVault OTX
- Custom threat feeds

Phase 1: PASSIVE collection only - no automated responses
"""

import asyncio
import hashlib
import ipaddress
import json
import logging
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Set
from urllib.parse import quote_plus

import aiohttp
from pydantic import BaseModel, Field, field_validator

from .base_collector import BaseCollector, CollectedEvent, CollectorConfig

logger = logging.getLogger(__name__)


class ThreatIntelligenceConfig(CollectorConfig):
    """Configuration for Threat Intelligence Collector."""

    # API Keys
    virustotal_api_key: Optional[str] = Field(
        default=None, description="VirusTotal API key"
    )
    abuseipdb_api_key: Optional[str] = Field(
        default=None, description="AbuseIPDB API key"
    )
    alienvault_api_key: Optional[str] = Field(
        default=None, description="AlienVault OTX API key"
    )
    misp_url: Optional[str] = Field(
        default=None, description="MISP instance URL"
    )
    misp_api_key: Optional[str] = Field(
        default=None, description="MISP API key"
    )

    # Collection settings
    check_ips: bool = Field(default=True, description="Check IP addresses")
    check_domains: bool = Field(default=True, description="Check domain names")
    check_hashes: bool = Field(default=True, description="Check file hashes")
    check_urls: bool = Field(default=True, description="Check URLs")

    # Rate limiting
    requests_per_minute: int = Field(
        default=60, description="Max API requests per minute"
    )
    cache_ttl_minutes: int = Field(
        default=60, description="Cache TTL in minutes"
    )

    # Thresholds
    min_reputation_score: float = Field(
        default=0.3, description="Minimum reputation score to flag as threat"
    )
    max_false_positives: int = Field(
        default=5, description="Max false positives before reducing confidence"
    )


class ThreatIndicator(BaseModel):
    """Represents a threat indicator."""

    indicator_type: str  # ip, domain, hash, url
    value: str
    source: str
    severity: str
    confidence: float
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class ThreatIntelligenceCollector(BaseCollector):
    """
    Collector for external threat intelligence feeds.

    Integrates with multiple threat intelligence sources to:
    - Validate IP reputation
    - Check domain/URL blocklists
    - Verify file hash indicators
    - Correlate with known threat campaigns

    Phase 1: PASSIVE collection only
    """

    def __init__(self, config: ThreatIntelligenceConfig):
        """Initialize threat intelligence collector."""
        super().__init__(config)
        self.config: ThreatIntelligenceConfig = config
        self.session: Optional[aiohttp.ClientSession] = None

        # Rate limiting
        self.request_times: List[datetime] = []

        # Cache for threat indicators
        self.cache: Dict[str, ThreatIndicator] = {}

        # Tracking false positives
        self.false_positives: Set[str] = set()

    async def initialize(self) -> None:
        """Initialize threat intelligence connections."""
        # Create HTTP session
        connector = aiohttp.TCPConnector(ssl=True)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )

        logger.info("Initialized Threat Intelligence Collector")

    async def validate_source(self) -> bool:
        """Validate connectivity to at least one threat intel source."""
        if not self.session:
            return False

        validations = []

        # Check VirusTotal
        if self.config.virustotal_api_key:
            validations.append(self._validate_virustotal())

        # Check AbuseIPDB
        if self.config.abuseipdb_api_key:
            validations.append(self._validate_abuseipdb())

        # Check AlienVault
        if self.config.alienvault_api_key:
            validations.append(self._validate_alienvault())

        # Check MISP
        if self.config.misp_url and self.config.misp_api_key:
            validations.append(self._validate_misp())

        if not validations:
            logger.warning("No threat intelligence sources configured")
            return False

        # Return True if at least one source is valid
        results = await asyncio.gather(*validations, return_exceptions=True)
        return any(r is True for r in results if not isinstance(r, Exception))

    async def _validate_virustotal(self) -> bool:
        """Validate VirusTotal API connectivity."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8"

            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"VirusTotal validation failed: {e}")
            return False

    async def _validate_abuseipdb(self) -> bool:
        """Validate AbuseIPDB API connectivity."""
        try:
            headers = {"Key": self.config.abuseipdb_api_key}
            url = "https://api.abuseipdb.com/api/v2/check"
            params = {"ipAddress": "8.8.8.8"}

            async with self.session.get(url, headers=headers, params=params) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"AbuseIPDB validation failed: {e}")
            return False

    async def _validate_alienvault(self) -> bool:
        """Validate AlienVault OTX API connectivity."""
        try:
            headers = {"X-OTX-API-KEY": self.config.alienvault_api_key}
            url = "https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general"

            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"AlienVault validation failed: {e}")
            return False

    async def _validate_misp(self) -> bool:
        """Validate MISP API connectivity."""
        try:
            headers = {
                "Authorization": self.config.misp_api_key,
                "Accept": "application/json"
            }
            url = f"{self.config.misp_url}/servers/getVersion"

            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"MISP validation failed: {e}")
            return False

    async def collect(self) -> AsyncIterator[CollectedEvent]:
        """Collect threat intelligence events."""
        if not self.session:
            return

        # Clean expired cache entries
        self._clean_cache()

        # Collect from active threat feeds
        indicators: List[ThreatIndicator] = []

        # Collect from each configured source
        if self.config.virustotal_api_key:
            vt_indicators = await self._collect_virustotal()
            indicators.extend(vt_indicators)

        if self.config.abuseipdb_api_key:
            abuse_indicators = await self._collect_abuseipdb()
            indicators.extend(abuse_indicators)

        if self.config.alienvault_api_key:
            otx_indicators = await self._collect_alienvault()
            indicators.extend(otx_indicators)

        if self.config.misp_url and self.config.misp_api_key:
            misp_indicators = await self._collect_misp()
            indicators.extend(misp_indicators)

        # Convert indicators to events
        for indicator in indicators:
            if await self._should_report(indicator):
                event = self._indicator_to_event(indicator)
                self.metrics.events_collected += 1
                yield event

    async def check_ip(self, ip_address: str) -> Optional[ThreatIndicator]:
        """Check IP address reputation."""
        if not self.config.check_ips:
            return None

        # Check cache first
        cache_key = f"ip:{ip_address}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Validate IP format
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return None

        # Rate limit check
        if not await self._check_rate_limit():
            return None

        # Check each source
        scores = []
        metadata = {}

        if self.config.virustotal_api_key:
            vt_score = await self._check_ip_virustotal(ip_address)
            if vt_score is not None:
                scores.append(vt_score)
                metadata["virustotal"] = vt_score

        if self.config.abuseipdb_api_key:
            abuse_score = await self._check_ip_abuseipdb(ip_address)
            if abuse_score is not None:
                scores.append(abuse_score)
                metadata["abuseipdb"] = abuse_score

        if not scores:
            return None

        # Calculate average score
        avg_score = sum(scores) / len(scores)

        if avg_score >= self.config.min_reputation_score:
            indicator = ThreatIndicator(
                indicator_type="ip",
                value=ip_address,
                source="multiple",
                severity=self._score_to_severity(avg_score),
                confidence=avg_score,
                metadata=metadata
            )

            # Cache the result
            self.cache[cache_key] = indicator
            return indicator

        return None

    async def check_domain(self, domain: str) -> Optional[ThreatIndicator]:
        """Check domain reputation."""
        if not self.config.check_domains:
            return None

        # Check cache first
        cache_key = f"domain:{domain}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Rate limit check
        if not await self._check_rate_limit():
            return None

        # Check each source
        scores = []
        metadata = {}

        if self.config.virustotal_api_key:
            vt_score = await self._check_domain_virustotal(domain)
            if vt_score is not None:
                scores.append(vt_score)
                metadata["virustotal"] = vt_score

        if not scores:
            return None

        # Calculate average score
        avg_score = sum(scores) / len(scores)

        if avg_score >= self.config.min_reputation_score:
            indicator = ThreatIndicator(
                indicator_type="domain",
                value=domain,
                source="multiple",
                severity=self._score_to_severity(avg_score),
                confidence=avg_score,
                metadata=metadata
            )

            # Cache the result
            self.cache[cache_key] = indicator
            return indicator

        return None

    async def check_hash(self, file_hash: str) -> Optional[ThreatIndicator]:
        """Check file hash reputation."""
        if not self.config.check_hashes:
            return None

        # Check cache first
        cache_key = f"hash:{file_hash}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Rate limit check
        if not await self._check_rate_limit():
            return None

        # Check each source
        scores = []
        metadata = {}

        if self.config.virustotal_api_key:
            vt_score = await self._check_hash_virustotal(file_hash)
            if vt_score is not None:
                scores.append(vt_score)
                metadata["virustotal"] = vt_score

        if not scores:
            return None

        # Calculate average score
        avg_score = sum(scores) / len(scores)

        if avg_score >= self.config.min_reputation_score:
            indicator = ThreatIndicator(
                indicator_type="hash",
                value=file_hash,
                source="multiple",
                severity=self._score_to_severity(avg_score),
                confidence=avg_score,
                metadata=metadata
            )

            # Cache the result
            self.cache[cache_key] = indicator
            return indicator

        return None

    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.utcnow()

        # Clean old request times
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Check limit
        if len(self.request_times) >= self.config.requests_per_minute:
            return False

        # Record this request
        self.request_times.append(now)
        return True

    async def _check_ip_virustotal(self, ip_address: str) -> Optional[float]:
        """Check IP reputation on VirusTotal."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                data = await response.json()

                # Calculate score based on malicious detections
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())

                if total > 0:
                    return malicious / total

        except Exception as e:
            logger.error(f"VirusTotal IP check failed: {e}")

        return None

    async def _check_ip_abuseipdb(self, ip_address: str) -> Optional[float]:
        """Check IP reputation on AbuseIPDB."""
        try:
            headers = {"Key": self.config.abuseipdb_api_key}
            url = "https://api.abuseipdb.com/api/v2/check"
            params = {"ipAddress": ip_address, "maxAgeInDays": 90}

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()

                # Use abuse confidence score (0-100)
                score = data.get("data", {}).get("abuseConfidenceScore", 0)
                return score / 100.0

        except Exception as e:
            logger.error(f"AbuseIPDB check failed: {e}")

        return None

    async def _check_domain_virustotal(self, domain: str) -> Optional[float]:
        """Check domain reputation on VirusTotal."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = f"https://www.virustotal.com/api/v3/domains/{domain}"

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                data = await response.json()

                # Calculate score based on malicious detections
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())

                if total > 0:
                    return malicious / total

        except Exception as e:
            logger.error(f"VirusTotal domain check failed: {e}")

        return None

    async def _check_hash_virustotal(self, file_hash: str) -> Optional[float]:
        """Check file hash reputation on VirusTotal."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = f"https://www.virustotal.com/api/v3/files/{file_hash}"

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                data = await response.json()

                # Calculate score based on malicious detections
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())

                if total > 0:
                    return malicious / total

        except Exception as e:
            logger.error(f"VirusTotal hash check failed: {e}")

        return None

    async def _collect_virustotal(self) -> List[ThreatIndicator]:
        """Collect recent threat indicators from VirusTotal (if available)."""
        # In Phase 1, we only check specific indicators, not collect in bulk
        return []

    async def _collect_abuseipdb(self) -> List[ThreatIndicator]:
        """Collect recent threat indicators from AbuseIPDB."""
        # In Phase 1, we only check specific indicators, not collect in bulk
        return []

    async def _collect_alienvault(self) -> List[ThreatIndicator]:
        """Collect recent threat indicators from AlienVault OTX."""
        indicators = []

        try:
            headers = {"X-OTX-API-KEY": self.config.alienvault_api_key}
            url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
            params = {"limit": 10, "page": 1}

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return indicators

                data = await response.json()

                for pulse in data.get("results", [])[:5]:  # Limit to 5 pulses
                    for indicator in pulse.get("indicators", [])[:10]:  # Limit indicators
                        ind = ThreatIndicator(
                            indicator_type=indicator.get("type", "unknown"),
                            value=indicator.get("indicator", ""),
                            source="alienvault",
                            severity="medium",
                            confidence=0.7,
                            tags=pulse.get("tags", []),
                            metadata={
                                "pulse_name": pulse.get("name"),
                                "pulse_id": pulse.get("id")
                            }
                        )
                        indicators.append(ind)

        except Exception as e:
            logger.error(f"AlienVault collection failed: {e}")

        return indicators

    async def _collect_misp(self) -> List[ThreatIndicator]:
        """Collect recent threat indicators from MISP."""
        indicators = []

        try:
            headers = {
                "Authorization": self.config.misp_api_key,
                "Accept": "application/json"
            }

            # Get recent events
            url = f"{self.config.misp_url}/events/index"
            params = {"limit": 10, "published": 1}

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return indicators

                data = await response.json()

                for event in data[:5]:  # Limit to 5 events
                    event_id = event.get("Event", {}).get("id")
                    if not event_id:
                        continue

                    # Get event details
                    detail_url = f"{self.config.misp_url}/events/view/{event_id}"

                    async with self.session.get(detail_url, headers=headers) as detail_response:
                        if detail_response.status != 200:
                            continue

                        event_data = await detail_response.json()

                        for attribute in event_data.get("Event", {}).get("Attribute", [])[:10]:
                            ind = ThreatIndicator(
                                indicator_type=attribute.get("type", "unknown"),
                                value=attribute.get("value", ""),
                                source="misp",
                                severity="high",
                                confidence=0.8,
                                tags=[attribute.get("category", "")],
                                metadata={
                                    "event_id": event_id,
                                    "event_info": event_data.get("Event", {}).get("info")
                                }
                            )
                            indicators.append(ind)

        except Exception as e:
            logger.error(f"MISP collection failed: {e}")

        return indicators

    async def _should_report(self, indicator: ThreatIndicator) -> bool:
        """Check if indicator should be reported."""
        # Skip if in false positives
        if indicator.value in self.false_positives:
            return False

        # Check confidence threshold
        if indicator.confidence < self.config.min_reputation_score:
            return False

        return True

    def _indicator_to_event(self, indicator: ThreatIndicator) -> CollectedEvent:
        """Convert threat indicator to collected event."""
        return CollectedEvent(
            collector_type="ThreatIntelligence",
            source=f"threatintel:{indicator.source}",
            severity=indicator.severity,
            raw_data={
                "indicator": indicator.value,
                "type": indicator.indicator_type,
                "confidence": indicator.confidence
            },
            parsed_data={
                "indicator_type": indicator.indicator_type,
                "indicator_value": indicator.value,
                "confidence": indicator.confidence,
                "source": indicator.source,
                "metadata": indicator.metadata
            },
            tags=[
                f"type:{indicator.indicator_type}",
                f"source:{indicator.source}",
                f"confidence:{indicator.confidence:.2f}",
                *indicator.tags
            ]
        )

    def _score_to_severity(self, score: float) -> str:
        """Convert reputation score to severity level."""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"

    def _clean_cache(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.config.cache_ttl_minutes)

        expired_keys = []
        for key, indicator in self.cache.items():
            # Handle both ThreatIndicator objects and dict entries
            if isinstance(indicator, ThreatIndicator):
                if indicator.last_seen < cutoff:
                    expired_keys.append(key)
            elif isinstance(indicator, dict):
                # Handle dict entries (for testing compatibility)
                timestamp = indicator.get("timestamp") or indicator.get("last_seen")
                if timestamp and timestamp < cutoff:
                    expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

    async def cleanup(self) -> None:
        """Clean up collector resources."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Cleaned up Threat Intelligence Collector")