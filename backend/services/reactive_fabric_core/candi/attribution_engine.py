"""
Attribution Engine
ML-powered threat actor identification and attribution scoring
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from .forensic_analyzer import ForensicReport
from .threat_intelligence import ThreatIntelReport

logger = logging.getLogger(__name__)

@dataclass
class AttributionResult:
    """Attribution analysis result"""
    attributed_actor: Optional[str] = None
    confidence: float = 0.0  # 0-100%

    # Evidence
    matching_ttps: List[str] = field(default_factory=list)
    matching_tools: List[str] = field(default_factory=list)
    matching_infrastructure: List[str] = field(default_factory=list)

    # Actor characteristics
    actor_type: str = "unknown"  # nation-state, criminal, hacktivist, script-kiddie
    motivation: Optional[str] = None  # espionage, financial, disruption, testing

    # APT indicators
    apt_indicators: List[str] = field(default_factory=list)

    # Alternative candidates
    alternative_actors: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    confidence_factors: Dict[str, float] = field(default_factory=dict)


class AttributionEngine:
    """
    ML-powered threat actor attribution engine

    Attribution Factors:
    1. TTP Matching - MITRE ATT&CK technique overlap
    2. Tool Usage - Malware families, exploit frameworks
    3. Infrastructure - IP ranges, hosting providers, domains
    4. Targeting - Industry, geography, victim profile
    5. Timing - Time zone patterns, operational hours
    6. Language - Code comments, error messages
    """

    def __init__(self):
        """Initialize attribution engine"""
        self._initialized = False

        # Threat actor database
        self.threat_actors = self._load_threat_actor_database()

        # TTP to actor mapping
        self.ttp_signatures = self._build_ttp_signatures()

        # Tool to actor mapping
        self.tool_signatures = self._build_tool_signatures()

        # Infrastructure intelligence
        self.infrastructure_db = self._load_infrastructure_database()

        # Statistics
        self.stats = {
            "total_attributions": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "apt_detected": 0
        }

    async def initialize(self):
        """Initialize attribution engine with external resources"""
        if self._initialized:
            return

        logger.info("Initializing Attribution Engine...")

        # In production, would load:
        # - Updated threat actor profiles from MISP/CTI feeds
        # - ML models for behavioral clustering
        # - Historical attribution data
        # - Threat intelligence feeds

        self._initialized = True
        logger.info("Attribution Engine initialized")

    async def attribute(self,
                       forensic: ForensicReport,
                       intel: ThreatIntelReport) -> AttributionResult:
        """
        Attribute attack to threat actor

        Args:
            forensic: Forensic analysis report
            intel: Threat intelligence report

        Returns:
            Attribution result with confidence score
        """
        logger.info(f"Starting attribution for event {forensic.event_id}")

        result = AttributionResult()

        # Factor 1: TTP Matching (40% weight)
        ttp_scores = self._score_ttp_overlap(forensic, intel)
        result.confidence_factors['ttp_matching'] = max(ttp_scores.values()) if ttp_scores else 0.0

        # Factor 2: Tool Usage (25% weight)
        tool_scores = self._score_tool_usage(forensic, intel)
        result.confidence_factors['tool_usage'] = max(tool_scores.values()) if tool_scores else 0.0

        # Factor 3: Infrastructure (20% weight)
        infra_scores = self._score_infrastructure(forensic, intel)
        result.confidence_factors['infrastructure'] = max(infra_scores.values()) if infra_scores else 0.0

        # Factor 4: Sophistication Level (15% weight)
        sophistication_scores = self._score_sophistication(forensic)
        result.confidence_factors['sophistication'] = max(sophistication_scores.values()) if sophistication_scores else 0.0

        # Aggregate scores across all actors
        actor_scores = self._aggregate_scores(
            ttp_scores,
            tool_scores,
            infra_scores,
            sophistication_scores
        )

        # Select best candidate
        if actor_scores:
            best_actor = max(actor_scores, key=actor_scores.get)
            result.attributed_actor = best_actor
            result.confidence = actor_scores[best_actor]

            # Get actor details
            actor_profile = self.threat_actors.get(best_actor, {})
            result.actor_type = actor_profile.get('type', 'unknown')
            result.motivation = actor_profile.get('motivation', 'unknown')

            # Build evidence
            result.matching_ttps = self._get_matching_ttps(best_actor, forensic)
            result.matching_tools = self._get_matching_tools(best_actor, forensic, intel)
            result.matching_infrastructure = self._get_matching_infrastructure(best_actor, forensic)

            # Check for APT indicators
            result.apt_indicators = self._detect_apt_indicators(forensic, intel, actor_profile)

            # Get alternative candidates (top 3)
            sorted_actors = sorted(actor_scores.items(), key=lambda x: x[1], reverse=True)
            for actor, score in sorted_actors[1:4]:
                if score > 30.0:  # Only include significant alternatives
                    result.alternative_actors.append({
                        'actor': actor,
                        'confidence': score,
                        'type': self.threat_actors.get(actor, {}).get('type', 'unknown')
                    })

        # Update statistics
        self.stats["total_attributions"] += 1
        if result.confidence >= 70:
            self.stats["high_confidence"] += 1
        elif result.confidence >= 40:
            self.stats["medium_confidence"] += 1
        else:
            self.stats["low_confidence"] += 1

        if result.apt_indicators:
            self.stats["apt_detected"] += 1

        logger.info(
            f"Attribution complete: {result.attributed_actor or 'unknown'} "
            f"(confidence: {result.confidence:.1f}%, type: {result.actor_type})"
        )

        return result

    def _score_ttp_overlap(self,
                          forensic: ForensicReport,
                          intel: ThreatIntelReport) -> Dict[str, float]:
        """Score TTP overlap with known actors"""
        scores = {}

        observed_behaviors = set(forensic.behaviors)

        for actor, signature in self.ttp_signatures.items():
            known_ttps = set(signature['ttps'])

            if not known_ttps:
                continue

            # Calculate Jaccard similarity
            intersection = observed_behaviors & known_ttps
            union = observed_behaviors | known_ttps

            if union:
                similarity = len(intersection) / len(union)
                scores[actor] = similarity * 100.0

        return scores

    def _score_tool_usage(self,
                         forensic: ForensicReport,
                         intel: ThreatIntelReport) -> Dict[str, float]:
        """Score tool usage matching"""
        scores = {}

        # Tools from forensics
        observed_tools = set()
        if forensic.malware_family:
            observed_tools.add(forensic.malware_family.lower())

        # Tools from intel
        for tool in intel.known_tools:
            observed_tools.add(tool.lower())

        if not observed_tools:
            return scores

        for actor, signature in self.tool_signatures.items():
            known_tools = set(t.lower() for t in signature['tools'])

            if not known_tools:
                continue

            # Calculate overlap
            matches = observed_tools & known_tools

            if matches:
                # Score based on number of matches
                score = (len(matches) / len(known_tools)) * 100.0
                scores[actor] = min(score, 100.0)

        return scores

    def _score_infrastructure(self,
                             forensic: ForensicReport,
                             intel: ThreatIntelReport) -> Dict[str, float]:
        """Score infrastructure matching"""
        scores = {}

        source_ip = forensic.source_ip

        if not source_ip or source_ip == 'unknown':
            return scores

        # Check IP against known actor infrastructure
        for actor, infra in self.infrastructure_db.items():
            # Check IP ranges
            for ip_range in infra.get('ip_ranges', []):
                if self._ip_in_range(source_ip, ip_range):
                    scores[actor] = scores.get(actor, 0.0) + 50.0

            # Check ASNs
            if 'asns' in infra:
                # In production, would do actual ASN lookup
                pass

            # Check hosting providers
            if 'hosting_providers' in infra:
                # In production, would check IP hosting provider
                pass

        return scores

    def _score_sophistication(self, forensic: ForensicReport) -> Dict[str, float]:
        """Score sophistication level matching"""
        scores = {}

        sophistication = forensic.sophistication_score

        for actor, profile in self.threat_actors.items():
            expected_sophistication = profile.get('typical_sophistication', 5.0)

            # Score based on how close sophistication matches
            diff = abs(sophistication - expected_sophistication)

            # Convert to score (0-10 diff mapped to 0-100 score)
            score = max(0, 100 - (diff * 10))
            scores[actor] = score

        return scores

    def _aggregate_scores(self,
                         ttp_scores: Dict[str, float],
                         tool_scores: Dict[str, float],
                         infra_scores: Dict[str, float],
                         sophistication_scores: Dict[str, float]) -> Dict[str, float]:
        """Aggregate scores with weighted average"""
        weights = {
            'ttp': 0.40,
            'tool': 0.25,
            'infra': 0.20,
            'sophistication': 0.15
        }

        # Get all unique actors
        all_actors = set()
        all_actors.update(ttp_scores.keys())
        all_actors.update(tool_scores.keys())
        all_actors.update(infra_scores.keys())
        all_actors.update(sophistication_scores.keys())

        final_scores = {}

        for actor in all_actors:
            score = 0.0

            score += ttp_scores.get(actor, 0.0) * weights['ttp']
            score += tool_scores.get(actor, 0.0) * weights['tool']
            score += infra_scores.get(actor, 0.0) * weights['infra']
            score += sophistication_scores.get(actor, 0.0) * weights['sophistication']

            final_scores[actor] = score

        return final_scores

    def _get_matching_ttps(self, actor: str, forensic: ForensicReport) -> List[str]:
        """Get TTPs that match the attributed actor"""
        matches = []

        if actor in self.ttp_signatures:
            known_ttps = set(self.ttp_signatures[actor]['ttps'])
            observed = set(forensic.behaviors)

            matches = list(known_ttps & observed)

        return matches

    def _get_matching_tools(self,
                           actor: str,
                           forensic: ForensicReport,
                           intel: ThreatIntelReport) -> List[str]:
        """Get tools that match the attributed actor"""
        matches = []

        if actor in self.tool_signatures:
            known_tools = set(t.lower() for t in self.tool_signatures[actor]['tools'])

            if forensic.malware_family and forensic.malware_family.lower() in known_tools:
                matches.append(forensic.malware_family)

            for tool in intel.known_tools:
                if tool.lower() in known_tools:
                    matches.append(tool)

        return matches

    def _get_matching_infrastructure(self, actor: str, forensic: ForensicReport) -> List[str]:
        """Get infrastructure that matches the attributed actor"""
        matches = []

        source_ip = forensic.source_ip

        if actor in self.infrastructure_db and source_ip != 'unknown':
            infra = self.infrastructure_db[actor]

            for ip_range in infra.get('ip_ranges', []):
                if self._ip_in_range(source_ip, ip_range):
                    matches.append(f"IP in known range: {ip_range}")

        return matches

    def _detect_apt_indicators(self,
                               forensic: ForensicReport,
                               intel: ThreatIntelReport,
                               actor_profile: Dict) -> List[str]:
        """Detect APT-specific indicators"""
        indicators = []

        # APT indicator: High sophistication
        if forensic.sophistication_score >= 7:
            indicators.append("High sophistication score")

        # APT indicator: Multi-stage attack
        if len(set(forensic.attack_stages)) >= 3:
            indicators.append("Multi-stage attack chain")

        # APT indicator: Custom malware
        if forensic.malware_family and 'custom' in forensic.malware_family.lower():
            indicators.append("Custom malware detected")

        # APT indicator: Known APT tools
        apt_tools = ['mimikatz', 'cobalt strike', 'metasploit', 'empire', 'covenant']
        for tool in intel.known_tools:
            if any(apt_tool in tool.lower() for apt_tool in apt_tools):
                indicators.append(f"APT tool detected: {tool}")

        # APT indicator: Actor type is nation-state
        if actor_profile.get('type') == 'nation_state':
            indicators.append("Attributed to nation-state actor")

        # APT indicator: Persistence mechanisms
        if 'persistence' in forensic.attack_stages:
            indicators.append("Persistence mechanisms deployed")

        # APT indicator: Lateral movement
        if 'lateral_movement' in forensic.behaviors:
            indicators.append("Lateral movement attempted")

        return indicators

    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP is in range (simplified)"""
        # In production, would use proper IP range checking (ipaddress module)
        # For now, just check prefix
        if '/' in ip_range:
            prefix = ip_range.split('/')[0].rsplit('.', 1)[0]
            return ip.startswith(prefix)
        return ip == ip_range

    def _load_threat_actor_database(self) -> Dict[str, Dict]:
        """Load threat actor profiles"""
        # In production, this would load from MISP, threat intel feeds, etc.
        return {
            'APT28': {
                'type': 'nation_state',
                'motivation': 'espionage',
                'typical_sophistication': 8.5,
                'description': 'Russian military intelligence (GRU)',
                'aliases': ['Fancy Bear', 'Sofacy', 'Pawn Storm']
            },
            'APT29': {
                'type': 'nation_state',
                'motivation': 'espionage',
                'typical_sophistication': 9.0,
                'description': 'Russian foreign intelligence (SVR)',
                'aliases': ['Cozy Bear', 'The Dukes']
            },
            'Lazarus Group': {
                'type': 'nation_state',
                'motivation': 'financial',
                'typical_sophistication': 8.0,
                'description': 'North Korean state-sponsored',
                'aliases': ['Hidden Cobra', 'Guardians of Peace']
            },
            'APT41': {
                'type': 'nation_state',
                'motivation': 'espionage',
                'typical_sophistication': 8.5,
                'description': 'Chinese state-sponsored',
                'aliases': ['Double Dragon', 'Barium']
            },
            'FIN7': {
                'type': 'criminal',
                'motivation': 'financial',
                'typical_sophistication': 7.5,
                'description': 'Cybercriminal group targeting financial sector',
                'aliases': ['Carbanak']
            },
            'Anonymous': {
                'type': 'hacktivist',
                'motivation': 'disruption',
                'typical_sophistication': 5.0,
                'description': 'Decentralized hacktivist collective',
                'aliases': []
            },
            'Script Kiddie': {
                'type': 'script_kiddie',
                'motivation': 'testing',
                'typical_sophistication': 2.0,
                'description': 'Unskilled attacker using existing tools',
                'aliases': []
            },
            'Opportunistic Scanner': {
                'type': 'automated',
                'motivation': 'discovery',
                'typical_sophistication': 1.0,
                'description': 'Automated scanning and exploitation',
                'aliases': []
            }
        }

    def _build_ttp_signatures(self) -> Dict[str, Dict]:
        """Build TTP signatures for each actor"""
        return {
            'APT28': {
                'ttps': [
                    'spearphishing', 'credential_dumping', 'lateral_movement',
                    'persistence', 'defense_evasion', 'data_exfiltration'
                ]
            },
            'APT29': {
                'ttps': [
                    'supply_chain_compromise', 'privilege_escalation',
                    'lateral_movement', 'persistence', 'data_exfiltration',
                    'defense_evasion', 'obfuscation'
                ]
            },
            'Lazarus Group': {
                'ttps': [
                    'spearphishing', 'watering_hole', 'malware_upload',
                    'destructive_commands', 'data_destruction', 'ransomware'
                ]
            },
            'FIN7': {
                'ttps': [
                    'sql_injection', 'credential_dumping', 'data_exfiltration',
                    'point_of_sale_malware', 'financial_data_theft'
                ]
            },
            'Anonymous': {
                'ttps': [
                    'ddos', 'sql_injection', 'xss_attack', 'defacement',
                    'data_leak', 'doxxing'
                ]
            },
            'Script Kiddie': {
                'ttps': [
                    'ssh_brute_force', 'sql_injection', 'xss_attack',
                    'scanner_user_agent', 'automated_attack'
                ]
            },
            'Opportunistic Scanner': {
                'ttps': [
                    'reconnaissance', 'scanner_user_agent', 'automated_attack',
                    'ssh_brute_force', 'exploit_attempt'
                ]
            }
        }

    def _build_tool_signatures(self) -> Dict[str, Dict]:
        """Build tool signatures for each actor"""
        return {
            'APT28': {
                'tools': ['X-Agent', 'Sofacy', 'Komplex', 'XTunnel', 'mimikatz']
            },
            'APT29': {
                'tools': ['WellMess', 'WellMail', 'Cobalt Strike', 'PowerShell Empire']
            },
            'Lazarus Group': {
                'tools': ['Destover', 'Volgmer', 'Duuzer', 'Trojan.Manuscrypt']
            },
            'FIN7': {
                'tools': ['Carbanak', 'Cobalt Strike', 'DNSMessenger', 'GRIFFON']
            },
            'Anonymous': {
                'tools': ['LOIC', 'HOIC', 'sqlmap', 'havij']
            },
            'Script Kiddie': {
                'tools': ['metasploit', 'sqlmap', 'nikto', 'nmap', 'hydra']
            },
            'Opportunistic Scanner': {
                'tools': ['masscan', 'shodan', 'nmap', 'zmap']
            }
        }

    def _load_infrastructure_database(self) -> Dict[str, Dict]:
        """Load infrastructure intelligence"""
        # In production, would load from threat intel feeds
        return {
            'APT28': {
                'ip_ranges': ['185.86.148.0/24', '193.169.244.0/24'],
                'asns': ['AS44812'],
                'hosting_providers': ['serveroid.com', 'rackservice.org']
            },
            'APT29': {
                'ip_ranges': ['45.32.0.0/16', '185.231.155.0/24'],
                'asns': ['AS64425'],
                'hosting_providers': ['vultr.com']
            },
            'Lazarus Group': {
                'ip_ranges': ['175.45.176.0/24'],
                'asns': ['AS4766'],
                'hosting_providers': []
            }
        }

    def get_stats(self) -> Dict:
        """Get attribution statistics"""
        return self.stats.copy()
