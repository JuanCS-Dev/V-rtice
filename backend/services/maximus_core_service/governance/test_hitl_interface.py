"""
HITL Interface - Comprehensive Test Suite

Tests for Human-in-the-Loop interface for governance decisions.
Tests session management, operator statistics, and decision operations.

Coverage target: 100%

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
"""

from datetime import datetime

import pytest

from .governance_engine import DecisionStatus, GovernanceEngine
from .hitl_interface import HITLInterface

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def governance_engine():
    """Create GovernanceEngine instance."""
    return GovernanceEngine()


@pytest.fixture
def hitl_interface(governance_engine):
    """Create HITLInterface instance."""
    return HITLInterface(governance_engine)


# ============================================================================
# SESSION MANAGEMENT TESTS
# ============================================================================


class TestSessionManagement:
    """Test session management."""

    def test_create_session(self, hitl_interface):
        """Test creating new session."""
        session_id = hitl_interface.create_session("operator-1")

        assert session_id is not None
        assert session_id in hitl_interface.sessions

        session = hitl_interface.sessions[session_id]
        assert session["operator_id"] == "operator-1"
        assert isinstance(session["created_at"], datetime)
        assert session["decisions_processed"] == 0

    def test_create_session_initializes_operator_stats(self, hitl_interface):
        """Test session creation initializes operator stats."""
        operator_id = "operator-new"

        assert operator_id not in hitl_interface.operator_stats

        hitl_interface.create_session(operator_id)

        assert operator_id in hitl_interface.operator_stats
        assert hitl_interface.operator_stats[operator_id]["total_decisions"] == 0

    def test_close_session(self, hitl_interface):
        """Test closing existing session."""
        session_id = hitl_interface.create_session("operator-1")

        assert session_id in hitl_interface.sessions

        result = hitl_interface.close_session(session_id)

        assert result is True
        assert session_id not in hitl_interface.sessions

    def test_close_nonexistent_session(self, hitl_interface):
        """Test closing nonexistent session returns False."""
        result = hitl_interface.close_session("nonexistent-session-id")

        assert result is False

    def test_multiple_sessions_same_operator(self, hitl_interface):
        """Test creating multiple sessions for same operator."""
        operator_id = "operator-multi"

        session_id_1 = hitl_interface.create_session(operator_id)
        session_id_2 = hitl_interface.create_session(operator_id)

        # Should create different sessions
        assert session_id_1 != session_id_2
        assert session_id_1 in hitl_interface.sessions
        assert session_id_2 in hitl_interface.sessions

        # But share operator stats
        assert len([k for k in hitl_interface.operator_stats if k == operator_id]) == 1


# ============================================================================
# DECISION OPERATIONS TESTS
# ============================================================================


class TestDecisionOperations:
    """Test decision approval, rejection, and escalation."""

    def test_approve_decision(self, hitl_interface, governance_engine):
        """Test approving a decision."""
        # Get one of the mock decisions
        decision_id = list(governance_engine.decisions.keys())[0]
        decision = governance_engine.decisions[decision_id]

        assert decision.status == DecisionStatus.PENDING

        result = hitl_interface.approve_decision(
            decision_id=decision_id,
            operator_id="operator-1",
            comment="Looks good",
            reasoning="All safety checks passed",
        )

        assert result is True
        assert decision.status == DecisionStatus.APPROVED
        assert decision.operator_id == "operator-1"
        assert decision.operator_comment == "Looks good"
        assert decision.operator_reasoning == "All safety checks passed"

    def test_reject_decision(self, hitl_interface, governance_engine):
        """Test rejecting a decision."""
        decision_id = list(governance_engine.decisions.keys())[0]
        decision = governance_engine.decisions[decision_id]

        result = hitl_interface.reject_decision(
            decision_id=decision_id,
            operator_id="operator-2",
            comment="Too risky",
            reasoning="Risk score exceeds threshold",
        )

        assert result is True
        assert decision.status == DecisionStatus.REJECTED
        assert decision.operator_id == "operator-2"
        assert decision.operator_comment == "Too risky"

    def test_escalate_decision(self, hitl_interface, governance_engine):
        """Test escalating a decision."""
        decision_id = list(governance_engine.decisions.keys())[0]
        decision = governance_engine.decisions[decision_id]

        result = hitl_interface.escalate_decision(
            decision_id=decision_id,
            operator_id="operator-3",
            reason="Needs senior approval",
            escalation_target="ERB",
        )

        assert result is True
        assert decision.status == DecisionStatus.ESCALATED
        assert decision.operator_id == "operator-3"
        assert "Escalated to: ERB" in decision.operator_comment

    def test_approve_nonexistent_decision(self, hitl_interface):
        """Test approving nonexistent decision returns False."""
        result = hitl_interface.approve_decision(
            decision_id="nonexistent-decision",
            operator_id="operator-1",
        )

        assert result is False

    def test_reject_nonexistent_decision(self, hitl_interface):
        """Test rejecting nonexistent decision returns False."""
        result = hitl_interface.reject_decision(
            decision_id="nonexistent-decision",
            operator_id="operator-1",
        )

        assert result is False

    def test_escalate_nonexistent_decision(self, hitl_interface):
        """Test escalating nonexistent decision returns False."""
        result = hitl_interface.escalate_decision(
            decision_id="nonexistent-decision",
            operator_id="operator-1",
            reason="Test",
            escalation_target="ERB",
        )

        assert result is False


# ============================================================================
# OPERATOR STATISTICS TESTS
# ============================================================================


