"""
HITL Message Models - RabbitMQ message payloads for Human-in-the-Loop.

These models define the structure of messages published to and consumed from
the HITL notification and decision queues.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HITLNotificationMessage(BaseModel):
    """
    Message published to HITL console when new APV needs review.

    Published after wargaming completes, notifying human reviewers
    that an APV is ready for decision.
    """

    # Message metadata
    message_id: str
    message_type: str = "hitl_notification"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # APV identification
    apv_id: str
    apv_code: str
    priority: int = Field(ge=1, le=10)

    # CVE information
    cve_id: str
    cve_title: str
    severity: str  # "critical", "high", "medium", "low"
    cvss_score: Optional[float] = None

    # Dependency information
    package_name: str
    package_version: str
    package_ecosystem: str

    # Patch information
    patch_strategy: str
    patch_description: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None

    # Confirmation scores
    confirmation_confidence: float = Field(ge=0.0, le=1.0)
    false_positive_probability: float = Field(ge=0.0, le=1.0)

    # Wargaming results
    wargame_verdict: str  # "success", "failure", "inconclusive"
    wargame_confidence: float = Field(ge=0.0, le=1.0)
    wargame_run_url: Optional[str] = None
    wargame_evidence: Optional[Dict[str, Any]] = None

    # Context for review
    affected_files: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

    # Urgency indicators
    requires_immediate_attention: bool = False
    escalation_reason: Optional[str] = None


class HITLDecisionMessage(BaseModel):
    """
    Message published after human makes decision on APV.

    Consumed by system to execute the decision (merge PR, close PR, etc).
    """

    # Message metadata
    message_id: str
    message_type: str = "hitl_decision"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # APV identification
    apv_id: str
    apv_code: str

    # Decision
    decision: str  # "approve", "reject", "modify", "escalate"
    justification: str = Field(min_length=10)
    confidence: float = Field(ge=0.0, le=1.0)

    # Modifications (if decision="modify")
    modifications: Optional[Dict[str, Any]] = None

    # Reviewer information
    reviewer_name: str
    reviewer_email: str
    decision_id: str

    # Context snapshot
    cve_id: str
    severity: str
    patch_strategy: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None

    # Action to execute
    action_type: str  # "merge_pr", "close_pr", "request_changes", "escalate_to_lead"
    action_target_pr: Optional[int] = None
    action_comment: Optional[str] = None
    action_assignees: Optional[List[str]] = None
    action_labels: Optional[List[str]] = None

    # Execution tracking
    requires_followup: bool = False
    followup_reason: Optional[str] = None


class HITLStatusUpdate(BaseModel):
    """
    Status update message about HITL system health.

    Published periodically to monitor HITL console and reviewer activity.
    """

    # Message metadata
    message_id: str
    message_type: str = "hitl_status"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Queue status
    pending_reviews_count: int
    reviews_completed_today: int
    average_review_time_seconds: float

    # Reviewer activity
    active_reviewers: int
    decisions_last_hour: int

    # System health
    console_healthy: bool
    database_healthy: bool
    websocket_connections: int

    # Alerts
    critical_reviews_overdue: int = 0
    high_priority_reviews_waiting: int = 0
    alert_level: str = "normal"  # "normal", "warning", "critical"
    alert_message: Optional[str] = None
