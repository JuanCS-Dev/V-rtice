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

from compassion.event_detector import EventDetector, SufferingEvent
from compassion.compassion_planner import CompassionPlanner, CompassionPlan
from justice.deontic_reasoner import DeonticReasoner, ComplianceResult
from .tom_engine import ToMEngine, UserMentalState


@dataclass
class OrchestratedDecision:
    """
    Complete orchestrated decision from PFC.

    Combines:
    - User mental state (ToM)
    - Detected suffering events (Compassion)
    - Planned interventions (Compassion)
    - Constitutional compliance (Justice/DDL)
    - Final decision and rationale

    Attributes:
        decision_id: Unique identifier
        user_id: User this decision pertains to
        mental_state: Inferred user mental state
        detected_events: Suffering events detected
        planned_interventions: Compassion plans created
        constitutional_check: DDL compliance result
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
    final_decision: str
    rationale: str
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
    5. PFC: Integrate and decide
    """

    def __init__(self):
        """Initialize PFC with all subsystems."""
        # Initialize subsystems
        self.tom = ToMEngine()
        self.compassion_detector = EventDetector()
        self.compassion_planner = CompassionPlanner()
        self.ddl = DeonticReasoner()

        # Decision history
        self._decisions: List[OrchestratedDecision] = []

        # Statistics
        self.stats = {
            "total_decisions": 0,
            "escalated": 0,
            "interventions_planned": 0,
            "suffering_detected": 0,
            "constitutional_violations": 0
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