class TestOperatorStats:
    """Test operator statistics tracking."""

    def test_get_operator_stats_new_operator(self, hitl_interface):
        """Test getting stats for new operator."""
        stats = hitl_interface.get_operator_stats("new-operator")

        assert stats["total_decisions"] == 0
        assert stats["approved"] == 0
        assert stats["rejected"] == 0
        assert stats["escalated"] == 0
        assert stats["avg_response_time"] == 0.0
        assert stats["session_start"] is None

    def test_get_operator_stats_with_history(self, hitl_interface, governance_engine):
        """Test getting stats for operator with history."""
        operator_id = "operator-stats-test"

        # Initialize operator
        hitl_interface.create_session(operator_id)

        # Approve a decision
        decision_id = list(governance_engine.decisions.keys())[0]
        hitl_interface.approve_decision(decision_id, operator_id)

        stats = hitl_interface.get_operator_stats(operator_id)

        assert stats["total_decisions"] == 1
        assert stats["approved"] == 1
        assert stats["rejected"] == 0
        assert stats["escalated"] == 0

    def test_approve_decision_updates_stats(self, hitl_interface, governance_engine):
        """Test approving decision updates operator stats."""
        operator_id = "operator-approve-stats"
        hitl_interface.create_session(operator_id)

        decision_id = list(governance_engine.decisions.keys())[0]

        # Initial stats
        assert hitl_interface.operator_stats[operator_id]["approved"] == 0

        # Approve decision
        hitl_interface.approve_decision(decision_id, operator_id)

        # Stats updated
        assert hitl_interface.operator_stats[operator_id]["approved"] == 1
        assert hitl_interface.operator_stats[operator_id]["total_decisions"] == 1

    def test_reject_decision_updates_stats(self, hitl_interface, governance_engine):
        """Test rejecting decision updates operator stats."""
        operator_id = "operator-reject-stats"
        hitl_interface.create_session(operator_id)

        decision_id = list(governance_engine.decisions.keys())[1]

        # Reject decision
        hitl_interface.reject_decision(decision_id, operator_id)

        # Stats updated
        assert hitl_interface.operator_stats[operator_id]["rejected"] == 1
        assert hitl_interface.operator_stats[operator_id]["total_decisions"] == 1

    def test_escalate_decision_updates_stats(self, hitl_interface, governance_engine):
        """Test escalating decision updates operator stats."""
        operator_id = "operator-escalate-stats"
        hitl_interface.create_session(operator_id)

        decision_id = list(governance_engine.decisions.keys())[2]

        # Escalate decision
        hitl_interface.escalate_decision(
            decision_id, operator_id, "Needs review", "Senior"
        )

        # Stats updated
        assert hitl_interface.operator_stats[operator_id]["escalated"] == 1
        assert hitl_interface.operator_stats[operator_id]["total_decisions"] == 1

    def test_avg_response_time_calculation(self, hitl_interface, governance_engine):
        """Test average response time calculation."""
        operator_id = "operator-response-time"
        hitl_interface.create_session(operator_id)

        # Approve multiple decisions
        for decision_id in list(governance_engine.decisions.keys())[:2]:
            hitl_interface.approve_decision(decision_id, operator_id)

        stats = hitl_interface.get_operator_stats(operator_id)

        # Average response time should be calculated
        assert stats["avg_response_time"] >= 0.0
        assert stats["total_decisions"] == 2

    def test_operator_stats_multiple_decisions(self, hitl_interface, governance_engine):
        """Test operator stats with multiple decision types."""
        operator_id = "operator-mixed"
        hitl_interface.create_session(operator_id)

        decisions = list(governance_engine.decisions.keys())

        # Approve one
        hitl_interface.approve_decision(decisions[0], operator_id)

        # Reject one
        hitl_interface.reject_decision(decisions[1], operator_id)

        # Escalate one
        hitl_interface.escalate_decision(decisions[2], operator_id, "Test", "ERB")

        stats = hitl_interface.get_operator_stats(operator_id)

        assert stats["total_decisions"] == 3
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
        assert stats["escalated"] == 1


# ============================================================================
# SESSION INFO TESTS
# ============================================================================


class TestSessionInfo:
    """Test session information retrieval."""

    def test_get_session_info_existing(self, hitl_interface):
        """Test getting info for existing session."""
        session_id = hitl_interface.create_session("operator-info")

        info = hitl_interface.get_session_info(session_id)

        assert info is not None
        assert info["operator_id"] == "operator-info"
        assert "created_at" in info
        assert "decisions_processed" in info

    def test_get_session_info_nonexistent(self, hitl_interface):
        """Test getting info for nonexistent session returns None."""
        info = hitl_interface.get_session_info("nonexistent-session")

        assert info is None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Test integrated workflows."""

    def test_complete_workflow_approve(self, hitl_interface, governance_engine):
        """Test complete workflow: create session, approve decision, close session."""
        operator_id = "operator-workflow"

        # Create session
        session_id = hitl_interface.create_session(operator_id)
        assert session_id in hitl_interface.sessions

        # Approve decision
        decision_id = list(governance_engine.decisions.keys())[0]
        result = hitl_interface.approve_decision(
            decision_id, operator_id, "Approved", "Safe to proceed"
        )
        assert result is True

        # Check stats
        stats = hitl_interface.get_operator_stats(operator_id)
        assert stats["approved"] == 1

        # Close session
        result = hitl_interface.close_session(session_id)
        assert result is True
        assert session_id not in hitl_interface.sessions

    def test_decision_without_operator_stats_initialization(self, hitl_interface, governance_engine):
        """Test decision operations work even if operator stats not initialized."""
        operator_id = "operator-no-init"

        # Don't create session (no stats initialized)
        assert operator_id not in hitl_interface.operator_stats

        # Approve decision
        decision_id = list(governance_engine.decisions.keys())[0]
        result = hitl_interface.approve_decision(decision_id, operator_id)

        # Should still work, but stats won't be updated
        assert result is True


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
