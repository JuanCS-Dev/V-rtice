"""PENELOPE Data Models.

Pydantic models for PENELOPE Christian Autonomous Healing Service.

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class Severity(str, Enum):
    """Severity levels for anomalies and interventions."""

    P0_CRITICAL = "P0"
    P1_HIGH = "P1"
    P2_MEDIUM = "P2"
    P3_LOW = "P3"


class InterventionLevel(int, Enum):
    """Intervention levels per Praotes (Mansidão) principle."""

    OBSERVE = 1  # Just log, no action
    CONFIG = 2  # Adjust parameters only
    PATCH_SURGICAL = 3  # 1-5 lines
    PATCH_MODERATE = 4  # 6-25 lines
    REDESIGN = 5  # > 25 lines (requires human approval)


class InterventionDecision(str, Enum):
    """Sophia Engine decisions."""

    OBSERVE_AND_WAIT = "observe"
    INTERVENE = "intervene"
    HUMAN_CONSULTATION_REQUIRED = "escalate"


class CompetenceLevel(str, Enum):
    """Humility-based competence assessment."""

    AUTONOMOUS = "autonomous"  # Can act independently
    ASSISTED = "assisted"  # Suggest only, wait for approval
    DEFER_TO_HUMAN = "defer"  # Cannot handle, escalate immediately


class ValidationResult(str, Enum):
    """Patch validation results."""

    APPROVED = "approved"
    TOO_INVASIVE = "too_invasive"
    NOT_EASILY_REVERSIBLE = "not_reversible"
    REQUIRES_HUMAN_REVIEW = "needs_review"


# === Request Models ===


class DiagnoseRequest(BaseModel):
    """Request to diagnose an anomaly."""

    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    anomaly_type: str = Field(
        ..., description="Type of anomaly (e.g., latency_spike, error_rate_increase)"
    )
    affected_service: str = Field(..., description="Service experiencing anomaly")
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Relevant metrics"
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context (recent deploys, alerts)"
    )


class GeneratePatchRequest(BaseModel):
    """Request to generate a healing patch."""

    diagnosis_id: str = Field(..., description="Diagnosis ID from diagnose endpoint")
    approved_by_sophia: bool = Field(
        ..., description="Whether Sophia Engine approved intervention"
    )
    human_approval_required: bool = Field(
        default=False, description="Whether human approval is needed"
    )


class ValidatePatchRequest(BaseModel):
    """Request to validate patch in digital twin."""

    patch_id: str = Field(..., description="Patch ID to validate")


class DeployPatchRequest(BaseModel):
    """Request to deploy validated patch."""

    patch_id: str = Field(..., description="Patch ID to deploy")
    force: bool = Field(
        default=False,
        description="Force deploy even if warnings (requires human approval)",
    )


class WisdomQueryRequest(BaseModel):
    """Request to query Wisdom Base for precedents."""

    anomaly_type: str = Field(..., description="Type of anomaly")
    service: str | None = Field(None, description="Filter by service")
    similarity_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Minimum similarity score"
    )


# === Response Models ===


class CausalChainStep(BaseModel):
    """Single step in causal chain analysis."""

    step: int
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class Precedent(BaseModel):
    """Historical precedent from Wisdom Base."""

    case_id: str
    similarity: float = Field(..., ge=0.0, le=1.0)
    outcome: str  # "success" or "failure"
    patch_applied: str
    lessons_learned: str | None = None


class DiagnosisResponse(BaseModel):
    """Response from diagnosis endpoint."""

    diagnosis_id: str
    root_cause: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    causal_chain: list[CausalChainStep]
    sophia_recommendation: InterventionDecision
    intervention_level: InterventionLevel
    precedents: list[Precedent] = Field(default_factory=list)


class PatchMetrics(BaseModel):
    """Metrics about a generated patch."""

    lines_changed: int
    functions_modified: int
    api_contracts_broken: int
    reversibility_score: float = Field(..., ge=0.0, le=1.0)
    mansidao_score: float = Field(
        ..., ge=0.0, le=1.0, description="Praotes compliance score"
    )


class PatchResponse(BaseModel):
    """Response from patch generation endpoint."""

    patch_id: str
    status: str
    patch_size_lines: int
    mansidao_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    affected_files: list[str]
    diff: str
    validation_plan: dict[str, Any]
    humility_assessment: str | None = None  # If confidence < threshold


class ValidationTestResult(BaseModel):
    """Result of a single validation test."""

    test_name: str
    passed: bool
    duration_ms: float
    error: str | None = None


class ValidationResponse(BaseModel):
    """Response from patch validation endpoint."""

    patch_id: str
    validation_status: str  # "passed", "failed", "warnings"
    tests_run: int
    tests_passed: int
    tests_failed: int
    test_results: list[ValidationTestResult] = Field(default_factory=list)
    performance_impact: dict[str, Any] = Field(default_factory=dict)
    side_effects_detected: list[str] = Field(default_factory=list)


class DeploymentResponse(BaseModel):
    """Response from patch deployment endpoint."""

    patch_id: str
    deployment_status: str  # "deployed", "failed", "rolled_back"
    git_commit_sha: str | None = None
    deployed_at: datetime | None = None
    rollback_command: str | None = None
    monitoring_period_minutes: int = 10


class WisdomPrecedent(BaseModel):
    """Precedent from Wisdom Base query."""

    case_id: str
    anomaly_type: str
    patch_applied: str
    outcome: str
    lessons_learned: str
    similarity: float = Field(..., ge=0.0, le=1.0)


class WisdomQueryResponse(BaseModel):
    """Response from Wisdom Base query."""

    precedents: list[WisdomPrecedent]
    total_found: int


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str  # "healthy", "degraded", "unhealthy"
    components: dict[str, str]
    virtues_status: dict[str, str] = Field(
        default_factory=lambda: {
            "sophia": "ok",
            "praotes": "ok",
            "tapeinophrosyne": "ok",
        }
    )
    sabbath_mode: bool = False


class ServiceInfo(BaseModel):
    """Service information response."""

    service: str = "PENELOPE - Christian Autonomous Healing Service"
    version: str
    status: str
    governance: str = "7_biblical_articles"
    sabbath_mode: bool
    virtues: list[str] = Field(
        default_factory=lambda: [
            "sophia",
            "praotes",
            "tapeinophrosyne",
            "stewardship",
            "agape",
            "sabbath",
            "aletheia",
        ]
    )
    endpoints: dict[str, str] = Field(default_factory=dict)


# === Internal Models ===


class Anomaly(BaseModel):
    """Internal representation of an anomaly."""

    anomaly_id: str
    anomaly_type: str
    service: str
    severity: Severity
    detected_at: datetime
    metrics: dict[str, Any]
    context: dict[str, Any]


class Diagnosis(BaseModel):
    """Internal diagnosis result."""

    diagnosis_id: str
    anomaly: Anomaly
    root_cause: str
    confidence: float
    causal_chain: list[dict[str, Any]]
    domain: str  # "known" or "unknown"
    precedents: list[dict[str, Any]]


class CodePatch(BaseModel):
    """Internal representation of a code patch."""

    patch_id: str
    diagnosis_id: str
    patch_content: str
    diff: str
    affected_files: list[str]
    patch_size_lines: int
    confidence: float
    mansidao_score: float
    humility_notes: str | None = None
    created_at: datetime


class Report(BaseModel):
    """Internal uncertainty report."""

    confidence: float
    risk_assessment: dict[str, Any]
    similar_precedents: list[dict[str, Any]]
    uncertainty_factors: list[str]


# === Validator ===


@validator("confidence", pre=True, always=True)
def validate_confidence(cls, v):
    """Ensure confidence is between 0.0 and 1.0."""
    if not 0.0 <= v <= 1.0:
        raise ValueError("Confidence must be between 0.0 and 1.0")
    return v
