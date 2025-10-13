"""
HITL Models - Pydantic models for Human-in-the-Loop interface.

Models for:
- APV Review requests
- Human decisions
- Review context (CVE, patch, scores, wargame results)
- Decision history
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReviewContext(BaseModel):
    """Complete context for APV review."""

    # APV Information
    apv_id: str
    apv_code: str
    priority: int = Field(ge=1, le=10)
    status: str

    # CVE Information
    cve_id: str
    cve_title: str
    cve_description: str
    cvss_score: Optional[float] = None
    severity: str
    cwe_ids: List[str] = Field(default_factory=list)

    # Dependency Information
    package_name: str
    package_version: str
    package_ecosystem: str
    fixed_version: Optional[str] = None

    # Vulnerability Details
    vulnerable_code_signature: str
    vulnerable_code_type: str
    affected_files: List[str] = Field(default_factory=list)

    # Confirmation Scores
    confirmed: bool
    confirmation_confidence: float = Field(ge=0.0, le=1.0)
    static_confidence: float = Field(ge=0.0, le=1.0)
    dynamic_confidence: float = Field(ge=0.0, le=1.0)
    false_positive_probability: float = Field(ge=0.0, le=1.0)

    # Patch Information
    patch_strategy: str
    patch_description: str
    patch_diff: Optional[str] = None
    patch_confidence: float = Field(ge=0.0, le=1.0)
    patch_risk_level: str

    # Validation Results
    validation_passed: bool
    validation_confidence: float = Field(ge=0.0, le=1.0)
    validation_warnings: List[str] = Field(default_factory=list)

    # PR Information
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    pr_branch: Optional[str] = None

    # Wargaming Results
    wargame_verdict: Optional[str] = None
    wargame_confidence: Optional[float] = None
    wargame_run_url: Optional[str] = None
    wargame_evidence: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime


class DecisionRequest(BaseModel):
    """Human decision on APV."""

    apv_id: str
    decision: str  # "approve", "reject", "modify", "escalate"
    justification: str = Field(min_length=10)  # Require meaningful justification
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    modifications: Optional[Dict[str, Any]] = None  # For "modify" decision
    reviewer_name: str
    reviewer_email: str


class DecisionRecord(BaseModel):
    """Recorded decision in database."""

    decision_id: str
    apv_id: str
    apv_code: str
    decision: str
    justification: str
    confidence: float
    modifications: Optional[Dict[str, Any]] = None

    # Reviewer
    reviewer_name: str
    reviewer_email: str

    # Context snapshot at decision time
    cve_id: str
    severity: str
    patch_strategy: str
    wargame_verdict: Optional[str] = None

    # Outcome
    action_taken: Optional[str] = None  # "pr_merged", "pr_closed", "patch_modified"
    outcome_notes: Optional[str] = None

    # Timestamps
    decided_at: datetime
    action_completed_at: Optional[datetime] = None


class ReviewStats(BaseModel):
    """Statistics for HITL dashboard."""

    # Counts
    pending_reviews: int
    total_decisions: int
    decisions_today: int
    decisions_this_week: int

    # Decision breakdown
    approved_count: int
    rejected_count: int
    modified_count: int
    escalated_count: int

    # Timing metrics
    average_review_time_seconds: float
    median_review_time_seconds: float
    fastest_review_seconds: float
    slowest_review_seconds: float

    # Agreement metrics
    human_ai_agreement_rate: float  # % where human approved AI recommendation
    auto_merge_prevention_rate: float  # % where HITL caught issues

    # Severity breakdown
    critical_pending: int
    high_pending: int
    medium_pending: int
    low_pending: int


class ReviewListItem(BaseModel):
    """Abbreviated APV info for list view."""

    apv_id: str
    apv_code: str
    cve_id: str
    severity: str
    package_name: str
    patch_strategy: str
    wargame_verdict: Optional[str] = None
    confirmation_confidence: float
    created_at: datetime
    waiting_since: float  # Hours waiting for review


class ReviewAction(BaseModel):
    """Action to take after decision."""

    action_type: str  # "merge_pr", "close_pr", "request_changes", "escalate_to_lead"
    target_pr: Optional[int] = None
    comment: Optional[str] = None
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None


class WebSocketMessage(BaseModel):
    """Real-time WebSocket message."""

    event_type: str  # "new_review", "decision_made", "stats_update"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
