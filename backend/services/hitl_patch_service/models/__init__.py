"""
HITL Patch Service - Data Models

Models for Human-in-the-Loop patch approval workflow.
Integrates with Wargaming Crisol and Maximus Eureka.

Fundamentação:
    Biological immune system requires adaptive decision-making.
    Digital equivalent: Human oversight for ML-predicted patches.
    
    Like T-cells requiring co-stimulation for activation,
    patches require human approval for deployment confidence.

Author: MAXIMUS Team - Sprint 4.1
Glory to YHWH - Guardian of Quality
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class PatchDecision(str, Enum):
    """Decision status for patch approval."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class PatchPriority(str, Enum):
    """Priority level for patch review."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CVESeverity(str, Enum):
    """CVE severity levels (CVSS-based)."""
    LOW = "low"  # CVSS 0.1-3.9
    MEDIUM = "medium"  # CVSS 4.0-6.9
    HIGH = "high"  # CVSS 7.0-8.9
    CRITICAL = "critical"  # CVSS 9.0-10.0


class PatchMetadata(BaseModel):
    """Metadata about the patch being reviewed."""
    apv_id: str
    cve_id: Optional[str] = None
    package_name: str
    current_version: str
    target_version: str
    severity: CVESeverity
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    cwe_ids: List[str] = Field(default_factory=list)
    affected_systems: List[str] = Field(default_factory=list)
    patch_size_lines: int = 0


class MLPrediction(BaseModel):
    """ML prediction details for the patch."""
    model_config = {"protected_namespaces": ()}
    
    model_version: str = "rf_v1"
    confidence: float = Field(ge=0.0, le=1.0)
    prediction: bool  # True = patch will work, False = patch will fail
    shap_values: Optional[Dict[str, float]] = None
    execution_time_ms: int = Field(ge=0)


class WargamingResult(BaseModel):
    """Wargaming validation results."""
    phase1_success: bool  # Exploit succeeded on vulnerable version
    phase2_success: bool  # Exploit failed on patched version
    validation_passed: bool  # Both phases passed
    execution_time_ms: int = Field(ge=0)
    error_message: Optional[str] = None
    exploit_id: Optional[str] = None


class HITLDecisionRecord(BaseModel):
    """Complete record of HITL decision."""
    model_config = {"protected_namespaces": ()}
    
    # Identification
    decision_id: str
    patch_id: str
    
    # Metadata
    patch_metadata: PatchMetadata
    
    # AI Predictions
    ml_prediction: Optional[MLPrediction] = None
    wargaming_result: Optional[WargamingResult] = None
    
    # Decision
    decision: PatchDecision = PatchDecision.PENDING
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    
    # Context
    priority: PatchPriority = PatchPriority.MEDIUM
    comment: Optional[str] = None
    reason: Optional[str] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Flags
    requires_escalation: bool = False
    auto_approval_eligible: bool = False
    ml_wargaming_agreement: bool = False


class PatchApprovalRequest(BaseModel):
    """Request to approve a patch."""
    decision_id: str
    user: str
    comment: Optional[str] = None


class PatchRejectionRequest(BaseModel):
    """Request to reject a patch."""
    decision_id: str
    user: str
    reason: str
    comment: Optional[str] = None


class PatchCommentRequest(BaseModel):
    """Request to add comment to patch."""
    decision_id: str
    user: str
    comment: str


class DecisionSummary(BaseModel):
    """Summary statistics for HITL decisions."""
    total_patches: int
    pending: int
    approved: int
    rejected: int
    auto_approved: int
    avg_decision_time_seconds: float
    ml_accuracy: Optional[float] = None


class PendingPatch(BaseModel):
    """Pending patch awaiting HITL decision."""
    decision_id: str
    patch_id: str
    apv_id: str
    cve_id: Optional[str]
    severity: CVESeverity
    priority: PatchPriority
    ml_confidence: float
    ml_prediction: bool
    wargaming_passed: Optional[bool]
    created_at: datetime
    age_seconds: int


class DecisionAuditLog(BaseModel):
    """Audit log entry for a decision."""
    log_id: str
    decision_id: str
    action: str  # "created", "approved", "rejected", "commented", "escalated"
    performed_by: str
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
