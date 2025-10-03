"""
Immunis - Dendritic Cell Service
=================================
Antigen presentation and adaptive immunity activation.

Biological inspiration: Dendritic Cells (DCs)
- Professional antigen-presenting cells (APCs)
- Bridge innate and adaptive immunity
- Capture antigens from pathogens
- Process and present on MHC-II molecules
- Migrate to lymph nodes
- Activate T cells and B cells
- Secrete cytokines (IL-12, IFN-α, TNF-α)
- Provide co-stimulatory signals

Computational implementation:
- Consume antigens from Macrophages (Kafka)
- Event correlation (multi-source analysis)
- Feature extraction and enrichment
- Present processed antigens to B/T cells
- Cytokine secretion (alert messages)
- Activation signals for adaptive response
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DendriticState(str, Enum):
    """Dendritic cell maturation states"""
    IMMATURE = "immature"  # Patrolling, capturing antigens
    SEMI_MATURE = "semi_mature"  # Processing antigens
    MATURE = "mature"  # Presenting antigens, secreting cytokines
    EXHAUSTED = "exhausted"  # Post-activation recovery


class Cytokine(str, Enum):
    """Cytokine types (immune signaling molecules)"""
    IL_12 = "il12"  # Promote Th1 response (cellular immunity)
    IFN_ALPHA = "ifn_alpha"  # Antiviral response
    IFN_BETA = "ifn_beta"  # Antiviral response
    TNF_ALPHA = "tnf_alpha"  # Inflammation
    IL_6 = "il6"  # Acute phase response
    IL_10 = "il10"  # Anti-inflammatory (regulatory)
    IL_4 = "il4"  # Promote Th2 response (humoral immunity)


class ActivationLevel(str, Enum):
    """Activation intensity"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Antigen:
    """Antigen from innate immune system"""
    antigen_id: str
    source_cell: str  # macrophage, neutrophil, nk_cell
    sample_hash: str
    malware_family: str
    severity: str
    static_features: Dict
    behavioral_features: Dict
    iocs: List[Dict]
    yara_rule: Optional[str]
    confidence: float
    timestamp: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class CorrelatedEvent:
    """Correlated multi-source event"""
    correlation_id: str
    antigens: List[Antigen]
    event_sources: Set[str]  # IPs, hosts, services involved
    event_timeline: List[Tuple[float, str]]  # (timestamp, description)
    attack_pattern: str  # multi_stage, coordinated, apt, etc.
    severity_score: float  # 0-1
    confidence: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProcessedAntigen:
    """
    Processed antigen ready for presentation.

    Like MHC-II molecules presenting peptides to T cells.
    """
    antigen_id: str
    original_antigen: Antigen
    correlated_event: Optional[CorrelatedEvent]

    # Extracted features for ML
    feature_vector: np.ndarray

    # Presentation context
    presentation_context: Dict  # When, where, how severe

    # Co-stimulatory signals
    costimulation: ActivationLevel

    # Recommended response
    recommended_response: str  # th1, th2, regulatory

    timestamp: float = field(default_factory=time.time)


@dataclass
class CytokineSignal:
    """Cytokine secretion (immune signaling)"""
    cytokine_type: Cytokine
    concentration: float  # 0-1 (relative amount)
    target_cells: List[str]  # b_cell, helper_t, cytotoxic_t, regulatory_t
    source_dc: str
    message: Dict  # Contextual information
    timestamp: float = field(default_factory=time.time)


