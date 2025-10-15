"""
Base Data Structures - 100% Coverage Test Suite

Complete tests for all dataclasses, enums, and utility methods in base.py.
Tests all to_dict() methods, boolean checks, calculations, and edge cases.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
"""

from datetime import datetime, timedelta

import pytest

from .base import (
    AuditLog,
    AuditLogLevel,
    DecisionType,
    ERBDecision,
    ERBMember,
    ERBMemberRole,
    ERBMeeting,
    GovernanceAction,
    GovernanceConfig,
    GovernanceResult,
    Policy,
    PolicyEnforcementResult,
    PolicySeverity,
    PolicyType,
    PolicyViolation,
    WhistleblowerReport,
)

# ============================================================================
# ENUM TESTS
# ============================================================================


class TestEnums:
    """Test all enum values."""

    def test_policy_type_values(self):
        """Test PolicyType enum values."""
        assert PolicyType.ETHICAL_USE.value == "ethical_use"
        assert PolicyType.RED_TEAMING.value == "red_teaming"
        assert PolicyType.DATA_PRIVACY.value == "data_privacy"
        assert PolicyType.INCIDENT_RESPONSE.value == "incident_response"
        assert PolicyType.WHISTLEBLOWER.value == "whistleblower"

    def test_policy_severity_values(self):
        """Test PolicySeverity enum values."""
        assert PolicySeverity.INFO.value == "info"
        assert PolicySeverity.LOW.value == "low"
        assert PolicySeverity.MEDIUM.value == "medium"
        assert PolicySeverity.HIGH.value == "high"
        assert PolicySeverity.CRITICAL.value == "critical"

    def test_erb_member_role_values(self):
        """Test ERBMemberRole enum values."""
        assert ERBMemberRole.CHAIR.value == "chair"
        assert ERBMemberRole.VICE_CHAIR.value == "vice_chair"
        assert ERBMemberRole.TECHNICAL_MEMBER.value == "technical_member"
        assert ERBMemberRole.LEGAL_MEMBER.value == "legal_member"
        assert ERBMemberRole.EXTERNAL_ADVISOR.value == "external_advisor"
        assert ERBMemberRole.OBSERVER.value == "observer"

    def test_decision_type_values(self):
        """Test DecisionType enum values."""
        assert DecisionType.APPROVED.value == "approved"
        assert DecisionType.REJECTED.value == "rejected"
        assert DecisionType.DEFERRED.value == "deferred"
        assert DecisionType.CONDITIONAL_APPROVED.value == "conditional_approved"
        assert DecisionType.REQUIRES_REVISION.value == "requires_revision"

    def test_audit_log_level_values(self):
        """Test AuditLogLevel enum values."""
        assert AuditLogLevel.DEBUG.value == "debug"
        assert AuditLogLevel.INFO.value == "info"
        assert AuditLogLevel.WARNING.value == "warning"
        assert AuditLogLevel.ERROR.value == "error"
        assert AuditLogLevel.CRITICAL.value == "critical"

    def test_governance_action_values(self):
        """Test GovernanceAction enum values."""
        assert GovernanceAction.POLICY_CREATED.value == "policy_created"
        assert GovernanceAction.POLICY_UPDATED.value == "policy_updated"
        assert GovernanceAction.POLICY_VIOLATED.value == "policy_violated"
        assert GovernanceAction.ERB_MEETING_SCHEDULED.value == "erb_meeting_scheduled"
        assert GovernanceAction.ERB_DECISION_MADE.value == "erb_decision_made"
        assert GovernanceAction.ERB_MEMBER_ADDED.value == "erb_member_added"
        assert GovernanceAction.ERB_MEMBER_REMOVED.value == "erb_member_removed"
        assert GovernanceAction.AUDIT_LOG_CREATED.value == "audit_log_created"
        assert GovernanceAction.INCIDENT_REPORTED.value == "incident_reported"
        assert GovernanceAction.WHISTLEBLOWER_REPORT.value == "whistleblower_report"


