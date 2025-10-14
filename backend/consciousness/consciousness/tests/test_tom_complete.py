"""
Complete coverage tests for ToM Engine

Covers all remaining branches and edge cases.
"""

import pytest
from uuid import uuid4

from consciousness.tom_engine import ToMEngine, UserMentalState, EmotionalState


class TestUserMentalStateValidation:
    """Tests for UserMentalState validation."""

    def test_confidence_validation_below_zero(self):
        """Test confidence validation rejects negative values."""
        with pytest.raises(ValueError, match="Confidence must be 0-1"):
            UserMentalState(
                user_id=uuid4(),
                emotional_state=EmotionalState.NEUTRAL,
                intent="test",
                confidence=-0.1
            )

    def test_confidence_validation_above_one(self):
        """Test confidence validation rejects values > 1."""
        with pytest.raises(ValueError, match="Confidence must be 0-1"):
            UserMentalState(
                user_id=uuid4(),
                emotional_state=EmotionalState.NEUTRAL,
                intent="test",
                confidence=1.5
            )

    def test_emotional_state_must_be_enum(self):
        """Test emotional_state validation rejects strings."""
        with pytest.raises(TypeError, match="emotional_state must be EmotionalState enum"):
            UserMentalState(
                user_id=uuid4(),
                emotional_state="neutral",  # String instead of enum
                intent="test",
                confidence=0.8
            )


class TestInferEmotionEdgeCases:
    """Tests for emotion inference edge cases."""

    def test_infer_stressed_from_high_errors_no_retries(self):
        """Test stressed state from high errors without retries."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 2,
            "retry_count": 0,
            "response_time_ms": 1000,
            "task_success": False
        }

        state = tom.infer_state(user_id, signals)

        assert state.emotional_state == EmotionalState.STRESSED
        assert state.confidence == 0.75

    def test_infer_stressed_from_slow_response_time(self):
        """Test stressed state from slow response time."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 0,
            "retry_count": 0,
            "response_time_ms": 6000,
            "task_success": True
        }

        state = tom.infer_state(user_id, signals)

        assert state.emotional_state == EmotionalState.STRESSED
        assert state.confidence == 0.65

    def test_infer_neutral_state(self):
        """Test neutral state as default."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 1,
            "retry_count": 1,
            "response_time_ms": 2000,
            "task_success": False
        }

        state = tom.infer_state(user_id, signals)

        assert state.emotional_state == EmotionalState.NEUTRAL
        assert state.confidence == 0.70


class TestInferIntentEdgeCases:
    """Tests for intent inference edge cases."""

    def test_infer_intent_creation_task(self):
        """Test intent inference for creation tasks."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {"user_query": "Create a new report"}

        state = tom.infer_state(user_id, signals)

        assert state.intent == "creation_task"

    def test_infer_intent_deletion_task(self):
        """Test intent inference for deletion tasks."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {"user_query": "Delete the old files"}

        state = tom.infer_state(user_id, signals)

        assert state.intent == "deletion_task"

    def test_infer_intent_general_query(self):
        """Test intent inference for general queries."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {"user_query": "Display the current status"}

        state = tom.infer_state(user_id, signals)

        assert state.intent == "general_query"


class TestNeedsAssistanceEdgeCases:
    """Tests for needs_assistance determination edge cases."""

    def test_needs_assistance_from_high_error_count(self):
        """Test assistance needed from high error count alone."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 2,
            "retry_count": 0,
            "response_time_ms": 1000,
            "task_success": False
        }

        state = tom.infer_state(user_id, signals)

        assert state.needs_assistance is True

    def test_needs_assistance_from_high_retry_count(self):
        """Test assistance needed from high retry count alone."""
        tom = ToMEngine()
        user_id = uuid4()

        signals = {
            "error_count": 0,
            "retry_count": 3,
            "response_time_ms": 1000,
            "task_success": False
        }

        state = tom.infer_state(user_id, signals)

        assert state.needs_assistance is True

    def test_needs_assistance_from_exactly_two_errors(self):
        """Test assistance needed from exactly 2 errors (edge case)."""
        tom = ToMEngine()
        user_id = uuid4()

        # 2 errors triggers assistance even with neutral emotion
        signals = {
            "error_count": 2,
            "retry_count": 1,
            "response_time_ms": 1000,
            "task_success": False
        }

        state = tom.infer_state(user_id, signals)

        # Should need assistance due to error_count >= 2
        assert state.needs_assistance is True


class TestGetRecentStatesEdgeCases:
    """Tests for get_recent_states edge cases."""

    def test_get_recent_states_with_user_filter(self):
        """Test filtering states by user_id."""
        tom = ToMEngine()
        user1 = uuid4()
        user2 = uuid4()

        tom.infer_state(user1, {"error_count": 0})
        tom.infer_state(user2, {"error_count": 0})
        tom.infer_state(user1, {"error_count": 0})

        states = tom.get_recent_states(user_id=user1)

        assert len(states) == 2
        assert all(s.user_id == user1 for s in states)

    def test_get_recent_states_sorted_by_timestamp(self):
        """Test states are sorted by timestamp descending."""
        tom = ToMEngine()
        user_id = uuid4()

        state1 = tom.infer_state(user_id, {"error_count": 0})
        state2 = tom.infer_state(user_id, {"error_count": 0})
        state3 = tom.infer_state(user_id, {"error_count": 0})

        states = tom.get_recent_states()

        # Most recent first
        assert states[0].state_id == state3.state_id
        assert states[1].state_id == state2.state_id
        assert states[2].state_id == state1.state_id

    def test_get_recent_states_respects_limit(self):
        """Test limit parameter works correctly."""
        tom = ToMEngine()
        user_id = uuid4()

        for i in range(15):
            tom.infer_state(user_id, {"error_count": 0})

        states = tom.get_recent_states(limit=5)

        assert len(states) == 5

    def test_tom_engine_repr(self):
        """Test ToMEngine __repr__ method."""
        tom = ToMEngine()
        user_id = uuid4()

        tom.infer_state(user_id, {"error_count": 0})
        tom.infer_state(user_id, {"error_count": 0})

        assert repr(tom) == "ToMEngine(states=2)"
