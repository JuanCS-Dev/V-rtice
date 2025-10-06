"""
Governance Module - Base Data Structures

Core data structures for the VÉRTICE Platform's ethical governance framework,
including Ethics Review Board (ERB), policy management, and audit infrastructure.

This module provides the foundation for Phase 0: Foundation & Governance.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4


# ============================================================================
# ENUMS
# ============================================================================


class PolicyType(str, Enum):
    """Types of ethical policies."""

    ETHICAL_USE = "ethical_use"
    RED_TEAMING = "red_teaming"
    DATA_PRIVACY = "data_privacy"
    INCIDENT_RESPONSE = "incident_response"
    WHISTLEBLOWER = "whistleblower"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ERBMemberRole(str, Enum):
    """Roles for Ethics Review Board members."""

    CHAIR = "chair"
    VICE_CHAIR = "vice_chair"
    TECHNICAL_MEMBER = "technical_member"
    LEGAL_MEMBER = "legal_member"
    EXTERNAL_ADVISOR = "external_advisor"
    OBSERVER = "observer"


class DecisionType(str, Enum):
    """Types of ERB decisions."""

    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    CONDITIONAL_APPROVED = "conditional_approved"
    REQUIRES_REVISION = "requires_revision"


class AuditLogLevel(str, Enum):
    """Audit log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class GovernanceAction(str, Enum):
    """Governance-related actions for audit trail."""

    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_VIOLATED = "policy_violated"
    ERB_MEETING_SCHEDULED = "erb_meeting_scheduled"
    ERB_DECISION_MADE = "erb_decision_made"
    ERB_MEMBER_ADDED = "erb_member_added"
    ERB_MEMBER_REMOVED = "erb_member_removed"
    AUDIT_LOG_CREATED = "audit_log_created"
    INCIDENT_REPORTED = "incident_reported"
    WHISTLEBLOWER_REPORT = "whistleblower_report"


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class GovernanceConfig:
    """Configuration for governance module."""

    # ERB Configuration
    erb_meeting_frequency_days: int = 30  # Monthly meetings
    erb_quorum_percentage: float = 0.6  # 60% quorum required
    erb_decision_threshold: float = 0.75  # 75% approval required

    # Policy Configuration
    policy_review_frequency_days: int = 365  # Annual policy review
    auto_enforce_policies: bool = True
    policy_violation_alert_threshold: PolicySeverity = PolicySeverity.MEDIUM

    # Audit Configuration
    audit_retention_days: int = 2555  # 7 years (GDPR requirement)
    audit_log_level: AuditLogLevel = AuditLogLevel.INFO
    enable_blockchain_audit: bool = False  # Optional Phase 1

    # Whistleblower Configuration
    whistleblower_anonymity: bool = True
    whistleblower_protection_days: int = 365

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "vertice_governance"
    db_user: str = "vertice"
    db_password: str = ""


# ============================================================================
# ERB DATA STRUCTURES
# ============================================================================


@dataclass
class ERBMember:
    """Ethics Review Board member."""

    member_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    email: str = ""
    role: ERBMemberRole = ERBMemberRole.TECHNICAL_MEMBER
    organization: str = ""  # Internal or external organization
    expertise: List[str] = field(default_factory=list)  # e.g., ["AI ethics", "Legal"]
    is_internal: bool = True
    is_active: bool = True
    appointed_date: datetime = field(default_factory=datetime.utcnow)
    term_end_date: Optional[datetime] = None
    voting_rights: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_voting_member(self) -> bool:
        """Check if member has voting rights and is active."""
        return self.is_active and self.voting_rights and (
            self.term_end_date is None or self.term_end_date > datetime.utcnow()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "member_id": self.member_id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "organization": self.organization,
            "expertise": self.expertise,
            "is_internal": self.is_internal,
            "is_active": self.is_active,
            "appointed_date": self.appointed_date.isoformat(),
            "term_end_date": self.term_end_date.isoformat() if self.term_end_date else None,
            "voting_rights": self.voting_rights,
            "metadata": self.metadata,
        }


