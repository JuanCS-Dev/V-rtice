"""
Ethics Review Board - 100% Coverage Test Suite

Comprehensive tests for ERBManager to achieve 100% coverage.
Tests member management, meeting management, decision-making, and reporting.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
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

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def config():
    """Create governance configuration."""
    return GovernanceConfig()


@pytest.fixture
def erb_manager(config):
    """Create ERB manager."""
    return ERBManager(config)


@pytest.fixture
def populated_erb(erb_manager):
    """Create ERB with members."""
    # Add chair
    erb_manager.add_member(
        name="Dr. Chair",
        email="chair@vertice.ai",
        role=ERBMemberRole.CHAIR,
        organization="VÉRTICE",
        expertise=["AI Ethics", "Governance"],
    )

    # Add members
    erb_manager.add_member(
        name="Dr. Technical",
        email="technical@vertice.ai",
        role=ERBMemberRole.TECHNICAL_MEMBER,
        organization="VÉRTICE",
        expertise=["Security"],
    )

    erb_manager.add_member(
        name="Dr. Legal",
        email="legal@vertice.ai",
        role=ERBMemberRole.LEGAL_MEMBER,
        organization="External Org",
        expertise=["Law"],
        is_internal=False,
    )

    return erb_manager


# ============================================================================
# MEMBER MANAGEMENT TESTS
# ============================================================================


class TestMemberManagement:
    """Test ERB member management."""

    def test_add_member_success(self, erb_manager):
        """Test successfully adding member."""
        result = erb_manager.add_member(
            name="Dr. Test",
            email="test@vertice.ai",
            role=ERBMemberRole.TECHNICAL_MEMBER,
            organization="Test Org",
            expertise=["Testing"],
        )

        assert result.success
        assert result.entity_id is not None
        assert erb_manager.stats["total_members"] == 1
        assert erb_manager.stats["active_members"] == 1

    def test_add_member_missing_name(self, erb_manager):
        """Test adding member with missing name fails."""
        result = erb_manager.add_member(
            name="",
            email="test@vertice.ai",
            role=ERBMemberRole.TECHNICAL_MEMBER,
            organization="Test Org",
            expertise=["Testing"],
        )

        assert not result.success
        assert "required" in result.message.lower()

    def test_add_member_missing_email(self, erb_manager):
        """Test adding member with missing email fails."""
        result = erb_manager.add_member(
            name="Dr. Test",
            email="",
            role=ERBMemberRole.TECHNICAL_MEMBER,
            organization="Test Org",
            expertise=["Testing"],
        )

        assert not result.success
        assert "required" in result.message.lower()

    def test_add_member_duplicate_email(self, erb_manager):
        """Test adding member with duplicate email fails."""
        email = "duplicate@vertice.ai"

        # Add first member
        result1 = erb_manager.add_member(
            name="Dr. First",
            email=email,
            role=ERBMemberRole.TECHNICAL_MEMBER,
            organization="Org 1",
            expertise=["Test"],
        )
        assert result1.success

        # Try to add second member with same email
        result2 = erb_manager.add_member(
            name="Dr. Second",
            email=email,
            role=ERBMemberRole.LEGAL_MEMBER,
            organization="Org 2",
            expertise=["Test"],
        )

        assert not result2.success
        assert "already exists" in result2.message.lower()

    def test_add_member_with_term(self, erb_manager):
        """Test adding member with term limit."""
        result = erb_manager.add_member(
            name="Dr. Term",
            email="term@vertice.ai",
            role=ERBMemberRole.TECHNICAL_MEMBER,
            organization="Org",
            expertise=["Test"],
            term_months=24,
        )

        assert result.success
        member_id = result.entity_id
        member = erb_manager.members[member_id]
        assert member.term_end_date is not None

    def test_add_member_no_voting_rights(self, erb_manager):
        """Test adding member without voting rights."""
        result = erb_manager.add_member(
            name="Dr. Observer",
            email="observer@vertice.ai",
            role=ERBMemberRole.OBSERVER,
            organization="Org",
            expertise=["Observation"],
            voting_rights=False,
        )

        assert result.success
        member_id = result.entity_id
        member = erb_manager.members[member_id]
        assert not member.voting_rights

    def test_remove_member_success(self, populated_erb):
        """Test successfully removing member."""
        # Get a member
        members = list(populated_erb.members.values())
        member_id = members[0].member_id

        result = populated_erb.remove_member(member_id, "Test removal")

        assert result.success
        assert not populated_erb.members[member_id].is_active
        assert populated_erb.stats["active_members"] == 2  # Started with 3

    def test_remove_member_not_found(self, erb_manager):
        """Test removing nonexistent member fails."""
        result = erb_manager.remove_member("nonexistent-id", "Test")

        assert not result.success
        assert "not found" in result.message.lower()

    def test_remove_member_already_inactive(self, populated_erb):
        """Test removing already inactive member."""
        # Get member and deactivate
        member_id = list(populated_erb.members.keys())[0]
        populated_erb.remove_member(member_id, "First removal")

        # Try to remove again
        result = populated_erb.remove_member(member_id, "Second removal")

        assert not result.success
        assert "already inactive" in result.message.lower()

    def test_get_active_members(self, populated_erb):
        """Test getting active members."""
        active = populated_erb.get_active_members()

        assert len(active) == 3
        assert all(m.is_active for m in active)

    def test_get_voting_members(self, populated_erb):
        """Test getting voting members."""
        voting = populated_erb.get_voting_members()

        assert len(voting) > 0
        assert all(m.voting_rights for m in voting)

    def test_get_member_by_role(self, populated_erb):
        """Test getting members by role."""
        chairs = populated_erb.get_member_by_role(ERBMemberRole.CHAIR)

        assert len(chairs) == 1
        assert chairs[0].role == ERBMemberRole.CHAIR

    def test_get_chair(self, populated_erb):
        """Test getting the chair."""
        chair = populated_erb.get_chair()

        assert chair is not None
        assert chair.role == ERBMemberRole.CHAIR

    def test_get_chair_none(self, erb_manager):
        """Test getting chair when none exists."""
        chair = erb_manager.get_chair()

        assert chair is None


# ============================================================================
# MEETING MANAGEMENT TESTS
# ============================================================================


class TestMeetingManagement:
    """Test ERB meeting management."""

    def test_schedule_meeting_success(self, erb_manager):
        """Test successfully scheduling meeting."""
        future_date = datetime.utcnow() + timedelta(days=7)

        result = erb_manager.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Item 1", "Item 2"],
            duration_minutes=120,
            location="Virtual",
        )

        assert result.success
        assert result.entity_id is not None
        assert erb_manager.stats["total_meetings"] == 1

    def test_schedule_meeting_past_date(self, erb_manager):
        """Test scheduling meeting with past date fails."""
        past_date = datetime.utcnow() - timedelta(days=1)

        result = erb_manager.schedule_meeting(
            scheduled_date=past_date,
            agenda=["Item 1"],
        )

        assert not result.success
        assert "future" in result.message.lower()

    def test_record_attendance_meeting_not_found(self, erb_manager):
        """Test recording attendance for nonexistent meeting."""
        result = erb_manager.record_attendance(
            meeting_id="nonexistent-meeting",
            attendees=["member1"],
        )

        assert not result.success
        assert "not found" in result.message.lower()

    def test_record_attendance_quorum_met(self, populated_erb):
        """Test recording attendance with quorum met."""
        # Schedule meeting
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test agenda"],
        )
        meeting_id = meeting_result.entity_id

        # Get all voting member IDs
        voting_members = populated_erb.get_voting_members()
        attendee_ids = [m.member_id for m in voting_members]

        # Record attendance
        result = populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=attendee_ids,
        )

        assert result.success
        assert "quorum met" in result.message.lower()
        assert result.metadata["quorum_met"] is True

    def test_record_attendance_quorum_not_met(self, populated_erb):
        """Test recording attendance with quorum not met."""
        # Schedule meeting
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test agenda"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance with no attendees
        result = populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[],
        )

        assert result.success  # Recording succeeds, but warns
        assert "NOT met" in result.message or len(result.warnings) > 0
        assert result.metadata["quorum_met"] is False

    def test_add_meeting_minutes_success(self, populated_erb):
        """Test adding meeting minutes."""
        # Schedule meeting
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Add minutes
        result = populated_erb.add_meeting_minutes(
            meeting_id=meeting_id,
            minutes="Meeting minutes text",
        )

        assert result.success
        assert populated_erb.meetings[meeting_id].status == "completed"

    def test_add_meeting_minutes_not_found(self, erb_manager):
        """Test adding minutes for nonexistent meeting."""
        result = erb_manager.add_meeting_minutes(
            meeting_id="nonexistent-meeting",
            minutes="Minutes",
        )

        assert not result.success
        assert "not found" in result.message.lower()


# ============================================================================
# DECISION MANAGEMENT TESTS
# ============================================================================


class TestDecisionManagement:
    """Test ERB decision management."""

    def test_record_decision_meeting_not_found(self, erb_manager):
        """Test recording decision for nonexistent meeting."""
        result = erb_manager.record_decision(
            meeting_id="nonexistent-meeting",
            title="Test Decision",
            description="Test",
            votes_for=5,
            votes_against=1,
        )

        assert not result.success
        assert "not found" in result.message.lower()

    def test_record_decision_quorum_not_met(self, populated_erb):
        """Test recording decision when quorum not met."""
        # Schedule meeting
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance with no quorum
        populated_erb.record_attendance(meeting_id=meeting_id, attendees=[])

        # Try to record decision
        result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Test Decision",
            description="Test",
            votes_for=5,
            votes_against=1,
        )

        assert not result.success
        assert "quorum" in result.message.lower()

    def test_record_decision_no_votes(self, populated_erb):
        """Test recording decision with no votes."""
        # Schedule meeting with quorum
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance with quorum
        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        # Try to record decision with no votes
        result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Test Decision",
            description="Test",
            votes_for=0,
            votes_against=0,
            votes_abstain=0,
        )

        assert not result.success
        assert "no votes" in result.message.lower()

    def test_record_decision_approved(self, populated_erb):
        """Test recording approved decision."""
        # Schedule meeting with quorum
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance
        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        # Record approved decision (>66% threshold)
        result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Approved Decision",
            description="This should be approved",
            votes_for=7,
            votes_against=1,
            votes_abstain=0,
        )

        assert result.success
        assert populated_erb.stats["decisions_approved"] == 1
        decision_id = result.entity_id
        decision = populated_erb.decisions[decision_id]
        assert decision.decision_type == DecisionType.APPROVED

    def test_record_decision_rejected(self, populated_erb):
        """Test recording rejected decision."""
        # Schedule meeting with quorum
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance
        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        # Record rejected decision (<66% threshold)
        result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Rejected Decision",
            description="This should be rejected",
            votes_for=2,
            votes_against=6,
            votes_abstain=0,
        )

        assert result.success
        assert populated_erb.stats["decisions_rejected"] == 1
        decision_id = result.entity_id
        decision = populated_erb.decisions[decision_id]
        assert decision.decision_type == DecisionType.REJECTED

    def test_record_decision_conditional(self, populated_erb):
        """Test recording conditional decision."""
        # Schedule meeting with quorum
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance
        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        # Record conditional decision (with conditions)
        result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Conditional Decision",
            description="Approved with conditions",
            votes_for=7,
            votes_against=0,
            votes_abstain=1,
            conditions=["Condition 1", "Condition 2"],
        )

        assert result.success
        decision_id = result.entity_id
        decision = populated_erb.decisions[decision_id]
        assert decision.decision_type == DecisionType.CONDITIONAL_APPROVED
        assert len(decision.conditions) == 2

    def test_record_decision_with_follow_up(self, populated_erb):
        """Test recording decision with follow-up."""
        # Schedule meeting with quorum
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance
        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        # Record decision with follow-up
        result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Decision with Follow-up",
            description="Needs follow-up",
            votes_for=7,
            votes_against=0,
            follow_up_required=True,
            follow_up_days=30,
        )

        assert result.success
        decision_id = result.entity_id
        decision = populated_erb.decisions[decision_id]
        assert decision.follow_up_required
        assert decision.follow_up_deadline is not None

    def test_get_decision(self, populated_erb):
        """Test getting decision by ID."""
        # Create a decision first
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        decision_result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Test",
            description="Test",
            votes_for=5,
            votes_against=0,
        )
        decision_id = decision_result.entity_id

        # Get decision
        decision = populated_erb.get_decision(decision_id)

        assert decision is not None
        assert decision.decision_id == decision_id

    def test_get_decision_none(self, erb_manager):
        """Test getting nonexistent decision."""
        decision = erb_manager.get_decision("nonexistent-id")

        assert decision is None

    def test_get_decisions_by_meeting(self, populated_erb):
        """Test getting decisions by meeting."""
        # Create meeting and decisions
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        # Create 2 decisions
        populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Decision 1",
            description="Test",
            votes_for=5,
            votes_against=0,
        )

        populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Decision 2",
            description="Test",
            votes_for=6,
            votes_against=0,
        )

        # Get decisions
        decisions = populated_erb.get_decisions_by_meeting(meeting_id)

        assert len(decisions) == 2

    def test_get_decisions_by_policy(self, populated_erb):
        """Test getting decisions by policy."""
        # Create decision with related policy
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Decision",
            description="Test",
            votes_for=5,
            votes_against=0,
            related_policies=[PolicyType.ETHICAL_USE],
        )

        # Get by policy
        decisions = populated_erb.get_decisions_by_policy(PolicyType.ETHICAL_USE)

        assert len(decisions) == 1

    def test_get_pending_follow_ups(self, populated_erb):
        """Test getting pending follow-ups."""
        # Create decision with future follow-up
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Decision",
            description="Test",
            votes_for=5,
            votes_against=0,
            follow_up_required=True,
            follow_up_days=30,  # Future follow-up
        )

        # Get pending
        pending = populated_erb.get_pending_follow_ups()

        assert len(pending) == 1

    def test_get_overdue_follow_ups(self, populated_erb):
        """Test getting overdue follow-ups."""
        # Create decision with past follow-up
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        decision_result = populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Decision",
            description="Test",
            votes_for=5,
            votes_against=0,
            follow_up_required=True,
            follow_up_days=1,
        )

        # Manually set follow-up to past
        decision_id = decision_result.entity_id
        decision = populated_erb.decisions[decision_id]
        decision.follow_up_deadline = datetime.utcnow() - timedelta(days=1)

        # Get overdue
        overdue = populated_erb.get_overdue_follow_ups()

        assert len(overdue) == 1


# ============================================================================
# QUORUM & VOTING TESTS
# ============================================================================


class TestQuorumVoting:
    """Test quorum and voting utilities."""

    def test_check_quorum_met(self, populated_erb):
        """Test quorum check when met."""
        voting_members = populated_erb.get_voting_members()
        attendee_ids = [m.member_id for m in voting_members]

        quorum_met, stats = populated_erb.check_quorum(attendee_ids)

        assert quorum_met
        assert stats["voting_attendees"] == len(voting_members)

    def test_check_quorum_not_met(self, populated_erb):
        """Test quorum check when not met."""
        quorum_met, stats = populated_erb.check_quorum([])

        assert not quorum_met
        assert stats["voting_attendees"] == 0

    def test_calculate_approval_approved(self, erb_manager):
        """Test approval calculation when approved."""
        approved, percentage = erb_manager.calculate_approval(
            votes_for=7,
            votes_against=1,
            votes_abstain=0,
        )

        assert approved
        assert percentage > 66.0  # Above threshold

    def test_calculate_approval_rejected(self, erb_manager):
        """Test approval calculation when rejected."""
        approved, percentage = erb_manager.calculate_approval(
            votes_for=2,
            votes_against=6,
            votes_abstain=0,
        )

        assert not approved
        assert percentage < 66.0  # Below threshold

    def test_calculate_approval_no_votes(self, erb_manager):
        """Test approval calculation with no votes."""
        approved, percentage = erb_manager.calculate_approval(
            votes_for=0,
            votes_against=0,
            votes_abstain=0,
        )

        assert not approved
        assert percentage == 0.0


# ============================================================================
# REPORTING & STATISTICS TESTS
# ============================================================================


class TestReporting:
    """Test ERB reporting and statistics."""

    def test_get_stats(self, populated_erb):
        """Test getting ERB statistics."""
        stats = populated_erb.get_stats()

        assert "total_members" in stats
        assert "active_members" in stats
        assert stats["total_members"] == 3
        assert stats["active_members"] == 3

    def test_get_member_participation(self, populated_erb):
        """Test getting member participation stats."""
        # Create meeting and record attendance
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        members = populated_erb.get_active_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[members[0].member_id],
            absentees=[members[1].member_id],
        )

        # Complete meeting
        populated_erb.add_meeting_minutes(meeting_id, "Minutes")

        # Get participation
        participation = populated_erb.get_member_participation()

        assert len(participation) == 3
        # First member attended
        assert participation[members[0].member_id]["meetings_attended"] == 1

    def test_get_member_participation_with_inactive(self, populated_erb):
        """Test participation stats excludes inactive members (line 570)."""
        # Create meeting
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        members = populated_erb.get_active_members()
        # Record attendance for first member
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[members[0].member_id],
        )

        # Complete meeting
        populated_erb.add_meeting_minutes(meeting_id, "Minutes")

        # Deactivate second member
        populated_erb.remove_member(members[1].member_id, "Test removal")

        # Get participation - should only include active members
        participation = populated_erb.get_member_participation()

        # Should only have 2 active members now (3 total - 1 removed)
        assert len(participation) == 2
        # Inactive member should NOT be in participation dict (line 570 continue)
        assert members[1].member_id not in participation
        # Active members should be present
        assert members[0].member_id in participation
        assert members[2].member_id in participation

    def test_generate_summary_report(self, populated_erb):
        """Test generating comprehensive summary report."""
        report = populated_erb.generate_summary_report()

        assert "generated_at" in report
        assert "members" in report
        assert "meetings" in report
        assert "decisions" in report
        assert "participation" in report

        # Check member stats
        assert report["members"]["total"] == 3
        assert report["members"]["active"] == 3

    def test_generate_summary_report_with_data(self, populated_erb):
        """Test summary report with meetings and decisions."""
        # Create meeting
        future_date = datetime.utcnow() + timedelta(days=7)
        meeting_result = populated_erb.schedule_meeting(
            scheduled_date=future_date,
            agenda=["Test"],
        )
        meeting_id = meeting_result.entity_id

        # Record attendance
        voting_members = populated_erb.get_voting_members()
        populated_erb.record_attendance(
            meeting_id=meeting_id,
            attendees=[m.member_id for m in voting_members],
        )

        # Complete meeting
        populated_erb.add_meeting_minutes(meeting_id, "Minutes")

        # Create decision
        populated_erb.record_decision(
            meeting_id=meeting_id,
            title="Decision",
            description="Test",
            votes_for=7,
            votes_against=0,
        )

        # Generate report
        report = populated_erb.generate_summary_report()

        assert report["meetings"]["total"] == 1
        assert report["meetings"]["completed"] == 1
        assert report["decisions"]["total"] == 1
        assert report["decisions"]["approved"] == 1


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
