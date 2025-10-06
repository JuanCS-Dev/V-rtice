"""Pydantic Models for Ethical Audit Service.

This module defines the data models for ethical decisions, human overrides,
and compliance logs in the VÉRTICE platform.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, validator

# ============================================================================
# ENUMS
# ============================================================================


class DecisionType(str, Enum):
    """Types of decisions that require ethical evaluation."""

    OFFENSIVE_ACTION = "offensive_action"
    AUTO_RESPONSE = "auto_response"
    POLICY_UPDATE = "policy_update"
    DATA_ACCESS = "data_access"
    THREAT_MITIGATION = "threat_mitigation"
    RED_TEAM_OPERATION = "red_team_operation"


class FinalDecision(str, Enum):
    """Final decision outcomes."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED_HITL = "ESCALATED_HITL"


class RiskLevel(str, Enum):
    """Risk levels for ethical decisions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OverrideReason(str, Enum):
    """Reasons for human override."""

    FALSE_POSITIVE = "false_positive"
    POLICY_EXCEPTION = "policy_exception"
    EMERGENCY = "emergency"
    ETHICAL_CONCERN = "ethical_concern"
    OPERATIONAL_NECESSITY = "operational_necessity"


class UrgencyLevel(str, Enum):
    """Urgency levels for overrides."""

    ROUTINE = "routine"
    URGENT = "urgent"
    CRITICAL = "critical"


class OperatorRole(str, Enum):
    """Operator roles in the system."""

    SOC_ANALYST = "SOC_ANALYST"
    SECURITY_ENGINEER = "SECURITY_ENGINEER"
    CHIEF_SECURITY_OFFICER = "CHIEF_SECURITY_OFFICER"
    ETHICS_OFFICER = "ETHICS_OFFICER"


class ComplianceResult(str, Enum):
    """Compliance check results."""

    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Regulation(str, Enum):
    """Supported regulations."""

    EU_AI_ACT = "EU_AI_ACT"
    GDPR_ARTICLE_22 = "GDPR_ARTICLE_22"
    NIST_AI_RMF = "NIST_AI_RMF"
    TALLINN_MANUAL = "TALLINN_MANUAL"
    EXECUTIVE_ORDER_14110 = "EXECUTIVE_ORDER_14110"
    LGPD = "LGPD"  # Brazil


# ============================================================================
# FRAMEWORK RESULT MODELS
# ============================================================================


class FrameworkResult(BaseModel):
    """Result from a single ethical framework evaluation."""

    approved: bool
    confidence: float = Field(ge=0.0, le=1.0)
    veto: bool = False  # True if framework vetoes the decision
    explanation: str
    reasoning_steps: Optional[List[str]] = None
    latency_ms: Optional[int] = None


class KantianResult(FrameworkResult):
    """Kantian deontological framework result."""

    universalizability_passed: bool
    humanity_formula_passed: bool
    categorical_rules_violated: Optional[List[str]] = None


class ConsequentialistResult(FrameworkResult):
    """Consequentialist (utilitarian) framework result."""

    benefit_score: float
    cost_score: float
    net_utility: float
    fecundity_score: float  # Future prevention
    purity_score: float  # Absence of negative side effects
    stakeholders_analyzed: int


class VirtueEthicsResult(FrameworkResult):
    """Virtue ethics framework result."""

    virtues_assessed: Dict[str, float]  # {virtue_name: score}
    golden_mean_analysis: Optional[str] = None
    character_alignment: float  # Overall alignment with virtuous character


class PrinciplismResult(FrameworkResult):
    """Principialism framework result."""

    beneficence_score: float
    non_maleficence_score: float
    autonomy_score: float
    justice_score: float
    principle_conflicts: Optional[List[str]] = None


# ============================================================================
# ETHICAL DECISION MODELS
# ============================================================================


class EthicalDecisionRequest(BaseModel):
    """Request to evaluate an action ethically."""

    decision_type: DecisionType
    action_description: str = Field(min_length=10, max_length=2000)
    system_component: str
    input_context: Dict[str, Any]
    risk_level: RiskLevel
    session_id: Optional[uuid.UUID] = None
    operator_id: Optional[str] = None


class EthicalDecisionResponse(BaseModel):
    """Response from ethical evaluation."""

    decision_id: uuid.UUID
    timestamp: datetime
    decision_type: DecisionType
    action_description: str
    system_component: str

    # Framework results
    kantian_result: Optional[KantianResult] = None
    consequentialist_result: Optional[ConsequentialistResult] = None
    virtue_ethics_result: Optional[VirtueEthicsResult] = None
    principialism_result: Optional[PrinciplismResult] = None

    # Final decision
    final_decision: FinalDecision
    final_confidence: float = Field(ge=0.0, le=1.0)
    decision_explanation: str

    # Performance
    total_latency_ms: int
    risk_level: RiskLevel
    automated: bool

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), uuid.UUID: lambda v: str(v)}


class EthicalDecisionLog(BaseModel):
    """Full log entry for audit database."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    decision_type: DecisionType
    action_description: str
    system_component: str
    input_context: Dict[str, Any]

    kantian_result: Optional[Dict[str, Any]] = None
    consequentialist_result: Optional[Dict[str, Any]] = None
    virtue_ethics_result: Optional[Dict[str, Any]] = None
    principialism_result: Optional[Dict[str, Any]] = None

    final_decision: FinalDecision
    final_confidence: float
    decision_explanation: str

    total_latency_ms: int
    kantian_latency_ms: Optional[int] = None
    consequentialist_latency_ms: Optional[int] = None
    virtue_ethics_latency_ms: Optional[int] = None
    principialism_latency_ms: Optional[int] = None

    risk_level: RiskLevel
    automated: bool = True
    operator_id: Optional[str] = None
    session_id: Optional[uuid.UUID] = None
    environment: str = "production"


