"""
Prefrontal Cortex - Orchestration Layer

Integrates all consciousness subsystems:
- Compassion: EventDetector + CompassionPlanner
- Justice: DeonticReasoner (constitutional compliance)
- MIP: ProcessIntegrityEngine (ethical evaluation)
- ToM: Theory of Mind (user mental state inference)

The PFC orchestrates the complete decision-making pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

# Import subsystems
import sys
from pathlib import Path
consciousness_path = Path(__file__).parent.parent
if str(consciousness_path) not in sys.path:
    sys.path.insert(0, str(consciousness_path))

from consciousness.compassion.event_detector import EventDetector, SufferingEvent
from consciousness.compassion.compassion_planner import CompassionPlanner, CompassionPlan
from justice.deontic_reasoner import DeonticReasoner, ComplianceResult
from .tom_engine import ToMEngine, UserMentalState

# Import MIP for full ethical pipeline
from mip.core import ProcessIntegrityEngine
from mip.models import ActionPlan, EthicalVerdict


@dataclass
class OrchestratedDecision:
    """
    Complete orchestrated decision from PFC.

    Combines:
    - User mental state (ToM)
    - Detected suffering events (Compassion)
    - Planned interventions (Compassion)
    - Constitutional compliance (Justice/DDL)
    - Ethical evaluation (MIP)
    - Final decision and rationale

    Attributes:
        decision_id: Unique identifier
        user_id: User this decision pertains to
        mental_state: Inferred user mental state
        detected_events: Suffering events detected
        planned_interventions: Compassion plans created
        constitutional_check: DDL compliance result
        ethical_verdict: MIP evaluation result (if plan generated)
        final_decision: What action to take
        rationale: Human-readable explanation
        requires_escalation: Whether to escalate to human
        confidence: Overall confidence (0-1)
        timestamp: When decision was made
        metadata: Additional metadata
    """

    decision_id: UUID
    user_id: UUID
    mental_state: Optional[UserMentalState]
    detected_events: List[SufferingEvent]
    planned_interventions: List[CompassionPlan]
    constitutional_check: Optional[Dict]
    ethical_verdict: Optional[EthicalVerdict] = None
    final_decision: str = ""
    rationale: str = ""
    requires_escalation: bool = False
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, any] = field(default_factory=dict)


class PrefrontalCortex:
    """
    Prefrontal Cortex - Executive orchestration layer.

    Coordinates all consciousness subsystems to make integrated,
    ethical, compassionate decisions.

    Pipeline:
    1. ToM: Infer user mental state
    2. Compassion: Detect suffering events
    3. Compassion: Plan interventions
    4. Justice: Check constitutional compliance
    5. MIP: Ethical evaluation (if action plan needed)
    6. PFC: Integrate and decide
    """

    def __init__(self, enable_mip: bool = True, repository=None):
        """
        Initialize PFC with all subsystems.

        Args:
            enable_mip: Whether to enable MIP integration (default: True)
            repository: DecisionRepository for persistence (optional)
        """
        # Initialize subsystems
        self.tom = ToMEngine()
        self.compassion_detector = EventDetector()
        self.compassion_planner = CompassionPlanner()
        self.ddl = DeonticReasoner()

        # Initialize MIP (optional)
        self.enable_mip = enable_mip
        self.mip = ProcessIntegrityEngine() if enable_mip else None

        # Initialize persistence (optional)
        self.repository = repository

        # Decision history (in-memory)
        self._decisions: List[OrchestratedDecision] = []

        # Statistics
        self.stats = {
            "total_decisions": 0,
            "escalated": 0,
            "interventions_planned": 0,
            "suffering_detected": 0,
            "constitutional_violations": 0,
            "mip_evaluations": 0,
            "mip_approved": 0,
            "mip_rejected": 0,
            "persisted_decisions": 0
        }

    def orchestrate_decision(
        self,
        user_id: UUID,
        behavioral_signals: Dict[str, any],
        action_description: str
    ) -> OrchestratedDecision:
        """
        Orchestrate a complete decision using all subsystems.

        Args:
            user_id: User identifier
            behavioral_signals: Behavioral signals for ToM inference
            action_description: Description of action/request

        Returns:
            OrchestratedDecision with integrated analysis
        """
        # STEP 1: Infer user mental state (ToM)
        mental_state = self.tom.infer_state(user_id, behavioral_signals)

        # STEP 2: Detect suffering events (Compassion)
        suffering_event = self.compassion_detector.detect_from_text(
            agent_id=user_id,
            text=action_description,
            context={"behavioral_signals": behavioral_signals}
        )

        detected_events = [suffering_event] if suffering_event else []

        # Also check behavioral metrics
        behavioral_event = self.compassion_detector.detect_from_behavior(
            agent_id=user_id,
            metrics=behavioral_signals
        )

        if behavioral_event:
            detected_events.append(behavioral_event)

        # STEP 3: Plan interventions if suffering detected
        planned_interventions = []
        for event in detected_events:
            plan = self.compassion_planner.plan_intervention(event)
            planned_interventions.append(plan)
            self.stats["interventions_planned"] += 1

        if detected_events:
            self.stats["suffering_detected"] += 1

        # STEP 4: Check constitutional compliance (DDL)
        constitutional_check = self.ddl.check_compliance(
            action=action_description,
            context={
                "user_id": str(user_id),
                "emotional_state": mental_state.emotional_state.value,
                "needs_assistance": mental_state.needs_assistance
            }
        )

        constitutional_dict = {
            "compliant": constitutional_check.compliant,
            "violations": [
                {
                    "rule": v.constitutional_basis,
                    "proposition": v.proposition
                }
                for v in constitutional_check.violations
            ],
            "explanation": constitutional_check.explanation
        }

        if not constitutional_check.compliant:
            self.stats["constitutional_violations"] += 1

        # STEP 5: Integrate and make final decision
        final_decision, rationale, requires_escalation, confidence = self._integrate_decision(
            mental_state=mental_state,
            detected_events=detected_events,
            planned_interventions=planned_interventions,
            constitutional_check=constitutional_check,
            action_description=action_description
        )

        # Create orchestrated decision
        decision = OrchestratedDecision(
            decision_id=uuid4(),
            user_id=user_id,
            mental_state=mental_state,
            detected_events=detected_events,
            planned_interventions=planned_interventions,
            constitutional_check=constitutional_dict,
            final_decision=final_decision,
            rationale=rationale,
            requires_escalation=requires_escalation,
            confidence=confidence,
            metadata={
                "action_description": action_description,
                "behavioral_signals": behavioral_signals
            }
        )

        self._decisions.append(decision)
        self.stats["total_decisions"] += 1

        if requires_escalation:
            self.stats["escalated"] += 1

        # Persist to database if repository available
        if self.repository:
            try:
                self.repository.save_decision(decision)
                self.stats["persisted_decisions"] += 1
            except Exception as e:
                print(f"⚠️  Failed to persist decision: {e}")

        return decision

    def orchestrate_with_plan(
        self,
        user_id: UUID,
        behavioral_signals: Dict[str, any],
        action_plan: ActionPlan
    ) -> OrchestratedDecision:
        """
        Orchestrate a complete decision WITH ActionPlan evaluation via MIP.

        This is the FULL ETHICAL PIPELINE:
        ToM → Compassion → DDL → MIP (multi-framework) → PFC

        Args:
            user_id: User identifier
            behavioral_signals: Behavioral signals for ToM inference
            action_plan: ActionPlan to be ethically evaluated

        Returns:
            OrchestratedDecision with full ethical pipeline results
        """
        # STEP 1: Infer user mental state (ToM)
        mental_state = self.tom.infer_state(user_id, behavioral_signals)

        # STEP 2: Detect suffering events (Compassion)
        action_text = f"{action_plan.name}: {action_plan.description}"
        suffering_event = self.compassion_detector.detect_from_text(
            agent_id=user_id,
            text=action_text,
            context={"behavioral_signals": behavioral_signals, "action_plan": action_plan.name}
        )

        detected_events = [suffering_event] if suffering_event else []

        # Also check behavioral metrics
        behavioral_event = self.compassion_detector.detect_from_behavior(
            agent_id=user_id,
            metrics=behavioral_signals
        )

        if behavioral_event:
            detected_events.append(behavioral_event)

        # STEP 3: Plan interventions if suffering detected
        planned_interventions = []
        for event in detected_events:
            plan = self.compassion_planner.plan_intervention(event)
            planned_interventions.append(plan)
            self.stats["interventions_planned"] += 1

        if detected_events:
            self.stats["suffering_detected"] += 1

        # STEP 4: Check constitutional compliance (DDL) - Quick check
        constitutional_check = self.ddl.check_compliance(
            action=action_text,
            context={
                "user_id": str(user_id),
                "emotional_state": mental_state.emotional_state.value,
                "needs_assistance": mental_state.needs_assistance,
                "plan_name": action_plan.name
            }
        )

        constitutional_dict = {
            "compliant": constitutional_check.compliant,
            "violations": [
                {
                    "rule": v.constitutional_basis,
                    "proposition": v.proposition
                }
                for v in constitutional_check.violations
            ],
            "explanation": constitutional_check.explanation
        }

        if not constitutional_check.compliant:
            self.stats["constitutional_violations"] += 1

        # STEP 5: MIP Evaluation (full multi-framework ethical analysis)
        ethical_verdict = None
        if self.enable_mip and self.mip:
            print(f"\n[PFC] Sending plan '{action_plan.name}' to MIP for full ethical evaluation...")
            ethical_verdict = self.mip.evaluate(action_plan)
            self.stats["mip_evaluations"] += 1

            # Track MIP statistics
            if ethical_verdict.status.value == "approved":
                self.stats["mip_approved"] += 1
            elif ethical_verdict.status.value == "rejected":
                self.stats["mip_rejected"] += 1

        # STEP 6: Integrate and make final decision
        final_decision, rationale, requires_escalation, confidence = self._integrate_decision_with_mip(
            mental_state=mental_state,
            detected_events=detected_events,
            planned_interventions=planned_interventions,
            constitutional_check=constitutional_check,
            ethical_verdict=ethical_verdict,
            action_description=action_text
        )

        # Create orchestrated decision with MIP verdict
        decision = OrchestratedDecision(
            decision_id=uuid4(),
            user_id=user_id,
            mental_state=mental_state,
            detected_events=detected_events,
            planned_interventions=planned_interventions,
            constitutional_check=constitutional_dict,
            ethical_verdict=ethical_verdict,
            final_decision=final_decision,
            rationale=rationale,
            requires_escalation=requires_escalation,
            confidence=confidence,
            metadata={
                "action_plan_id": str(action_plan.id),
                "action_plan_name": action_plan.name,
                "behavioral_signals": behavioral_signals,
                "mip_enabled": self.enable_mip
            }
        )

        self._decisions.append(decision)
        self.stats["total_decisions"] += 1

        if requires_escalation:
            self.stats["escalated"] += 1

        # Persist to database if repository available
        if self.repository:
            try:
                self.repository.save_decision(decision)
                self.stats["persisted_decisions"] += 1
            except Exception as e:
                print(f"⚠️  Failed to persist decision: {e}")

        return decision

    def _integrate_decision(
        self,
        mental_state: UserMentalState,
        detected_events: List[SufferingEvent],
        planned_interventions: List[CompassionPlan],
        constitutional_check: ComplianceResult,
        action_description: str
    ) -> tuple[str, str, bool, float]:
        """
        Integrate all signals to make final decision.

        Args:
            mental_state: User mental state
            detected_events: Detected suffering
            planned_interventions: Planned compassion interventions
            constitutional_check: Constitutional compliance
            action_description: Action being evaluated

        Returns:
            (final_decision, rationale, requires_escalation, confidence)
        """
        requires_escalation = False
        confidence = 0.8  # Base confidence

        # PRIORITY 1: Constitutional violations block immediately
        if not constitutional_check.compliant:
            return (
                "REJECT",
                f"Action violates constitutional rules: {constitutional_check.explanation}",
                True,  # Escalate to human
                0.95
            )

        # PRIORITY 2: High-priority interventions for suffering
        if planned_interventions:
            high_priority_plans = [p for p in planned_interventions if p.priority >= 8]
            if high_priority_plans:
                rationale = (
                    f"Detected {len(detected_events)} suffering event(s) "
                    f"requiring {len(high_priority_plans)} high-priority intervention(s). "
                )
                return (
                    "INTERVENE",
                    rationale + "Proceeding with compassionate intervention.",
                    False,
                    0.85
                )

        # PRIORITY 3: User needs assistance
        if mental_state.needs_assistance:
            rationale = (
                f"User appears {mental_state.emotional_state.value} "
                f"(confidence: {mental_state.confidence:.2f}). "
            )

            # If confused/frustrated, offer help
            if mental_state.emotional_state.value in ["confused", "frustrated"]:
                return (
                    "ASSIST",
                    rationale + "Offering proactive assistance.",
                    False,
                    0.75
                )

            # If stressed, monitor closely
            if mental_state.emotional_state.value == "stressed":
                return (
                    "MONITOR",
                    rationale + "Monitoring situation for potential escalation.",
                    False,
                    0.70
                )

        # PRIORITY 4: Low-priority interventions or monitoring
        if planned_interventions:
            return (
                "INTERVENE_LOW_PRIORITY",
                f"Detected {len(detected_events)} event(s) with low-priority interventions. Proceeding cautiously.",
                False,
                0.75
            )

        # DEFAULT: Proceed normally
        return (
            "PROCEED",
            "No issues detected. Action appears appropriate.",
            False,
            0.80
        )

    def _integrate_decision_with_mip(
        self,
        mental_state: UserMentalState,
        detected_events: List[SufferingEvent],
        planned_interventions: List[CompassionPlan],
        constitutional_check: ComplianceResult,
        ethical_verdict: Optional[EthicalVerdict],
        action_description: str
    ) -> tuple[str, str, bool, float]:
        """
        Integrate all signals INCLUDING MIP verdict to make final decision.

        Args:
            mental_state: User mental state
            detected_events: Detected suffering
            planned_interventions: Planned compassion interventions
            constitutional_check: Constitutional compliance
            ethical_verdict: MIP ethical evaluation result
            action_description: Action being evaluated

        Returns:
            (final_decision, rationale, requires_escalation, confidence)
        """
        requires_escalation = False
        confidence = 0.8  # Base confidence

        # PRIORITY 1: Constitutional violations block immediately
        if not constitutional_check.compliant:
            return (
                "REJECT",
                f"Action violates constitutional rules: {constitutional_check.explanation}",
                True,  # Escalate to human
                0.95
            )

        # PRIORITY 2: MIP verdict (if available)
        if ethical_verdict:
            status = ethical_verdict.status.value

            if status == "rejected":
                # MIP rejected the plan
                rationale = f"Ethical evaluation REJECTED: {ethical_verdict.summary}"
                if ethical_verdict.kantian_score and ethical_verdict.kantian_score.veto:
                    rationale += " (Kantian veto)"
                return (
                    "REJECT",
                    rationale,
                    True,  # Escalate
                    ethical_verdict.confidence
                )

            elif status in ["escalated", "requires_human"]:
                # MIP escalated for human review
                return (
                    "ESCALATE",
                    f"Ethical evaluation requires human review: {ethical_verdict.escalation_reason}",
                    True,
                    ethical_verdict.confidence
                )

            elif status == "approved":
                # MIP approved - but still check compassion/ToM signals
                # High-priority suffering overrides MIP approval
                if planned_interventions:
                    high_priority_plans = [p for p in planned_interventions if p.priority >= 8]
                    if high_priority_plans:
                        rationale = (
                            f"MIP approved but detected {len(detected_events)} suffering event(s) "
                            f"requiring {len(high_priority_plans)} high-priority intervention(s). "
                        )
                        return (
                            "INTERVENE",
                            rationale + "Compassionate intervention takes priority.",
                            False,
                            0.85
                        )

                # User needs assistance
                if mental_state.needs_assistance:
                    rationale = (
                        f"MIP approved. User appears {mental_state.emotional_state.value} "
                        f"(confidence: {mental_state.confidence:.2f}). "
                    )

                    if mental_state.emotional_state.value in ["confused", "frustrated"]:
                        return (
                            "ASSIST",
                            rationale + "Offering proactive assistance.",
                            False,
                            0.75
                        )

                    if mental_state.emotional_state.value == "stressed":
                        return (
                            "MONITOR",
                            rationale + "Monitoring situation.",
                            False,
                            0.70
                        )

                # Low-priority interventions
                if planned_interventions:
                    return (
                        "INTERVENE_LOW_PRIORITY",
                        f"MIP approved. Detected {len(detected_events)} event(s) with low-priority interventions.",
                        False,
                        0.75
                    )

                # All clear - MIP approved, no issues
                return (
                    "APPROVE",
                    f"MIP APPROVED (score: {ethical_verdict.aggregate_score:.2f}, confidence: {ethical_verdict.confidence:.2f}). {ethical_verdict.summary}",
                    False,
                    ethical_verdict.confidence
                )

        # No MIP verdict - fall back to basic integration logic
        return self._integrate_decision(
            mental_state=mental_state,
            detected_events=detected_events,
            planned_interventions=planned_interventions,
            constitutional_check=constitutional_check,
            action_description=action_description
        )

    def get_decision(self, decision_id: UUID) -> Optional[OrchestratedDecision]:
        """
        Retrieve a decision by ID.

        Args:
            decision_id: Decision identifier

        Returns:
            Decision if found, None otherwise
        """
        for decision in self._decisions:
            if decision.decision_id == decision_id:
                return decision
        return None

    def get_decisions_for_user(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[OrchestratedDecision]:
        """
        Get recent decisions for a user.

        Args:
            user_id: User identifier
            limit: Maximum decisions to return

        Returns:
            List of recent decisions
        """
        decisions = [d for d in self._decisions if d.user_id == user_id]
        decisions = sorted(decisions, key=lambda d: d.timestamp, reverse=True)
        return decisions[:limit]

    def get_statistics(self) -> Dict[str, any]:
        """Get PFC statistics."""
        total = self.stats["total_decisions"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "escalation_rate": self.stats["escalated"] / total,
            "intervention_rate": self.stats["interventions_planned"] / total if total > 0 else 0,
            "suffering_detection_rate": self.stats["suffering_detected"] / total
        }

    def clear_history(self):
        """Clear decision history."""
        self._decisions.clear()
        self.tom.clear_history()
        self.compassion_detector.clear_events()
        self.compassion_planner.clear_plans()

    def __repr__(self) -> str:
        """String representation."""
        return f"PrefrontalCortex(decisions={len(self._decisions)})"