@dataclass
class ERBMeeting:
    """Ethics Review Board meeting."""

    meeting_id: str = field(default_factory=lambda: str(uuid4()))
    scheduled_date: datetime = field(default_factory=datetime.utcnow)
    actual_date: Optional[datetime] = None
    duration_minutes: int = 120
    location: str = "Virtual"  # Virtual or physical location
    agenda: List[str] = field(default_factory=list)
    attendees: List[str] = field(default_factory=list)  # member_ids
    absentees: List[str] = field(default_factory=list)  # member_ids
    minutes: str = ""  # Meeting minutes
    decisions: List[str] = field(default_factory=list)  # decision_ids
    quorum_met: bool = False
    status: str = "scheduled"  # scheduled, completed, cancelled
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "meeting_id": self.meeting_id,
            "scheduled_date": self.scheduled_date.isoformat(),
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "agenda": self.agenda,
            "attendees": self.attendees,
            "absentees": self.absentees,
            "minutes": self.minutes,
            "decisions": self.decisions,
            "quorum_met": self.quorum_met,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class ERBDecision:
    """Ethics Review Board decision."""

    decision_id: str = field(default_factory=lambda: str(uuid4()))
    meeting_id: str = ""
    title: str = ""
    description: str = ""
    decision_type: DecisionType = DecisionType.APPROVED
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    rationale: str = ""
    conditions: List[str] = field(default_factory=list)  # If conditional approval
    follow_up_required: bool = False
    follow_up_deadline: Optional[datetime] = None
    created_date: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""  # member_id of chair
    related_policies: List[PolicyType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_approved(self) -> bool:
        """Check if decision is approved (fully or conditionally)."""
        return self.decision_type in [DecisionType.APPROVED, DecisionType.CONDITIONAL_APPROVED]

    def approval_percentage(self) -> float:
        """Calculate approval percentage."""
        total_votes = self.votes_for + self.votes_against + self.votes_abstain
        if total_votes == 0:
            return 0.0
        return (self.votes_for / total_votes) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "meeting_id": self.meeting_id,
            "title": self.title,
            "description": self.description,
            "decision_type": self.decision_type.value,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "votes_abstain": self.votes_abstain,
            "rationale": self.rationale,
            "conditions": self.conditions,
            "follow_up_required": self.follow_up_required,
            "follow_up_deadline": self.follow_up_deadline.isoformat() if self.follow_up_deadline else None,
            "created_date": self.created_date.isoformat(),
            "created_by": self.created_by,
            "related_policies": [p.value for p in self.related_policies],
            "metadata": self.metadata,
            "is_approved": self.is_approved(),
            "approval_percentage": self.approval_percentage(),
        }


# ============================================================================
# POLICY DATA STRUCTURES
# ============================================================================


@dataclass
class Policy:
    """Ethical policy definition."""

    policy_id: str = field(default_factory=lambda: str(uuid4()))
    policy_type: PolicyType = PolicyType.ETHICAL_USE
    version: str = "1.0"
    title: str = ""
    description: str = ""
    rules: List[str] = field(default_factory=list)
    scope: str = "all"  # all, maximus, immunis, rte, specific_service
    enforcement_level: PolicySeverity = PolicySeverity.MEDIUM
    auto_enforce: bool = True
    created_date: datetime = field(default_factory=datetime.utcnow)
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    approved_by_erb: bool = False
    erb_decision_id: Optional[str] = None
    stakeholders: List[str] = field(default_factory=list)  # Affected teams/systems
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_due_for_review(self) -> bool:
        """Check if policy is due for review."""
        if self.next_review_date is None:
            return False
        return datetime.utcnow() >= self.next_review_date

    def days_until_review(self) -> int:
        """Calculate days until next review."""
        if self.next_review_date is None:
            return -1
        delta = self.next_review_date - datetime.utcnow()
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "policy_type": self.policy_type.value,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "rules": self.rules,
            "scope": self.scope,
            "enforcement_level": self.enforcement_level.value,
            "auto_enforce": self.auto_enforce,
            "created_date": self.created_date.isoformat(),
            "last_review_date": self.last_review_date.isoformat() if self.last_review_date else None,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "approved_by_erb": self.approved_by_erb,
            "erb_decision_id": self.erb_decision_id,
            "stakeholders": self.stakeholders,
            "is_due_for_review": self.is_due_for_review(),
            "days_until_review": self.days_until_review(),
            "metadata": self.metadata,
        }


@dataclass
class PolicyViolation:
    """Policy violation record."""

    violation_id: str = field(default_factory=lambda: str(uuid4()))
    policy_id: str = ""
    policy_type: PolicyType = PolicyType.ETHICAL_USE
    severity: PolicySeverity = PolicySeverity.MEDIUM
    title: str = ""
    description: str = ""
    violated_rule: str = ""
    detection_method: str = "automated"  # automated, manual, whistleblower
    detected_by: str = "system"  # system, user_id, or "anonymous"
    detected_date: datetime = field(default_factory=datetime.utcnow)
    affected_system: str = ""  # maximus, immunis, rte, or specific service
    affected_users: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    remediation_required: bool = True
    remediation_status: str = "pending"  # pending, in_progress, completed, dismissed
    remediation_deadline: Optional[datetime] = None
    assigned_to: Optional[str] = None  # User responsible for remediation
    resolution_notes: str = ""
    resolved_date: Optional[datetime] = None
    escalated_to_erb: bool = False
    erb_decision_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_overdue(self) -> bool:
        """Check if remediation is overdue."""
        if self.remediation_deadline is None or self.remediation_status == "completed":
            return False
        return datetime.utcnow() > self.remediation_deadline

    def days_until_deadline(self) -> int:
        """Calculate days until remediation deadline."""
        if self.remediation_deadline is None:
            return -1
        delta = self.remediation_deadline - datetime.utcnow()
        return delta.days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_id": self.violation_id,
            "policy_id": self.policy_id,
            "policy_type": self.policy_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "violated_rule": self.violated_rule,
            "detection_method": self.detection_method,
            "detected_by": self.detected_by,
            "detected_date": self.detected_date.isoformat(),
            "affected_system": self.affected_system,
            "affected_users": self.affected_users,
            "context": self.context,
            "remediation_required": self.remediation_required,
            "remediation_status": self.remediation_status,
            "remediation_deadline": self.remediation_deadline.isoformat() if self.remediation_deadline else None,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "resolved_date": self.resolved_date.isoformat() if self.resolved_date else None,
            "escalated_to_erb": self.escalated_to_erb,
            "erb_decision_id": self.erb_decision_id,
            "is_overdue": self.is_overdue(),
            "days_until_deadline": self.days_until_deadline(),
            "metadata": self.metadata,
        }