# ============================================================================
# GOVERNANCE CONFIG TESTS
# ============================================================================


class TestGovernanceConfig:
    """Test GovernanceConfig dataclass."""

    def test_config_defaults(self):
        """Test GovernanceConfig default values."""
        config = GovernanceConfig()

        assert config.erb_meeting_frequency_days == 30
        assert config.erb_quorum_percentage == 0.6
        assert config.erb_decision_threshold == 0.75
        assert config.policy_review_frequency_days == 365
        assert config.auto_enforce_policies is True
        assert config.policy_violation_alert_threshold == PolicySeverity.MEDIUM
        assert config.audit_retention_days == 2555  # 7 years
        assert config.audit_log_level == AuditLogLevel.INFO
        assert config.enable_blockchain_audit is False
        assert config.whistleblower_anonymity is True
        assert config.whistleblower_protection_days == 365
        assert config.db_host == "localhost"
        assert config.db_port == 5432
        assert config.db_name == "vertice_governance"
        assert config.db_user == "vertice"
        assert config.db_password == ""

    def test_config_custom_values(self):
        """Test GovernanceConfig with custom values."""
        config = GovernanceConfig(
            erb_meeting_frequency_days=14,
            auto_enforce_policies=False,
            audit_log_level=AuditLogLevel.DEBUG,
        )

        assert config.erb_meeting_frequency_days == 14
        assert config.auto_enforce_policies is False
        assert config.audit_log_level == AuditLogLevel.DEBUG


# ============================================================================
# ERB MEMBER TESTS
# ============================================================================


class TestERBMember:
    """Test ERBMember dataclass."""

    def test_erb_member_defaults(self):
        """Test ERBMember default values."""
        member = ERBMember()

        assert member.member_id != ""
        assert member.name == ""
        assert member.email == ""
        assert member.role == ERBMemberRole.TECHNICAL_MEMBER
        assert member.organization == ""
        assert member.expertise == []
        assert member.is_internal is True
        assert member.is_active is True
        assert member.voting_rights is True
        assert isinstance(member.appointed_date, datetime)
        assert member.term_end_date is None
        assert member.metadata == {}

    def test_erb_member_is_voting_member_active_no_term(self):
        """Test is_voting_member() for active member with no term end."""
        member = ERBMember(
            name="Dr. Test",
            is_active=True,
            voting_rights=True,
            term_end_date=None,
        )

        assert member.is_voting_member() is True

    def test_erb_member_is_voting_member_active_future_term(self):
        """Test is_voting_member() for active member with future term end."""
        future_date = datetime.utcnow() + timedelta(days=365)
        member = ERBMember(
            name="Dr. Test",
            is_active=True,
            voting_rights=True,
            term_end_date=future_date,
        )

        assert member.is_voting_member() is True

    def test_erb_member_is_voting_member_expired_term(self):
        """Test is_voting_member() for member with expired term."""
        past_date = datetime.utcnow() - timedelta(days=1)
        member = ERBMember(
            name="Dr. Test",
            is_active=True,
            voting_rights=True,
            term_end_date=past_date,
        )

        assert member.is_voting_member() is False

    def test_erb_member_is_voting_member_inactive(self):
        """Test is_voting_member() for inactive member."""
        member = ERBMember(
            name="Dr. Test",
            is_active=False,
            voting_rights=True,
        )

        assert member.is_voting_member() is False

    def test_erb_member_is_voting_member_no_rights(self):
        """Test is_voting_member() for member without voting rights."""
        member = ERBMember(
            name="Dr. Test",
            is_active=True,
            voting_rights=False,
        )

        assert member.is_voting_member() is False

    def test_erb_member_to_dict(self):
        """Test ERBMember.to_dict()."""
        member = ERBMember(
            name="Dr. Test",
            email="test@example.com",
            role=ERBMemberRole.CHAIR,
            organization="Test Org",
            expertise=["AI Ethics"],
        )

        result = member.to_dict()

        assert result["name"] == "Dr. Test"
        assert result["email"] == "test@example.com"
        assert result["role"] == "chair"
        assert result["organization"] == "Test Org"
        assert result["expertise"] == ["AI Ethics"]
        assert result["is_active"] is True
        assert result["voting_rights"] is True
        assert result["term_end_date"] is None

    def test_erb_member_to_dict_with_term_end(self):
        """Test ERBMember.to_dict() with term_end_date."""
        term_end = datetime.utcnow() + timedelta(days=365)
        member = ERBMember(
            name="Dr. Test",
            term_end_date=term_end,
        )

        result = member.to_dict()

        assert result["term_end_date"] is not None
        assert isinstance(result["term_end_date"], str)


