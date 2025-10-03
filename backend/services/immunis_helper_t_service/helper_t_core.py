"""
Immunis - Helper T Cell Service
===============================
Immune response orchestration and strategy selection.

Biological inspiration: Helper T Cells (CD4+)
- Central coordinators of adaptive immunity
- Receive antigen presentation from DCs
- Differentiate into subsets based on cytokines:
  - Th1: Cellular immunity (vs intracellular pathogens)
  - Th2: Humoral immunity (vs extracellular pathogens)
  - Th17: Inflammatory response (vs bacteria/fungi)
  - Treg: Regulatory (prevent autoimmunity)
- Secrete cytokines to direct other cells
- Activate B cells and Cytotoxic T cells

Computational implementation:
- Strategy selection (Th1 vs Th2 vs Treg)
- Orchestration of immune response
- Cytokine-based communication (Kafka)
- Decision making based on threat context
- Coordination of B cells and CTLs
- Feedback regulation
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class HelperSubset(str, Enum):
    """Helper T cell subsets"""
    TH0 = "th0"  # Naive, undifferentiated
    TH1 = "th1"  # Cellular immunity (CTL activation)
    TH2 = "th2"  # Humoral immunity (B cell activation)
    TH17 = "th17"  # Inflammatory response
    TREG = "treg"  # Regulatory (suppress response)


class ResponseStrategy(str, Enum):
    """Immune response strategies"""
    AGGRESSIVE_CELLULAR = "aggressive_cellular"  # Th1-dominant
    BALANCED_HUMORAL = "balanced_humoral"  # Th2-dominant
    INFLAMMATORY = "inflammatory"  # Th17-dominant
    REGULATORY = "regulatory"  # Treg-dominant
    MIXED = "mixed"  # Combined response


class Cytokine(str, Enum):
    """Cytokines secreted by Helper T cells"""
    # Th1 cytokines
    IL_2 = "il2"  # T cell proliferation
    IFN_GAMMA = "ifn_gamma"  # Macrophage activation, CTL activation
    TNF_BETA = "tnf_beta"  # Inflammation

    # Th2 cytokines
    IL_4 = "il4"  # B cell activation
    IL_5 = "il5"  # Eosinophil activation
    IL_13 = "il13"  # Alternative macrophage activation

    # Th17 cytokines
    IL_17 = "il17"  # Neutrophil recruitment
    IL_22 = "il22"  # Antimicrobial peptides

    # Treg cytokines
    IL_10 = "il10"  # Anti-inflammatory
    TGF_BETA = "tgf_beta"  # Immune suppression


@dataclass
class AntigenPresentation:
    """Antigen presented by dendritic cell"""
    antigen_id: str
    dc_id: str
    malware_family: str
    severity: str
    confidence: float
    costimulation: str  # Activation level
    recommended_response: str  # th1, th2, regulatory
    correlated: bool
    feature_vector: List[float]
    presentation_context: Dict
    timestamp: float


@dataclass
class ImmuneResponse:
    """Coordinated immune response"""
    response_id: str
    strategy: ResponseStrategy
    helper_subset: HelperSubset

    # Activated cells
    b_cells_activated: List[str]
    ctl_cells_activated: List[str]
    other_cells_activated: List[str]

    # Cytokines secreted
    cytokines_secreted: List[Dict]

    # Targets
    targets: Set[str]  # Threat sources to eliminate

    # Timeline
    initiated_at: float
    expected_duration_seconds: int

    # Outcome
    completed: bool = False
    success_rate: float = 0.0
    threats_neutralized: int = 0

    metadata: Dict = field(default_factory=dict)


@dataclass
class CytokineSignal:
    """Cytokine signal to other immune cells"""
    cytokine_type: Cytokine
    concentration: float
    target_cells: List[str]
    source_helper: str
    message: Dict
    timestamp: float = field(default_factory=time.time)


class HelperTCore:
    """
    Helper T Cell - Immune response orchestrator.

    Decision process:
    1. Receive antigen from DC
    2. Read cytokine context (IL-12 → Th1, IL-4 → Th2)
    3. Differentiate to appropriate subset
    4. Select response strategy
    5. Activate B cells and/or CTLs
    6. Secrete directing cytokines
    7. Monitor response
    8. Provide feedback regulation

    Key functions:
    - Strategy selection
    - Cell activation
    - Cytokine orchestration
    - Response monitoring
    - Feedback control
    """

    def __init__(
        self,
        helper_id: str,
        default_subset: HelperSubset = HelperSubset.TH0
    ):
        self.helper_id = helper_id
        self.current_subset = default_subset

        # Active responses
        self.active_responses: Dict[str, ImmuneResponse] = {}

        # Cytokine sensing (from DCs)
        self.sensed_cytokines: Dict[Cytokine, float] = defaultdict(float)

        # Statistics
        self.stats = {
            "antigens_received": 0,
            "responses_orchestrated": 0,
            "b_cells_activated": 0,
            "ctl_activated": 0,
            "cytokines_secreted": 0,
            "th1_responses": 0,
            "th2_responses": 0,
            "treg_responses": 0
        }

        logger.info(
            f"Helper T Cell {helper_id} initialized (subset={default_subset.value})"
        )

    async def receive_antigen(
        self,
        presentation: AntigenPresentation,
        dc_cytokines: List[Dict]
    ) -> ImmuneResponse:
        """
        Receive antigen presentation from dendritic cell.

        Biological: TCR (T cell receptor) binds MHC-II-peptide complex
        Computational: Process antigen and decide response

        Args:
            presentation: Antigen presented by DC
            dc_cytokines: Cytokines from DC (IL-12, IL-4, etc.)

        Returns:
            Orchestrated immune response
        """
        logger.info(
            f"[{self.helper_id}] Received antigen {presentation.antigen_id} "
            f"from {presentation.dc_id}"
        )

        self.stats["antigens_received"] += 1

        # Sense cytokine context
        for cyt_data in dc_cytokines:
            cyt_type = Cytokine(cyt_data['cytokine_type'])
            concentration = cyt_data['concentration']
            self.sensed_cytokines[cyt_type] += concentration

        # Differentiate based on cytokines
        await self._differentiate(dc_cytokines)

        # Select response strategy
        strategy = self._select_strategy(presentation, dc_cytokines)

        # Orchestrate response
        response = await self._orchestrate_response(presentation, strategy)

        self.stats["responses_orchestrated"] += 1

        return response

    async def _differentiate(self, dc_cytokines: List[Dict]):
        """
        Differentiate to appropriate subset based on cytokines.

        Biological differentiation signals:
        - IL-12 + IFN-γ → Th1
        - IL-4 → Th2
        - IL-6 + TGF-β → Th17
        - TGF-β + IL-2 → Treg
        """
        if self.current_subset != HelperSubset.TH0:
            # Already differentiated
            return

        # Count cytokine signals
        th1_signals = 0
        th2_signals = 0
        th17_signals = 0
        treg_signals = 0

        for cyt_data in dc_cytokines:
            cyt_type = cyt_data.get('cytokine_type', '')

            if cyt_type in ['il12', 'ifn_alpha']:
                th1_signals += 1
            elif cyt_type == 'il4':
                th2_signals += 1
            elif cyt_type == 'il6':
                th17_signals += 1
            elif cyt_type == 'il10':
                treg_signals += 1

        # Differentiate to dominant signal
        if th1_signals > max(th2_signals, th17_signals, treg_signals):
            self.current_subset = HelperSubset.TH1
            logger.info(f"[{self.helper_id}] Differentiated to Th1 (cellular immunity)")

        elif th2_signals > max(th1_signals, th17_signals, treg_signals):
            self.current_subset = HelperSubset.TH2
            logger.info(f"[{self.helper_id}] Differentiated to Th2 (humoral immunity)")

        elif th17_signals > max(th1_signals, th2_signals, treg_signals):
            self.current_subset = HelperSubset.TH17
            logger.info(f"[{self.helper_id}] Differentiated to Th17 (inflammatory)")

        elif treg_signals > 0:
            self.current_subset = HelperSubset.TREG
            logger.info(f"[{self.helper_id}] Differentiated to Treg (regulatory)")

        else:
            # Default to Th1 for unknown threats
            self.current_subset = HelperSubset.TH1

    def _select_strategy(
        self,
        presentation: AntigenPresentation,
        dc_cytokines: List[Dict]
    ) -> ResponseStrategy:
        """
        Select immune response strategy.

        Decision factors:
        - Threat severity
        - Confidence
        - Correlation (coordinated attack?)
        - Current subset
        - DC recommendation
        """
        severity = presentation.severity
        confidence = presentation.confidence
        recommended = presentation.recommended_response
        correlated = presentation.correlated

        # Critical threats → Aggressive
        if severity == "critical" and confidence > 0.8:
            if correlated:
                return ResponseStrategy.MIXED  # Full arsenal
            else:
                return ResponseStrategy.AGGRESSIVE_CELLULAR

        # High severity → Cellular or Mixed
        if severity == "high":
            if self.current_subset == HelperSubset.TH1:
                return ResponseStrategy.AGGRESSIVE_CELLULAR
            elif self.current_subset == HelperSubset.TH2:
                return ResponseStrategy.BALANCED_HUMORAL
            else:
                return ResponseStrategy.MIXED

        # Medium severity → Balanced
        if severity == "medium":
            if recommended == "th2":
                return ResponseStrategy.BALANCED_HUMORAL
            else:
                return ResponseStrategy.AGGRESSIVE_CELLULAR

        # Low severity or low confidence → Regulatory
        if severity == "low" or confidence < 0.5:
            return ResponseStrategy.REGULATORY

        # Default: balanced
        return ResponseStrategy.BALANCED_HUMORAL

    async def _orchestrate_response(
        self,
        presentation: AntigenPresentation,
        strategy: ResponseStrategy
    ) -> ImmuneResponse:
        """
        Orchestrate immune response based on strategy.

        Activates appropriate immune cells and directs their actions.
        """
        logger.info(
            f"[{self.helper_id}] Orchestrating {strategy.value} response "
            f"for {presentation.malware_family}"
        )

        response_id = f"resp_{int(time.time())}_{hash(presentation.antigen_id) % 10000}"

        b_cells = []
        ctl_cells = []
        other_cells = []
        cytokines = []

        # Strategy-specific orchestration
        if strategy == ResponseStrategy.AGGRESSIVE_CELLULAR:
            # Th1 response: Activate CTLs
            ctl_cells = await self._activate_cytotoxic_t_cells(presentation)
            self.stats["ctl_activated"] += len(ctl_cells)
            self.stats["th1_responses"] += 1

            # Secrete Th1 cytokines
            cytokines.extend([
                self._secrete_cytokine(
                    Cytokine.IL_2,
                    concentration=0.8,
                    targets=["cytotoxic_t"],
                    message={"action": "proliferate_and_kill"}
                ),
                self._secrete_cytokine(
                    Cytokine.IFN_GAMMA,
                    concentration=0.9,
                    targets=["macrophage", "cytotoxic_t"],
                    message={"action": "enhance_killing"}
                )
            ])

        elif strategy == ResponseStrategy.BALANCED_HUMORAL:
            # Th2 response: Activate B cells
            b_cells = await self._activate_b_cells(presentation)
            self.stats["b_cells_activated"] += len(b_cells)
            self.stats["th2_responses"] += 1

            # Secrete Th2 cytokines
            cytokines.extend([
                self._secrete_cytokine(
                    Cytokine.IL_4,
                    concentration=0.8,
                    targets=["b_cell"],
                    message={"action": "produce_antibodies"}
                ),
                self._secrete_cytokine(
                    Cytokine.IL_5,
                    concentration=0.6,
                    targets=["b_cell"],
                    message={"action": "class_switching"}
                )
            ])

        elif strategy == ResponseStrategy.INFLAMMATORY:
            # Th17 response: Recruit neutrophils
            other_cells = await self._recruit_neutrophils(presentation)

            cytokines.append(
                self._secrete_cytokine(
                    Cytokine.IL_17,
                    concentration=0.9,
                    targets=["neutrophil"],
                    message={"action": "rapid_response"}
                )
            )

        elif strategy == ResponseStrategy.REGULATORY:
            # Treg response: Suppress (investigate further)
            self.stats["treg_responses"] += 1

            cytokines.append(
                self._secrete_cytokine(
                    Cytokine.IL_10,
                    concentration=0.7,
                    targets=["dendritic", "macrophage"],
                    message={"action": "suppress_until_verified"}
                )
            )

        elif strategy == ResponseStrategy.MIXED:
            # Full response: B cells + CTLs
            b_cells = await self._activate_b_cells(presentation)
            ctl_cells = await self._activate_cytotoxic_t_cells(presentation)

            self.stats["b_cells_activated"] += len(b_cells)
            self.stats["ctl_activated"] += len(ctl_cells)

            # Mixed cytokines
            cytokines.extend([
                self._secrete_cytokine(Cytokine.IL_2, 0.8, ["cytotoxic_t"], {}),
                self._secrete_cytokine(Cytokine.IL_4, 0.7, ["b_cell"], {}),
                self._secrete_cytokine(Cytokine.IFN_GAMMA, 0.9, ["macrophage", "cytotoxic_t"], {})
            ])

        # Extract targets from antigen
        targets = set()
        for ioc in presentation.presentation_context.get('iocs', []):
            if ioc.get('ioc_type') in ['ip', 'domain']:
                targets.add(ioc['value'])

        # Create response record
        response = ImmuneResponse(
            response_id=response_id,
            strategy=strategy,
            helper_subset=self.current_subset,
            b_cells_activated=b_cells,
            ctl_cells_activated=ctl_cells,
            other_cells_activated=other_cells,
            cytokines_secreted=[cyt.__dict__ for cyt in cytokines],
            targets=targets,
            initiated_at=time.time(),
            expected_duration_seconds=self._estimate_duration(strategy),
            metadata={
                "antigen_id": presentation.antigen_id,
                "malware_family": presentation.malware_family,
                "severity": presentation.severity
            }
        )

        self.active_responses[response_id] = response
        self.stats["cytokines_secreted"] += len(cytokines)

        logger.info(
            f"[{self.helper_id}] Response orchestrated: "
            f"{len(b_cells)} B cells, {len(ctl_cells)} CTLs activated"
        )

        return response

    async def _activate_b_cells(self, presentation: AntigenPresentation) -> List[str]:
        """
        Activate B cells for antibody production.

        Sends signal to B Cell Service via Kafka.
        """
        # In production: publish to Kafka topic "bcell.activation"
        # For now: simulate
        num_b_cells = 3 if presentation.severity == "critical" else 1

        b_cell_ids = [f"bcell_{i}_{int(time.time())}" for i in range(num_b_cells)]

        logger.info(
            f"[{self.helper_id}] Activated {len(b_cell_ids)} B cells "
            f"for {presentation.malware_family}"
        )

        return b_cell_ids

    async def _activate_cytotoxic_t_cells(self, presentation: AntigenPresentation) -> List[str]:
        """
        Activate Cytotoxic T cells for direct killing.

        Sends signal to CTL Service via Kafka.
        """
        # In production: publish to Kafka topic "ctl.activation"
        num_ctls = 5 if presentation.severity == "critical" else 2

        ctl_ids = [f"ctl_{i}_{int(time.time())}" for i in range(num_ctls)]

        logger.info(
            f"[{self.helper_id}] Activated {len(ctl_ids)} CTLs "
            f"for {presentation.malware_family}"
        )

        return ctl_ids

    async def _recruit_neutrophils(self, presentation: AntigenPresentation) -> List[str]:
        """Recruit neutrophils for rapid response"""
        num_neutrophils = 10 if presentation.severity == "critical" else 5

        neutrophil_ids = [f"neut_{i}_{int(time.time())}" for i in range(num_neutrophils)]

        logger.info(
            f"[{self.helper_id}] Recruited {len(neutrophil_ids)} neutrophils"
        )

        return neutrophil_ids

    def _secrete_cytokine(
        self,
        cytokine_type: Cytokine,
        concentration: float,
        targets: List[str],
        message: Dict
    ) -> CytokineSignal:
        """Secrete cytokine signal"""
        return CytokineSignal(
            cytokine_type=cytokine_type,
            concentration=concentration,
            target_cells=targets,
            source_helper=self.helper_id,
            message=message
        )

    def _estimate_duration(self, strategy: ResponseStrategy) -> int:
        """Estimate response duration in seconds"""
        durations = {
            ResponseStrategy.AGGRESSIVE_CELLULAR: 300,  # 5 minutes
            ResponseStrategy.BALANCED_HUMORAL: 600,  # 10 minutes
            ResponseStrategy.INFLAMMATORY: 180,  # 3 minutes
            ResponseStrategy.REGULATORY: 3600,  # 1 hour (investigation)
            ResponseStrategy.MIXED: 900  # 15 minutes
        }
        return durations.get(strategy, 300)

    async def monitor_response(self, response_id: str) -> Dict:
        """
        Monitor ongoing immune response.

        Checks progress and provides feedback.
        """
        if response_id not in self.active_responses:
            return {"error": "Response not found"}

        response = self.active_responses[response_id]

        # Check if completed
        elapsed = time.time() - response.initiated_at
        if elapsed >= response.expected_duration_seconds:
            response.completed = True

            # Simulate success (in production: check actual metrics)
            response.success_rate = 0.95
            response.threats_neutralized = len(response.targets)

        return {
            "response_id": response_id,
            "strategy": response.strategy.value,
            "elapsed_seconds": elapsed,
            "expected_duration": response.expected_duration_seconds,
            "completed": response.completed,
            "success_rate": response.success_rate,
            "threats_neutralized": response.threats_neutralized
        }

    def get_stats(self) -> Dict:
        """Get Helper T cell statistics"""
        return {
            **self.stats,
            "current_subset": self.current_subset.value,
            "active_responses": len(self.active_responses)
        }


# Test
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("HELPER T CELL SERVICE - IMMUNE ORCHESTRATION")
    print("="*80 + "\n")

    async def test_helper_t():
        # Initialize Helper T cell
        helper = HelperTCore(helper_id="helper_001")

        # Mock antigen presentation
        presentation = AntigenPresentation(
            antigen_id="ag_001",
            dc_id="dc_001",
            malware_family="ransomware",
            severity="critical",
            confidence=0.9,
            costimulation="high",
            recommended_response="th1",
            correlated=True,
            feature_vector=[0.9, 0.8, 7.5, 500000],
            presentation_context={"iocs": [{"ioc_type": "ip", "value": "192.168.1.100"}]},
            timestamp=time.time()
        )

        # DC cytokines (promote Th1)
        dc_cytokines = [
            {"cytokine_type": "il12", "concentration": 0.8},
            {"cytokine_type": "ifn_alpha", "concentration": 0.7}
        ]

        print(f"Antigen presentation: {presentation.malware_family}")
        print(f"  Severity: {presentation.severity}")
        print(f"  DC recommendation: {presentation.recommended_response}")
        print()

        # Receive antigen and orchestrate response
        response = await helper.receive_antigen(presentation, dc_cytokines)

        print(f"Response orchestrated:")
        print(f"  ID: {response.response_id}")
        print(f"  Strategy: {response.strategy.value}")
        print(f"  Helper subset: {response.helper_subset.value}")
        print(f"  B cells activated: {len(response.b_cells_activated)}")
        print(f"  CTLs activated: {len(response.ctl_cells_activated)}")
        print(f"  Cytokines secreted: {len(response.cytokines_secreted)}")
        print()

        for cyt in response.cytokines_secreted:
            print(f"  Cytokine: {cyt['cytokine_type']}")
            print(f"    Concentration: {cyt['concentration']:.2f}")
            print(f"    Targets: {cyt['target_cells']}")

        print()

        # Monitor response
        print("Monitoring response...")
        await asyncio.sleep(1)
        status = await helper.monitor_response(response.response_id)
        print(f"  Status: {status}")
        print()

        # Stats
        print("="*80)
        print("STATISTICS")
        print("="*80)
        stats = helper.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n" + "="*80)
        print("HELPER T CELL TEST COMPLETE!")
        print("="*80 + "\n")

    asyncio.run(test_helper_t())
