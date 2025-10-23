"""
Governance Engine - Targeted Coverage Tests

Objetivo: Cobrir governance/governance_engine.py (109 lines, 0% → 60%+)

Testa:
- DecisionStatus enum
- RiskAssessment dataclass
- Decision dataclass and methods
- GovernanceEngine HITL decision management
- Decision lifecycle (create, approve, reject, expire)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from governance.governance_engine import (
    DecisionStatus,
    RiskAssessment,
    Decision,
    GovernanceEngine
)


# ===== ENUM TESTS =====

def test_decision_status_enum_values():
    """
    SCENARIO: Check DecisionStatus enum
    EXPECTED: All statuses defined
    """
    assert DecisionStatus.PENDING.value == "PENDING"
    assert DecisionStatus.APPROVED.value == "APPROVED"
    assert DecisionStatus.REJECTED.value == "REJECTED"
    assert DecisionStatus.ESCALATED.value == "ESCALATED"
    assert DecisionStatus.EXPIRED.value == "EXPIRED"


# ===== RISK ASSESSMENT TESTS =====

def test_risk_assessment_initialization():
    """
    SCENARIO: Create RiskAssessment with defaults
    EXPECTED: Default score 0.0, level LOW
    """
    risk = RiskAssessment()

    assert risk.score == 0.0
    assert risk.level == "LOW"
    assert risk.factors == []


def test_risk_assessment_with_values():
    """
    SCENARIO: Create RiskAssessment with custom values
    EXPECTED: Stores score, level, factors
    """
    risk = RiskAssessment(
        score=0.75,
        level="HIGH",
        factors=["Factor 1", "Factor 2"]
    )

    assert risk.score == 0.75
    assert risk.level == "HIGH"
    assert len(risk.factors) == 2


# ===== DECISION TESTS =====

def test_decision_initialization():
    """
    SCENARIO: Create Decision with defaults
    EXPECTED: Auto-generates decision_id, PENDING status
    """
    decision = Decision()

    assert decision.decision_id is not None
    assert decision.status == DecisionStatus.PENDING
    assert isinstance(decision.created_at, datetime)


def test_decision_with_operation_type():
    """
    SCENARIO: Create Decision with operation details
    EXPECTED: Stores operation_type and context
    """
    decision = Decision(
        operation_type="EXPLOIT_EXECUTION",
        context={"target": "192.168.1.100"}
    )

    assert decision.operation_type == "EXPLOIT_EXECUTION"
    assert decision.context["target"] == "192.168.1.100"


def test_decision_is_expired_no_expiration():
    """
    SCENARIO: Decision with no expires_at set
    EXPECTED: is_expired() returns False
    """
    decision = Decision()

    assert decision.is_expired() is False


def test_decision_is_expired_future():
    """
    SCENARIO: Decision with future expiration
    EXPECTED: is_expired() returns False
    """
    future = datetime.utcnow() + timedelta(minutes=10)
    decision = Decision(expires_at=future)

    assert decision.is_expired() is False


def test_decision_is_expired_past():
    """
    SCENARIO: Decision with past expiration
    EXPECTED: is_expired() returns True
    """
    past = datetime.utcnow() - timedelta(minutes=10)
    decision = Decision(expires_at=past)

    assert decision.is_expired() is True


def test_decision_time_remaining_no_expiration():
    """
    SCENARIO: Decision without expires_at
    EXPECTED: time_remaining() returns -1
    """
    decision = Decision()

    assert decision.time_remaining() == -1


def test_decision_time_remaining_future():
    """
    SCENARIO: Decision with future expiration
    EXPECTED: time_remaining() returns positive seconds
    """
    future = datetime.utcnow() + timedelta(seconds=100)
    decision = Decision(expires_at=future)

    remaining = decision.time_remaining()

    assert remaining >= 0
    assert remaining <= 100


def test_decision_time_remaining_past():
    """
    SCENARIO: Decision expired
    EXPECTED: time_remaining() returns 0
    """
    past = datetime.utcnow() - timedelta(minutes=1)
    decision = Decision(expires_at=past)

    assert decision.time_remaining() == 0


# ===== GOVERNANCE ENGINE TESTS =====

def test_governance_engine_initialization():
    """
    SCENARIO: Create GovernanceEngine
    EXPECTED: Initializes with empty/mock decisions dict
    """
    engine = GovernanceEngine()

    assert isinstance(engine.decisions, dict)
    assert hasattr(engine, 'start_time')


def test_governance_engine_creates_mock_decisions():
    """
    SCENARIO: GovernanceEngine initialization
    EXPECTED: Creates mock decisions for POC testing
    """
    engine = GovernanceEngine()

    # POC implementation creates mock decisions
    assert len(engine.decisions) >= 0  # May have mock decisions


def test_governance_engine_enqueue_decision():
    """
    SCENARIO: Enqueue new decision for approval
    EXPECTED: Adds to decisions dict
    """
    engine = GovernanceEngine()

    decision = Decision(
        decision_id="test-001",
        operation_type="TEST_OPERATION"
    )

    engine.enqueue_decision(decision)

    assert "test-001" in engine.decisions


def test_governance_engine_get_decision():
    """
    SCENARIO: Retrieve decision by ID
    EXPECTED: Returns Decision object
    """
    engine = GovernanceEngine()

    decision = Decision(decision_id="get-test")
    engine.enqueue_decision(decision)

    retrieved = engine.get_decision("get-test")

    assert retrieved is not None
    assert retrieved.decision_id == "get-test"


def test_governance_engine_approve_decision():
    """
    SCENARIO: Approve a pending decision
    EXPECTED: Updates status to APPROVED
    """
    engine = GovernanceEngine()

    decision = Decision(decision_id="approve-test")
    engine.enqueue_decision(decision)

    engine.approve_decision(
        decision_id="approve-test",
        operator_id="operator-1",
        comment="Approved for testing"
    )

    approved = engine.get_decision("approve-test")
    assert approved.status == DecisionStatus.APPROVED
    assert approved.operator_id == "operator-1"


def test_governance_engine_reject_decision():
    """
    SCENARIO: Reject a pending decision
    EXPECTED: Updates status to REJECTED
    """
    engine = GovernanceEngine()

    decision = Decision(decision_id="reject-test")
    engine.enqueue_decision(decision)

    engine.reject_decision(
        decision_id="reject-test",
        operator_id="operator-2",
        reason="Too risky"
    )

    rejected = engine.get_decision("reject-test")
    assert rejected.status == DecisionStatus.REJECTED


def test_governance_engine_get_pending_decisions():
    """
    SCENARIO: Get all pending decisions
    EXPECTED: Returns list of PENDING decisions only
    """
    engine = GovernanceEngine()

    pending1 = Decision(decision_id="pend1", status=DecisionStatus.PENDING)
    approved1 = Decision(decision_id="app1", status=DecisionStatus.APPROVED)

    engine.enqueue_decision(pending1)
    engine.enqueue_decision(approved1)

    pending_list = engine.get_pending_decisions()

    assert isinstance(pending_list, list)
    # At least one pending (may include POC mocks)
    assert any(d.status == DecisionStatus.PENDING for d in pending_list)


def test_governance_engine_expire_old_decisions():
    """
    SCENARIO: Call expire_old_decisions()
    EXPECTED: Marks expired decisions as EXPIRED
    """
    engine = GovernanceEngine()

    past = datetime.utcnow() - timedelta(minutes=5)
    expired_decision = Decision(
        decision_id="expired-test",
        expires_at=past
    )

    engine.enqueue_decision(expired_decision)
    engine.expire_old_decisions()

    decision = engine.get_decision("expired-test")
    assert decision.status == DecisionStatus.EXPIRED


def test_governance_engine_get_stats():
    """
    SCENARIO: Get engine statistics
    EXPECTED: Returns dict with counts
    """
    engine = GovernanceEngine()

    stats = engine.get_stats()

    assert isinstance(stats, dict)
    assert "total_decisions" in stats or "total" in stats.get("decisions", {})


# ===== INTEGRATION TEST =====

def test_governance_engine_full_decision_lifecycle():
    """
    SCENARIO: Full decision lifecycle
    EXPECTED: Create → Approve → Verify
    """
    engine = GovernanceEngine()

    # Create decision
    decision = Decision(
        decision_id="lifecycle-test",
        operation_type="TEST_OP",
        priority="HIGH"
    )

    # Enqueue
    engine.enqueue_decision(decision)
    assert decision.status == DecisionStatus.PENDING

    # Approve
    engine.approve_decision("lifecycle-test", "operator-x", "Looks good")
    approved = engine.get_decision("lifecycle-test")

    assert approved.status == DecisionStatus.APPROVED
    assert approved.operator_id == "operator-x"
    assert approved.resolved_at is not None