# ============================================================================
# ERB MEETING TESTS
# ============================================================================


class TestERBMeeting:
    """Test ERBMeeting dataclass."""

    def test_erb_meeting_defaults(self):
        """Test ERBMeeting default values."""
        meeting = ERBMeeting()

        assert meeting.meeting_id != ""
        assert isinstance(meeting.scheduled_date, datetime)
        assert meeting.actual_date is None
        assert meeting.duration_minutes == 120
        assert meeting.location == "Virtual"
        assert meeting.agenda == []
        assert meeting.attendees == []
        assert meeting.absentees == []
        assert meeting.minutes == ""
        assert meeting.decisions == []
        assert meeting.quorum_met is False
        assert meeting.status == "scheduled"
        assert meeting.metadata == {}

    def test_erb_meeting_to_dict(self):
        """Test ERBMeeting.to_dict()."""
        meeting = ERBMeeting(
            scheduled_date=datetime.utcnow(),
            agenda=["Item 1", "Item 2"],
            attendees=["member-1", "member-2"],
            quorum_met=True,
            status="completed",
        )

        result = meeting.to_dict()

        assert result["agenda"] == ["Item 1", "Item 2"]
        assert result["attendees"] == ["member-1", "member-2"]
        assert result["quorum_met"] is True
        assert result["status"] == "completed"
        assert result["actual_date"] is None

    def test_erb_meeting_to_dict_with_actual_date(self):
        """Test ERBMeeting.to_dict() with actual_date."""
        meeting = ERBMeeting(
            scheduled_date=datetime.utcnow(),
            actual_date=datetime.utcnow(),
        )

        result = meeting.to_dict()

        assert result["actual_date"] is not None
        assert isinstance(result["actual_date"], str)


# ============================================================================
# ERB DECISION TESTS
# ============================================================================


