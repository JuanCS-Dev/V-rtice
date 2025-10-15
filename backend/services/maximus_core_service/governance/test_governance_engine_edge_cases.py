"""
Governance Engine - Edge Cases & Coverage Gaps Test Suite

Additional tests for GovernanceEngine to achieve 100% coverage.
Focuses on event subscription, decision expiration, and edge cases.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
"""

from datetime import datetime, timedelta

import pytest

from .governance_engine import Decision, DecisionStatus, GovernanceEngine, RiskAssessment

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def engine():
    """Create GovernanceEngine instance."""
    return GovernanceEngine()


@pytest.fixture
def sample_decision():
    """Create sample decision."""
    return Decision(
        decision_id="test-decision-1",
        operation_type="EXPLOIT_EXECUTION",
        context={"target": "192.168.1.100"},
        risk=RiskAssessment(score=0.75, level="HIGH", factors=["Critical system"]),
        priority="HIGH",
        sla_seconds=600,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )


# ============================================================================
# EVENT SUBSCRIPTION TESTS
# ============================================================================


class TestEventSubscription:
    """Test event subscription and streaming."""

    def test_subscribe_decision_events(self, engine):
        """Test subscribing to decision events."""
        events = list(engine.subscribe_decision_events())

        # Should yield existing decisions as events
        assert isinstance(events, list)
        assert len(events) == 3  # 3 mock decisions from init

        # Each event should have type and decision
        for event in events:
            assert event["type"] == "new_decision"
            assert "decision" in event
            assert isinstance(event["decision"], Decision)

    def test_subscribe_events(self, engine):
        """Test subscribing to general governance events."""
        events = list(engine.subscribe_events())

        # Should yield at least connection event
        assert isinstance(events, list)
        assert len(events) >= 1

        # First event should be connection established
        first_event = events[0]
        assert first_event["type"] == "connection_established"
        assert "metrics" in first_event
        assert "message" in first_event

    def test_emit_event_to_subscribers(self, engine):
        """Test _emit_event dispatches to subscribers."""
        received_events = []

        def test_subscriber(event):
            received_events.append(event)

        # Register subscriber
        engine._event_subscribers.append(test_subscriber)

        # Emit event
        test_event = {"type": "test_event", "data": "test_data"}
        engine._emit_event(test_event)

        # Verify subscriber received event
        assert len(received_events) == 1
        assert received_events[0] == test_event

    def test_emit_event_multiple_subscribers(self, engine):
        """Test _emit_event dispatches to multiple subscribers."""
        received_1 = []
        received_2 = []

        def subscriber1(event):
            received_1.append(event)

        def subscriber2(event):
            received_2.append(event)

        # Register both subscribers
        engine._event_subscribers.append(subscriber1)
        engine._event_subscribers.append(subscriber2)

        # Emit event
        test_event = {"type": "broadcast", "message": "hello"}
        engine._emit_event(test_event)

        # Both should receive
        assert len(received_1) == 1
        assert len(received_2) == 1
        assert received_1[0] == test_event
        assert received_2[0] == test_event


# ============================================================================
# DECISION EXPIRATION TESTS
# ============================================================================