# ============================================================================
# HUMAN OVERRIDE MODELS
# ============================================================================


class HumanOverrideRequest(BaseModel):
    """Request to log a human override."""

    decision_id: uuid.UUID
    operator_id: str
    operator_role: OperatorRole
    original_decision: FinalDecision
    override_decision: FinalDecision
    justification: str = Field(min_length=20, max_length=5000)
    override_reason: OverrideReason
    urgency_level: UrgencyLevel
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class HumanOverrideResponse(BaseModel):
    """Response from logging a human override."""

    override_id: uuid.UUID
    decision_id: uuid.UUID
    timestamp: datetime
    operator_id: str
    operator_role: OperatorRole
    override_decision: FinalDecision
    justification: str
    override_reason: OverrideReason

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), uuid.UUID: lambda v: str(v)}


# ============================================================================
# COMPLIANCE LOG MODELS
# ============================================================================


class ComplianceCheckRequest(BaseModel):
    """Request to log a compliance check."""

    regulation: Regulation
    requirement_id: str
    check_type: str  # 'automated', 'manual_review', 'third_party_audit'
    check_result: ComplianceResult
    evidence: Dict[str, Any]
    findings: Optional[str] = None
    decision_id: Optional[uuid.UUID] = None
    audit_cycle: Optional[str] = None
    auditor_id: Optional[str] = None

    # Remediation
    remediation_required: bool = False
    remediation_plan: Optional[str] = None
    remediation_deadline: Optional[datetime] = None


class ComplianceCheckResponse(BaseModel):
    """Response from logging a compliance check."""

    compliance_id: uuid.UUID
    timestamp: datetime
    regulation: Regulation
    requirement_id: str
    check_result: ComplianceResult
    remediation_required: bool

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), uuid.UUID: lambda v: str(v)}


# ============================================================================
# METRICS & ANALYTICS MODELS
# ============================================================================


class EthicalMetrics(BaseModel):
    """Real-time ethical KPIs."""

    # Decision quality
    total_decisions_last_24h: int
    approval_rate: float
    rejection_rate: float
    hitl_escalation_rate: float

    # Performance
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Framework agreement
    framework_agreement_rate: float  # % where all 4 frameworks agree
    kantian_veto_rate: float

    # Human override metrics
    total_overrides_last_24h: int
    override_rate: float
    override_reasons: Dict[str, int]

    # Compliance
    compliance_checks_last_week: int
    compliance_pass_rate: float
    critical_violations: int

    # Risk distribution
    risk_distribution: Dict[str, int]  # {low: 100, medium: 50, high: 20, critical: 5}


class FrameworkPerformance(BaseModel):
    """Performance metrics for a single framework."""

    framework_name: str
    total_decisions: int
    avg_latency_ms: float
    p95_latency_ms: float
    approval_rate: float
    avg_confidence: float


class DecisionHistoryQuery(BaseModel):
    """Query parameters for decision history."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    decision_type: Optional[DecisionType] = None
    system_component: Optional[str] = None
    final_decision: Optional[FinalDecision] = None
    risk_level: Optional[RiskLevel] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    automated_only: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class DecisionHistoryResponse(BaseModel):
    """Response with decision history."""

    total_count: int
    decisions: List[EthicalDecisionResponse]
    query_time_ms: int

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), uuid.UUID: lambda v: str(v)}