class TestERBDecision:
    """Test ERBDecision dataclass."""

    def test_erb_decision_defaults(self):
        """Test ERBDecision default values."""
        decision = ERBDecision()

        assert decision.decision_id != ""
        assert decision.meeting_id == ""
        assert decision.title == ""
        assert decision.description == ""
        assert decision.decision_type == DecisionType.APPROVED
        assert decision.votes_for == 0
        assert decision.votes_against == 0
        assert decision.votes_abstain == 0
        assert decision.rationale == ""
        assert decision.conditions == []
        assert decision.follow_up_required is False
        assert decision.follow_up_deadline is None
        assert isinstance(decision.created_date, datetime)
        assert decision.created_by == ""
        assert decision.related_policies == []
        assert decision.metadata == {}

    def test_erb_decision_is_approved_fully(self):
        """Test is_approved() for fully approved decision."""
        decision = ERBDecision(decision_type=DecisionType.APPROVED)

        assert decision.is_approved() is True

    def test_erb_decision_is_approved_conditionally(self):
        """Test is_approved() for conditionally approved decision."""
        decision = ERBDecision(decision_type=DecisionType.CONDITIONAL_APPROVED)

        assert decision.is_approved() is True

    def test_erb_decision_is_approved_rejected(self):
        """Test is_approved() for rejected decision."""
        decision = ERBDecision(decision_type=DecisionType.REJECTED)

        assert decision.is_approved() is False

    def test_erb_decision_is_approved_deferred(self):
        """Test is_approved() for deferred decision."""
        decision = ERBDecision(decision_type=DecisionType.DEFERRED)

        assert decision.is_approved() is False

    def test_erb_decision_approval_percentage(self):
        """Test approval_percentage() calculation."""
        decision = ERBDecision(
            votes_for=7,
            votes_against=2,
            votes_abstain=1,
        )

        percentage = decision.approval_percentage()

        assert percentage == 70.0

    def test_erb_decision_approval_percentage_zero_votes(self):
        """Test approval_percentage() with zero votes."""
        decision = ERBDecision()

        percentage = decision.approval_percentage()

        assert percentage == 0.0

    def test_erb_decision_to_dict(self):
        """Test ERBDecision.to_dict()."""
        decision = ERBDecision(
            title="Test Decision",
            votes_for=8,
            votes_against=1,
            related_policies=[PolicyType.ETHICAL_USE, PolicyType.DATA_PRIVACY],
        )

        result = decision.to_dict()

        assert result["title"] == "Test Decision"
        assert result["votes_for"] == 8
        assert result["votes_against"] == 1
        assert result["related_policies"] == ["ethical_use", "data_privacy"]
        assert result["is_approved"] is True
        assert result["approval_percentage"] > 0

    def test_erb_decision_to_dict_with_follow_up(self):
        """Test ERBDecision.to_dict() with follow_up_deadline."""
        deadline = datetime.utcnow() + timedelta(days=30)
        decision = ERBDecision(
            follow_up_required=True,
            follow_up_deadline=deadline,
        )

        result = decision.to_dict()

        assert result["follow_up_deadline"] is not None
        assert isinstance(result["follow_up_deadline"], str)


# ============================================================================
# POLICY TESTS
# ============================================================================


class TestPolicy:
    """Test Policy dataclass."""

    def test_policy_defaults(self):
        """Test Policy default values."""
        policy = Policy()

        assert policy.policy_id != ""
        assert policy.policy_type == PolicyType.ETHICAL_USE
        assert policy.version == "1.0"
        assert policy.title == ""
        assert policy.description == ""
        assert policy.rules == []
        assert policy.scope == "all"
        assert policy.enforcement_level == PolicySeverity.MEDIUM
        assert policy.auto_enforce is True
        assert isinstance(policy.created_date, datetime)
        assert policy.last_review_date is None
        assert policy.next_review_date is None
        assert policy.approved_by_erb is False
        assert policy.erb_decision_id is None
        assert policy.stakeholders == []
        assert policy.metadata == {}

    def test_policy_is_due_for_review_no_date(self):
        """Test is_due_for_review() with no next_review_date."""
        policy = Policy(next_review_date=None)

        assert policy.is_due_for_review() is False

    def test_policy_is_due_for_review_future_date(self):
        """Test is_due_for_review() with future review date."""
        future_date = datetime.utcnow() + timedelta(days=100)
        policy = Policy(next_review_date=future_date)

        assert policy.is_due_for_review() is False

    def test_policy_is_due_for_review_past_date(self):
        """Test is_due_for_review() with past review date."""
        past_date = datetime.utcnow() - timedelta(days=1)
        policy = Policy(next_review_date=past_date)

        assert policy.is_due_for_review() is True

    def test_policy_days_until_review_no_date(self):
        """Test days_until_review() with no next_review_date."""
        policy = Policy(next_review_date=None)

        assert policy.days_until_review() == -1

    def test_policy_days_until_review_future_date(self):
        """Test days_until_review() with future review date."""
        future_date = datetime.utcnow() + timedelta(days=30)
        policy = Policy(next_review_date=future_date)

        days = policy.days_until_review()

        assert 28 <= days <= 30  # Allow some tolerance

    def test_policy_days_until_review_past_date(self):
        """Test days_until_review() with past review date."""
        past_date = datetime.utcnow() - timedelta(days=10)
        policy = Policy(next_review_date=past_date)

        assert policy.days_until_review() == 0  # max(0, negative)

    def test_policy_to_dict(self):
        """Test Policy.to_dict()."""
        policy = Policy(
            policy_type=PolicyType.RED_TEAMING,
            version="2.0",
            title="Test Policy",
            rules=["Rule 1", "Rule 2"],
            enforcement_level=PolicySeverity.HIGH,
        )

        result = policy.to_dict()

        assert result["policy_type"] == "red_teaming"
        assert result["version"] == "2.0"
        assert result["title"] == "Test Policy"
        assert result["rules"] == ["Rule 1", "Rule 2"]
        assert result["enforcement_level"] == "high"
        assert result["is_due_for_review"] is False
        assert result["days_until_review"] == -1