class TestDecisionExpiration:
    """Test decision expiration logic."""

    def test_is_expired_no_expiry(self):
        """Test decision with no expiry is never expired."""
        decision = Decision(
            operation_type="TEST",
            context={},
            risk=RiskAssessment(),
            expires_at=None,  # No expiry
        )

        assert decision.is_expired() is False

    def test_is_expired_future_expiry(self):
        """Test decision with future expiry is not expired."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        decision = Decision(
            operation_type="TEST",
            context={},
            risk=RiskAssessment(),
            expires_at=future_time,
        )

        assert decision.is_expired() is False

    def test_is_expired_past_expiry(self):
        """Test decision with past expiry is expired."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        decision = Decision(
            operation_type="TEST",
            context={},
            risk=RiskAssessment(),
            expires_at=past_time,
        )

        assert decision.is_expired() is True

    def test_time_remaining_no_expiry(self):
        """Test time_remaining with no expiry returns -1."""
        decision = Decision(
            operation_type="TEST",
            context={},
            risk=RiskAssessment(),
            expires_at=None,
        )

        assert decision.time_remaining() == -1

    def test_time_remaining_future_expiry(self):
        """Test time_remaining with future expiry."""
        future_time = datetime.utcnow() + timedelta(seconds=300)
        decision = Decision(
            operation_type="TEST",
            context={},
            risk=RiskAssessment(),
            expires_at=future_time,
        )

        remaining = decision.time_remaining()

        # Should be approximately 300 seconds (with some tolerance)
        assert 295 <= remaining <= 305

    def test_time_remaining_expired(self):
        """Test time_remaining for expired decision returns 0."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        decision = Decision(
            operation_type="TEST",
            context={},
            risk=RiskAssessment(),
            expires_at=past_time,
        )

        assert decision.time_remaining() == 0


# ============================================================================
# GET_PENDING_DECISIONS EDGE CASES
# ============================================================================


class TestGetPendingDecisionsEdgeCases:
    """Test edge cases for get_pending_decisions."""

    def test_get_pending_decisions_empty_status_filter(self, engine):
        """Test with empty status filter."""
        decisions = engine.get_pending_decisions(status="")

        # Should return all decisions
        assert len(decisions) > 0

    def test_get_pending_decisions_priority_sorting(self, engine):
        """Test priority-based sorting."""
        # Add decisions with different priorities
        engine.create_decision(
            operation_type="LOW_PRIORITY",
            context={},
            risk=RiskAssessment(score=0.3, level="LOW"),
            priority="LOW",
        )

        engine.create_decision(
            operation_type="CRITICAL_PRIORITY",
            context={},
            risk=RiskAssessment(score=0.95, level="CRITICAL"),
            priority="CRITICAL",
        )

        decisions = engine.get_pending_decisions(status="PENDING", limit=10)

        # CRITICAL should be first
        assert decisions[0].priority == "CRITICAL"

    def test_get_pending_decisions_limit_applied(self, engine):
        """Test limit is correctly applied."""
        # Create many decisions
        for i in range(10):
            engine.create_decision(
                operation_type=f"OP_{i}",
                context={},
                risk=RiskAssessment(),
                priority="MEDIUM",
            )

        decisions = engine.get_pending_decisions(limit=5)

        # Should return exactly 5
        assert len(decisions) == 5


# ============================================================================
# UPDATE_DECISION_STATUS EDGE CASES
# ============================================================================


class TestUpdateDecisionStatusEdgeCases:
    """Test edge cases for update_decision_status."""

    def test_update_decision_status_nonexistent(self, engine):
        """Test updating nonexistent decision returns False."""
        result = engine.update_decision_status(
            decision_id="nonexistent-id",
            status=DecisionStatus.APPROVED,
            operator_id="operator-1",
        )

        assert result is False

    def test_update_decision_status_sets_resolved_at(self, engine, sample_decision):
        """Test update sets resolved_at timestamp."""
        engine.decisions[sample_decision.decision_id] = sample_decision

        assert sample_decision.resolved_at is None

        engine.update_decision_status(
            decision_id=sample_decision.decision_id,
            status=DecisionStatus.APPROVED,
            operator_id="operator-1",
        )

        assert sample_decision.resolved_at is not None
        assert isinstance(sample_decision.resolved_at, datetime)

    def test_update_decision_status_emits_event(self, engine, sample_decision):
        """Test update emits decision_resolved event."""
        engine.decisions[sample_decision.decision_id] = sample_decision

        received_events = []

        def subscriber(event):
            received_events.append(event)

        engine._event_subscribers.append(subscriber)

        engine.update_decision_status(
            decision_id=sample_decision.decision_id,
            status=DecisionStatus.REJECTED,
            operator_id="operator-2",
            comment="Not authorized",
        )

        # Verify event was emitted
        assert len(received_events) == 1
        assert received_events[0]["type"] == "decision_resolved"
        assert received_events[0]["decision"].status == DecisionStatus.REJECTED


# ============================================================================
# CREATE_DECISION EDGE CASES
# ============================================================================


class TestCreateDecisionEdgeCases:
    """Test edge cases for create_decision."""

    def test_create_decision_emits_new_decision_event(self, engine):
        """Test create_decision emits new_decision event."""
        received_events = []

        def subscriber(event):
            received_events.append(event)

        engine._event_subscribers.append(subscriber)

        decision = engine.create_decision(
            operation_type="TEST_OP",
            context={"test": "data"},
            risk=RiskAssessment(score=0.5, level="MEDIUM"),
        )

        # Verify event was emitted
        assert len(received_events) == 1
        assert received_events[0]["type"] == "new_decision"
        assert received_events[0]["decision"].decision_id == decision.decision_id

    def test_create_decision_calculates_expiry(self, engine):
        """Test create_decision calculates expiration time."""
        sla_seconds = 300

        decision = engine.create_decision(
            operation_type="TEST_OP",
            context={},
            risk=RiskAssessment(),
            sla_seconds=sla_seconds,
        )

        # Verify expiry is set
        assert decision.expires_at is not None

        # Verify expiry is approximately sla_seconds in the future
        time_diff = (decision.expires_at - decision.created_at).total_seconds()
        assert abs(time_diff - sla_seconds) < 2  # Allow 2 second tolerance


# ============================================================================
# GET_METRICS EDGE CASES
# ============================================================================


class TestGetMetricsEdgeCases:
    """Test edge cases for get_metrics."""

    def test_get_metrics_zero_resolved_decisions(self, engine):
        """Test metrics with no resolved decisions."""
        # All mock decisions are pending
        metrics = engine.get_metrics()

        # Should not crash, avg_response_time should be 0
        assert metrics["avg_response_time"] == 0.0
        assert metrics["approval_rate"] == 0.0

    def test_get_metrics_sla_violations(self, engine):
        """Test SLA violation counting."""
        # Create decision and resolve it after SLA
        decision = engine.create_decision(
            operation_type="SLOW_OP",
            context={},
            risk=RiskAssessment(),
            sla_seconds=60,  # 1 minute SLA
        )

        # Simulate slow resolution (beyond SLA)
        decision.created_at = datetime.utcnow() - timedelta(minutes=5)
        decision.resolved_at = datetime.utcnow()
        decision.status = DecisionStatus.APPROVED

        metrics = engine.get_metrics()

        # Should count as SLA violation
        assert metrics["sla_violations"] >= 1

    def test_get_metrics_approval_rate_calculation(self, engine):
        """Test approval rate calculation."""
        # Create and approve decision
        decision1 = engine.create_decision(
            operation_type="OP1",
            context={},
            risk=RiskAssessment(),
        )
        engine.update_decision_status(
            decision1.decision_id, DecisionStatus.APPROVED, "op1"
        )

        # Create and reject decision
        decision2 = engine.create_decision(
            operation_type="OP2",
            context={},
            risk=RiskAssessment(),
        )
        engine.update_decision_status(
            decision2.decision_id, DecisionStatus.REJECTED, "op2"
        )

        metrics = engine.get_metrics()

        # Approval rate should be 50% (1 approved out of 2 resolved)
        assert metrics["approval_rate"] == 50.0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
