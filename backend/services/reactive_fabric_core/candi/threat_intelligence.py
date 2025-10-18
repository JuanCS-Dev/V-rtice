"""
Threat Intelligence
Integration with MISP and threat intelligence feeds
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .forensic_analyzer import ForensicReport

logger = logging.getLogger(__name__)

@dataclass
class ThreatIntelReport:
    """Threat intelligence correlation report"""
    event_id: str
    timestamp: datetime

    # Matched intelligence
    known_iocs: List[str] = field(default_factory=list)
    known_tools: List[str] = field(default_factory=list)
    known_exploits: List[str] = field(default_factory=list)
    related_campaigns: List[str] = field(default_factory=list)

    # IOC enrichment
    related_iocs: List[str] = field(default_factory=list)
    ioc_reputation: Dict[str, str] = field(default_factory=dict)  # IOC -> reputation

    # Threat context
    threat_tags: List[str] = field(default_factory=list)
    threat_score: float = 0.0  # 0-100
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    # MISP events
    misp_events: List[Dict] = field(default_factory=list)

    # Metadata
    intelligence_sources: List[str] = field(default_factory=list)
    correlation_confidence: float = 0.0  # 0-100%


class ThreatIntelligence:
    """
    Threat intelligence correlation engine

    Intelligence Sources:
    1. MISP Platform (Malware Information Sharing Platform)
    2. Local IOC database
    3. Threat actor profiles
    4. Campaign tracking
    5. CVE database

    Features:
    - Real-time IOC correlation
    - Threat actor tracking
    - Campaign identification
    - IOC enrichment
    - Threat scoring
    """

    def __init__(self, misp_url: Optional[str] = None, misp_key: Optional[str] = None):
        """
        Initialize threat intelligence engine

        Args:
            misp_url: MISP instance URL
            misp_key: MISP API key
        """
        self._initialized = False

        self.misp_url = misp_url or "http://localhost:8080"
        self.misp_key = misp_key
        self.misp_available = False

        # Local intelligence databases
        self.ioc_database = self._load_ioc_database()
        self.tool_database = self._load_tool_database()
        self.exploit_database = self._load_exploit_database()
        self.campaign_database = self._load_campaign_database()

        # Cache for performance
        self.ioc_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(hours=1)

        # Statistics
        self.stats = {
            "total_correlations": 0,
            "ioc_hits": 0,
            "tool_hits": 0,
            "exploit_hits": 0,
            "campaign_hits": 0,
            "misp_queries": 0
        }

    async def initialize(self):
        """Initialize threat intelligence engine"""
        if self._initialized:
            return

        logger.info("Initializing Threat Intelligence engine...")

        # Test MISP connectivity
        if self.misp_key:
            self.misp_available = await self._test_misp_connection()
            if self.misp_available:
                logger.info("MISP connection established")
            else:
                logger.warning("MISP connection failed, using local intelligence only")
        else:
            logger.info("No MISP credentials provided, using local intelligence only")

        self._initialized = True
        logger.info("Threat Intelligence engine initialized")

    async def correlate(self, forensic: ForensicReport) -> ThreatIntelReport:
        """
        Correlate forensic findings with threat intelligence

        Args:
            forensic: Forensic analysis report

        Returns:
            Threat intelligence report
        """
        logger.info(f"Starting threat intelligence correlation for {forensic.event_id}")

        report = ThreatIntelReport(
            event_id=forensic.event_id,
            timestamp=datetime.now()
        )

        # 1. IOC Correlation
        await self._correlate_iocs(forensic, report)

        # 2. Tool Identification
        await self._correlate_tools(forensic, report)

        # 3. Exploit Correlation
        await self._correlate_exploits(forensic, report)

        # 4. Campaign Tracking
        await self._correlate_campaigns(forensic, report)

        # 5. MISP Query (if available)
        if self.misp_available:
            await self._query_misp(forensic, report)

        # 6. Enrichment - Get related IOCs
        await self._enrich_iocs(report)

        # 7. Calculate threat score
        report.threat_score = self._calculate_threat_score(report, forensic)

        # 8. Determine intelligence sources used
        report.intelligence_sources = self._get_sources_used(report)

        # 9. Calculate correlation confidence
        report.correlation_confidence = self._calculate_confidence(report)

        # Update statistics
        self.stats["total_correlations"] += 1
        if report.known_iocs:
            self.stats["ioc_hits"] += 1
        if report.known_tools:
            self.stats["tool_hits"] += 1
        if report.known_exploits:
            self.stats["exploit_hits"] += 1
        if report.related_campaigns:
            self.stats["campaign_hits"] += 1

        logger.info(
            f"Threat intelligence correlation complete: {forensic.event_id} "
            f"(threat score: {report.threat_score:.1f}/100, "
            f"confidence: {report.correlation_confidence:.1f}%)"
        )

        return report

    async def _correlate_iocs(self, forensic: ForensicReport, report: ThreatIntelReport):
        """Correlate IOCs against threat intelligence"""
        # Check all network IOCs
        for ioc in forensic.network_iocs:
            if ioc in self.ioc_database:
                report.known_iocs.append(ioc)
                intel = self.ioc_database[ioc]

                # Add reputation
                report.ioc_reputation[ioc] = intel.get('reputation', 'unknown')

                # Add threat tags
                for tag in intel.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

                # Track first/last seen
                if 'first_seen' in intel:
                    fs = intel['first_seen']
                    if not report.first_seen or fs < report.first_seen:
                        report.first_seen = fs

                if 'last_seen' in intel:
                    ls = intel['last_seen']
                    if not report.last_seen or ls > report.last_seen:
                        report.last_seen = ls

        # Check file hashes
        for file_hash in forensic.file_hashes:
            ioc_key = f"sha256:{file_hash}"
            if ioc_key in self.ioc_database:
                report.known_iocs.append(ioc_key)
                intel = self.ioc_database[ioc_key]
                report.ioc_reputation[ioc_key] = intel.get('reputation', 'unknown')

    async def _correlate_tools(self, forensic: ForensicReport, report: ThreatIntelReport):
        """Correlate tools and malware families"""
        # Check malware family
        if forensic.malware_family:
            malware_lower = forensic.malware_family.lower()
            if malware_lower in self.tool_database:
                report.known_tools.append(forensic.malware_family)
                tool_intel = self.tool_database[malware_lower]

                # Add threat tags
                for tag in tool_intel.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

        # Check for known tools in commands
        for cmd in forensic.suspicious_commands:
            cmd_lower = cmd.lower()
            for tool_name, tool_info in self.tool_database.items():
                if tool_name in cmd_lower:
                    if tool_name not in report.known_tools:
                        report.known_tools.append(tool_name)

                    for tag in tool_info.get('tags', []):
                        if tag not in report.threat_tags:
                            report.threat_tags.append(tag)

    async def _correlate_exploits(self, forensic: ForensicReport, report: ThreatIntelReport):
        """Correlate exploits with CVE database"""
        for cve in forensic.exploit_cves:
            if cve in self.exploit_database:
                report.known_exploits.append(cve)
                exploit_intel = self.exploit_database[cve]

                # Add threat tags
                for tag in exploit_intel.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

    async def _correlate_campaigns(self, forensic: ForensicReport, report: ThreatIntelReport):
        """Correlate with known threat campaigns"""
        # Check behaviors against campaign signatures
        observed_behaviors = set(forensic.behaviors)

        for campaign_name, campaign_info in self.campaign_database.items():
            campaign_behaviors = set(campaign_info.get('behaviors', []))

            # Check for overlap
            overlap = observed_behaviors & campaign_behaviors
            if len(overlap) >= 2:  # At least 2 matching behaviors
                report.related_campaigns.append(campaign_name)

                # Add campaign tags
                for tag in campaign_info.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

    async def _query_misp(self, forensic: ForensicReport, report: ThreatIntelReport):
        """Query MISP platform for threat intelligence"""
        if not self.misp_available:
            return

        self.stats["misp_queries"] += 1

        try:
            # In production, would use PyMISP library to query MISP
            # For now, simulate MISP query

            # Query by IP
            if forensic.source_ip and forensic.source_ip != 'unknown':
                misp_result = await self._misp_search_ioc(forensic.source_ip)
                if misp_result:
                    report.misp_events.append(misp_result)

            # Query by file hash
            for file_hash in forensic.file_hashes[:3]:  # Limit queries
                misp_result = await self._misp_search_ioc(file_hash)
                if misp_result:
                    report.misp_events.append(misp_result)

        except Exception as e:
            logger.error(f"MISP query error: {e}")

    async def _misp_search_ioc(self, ioc: str) -> Optional[Dict]:
        """
        Search MISP for IOC (simulated)

        In production, would use:
        from pymisp import PyMISP
        misp = PyMISP(self.misp_url, self.misp_key)
        result = misp.search('attributes', value=ioc)
        """
        # Simulate MISP response
        await asyncio.sleep(0.01)  # Simulate network delay

        # Return None for now (would return actual MISP event)
        return None

    async def _enrich_iocs(self, report: ThreatIntelReport):
        """Enrich IOCs with related indicators"""
        # For each known IOC, get related IOCs from intelligence
        for ioc in report.known_iocs:
            if ioc in self.ioc_database:
                intel = self.ioc_database[ioc]
                related = intel.get('related_iocs', [])

                for related_ioc in related:
                    if related_ioc not in report.related_iocs:
                        report.related_iocs.append(related_ioc)

    def _calculate_threat_score(self,
                                report: ThreatIntelReport,
                                forensic: ForensicReport) -> float:
        """
        Calculate overall threat score (0-100)

        Factors:
        - Known malicious IOCs: +30
        - Known tools/malware: +25
        - Known exploits: +20
        - Campaign correlation: +15
        - Forensic sophistication: +10
        """
        score = 0.0

        # Known IOCs
        if report.known_iocs:
            # Check for malicious reputation
            malicious_count = sum(
                1 for rep in report.ioc_reputation.values()
                if rep in ['malicious', 'high_threat']
            )
            if malicious_count:
                score += min(30.0, malicious_count * 10)

        # Known tools
        if report.known_tools:
            score += min(25.0, len(report.known_tools) * 8)

        # Known exploits
        if report.known_exploits:
            score += min(20.0, len(report.known_exploits) * 10)

        # Campaign correlation
        if report.related_campaigns:
            score += min(15.0, len(report.related_campaigns) * 7)

        # Forensic sophistication bonus
        if forensic.sophistication_score >= 7:
            score += 10.0

        return min(score, 100.0)

    def _get_sources_used(self, report: ThreatIntelReport) -> List[str]:
        """Get list of intelligence sources used"""
        sources = ['local_ioc_database']

        if report.known_tools:
            sources.append('tool_database')

        if report.known_exploits:
            sources.append('cve_database')

        if report.related_campaigns:
            sources.append('campaign_database')

        if report.misp_events:
            sources.append('misp_platform')

        return sources

    def _calculate_confidence(self, report: ThreatIntelReport) -> float:
        """Calculate correlation confidence (0-100%)"""
        confidence = 0.0

        # Multiple sources = higher confidence
        confidence += len(report.intelligence_sources) * 10

        # Known IOCs = high confidence
        if report.known_iocs:
            confidence += 30

        # Known tools = high confidence
        if report.known_tools:
            confidence += 25

        # MISP correlation = high confidence
        if report.misp_events:
            confidence += 20

        return min(confidence, 100.0)

    async def _test_misp_connection(self) -> bool:
        """Test MISP connectivity"""
        try:
            # In production, would test actual MISP connection
            # from pymisp import PyMISP
            # misp = PyMISP(self.misp_url, self.misp_key)
            # misp.get_version()
            return False  # No real MISP for now
        except Exception as e:
            logger.warning(f"MISP connection test failed: {e}")
            return False

    def _load_ioc_database(self) -> Dict[str, Dict]:
        """Load local IOC database"""
        # In production, would load from database or file
        return {
            'ip:185.86.148.10': {
                'reputation': 'malicious',
                'tags': ['apt28', 'russia', 'military'],
                'first_seen': datetime.now() - timedelta(days=180),
                'last_seen': datetime.now() - timedelta(days=5),
                'related_iocs': ['ip:185.86.148.11', 'ip:185.86.148.12']
            },
            'ip:45.32.10.15': {
                'reputation': 'suspicious',
                'tags': ['apt29', 'russia', 'intelligence'],
                'first_seen': datetime.now() - timedelta(days=90),
                'last_seen': datetime.now() - timedelta(days=2),
                'related_iocs': ['domain:example-c2.com']
            },
            'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855': {
                'reputation': 'malicious',
                'tags': ['mirai', 'botnet', 'iot'],
                'first_seen': datetime.now() - timedelta(days=365),
                'last_seen': datetime.now() - timedelta(days=10),
                'related_iocs': []
            }
        }

    def _load_tool_database(self) -> Dict[str, Dict]:
        """Load tool/malware database"""
        return {
            'mimikatz': {
                'type': 'credential_dumper',
                'tags': ['credential_access', 'post_exploitation'],
                'severity': 'high'
            },
            'cobalt strike': {
                'type': 'c2_framework',
                'tags': ['apt', 'command_and_control', 'post_exploitation'],
                'severity': 'critical'
            },
            'metasploit': {
                'type': 'exploit_framework',
                'tags': ['exploitation', 'penetration_testing'],
                'severity': 'medium'
            },
            'nmap': {
                'type': 'scanner',
                'tags': ['reconnaissance', 'discovery'],
                'severity': 'low'
            },
            'sqlmap': {
                'type': 'sql_injection_tool',
                'tags': ['web_attack', 'sql_injection'],
                'severity': 'medium'
            },
            'mirai': {
                'type': 'botnet',
                'tags': ['iot', 'ddos', 'malware'],
                'severity': 'high'
            },
            'empire': {
                'type': 'c2_framework',
                'tags': ['post_exploitation', 'powershell'],
                'severity': 'high'
            }
        }

    def _load_exploit_database(self) -> Dict[str, Dict]:
        """Load exploit/CVE database"""
        return {
            'CVE-2021-44228': {
                'name': 'Log4Shell',
                'severity': 'critical',
                'tags': ['java', 'rce', 'widespread'],
                'description': 'Apache Log4j2 RCE vulnerability'
            },
            'CVE-2017-5638': {
                'name': 'Apache Struts2 RCE',
                'severity': 'critical',
                'tags': ['java', 'rce', 'web'],
                'description': 'Apache Struts2 content-type RCE'
            },
            'CVE-2019-0708': {
                'name': 'BlueKeep',
                'severity': 'critical',
                'tags': ['rdp', 'windows', 'wormable'],
                'description': 'Windows RDP RCE vulnerability'
            },
            'CVE-2020-1472': {
                'name': 'Zerologon',
                'severity': 'critical',
                'tags': ['windows', 'domain_controller', 'privilege_escalation'],
                'description': 'Windows Netlogon privilege escalation'
            }
        }

    def _load_campaign_database(self) -> Dict[str, Dict]:
        """Load threat campaign database"""
        return {
            'SolarWinds Supply Chain Attack': {
                'actor': 'APT29',
                'start_date': '2020-03-01',
                'behaviors': [
                    'supply_chain_compromise', 'lateral_movement',
                    'credential_dumping', 'data_exfiltration'
                ],
                'tags': ['apt29', 'supply_chain', 'espionage']
            },
            'NotPetya Ransomware Campaign': {
                'actor': 'Sandworm',
                'start_date': '2017-06-01',
                'behaviors': [
                    'destructive_commands', 'data_destruction',
                    'lateral_movement', 'credential_dumping'
                ],
                'tags': ['sandworm', 'ransomware', 'destructive']
            },
            'Hafnium Exchange Server Attacks': {
                'actor': 'Hafnium',
                'start_date': '2021-01-01',
                'behaviors': [
                    'exploit_attempt', 'web_shell', 'data_exfiltration',
                    'lateral_movement'
                ],
                'tags': ['hafnium', 'exchange', 'china']
            },
            'Emotet Campaign': {
                'actor': 'TA542',
                'start_date': '2014-01-01',
                'behaviors': [
                    'spearphishing', 'malware_upload', 'credential_dumping',
                    'lateral_movement', 'data_exfiltration'
                ],
                'tags': ['emotet', 'banking_trojan', 'botnet']
            }
        }

    def get_stats(self) -> Dict:
        """Get threat intelligence statistics"""
        return {
            **self.stats,
            'misp_available': self.misp_available,
            'ioc_database_size': len(self.ioc_database),
            'tool_database_size': len(self.tool_database),
            'exploit_database_size': len(self.exploit_database),
            'campaign_database_size': len(self.campaign_database)
        }