# ============================================================================
# POLICY VIOLATION TESTS
# ============================================================================


class TestPolicyViolation:
    """Test PolicyViolation dataclass."""

    def test_policy_violation_defaults(self):
        """Test PolicyViolation default values."""
        violation = PolicyViolation()

        assert violation.violation_id != ""
        assert violation.policy_id == ""
        assert violation.policy_type == PolicyType.ETHICAL_USE
        assert violation.severity == PolicySeverity.MEDIUM
        assert violation.title == ""
        assert violation.description == ""
        assert violation.violated_rule == ""
        assert violation.detection_method == "automated"
        assert violation.detected_by == "system"
        assert isinstance(violation.detected_date, datetime)
        assert violation.affected_system == ""
        assert violation.affected_users == []
        assert violation.context == {}
        assert violation.remediation_required is True
        assert violation.remediation_status == "pending"
        assert violation.remediation_deadline is None
        assert violation.assigned_to is None
        assert violation.resolution_notes == ""
        assert violation.resolved_date is None
        assert violation.escalated_to_erb is False
        assert violation.erb_decision_id is None
        assert violation.metadata == {}

    def test_policy_violation_is_overdue_no_deadline(self):
        """Test is_overdue() with no deadline."""
        violation = PolicyViolation(remediation_deadline=None)

        assert violation.is_overdue() is False

    def test_policy_violation_is_overdue_completed(self):
        """Test is_overdue() for completed remediation."""
        past_deadline = datetime.utcnow() - timedelta(days=1)
        violation = PolicyViolation(
            remediation_deadline=past_deadline,
            remediation_status="completed",
        )

        assert violation.is_overdue() is False

    def test_policy_violation_is_overdue_past_deadline(self):
        """Test is_overdue() with past deadline."""
        past_deadline = datetime.utcnow() - timedelta(days=1)
        violation = PolicyViolation(
            remediation_deadline=past_deadline,
            remediation_status="pending",
        )

        assert violation.is_overdue() is True

    def test_policy_violation_is_overdue_future_deadline(self):
        """Test is_overdue() with future deadline."""
        future_deadline = datetime.utcnow() + timedelta(days=7)
        violation = PolicyViolation(
            remediation_deadline=future_deadline,
            remediation_status="pending",
        )

        assert violation.is_overdue() is False

    def test_policy_violation_days_until_deadline_no_deadline(self):
        """Test days_until_deadline() with no deadline."""
        violation = PolicyViolation(remediation_deadline=None)

        assert violation.days_until_deadline() == -1

    def test_policy_violation_days_until_deadline_future(self):
        """Test days_until_deadline() with future deadline."""
        future_deadline = datetime.utcnow() + timedelta(days=10)
        violation = PolicyViolation(remediation_deadline=future_deadline)

        days = violation.days_until_deadline()

        assert 9 <= days <= 10

    def test_policy_violation_to_dict(self):
        """Test PolicyViolation.to_dict()."""
        violation = PolicyViolation(
            title="Test Violation",
            severity=PolicySeverity.CRITICAL,
            remediation_status="in_progress",
        )

        result = violation.to_dict()

        assert result["title"] == "Test Violation"
        assert result["severity"] == "critical"
        assert result["remediation_status"] == "in_progress"
        assert result["is_overdue"] is False
        assert result["days_until_deadline"] == -1


