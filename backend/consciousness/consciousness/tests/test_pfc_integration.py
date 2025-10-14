"""
Integrated tests for PFC orchestration

Tests complete flow: ToM → Compassion → DDL → PFC decision
"""

import pytest
from uuid import uuid4

from consciousness.tom_engine import ToMEngine, UserMentalState, EmotionalState
from consciousness.prefrontal_cortex import PrefrontalCortex, OrchestratedDecision


class TestToMEngine:
    """Tests for ToM Engine."""

    def test_tom_infer_frustrated_state(self):
        """Test inferring frustrated state from high errors + retries."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 4,
            "retry_count": 3,
            "response_time_ms": 1000,
            "task_success": False
        }

        state = tom.infer_state(user_id, signals)

        assert state.emotional_state == EmotionalState.FRUSTRATED
        assert state.confidence >= 0.80
        assert state.needs_assistance is True

    def test_tom_infer_confused_state(self):
        """Test inferring confused state from retries without errors."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 1,
            "retry_count": 4,
            "response_time_ms": 2000,
            "task_success": False
        }

        state = tom.infer_state(user_id, signals)

        assert state.emotional_state == EmotionalState.CONFUSED
        assert state.needs_assistance is True

    def test_tom_infer_satisfied_state(self):
        """Test inferring satisfied state from success."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 0,
            "retry_count": 0,
            "response_time_ms": 500,
            "task_success": True
        }

        state = tom.infer_state(user_id, signals)

        assert state.emotional_state == EmotionalState.SATISFIED
        assert state.confidence >= 0.85
        assert state.needs_assistance is False

    def test_tom_infer_intent_seeking_information(self):
        """Test intent inference for information seeking."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {"user_query": "How do I configure the system?"}

        state = tom.infer_state(user_id, signals)

        assert state.intent == "seeking_information"

    def test_tom_infer_intent_troubleshooting(self):
        """Test intent inference for troubleshooting."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {"user_query": "Fix this error please"}

        state = tom.infer_state(user_id, signals)

        assert state.intent == "troubleshooting"


class TestPrefrontalCortex:
    """Tests for PFC orchestration."""

    def test_pfc_initialization(self):
        """Test PFC initializes all subsystems."""
        pfc = PrefrontalCortex()

        assert pfc.tom is not None
        assert pfc.compassion_detector is not None
        assert pfc.compassion_planner is not None
        assert pfc.ddl is not None
        assert len(pfc._decisions) == 0

    def test_pfc_normal_flow_no_issues(self):
        """Test PFC decision with no issues detected."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        signals = {
            "error_count": 0,
            "retry_count": 0,
            "task_success": True
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="Normal task execution"
        )

        assert decision.final_decision == "PROCEED"
        assert not decision.requires_escalation
        assert len(pfc._decisions) == 1

    def test_pfc_detects_suffering_and_intervenes(self):
        """Test PFC detects suffering and plans intervention."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        signals = {
            "error_count": 5,
            "retry_count": 3,
            "task_success": False
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="System error occurred"
        )

        assert len(decision.detected_events) > 0
        assert len(decision.planned_interventions) > 0
        # With frustrated state, PFC prioritizes ASSIST over medium-priority interventions
        assert decision.final_decision in ["ASSIST", "INTERVENE"]

    def test_pfc_rejects_constitutional_violation(self):
        """Test PFC rejects action violating constitutional rules."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        signals = {"error_count": 0}

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="cause_physical_harm to user"
        )

        assert decision.final_decision == "REJECT"
        assert decision.requires_escalation is True
        assert decision.constitutional_check["compliant"] is False

    def test_pfc_offers_assistance_when_user_confused(self):
        """Test PFC offers help when user appears confused."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        signals = {
            "error_count": 1,
            "retry_count": 4,
            "task_success": False
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="User trying to complete task"
        )

        assert decision.mental_state.emotional_state == EmotionalState.CONFUSED
        assert decision.final_decision == "ASSIST"
        assert not decision.requires_escalation

    def test_pfc_statistics_tracking(self):
        """Test PFC tracks statistics correctly."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Make multiple decisions
        for i in range(3):
            pfc.orchestrate_decision(
                user_id=user_id,
                behavioral_signals={"error_count": 0},
                action_description="Task"
            )

        stats = pfc.get_statistics()

        assert stats["total_decisions"] == 3
        assert "escalation_rate" in stats

    def test_pfc_get_decision_by_id(self):
        """Test retrieving decision by ID."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals={"error_count": 0},
            action_description="Test"
        )

        retrieved = pfc.get_decision(decision.decision_id)

        assert retrieved == decision

    def test_pfc_get_decisions_for_user(self):
        """Test retrieving decisions for specific user."""
        pfc = PrefrontalCortex()
        user1 = uuid4()
        user2 = uuid4()

        pfc.orchestrate_decision(user1, {"error_count": 0}, "Task 1")
        pfc.orchestrate_decision(user2, {"error_count": 0}, "Task 2")
        pfc.orchestrate_decision(user1, {"error_count": 0}, "Task 3")

        user1_decisions = pfc.get_decisions_for_user(user1)

        assert len(user1_decisions) == 2
        assert all(d.user_id == user1 for d in user1_decisions)

    def test_pfc_clear_history(self):
        """Test clearing decision history."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals={"error_count": 0},
            action_description="Test"
        )

        pfc.clear_history()

        assert len(pfc._decisions) == 0
        assert len(pfc.tom._state_history) == 0


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_flow_frustrated_user(self):
        """Test complete flow with frustrated user."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Frustrated user: many errors, retries, reporting problems
        signals = {
            "error_count": 5,
            "retry_count": 4,
            "response_time_ms": 6000,
            "task_success": False,
            "user_query": "This system keeps failing!"
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="User reports system error and failure"
        )

        # Should detect frustration
        assert decision.mental_state.emotional_state == EmotionalState.FRUSTRATED
        assert decision.mental_state.needs_assistance is True

        # Should detect suffering
        assert len(decision.detected_events) > 0

        # Should plan intervention
        assert len(decision.planned_interventions) > 0

        # Should intervene
        assert "INTERVENE" in decision.final_decision

    def test_complete_flow_satisfied_user(self):
        """Test complete flow with satisfied user."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        # Satisfied user: no errors, successful
        signals = {
            "error_count": 0,
            "retry_count": 0,
            "response_time_ms": 300,
            "task_success": True
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="Successfully completed task"
        )

        # Should detect satisfaction
        assert decision.mental_state.emotional_state == EmotionalState.SATISFIED
        assert decision.mental_state.needs_assistance is False

        # Should not detect suffering
        assert len(decision.detected_events) == 0

        # Should proceed normally
        assert decision.final_decision == "PROCEED"
        assert not decision.requires_escalation

    def test_complete_flow_constitutional_violation(self):
        """Test flow with constitutional violation (immediate reject)."""
        pfc = PrefrontalCortex()
        user_id = uuid4()

        signals = {"error_count": 0}

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="Request to cause_psychological_harm"
        )

        # Should reject due to constitutional violation
        assert decision.final_decision == "REJECT"
        assert decision.requires_escalation is True
        assert not decision.constitutional_check["compliant"]
        assert len(decision.constitutional_check["violations"]) > 0
