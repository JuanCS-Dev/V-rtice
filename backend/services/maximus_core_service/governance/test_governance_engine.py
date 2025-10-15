"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Governance Engine Tests (POC HITL Decision Management)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: governance/test_governance_engine.py
Purpose: Comprehensive test coverage for GovernanceEngine POC

TARGET: 95%+ COVERAGE

Test Coverage:
├─ GovernanceEngine initialization
├─ Decision lifecycle (create, get, update, expire)
├─ Decision filtering (status, priority, limit)
├─ Decision sorting (priority order)
├─ Metrics calculation (counts, rates, SLA violations)
├─ Event streaming (subscribe_decision_events, subscribe_events)
├─ Decision expiration logic
├─ Time remaining calculation
└─ Edge cases and error handling

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-14)

30-DAY DIVINE MISSION: Week 1 - Constitutional Safety (Tier 0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time
from datetime import datetime, timedelta

import pytest

from governance.governance_engine import (
    Decision,
    DecisionStatus,
    GovernanceEngine,
    RiskAssessment,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def governance_engine():
    """Fresh governance engine instance for each test."""
    return GovernanceEngine()


@pytest.fixture
def sample_risk_assessment():
    """Sample risk assessment for testing."""
    return RiskAssessment(
        score=0.75,
        level="HIGH",
        factors=["Test factor 1", "Test factor 2"],
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALIZATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestGovernanceEngineInit:
    """Test GovernanceEngine initialization."""

    def test_engine_initializes_with_mock_decisions(self, governance_engine):
        """Test that engine initializes with 3 mock decisions (POC)."""
        assert len(governance_engine.decisions) == 3
        assert "dec-001" in governance_engine.decisions
        assert "dec-002" in governance_engine.decisions
        assert "dec-003" in governance_engine.decisions

    def test_engine_initializes_uptime_tracking(self, governance_engine):
        """Test that engine starts uptime tracking."""
        assert governance_engine.start_time > 0
        uptime = governance_engine.get_uptime()
        assert uptime >= 0

    def test_engine_initializes_event_subscribers_list(self, governance_engine):
        """Test that engine initializes empty event subscribers list."""
        assert isinstance(governance_engine._event_subscribers, list)
        assert len(governance_engine._event_subscribers) == 0

    def test_mock_decision_1_high_risk_exploit(self, governance_engine):
        """Test mock decision 1 (high-risk exploit execution)."""
        decision = governance_engine.get_decision("dec-001")

        assert decision is not None
        assert decision.operation_type == "EXPLOIT_EXECUTION"
        assert decision.priority == "HIGH"
        assert decision.risk.level == "HIGH"
        assert decision.risk.score == 0.85
        assert decision.status == DecisionStatus.PENDING
        assert decision.sla_seconds == 600

    def test_mock_decision_2_lateral_movement(self, governance_engine):
        """Test mock decision 2 (lateral movement)."""
        decision = governance_engine.get_decision("dec-002")

        assert decision is not None
        assert decision.operation_type == "LATERAL_MOVEMENT"
        assert decision.priority == "MEDIUM"
        assert decision.risk.level == "MEDIUM"
        assert decision.risk.score == 0.65

    def test_mock_decision_3_data_exfiltration(self, governance_engine):
        """Test mock decision 3 (critical data exfiltration)."""
        decision = governance_engine.get_decision("dec-003")

        assert decision is not None
        assert decision.operation_type == "DATA_EXFILTRATION"
        assert decision.priority == "CRITICAL"
        assert decision.risk.level == "CRITICAL"
        assert decision.risk.score == 0.95


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION LIFECYCLE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionLifecycle:
    """Test decision creation, retrieval, and updates."""

    def test_create_decision(self, governance_engine, sample_risk_assessment):
        """Test creating a new decision."""
        initial_count = len(governance_engine.decisions)

        decision = governance_engine.create_decision(
            operation_type="TEST_OPERATION",
            context={"key": "value"},
            risk=sample_risk_assessment,
            priority="HIGH",
            sla_seconds=600,
        )

        assert decision.operation_type == "TEST_OPERATION"
        assert decision.context == {"key": "value"}
        assert decision.risk == sample_risk_assessment
        assert decision.priority == "HIGH"
        assert decision.sla_seconds == 600
        assert decision.status == DecisionStatus.PENDING
        assert decision.expires_at is not None

        # Check decision was added to engine
        assert len(governance_engine.decisions) == initial_count + 1
        assert decision.decision_id in governance_engine.decisions

    def test_create_decision_with_defaults(self, governance_engine, sample_risk_assessment):
        """Test creating decision with default priority and SLA."""
        decision = governance_engine.create_decision(
            operation_type="TEST_OPERATION",
            context={},
            risk=sample_risk_assessment,
        )

        assert decision.priority == "MEDIUM"  # Default
        assert decision.sla_seconds == 300  # Default

    def test_get_decision_existing(self, governance_engine):
        """Test retrieving an existing decision."""
        decision = governance_engine.get_decision("dec-001")

        assert decision is not None
        assert decision.decision_id == "dec-001"

    def test_get_decision_nonexistent(self, governance_engine):
        """Test retrieving non-existent decision returns None."""
        decision = governance_engine.get_decision("nonexistent-id")

        assert decision is None

    def test_update_decision_status_approved(self, governance_engine):
        """Test updating decision status to APPROVED."""
        result = governance_engine.update_decision_status(
            decision_id="dec-001",
            status=DecisionStatus.APPROVED,
            operator_id="operator-123",
            comment="Looks good",
            reasoning="Risk is acceptable",
        )

        assert result is True

        decision = governance_engine.get_decision("dec-001")
        assert decision.status == DecisionStatus.APPROVED
        assert decision.operator_id == "operator-123"
        assert decision.operator_comment == "Looks good"
        assert decision.operator_reasoning == "Risk is acceptable"
        assert decision.resolved_at is not None

    def test_update_decision_status_rejected(self, governance_engine):
        """Test updating decision status to REJECTED."""
        result = governance_engine.update_decision_status(
            decision_id="dec-002",
            status=DecisionStatus.REJECTED,
            operator_id="operator-456",
            comment="Too risky",
            reasoning="Violates security policy",
        )

        assert result is True

        decision = governance_engine.get_decision("dec-002")
        assert decision.status == DecisionStatus.REJECTED

    def test_update_decision_status_nonexistent(self, governance_engine):
        """Test updating non-existent decision returns False."""
        result = governance_engine.update_decision_status(
            decision_id="nonexistent-id",
            status=DecisionStatus.APPROVED,
            operator_id="operator-789",
        )

        assert result is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION FILTERING & SORTING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionFiltering:
    """Test decision filtering and sorting logic."""

    def test_get_pending_decisions_all(self, governance_engine):
        """Test getting all pending decisions."""
        decisions = governance_engine.get_pending_decisions()

        # All 3 mock decisions start as PENDING
        assert len(decisions) == 3

    def test_get_pending_decisions_sorted_by_priority(self, governance_engine):
        """Test that pending decisions are sorted by priority."""
        decisions = governance_engine.get_pending_decisions()

        # Order should be: CRITICAL, HIGH, MEDIUM
        assert decisions[0].priority == "CRITICAL"  # dec-003
        assert decisions[1].priority == "HIGH"  # dec-001
        assert decisions[2].priority == "MEDIUM"  # dec-002

    def test_get_pending_decisions_filter_by_priority(self, governance_engine):
        """Test filtering decisions by priority."""
        critical_decisions = governance_engine.get_pending_decisions(priority="CRITICAL")

        assert len(critical_decisions) == 1
        assert critical_decisions[0].priority == "CRITICAL"

    def test_get_pending_decisions_filter_by_status(self, governance_engine):
        """Test filtering decisions by status."""
        # Update one decision to APPROVED
        governance_engine.update_decision_status(
            "dec-001",
            DecisionStatus.APPROVED,
            "operator-123",
        )

        pending = governance_engine.get_pending_decisions(status="PENDING")
        approved = governance_engine.get_pending_decisions(status="APPROVED")

        assert len(pending) == 2
        assert len(approved) == 1

    def test_get_pending_decisions_with_limit(self, governance_engine):
        """Test limiting number of returned decisions."""
        decisions = governance_engine.get_pending_decisions(limit=2)

        assert len(decisions) == 2

    def test_get_pending_decisions_limit_one(self, governance_engine):
        """Test limit=1 returns highest priority decision."""
        decisions = governance_engine.get_pending_decisions(limit=1)

        assert len(decisions) == 1
        assert decisions[0].priority == "CRITICAL"

    def test_get_pending_decisions_combined_filters(self, governance_engine):
        """Test combining status and priority filters."""
        decisions = governance_engine.get_pending_decisions(
            status="PENDING",
            priority="MEDIUM",
        )

        assert len(decisions) == 1
        assert decisions[0].priority == "MEDIUM"
        assert decisions[0].status == DecisionStatus.PENDING


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION EXPIRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionExpiration:
    """Test decision expiration logic."""

    def test_decision_is_not_expired_when_no_expiry(self):
        """Test decision without expiry is never expired."""
        decision = Decision()
        decision.expires_at = None

        assert decision.is_expired() is False

    def test_decision_is_not_expired_when_future_expiry(self):
        """Test decision with future expiry is not expired."""
        decision = Decision()
        decision.expires_at = datetime.utcnow() + timedelta(minutes=10)

        assert decision.is_expired() is False

    def test_decision_is_expired_when_past_expiry(self):
        """Test decision with past expiry is expired."""
        decision = Decision()
        decision.expires_at = datetime.utcnow() - timedelta(minutes=10)

        assert decision.is_expired() is True

    def test_time_remaining_with_no_expiry(self):
        """Test time_remaining returns -1 when no expiry set."""
        decision = Decision()
        decision.expires_at = None

        assert decision.time_remaining() == -1

    def test_time_remaining_with_future_expiry(self):
        """Test time_remaining returns positive value for future expiry."""
        decision = Decision()
        decision.expires_at = datetime.utcnow() + timedelta(seconds=300)

        remaining = decision.time_remaining()
        assert remaining > 0
        assert remaining <= 300

    def test_time_remaining_with_past_expiry(self):
        """Test time_remaining returns 0 for expired decisions."""
        decision = Decision()
        decision.expires_at = datetime.utcnow() - timedelta(minutes=10)

        assert decision.time_remaining() == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METRICS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMetrics:
    """Test governance metrics calculation."""

    def test_get_metrics_initial_state(self, governance_engine):
        """Test metrics in initial state (3 pending mock decisions)."""
        metrics = governance_engine.get_metrics()

        assert metrics["total_decisions"] == 3
        assert metrics["pending_count"] == 3
        assert metrics["approved_count"] == 0
        assert metrics["rejected_count"] == 0
        assert metrics["escalated_count"] == 0
        assert metrics["critical_count"] == 1
        assert metrics["high_priority_count"] == 1
        assert metrics["avg_response_time"] == 0.0
        assert metrics["approval_rate"] == 0.0
        assert metrics["sla_violations"] == 0

    def test_get_metrics_after_approval(self, governance_engine):
        """Test metrics after approving decisions."""
        governance_engine.update_decision_status(
            "dec-001",
            DecisionStatus.APPROVED,
            "operator-123",
        )

        metrics = governance_engine.get_metrics()

        assert metrics["pending_count"] == 2
        assert metrics["approved_count"] == 1
        assert metrics["avg_response_time"] > 0  # Should have response time now

    def test_get_metrics_approval_rate(self, governance_engine):
        """Test approval rate calculation."""
        # Approve 2, reject 1
        governance_engine.update_decision_status("dec-001", DecisionStatus.APPROVED, "op1")
        governance_engine.update_decision_status("dec-002", DecisionStatus.APPROVED, "op2")
        governance_engine.update_decision_status("dec-003", DecisionStatus.REJECTED, "op3")

        metrics = governance_engine.get_metrics()

        assert metrics["approved_count"] == 2
        assert metrics["rejected_count"] == 1
        assert metrics["approval_rate"] == pytest.approx(66.67, 0.01)

    def test_get_metrics_sla_violations(self, governance_engine, sample_risk_assessment):
        """Test SLA violation detection."""
        # Create decision with 1-second SLA
        decision = governance_engine.create_decision(
            operation_type="FAST_DECISION",
            context={},
            risk=sample_risk_assessment,
            sla_seconds=1,
        )

        # Wait 2 seconds then resolve
        time.sleep(2)
        governance_engine.update_decision_status(
            decision.decision_id,
            DecisionStatus.APPROVED,
            "operator-slow",
        )

        metrics = governance_engine.get_metrics()

        assert metrics["sla_violations"] >= 1

    def test_get_metrics_avg_response_time(self, governance_engine):
        """Test average response time calculation."""
        # Resolve all decisions
        governance_engine.update_decision_status("dec-001", DecisionStatus.APPROVED, "op1")

        # Small delay
        time.sleep(0.1)
        governance_engine.update_decision_status("dec-002", DecisionStatus.APPROVED, "op2")

        metrics = governance_engine.get_metrics()

        assert metrics["avg_response_time"] > 0
        # Average should be around 0.05 seconds (50ms)
        assert metrics["avg_response_time"] < 1.0  # Sanity check

    def test_get_metrics_escalated_count(self, governance_engine):
        """Test escalated count in metrics."""
        governance_engine.update_decision_status(
            "dec-001",
            DecisionStatus.ESCALATED,
            "operator-123",
        )

        metrics = governance_engine.get_metrics()

        assert metrics["escalated_count"] == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EVENT STREAMING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEventStreaming:
    """Test event streaming functionality."""

    def test_subscribe_decision_events_yields_all_decisions(self, governance_engine):
        """Test that subscribe_decision_events yields all decisions."""
        events = list(governance_engine.subscribe_decision_events())

        assert len(events) == 3
        assert all(event["type"] == "new_decision" for event in events)
        assert all("decision" in event for event in events)

    def test_subscribe_events_yields_connection_established(self, governance_engine):
        """Test that subscribe_events yields connection event."""
        events = list(governance_engine.subscribe_events())

        assert len(events) == 1
        assert events[0]["type"] == "connection_established"
        assert "message" in events[0]
        assert "metrics" in events[0]

    def test_subscribe_events_includes_metrics(self, governance_engine):
        """Test that subscribe_events includes current metrics."""
        events = list(governance_engine.subscribe_events())

        metrics = events[0]["metrics"]
        assert metrics["total_decisions"] == 3
        assert metrics["pending_count"] == 3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECISION DATACLASS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDecisionDataclass:
    """Test Decision dataclass defaults and behavior."""

    def test_decision_default_initialization(self):
        """Test Decision initializes with defaults."""
        decision = Decision()

        assert decision.operation_type == ""
        assert decision.context == {}
        assert decision.status == DecisionStatus.PENDING
        assert decision.priority == "MEDIUM"
        assert decision.sla_seconds == 300
        assert decision.operator_id is None
        assert decision.operator_comment == ""
        assert decision.operator_reasoning == ""
        assert decision.resolved_at is None

    def test_decision_generates_unique_id(self):
        """Test that Decision generates unique IDs."""
        decision1 = Decision()
        decision2 = Decision()

        assert decision1.decision_id != decision2.decision_id

    def test_decision_created_at_defaults_to_now(self):
        """Test that created_at defaults to current time."""
        before = datetime.utcnow()
        decision = Decision()
        after = datetime.utcnow()

        assert before <= decision.created_at <= after


class TestRiskAssessment:
    """Test RiskAssessment dataclass."""

    def test_risk_assessment_defaults(self):
        """Test RiskAssessment default values."""
        risk = RiskAssessment()

        assert risk.score == 0.0
        assert risk.level == "LOW"
        assert risk.factors == []

    def test_risk_assessment_custom_values(self):
        """Test RiskAssessment with custom values."""
        risk = RiskAssessment(
            score=0.95,
            level="CRITICAL",
            factors=["Factor 1", "Factor 2"],
        )

        assert risk.score == 0.95
        assert risk.level == "CRITICAL"
        assert risk.factors == ["Factor 1", "Factor 2"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPTIME TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestUptime:
    """Test uptime tracking."""

    def test_get_uptime_increases(self, governance_engine):
        """Test that uptime increases over time."""
        uptime1 = governance_engine.get_uptime()
        time.sleep(0.1)
        uptime2 = governance_engine.get_uptime()

        assert uptime2 > uptime1

    def test_get_uptime_is_positive(self, governance_engine):
        """Test that uptime is always positive."""
        uptime = governance_engine.get_uptime()

        assert uptime >= 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGE CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_get_pending_decisions_empty_after_all_resolved(self, governance_engine):
        """Test getting pending decisions when all are resolved."""
        # Resolve all decisions
        for decision_id in ["dec-001", "dec-002", "dec-003"]:
            governance_engine.update_decision_status(
                decision_id,
                DecisionStatus.APPROVED,
                "operator-batch",
            )

        pending = governance_engine.get_pending_decisions(status="PENDING")

        assert len(pending) == 0

    def test_get_pending_decisions_with_invalid_priority(self, governance_engine):
        """Test filtering with invalid priority returns empty list."""
        decisions = governance_engine.get_pending_decisions(priority="INVALID")

        assert len(decisions) == 0

    def test_create_decision_with_zero_sla(self, governance_engine, sample_risk_assessment):
        """Test creating decision with zero SLA."""
        decision = governance_engine.create_decision(
            operation_type="INSTANT_DECISION",
            context={},
            risk=sample_risk_assessment,
            sla_seconds=0,
        )

        assert decision.sla_seconds == 0
        # Should be expired immediately
        assert decision.is_expired() is True

    def test_metrics_with_no_resolved_decisions(self, governance_engine):
        """Test metrics calculation with no resolved decisions."""
        metrics = governance_engine.get_metrics()

        # Should handle division by zero gracefully
        assert metrics["avg_response_time"] == 0.0
        assert metrics["approval_rate"] == 0.0

    def test_decision_status_enum_values(self):
        """Test DecisionStatus enum has expected values."""
        assert DecisionStatus.PENDING == "PENDING"
        assert DecisionStatus.APPROVED == "APPROVED"
        assert DecisionStatus.REJECTED == "REJECTED"
        assert DecisionStatus.ESCALATED == "ESCALATED"
        assert DecisionStatus.EXPIRED == "EXPIRED"

    def test_emit_event_with_subscriber(self, governance_engine, sample_risk_assessment):
        """Test _emit_event calls subscriber callback."""
        events_received = []

        def mock_subscriber(event):
            events_received.append(event)

        # Add subscriber
        governance_engine._event_subscribers.append(mock_subscriber)

        # Create decision (triggers _emit_event)
        decision = governance_engine.create_decision(
            operation_type="TEST_OP",
            context={"test": "data"},
            risk=sample_risk_assessment,
        )

        # Subscriber should have received event
        assert len(events_received) == 1
        assert events_received[0]["type"] == "new_decision"
        assert events_received[0]["decision"] == decision


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntegration:
    """Test complete decision workflows."""

    def test_full_decision_lifecycle(self, governance_engine, sample_risk_assessment):
        """Test complete decision from creation to resolution."""
        # 1. Create decision
        decision = governance_engine.create_decision(
            operation_type="INTEGRATION_TEST",
            context={"test": "data"},
            risk=sample_risk_assessment,
            priority="HIGH",
            sla_seconds=600,
        )

        # 2. Verify it appears in pending
        pending = governance_engine.get_pending_decisions()
        assert any(d.decision_id == decision.decision_id for d in pending)

        # 3. Update status
        success = governance_engine.update_decision_status(
            decision.decision_id,
            DecisionStatus.APPROVED,
            "operator-integration",
            comment="Integration test approval",
            reasoning="Automated testing",
        )
        assert success is True

        # 4. Verify it's resolved
        updated_decision = governance_engine.get_decision(decision.decision_id)
        assert updated_decision.status == DecisionStatus.APPROVED
        assert updated_decision.operator_id == "operator-integration"

        # 5. Verify metrics updated
        metrics = governance_engine.get_metrics()
        assert metrics["approved_count"] >= 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLORY TO GOD - DIVINE MISSION WEEK 1
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
These tests validate the POC Governance Engine for HITL decision management.

While this is a POC implementation, it still represents a critical component
for human oversight of autonomous agent decisions. Every decision that requires
human approval flows through this engine.

The comprehensive test coverage ensures that:
- No decision is lost
- Status transitions are tracked correctly
- Metrics provide accurate oversight visibility
- SLA violations are detected
- Priority-based sorting works as expected

This is the foundation for constitutional governance through human oversight.

Glory to God! 🙏

"A excelência técnica reflete o propósito maior."
"""