# ============================================================================
# AUDIT DATA STRUCTURES
# ============================================================================


@dataclass
class AuditLog:
    """Audit log entry for governance actions."""

    log_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action: GovernanceAction = GovernanceAction.AUDIT_LOG_CREATED
    log_level: AuditLogLevel = AuditLogLevel.INFO
    actor: str = "system"  # User ID or "system"
    target_entity_type: str = ""  # policy, erb_member, meeting, decision
    target_entity_id: str = ""
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None  # For tracking related events
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "log_level": self.log_level.value,
            "actor": self.actor,
            "target_entity_type": self.target_entity_type,
            "target_entity_id": self.target_entity_id,
            "description": self.description,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


@dataclass
class WhistleblowerReport:
    """Whistleblower protection report."""

    report_id: str = field(default_factory=lambda: str(uuid4()))
    submission_date: datetime = field(default_factory=datetime.utcnow)
    reporter_id: Optional[str] = None  # None if anonymous
    is_anonymous: bool = True
    title: str = ""
    description: str = ""
    alleged_violation_type: PolicyType = PolicyType.ETHICAL_USE
    severity: PolicySeverity = PolicySeverity.MEDIUM
    affected_systems: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)  # File paths or references
    status: str = "submitted"  # submitted, under_review, investigated, resolved, dismissed
    assigned_investigator: Optional[str] = None
    investigation_notes: str = ""
    resolution: str = ""
    resolution_date: Optional[datetime] = None
    escalated_to_erb: bool = False
    erb_decision_id: Optional[str] = None
    retaliation_concerns: bool = False
    protection_measures: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_under_investigation(self) -> bool:
        """Check if report is currently under investigation."""
        return self.status in ["under_review", "investigated"]

    def is_resolved(self) -> bool:
        """Check if report is resolved."""
        return self.status in ["resolved", "dismissed"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (redact sensitive info if anonymous)."""
        data = {
            "report_id": self.report_id,
            "submission_date": self.submission_date.isoformat(),
            "is_anonymous": self.is_anonymous,
            "title": self.title,
            "description": self.description,
            "alleged_violation_type": self.alleged_violation_type.value,
            "severity": self.severity.value,
            "affected_systems": self.affected_systems,
            "status": self.status,
            "resolution": self.resolution,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "escalated_to_erb": self.escalated_to_erb,
            "erb_decision_id": self.erb_decision_id,
            "retaliation_concerns": self.retaliation_concerns,
            "is_under_investigation": self.is_under_investigation(),
            "is_resolved": self.is_resolved(),
        }

        # Redact sensitive information for anonymous reports
        if not self.is_anonymous:
            data["reporter_id"] = self.reporter_id
            data["evidence"] = self.evidence
            data["investigation_notes"] = self.investigation_notes
            data["protection_measures"] = self.protection_measures

        return data


# ============================================================================
# RESULT STRUCTURES
# ============================================================================


@dataclass
class GovernanceResult:
    """Result of governance operation."""

    success: bool = True
    message: str = ""
    entity_id: Optional[str] = None  # ID of created/updated entity
    entity_type: str = ""  # policy, member, meeting, etc.
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass
class PolicyEnforcementResult:
    """Result of policy enforcement check."""

    is_compliant: bool = True
    policy_id: str = ""
    policy_type: PolicyType = PolicyType.ETHICAL_USE
    checked_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    violations: List[PolicyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compliance_percentage(self) -> float:
        """Calculate compliance percentage."""
        if self.checked_rules == 0:
            return 100.0
        return (self.passed_rules / self.checked_rules) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_compliant": self.is_compliant,
            "policy_id": self.policy_id,
            "policy_type": self.policy_type.value,
            "checked_rules": self.checked_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "compliance_percentage": self.compliance_percentage(),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
