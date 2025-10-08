"""
Governance Module - Test Suite

Comprehensive tests for governance module including ERB, policies, audit, and enforcement.

Run with: pytest test_governance.py -v

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime, timedelta

import pytest

from .base import (
    DecisionType,
    ERBMemberRole,
    GovernanceConfig,
    PolicyType,
)
from .ethics_review_board import ERBManager
from .policies import PolicyRegistry
from .policy_engine import PolicyEngine

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def config():
    """Create test configuration."""
    return GovernanceConfig(
        erb_meeting_frequency_days=30,
        erb_quorum_percentage=0.6,
        erb_decision_threshold=0.75,
        auto_enforce_policies=True,
    )


@pytest.fixture
def erb_manager(config):
    """Create ERB manager."""
    return ERBManager(config)


@pytest.fixture
def policy_registry():
    """Create policy registry."""
    return PolicyRegistry()


@pytest.fixture
def policy_engine(config):
    """Create policy engine."""
    return PolicyEngine(config)


# ============================================================================
# ERB MEMBER TESTS
# ============================================================================


def test_add_erb_member(erb_manager):
    """Test adding ERB member."""
    result = erb_manager.add_member(
        name="Dr. Alice Smith",
        email="alice@example.com",
        role=ERBMemberRole.CHAIR,
        organization="VÉRTICE",
        expertise=["AI Ethics", "Philosophy"],
        is_internal=True,
        term_months=24,
        voting_rights=True,
    )

    assert result.success
    assert result.entity_id is not None
    assert erb_manager.stats["total_members"] == 1
    assert erb_manager.stats["active_members"] == 1


def test_remove_erb_member(erb_manager):
    """Test removing ERB member."""
    result = erb_manager.add_member(
        "Bob Jones", "bob@example.com", ERBMemberRole.TECHNICAL_MEMBER, "Security Inc", ["Cybersecurity"]
    )
    member_id = result.entity_id

    remove_result = erb_manager.remove_member(member_id, "Term completed")
    assert remove_result.success
    assert erb_manager.stats["active_members"] == 0


def test_get_voting_members(erb_manager):
    """Test getting voting members."""
    erb_manager.add_member("Alice", "alice@ex.com", ERBMemberRole.CHAIR, "VÉRTICE", ["Ethics"])
    erb_manager.add_member("Bob", "bob@ex.com", ERBMemberRole.OBSERVER, "External", ["Legal"], voting_rights=False)

    voting_members = erb_manager.get_voting_members()
    assert len(voting_members) == 1
    assert voting_members[0].name == "Alice"


# ============================================================================
# ERB MEETING TESTS
# ============================================================================


def test_schedule_meeting(erb_manager):
    """Test scheduling ERB meeting."""
    future_date = datetime.utcnow() + timedelta(days=7)
    result = erb_manager.schedule_meeting(
        scheduled_date=future_date,
        agenda=["Policy review", "Incident analysis"],
        duration_minutes=120,
    )

    assert result.success
    assert result.entity_id is not None
    assert erb_manager.stats["total_meetings"] == 1


def test_record_attendance_quorum_met(erb_manager):
    """Test recording attendance with quorum."""
    # Add 5 voting members
    for i in range(5):
        erb_manager.add_member(f"Member{i}", f"m{i}@ex.com", ERBMemberRole.TECHNICAL_MEMBER, "VÉRTICE", ["Tech"])

    # Schedule meeting
    future_date = datetime.utcnow() + timedelta(days=1)
    meeting_result = erb_manager.schedule_meeting(future_date, ["Agenda item"])
    meeting_id = meeting_result.entity_id

    # Record attendance (4 out of 5 = 80% > 60% quorum)
    attendee_ids = [m.member_id for m in list(erb_manager.members.values())[:4]]
    result = erb_manager.record_attendance(meeting_id, attendee_ids)

    assert result.success
    assert erb_manager.meetings[meeting_id].quorum_met


# ============================================================================
# ERB DECISION TESTS
# ============================================================================


def test_record_decision_approved(erb_manager):
    """Test recording approved decision."""
    # Setup ERB and meeting
    erb_manager.add_member("Chair", "chair@ex.com", ERBMemberRole.CHAIR, "VÉRTICE", ["Ethics"])
    future_date = datetime.utcnow() + timedelta(days=1)
    meeting_result = erb_manager.schedule_meeting(future_date, ["Decision"])
    meeting_id = meeting_result.entity_id

    attendee_ids = [m.member_id for m in erb_manager.get_voting_members()]
    erb_manager.record_attendance(meeting_id, attendee_ids)

    # Record decision (80% approval > 75% threshold)
    result = erb_manager.record_decision(
        meeting_id=meeting_id,
        title="Approve Ethical Use Policy v1.0",
        description="Approve new ethical use policy",
        votes_for=4,
        votes_against=1,
        votes_abstain=0,
        rationale="Policy aligns with organizational values",
    )

    assert result.success
    decision_id = result.entity_id
    decision = erb_manager.decisions[decision_id]
    assert decision.is_approved()
    assert decision.decision_type == DecisionType.APPROVED


def test_record_decision_rejected(erb_manager):
    """Test recording rejected decision."""
    erb_manager.add_member("Chair", "chair@ex.com", ERBMemberRole.CHAIR, "VÉRTICE", ["Ethics"])
    future_date = datetime.utcnow() + timedelta(days=1)
    meeting_result = erb_manager.schedule_meeting(future_date, ["Decision"])
    meeting_id = meeting_result.entity_id

    erb_manager.record_attendance(meeting_id, [list(erb_manager.members.keys())[0]])

    # Record decision (40% approval < 75% threshold)
    result = erb_manager.record_decision(
        meeting_id=meeting_id,
        title="Controversial Policy",
        description="Test rejection",
        votes_for=2,
        votes_against=3,
        votes_abstain=0,
    )

    assert result.success
    decision_id = result.entity_id
    decision = erb_manager.decisions[decision_id]
    assert not decision.is_approved()
    assert decision.decision_type == DecisionType.REJECTED


# ============================================================================
# POLICY REGISTRY TESTS
# ============================================================================


def test_get_all_policies(policy_registry):
    """Test getting all policies."""
    policies = policy_registry.get_all_policies()
    assert len(policies) == 5  # 5 core policies


def test_get_policy_by_type(policy_registry):
    """Test getting policy by type."""
    policy = policy_registry.get_policy(PolicyType.ETHICAL_USE)
    assert policy.policy_type == PolicyType.ETHICAL_USE
    assert policy.title == "VÉRTICE Ethical Use Policy"
    assert len(policy.rules) > 0


def test_approve_policy(policy_registry):
    """Test approving policy."""
    policy_registry.approve_policy(PolicyType.ETHICAL_USE, "decision-123")
    policy = policy_registry.get_policy(PolicyType.ETHICAL_USE)
    assert policy.approved_by_erb
    assert policy.erb_decision_id == "decision-123"


# ============================================================================
# POLICY ENGINE TESTS
# ============================================================================


def test_enforce_ethical_use_authorized(policy_engine):
    """Test ethical use policy with authorized action."""
    result = policy_engine.enforce_policy(
        policy_type=PolicyType.ETHICAL_USE,
        action="block_ip",
        context={"authorized": True, "logged": True},
        actor="security_analyst",
    )

    assert result.is_compliant
    assert len(result.violations) == 0


def test_enforce_ethical_use_unauthorized(policy_engine):
    """Test ethical use policy with unauthorized action."""
    result = policy_engine.enforce_policy(
        policy_type=PolicyType.ETHICAL_USE,
        action="block_ip",
        context={"authorized": False, "logged": True},
        actor="user",
    )

    assert not result.is_compliant
    assert len(result.violations) > 0


def test_enforce_red_teaming_no_authorization(policy_engine):
    """Test red teaming policy without authorization."""
    result = policy_engine.enforce_policy(
        policy_type=PolicyType.RED_TEAMING,
        action="execute_exploit",
        context={"written_authorization": False, "target_environment": "production"},
        actor="red_team",
    )

    assert not result.is_compliant
    assert len(result.violations) > 0


def test_enforce_data_privacy_no_encryption(policy_engine):
    """Test data privacy policy without encryption."""
    result = policy_engine.enforce_policy(
        policy_type=PolicyType.DATA_PRIVACY,
        action="store_personal_data",
        context={"encrypted": False, "legal_basis": "consent"},
        actor="system",
    )

    assert not result.is_compliant


def test_check_action_allowed(policy_engine):
    """Test checking if action is allowed."""
    is_allowed, violations = policy_engine.check_action(
        action="analyze_traffic",
        context={"authorized": True, "logged": True, "encrypted": True},
        actor="system",
    )

    assert is_allowed
    assert len(violations) == 0


def test_check_action_blocked(policy_engine):
    """Test checking if action is blocked."""
    is_allowed, violations = policy_engine.check_action(
        action="execute_exploit",
        context={"written_authorization": False},
        actor="unauthorized_user",
    )

    assert not is_allowed
    assert len(violations) > 0


# ============================================================================
# STATISTICS TESTS
# ============================================================================


def test_erb_statistics(erb_manager):
    """Test ERB statistics."""
    erb_manager.add_member("Alice", "alice@ex.com", ERBMemberRole.CHAIR, "VÉRTICE", ["Ethics"])
    erb_manager.add_member("Bob", "bob@ex.com", ERBMemberRole.TECHNICAL_MEMBER, "VÉRTICE", ["Tech"])

    stats = erb_manager.get_stats()
    assert stats["total_members"] == 2
    assert stats["active_members"] == 2


def test_policy_engine_statistics(policy_engine):
    """Test policy engine statistics."""
    # Trigger some violations
    policy_engine.enforce_policy(PolicyType.ETHICAL_USE, "block_ip", {"authorized": False}, "user")

    stats = policy_engine.get_statistics()
    assert stats["total_violations_detected"] > 0
    assert stats["total_policies"] == 5


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
