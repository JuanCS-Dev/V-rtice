"""
👥 Threat Actor Profiler - Profiling e tracking de threat actors

Track APT groups, cybercrime gangs, hacktivists, and nation-state actors.

Features:
- APT group database (APT1-APT42, Lazarus, FIN7, etc)
- Attribution analysis
- Campaign tracking
- TTP profiling
- Target industry tracking
- Geolocation/attribution
- Aliases/alternative names

Actor Categories:
- Nation-State (Advanced Persistent Threats)
- Cybercrime Groups
- Hacktivists
- Insider Threats
- Script Kiddies
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ActorType(Enum):
    """Tipo de threat actor"""
    NATION_STATE = "nation_state"
    APT_GROUP = "apt_group"
    CYBERCRIME_GROUP = "cybercrime_group"
    HACKTIVIST = "hacktivist"
    INSIDER_THREAT = "insider_threat"
    SCRIPT_KIDDIE = "script_kiddie"
    UNKNOWN = "unknown"


class ActorSophistication(Enum):
    """Nível de sofisticação"""
    NONE = "none"  # Script kiddies
    MINIMAL = "minimal"  # Basic tools
    INTERMEDIATE = "intermediate"  # Custom tools, some evasion
    ADVANCED = "advanced"  # Custom malware, advanced TTPs
    EXPERT = "expert"  # Zero-days, state-level resources
    STRATEGIC = "strategic"  # Nation-state level


class ActorMotivation(Enum):
    """Motivação do actor"""
    FINANCIAL = "financial"
    ESPIONAGE = "espionage"
    SABOTAGE = "sabotage"
    IDEOLOGY = "ideology"
    REVENGE = "revenge"
    NOTORIETY = "notoriety"
    UNKNOWN = "unknown"


class TargetSector(Enum):
    """Setores alvo"""
    GOVERNMENT = "government"
    MILITARY = "military"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    ENERGY = "energy"
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    TELECOMMUNICATIONS = "telecommunications"
    EDUCATION = "education"
    RETAIL = "retail"
    MEDIA = "media"
    DEFENSE_INDUSTRIAL = "defense_industrial"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"


@dataclass
class Campaign:
    """
    Campanha de ataque

    Attributes:
        id: Campaign ID
        name: Campaign name
        start_date: When campaign started
        end_date: When campaign ended (if known)
        description: Campaign description
        targets: Target organizations/sectors
        iocs: Associated IOCs
        ttps: TTPs used
        attributed_to: Actor attribution
    """
    id: str
    name: str
    start_date: datetime
    end_date: Optional[datetime] = None

    description: str = ""

    # Targeting
    targets: List[str] = field(default_factory=list)
    target_sectors: List[TargetSector] = field(default_factory=list)
    target_countries: List[str] = field(default_factory=list)

    # Technical indicators
    iocs: List[str] = field(default_factory=list)
    ttps: List[str] = field(default_factory=list)

    # Attribution
    attributed_to: Optional[str] = None  # Actor ID
    confidence: int = 0  # Attribution confidence (0-100)

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatActor:
    """
    Threat Actor Profile

    Attributes:
        id: Unique actor ID
        name: Primary name
        aliases: Alternative names
        actor_type: Type of actor
        sophistication: Sophistication level
        motivation: Primary motivation
        origin_country: Country of origin (if known)
        active_since: First observed activity
        last_seen: Most recent activity
        description: Actor description
        target_sectors: Targeted industries
        target_countries: Targeted countries
        ttps: Known TTPs
        campaigns: Associated campaigns
        iocs: Associated IOCs
        tools: Known tools/malware
    """
    id: str
    name: str
    aliases: List[str] = field(default_factory=list)

    # Classification
    actor_type: ActorType = ActorType.UNKNOWN
    sophistication: ActorSophistication = ActorSophistication.INTERMEDIATE
    motivation: ActorMotivation = ActorMotivation.UNKNOWN

    # Attribution
    origin_country: Optional[str] = None
    suspected_sponsors: List[str] = field(default_factory=list)

    # Timeline
    active_since: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_active: bool = True

    # Description
    description: str = ""

    # Targeting
    target_sectors: List[TargetSector] = field(default_factory=list)
    target_countries: List[str] = field(default_factory=list)

    # TTPs
    ttps: List[str] = field(default_factory=list)  # MITRE ATT&CK technique IDs

    # Campaigns
    campaigns: List[str] = field(default_factory=list)  # Campaign IDs

    # IOCs
    iocs: List[str] = field(default_factory=list)

    # Tools & Malware
    tools: List[str] = field(default_factory=list)
    malware_families: List[str] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # References
    references: List[str] = field(default_factory=list)  # URLs to reports


class ThreatActorProfiler:
    """
    Threat Actor Profiling & Tracking System

    Features:
    - APT group database
    - Campaign tracking
    - Attribution analysis
    - TTP profiling
    - IOC correlation
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do threat_actor_service
            use_backend: Se True, usa backend
        """
        self.backend_url = backend_url or "http://localhost:8020"
        self.use_backend = use_backend

        # Actor database
        self.actors: Dict[str, ThreatActor] = {}

        # Campaign database
        self.campaigns: Dict[str, Campaign] = {}

        # Load known APT groups
        self._load_known_actors()

    def _load_known_actors(self):
        """Carrega threat actors conhecidos"""

        known_actors = [
            ThreatActor(
                id="APT28",
                name="APT28",
                aliases=["Fancy Bear", "Sofacy", "Sednit", "Pawn Storm", "STRONTIUM"],
                actor_type=ActorType.NATION_STATE,
                sophistication=ActorSophistication.EXPERT,
                motivation=ActorMotivation.ESPIONAGE,
                origin_country="Russia",
                suspected_sponsors=["GRU (Russian Military Intelligence)"],
                active_since=datetime(2007, 1, 1),
                is_active=True,
                description="Russian nation-state APT group attributed to GRU, targets government, military, and security organizations",
                target_sectors=[
                    TargetSector.GOVERNMENT,
                    TargetSector.MILITARY,
                    TargetSector.DEFENSE_INDUSTRIAL,
                ],
                target_countries=["USA", "Ukraine", "Georgia", "France", "Germany"],
                tools=["X-Agent", "Sofacy", "LoJax", "Zebrocy"],
                tags=["apt", "russia", "espionage", "gru"],
            ),
            ThreatActor(
                id="APT29",
                name="APT29",
                aliases=["Cozy Bear", "The Dukes", "NOBELIUM", "UNC2452"],
                actor_type=ActorType.NATION_STATE,
                sophistication=ActorSophistication.EXPERT,
                motivation=ActorMotivation.ESPIONAGE,
                origin_country="Russia",
                suspected_sponsors=["SVR (Russian Foreign Intelligence)"],
                active_since=datetime(2008, 1, 1),
                is_active=True,
                description="Russian APT attributed to SVR, known for SolarWinds supply chain attack",
                target_sectors=[
                    TargetSector.GOVERNMENT,
                    TargetSector.TECHNOLOGY,
                    TargetSector.TELECOMMUNICATIONS,
                ],
                target_countries=["USA", "EU countries", "UK"],
                tools=["SUNBURST", "TEARDROP", "CozyDuke", "MiniDuke"],
                tags=["apt", "russia", "espionage", "svr", "solarwinds"],
            ),
            ThreatActor(
                id="LAZARUS",
                name="Lazarus Group",
                aliases=["HIDDEN COBRA", "Guardians of Peace", "ZINC", "APT38"],
                actor_type=ActorType.NATION_STATE,
                sophistication=ActorSophistication.EXPERT,
                motivation=ActorMotivation.FINANCIAL,
                origin_country="North Korea",
                suspected_sponsors=["RGB (Reconnaissance General Bureau)"],
                active_since=datetime(2009, 1, 1),
                is_active=True,
                description="North Korean APT conducting both espionage and financially motivated attacks",
                target_sectors=[
                    TargetSector.FINANCIAL,
                    TargetSector.MEDIA,
                    TargetSector.DEFENSE_INDUSTRIAL,
                ],
                target_countries=["USA", "South Korea", "Bangladesh", "Global"],
                tools=["WannaCry", "DYEPACK", "FastCash", "AppleJeus"],
                malware_families=["WannaCry", "FALLCHILL", "BLINDINGCAN"],
                tags=["apt", "north-korea", "financial", "destructive"],
            ),
            ThreatActor(
                id="APT41",
                name="APT41",
                aliases=["Wicked Panda", "BARIUM", "Double Dragon"],
                actor_type=ActorType.NATION_STATE,
                sophistication=ActorSophistication.ADVANCED,
                motivation=ActorMotivation.ESPIONAGE,
                origin_country="China",
                active_since=datetime(2012, 1, 1),
                is_active=True,
                description="Chinese APT conducting both state-sponsored espionage and financially motivated operations",
                target_sectors=[
                    TargetSector.HEALTHCARE,
                    TargetSector.TECHNOLOGY,
                    TargetSector.TELECOMMUNICATIONS,
                    TargetSector.GAMING,
                ],
                tools=["HIGHNOON", "LOWKEY", "CROSSWALK"],
                tags=["apt", "china", "dual-espionage"],
            ),
            ThreatActor(
                id="FIN7",
                name="FIN7",
                aliases=["Carbanak Group", "Navigator Group"],
                actor_type=ActorType.CYBERCRIME_GROUP,
                sophistication=ActorSophistication.ADVANCED,
                motivation=ActorMotivation.FINANCIAL,
                active_since=datetime(2013, 1, 1),
                is_active=True,
                description="Financially motivated cybercrime group targeting retail and hospitality",
                target_sectors=[
                    TargetSector.RETAIL,
                    TargetSector.FINANCIAL,
                    TargetSector.HOSPITALITY,
                ],
                tools=["Carbanak", "GRIFFON", "POWERSOURCE"],
                malware_families=["Carbanak", "Cobalt Strike"],
                tags=["cybercrime", "financial", "pos-malware"],
            ),
            ThreatActor(
                id="CONTI",
                name="Conti",
                aliases=["Wizard Spider"],
                actor_type=ActorType.CYBERCRIME_GROUP,
                sophistication=ActorSophistication.ADVANCED,
                motivation=ActorMotivation.FINANCIAL,
                active_since=datetime(2018, 1, 1),
                is_active=False,  # Disbanded
                description="Ransomware-as-a-Service operation, disbanded after internal leaks",
                target_sectors=[
                    TargetSector.HEALTHCARE,
                    TargetSector.GOVERNMENT,
                    TargetSector.MANUFACTURING,
                ],
                tools=["Conti Ransomware", "TrickBot", "BazarLoader"],
                malware_families=["Conti", "Ryuk"],
                tags=["ransomware", "raas", "cybercrime"],
            ),
        ]

        for actor in known_actors:
            self.actors[actor.id] = actor

        logger.info(f"Loaded {len(known_actors)} known threat actors")

    def add_actor(self, actor: ThreatActor) -> None:
        """
        Adiciona threat actor ao banco

        Args:
            actor: ThreatActor object
        """
        self.actors[actor.id] = actor
        logger.info(f"Added threat actor: {actor.name} ({actor.id})")

    def get_actor(self, actor_id: str) -> Optional[ThreatActor]:
        """Retorna actor por ID"""
        return self.actors.get(actor_id)

    def search_actors(
        self,
        query: str,
    ) -> List[ThreatActor]:
        """
        Busca actors por nome ou alias

        Args:
            query: Search query

        Returns:
            List of matching actors
        """
        query_lower = query.lower()

        results = []

        for actor in self.actors.values():
            # Search in name
            if query_lower in actor.name.lower():
                results.append(actor)
                continue

            # Search in aliases
            if any(query_lower in alias.lower() for alias in actor.aliases):
                results.append(actor)
                continue

        return results

    def get_actors_by_type(
        self,
        actor_type: ActorType,
        active_only: bool = True,
    ) -> List[ThreatActor]:
        """
        Retorna actors por tipo

        Args:
            actor_type: Actor type filter
            active_only: Only active actors

        Returns:
            List of ThreatActor
        """
        actors = [
            a for a in self.actors.values()
            if a.actor_type == actor_type
        ]

        if active_only:
            actors = [a for a in actors if a.is_active]

        return actors

    def get_actors_by_country(
        self,
        country: str,
    ) -> List[ThreatActor]:
        """
        Retorna actors por país de origem

        Args:
            country: Country name

        Returns:
            List of ThreatActor
        """
        return [
            a for a in self.actors.values()
            if a.origin_country and country.lower() in a.origin_country.lower()
        ]

    def add_campaign(self, campaign: Campaign) -> None:
        """
        Adiciona campanha

        Args:
            campaign: Campaign object
        """
        self.campaigns[campaign.id] = campaign

        # Link to actor if attributed
        if campaign.attributed_to:
            actor = self.get_actor(campaign.attributed_to)
            if actor and campaign.id not in actor.campaigns:
                actor.campaigns.append(campaign.id)

        logger.info(f"Added campaign: {campaign.name} ({campaign.id})")

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Retorna campanha por ID"""
        return self.campaigns.get(campaign_id)

    def get_actor_campaigns(self, actor_id: str) -> List[Campaign]:
        """
        Retorna campanhas de um actor

        Args:
            actor_id: Actor ID

        Returns:
            List of Campaign
        """
        actor = self.get_actor(actor_id)

        if not actor:
            return []

        return [
            self.campaigns[cid]
            for cid in actor.campaigns
            if cid in self.campaigns
        ]

    def attribute_campaign(
        self,
        campaign_id: str,
        actor_id: str,
        confidence: int,
    ) -> bool:
        """
        Atribui campanha a actor

        Args:
            campaign_id: Campaign ID
            actor_id: Actor ID
            confidence: Attribution confidence (0-100)

        Returns:
            True se sucesso
        """
        campaign = self.get_campaign(campaign_id)
        actor = self.get_actor(actor_id)

        if not campaign or not actor:
            return False

        campaign.attributed_to = actor_id
        campaign.confidence = confidence

        if campaign_id not in actor.campaigns:
            actor.campaigns.append(campaign_id)

        logger.info(
            f"Campaign {campaign.name} attributed to {actor.name} "
            f"(confidence: {confidence}%)"
        )

        return True

    def correlate_iocs_to_actor(
        self,
        iocs: List[str],
    ) -> Dict[str, List[str]]:
        """
        Correlaciona IOCs com actors conhecidos

        Args:
            iocs: List of IOCs

        Returns:
            Dict mapping actor_id to matching IOCs
        """
        correlations = {}

        for actor in self.actors.values():
            matching_iocs = [
                ioc for ioc in iocs
                if ioc in actor.iocs
            ]

            if matching_iocs:
                correlations[actor.id] = matching_iocs

        return correlations

    def get_actor_profile(self, actor_id: str) -> Optional[Dict[str, Any]]:
        """
        Retorna perfil completo de actor

        Args:
            actor_id: Actor ID

        Returns:
            Complete profile dict
        """
        actor = self.get_actor(actor_id)

        if not actor:
            return None

        # Get campaigns
        campaigns = self.get_actor_campaigns(actor_id)

        return {
            "id": actor.id,
            "name": actor.name,
            "aliases": actor.aliases,
            "type": actor.actor_type.value,
            "sophistication": actor.sophistication.value,
            "motivation": actor.motivation.value,
            "origin_country": actor.origin_country,
            "suspected_sponsors": actor.suspected_sponsors,
            "active_since": actor.active_since.isoformat() if actor.active_since else None,
            "last_seen": actor.last_seen.isoformat() if actor.last_seen else None,
            "is_active": actor.is_active,
            "description": actor.description,
            "target_sectors": [s.value for s in actor.target_sectors],
            "target_countries": actor.target_countries,
            "ttps": actor.ttps,
            "tools": actor.tools,
            "malware_families": actor.malware_families,
            "campaigns": [
                {
                    "id": c.id,
                    "name": c.name,
                    "start_date": c.start_date.isoformat(),
                    "targets": c.targets,
                }
                for c in campaigns
            ],
            "iocs_count": len(actor.iocs),
            "references": actor.references,
            "tags": actor.tags,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        # Count by type
        by_type = {}
        for actor in self.actors.values():
            by_type[actor.actor_type.value] = by_type.get(actor.actor_type.value, 0) + 1

        # Count by sophistication
        by_sophistication = {}
        for actor in self.actors.values():
            level = actor.sophistication.value
            by_sophistication[level] = by_sophistication.get(level, 0) + 1

        # Count by motivation
        by_motivation = {}
        for actor in self.actors.values():
            motivation = actor.motivation.value
            by_motivation[motivation] = by_motivation.get(motivation, 0) + 1

        # Active vs inactive
        active = len([a for a in self.actors.values() if a.is_active])
        inactive = len(self.actors) - active

        return {
            "total_actors": len(self.actors),
            "active_actors": active,
            "inactive_actors": inactive,
            "total_campaigns": len(self.campaigns),
            "by_type": by_type,
            "by_sophistication": by_sophistication,
            "by_motivation": by_motivation,
        }

    def list_actors(
        self,
        actor_type: Optional[ActorType] = None,
        active_only: bool = False,
        limit: int = 100,
    ) -> List[ThreatActor]:
        """
        Lista actors com filtros

        Args:
            actor_type: Filter by type
            active_only: Only active actors
            limit: Max results

        Returns:
            List of ThreatActor
        """
        actors = list(self.actors.values())

        if actor_type:
            actors = [a for a in actors if a.actor_type == actor_type]

        if active_only:
            actors = [a for a in actors if a.is_active]

        # Sort by last_seen (most recent first)
        actors = sorted(
            actors,
            key=lambda a: a.last_seen if a.last_seen else datetime.min,
            reverse=True
        )

        return actors[:limit]
