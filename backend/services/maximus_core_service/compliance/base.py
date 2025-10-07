"""
Compliance Base Classes and Data Structures

This module defines the core data structures, enums, and base classes for the
multi-jurisdictional compliance and certification engine.

Supports:
- 8 major regulations (EU AI Act, GDPR, NIST AI RMF, US EO 14110, Brazil LGPD, ISO 27001, SOC 2, IEEE 7000)
- Automated compliance checking
- Evidence collection and management
- Gap analysis and remediation tracking
- Compliance monitoring and alerting

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import uuid


# ============================================================================
# ENUMS
# ============================================================================


class RegulationType(Enum):
    """Supported regulatory frameworks."""

    EU_AI_ACT = "eu_ai_act"  # EU Artificial Intelligence Act (High-Risk AI)
    GDPR = "gdpr"  # General Data Protection Regulation (Article 22)
    NIST_AI_RMF = "nist_ai_rmf"  # NIST AI Risk Management Framework 1.0
    US_EO_14110 = "us_eo_14110"  # US Executive Order 14110 (Safe, Secure AI)
    BRAZIL_LGPD = "brazil_lgpd"  # Lei Geral de Proteção de Dados
    ISO_27001 = "iso_27001"  # ISO/IEC 27001:2022 (Information Security)
    SOC2_TYPE_II = "soc2_type_ii"  # SOC 2 Type II (Trust Services)
    IEEE_7000 = "ieee_7000"  # IEEE 7000-2021 (Ethical AI Design)


class ControlCategory(Enum):
    """Categories of compliance controls."""

    TECHNICAL = "technical"  # Technical safeguards (encryption, access control)
    ORGANIZATIONAL = "organizational"  # Policies, procedures, training
    DOCUMENTATION = "documentation"  # Required documentation and records
    TESTING = "testing"  # Testing and validation requirements
    MONITORING = "monitoring"  # Continuous monitoring and alerting
    GOVERNANCE = "governance"  # Governance structures and oversight
    SECURITY = "security"  # Security controls and measures
    PRIVACY = "privacy"  # Privacy protection controls


class ComplianceStatus(Enum):
    """Status of compliance checks."""

    COMPLIANT = "compliant"  # Fully compliant with requirement
    NON_COMPLIANT = "non_compliant"  # Not compliant, violation detected
    PARTIALLY_COMPLIANT = "partially_compliant"  # Partially compliant, gaps exist
    NOT_APPLICABLE = "not_applicable"  # Control not applicable to current scope
    PENDING_REVIEW = "pending_review"  # Awaiting manual review
    EVIDENCE_REQUIRED = "evidence_required"  # Missing required evidence
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"  # Fixes being implemented


class ViolationSeverity(Enum):
    """Severity levels for compliance violations."""

    CRITICAL = "critical"  # Critical violation, immediate action required
    HIGH = "high"  # High severity, urgent remediation needed
    MEDIUM = "medium"  # Medium severity, remediation required
    LOW = "low"  # Low severity, should be addressed
    INFORMATIONAL = "informational"  # Informational finding, no immediate action


class EvidenceType(Enum):
    """Types of compliance evidence."""

    LOG = "log"  # System logs, audit logs
    DOCUMENT = "document"  # Policy documents, procedures, manuals
    SCREENSHOT = "screenshot"  # Screenshots of configurations, dashboards
    TEST_RESULT = "test_result"  # Test execution results
    AUDIT_REPORT = "audit_report"  # Third-party audit reports
    CONFIGURATION = "configuration"  # System/service configuration files
    CODE_REVIEW = "code_review"  # Code review records
    POLICY = "policy"  # Organizational policies
    TRAINING_RECORD = "training_record"  # Training completion records
    INCIDENT_REPORT = "incident_report"  # Security incident reports
    RISK_ASSESSMENT = "risk_assessment"  # Risk assessment documents
    CERTIFICATION = "certification"  # Certification documents


class RemediationStatus(Enum):
    """Status of remediation efforts."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    VERIFIED = "verified"
    FAILED = "failed"


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================


