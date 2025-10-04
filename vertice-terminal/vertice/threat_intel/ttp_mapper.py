"""
🎯 TTP Mapper - MITRE ATT&CK Tactics, Techniques & Procedures mapping

Mapeia TTPs observados para MITRE ATT&CK Framework.

MITRE ATT&CK Enterprise Matrix:
- 14 Tactics (goal-based categorization)
- 200+ Techniques
- 400+ Sub-techniques
- Procedures (specific implementations)

Features:
- TTP-to-MITRE mapping
- Kill chain analysis
- Technique frequency tracking
- Actor TTP profiling
- Detection coverage mapping
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MITRETactic(Enum):
    """MITRE ATT&CK Enterprise Tactics"""
    RECONNAISSANCE = "TA0043"
    RESOURCE_DEVELOPMENT = "TA0042"
    INITIAL_ACCESS = "TA0001"
    EXECUTION = "TA0002"
    PERSISTENCE = "TA0003"
    PRIVILEGE_ESCALATION = "TA0004"
    DEFENSE_EVASION = "TA0005"
    CREDENTIAL_ACCESS = "TA0006"
    DISCOVERY = "TA0007"
    LATERAL_MOVEMENT = "TA0008"
    COLLECTION = "TA0009"
    COMMAND_AND_CONTROL = "TA0011"
    EXFILTRATION = "TA0010"
    IMPACT = "TA0040"


@dataclass
class MITRETechnique:
    """
    MITRE ATT&CK Technique

    Attributes:
        technique_id: MITRE technique ID (T1234)
        name: Technique name
        tactic: Primary tactic
        description: Technique description
        platforms: Affected platforms
        data_sources: Detection data sources
        defenses: Mitigations
        sub_techniques: Sub-technique IDs
    """
    technique_id: str  # T1234
    name: str
    tactic: MITRETactic
    description: str

    # Additional tactics (techniques can map to multiple)
    additional_tactics: List[MITRETactic] = field(default_factory=list)

    # Technical details
    platforms: List[str] = field(default_factory=list)  # Windows, Linux, macOS
    data_sources: List[str] = field(default_factory=list)
    defenses: List[str] = field(default_factory=list)

    # Sub-techniques
    sub_techniques: List[str] = field(default_factory=list)

    # Metadata
    mitre_url: str = ""


@dataclass
class TTP:
    """
    Tactics, Techniques & Procedures observation

    Attributes:
        id: Unique TTP observation ID
        technique_id: MITRE technique ID
        observed_at: When observed
        observed_in: Where observed (incident, campaign, etc)
        actor_id: Associated actor (if known)
        confidence: Attribution confidence
        description: Observation description
        iocs: Related IOCs
        context: Additional context
    """
    id: str
    technique_id: str  # MITRE T-code
    observed_at: datetime
    observed_in: str  # incident_id, campaign_id, etc

    # Attribution
    actor_id: Optional[str] = None
    confidence: int = 0  # 0-100

    # Context
    description: str = ""
    iocs: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)


class TTPMapper:
    """
    MITRE ATT&CK TTP Mapping System

    Features:
    - TTP-to-MITRE mapping
    - Kill chain reconstruction
    - Frequency analysis
    - Actor profiling
    - Coverage analysis
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do ttp_service
            use_backend: Se True, usa backend
        """
        self.backend_url = backend_url or "http://localhost:8021"
        self.use_backend = use_backend

        # MITRE technique database
        self.techniques: Dict[str, MITRETechnique] = {}

        # TTP observations
        self.observations: Dict[str, TTP] = {}

        # Load MITRE techniques
        self._load_mitre_techniques()

    def _load_mitre_techniques(self):
        """Carrega técnicas MITRE ATT&CK"""

        # Sample techniques (na produção, carregaria de MITRE STIX/JSON)
        techniques = [
            MITRETechnique(
                technique_id="T1566",
                name="Phishing",
                tactic=MITRETactic.INITIAL_ACCESS,
                description="Adversaries may send phishing messages to gain access to victim systems",
                platforms=["Linux", "macOS", "Windows", "SaaS", "Office 365", "Google Workspace"],
                data_sources=["Email Gateway", "Email Content", "Email Metadata"],
                defenses=["User Training", "Email Security"],
                sub_techniques=["T1566.001", "T1566.002", "T1566.003"],
                mitre_url="https://attack.mitre.org/techniques/T1566/",
            ),
            MITRETechnique(
                technique_id="T1059",
                name="Command and Scripting Interpreter",
                tactic=MITRETactic.EXECUTION,
                description="Adversaries may abuse command and script interpreters to execute commands",
                platforms=["Linux", "macOS", "Windows", "Network"],
                data_sources=["Process", "Command Execution"],
                defenses=["Application Control", "Execution Prevention"],
                sub_techniques=["T1059.001", "T1059.003", "T1059.005", "T1059.006"],
                mitre_url="https://attack.mitre.org/techniques/T1059/",
            ),
            MITRETechnique(
                technique_id="T1547",
                name="Boot or Logon Autostart Execution",
                tactic=MITRETactic.PERSISTENCE,
                additional_tactics=[MITRETactic.PRIVILEGE_ESCALATION],
                description="Adversaries may configure system settings to automatically execute a program",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["Windows Registry", "File Modification", "Process Creation"],
                defenses=["Limit Software Installation", "User Account Management"],
                sub_techniques=["T1547.001", "T1547.004", "T1547.009"],
                mitre_url="https://attack.mitre.org/techniques/T1547/",
            ),
            MITRETechnique(
                technique_id="T1055",
                name="Process Injection",
                tactic=MITRETactic.PRIVILEGE_ESCALATION,
                additional_tactics=[MITRETactic.DEFENSE_EVASION],
                description="Adversaries may inject code into processes to evade detection",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["Process", "Module Load", "Memory Access"],
                defenses=["Behavior Prevention on Endpoint"],
                sub_techniques=["T1055.001", "T1055.002", "T1055.003", "T1055.012"],
                mitre_url="https://attack.mitre.org/techniques/T1055/",
            ),
            MITRETechnique(
                technique_id="T1027",
                name="Obfuscated Files or Information",
                tactic=MITRETactic.DEFENSE_EVASION,
                description="Adversaries may obfuscate files or information to evade detection",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["File", "Script", "Process"],
                defenses=["Antivirus/EDR"],
                sub_techniques=["T1027.001", "T1027.002", "T1027.004", "T1027.005"],
                mitre_url="https://attack.mitre.org/techniques/T1027/",
            ),
            MITRETechnique(
                technique_id="T1003",
                name="OS Credential Dumping",
                tactic=MITRETactic.CREDENTIAL_ACCESS,
                description="Adversaries may dump credentials to obtain account login info",
                platforms=["Windows", "Linux", "macOS"],
                data_sources=["Process Access", "Command Execution", "File Access"],
                defenses=["Privileged Account Management", "Credential Access Protection"],
                sub_techniques=["T1003.001", "T1003.002", "T1003.003"],
                mitre_url="https://attack.mitre.org/techniques/T1003/",
            ),
            MITRETechnique(
                technique_id="T1083",
                name="File and Directory Discovery",
                tactic=MITRETactic.DISCOVERY,
                description="Adversaries may enumerate files and directories",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["Process", "Command Execution", "File Access"],
                defenses=["Limit Access to Resource"],
                mitre_url="https://attack.mitre.org/techniques/T1083/",
            ),
            MITRETechnique(
                technique_id="T1021",
                name="Remote Services",
                tactic=MITRETactic.LATERAL_MOVEMENT,
                description="Adversaries may use valid accounts to log into a service",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["Network Traffic", "Logon Session", "Process Creation"],
                defenses=["Network Segmentation", "Multi-factor Authentication"],
                sub_techniques=["T1021.001", "T1021.002", "T1021.004"],
                mitre_url="https://attack.mitre.org/techniques/T1021/",
            ),
            MITRETechnique(
                technique_id="T1560",
                name="Archive Collected Data",
                tactic=MITRETactic.COLLECTION,
                description="Adversaries may compress and/or encrypt data prior to exfiltration",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["File", "Process", "Command Execution"],
                defenses=["Audit"],
                sub_techniques=["T1560.001", "T1560.002", "T1560.003"],
                mitre_url="https://attack.mitre.org/techniques/T1560/",
            ),
            MITRETechnique(
                technique_id="T1071",
                name="Application Layer Protocol",
                tactic=MITRETactic.COMMAND_AND_CONTROL,
                description="Adversaries may communicate using application layer protocols",
                platforms=["Linux", "macOS", "Windows", "Network"],
                data_sources=["Network Traffic"],
                defenses=["Network Intrusion Prevention"],
                sub_techniques=["T1071.001", "T1071.002", "T1071.003", "T1071.004"],
                mitre_url="https://attack.mitre.org/techniques/T1071/",
            ),
            MITRETechnique(
                technique_id="T1041",
                name="Exfiltration Over C2 Channel",
                tactic=MITRETactic.EXFILTRATION,
                description="Adversaries may steal data by exfiltrating over their C2 channel",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["Network Traffic", "Network Connection Creation"],
                defenses=["Network Intrusion Prevention", "Data Loss Prevention"],
                mitre_url="https://attack.mitre.org/techniques/T1041/",
            ),
            MITRETechnique(
                technique_id="T1486",
                name="Data Encrypted for Impact",
                tactic=MITRETactic.IMPACT,
                description="Adversaries may encrypt data on target systems to interrupt availability (ransomware)",
                platforms=["Linux", "macOS", "Windows"],
                data_sources=["File", "Process", "Command Execution"],
                defenses=["Data Backup", "Behavior Prevention on Endpoint"],
                mitre_url="https://attack.mitre.org/techniques/T1486/",
            ),
        ]

        for technique in techniques:
            self.techniques[technique.technique_id] = technique

        logger.info(f"Loaded {len(techniques)} MITRE ATT&CK techniques")

    def add_technique(self, technique: MITRETechnique) -> None:
        """
        Adiciona técnica MITRE customizada

        Args:
            technique: MITRETechnique object
        """
        self.techniques[technique.technique_id] = technique
        logger.info(f"Added MITRE technique: {technique.name} ({technique.technique_id})")

    def get_technique(self, technique_id: str) -> Optional[MITRETechnique]:
        """Retorna técnica por ID"""
        return self.techniques.get(technique_id)

    def observe_ttp(
        self,
        technique_id: str,
        observed_in: str,
        actor_id: Optional[str] = None,
        description: str = "",
        iocs: Optional[List[str]] = None,
        confidence: int = 0,
    ) -> TTP:
        """
        Registra observação de TTP

        Args:
            technique_id: MITRE technique ID
            observed_in: Incident/campaign ID
            actor_id: Actor ID (if attributed)
            description: Observation description
            iocs: Related IOCs
            confidence: Confidence score

        Returns:
            TTP observation
        """
        import uuid

        ttp = TTP(
            id=f"TTP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            technique_id=technique_id,
            observed_at=datetime.now(),
            observed_in=observed_in,
            actor_id=actor_id,
            description=description,
            iocs=iocs or [],
            confidence=confidence,
        )

        self.observations[ttp.id] = ttp

        logger.info(
            f"TTP observed: {technique_id} in {observed_in}"
        )

        return ttp

    def get_ttps_by_actor(self, actor_id: str) -> List[TTP]:
        """
        Retorna TTPs de um actor

        Args:
            actor_id: Actor ID

        Returns:
            List of TTP observations
        """
        return [
            ttp for ttp in self.observations.values()
            if ttp.actor_id == actor_id
        ]

    def get_ttps_by_tactic(self, tactic: MITRETactic) -> List[MITRETechnique]:
        """
        Retorna técnicas por tactic

        Args:
            tactic: MITRE tactic

        Returns:
            List of techniques
        """
        return [
            t for t in self.techniques.values()
            if t.tactic == tactic or tactic in t.additional_tactics
        ]

    def get_kill_chain_coverage(
        self,
        observed_techniques: List[str],
    ) -> Dict[str, Any]:
        """
        Analisa cobertura da kill chain

        Args:
            observed_techniques: List of technique IDs

        Returns:
            Kill chain coverage analysis
        """
        # Map techniques to tactics
        tactics_covered = set()

        for tech_id in observed_techniques:
            technique = self.get_technique(tech_id)
            if technique:
                tactics_covered.add(technique.tactic)
                tactics_covered.update(technique.additional_tactics)

        # All tactics
        all_tactics = list(MITRETactic)

        coverage = {
            "total_tactics": len(all_tactics),
            "tactics_covered": len(tactics_covered),
            "coverage_percentage": (len(tactics_covered) / len(all_tactics)) * 100,
            "covered_tactics": [t.name for t in tactics_covered],
            "missing_tactics": [
                t.name for t in all_tactics
                if t not in tactics_covered
            ],
        }

        return coverage

    def get_technique_frequency(
        self,
        actor_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Retorna frequência de técnicas observadas

        Args:
            actor_id: Filter by actor (optional)

        Returns:
            Dict mapping technique_id to count
        """
        observations = self.observations.values()

        if actor_id:
            observations = [
                o for o in observations
                if o.actor_id == actor_id
            ]

        frequency = {}
        for ttp in observations:
            frequency[ttp.technique_id] = frequency.get(ttp.technique_id, 0) + 1

        # Sort by frequency
        frequency = dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))

        return frequency

    def get_actor_ttp_profile(self, actor_id: str) -> Dict[str, Any]:
        """
        Retorna perfil TTP de actor

        Args:
            actor_id: Actor ID

        Returns:
            TTP profile dict
        """
        actor_ttps = self.get_ttps_by_actor(actor_id)

        if not actor_ttps:
            return {
                "actor_id": actor_id,
                "total_observations": 0,
                "unique_techniques": 0,
                "tactics_used": [],
                "top_techniques": [],
                "kill_chain_coverage": {},
            }

        # Get unique techniques
        unique_techniques = list(set(ttp.technique_id for ttp in actor_ttps))

        # Get frequency
        frequency = self.get_technique_frequency(actor_id=actor_id)

        # Top techniques
        top_techniques = [
            {
                "technique_id": tech_id,
                "name": self.techniques[tech_id].name if tech_id in self.techniques else "Unknown",
                "count": count,
            }
            for tech_id, count in list(frequency.items())[:10]
        ]

        # Tactics used
        tactics_used = set()
        for tech_id in unique_techniques:
            technique = self.get_technique(tech_id)
            if technique:
                tactics_used.add(technique.tactic.name)

        # Kill chain coverage
        kill_chain = self.get_kill_chain_coverage(unique_techniques)

        return {
            "actor_id": actor_id,
            "total_observations": len(actor_ttps),
            "unique_techniques": len(unique_techniques),
            "tactics_used": sorted(list(tactics_used)),
            "top_techniques": top_techniques,
            "kill_chain_coverage": kill_chain,
        }

    def search_techniques(self, query: str) -> List[MITRETechnique]:
        """
        Busca técnicas por nome

        Args:
            query: Search query

        Returns:
            List of matching techniques
        """
        query_lower = query.lower()

        return [
            t for t in self.techniques.values()
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        # Count by tactic
        by_tactic = {}
        for technique in self.techniques.values():
            tactic = technique.tactic.name
            by_tactic[tactic] = by_tactic.get(tactic, 0) + 1

        return {
            "total_techniques": len(self.techniques),
            "total_observations": len(self.observations),
            "by_tactic": by_tactic,
        }

    def list_techniques(
        self,
        tactic: Optional[MITRETactic] = None,
        limit: int = 100,
    ) -> List[MITRETechnique]:
        """
        Lista técnicas com filtros

        Args:
            tactic: Filter by tactic
            limit: Max results

        Returns:
            List of MITRETechnique
        """
        techniques = list(self.techniques.values())

        if tactic:
            techniques = [
                t for t in techniques
                if t.tactic == tactic or tactic in t.additional_tactics
            ]

        return techniques[:limit]
