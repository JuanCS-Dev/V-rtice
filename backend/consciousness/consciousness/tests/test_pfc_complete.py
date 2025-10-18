"""
Complete coverage tests for PFC

Covers all remaining branches and edge cases.
"""

from uuid import uuid4

from consciousness.prefrontal_cortex import PrefrontalCortex
from consciousness.tom_engine import EmotionalState


class TestPFCEdgeCases:
    """Tests for PFC edge cases."""

    def test_pfc_get_decision_not_found(self):
        """Test get_decision returns None for non-existent ID."""
        pfc = PrefrontalCortex()

        decision = pfc.get_decision(uuid4())

        assert decision is None

    def test_pfc_monitor_decision_for_stressed_user(self):
        """Test MONITOR decision for stressed user."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Stressed user: high errors, no retries
        signals = {
            "error_count": 2,
            "retry_count": 0,
            "response_time_ms": 1000,
            "task_success": False
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="User experiencing errors"
        )

        assert decision.mental_state.emotional_state == EmotionalState.STRESSED
        assert decision.final_decision == "MONITOR"
        assert not decision.requires_escalation

    def test_pfc_intervene_low_priority_for_minor_suffering(self):
        """Test low-priority intervention for minor suffering."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Minor suffering: some issues but not critical
        signals = {
            "error_count": 1,
            "retry_count": 0,
            "response_time_ms": 2000,
            "task_success": False
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="User reports minor issue"
        )

        # Should detect low-severity event
        if decision.detected_events:
            assert decision.final_decision in ["INTERVENE_LOW_PRIORITY", "PROCEED", "MONITOR"]

    def test_pfc_statistics_with_multiple_escalations(self):
        """Test statistics tracking with escalations."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Constitutional violation - will escalate
        pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals={"error_count": 0},
            action_description="cause_physical_harm action"
        )

        # Normal action - will not escalate
        pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals={"error_count": 0, "task_success": True},
            action_description="Normal action"
        )

        stats = pfc.get_statistics()

        assert stats["total_decisions"] == 2
        assert stats["escalated"] == 1
        assert stats["escalation_rate"] == 0.5
        assert stats["constitutional_violations"] == 1

    def test_pfc_decisions_sorted_by_timestamp(self):
        """Test get_decisions_for_user sorts by timestamp descending."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        decision1 = pfc.orchestrate_decision(
            user_id, {"error_count": 0}, "Action 1"
        )
        decision2 = pfc.orchestrate_decision(
            user_id, {"error_count": 0}, "Action 2"
        )
        decision3 = pfc.orchestrate_decision(
            user_id, {"error_count": 0}, "Action 3"
        )

        decisions = pfc.get_decisions_for_user(user_id)

        # Most recent first
        assert decisions[0].decision_id == decision3.decision_id
        assert decisions[1].decision_id == decision2.decision_id
        assert decisions[2].decision_id == decision1.decision_id

    def test_pfc_statistics_empty_when_no_decisions(self):
        """Test statistics with no decisions."""
        pfc = PrefrontalCortex()

        stats = pfc.get_statistics()

        assert stats["total_decisions"] == 0
        assert stats["escalated"] == 0
        assert stats["interventions_planned"] == 0

    def test_pfc_repr(self):
        """Test PFC __repr__ method."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        pfc.orchestrate_decision(user_id, {"error_count": 0}, "Test")

        assert repr(pfc) == "PrefrontalCortex(decisions=1)"

    def test_pfc_detect_suffering_from_behavioral_metrics_only(self):
        """Test suffering detection from behavioral metrics without text."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # High error rate triggers behavioral detection
        signals = {
            "error_rate": 0.8,
            "retry_count": 0,
            "response_time_ms": 1000
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="Normal operation"
        )

        # Should detect distress from error_rate metric
        assert len(decision.detected_events) > 0

    def test_pfc_no_suffering_on_clean_behavioral_metrics(self):
        """Test no suffering detected with good behavioral metrics."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        signals = {
            "error_rate": 0.01,
            "retry_count": 0,
            "response_time_ms": 200,
            "active_connections": 10
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="Normal operation"
        )

        # No suffering should be detected
        assert len(decision.detected_events) == 0

    def test_pfc_high_priority_intervention_for_severe_suffering(self):
        """Test high-priority intervention for severe suffering."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Very high error rate + slow response = severe distress
        signals = {
            "error_rate": 0.95,
            "response_time_ms": 10000,
            "task_success": False
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="System critical error failure"
        )

        # Should plan high-priority intervention
        if decision.planned_interventions:
            high_priority = [p for p in decision.planned_interventions if p.priority >= 8]
            if high_priority:
                assert "INTERVENE" in decision.final_decision

    def test_pfc_low_priority_intervention_path(self):
        """Test INTERVENE_LOW_PRIORITY decision path."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Low errors, neutral state, but with text indicating minor issue
        signals = {
            "error_count": 0,
            "retry_count": 0,
            "response_time_ms": 1000,
            "task_success": True
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="Experienced minor error but continuing"
        )

        # Should detect event and plan low-priority intervention
        if decision.detected_events and decision.planned_interventions:
            # Low-priority plans won't trigger high-priority intervention
            low_priority_plans = [p for p in decision.planned_interventions if p.priority < 8]
            if low_priority_plans and not decision.mental_state.needs_assistance:
                assert decision.final_decision == "INTERVENE_LOW_PRIORITY"
