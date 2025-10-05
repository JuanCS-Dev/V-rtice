"""FASE 8: Autonomous Investigation - Core Logic

Autonomous threat actor profiling, campaign correlation, and automated investigations.
Bio-inspired investigative intelligence for attribution and incident response.

NO MOCKS - Production-ready investigation algorithms.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict
import json
import hashlib

import numpy as np
from scipy.spatial.distance import cosine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class TTP(Enum):
    """MITRE ATT&CK Tactics, Techniques, and Procedures."""
    # Initial Access
    PHISHING = "T1566"
    EXPLOIT_PUBLIC_FACING = "T1190"
    # Execution
    COMMAND_SCRIPTING = "T1059"
    # Persistence
    CREATE_ACCOUNT = "T1136"
    REGISTRY_RUN_KEYS = "T1547"
    # Privilege Escalation
    EXPLOIT_ELEVATION = "T1068"
    # Defense Evasion
    OBFUSCATED_FILES = "T1027"
    DISABLE_SECURITY_TOOLS = "T1562"
    # Credential Access
    CREDENTIAL_DUMPING = "T1003"
    BRUTE_FORCE = "T1110"
    # Discovery
    NETWORK_SCANNING = "T1046"
    # Lateral Movement
    REMOTE_SERVICES = "T1021"
    # Collection
    DATA_STAGED = "T1074"
    # Exfiltration
    EXFILTRATION_C2 = "T1041"


class InvestigationStatus(Enum):
    """Investigation lifecycle status."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    EVIDENCE_COLLECTED = "evidence_collected"
    ACTOR_ATTRIBUTED = "actor_attributed"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class ThreatActorProfile:
    """Threat actor behavioral profile."""
    actor_id: str
    actor_name: str
    ttps: Set[TTP]  # Known TTPs
    infrastructure: Set[str]  # IP addresses, domains
    malware_families: Set[str]  # Associated malware
    targets: Set[str]  # Typical targets (industries, geos)
    sophistication_score: float  # 0-1 (0=script kiddie, 1=nation-state)
    activity_timeline: List[datetime]  # Historical activity
    attribution_confidence: float  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityIncident:
    """Security incident for investigation."""
    incident_id: str
    timestamp: datetime
    incident_type: str  # "malware", "intrusion", "data_breach", etc
    affected_assets: List[str]
    iocs: List[str]  # Indicators of Compromise
    ttps_observed: Set[TTP]
    severity: float  # 0-1
    raw_evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Campaign:
    """Coordinated attack campaign."""
    campaign_id: str
    campaign_name: str
    incidents: List[str]  # Incident IDs
    attributed_actor: Optional[str]  # Actor ID
    start_date: datetime
    last_activity: datetime
    ttps: Set[TTP]
    targets: Set[str]
    iocs: Set[str]
    confidence_score: float  # 0-1
    campaign_pattern: str  # Description of the pattern
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Investigation:
    """Autonomous investigation instance."""
    investigation_id: str
    incident_id: str
    status: InvestigationStatus
    findings: List[str]
    evidence_chain: List[Dict[str, Any]]
    attributed_actor: Optional[str]
    related_campaigns: List[str]
    confidence_score: float
    playbook_used: str
    start_time: datetime
    end_time: Optional[datetime] = None
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# Threat Actor Profiler
# ============================================================================

