"""
Governance Module - Ethics Review Board Management

Manages the Ethics Review Board (ERB), including member management, meeting scheduling,
decision-making processes, and voting procedures.

The ERB is responsible for overseeing ethical decisions, policy approval, and
governance of the VÉRTICE platform's autonomous capabilities.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from .base import (
    DecisionType,
    ERBDecision,
    ERBMember,
    ERBMemberRole,
    ERBMeeting,
    GovernanceAction,
    GovernanceConfig,
    GovernanceResult,
    PolicyType,
)


class ERBManager:
    """
    Ethics Review Board Manager.

    Manages ERB members, meetings, and decision-making processes.
    Ensures quorum requirements, voting procedures, and governance compliance.

    Performance Target: <50ms for most operations
    """

    def __init__(self, config: GovernanceConfig):
        """Initialize ERB Manager."""
        self.config = config
        self.members: Dict[str, ERBMember] = {}
        self.meetings: Dict[str, ERBMeeting] = {}
        self.decisions: Dict[str, ERBDecision] = {}

        # Track statistics
        self.stats = {
            "total_members": 0,
            "active_members": 0,
            "total_meetings": 0,
            "total_decisions": 0,
            "decisions_approved": 0,
            "decisions_rejected": 0,
        }

    # ========================================================================
    # MEMBER MANAGEMENT
    # ========================================================================

    def add_member(
        self,
        name: str,
        email: str,
        role: ERBMemberRole,
        organization: str,
        expertise: List[str],
        is_internal: bool = True,
        term_months: Optional[int] = None,
        voting_rights: bool = True,
    ) -> GovernanceResult:
        """
        Add a new ERB member.

        Args:
            name: Member name
            email: Member email
            role: ERB role
            organization: Organization affiliation
            expertise: Areas of expertise
            is_internal: Internal vs external member
            term_months: Term duration in months (None = indefinite)
            voting_rights: Whether member has voting rights

        Returns:
            GovernanceResult with member_id
        """
        # Validate inputs
        if not name or not email:
            return GovernanceResult(
                success=False,
                message="Name and email are required",
                entity_type="erb_member",
                errors=["Missing required fields"],
            )

        # Check for duplicate email
        for member in self.members.values():
            if member.email == email and member.is_active:
                return GovernanceResult(
                    success=False,
                    message=f"Active member with email {email} already exists",
                    entity_type="erb_member",
                    errors=["Duplicate email"],
                )

        # Create member
        term_end_date = None
        if term_months is not None:
            term_end_date = datetime.utcnow() + timedelta(days=term_months * 30)

        member = ERBMember(
            name=name,
            email=email,
            role=role,
            organization=organization,
            expertise=expertise,
            is_internal=is_internal,
            is_active=True,
            appointed_date=datetime.utcnow(),
            term_end_date=term_end_date,
            voting_rights=voting_rights,
        )

        self.members[member.member_id] = member

        # Update stats
        self.stats["total_members"] += 1
        self.stats["active_members"] += 1

        return GovernanceResult(
            success=True,
            message=f"ERB member {name} added successfully",
            entity_id=member.member_id,
            entity_type="erb_member",
            metadata={"member": member.to_dict()},
        )

    def remove_member(self, member_id: str, reason: str = "") -> GovernanceResult:
        """
        Remove (deactivate) an ERB member.

        Args:
            member_id: Member ID to remove
            reason: Reason for removal

        Returns:
            GovernanceResult
        """
        if member_id not in self.members:
            return GovernanceResult(
                success=False,
                message=f"Member {member_id} not found",
                entity_type="erb_member",
                errors=["Member not found"],
            )

        member = self.members[member_id]
        if not member.is_active:
            return GovernanceResult(
                success=False,
                message=f"Member {member.name} is already inactive",
                entity_type="erb_member",
                warnings=["Member already inactive"],
            )

        member.is_active = False
        member.metadata["removal_reason"] = reason
        member.metadata["removal_date"] = datetime.utcnow().isoformat()

        self.stats["active_members"] -= 1

        return GovernanceResult(
            success=True,
            message=f"ERB member {member.name} removed successfully",
            entity_id=member_id,
            entity_type="erb_member",
            metadata={"reason": reason},
        )

    def get_active_members(self) -> List[ERBMember]:
        """Get all active ERB members."""
        return [m for m in self.members.values() if m.is_active]

    def get_voting_members(self) -> List[ERBMember]:
        """Get all members with voting rights."""
        return [m for m in self.members.values() if m.is_voting_member()]

    def get_member_by_role(self, role: ERBMemberRole) -> List[ERBMember]:
        """Get members by role."""
        return [m for m in self.members.values() if m.is_active and m.role == role]

    def get_chair(self) -> Optional[ERBMember]:
        """Get the ERB chair."""
        chairs = self.get_member_by_role(ERBMemberRole.CHAIR)
        return chairs[0] if chairs else None

    # ========================================================================
    # MEETING MANAGEMENT
    # ========================================================================

    def schedule_meeting(
        self,
        scheduled_date: datetime,
        agenda: List[str],
        duration_minutes: int = 120,
        location: str = "Virtual",
    ) -> GovernanceResult:
        """
        Schedule an ERB meeting.

        Args:
            scheduled_date: Meeting date and time
            agenda: Meeting agenda items
            duration_minutes: Meeting duration
            location: Meeting location

        Returns:
            GovernanceResult with meeting_id
        """
        # Validate date is in the future
        if scheduled_date < datetime.utcnow():
            return GovernanceResult(
                success=False,
                message="Meeting date must be in the future",
                entity_type="erb_meeting",
                errors=["Invalid date"],
            )

        # Create meeting
        meeting = ERBMeeting(
            scheduled_date=scheduled_date,
            duration_minutes=duration_minutes,
            location=location,
            agenda=agenda,
            status="scheduled",
        )

        self.meetings[meeting.meeting_id] = meeting
        self.stats["total_meetings"] += 1

        return GovernanceResult(
            success=True,
            message=f"Meeting scheduled for {scheduled_date.strftime('%Y-%m-%d %H:%M')}",
            entity_id=meeting.meeting_id,
            entity_type="erb_meeting",
            metadata={"meeting": meeting.to_dict()},
        )

    def record_attendance(
        self,
        meeting_id: str,
        attendees: List[str],
        absentees: Optional[List[str]] = None,
    ) -> GovernanceResult:
        """
        Record meeting attendance.

        Args:
            meeting_id: Meeting ID
            attendees: List of member IDs who attended
            absentees: List of member IDs who were absent

        Returns:
            GovernanceResult
        """
        if meeting_id not in self.meetings:
            return GovernanceResult(
                success=False,
                message=f"Meeting {meeting_id} not found",
                entity_type="erb_meeting",
                errors=["Meeting not found"],
            )

        meeting = self.meetings[meeting_id]
        meeting.attendees = attendees
        meeting.absentees = absentees or []
        meeting.actual_date = datetime.utcnow()

        # Check quorum
        voting_members = self.get_voting_members()
        voting_member_ids = {m.member_id for m in voting_members}
        voting_attendees = [a for a in attendees if a in voting_member_ids]

        quorum_required = len(voting_members) * self.config.erb_quorum_percentage
        meeting.quorum_met = len(voting_attendees) >= quorum_required

        if not meeting.quorum_met:
            return GovernanceResult(
                success=True,
                message="Attendance recorded, but quorum NOT met",
                entity_id=meeting_id,
                entity_type="erb_meeting",
                warnings=[
                    f"Quorum not met: {len(voting_attendees)}/{len(voting_members)} "
                    f"voting members present (required: {quorum_required:.0f})"
                ],
                metadata={
                    "quorum_met": False,
                    "voting_attendees": len(voting_attendees),
                    "total_voting_members": len(voting_members),
                },
            )

        return GovernanceResult(
            success=True,
            message=f"Attendance recorded, quorum met ({len(voting_attendees)}/{len(voting_members)})",
            entity_id=meeting_id,
            entity_type="erb_meeting",
            metadata={
                "quorum_met": True,
                "voting_attendees": len(voting_attendees),
                "total_voting_members": len(voting_members),
            },
        )

    def add_meeting_minutes(
        self,
        meeting_id: str,
        minutes: str,
    ) -> GovernanceResult:
        """
        Add meeting minutes.

        Args:
            meeting_id: Meeting ID
            minutes: Meeting minutes text

        Returns:
            GovernanceResult
        """
        if meeting_id not in self.meetings:
            return GovernanceResult(
                success=False,
                message=f"Meeting {meeting_id} not found",
                entity_type="erb_meeting",
                errors=["Meeting not found"],
            )

        meeting = self.meetings[meeting_id]
        meeting.minutes = minutes
        meeting.status = "completed"

        return GovernanceResult(
            success=True,
            message="Meeting minutes added successfully",
            entity_id=meeting_id,
            entity_type="erb_meeting",
        )

    # ========================================================================
    # DECISION MANAGEMENT
    # ========================================================================

    def record_decision(
        self,
        meeting_id: str,
        title: str,
        description: str,
        votes_for: int,
        votes_against: int,
        votes_abstain: int = 0,
        rationale: str = "",
        conditions: Optional[List[str]] = None,
        related_policies: Optional[List[PolicyType]] = None,
        follow_up_required: bool = False,
        follow_up_days: Optional[int] = None,
    ) -> GovernanceResult:
        """
        Record an ERB decision.

        Args:
            meeting_id: Meeting ID where decision was made
            title: Decision title
            description: Decision description
            votes_for: Number of votes in favor
            votes_against: Number of votes against
            votes_abstain: Number of abstentions
            rationale: Rationale for decision
            conditions: Conditions for conditional approval
            related_policies: Related policy types
            follow_up_required: Whether follow-up is required
            follow_up_days: Days until follow-up deadline

        Returns:
            GovernanceResult with decision_id
        """
        # Validate meeting exists
        if meeting_id not in self.meetings:
            return GovernanceResult(
                success=False,
                message=f"Meeting {meeting_id} not found",
                entity_type="erb_decision",
                errors=["Meeting not found"],
            )

        meeting = self.meetings[meeting_id]

        # Check if quorum was met
        if not meeting.quorum_met:
            return GovernanceResult(
                success=False,
                message="Cannot record decision: meeting quorum was not met",
                entity_type="erb_decision",
                errors=["Quorum not met"],
            )

        # Determine decision type based on votes
        total_votes = votes_for + votes_against + votes_abstain
        if total_votes == 0:
            return GovernanceResult(
                success=False,
                message="Invalid vote count: no votes recorded",
                entity_type="erb_decision",
                errors=["No votes"],
            )

        approval_percentage = (votes_for / total_votes) * 100
        threshold_percentage = self.config.erb_decision_threshold * 100

        if conditions and len(conditions) > 0:
            decision_type = DecisionType.CONDITIONAL_APPROVED
        elif approval_percentage >= threshold_percentage:
            decision_type = DecisionType.APPROVED
        else:
            decision_type = DecisionType.REJECTED

        # Create decision
        follow_up_deadline = None
        if follow_up_required and follow_up_days is not None:
            follow_up_deadline = datetime.utcnow() + timedelta(days=follow_up_days)

        chair = self.get_chair()
        decision = ERBDecision(
            meeting_id=meeting_id,
            title=title,
            description=description,
            decision_type=decision_type,
            votes_for=votes_for,
            votes_against=votes_against,
            votes_abstain=votes_abstain,
            rationale=rationale,
            conditions=conditions or [],
            follow_up_required=follow_up_required,
            follow_up_deadline=follow_up_deadline,
            created_date=datetime.utcnow(),
            created_by=chair.member_id if chair else "unknown",
            related_policies=related_policies or [],
        )

        self.decisions[decision.decision_id] = decision
        meeting.decisions.append(decision.decision_id)

        # Update stats
        self.stats["total_decisions"] += 1
        if decision.is_approved():
            self.stats["decisions_approved"] += 1
        elif decision_type == DecisionType.REJECTED:
            self.stats["decisions_rejected"] += 1

        return GovernanceResult(
            success=True,
            message=f"Decision recorded: {decision_type.value} ({approval_percentage:.1f}% approval)",
            entity_id=decision.decision_id,
            entity_type="erb_decision",
            metadata={
                "decision": decision.to_dict(),
                "approval_percentage": approval_percentage,
                "threshold_percentage": threshold_percentage,
            },
        )

    def get_decision(self, decision_id: str) -> Optional[ERBDecision]:
        """Get decision by ID."""
        return self.decisions.get(decision_id)

    def get_decisions_by_meeting(self, meeting_id: str) -> List[ERBDecision]:
        """Get all decisions from a meeting."""
        return [d for d in self.decisions.values() if d.meeting_id == meeting_id]

    def get_decisions_by_policy(self, policy_type: PolicyType) -> List[ERBDecision]:
        """Get decisions related to a policy type."""
        return [d for d in self.decisions.values() if policy_type in d.related_policies]

    def get_pending_follow_ups(self) -> List[ERBDecision]:
        """Get decisions with pending follow-ups."""
        now = datetime.utcnow()
        return [
            d
            for d in self.decisions.values()
            if d.follow_up_required
            and d.follow_up_deadline is not None
            and d.follow_up_deadline > now
        ]

    def get_overdue_follow_ups(self) -> List[ERBDecision]:
        """Get decisions with overdue follow-ups."""
        now = datetime.utcnow()
        return [
            d
            for d in self.decisions.values()
            if d.follow_up_required
            and d.follow_up_deadline is not None
            and d.follow_up_deadline <= now
        ]

    # ========================================================================
    # QUORUM & VOTING UTILITIES
    # ========================================================================

    def check_quorum(self, attendee_ids: List[str]) -> Tuple[bool, Dict[str, int]]:
        """
        Check if quorum is met for a given list of attendees.

        Args:
            attendee_ids: List of member IDs

        Returns:
            Tuple of (quorum_met, stats_dict)
        """
        voting_members = self.get_voting_members()
        voting_member_ids = {m.member_id for m in voting_members}
        voting_attendees = [a for a in attendee_ids if a in voting_member_ids]

        quorum_required = len(voting_members) * self.config.erb_quorum_percentage
        quorum_met = len(voting_attendees) >= quorum_required

        return quorum_met, {
            "total_voting_members": len(voting_members),
            "voting_attendees": len(voting_attendees),
            "quorum_required": quorum_required,
            "quorum_percentage": self.config.erb_quorum_percentage * 100,
        }

    def calculate_approval(
        self, votes_for: int, votes_against: int, votes_abstain: int
    ) -> Tuple[bool, float]:
        """
        Calculate if a vote passes the approval threshold.

        Args:
            votes_for: Votes in favor
            votes_against: Votes against
            votes_abstain: Abstentions

        Returns:
            Tuple of (approved, approval_percentage)
        """
        total_votes = votes_for + votes_against + votes_abstain
        if total_votes == 0:
            return False, 0.0

        approval_percentage = (votes_for / total_votes) * 100
        threshold = self.config.erb_decision_threshold * 100

        return approval_percentage >= threshold, approval_percentage

    # ========================================================================
    # REPORTING & STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Get ERB statistics."""
        return self.stats.copy()

    def get_member_participation(self) -> Dict[str, Dict[str, int]]:
        """
        Get participation statistics for each member.

        Returns:
            Dict mapping member_id to participation stats
        """
        participation = {}

        for member_id, member in self.members.items():
            if not member.is_active:
                continue

            meetings_attended = sum(
                1 for m in self.meetings.values() if member_id in m.attendees
            )
            meetings_missed = sum(
                1 for m in self.meetings.values() if member_id in m.absentees
            )
            total_meetings = len([m for m in self.meetings.values() if m.status == "completed"])

            participation[member_id] = {
                "name": member.name,
                "role": member.role.value,
                "meetings_attended": meetings_attended,
                "meetings_missed": meetings_missed,
                "total_meetings": total_meetings,
                "attendance_rate": (
                    (meetings_attended / total_meetings * 100) if total_meetings > 0 else 0
                ),
            }

        return participation

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive ERB summary report.

        Returns:
            Dict with ERB statistics and summary
        """
        active_members = self.get_active_members()
        voting_members = self.get_voting_members()
        completed_meetings = [m for m in self.meetings.values() if m.status == "completed"]

        approval_rate = 0.0
        if self.stats["total_decisions"] > 0:
            approval_rate = (
                self.stats["decisions_approved"] / self.stats["total_decisions"] * 100
            )

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "members": {
                "total": self.stats["total_members"],
                "active": self.stats["active_members"],
                "voting": len(voting_members),
                "internal": len([m for m in active_members if m.is_internal]),
                "external": len([m for m in active_members if not m.is_internal]),
                "by_role": {
                    role.value: len(self.get_member_by_role(role)) for role in ERBMemberRole
                },
            },
            "meetings": {
                "total": self.stats["total_meetings"],
                "completed": len(completed_meetings),
                "upcoming": len(
                    [
                        m
                        for m in self.meetings.values()
                        if m.status == "scheduled" and m.scheduled_date > datetime.utcnow()
                    ]
                ),
                "quorum_met_rate": (
                    len([m for m in completed_meetings if m.quorum_met])
                    / len(completed_meetings)
                    * 100
                    if completed_meetings
                    else 0
                ),
            },
            "decisions": {
                "total": self.stats["total_decisions"],
                "approved": self.stats["decisions_approved"],
                "rejected": self.stats["decisions_rejected"],
                "approval_rate": approval_rate,
                "pending_follow_ups": len(self.get_pending_follow_ups()),
                "overdue_follow_ups": len(self.get_overdue_follow_ups()),
            },
            "participation": self.get_member_participation(),
        }