class DendriticCore:
    """
    Dendritic Cell - Antigen presentation and immune activation.

    Lifecycle:
    1. Immature DC patrols tissues (consume Kafka antigens)
    2. Capture antigens from innate cells
    3. Process antigens (correlation, feature extraction)
    4. Mature while migrating to lymph nodes
    5. Present antigens to T/B cells (Kafka publish)
    6. Secrete cytokines (alert adaptive immunity)
    7. Exhaustion and recovery

    Key functions:
    - Multi-source event correlation
    - Attack pattern recognition
    - Feature enrichment
    - Co-stimulation signal generation
    - Cytokine secretion
    """

    def __init__(
        self,
        dc_id: str,
        correlation_window_seconds: int = 300,  # 5 minutes
        maturation_threshold: int = 3  # Antigens needed to mature
    ):
        self.dc_id = dc_id
        self.correlation_window_seconds = correlation_window_seconds
        self.maturation_threshold = maturation_threshold

        self.state = DendriticState.IMMATURE

        # Antigen capture
        self.captured_antigens: deque = deque(maxlen=100)
        self.antigen_index: Dict[str, Antigen] = {}  # Fast lookup

        # Correlation state
        self.correlation_window: deque = deque(maxlen=1000)
        self.correlated_events: Dict[str, CorrelatedEvent] = {}

        # Presentation queue
        self.presentation_queue: List[ProcessedAntigen] = []

        # Cytokine secretion history
        self.cytokine_history: deque = deque(maxlen=100)

        # Statistics
        self.stats = {
            "antigens_captured": 0,
            "antigens_processed": 0,
            "events_correlated": 0,
            "cytokines_secreted": 0,
            "t_cells_activated": 0,
            "b_cells_activated": 0,
            "maturations": 0
        }

        logger.info(
            f"Dendritic Cell {dc_id} initialized "
            f"(correlation_window={correlation_window_seconds}s, "
            f"maturation_threshold={maturation_threshold})"
        )

    async def capture_antigen(self, antigen: Antigen):
        """
        Capture antigen from innate immune cells.

        Biological: DC phagocytoses pathogen fragments
        Computational: Consume antigen from Kafka
        """
        logger.info(
            f"[{self.dc_id}] Capturing antigen {antigen.antigen_id} "
            f"from {antigen.source_cell}"
        )

        # Store antigen
        self.captured_antigens.append(antigen)
        self.antigen_index[antigen.antigen_id] = antigen
        self.correlation_window.append(antigen)

        self.stats["antigens_captured"] += 1

        # Check maturation threshold
        if len(self.captured_antigens) >= self.maturation_threshold:
            await self._mature()

    async def correlate_events(self) -> List[CorrelatedEvent]:
        """
        Correlate events across multiple sources.

        Patterns to detect:
        1. Multi-stage attacks (reconnaissance → exploitation → lateral movement)
        2. Coordinated attacks (multiple sources, same target)
        3. APT campaigns (low-and-slow, persistent)
        4. Ransomware chains (initial access → encryption → exfiltration)
        """
        if self.state == DendriticState.IMMATURE:
            return []

        correlated = []

        # Get antigens in time window
        cutoff_time = time.time() - self.correlation_window_seconds
        recent_antigens = [
            ag for ag in self.correlation_window
            if ag.timestamp >= cutoff_time
        ]

        if len(recent_antigens) < 2:
            return []

        # Correlation strategy 1: Same source IP
        source_groups = defaultdict(list)
        for antigen in recent_antigens:
            # Extract source IPs from IOCs
            source_ips = [
                ioc['value'] for ioc in antigen.iocs
                if ioc.get('ioc_type') == 'ip'
            ]
            for ip in source_ips:
                source_groups[ip].append(antigen)

        # Create correlated events for multi-antigen sources
        for source_ip, antigens in source_groups.items():
            if len(antigens) >= 2:
                event = self._create_correlated_event(
                    antigens,
                    correlation_type="same_source",
                    source_identifier=source_ip
                )
                correlated.append(event)
                self.correlated_events[event.correlation_id] = event

        # Correlation strategy 2: Temporal sequence (attack chain)
        attack_chains = self._detect_attack_chains(recent_antigens)
        for chain in attack_chains:
            event = self._create_correlated_event(
                chain,
                correlation_type="attack_chain",
                source_identifier="multi_stage"
            )
            correlated.append(event)
            self.correlated_events[event.correlation_id] = event

        # Correlation strategy 3: Similar malware family
        family_groups = defaultdict(list)
        for antigen in recent_antigens:
            family_groups[antigen.malware_family].append(antigen)

        for family, antigens in family_groups.items():
            if len(antigens) >= 3 and family != "unknown":
                event = self._create_correlated_event(
                    antigens,
                    correlation_type="campaign",
                    source_identifier=family
                )
                correlated.append(event)
                self.correlated_events[event.correlation_id] = event

        if correlated:
            self.stats["events_correlated"] += len(correlated)
            logger.info(
                f"[{self.dc_id}] Correlated {len(correlated)} multi-source events"
            )

        return correlated

    def _create_correlated_event(
        self,
        antigens: List[Antigen],
        correlation_type: str,
        source_identifier: str
    ) -> CorrelatedEvent:
        """Create correlated event from multiple antigens"""

        # Build timeline
        timeline = []
        for ag in sorted(antigens, key=lambda x: x.timestamp):
            timeline.append((
                ag.timestamp,
                f"{ag.source_cell}: {ag.malware_family} detected"
            ))

        # Extract all sources
        sources = set()
        for ag in antigens:
            sources.add(source_identifier)
            # Add all IOC sources
            for ioc in ag.iocs:
                if ioc.get('ioc_type') in ['ip', 'domain']:
                    sources.add(ioc['value'])

        # Determine attack pattern
        if correlation_type == "attack_chain":
            attack_pattern = "multi_stage_attack"
        elif correlation_type == "campaign":
            attack_pattern = "coordinated_campaign"
        elif len(antigens) >= 5:
            attack_pattern = "apt_suspected"
        else:
            attack_pattern = "related_incidents"

        # Compute severity (max of all antigens)
        severity_map = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.3}
        severity_score = max(
            severity_map.get(ag.severity, 0.5) for ag in antigens
        )

        # Confidence (higher for more antigens)
        confidence = min(0.5 + len(antigens) * 0.1, 0.99)

        correlation_id = f"corr_{int(time.time())}_{hash(source_identifier) % 10000}"

        return CorrelatedEvent(
            correlation_id=correlation_id,
            antigens=antigens,
            event_sources=sources,
            event_timeline=timeline,
            attack_pattern=attack_pattern,
            severity_score=severity_score,
            confidence=confidence,
            metadata={
                "correlation_type": correlation_type,
                "antigen_count": len(antigens),
                "time_span_seconds": max(ag.timestamp for ag in antigens) - min(ag.timestamp for ag in antigens)
            }
        )

    def _detect_attack_chains(self, antigens: List[Antigen]) -> List[List[Antigen]]:
        """
        Detect multi-stage attack chains.

        Common patterns:
        1. Recon → Exploit → Install → C2 → Exfil
        2. Phishing → Malware → Lateral → Data theft
        """
        chains = []

        # Sort by timestamp
        sorted_antigens = sorted(antigens, key=lambda x: x.timestamp)

        # Define attack stages
        stage_keywords = {
            "reconnaissance": ["scan", "recon", "probe"],
            "exploitation": ["exploit", "rce", "sqli", "xss"],
            "installation": ["malware", "trojan", "backdoor"],
            "command_control": ["c2", "botnet"],
            "exfiltration": ["exfil", "data", "steal"]
        }

        # Classify antigens by stage
        staged_antigens = defaultdict(list)
        for ag in sorted_antigens:
            ag_text = f"{ag.malware_family} {ag.metadata.get('description', '')}".lower()

            for stage, keywords in stage_keywords.items():
                if any(kw in ag_text for kw in keywords):
                    staged_antigens[stage].append(ag)
                    break

        # Find sequential chains (at least 2 consecutive stages)
        stage_order = list(stage_keywords.keys())
        for i in range(len(stage_order) - 1):
            stage1 = stage_order[i]
            stage2 = stage_order[i + 1]

            if staged_antigens[stage1] and staged_antigens[stage2]:
                # Combine stages into chain
                chain = staged_antigens[stage1] + staged_antigens[stage2]
                if len(chain) >= 2:
                    chains.append(chain)

        return chains

    async def process_antigens(self) -> List[ProcessedAntigen]:
        """
        Process captured antigens for presentation.

        Steps:
        1. Event correlation
        2. Feature extraction
        3. Context enrichment
        4. Co-stimulation signal generation
        5. Response recommendation
        """
        if self.state not in [DendriticState.SEMI_MATURE, DendriticState.MATURE]:
            return []

        processed = []

        # Correlate events first
        correlated_events = await self.correlate_events()

        # Process each antigen
        for antigen in self.captured_antigens:
            # Find correlated event if exists
            correlated = None
            for event in correlated_events:
                if antigen in event.antigens:
                    correlated = event
                    break

            # Extract features
            feature_vector = self._extract_features(antigen, correlated)

            # Determine co-stimulation level
            costimulation = self._determine_costimulation(antigen, correlated)

            # Recommend response type
            recommended_response = self._recommend_response(antigen, correlated, costimulation)

            # Create processed antigen
            processed_ag = ProcessedAntigen(
                antigen_id=antigen.antigen_id,
                original_antigen=antigen,
                correlated_event=correlated,
                feature_vector=feature_vector,
                presentation_context={
                    "severity": antigen.severity,
                    "confidence": antigen.confidence,
                    "correlated": correlated is not None,
                    "sources": len(correlated.event_sources) if correlated else 1
                },
                costimulation=costimulation,
                recommended_response=recommended_response
            )

            processed.append(processed_ag)
            self.presentation_queue.append(processed_ag)

        self.stats["antigens_processed"] += len(processed)

        logger.info(
            f"[{self.dc_id}] Processed {len(processed)} antigens "
            f"({len(correlated_events)} correlated events)"
        )

        return processed

    def _extract_features(
        self,
        antigen: Antigen,
        correlated: Optional[CorrelatedEvent]
    ) -> np.ndarray:
        """Extract ML feature vector from antigen"""
        features = []

        # Severity encoding
        severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1, "benign": 0}
        features.append(severity_map.get(antigen.severity, 0))

        # Confidence
        features.append(antigen.confidence)

        # IOC count by type
        ioc_counts = defaultdict(int)
        for ioc in antigen.iocs:
            ioc_counts[ioc.get('ioc_type', 'unknown')] += 1

        features.append(ioc_counts.get('ip', 0))
        features.append(ioc_counts.get('domain', 0))
        features.append(ioc_counts.get('url', 0))
        features.append(ioc_counts.get('hash_sha256', 0))

        # Correlation features
        if correlated:
            features.append(len(correlated.antigens))
            features.append(len(correlated.event_sources))
            features.append(correlated.severity_score)
            features.append(correlated.confidence)
        else:
            features.extend([1, 1, 0.5, 0.5])

        # Static features (if available)
        static = antigen.static_features
        features.append(static.get('entropy', 0) / 8.0)  # Normalize
        features.append(static.get('file_size', 0) / 1000000.0)  # MB

        # Pad to fixed size
        while len(features) < 20:
            features.append(0.0)

        return np.array(features[:20], dtype=np.float32)

    def _determine_costimulation(
        self,
        antigen: Antigen,
        correlated: Optional[CorrelatedEvent]
    ) -> ActivationLevel:
        """
        Determine co-stimulation signal strength.

        Biological: CD80/CD86 molecules provide "signal 2" for T cell activation
        Computational: Contextual signals that indicate response urgency
        """
        score = 0

        # Base severity
        if antigen.severity == "critical":
            score += 4
        elif antigen.severity == "high":
            score += 3
        elif antigen.severity == "medium":
            score += 2
        else:
            score += 1

        # Confidence boost
        if antigen.confidence > 0.8:
            score += 2

        # Correlation boost (coordinated attack)
        if correlated:
            score += len(correlated.antigens)
            if correlated.attack_pattern == "apt_suspected":
                score += 3

        # Map to activation level
        if score >= 10:
            return ActivationLevel.CRITICAL
        elif score >= 7:
            return ActivationLevel.HIGH
        elif score >= 4:
            return ActivationLevel.MEDIUM
        elif score >= 2:
            return ActivationLevel.LOW
        else:
            return ActivationLevel.NONE

    def _recommend_response(
        self,
        antigen: Antigen,
        correlated: Optional[CorrelatedEvent],
        costimulation: ActivationLevel
    ) -> str:
        """
        Recommend adaptive immune response type.

        - th1: Cellular immunity (Cytotoxic T cells)
        - th2: Humoral immunity (B cells, antibodies)
        - regulatory: Suppress response (false positive)
        """
        # High severity + high confidence → Th1 (cellular, aggressive)
        if antigen.severity in ["critical", "high"] and antigen.confidence > 0.7:
            return "th1"

        # Correlated event → Th1 (coordinated response)
        if correlated and len(correlated.antigens) >= 3:
            return "th1"

        # Medium severity → Th2 (humoral, signature-based)
        if antigen.severity == "medium":
            return "th2"

        # Low confidence → Regulatory (investigate first)
        if antigen.confidence < 0.5:
            return "regulatory"

        # Default: Th2
        return "th2"

    async def secrete_cytokines(
        self,
        processed_antigens: List[ProcessedAntigen]
    ) -> List[CytokineSignal]:
        """
        Secrete cytokines to activate adaptive immunity.

        Cytokine types:
        - IL-12: Promote Th1 (cellular immunity)
        - IL-4: Promote Th2 (humoral immunity)
        - IFN-α/β: Antiviral response
        - TNF-α: Inflammation
        - IL-10: Regulatory (suppress)
        """
        if self.state != DendriticState.MATURE:
            return []

        cytokines = []

        for ag in processed_antigens:
            # Determine cytokine mix based on recommendation
            if ag.recommended_response == "th1":
                # Th1 response: IL-12 + IFN-α
                cytokines.append(CytokineSignal(
                    cytokine_type=Cytokine.IL_12,
                    concentration=0.8 if ag.costimulation in [ActivationLevel.HIGH, ActivationLevel.CRITICAL] else 0.5,
                    target_cells=["helper_t", "cytotoxic_t"],
                    source_dc=self.dc_id,
                    message={
                        "antigen_id": ag.antigen_id,
                        "severity": ag.original_antigen.severity,
                        "recommendation": "cellular_immunity_required"
                    }
                ))

                cytokines.append(CytokineSignal(
                    cytokine_type=Cytokine.IFN_ALPHA,
                    concentration=0.6,
                    target_cells=["helper_t", "cytotoxic_t", "nk_cell"],
                    source_dc=self.dc_id,
                    message={
                        "antigen_id": ag.antigen_id,
                        "action": "enhance_killing"
                    }
                ))

            elif ag.recommended_response == "th2":
                # Th2 response: IL-4
                cytokines.append(CytokineSignal(
                    cytokine_type=Cytokine.IL_4,
                    concentration=0.7,
                    target_cells=["helper_t", "b_cell"],
                    source_dc=self.dc_id,
                    message={
                        "antigen_id": ag.antigen_id,
                        "recommendation": "antibody_production_required"
                    }
                ))

            elif ag.recommended_response == "regulatory":
                # Regulatory: IL-10
                cytokines.append(CytokineSignal(
                    cytokine_type=Cytokine.IL_10,
                    concentration=0.4,
                    target_cells=["regulatory_t"],
                    source_dc=self.dc_id,
                    message={
                        "antigen_id": ag.antigen_id,
                        "recommendation": "investigate_before_response"
                    }
                ))

            # Critical threats get TNF-α (inflammation)
            if ag.costimulation == ActivationLevel.CRITICAL:
                cytokines.append(CytokineSignal(
                    cytokine_type=Cytokine.TNF_ALPHA,
                    concentration=0.9,
                    target_cells=["helper_t", "cytotoxic_t", "macrophage", "neutrophil"],
                    source_dc=self.dc_id,
                    message={
                        "antigen_id": ag.antigen_id,
                        "alert": "critical_threat_detected"
                    }
                ))

        # Store history
        for cyt in cytokines:
            self.cytokine_history.append(cyt)

        self.stats["cytokines_secreted"] += len(cytokines)

        logger.info(
            f"[{self.dc_id}] Secreted {len(cytokines)} cytokine signals"
        )

        return cytokines

    async def _mature(self):
        """
        Mature dendritic cell.

        Biological: DC matures after capturing antigens, upregulates MHC-II and co-stimulatory molecules
        Computational: Transition to processing and presentation mode
        """
        if self.state == DendriticState.IMMATURE:
            self.state = DendriticState.SEMI_MATURE
            logger.info(f"[{self.dc_id}] Maturing to semi-mature state")

        # Process antigens
        processed = await self.process_antigens()

        if processed:
            self.state = DendriticState.MATURE
            self.stats["maturations"] += 1
            logger.info(
                f"[{self.dc_id}] Fully matured with {len(processed)} processed antigens"
            )

            # Secrete cytokines
            await self.secrete_cytokines(processed)

    def get_stats(self) -> Dict:
        """Get dendritic cell statistics"""
        return {
            **self.stats,
            "state": self.state.value,
            "captured_antigens": len(self.captured_antigens),
            "presentation_queue": len(self.presentation_queue),
            "correlated_events": len(self.correlated_events)
        }