class ThreatActorProfiler:
    """Profiles threat actors based on TTPs, infrastructure, and behavior.

    Uses behavioral fingerprinting and pattern matching for attribution.
    """

    def __init__(self):
        self.actor_database: Dict[str, ThreatActorProfile] = {}
        self.attributions_made: int = 0
        self.correct_attributions: int = 0

    def register_threat_actor(
        self,
        actor_id: str,
        actor_name: str,
        known_ttps: List[TTP],
        known_infrastructure: List[str],
        sophistication_score: float = 0.5
    ):
        """Register known threat actor in database.

        Args:
            actor_id: Unique actor identifier
            actor_name: Actor name (APT28, Lazarus, etc)
            known_ttps: Known TTPs from historical campaigns
            sophistication_score: 0-1 sophistication rating
        """
        profile = ThreatActorProfile(
            actor_id=actor_id,
            actor_name=actor_name,
            ttps=set(known_ttps),
            infrastructure=set(known_infrastructure),
            malware_families=set(),
            targets=set(),
            sophistication_score=sophistication_score,
            activity_timeline=[],
            attribution_confidence=1.0  # High confidence for known actors
        )

        self.actor_database[actor_id] = profile
        logger.info(f"Registered threat actor: {actor_name} ({actor_id})")

    def attribute_incident(self, incident: SecurityIncident) -> Tuple[Optional[str], float]:
        """Attribute incident to threat actor.

        Algorithm:
        1. Extract TTP fingerprint from incident
        2. Compare to known actor TTP fingerprints
        3. Match infrastructure (IPs, domains)
        4. Compute similarity scores
        5. Return best match above threshold

        Args:
            incident: Security incident to attribute

        Returns:
            Tuple of (actor_id, confidence_score)
        """
        if len(self.actor_database) == 0:
            return None, 0.0

        best_match_actor = None
        best_match_score = 0.0

        # Extract incident fingerprint
        incident_ttps = incident.ttps_observed
        incident_iocs = set(incident.iocs)

        # Compare to each known actor
        for actor_id, profile in self.actor_database.items():
            # TTP similarity (Jaccard)
            ttp_similarity = self._compute_ttp_similarity(incident_ttps, profile.ttps)

            # Infrastructure overlap
            infra_similarity = self._compute_infrastructure_similarity(
                incident_iocs,
                profile.infrastructure
            )

            # Weighted combination
            # TTPs are more important than infrastructure (IPs can change)
            similarity = 0.7 * ttp_similarity + 0.3 * infra_similarity

            if similarity > best_match_score:
                best_match_score = similarity
                best_match_actor = actor_id

        # Only attribute if confidence > 0.6
        if best_match_score >= 0.6:
            self.attributions_made += 1

            # Update actor profile with new activity
            if best_match_actor:
                self.actor_database[best_match_actor].activity_timeline.append(incident.timestamp)
                self.actor_database[best_match_actor].ttps.update(incident_ttps)

            return best_match_actor, best_match_score
        else:
            return None, best_match_score

    def _compute_ttp_similarity(self, ttps1: Set[TTP], ttps2: Set[TTP]) -> float:
        """Compute TTP similarity using Jaccard index.

        Args:
            ttps1: First TTP set
            ttps2: Second TTP set

        Returns:
            Jaccard similarity (0-1)
        """
        if len(ttps1) == 0 and len(ttps2) == 0:
            return 1.0

        if len(ttps1) == 0 or len(ttps2) == 0:
            return 0.0

        intersection = len(ttps1 & ttps2)
        union = len(ttps1 | ttps2)

        return intersection / union if union > 0 else 0.0

    def _compute_infrastructure_similarity(self, iocs1: Set[str], iocs2: Set[str]) -> float:
        """Compute infrastructure overlap.

        Args:
            iocs1: First IOC set
            iocs2: Second IOC set

        Returns:
            Similarity score (0-1)
        """
        if len(iocs1) == 0 and len(iocs2) == 0:
            return 1.0

        if len(iocs1) == 0 or len(iocs2) == 0:
            return 0.0

        # Extract IPs and domains from IOCs
        ips1 = {ioc for ioc in iocs1 if self._is_ip_address(ioc)}
        ips2 = {ioc for ioc in iocs2 if self._is_ip_address(ioc)}

        domains1 = {ioc for ioc in iocs1 if self._is_domain(ioc)}
        domains2 = {ioc for ioc in iocs2 if self._is_domain(ioc)}

        # Compute overlap
        ip_overlap = len(ips1 & ips2) / max(len(ips1 | ips2), 1)
        domain_overlap = len(domains1 & domains2) / max(len(domains1 | domains2), 1)

        # Average
        return (ip_overlap + domain_overlap) / 2

    def _is_ip_address(self, ioc: str) -> bool:
        """Check if IOC is IP address.

        Args:
            ioc: IOC string

        Returns:
            True if IP address
        """
        parts = ioc.split('.')
        if len(parts) != 4:
            return False

        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

    def _is_domain(self, ioc: str) -> bool:
        """Check if IOC is domain name.

        Args:
            ioc: IOC string

        Returns:
            True if domain
        """
        return '.' in ioc and not self._is_ip_address(ioc)

    def get_actor_profile(self, actor_id: str) -> Optional[ThreatActorProfile]:
        """Retrieve actor profile.

        Args:
            actor_id: Actor identifier

        Returns:
            Actor profile or None
        """
        return self.actor_database.get(actor_id)

    def get_status(self) -> Dict[str, Any]:
        """Get profiler status.

        Returns:
            Status dictionary
        """
        accuracy = (
            self.correct_attributions / self.attributions_made
            if self.attributions_made > 0
            else 0.0
        )

        return {
            "component": "threat_actor_profiler",
            "actors_tracked": len(self.actor_database),
            "attributions_made": self.attributions_made,
            "accuracy": accuracy,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Campaign Correlator
# ============================================================================

class CampaignCorrelator:
    """Correlates incidents into coordinated campaigns.

    Identifies patterns across seemingly unrelated incidents.
    """

    def __init__(self):
        self.incidents: List[SecurityIncident] = []
        self.campaigns: Dict[str, Campaign] = {}
        self.incident_to_campaign: Dict[str, str] = {}
        self.campaigns_identified: int = 0

    def ingest_incident(self, incident: SecurityIncident):
        """Ingest security incident for correlation.

        Args:
            incident: Security incident
        """
        self.incidents.append(incident)
        logger.debug(f"Ingested incident: {incident.incident_id}")

    def correlate_campaigns(self, time_window_days: int = 30) -> List[Campaign]:
        """Correlate incidents into campaigns.

        Algorithm:
        1. Group incidents by time proximity
        2. Compute incident-to-incident similarity (TTPs, IOCs)
        3. Use hierarchical clustering
        4. Identify campaign patterns

        Args:
            time_window_days: Maximum time span for campaign

        Returns:
            List of identified campaigns
        """
        if len(self.incidents) < 2:
            return []

        # Build similarity matrix
        n = len(self.incidents)
        similarity_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._compute_incident_similarity(
                    self.incidents[i],
                    self.incidents[j],
                    time_window_days
                )
                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity

        # Hierarchical clustering (simple agglomerative)
        clusters = self._agglomerative_clustering(similarity_matrix, threshold=0.6)

        # Create campaigns from clusters
        new_campaigns = []

        for cluster_indices in clusters:
            if len(cluster_indices) >= 2:  # Campaign = 2+ incidents
                campaign = self._create_campaign_from_cluster(cluster_indices)
                self.campaigns[campaign.campaign_id] = campaign
                new_campaigns.append(campaign)
                self.campaigns_identified += 1

                # Map incidents to campaign
                for idx in cluster_indices:
                    incident_id = self.incidents[idx].incident_id
                    self.incident_to_campaign[incident_id] = campaign.campaign_id

        return new_campaigns

    def _compute_incident_similarity(
        self,
        inc1: SecurityIncident,
        inc2: SecurityIncident,
        time_window_days: int
    ) -> float:
        """Compute similarity between two incidents.

        Factors:
        1. TTP overlap (Jaccard)
        2. IOC overlap
        3. Target similarity
        4. Temporal proximity

        Args:
            inc1: First incident
            inc2: Second incident
            time_window_days: Time window

        Returns:
            Similarity score (0-1)
        """
        # TTP similarity
        ttp_sim = self._jaccard_similarity(inc1.ttps_observed, inc2.ttps_observed)

        # IOC similarity
        ioc_sim = self._jaccard_similarity(set(inc1.iocs), set(inc2.iocs))

        # Target similarity
        target_sim = self._jaccard_similarity(
            set(inc1.affected_assets),
            set(inc2.affected_assets)
        )

        # Temporal proximity (closer in time = higher score)
        time_diff_days = abs((inc1.timestamp - inc2.timestamp).days)
        temporal_sim = max(0, 1 - (time_diff_days / time_window_days))

        # Weighted combination
        similarity = (
            0.4 * ttp_sim +
            0.3 * ioc_sim +
            0.2 * target_sim +
            0.1 * temporal_sim
        )

        return similarity

    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """Compute Jaccard similarity.

        Args:
            set1: First set
            set2: Second set

        Returns:
            Jaccard index (0-1)
        """
        if len(set1) == 0 and len(set2) == 0:
            return 1.0

        if len(set1) == 0 or len(set2) == 0:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _agglomerative_clustering(
        self,
        similarity_matrix: np.ndarray,
        threshold: float
    ) -> List[List[int]]:
        """Simple agglomerative clustering.

        Args:
            similarity_matrix: N×N similarity matrix
            threshold: Minimum similarity for clustering

        Returns:
            List of clusters (each cluster is list of indices)
        """
        n = len(similarity_matrix)

        # Initialize: each incident is its own cluster
        clusters = [[i] for i in range(n)]

        # Iteratively merge most similar clusters
        while True:
            # Find most similar pair of clusters
            max_sim = -1
            best_pair = None

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Average linkage: average similarity between all pairs
                    similarities = []
                    for idx_i in clusters[i]:
                        for idx_j in clusters[j]:
                            similarities.append(similarity_matrix[idx_i, idx_j])

                    avg_sim = np.mean(similarities) if similarities else 0

                    if avg_sim > max_sim:
                        max_sim = avg_sim
                        best_pair = (i, j)

            # If best similarity below threshold, stop
            if max_sim < threshold:
                break

            # Merge clusters
            if best_pair:
                i, j = best_pair
                clusters[i].extend(clusters[j])
                del clusters[j]
            else:
                break

        return clusters

    def _create_campaign_from_cluster(self, cluster_indices: List[int]) -> Campaign:
        """Create campaign from incident cluster.

        Args:
            cluster_indices: Indices of incidents in cluster

        Returns:
            Campaign object
        """
        incidents_in_cluster = [self.incidents[idx] for idx in cluster_indices]

        # Aggregate TTPs
        all_ttps = set()
        for inc in incidents_in_cluster:
            all_ttps.update(inc.ttps_observed)

        # Aggregate IOCs
        all_iocs = set()
        for inc in incidents_in_cluster:
            all_iocs.update(inc.iocs)

        # Aggregate targets
        all_targets = set()
        for inc in incidents_in_cluster:
            all_targets.update(inc.affected_assets)

        # Time span
        timestamps = [inc.timestamp for inc in incidents_in_cluster]
        start_date = min(timestamps)
        last_activity = max(timestamps)

        # Generate campaign ID and name
        campaign_id = f"campaign_{start_date.strftime('%Y%m%d')}_{len(self.campaigns)}"

        # Describe pattern
        most_common_ttp = max(all_ttps, key=lambda ttp: sum(
            1 for inc in incidents_in_cluster if ttp in inc.ttps_observed
        )) if all_ttps else None

        pattern = f"Coordinated activity using {most_common_ttp.value if most_common_ttp else 'multiple TTPs'}"

        # Compute confidence (higher if more incidents, more TTP overlap)
        confidence = min(0.95, 0.5 + (len(incidents_in_cluster) * 0.1))

        campaign = Campaign(
            campaign_id=campaign_id,
            campaign_name=f"Campaign {campaign_id}",
            incidents=[inc.incident_id for inc in incidents_in_cluster],
            attributed_actor=None,  # Attribution happens separately
            start_date=start_date,
            last_activity=last_activity,
            ttps=all_ttps,
            targets=all_targets,
            iocs=all_iocs,
            confidence_score=confidence,
            campaign_pattern=pattern
        )

        return campaign

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Retrieve campaign by ID.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign or None
        """
        return self.campaigns.get(campaign_id)

    def get_incident_campaign(self, incident_id: str) -> Optional[str]:
        """Get campaign ID for incident.

        Args:
            incident_id: Incident identifier

        Returns:
            Campaign ID or None
        """
        return self.incident_to_campaign.get(incident_id)

    def get_status(self) -> Dict[str, Any]:
        """Get correlator status.

        Returns:
            Status dictionary
        """
        return {
            "component": "campaign_correlator",
            "incidents_ingested": len(self.incidents),
            "campaigns_identified": self.campaigns_identified,
            "active_campaigns": len([c for c in self.campaigns.values()
                                     if (datetime.now() - c.last_activity).days <= 30]),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Autonomous Investigator
# ============================================================================

class AutonomousInvestigator:
    """Conducts autonomous investigations using playbooks.

    Automates evidence collection, correlation, and attribution.
    """

    def __init__(self, profiler: ThreatActorProfiler, correlator: CampaignCorrelator):
        self.profiler = profiler
        self.correlator = correlator
        self.investigations: Dict[str, Investigation] = {}
        self.investigations_completed: int = 0

    def initiate_investigation(
        self,
        incident: SecurityIncident,
        playbook: str = "standard"
    ) -> Investigation:
        """Initiate autonomous investigation.

        Args:
            incident: Security incident to investigate
            playbook: Investigation playbook to use

        Returns:
            Investigation instance
        """
        investigation_id = f"inv_{incident.incident_id}_{int(datetime.now().timestamp())}"

        investigation = Investigation(
            investigation_id=investigation_id,
            incident_id=incident.incident_id,
            status=InvestigationStatus.INITIATED,
            findings=[],
            evidence_chain=[],
            attributed_actor=None,
            related_campaigns=[],
            confidence_score=0.0,
            playbook_used=playbook,
            start_time=datetime.now()
        )

        self.investigations[investigation_id] = investigation

        logger.info(f"Initiated investigation: {investigation_id}")

        # Execute playbook
        self._execute_playbook(investigation, incident, playbook)

        return investigation

    def _execute_playbook(
        self,
        investigation: Investigation,
        incident: SecurityIncident,
        playbook: str
    ):
        """Execute investigation playbook.

        Playbook steps:
        1. Collect evidence (IOCs, logs, artifacts)
        2. Correlate to campaigns
        3. Attribute to threat actor
        4. Generate findings and recommendations

        Args:
            investigation: Investigation instance
            incident: Security incident
            playbook: Playbook name
        """
        # STEP 1: Collect evidence
        investigation.status = InvestigationStatus.IN_PROGRESS
        self._collect_evidence(investigation, incident)

        # STEP 2: Correlate to campaigns
        campaign_id = self.correlator.get_incident_campaign(incident.incident_id)
        if campaign_id:
            investigation.related_campaigns.append(campaign_id)
            investigation.findings.append(
                f"Incident correlated to campaign: {campaign_id}"
            )

        # STEP 3: Attribute to threat actor
        investigation.status = InvestigationStatus.EVIDENCE_COLLECTED
        actor_id, confidence = self.profiler.attribute_incident(incident)

        if actor_id:
            investigation.attributed_actor = actor_id
            investigation.confidence_score = confidence
            investigation.status = InvestigationStatus.ACTOR_ATTRIBUTED

            actor_profile = self.profiler.get_actor_profile(actor_id)
            if actor_profile:
                investigation.findings.append(
                    f"Attributed to threat actor: {actor_profile.actor_name} "
                    f"(confidence: {confidence:.2%})"
                )

        # STEP 4: Generate recommendations
        investigation.recommendations = self._generate_recommendations(incident, actor_id)

        # Complete investigation
        investigation.status = InvestigationStatus.COMPLETED
        investigation.end_time = datetime.now()
        self.investigations_completed += 1

        logger.info(f"Completed investigation: {investigation.investigation_id}")

    def _collect_evidence(self, investigation: Investigation, incident: SecurityIncident):
        """Collect and chain evidence.

        Args:
            investigation: Investigation instance
            incident: Security incident
        """
        # Evidence 1: IOCs
        for ioc in incident.iocs:
            evidence = {
                "type": "ioc",
                "value": ioc,
                "timestamp": datetime.now().isoformat(),
                "hash": hashlib.sha256(ioc.encode()).hexdigest()[:16]
            }
            investigation.evidence_chain.append(evidence)

        investigation.findings.append(f"Collected {len(incident.iocs)} IOCs")

        # Evidence 2: TTPs
        for ttp in incident.ttps_observed:
            evidence = {
                "type": "ttp",
                "value": ttp.value,
                "timestamp": datetime.now().isoformat(),
                "hash": hashlib.sha256(ttp.value.encode()).hexdigest()[:16]
            }
            investigation.evidence_chain.append(evidence)

        investigation.findings.append(f"Identified {len(incident.ttps_observed)} TTPs")

        # Evidence 3: Affected assets
        for asset in incident.affected_assets:
            evidence = {
                "type": "affected_asset",
                "value": asset,
                "timestamp": datetime.now().isoformat(),
                "hash": hashlib.sha256(asset.encode()).hexdigest()[:16]
            }
            investigation.evidence_chain.append(evidence)

        investigation.findings.append(f"Documented {len(incident.affected_assets)} affected assets")

    def _generate_recommendations(
        self,
        incident: SecurityIncident,
        actor_id: Optional[str]
    ) -> List[str]:
        """Generate investigation recommendations.

        Args:
            incident: Security incident
            actor_id: Attributed actor (if any)

        Returns:
            List of recommendations
        """
        recommendations = []

        # IOC-based recommendations
        if len(incident.iocs) > 0:
            recommendations.append("Block all identified IOCs in network perimeter")
            recommendations.append("Hunt for IOCs across environment using EDR")

        # TTP-based recommendations
        if TTP.CREDENTIAL_DUMPING in incident.ttps_observed:
            recommendations.append("Force password reset for affected accounts")
            recommendations.append("Review privileged access logs")

        if TTP.LATERAL_MOVEMENT in incident.ttps_observed:
            recommendations.append("Segment network to limit lateral movement")

        if TTP.EXFILTRATION_C2 in incident.ttps_observed:
            recommendations.append("Review DLP alerts for data exfiltration")
            recommendations.append("Analyze network traffic for C2 communication")

        # Actor-based recommendations
        if actor_id:
            actor_profile = self.profiler.get_actor_profile(actor_id)
            if actor_profile and actor_profile.sophistication_score > 0.7:
                recommendations.append("Engage incident response team (sophisticated actor)")
                recommendations.append("Consider external threat intelligence support")

        # General recommendations
        recommendations.append("Document incident in SIEM for future correlation")
        recommendations.append("Update detection rules based on TTPs")

        return recommendations

    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        """Retrieve investigation by ID.

        Args:
            investigation_id: Investigation identifier

        Returns:
            Investigation or None
        """
        return self.investigations.get(investigation_id)

    def get_status(self) -> Dict[str, Any]:
        """Get investigator status.

        Returns:
            Status dictionary
        """
        active_investigations = len([
            inv for inv in self.investigations.values()
            if inv.status != InvestigationStatus.COMPLETED
        ])

        return {
            "component": "autonomous_investigator",
            "investigations_completed": self.investigations_completed,
            "active_investigations": active_investigations,
            "total_investigations": len(self.investigations),
            "timestamp": datetime.now().isoformat()
        }