@dataclass
class Control:
    """
    Individual compliance control.

    Represents a specific requirement from a regulation that must be satisfied.
    """

    control_id: str  # Unique control identifier (e.g., "EU-AI-ACT-ART-9")
    regulation_type: RegulationType  # Parent regulation
    category: ControlCategory  # Control category
    title: str  # Control title
    description: str  # Detailed description of requirement
    mandatory: bool = True  # Whether control is mandatory
    test_procedure: Optional[str] = None  # How to test compliance
    evidence_required: List[EvidenceType] = field(default_factory=list)
    reference: Optional[str] = None  # Citation (e.g., "Article 9, Section 2")
    tags: Set[str] = field(default_factory=set)  # Tags for filtering

    def __post_init__(self):
        """Validate control data."""
        if not self.control_id:
            raise ValueError("control_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.description:
            raise ValueError("description is required")


@dataclass
class Regulation:
    """
    Complete regulation definition.

    Defines a regulatory framework with all its controls and requirements.
    """

    regulation_type: RegulationType
    name: str  # Full name (e.g., "EU Artificial Intelligence Act")
    version: str  # Regulation version
    effective_date: datetime  # When regulation becomes effective
    jurisdiction: str  # Geographic jurisdiction (e.g., "EU", "USA", "Brazil")
    description: str  # High-level description
    controls: List[Control] = field(default_factory=list)
    scope: Optional[str] = None  # Applicability scope
    penalties: Optional[str] = None  # Non-compliance penalties
    update_frequency_days: int = 90  # How often to review for updates
    authority: Optional[str] = None  # Regulatory authority
    url: Optional[str] = None  # Official regulation URL

    def __post_init__(self):
        """Validate regulation data."""
        if not self.name:
            raise ValueError("name is required")
        if not self.version:
            raise ValueError("version is required")
        if self.update_frequency_days <= 0:
            raise ValueError("update_frequency_days must be positive")

    def get_mandatory_controls(self) -> List[Control]:
        """Return list of mandatory controls."""
        return [c for c in self.controls if c.mandatory]

    def get_controls_by_category(self, category: ControlCategory) -> List[Control]:
        """Return controls for specific category."""
        return [c for c in self.controls if c.category == category]

    def get_control(self, control_id: str) -> Optional[Control]:
        """Get specific control by ID."""
        for control in self.controls:
            if control.control_id == control_id:
                return control
        return None


@dataclass
class Evidence:
    """
    Evidence item supporting compliance.

    Documents proof of compliance with specific controls.
    """

    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    control_id: str = ""  # Associated control
    title: str = ""
    description: str = ""
    collected_at: datetime = field(default_factory=datetime.utcnow)
    collected_by: Optional[str] = None  # User/system that collected evidence
    file_path: Optional[str] = None  # Path to evidence file
    file_hash: Optional[str] = None  # SHA-256 hash for integrity
    metadata: Dict[str, Any] = field(default_factory=dict)
    expiration_date: Optional[datetime] = None  # When evidence expires
    verified: bool = False  # Whether evidence was verified by auditor
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate evidence data."""
        if not self.control_id:
            raise ValueError("control_id is required")
        if not self.title:
            raise ValueError("title is required")

    def is_expired(self) -> bool:
        """Check if evidence has expired."""
        if self.expiration_date is None:
            return False
        return datetime.utcnow() > self.expiration_date

    def verify(self, verified_by: str):
        """Mark evidence as verified."""
        self.verified = True
        self.verified_by = verified_by
        self.verified_at = datetime.utcnow()


@dataclass
class ComplianceViolation:
    """
    Compliance violation details.

    Documents a specific non-compliance finding.
    """

    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str = ""  # Violated control
    regulation_type: RegulationType = RegulationType.ISO_27001
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    title: str = ""
    description: str = ""  # What was violated
    detected_at: datetime = field(default_factory=datetime.utcnow)
    detected_by: str = "system"  # System or auditor name
    impact: Optional[str] = None  # Business/security impact
    recommendation: Optional[str] = None  # Remediation recommendation
    affected_systems: List[str] = field(default_factory=list)
    cve_ids: List[str] = field(default_factory=list)  # Related CVEs if applicable
    mitre_tactics: List[str] = field(default_factory=list)  # MITRE ATT&CK tactics
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

    def __post_init__(self):
        """Validate violation data."""
        if not self.control_id:
            raise ValueError("control_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.description:
            raise ValueError("description is required")

    def resolve(self, resolved_by: str, notes: str):
        """Mark violation as resolved."""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        self.resolution_notes = notes

    def get_age_hours(self) -> float:
        """Get age of violation in hours."""
        delta = datetime.utcnow() - self.detected_at
        return delta.total_seconds() / 3600


@dataclass
class ComplianceResult:
    """
    Result of compliance check.

    Documents the outcome of checking compliance for a specific control.
    """

    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str = ""
    regulation_type: RegulationType = RegulationType.ISO_27001
    status: ComplianceStatus = ComplianceStatus.PENDING_REVIEW
    checked_at: datetime = field(default_factory=datetime.utcnow)
    checked_by: str = "system"
    score: Optional[float] = None  # Compliance score 0.0-1.0
    evidence: List[Evidence] = field(default_factory=list)
    violations: List[ComplianceViolation] = field(default_factory=list)
    notes: Optional[str] = None
    next_check_due: Optional[datetime] = None
    automated: bool = True  # Whether check was automated

    def __post_init__(self):
        """Validate result data."""
        if not self.control_id:
            raise ValueError("control_id is required")
        if self.score is not None and not (0.0 <= self.score <= 1.0):
            raise ValueError("score must be between 0.0 and 1.0")

    def is_compliant(self) -> bool:
        """Check if result indicates compliance."""
        return self.status == ComplianceStatus.COMPLIANT

    def has_violations(self) -> bool:
        """Check if violations were found."""
        return len(self.violations) > 0

    def get_critical_violations(self) -> List[ComplianceViolation]:
        """Get critical violations."""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]


@dataclass
class Gap:
    """
    Compliance gap identified during gap analysis.
    """

    gap_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str = ""
    regulation_type: RegulationType = RegulationType.ISO_27001
    title: str = ""
    description: str = ""
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    current_state: str = ""  # Current implementation status
    required_state: str = ""  # Required implementation status
    gap_type: str = "missing_control"  # missing_control, partial_implementation, outdated
    identified_at: datetime = field(default_factory=datetime.utcnow)
    estimated_effort_hours: Optional[int] = None
    priority: int = 3  # 1 (highest) to 5 (lowest)
    remediation_status: RemediationStatus = RemediationStatus.NOT_STARTED

    def __post_init__(self):
        """Validate gap data."""
        if not self.control_id:
            raise ValueError("control_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not (1 <= self.priority <= 5):
            raise ValueError("priority must be between 1 and 5")


@dataclass
class RemediationAction:
    """
    Action to remediate a compliance gap.
    """

    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gap_id: str = ""
    title: str = ""
    description: str = ""
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: RemediationStatus = RemediationStatus.NOT_STARTED
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    blockers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other action IDs
    completion_percentage: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate remediation action data."""
        if not self.gap_id:
            raise ValueError("gap_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not (0 <= self.completion_percentage <= 100):
            raise ValueError("completion_percentage must be between 0 and 100")

    def is_overdue(self) -> bool:
        """Check if action is overdue."""
        if self.due_date is None or self.status == RemediationStatus.COMPLETED:
            return False
        return datetime.utcnow() > self.due_date


@dataclass
class RemediationPlan:
    """
    Complete remediation plan for compliance gaps.
    """

    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    regulation_type: RegulationType = RegulationType.ISO_27001
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    gaps: List[Gap] = field(default_factory=list)
    actions: List[RemediationAction] = field(default_factory=list)
    target_completion_date: Optional[datetime] = None
    status: str = "draft"  # draft, approved, in_progress, completed
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate remediation plan data."""
        if not self.created_by:
            raise ValueError("created_by is required")

    def get_critical_gaps(self) -> List[Gap]:
        """Get critical severity gaps."""
        return [g for g in self.gaps if g.severity == ViolationSeverity.CRITICAL]

    def get_overdue_actions(self) -> List[RemediationAction]:
        """Get overdue remediation actions."""
        return [a for a in self.actions if a.is_overdue()]

    def get_completion_percentage(self) -> float:
        """Calculate overall plan completion percentage."""
        if not self.actions:
            return 0.0
        completed = sum(1 for a in self.actions if a.status == RemediationStatus.COMPLETED)
        return (completed / len(self.actions)) * 100


@dataclass
class GapAnalysisResult:
    """
    Result of gap analysis for a regulation.
    """

    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    regulation_type: RegulationType = RegulationType.ISO_27001
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    analyzed_by: str = "system"
    total_controls: int = 0
    compliant_controls: int = 0
    non_compliant_controls: int = 0
    partially_compliant_controls: int = 0
    gaps: List[Gap] = field(default_factory=list)
    compliance_percentage: float = 0.0
    remediation_plan: Optional[RemediationPlan] = None
    estimated_remediation_hours: int = 0
    next_review_date: Optional[datetime] = None

    def __post_init__(self):
        """Calculate compliance percentage."""
        if self.total_controls > 0:
            self.compliance_percentage = (self.compliant_controls / self.total_controls) * 100

    def get_gaps_by_severity(self, severity: ViolationSeverity) -> List[Gap]:
        """Get gaps filtered by severity."""
        return [g for g in self.gaps if g.severity == severity]

    def is_certification_ready(self, threshold: float = 90.0) -> bool:
        """Check if compliance meets certification threshold."""
        return self.compliance_percentage >= threshold


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class ComplianceConfig:
    """
    Configuration for compliance engine.
    """

    # Scope
    enabled_regulations: List[RegulationType] = field(
        default_factory=lambda: [
            RegulationType.EU_AI_ACT,
            RegulationType.GDPR,
            RegulationType.NIST_AI_RMF,
            RegulationType.ISO_27001,
        ]
    )

    # Automation
    auto_collect_evidence: bool = True
    auto_remediation_enabled: bool = False  # Requires manual approval
    continuous_monitoring: bool = True

    # Scheduling
    daily_compliance_check: bool = True
    check_interval_hours: int = 24
    evidence_expiration_days: int = 90

    # Alerting
    alert_on_violations: bool = True
    alert_critical_violations_immediately: bool = True
    alert_threshold_percentage: float = 80.0  # Alert if compliance drops below

    # Reporting
    generate_weekly_report: bool = True
    generate_monthly_report: bool = True
    compliance_report_recipients: List[str] = field(default_factory=list)

    # Storage
    evidence_storage_path: str = "/data/compliance/evidence"
    report_storage_path: str = "/data/compliance/reports"
    audit_log_path: str = "/data/compliance/audit.log"

    # Thresholds
    certification_ready_threshold: float = 95.0  # 95% compliance required
    acceptable_compliance_threshold: float = 80.0

    # Integration
    siem_integration_enabled: bool = True
    ticketing_system_integration: bool = False

    def __post_init__(self):
        """Validate configuration."""
        if not self.enabled_regulations:
            raise ValueError("At least one regulation must be enabled")
        if not (0 <= self.alert_threshold_percentage <= 100):
            raise ValueError("alert_threshold_percentage must be between 0 and 100")
        if not (0 <= self.certification_ready_threshold <= 100):
            raise ValueError("certification_ready_threshold must be between 0 and 100")
        if self.check_interval_hours <= 0:
            raise ValueError("check_interval_hours must be positive")

    def is_regulation_enabled(self, regulation_type: RegulationType) -> bool:
        """Check if regulation is enabled."""
        return regulation_type in self.enabled_regulations