# ============================================================================
# AUDIT LOG TESTS
# ============================================================================


class TestAuditLog:
    """Test AuditLog dataclass."""

    def test_audit_log_defaults(self):
        """Test AuditLog default values."""
        log = AuditLog()

        assert log.log_id != ""
        assert isinstance(log.timestamp, datetime)
        assert log.action == GovernanceAction.AUDIT_LOG_CREATED
        assert log.log_level == AuditLogLevel.INFO
        assert log.actor == "system"
        assert log.target_entity_type == ""
        assert log.target_entity_id == ""
        assert log.description == ""
        assert log.details == {}
        assert log.ip_address is None
        assert log.user_agent is None
        assert log.session_id is None
        assert log.correlation_id is None
        assert log.metadata == {}

    def test_audit_log_to_dict(self):
        """Test AuditLog.to_dict()."""
        log = AuditLog(
            action=GovernanceAction.POLICY_CREATED,
            log_level=AuditLogLevel.WARNING,
            actor="user-123",
            target_entity_type="policy",
            target_entity_id="policy-456",
            description="Test log",
        )

        result = log.to_dict()

        assert result["action"] == "policy_created"
        assert result["log_level"] == "warning"
        assert result["actor"] == "user-123"
        assert result["target_entity_type"] == "policy"
        assert result["target_entity_id"] == "policy-456"
        assert result["description"] == "Test log"


# ============================================================================
# WHISTLEBLOWER REPORT TESTS
# ============================================================================


class TestWhistleblowerReport:
    """Test WhistleblowerReport dataclass."""

    def test_whistleblower_report_defaults(self):
        """Test WhistleblowerReport default values."""
        report = WhistleblowerReport()

        assert report.report_id != ""
        assert isinstance(report.submission_date, datetime)
        assert report.reporter_id is None
        assert report.is_anonymous is True
        assert report.title == ""
        assert report.description == ""
        assert report.alleged_violation_type == PolicyType.ETHICAL_USE
        assert report.severity == PolicySeverity.MEDIUM
        assert report.affected_systems == []
        assert report.evidence == []
        assert report.status == "submitted"
        assert report.assigned_investigator is None
        assert report.investigation_notes == ""
        assert report.resolution == ""
        assert report.resolution_date is None
        assert report.escalated_to_erb is False
        assert report.erb_decision_id is None
        assert report.retaliation_concerns is False
        assert report.protection_measures == []
        assert report.metadata == {}

    def test_whistleblower_report_is_under_investigation_under_review(self):
        """Test is_under_investigation() for under_review status."""
        report = WhistleblowerReport(status="under_review")

        assert report.is_under_investigation() is True

    def test_whistleblower_report_is_under_investigation_investigated(self):
        """Test is_under_investigation() for investigated status."""
        report = WhistleblowerReport(status="investigated")

        assert report.is_under_investigation() is True

    def test_whistleblower_report_is_under_investigation_submitted(self):
        """Test is_under_investigation() for submitted status."""
        report = WhistleblowerReport(status="submitted")

        assert report.is_under_investigation() is False

    def test_whistleblower_report_is_resolved_resolved(self):
        """Test is_resolved() for resolved status."""
        report = WhistleblowerReport(status="resolved")

        assert report.is_resolved() is True

    def test_whistleblower_report_is_resolved_dismissed(self):
        """Test is_resolved() for dismissed status."""
        report = WhistleblowerReport(status="dismissed")

        assert report.is_resolved() is True

    def test_whistleblower_report_is_resolved_submitted(self):
        """Test is_resolved() for submitted status."""
        report = WhistleblowerReport(status="submitted")

        assert report.is_resolved() is False

    def test_whistleblower_report_to_dict_anonymous(self):
        """Test WhistleblowerReport.to_dict() for anonymous report."""
        report = WhistleblowerReport(
            title="Test Report",
            is_anonymous=True,
            reporter_id="secret-123",
            evidence=["evidence1.pdf"],
        )

        result = report.to_dict()

        assert result["title"] == "Test Report"
        assert result["is_anonymous"] is True
        # Should NOT include reporter_id or evidence for anonymous
        assert "reporter_id" not in result
        assert "evidence" not in result

    def test_whistleblower_report_to_dict_non_anonymous(self):
        """Test WhistleblowerReport.to_dict() for non-anonymous report."""
        report = WhistleblowerReport(
            title="Test Report",
            is_anonymous=False,
            reporter_id="user-123",
            evidence=["evidence1.pdf"],
            investigation_notes="Notes",
            protection_measures=["Measure 1"],
        )

        result = report.to_dict()

        assert result["title"] == "Test Report"
        assert result["is_anonymous"] is False
        # Should include all fields for non-anonymous
        assert result["reporter_id"] == "user-123"
        assert result["evidence"] == ["evidence1.pdf"]
        assert result["investigation_notes"] == "Notes"
        assert result["protection_measures"] == ["Measure 1"]


