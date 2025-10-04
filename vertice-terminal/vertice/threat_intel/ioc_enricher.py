"""
🔍 IOC Enrichment Engine - Enriquecimento de indicadores de compromisso

Enriquece IOCs com contexto adicional de múltiplas fontes:
- VirusTotal (malware analysis, reputation)
- AbuseIPDB (IP reputation)
- Shodan (IP infrastructure)
- URLscan.io (URL analysis)
- Hybrid Analysis (malware sandbox)
- PassiveTotal/RiskIQ (passive DNS)
- GreyNoise (internet scanner detection)

IOC Types:
- IP addresses
- Domains
- URLs
- File hashes (MD5, SHA1, SHA256)
- Email addresses
- CVEs
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IOCType(Enum):
    """Tipos de IOC"""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH_MD5 = "file_hash_md5"
    FILE_HASH_SHA1 = "file_hash_sha1"
    FILE_HASH_SHA256 = "file_hash_sha256"
    EMAIL = "email"
    CVE = "cve"
    MUTEX = "mutex"
    REGISTRY_KEY = "registry_key"


class ThreatLevel(Enum):
    """Nível de ameaça"""
    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class IOC:
    """
    Indicator of Compromise

    Attributes:
        value: IOC value (IP, domain, hash, etc)
        ioc_type: Type of IOC
        threat_level: Threat level assessment
        confidence: Confidence score (0-100)
        first_seen: First time seen
        last_seen: Last time seen
        tags: Classification tags
        sources: Sources that reported this IOC
        metadata: Additional metadata
    """
    value: str
    ioc_type: IOCType
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    confidence: int = 0  # 0-100

    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)

    # Classification
    tags: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    # Context
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Related IOCs
    related_iocs: List[str] = field(default_factory=list)


@dataclass
class EnrichmentResult:
    """
    Resultado de enrichment de IOC

    Attributes:
        ioc: IOC original
        enriched: If enrichment was successful
        enrichment_sources: Sources used for enrichment
        threat_level: Assessed threat level
        confidence: Overall confidence
        verdicts: Verdicts from different sources
        context: Enrichment context data
        enriched_at: When enrichment happened
    """
    ioc: IOC
    enriched: bool
    enrichment_sources: List[str] = field(default_factory=list)

    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    confidence: int = 0

    # Verdicts from sources
    verdicts: Dict[str, str] = field(default_factory=dict)

    # Enrichment context
    context: Dict[str, Any] = field(default_factory=dict)

    enriched_at: datetime = field(default_factory=datetime.now)


class IOCEnricher:
    """
    IOC Enrichment System

    Features:
    - Multi-source enrichment
    - Automatic API rotation
    - Caching for performance
    - Confidence scoring
    - Threat level assessment
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        virustotal_api_key: Optional[str] = None,
        abuseipdb_api_key: Optional[str] = None,
        shodan_api_key: Optional[str] = None,
    ):
        """
        Args:
            backend_url: URL do enrichment_service
            use_backend: Se True, usa backend
            virustotal_api_key: VirusTotal API key
            abuseipdb_api_key: AbuseIPDB API key
            shodan_api_key: Shodan API key
        """
        self.backend_url = backend_url or "http://localhost:8019"
        self.use_backend = use_backend

        # API keys
        self.virustotal_api_key = virustotal_api_key
        self.abuseipdb_api_key = abuseipdb_api_key
        self.shodan_api_key = shodan_api_key

        # Enrichment cache
        self.cache: Dict[str, EnrichmentResult] = {}

    def enrich(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        use_cache: bool = True,
    ) -> EnrichmentResult:
        """
        Enriquece IOC com contexto de múltiplas fontes

        Args:
            ioc_value: IOC value
            ioc_type: IOC type
            use_cache: Use cached result if available

        Returns:
            EnrichmentResult
        """
        # Check cache
        if use_cache and ioc_value in self.cache:
            logger.debug(f"Using cached enrichment for: {ioc_value}")
            return self.cache[ioc_value]

        # Create IOC object
        ioc = IOC(value=ioc_value, ioc_type=ioc_type)

        logger.info(f"Enriching IOC: {ioc_value} ({ioc_type.value})")

        # Enrich based on type
        if ioc_type == IOCType.IP_ADDRESS:
            result = self._enrich_ip(ioc)

        elif ioc_type == IOCType.DOMAIN:
            result = self._enrich_domain(ioc)

        elif ioc_type == IOCType.URL:
            result = self._enrich_url(ioc)

        elif ioc_type in [
            IOCType.FILE_HASH_MD5,
            IOCType.FILE_HASH_SHA1,
            IOCType.FILE_HASH_SHA256,
        ]:
            result = self._enrich_file_hash(ioc)

        else:
            logger.warning(f"IOC type not supported for enrichment: {ioc_type.value}")
            result = EnrichmentResult(ioc=ioc, enriched=False)

        # Cache result
        self.cache[ioc_value] = result

        return result

    def _enrich_ip(self, ioc: IOC) -> EnrichmentResult:
        """Enriquece IP address"""
        result = EnrichmentResult(ioc=ioc, enriched=False)

        # VirusTotal IP report
        if self.virustotal_api_key:
            try:
                vt_data = self._virustotal_ip_lookup(ioc.value)

                if vt_data:
                    result.enriched = True
                    result.enrichment_sources.append("VirusTotal")

                    # Parse VirusTotal response
                    malicious_count = vt_data.get("malicious", 0)
                    total_count = vt_data.get("total", 0)

                    if total_count > 0:
                        malicious_ratio = malicious_count / total_count

                        if malicious_ratio > 0.1:
                            result.threat_level = ThreatLevel.MALICIOUS
                            result.confidence = min(int(malicious_ratio * 100), 100)
                        elif malicious_ratio > 0:
                            result.threat_level = ThreatLevel.SUSPICIOUS
                            result.confidence = 50
                        else:
                            result.threat_level = ThreatLevel.BENIGN
                            result.confidence = 80

                    result.verdicts["virustotal"] = f"{malicious_count}/{total_count} malicious"
                    result.context["virustotal"] = vt_data

            except Exception as e:
                logger.error(f"VirusTotal IP lookup failed: {e}")

        # AbuseIPDB lookup
        if self.abuseipdb_api_key:
            try:
                abuseipdb_data = self._abuseipdb_lookup(ioc.value)

                if abuseipdb_data:
                    result.enriched = True
                    result.enrichment_sources.append("AbuseIPDB")

                    abuse_score = abuseipdb_data.get("abuseConfidenceScore", 0)

                    if abuse_score > 75:
                        result.threat_level = ThreatLevel.MALICIOUS
                        result.confidence = max(result.confidence, abuse_score)
                    elif abuse_score > 25:
                        result.threat_level = ThreatLevel.SUSPICIOUS
                        result.confidence = max(result.confidence, abuse_score)

                    result.verdicts["abuseipdb"] = f"Abuse score: {abuse_score}%"
                    result.context["abuseipdb"] = abuseipdb_data

            except Exception as e:
                logger.error(f"AbuseIPDB lookup failed: {e}")

        # Shodan lookup
        if self.shodan_api_key:
            try:
                shodan_data = self._shodan_lookup(ioc.value)

                if shodan_data:
                    result.enriched = True
                    result.enrichment_sources.append("Shodan")

                    result.context["shodan"] = shodan_data
                    result.verdicts["shodan"] = f"Open ports: {len(shodan_data.get('ports', []))}"

            except Exception as e:
                logger.error(f"Shodan lookup failed: {e}")

        return result

    def _enrich_domain(self, ioc: IOC) -> EnrichmentResult:
        """Enriquece domain"""
        result = EnrichmentResult(ioc=ioc, enriched=False)

        # VirusTotal domain report
        if self.virustotal_api_key:
            try:
                vt_data = self._virustotal_domain_lookup(ioc.value)

                if vt_data:
                    result.enriched = True
                    result.enrichment_sources.append("VirusTotal")

                    malicious_count = vt_data.get("malicious", 0)
                    total_count = vt_data.get("total", 0)

                    if total_count > 0:
                        malicious_ratio = malicious_count / total_count

                        if malicious_ratio > 0.1:
                            result.threat_level = ThreatLevel.MALICIOUS
                            result.confidence = min(int(malicious_ratio * 100), 100)
                        else:
                            result.threat_level = ThreatLevel.BENIGN
                            result.confidence = 70

                    result.verdicts["virustotal"] = f"{malicious_count}/{total_count} malicious"
                    result.context["virustotal"] = vt_data

            except Exception as e:
                logger.error(f"VirusTotal domain lookup failed: {e}")

        return result

    def _enrich_url(self, ioc: IOC) -> EnrichmentResult:
        """Enriquece URL"""
        result = EnrichmentResult(ioc=ioc, enriched=False)

        # VirusTotal URL report
        if self.virustotal_api_key:
            try:
                vt_data = self._virustotal_url_lookup(ioc.value)

                if vt_data:
                    result.enriched = True
                    result.enrichment_sources.append("VirusTotal")

                    malicious_count = vt_data.get("malicious", 0)
                    total_count = vt_data.get("total", 0)

                    if total_count > 0:
                        malicious_ratio = malicious_count / total_count

                        if malicious_ratio > 0.1:
                            result.threat_level = ThreatLevel.MALICIOUS
                            result.confidence = min(int(malicious_ratio * 100), 100)

                    result.verdicts["virustotal"] = f"{malicious_count}/{total_count} malicious"
                    result.context["virustotal"] = vt_data

            except Exception as e:
                logger.error(f"VirusTotal URL lookup failed: {e}")

        return result

    def _enrich_file_hash(self, ioc: IOC) -> EnrichmentResult:
        """Enriquece file hash"""
        result = EnrichmentResult(ioc=ioc, enriched=False)

        # VirusTotal file report
        if self.virustotal_api_key:
            try:
                vt_data = self._virustotal_file_lookup(ioc.value)

                if vt_data:
                    result.enriched = True
                    result.enrichment_sources.append("VirusTotal")

                    malicious_count = vt_data.get("malicious", 0)
                    total_count = vt_data.get("total", 0)

                    if total_count > 0:
                        malicious_ratio = malicious_count / total_count

                        if malicious_ratio > 0.3:
                            result.threat_level = ThreatLevel.MALICIOUS
                            result.confidence = min(int(malicious_ratio * 100), 100)
                        elif malicious_ratio > 0:
                            result.threat_level = ThreatLevel.SUSPICIOUS
                            result.confidence = 60

                    result.verdicts["virustotal"] = f"{malicious_count}/{total_count} detected"
                    result.context["virustotal"] = vt_data

            except Exception as e:
                logger.error(f"VirusTotal file lookup failed: {e}")

        return result

    # ==================== API Integrations ====================

    def _virustotal_ip_lookup(self, ip: str) -> Optional[Dict[str, Any]]:
        """VirusTotal IP lookup"""
        import httpx

        try:
            headers = {"x-apikey": self.virustotal_api_key}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()

                # Parse last_analysis_stats
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})

                return {
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "total": sum(stats.values()),
                }

        except Exception as e:
            logger.error(f"VirusTotal IP lookup error: {e}")
            return None

    def _virustotal_domain_lookup(self, domain: str) -> Optional[Dict[str, Any]]:
        """VirusTotal domain lookup"""
        import httpx

        try:
            headers = {"x-apikey": self.virustotal_api_key}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"https://www.virustotal.com/api/v3/domains/{domain}",
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()

                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})

                return {
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "total": sum(stats.values()),
                }

        except Exception as e:
            logger.error(f"VirusTotal domain lookup error: {e}")
            return None

    def _virustotal_url_lookup(self, url: str) -> Optional[Dict[str, Any]]:
        """VirusTotal URL lookup"""
        import httpx
        import base64

        try:
            # URL ID is base64 without padding
            url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")

            headers = {"x-apikey": self.virustotal_api_key}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"https://www.virustotal.com/api/v3/urls/{url_id}",
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()

                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})

                return {
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "total": sum(stats.values()),
                }

        except Exception as e:
            logger.error(f"VirusTotal URL lookup error: {e}")
            return None

    def _virustotal_file_lookup(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """VirusTotal file lookup"""
        import httpx

        try:
            headers = {"x-apikey": self.virustotal_api_key}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"https://www.virustotal.com/api/v3/files/{file_hash}",
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()

                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})

                return {
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "undetected": stats.get("undetected", 0),
                    "total": sum(stats.values()),
                }

        except Exception as e:
            logger.error(f"VirusTotal file lookup error: {e}")
            return None

    def _abuseipdb_lookup(self, ip: str) -> Optional[Dict[str, Any]]:
        """AbuseIPDB lookup"""
        import httpx

        try:
            headers = {"Key": self.abuseipdb_api_key}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    headers=headers,
                    params={"ipAddress": ip, "maxAgeInDays": 90}
                )
                response.raise_for_status()

                data = response.json()

                return data.get("data", {})

        except Exception as e:
            logger.error(f"AbuseIPDB lookup error: {e}")
            return None

    def _shodan_lookup(self, ip: str) -> Optional[Dict[str, Any]]:
        """Shodan lookup"""
        import httpx

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"https://api.shodan.io/shodan/host/{ip}",
                    params={"key": self.shodan_api_key}
                )
                response.raise_for_status()

                return response.json()

        except Exception as e:
            logger.error(f"Shodan lookup error: {e}")
            return None

    def bulk_enrich(
        self,
        iocs: List[tuple[str, IOCType]],
    ) -> List[EnrichmentResult]:
        """
        Enriquece múltiplos IOCs em batch

        Args:
            iocs: List of (ioc_value, ioc_type) tuples

        Returns:
            List of EnrichmentResult
        """
        results = []

        for ioc_value, ioc_type in iocs:
            result = self.enrich(ioc_value, ioc_type)
            results.append(result)

        logger.info(f"Bulk enrichment completed: {len(results)} IOCs")

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de enrichment"""
        enriched = len([r for r in self.cache.values() if r.enriched])

        by_threat_level = {}
        for result in self.cache.values():
            level = result.threat_level.value
            by_threat_level[level] = by_threat_level.get(level, 0) + 1

        return {
            "total_cached": len(self.cache),
            "enriched": enriched,
            "by_threat_level": by_threat_level,
        }
