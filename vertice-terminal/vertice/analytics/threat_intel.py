"""
🌐 Threat Intelligence Feed - Integração com feeds externos

Integra com:
- MISP (Malware Information Sharing Platform)
- AlienVault OTX (Open Threat Exchange)
- VirusTotal
- AbuseIPDB
- Backend threat_intel_service

Features:
- IOC enrichment
- Threat actor tracking
- Campaign correlation
- Automatic IOC updates
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)


class IOCType(Enum):
    """Tipo de Indicator of Compromise"""
    IP_ADDRESS = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH_MD5 = "md5"
    FILE_HASH_SHA1 = "sha1"
    FILE_HASH_SHA256 = "sha256"
    EMAIL = "email"
    MUTEX = "mutex"
    REGISTRY_KEY = "registry"
    CVE = "cve"


@dataclass
class IOC:
    """
    Indicator of Compromise enriquecido
    """
    value: str
    ioc_type: IOCType
    first_seen: datetime
    last_seen: datetime

    # Threat intelligence
    threat_level: str = "unknown"  # low, medium, high, critical
    confidence: float = 0.0  # 0.0 to 1.0

    # Attribution
    threat_actors: List[str] = field(default_factory=list)
    campaigns: List[str] = field(default_factory=list)
    families: List[str] = field(default_factory=list)  # Malware families

    # Context
    tags: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    # Sources
    sources: List[str] = field(default_factory=list)  # MISP, OTX, VT, etc

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Status
    is_active: bool = True
    is_false_positive: bool = False


@dataclass
class ThreatActor:
    """
    Threat Actor (APT, cybercrime group, etc)
    """
    name: str
    aliases: List[str] = field(default_factory=list)

    # Classification
    type: str = "unknown"  # apt, cybercrime, hacktiv

ist, nation_state
    motivation: str = "unknown"  # financial, espionage, destruction

    # Attribution
    country: Optional[str] = None
    first_seen: Optional[datetime] = None

    # TTPs
    tactics: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    # IOCs associated
    associated_iocs: List[str] = field(default_factory=list)
    campaigns: List[str] = field(default_factory=list)

    # Metadata
    description: str = ""
    references: List[str] = field(default_factory=list)


class ThreatIntelFeed:
    """
    Threat Intelligence Feed Manager

    Features:
    - Integração com múltiplos feeds
    - IOC enrichment
    - Automatic updates
    - Backend caching
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        misp_url: Optional[str] = None,
        misp_key: Optional[str] = None,
        otx_key: Optional[str] = None,
        vt_key: Optional[str] = None,
    ):
        """
        Args:
            backend_url: URL do threat_intel_service
            use_backend: Se True, usa backend para caching
            misp_url: MISP instance URL
            misp_key: MISP API key
            otx_key: AlienVault OTX API key
            vt_key: VirusTotal API key
        """
        self.backend_url = backend_url or "http://localhost:8006"
        self.use_backend = use_backend

        # External feeds config
        self.misp_url = misp_url
        self.misp_key = misp_key
        self.otx_key = otx_key
        self.vt_key = vt_key

        # Cache
        self.ioc_cache: Dict[str, IOC] = {}
        self.threat_actors: Dict[str, ThreatActor] = {}

    def enrich_ioc(self, ioc_value: str, ioc_type: IOCType) -> Optional[IOC]:
        """
        Enriquece IOC com threat intel de múltiplas fontes

        Args:
            ioc_value: IOC value (IP, domain, hash, etc)
            ioc_type: IOC type

        Returns:
            IOC enriquecido ou None
        """
        # Check cache first
        if ioc_value in self.ioc_cache:
            return self.ioc_cache[ioc_value]

        if self.use_backend:
            try:
                return self._enrich_ioc_backend(ioc_value, ioc_type)
            except Exception as e:
                logger.warning(f"Backend enrichment failed, trying direct feeds: {e}")

        # Fallback: query feeds directly
        return self._enrich_ioc_direct(ioc_value, ioc_type)

    def _enrich_ioc_backend(self, ioc_value: str, ioc_type: IOCType) -> Optional[IOC]:
        """
        Enriquece via backend (aggregated intel)

        Args:
            ioc_value: IOC value
            ioc_type: IOC type

        Returns:
            IOC object
        """
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/threat-intel/enrich",
                    json={
                        "ioc": ioc_value,
                        "type": ioc_type.value,
                    }
                )
                response.raise_for_status()

                data = response.json()

                ioc = IOC(
                    value=ioc_value,
                    ioc_type=ioc_type,
                    first_seen=datetime.fromisoformat(data.get("first_seen")),
                    last_seen=datetime.fromisoformat(data.get("last_seen")),
                    threat_level=data.get("threat_level", "unknown"),
                    confidence=data.get("confidence", 0.0),
                    threat_actors=data.get("threat_actors", []),
                    campaigns=data.get("campaigns", []),
                    families=data.get("families", []),
                    tags=data.get("tags", []),
                    mitre_techniques=data.get("mitre_techniques", []),
                    sources=data.get("sources", []),
                    is_active=data.get("is_active", True),
                )

                self.ioc_cache[ioc_value] = ioc

                return ioc

        except Exception as e:
            logger.error(f"Backend IOC enrichment failed: {e}")
            raise

    def _enrich_ioc_direct(self, ioc_value: str, ioc_type: IOCType) -> Optional[IOC]:
        """
        Enriquece consultando feeds diretamente

        Args:
            ioc_value: IOC value
            ioc_type: IOC type

        Returns:
            IOC object
        """
        ioc = IOC(
            value=ioc_value,
            ioc_type=ioc_type,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )

        sources = []

        # Query VirusTotal
        if self.vt_key and ioc_type in [IOCType.FILE_HASH_SHA256, IOCType.IP_ADDRESS, IOCType.DOMAIN]:
            try:
                vt_data = self._query_virustotal(ioc_value, ioc_type)
                if vt_data:
                    ioc.threat_level = vt_data.get("threat_level", "unknown")
                    ioc.tags.extend(vt_data.get("tags", []))
                    sources.append("VirusTotal")
            except Exception as e:
                logger.warning(f"VirusTotal query failed: {e}")

        # Query AlienVault OTX
        if self.otx_key:
            try:
                otx_data = self._query_otx(ioc_value, ioc_type)
                if otx_data:
                    ioc.threat_actors.extend(otx_data.get("threat_actors", []))
                    ioc.campaigns.extend(otx_data.get("campaigns", []))
                    sources.append("AlienVault OTX")
            except Exception as e:
                logger.warning(f"OTX query failed: {e}")

        # Query MISP
        if self.misp_url and self.misp_key:
            try:
                misp_data = self._query_misp(ioc_value, ioc_type)
                if misp_data:
                    ioc.families.extend(misp_data.get("families", []))
                    ioc.mitre_techniques.extend(misp_data.get("mitre", []))
                    sources.append("MISP")
            except Exception as e:
                logger.warning(f"MISP query failed: {e}")

        ioc.sources = sources

        # Cache IOC
        self.ioc_cache[ioc_value] = ioc

        return ioc if sources else None

    def _query_virustotal(self, ioc_value: str, ioc_type: IOCType) -> Optional[Dict[str, Any]]:
        """
        Query VirusTotal API

        Args:
            ioc_value: IOC value
            ioc_type: IOC type

        Returns:
            VT data dict
        """
        if not self.vt_key:
            return None

        try:
            with httpx.Client(timeout=10.0) as client:
                headers = {"x-apikey": self.vt_key}

                # Endpoint depends on IOC type
                if ioc_type == IOCType.FILE_HASH_SHA256:
                    url = f"https://www.virustotal.com/api/v3/files/{ioc_value}"
                elif ioc_type == IOCType.IP_ADDRESS:
                    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc_value}"
                elif ioc_type == IOCType.DOMAIN:
                    url = f"https://www.virustotal.com/api/v3/domains/{ioc_value}"
                else:
                    return None

                response = client.get(url, headers=headers)

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                data = response.json()
                attributes = data.get("data", {}).get("attributes", {})

                # Parse stats
                stats = attributes.get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)

                threat_level = "unknown"
                if malicious > 5:
                    threat_level = "critical"
                elif malicious > 2:
                    threat_level = "high"
                elif suspicious > 3:
                    threat_level = "medium"

                return {
                    "threat_level": threat_level,
                    "tags": attributes.get("tags", []),
                    "reputation": attributes.get("reputation", 0),
                }

        except Exception as e:
            logger.error(f"VirusTotal API error: {e}")
            return None

    def _query_otx(self, ioc_value: str, ioc_type: IOCType) -> Optional[Dict[str, Any]]:
        """
        Query AlienVault OTX API

        Args:
            ioc_value: IOC value
            ioc_type: IOC type

        Returns:
            OTX data dict
        """
        if not self.otx_key:
            return None

        try:
            with httpx.Client(timeout=10.0) as client:
                headers = {"X-OTX-API-KEY": self.otx_key}

                # Endpoint depends on type
                if ioc_type == IOCType.IP_ADDRESS:
                    url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ioc_value}/general"
                elif ioc_type == IOCType.DOMAIN:
                    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{ioc_value}/general"
                elif ioc_type in [IOCType.FILE_HASH_MD5, IOCType.FILE_HASH_SHA1, IOCType.FILE_HASH_SHA256]:
                    url = f"https://otx.alienvault.com/api/v1/indicators/file/{ioc_value}/general"
                else:
                    return None

                response = client.get(url, headers=headers)

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                data = response.json()

                # Parse pulse data
                pulse_info = data.get("pulse_info", {})
                pulses = pulse_info.get("pulses", [])

                threat_actors = []
                campaigns = []

                for pulse in pulses:
                    tags = pulse.get("tags", [])

                    # Extract threat actors and campaigns from tags
                    for tag in tags:
                        if "apt" in tag.lower() or "group" in tag.lower():
                            threat_actors.append(tag)
                        elif "campaign" in tag.lower() or "operation" in tag.lower():
                            campaigns.append(tag)

                return {
                    "threat_actors": list(set(threat_actors)),
                    "campaigns": list(set(campaigns)),
                }

        except Exception as e:
            logger.error(f"OTX API error: {e}")
            return None

    def _query_misp(self, ioc_value: str, ioc_type: IOCType) -> Optional[Dict[str, Any]]:
        """
        Query MISP instance

        Args:
            ioc_value: IOC value
            ioc_type: IOC type

        Returns:
            MISP data dict
        """
        if not self.misp_url or not self.misp_key:
            return None

        try:
            with httpx.Client(timeout=10.0) as client:
                headers = {
                    "Authorization": self.misp_key,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }

                url = f"{self.misp_url}/attributes/restSearch"

                payload = {
                    "returnFormat": "json",
                    "value": ioc_value,
                }

                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()

                attributes = data.get("response", {}).get("Attribute", [])

                families = []
                mitre_techniques = []

                for attr in attributes:
                    tags = attr.get("Tag", [])

                    for tag in tags:
                        tag_name = tag.get("name", "")

                        if "mitre-attack" in tag_name:
                            mitre_techniques.append(tag_name)

                        if "malware" in tag_name or "family" in tag_name:
                            families.append(tag_name)

                return {
                    "families": list(set(families)),
                    "mitre": list(set(mitre_techniques)),
                }

        except Exception as e:
            logger.error(f"MISP API error: {e}")
            return None

    def lookup_threat_actor(self, actor_name: str) -> Optional[ThreatActor]:
        """
        Busca informações sobre threat actor

        Args:
            actor_name: Nome do threat actor (APT28, Lazarus, etc)

        Returns:
            ThreatActor object ou None
        """
        # Check cache
        if actor_name in self.threat_actors:
            return self.threat_actors[actor_name]

        if self.use_backend:
            try:
                return self._lookup_threat_actor_backend(actor_name)
            except Exception as e:
                logger.warning(f"Backend lookup failed: {e}")

        # TODO: Query external sources (MITRE ATT&CK, MISP, OTX)
        return None

    def _lookup_threat_actor_backend(self, actor_name: str) -> Optional[ThreatActor]:
        """
        Lookup threat actor via backend

        Args:
            actor_name: Actor name

        Returns:
            ThreatActor object
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.backend_url}/api/threat-intel/actors/{actor_name}"
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                data = response.json()

                actor = ThreatActor(
                    name=actor_name,
                    aliases=data.get("aliases", []),
                    type=data.get("type", "unknown"),
                    motivation=data.get("motivation", "unknown"),
                    country=data.get("country"),
                    tactics=data.get("tactics", []),
                    techniques=data.get("techniques", []),
                    tools=data.get("tools", []),
                    campaigns=data.get("campaigns", []),
                    description=data.get("description", ""),
                    references=data.get("references", []),
                )

                self.threat_actors[actor_name] = actor

                return actor

        except Exception as e:
            logger.error(f"Backend threat actor lookup failed: {e}")
            raise

    def get_cached_iocs(
        self,
        ioc_type: Optional[IOCType] = None,
        threat_level: Optional[str] = None,
        is_active: bool = True,
    ) -> List[IOC]:
        """
        Retorna IOCs do cache com filtros

        Args:
            ioc_type: Filter by type
            threat_level: Filter by threat level
            is_active: Filter by active status

        Returns:
            List of IOC
        """
        iocs = list(self.ioc_cache.values())

        if ioc_type:
            iocs = [i for i in iocs if i.ioc_type == ioc_type]

        if threat_level:
            iocs = [i for i in iocs if i.threat_level == threat_level]

        if is_active is not None:
            iocs = [i for i in iocs if i.is_active == is_active]

        return iocs