# ============================================================================
# RESULT STRUCTURES TESTS
# ============================================================================


class TestGovernanceResult:
    """Test GovernanceResult dataclass."""

    def test_governance_result_defaults(self):
        """Test GovernanceResult default values."""
        result = GovernanceResult()

        assert result.success is True
        assert result.message == ""
        assert result.entity_id is None
        assert result.entity_type == ""
        assert result.warnings == []
        assert result.errors == []
        assert result.metadata == {}

    def test_governance_result_to_dict(self):
        """Test GovernanceResult.to_dict()."""
        result = GovernanceResult(
            success=True,
            message="Operation successful",
            entity_id="entity-123",
            entity_type="policy",
            warnings=["Warning 1"],
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["message"] == "Operation successful"
        assert data["entity_id"] == "entity-123"
        assert data["entity_type"] == "policy"
        assert data["warnings"] == ["Warning 1"]


class TestPolicyEnforcementResult:
    """Test PolicyEnforcementResult dataclass."""

    def test_policy_enforcement_result_defaults(self):
        """Test PolicyEnforcementResult default values."""
        result = PolicyEnforcementResult()

        assert result.is_compliant is True
        assert result.policy_id == ""
        assert result.policy_type == PolicyType.ETHICAL_USE
        assert result.checked_rules == 0
        assert result.passed_rules == 0
        assert result.failed_rules == 0
        assert result.violations == []
        assert result.warnings == []
        assert isinstance(result.timestamp, datetime)
        assert result.metadata == {}

    def test_policy_enforcement_result_compliance_percentage(self):
        """Test compliance_percentage() calculation."""
        result = PolicyEnforcementResult(
            checked_rules=10,
            passed_rules=7,
            failed_rules=3,
        )

        percentage = result.compliance_percentage()

        assert percentage == 70.0

    def test_policy_enforcement_result_compliance_percentage_zero_rules(self):
        """Test compliance_percentage() with zero checked rules."""
        result = PolicyEnforcementResult()

        percentage = result.compliance_percentage()

        assert percentage == 100.0

    def test_policy_enforcement_result_to_dict(self):
        """Test PolicyEnforcementResult.to_dict()."""
        result = PolicyEnforcementResult(
            is_compliant=False,
            checked_rules=5,
            passed_rules=3,
            failed_rules=2,
            warnings=["Warning 1"],
        )

        data = result.to_dict()

        assert data["is_compliant"] is False
        assert data["checked_rules"] == 5
        assert data["passed_rules"] == 3
        assert data["failed_rules"] == 2
        assert data["compliance_percentage"] == 60.0
        assert data["warnings"] == ["Warning 1"]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