# Test
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("DENDRITIC CELL SERVICE - ANTIGEN PRESENTATION")
    print("="*80 + "\n")

    async def test_dendritic():
        # Initialize DC
        dc = DendriticCore(
            dc_id="dc_001",
            correlation_window_seconds=300,
            maturation_threshold=2
        )

        # Create test antigens
        antigens = [
            Antigen(
                antigen_id="ag_001",
                source_cell="macrophage_1",
                sample_hash="abc123",
                malware_family="ransomware",
                severity="critical",
                static_features={"entropy": 7.8, "file_size": 500000},
                behavioral_features={},
                iocs=[
                    {"ioc_type": "ip", "value": "192.168.1.100"},
                    {"ioc_type": "domain", "value": "malicious.com"}
                ],
                yara_rule="rule test {}",
                confidence=0.9,
                timestamp=time.time(),
                metadata={"description": "ransomware detected"}
            ),
            Antigen(
                antigen_id="ag_002",
                source_cell="neutrophil_1",
                sample_hash="def456",
                malware_family="ransomware",
                severity="high",
                static_features={"entropy": 7.5, "file_size": 450000},
                behavioral_features={},
                iocs=[
                    {"ioc_type": "ip", "value": "192.168.1.100"},
                    {"ioc_type": "domain", "value": "evil.net"}
                ],
                yara_rule=None,
                confidence=0.85,
                timestamp=time.time() + 60,
                metadata={"description": "ransomware propagation"}
            )
        ]

        # Capture antigens
        for ag in antigens:
            await dc.capture_antigen(ag)
            print(f"Captured: {ag.antigen_id} from {ag.source_cell}")

        print()

        # Check presentation queue
        if dc.presentation_queue:
            print(f"Presentation queue: {len(dc.presentation_queue)} antigens")
            for pag in dc.presentation_queue:
                print(f"  {pag.antigen_id}:")
                print(f"    Costimulation: {pag.costimulation}")
                print(f"    Recommended response: {pag.recommended_response}")
                print(f"    Correlated: {pag.correlated_event is not None}")
            print()

        # Check cytokines
        if dc.cytokine_history:
            print(f"Cytokines secreted: {len(dc.cytokine_history)}")
            for cyt in dc.cytokine_history:
                print(f"  {cyt.cytokine_type.value}: concentration={cyt.concentration:.2f}")
                print(f"    Targets: {cyt.target_cells}")
            print()

        # Stats
        print("="*80)
        print("STATISTICS")
        print("="*80)
        stats = dc.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n" + "="*80)
        print("DENDRITIC CELL TEST COMPLETE!")
        print("="*80 + "\n")

    asyncio.run(test_dendritic())
