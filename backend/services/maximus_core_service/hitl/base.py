"""
HITL Base Classes and Data Structures

This module defines all foundational classes, enums, and configurations for
the Human-in-the-Loop framework.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


# ============================================================================
# Enums
# ============================================================================

class AutomationLevel(Enum):
    """
    Automation level for AI decisions based on confidence and risk.

    Levels:
    - FULL: AI executes autonomously (≥95% confidence, low risk)
    - SUPERVISED: AI proposes, human approves (≥80% confidence)
    - ADVISORY: AI advises, human decides (≥60% confidence)
    - MANUAL: Human only, no AI execution (<60% confidence or high risk)
    """
    FULL = "full"  # Auto-execute, log audit trail
    SUPERVISED = "supervised"  # Require human approval
    ADVISORY = "advisory"  # AI suggests, human chooses
    MANUAL = "manual"  # Human only, no AI autonomy


class RiskLevel(Enum):
    """
    Risk level for security actions.

    Levels determine SLA timers and escalation policies:
    - LOW: 30min SLA, automated escalation
    - MEDIUM: 15min SLA, supervisor escalation
    - HIGH: 10min SLA, manager escalation
    - CRITICAL: 5min SLA, immediate executive escalation
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(Enum):
    """Status of HITL decision in workflow."""
    PENDING = "pending"  # Waiting for operator review
    APPROVED = "approved"  # Operator approved
    REJECTED = "rejected"  # Operator rejected
    EXECUTED = "executed"  # Action executed successfully
    FAILED = "failed"  # Execution failed
    TIMEOUT = "timeout"  # SLA timeout occurred
    ESCALATED = "escalated"  # Escalated to supervisor
    CANCELLED = "cancelled"  # Cancelled by operator


class ActionType(Enum):
    """
    Types of security actions that can be automated.

    Categories:
    - Network: isolate_host, block_ip, block_domain, throttle_connection
    - Endpoint: quarantine_file, kill_process, disable_user, lock_account
    - Data: encrypt_data, backup_data, delete_data, archive_logs
    - Investigation: collect_forensics, capture_memory, snapshot_vm
    - Response: send_alert, create_ticket, notify_team, escalate_incident
    """
    # Network actions
    ISOLATE_HOST = "isolate_host"
    BLOCK_IP = "block_ip"
    BLOCK_DOMAIN = "block_domain"
    BLOCK_PORT = "block_port"
    THROTTLE_CONNECTION = "throttle_connection"
    RESET_CONNECTION = "reset_connection"

    # Endpoint actions
    QUARANTINE_FILE = "quarantine_file"
    DELETE_FILE = "delete_file"
    KILL_PROCESS = "kill_process"
    SUSPEND_PROCESS = "suspend_process"
    DISABLE_USER = "disable_user"
    LOCK_ACCOUNT = "lock_account"
    RESET_PASSWORD = "reset_password"

    # Data actions
    ENCRYPT_DATA = "encrypt_data"
    BACKUP_DATA = "backup_data"
    DELETE_DATA = "delete_data"
    ARCHIVE_LOGS = "archive_logs"
    EXFILTRATE_PREVENTION = "exfiltrate_prevention"

    # Investigation actions
    COLLECT_FORENSICS = "collect_forensics"
    CAPTURE_MEMORY = "capture_memory"
    SNAPSHOT_VM = "snapshot_vm"
    CAPTURE_NETWORK = "capture_network"
    COLLECT_LOGS = "collect_logs"

    # Response actions
    SEND_ALERT = "send_alert"
    CREATE_TICKET = "create_ticket"
    NOTIFY_TEAM = "notify_team"
    ESCALATE_INCIDENT = "escalate_incident"
    UPDATE_THREAT_INTEL = "update_threat_intel"


# ============================================================================
# Configuration Classes
# ============================================================================

@dataclass
class SLAConfig:
    """
    SLA (Service Level Agreement) configuration for decision review.

    Defines timeout periods for different risk levels and escalation policies.
    """
    # SLA timeout by risk level (minutes)
    low_risk_timeout: int = 30
    medium_risk_timeout: int = 15
    high_risk_timeout: int = 10
    critical_risk_timeout: int = 5

    # Warning threshold (% of SLA before warning)
    warning_threshold: float = 0.75  # Warn at 75% of SLA

    # Auto-escalate on timeout
    auto_escalate_on_timeout: bool = True

    # Escalation chain
    escalation_chain: List[str] = field(default_factory=lambda: [
        "soc_operator",
        "soc_supervisor",
        "security_manager",
        "ciso",
    ])

    def get_timeout_minutes(self, risk_level: RiskLevel) -> int:
        """Get SLA timeout for risk level."""
        mapping = {
            RiskLevel.LOW: self.low_risk_timeout,
            RiskLevel.MEDIUM: self.medium_risk_timeout,
            RiskLevel.HIGH: self.high_risk_timeout,
            RiskLevel.CRITICAL: self.critical_risk_timeout,
        }
        return mapping[risk_level]

    def get_timeout_delta(self, risk_level: RiskLevel) -> timedelta:
        """Get SLA timeout as timedelta."""
        return timedelta(minutes=self.get_timeout_minutes(risk_level))

    def get_warning_delta(self, risk_level: RiskLevel) -> timedelta:
        """Get warning threshold as timedelta."""
        total_minutes = self.get_timeout_minutes(risk_level)
        warning_minutes = int(total_minutes * self.warning_threshold)
        return timedelta(minutes=warning_minutes)


@dataclass
class EscalationConfig:
    """Configuration for decision escalation."""
    # Enable escalation
    enabled: bool = True

    # Escalation triggers
    escalate_on_timeout: bool = True
    escalate_on_high_risk: bool = True
    escalate_on_multiple_rejections: bool = True
    rejection_threshold: int = 2  # Escalate after N rejections

    # Escalation targets by risk level
    low_risk_escalation: str = "soc_supervisor"
    medium_risk_escalation: str = "soc_supervisor"
    high_risk_escalation: str = "security_manager"
    critical_risk_escalation: str = "ciso"

    # Notification
    send_email: bool = True
    send_sms: bool = False  # For critical only
    send_slack: bool = True

    def get_escalation_target(self, risk_level: RiskLevel) -> str:
        """Get escalation target for risk level."""
        mapping = {
            RiskLevel.LOW: self.low_risk_escalation,
            RiskLevel.MEDIUM: self.medium_risk_escalation,
            RiskLevel.HIGH: self.high_risk_escalation,
            RiskLevel.CRITICAL: self.critical_risk_escalation,
        }
        return mapping[risk_level]


@dataclass
class HITLConfig:
    """Main HITL framework configuration."""
    # Confidence thresholds for automation levels
    full_automation_threshold: float = 0.95  # ≥95% → FULL
    supervised_threshold: float = 0.80  # ≥80% → SUPERVISED
    advisory_threshold: float = 0.60  # ≥60% → ADVISORY
    # <60% → MANUAL

    # Risk-based overrides (even high confidence may need approval)
    high_risk_requires_approval: bool = True
    critical_risk_requires_approval: bool = True

    # SLA configuration
    sla_config: SLAConfig = field(default_factory=SLAConfig)

    # Escalation configuration
    escalation_config: EscalationConfig = field(default_factory=EscalationConfig)

    # Audit configuration
    audit_all_decisions: bool = True
    redact_pii_in_audit: bool = True
    audit_retention_days: int = 365 * 7  # 7 years for compliance

    # Queue configuration
    max_queue_size: int = 1000
    priority_queue_enabled: bool = True

    # Operator assignment
    auto_assign_operator: bool = True
    round_robin_assignment: bool = True

    def __post_init__(self):
        """Validate configuration."""
        # Validate thresholds
        if not (0.0 <= self.full_automation_threshold <= 1.0):
            raise ValueError("full_automation_threshold must be between 0 and 1")
        if not (0.0 <= self.supervised_threshold <= 1.0):
            raise ValueError("supervised_threshold must be between 0 and 1")
        if not (0.0 <= self.advisory_threshold <= 1.0):
            raise ValueError("advisory_threshold must be between 0 and 1")

        # Validate threshold ordering
        if not (self.advisory_threshold <= self.supervised_threshold <= self.full_automation_threshold):
            raise ValueError(
                "Thresholds must be ordered: advisory <= supervised <= full_automation"
            )

    def get_automation_level(
        self, confidence: float, risk_level: RiskLevel
    ) -> AutomationLevel:
        """
        Determine automation level based on confidence and risk.

        Args:
            confidence: AI confidence score (0.0 to 1.0)
            risk_level: Risk level of the action

        Returns:
            Appropriate automation level
        """
        # Critical/High risk always requires approval
        if risk_level == RiskLevel.CRITICAL and self.critical_risk_requires_approval:
            return AutomationLevel.MANUAL

        if risk_level == RiskLevel.HIGH and self.high_risk_requires_approval:
            return AutomationLevel.SUPERVISED

        # Confidence-based levels
        if confidence >= self.full_automation_threshold:
            return AutomationLevel.FULL
        elif confidence >= self.supervised_threshold:
            return AutomationLevel.SUPERVISED
        elif confidence >= self.advisory_threshold:
            return AutomationLevel.ADVISORY
        else:
            return AutomationLevel.MANUAL


# ============================================================================
# Core Data Classes
# ============================================================================

@dataclass
class DecisionContext:
    """
    Context for a security decision.

    Contains all information needed for human review and audit trail.
    """
    # Action details
    action_type: ActionType
    action_params: Dict[str, Any] = field(default_factory=dict)

    # AI reasoning
    ai_reasoning: str = ""
    confidence: float = 0.0
    model_version: str = ""

    # Threat context
    threat_score: float = 0.0
    threat_type: str = ""
    iocs: List[str] = field(default_factory=list)  # Indicators of Compromise

    # Asset context
    affected_assets: List[str] = field(default_factory=list)
    asset_criticality: str = "medium"  # low, medium, high, critical

    # Business context
    business_impact: str = ""
    estimated_cost: float = 0.0

    # Related incidents
    related_incidents: List[str] = field(default_factory=list)
    similar_past_decisions: List[str] = field(default_factory=list)

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_summary(self) -> str:
        """Get human-readable summary of context."""
        summary_parts = [
            f"Action: {self.action_type.value}",
            f"Confidence: {self.confidence:.1%}",
            f"Threat Score: {self.threat_score:.2f}",
        ]

        if self.affected_assets:
            summary_parts.append(f"Assets: {', '.join(self.affected_assets[:3])}")

        if self.ai_reasoning:
            summary_parts.append(f"Reasoning: {self.ai_reasoning[:100]}...")

        return " | ".join(summary_parts)


@dataclass
class HITLDecision:
    """
    A decision requiring human-in-the-loop review.

    Represents a single security decision made by MAXIMUS AI that may
    require human oversight based on confidence and risk level.
    """
    # Unique identifier
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Decision context
    context: DecisionContext = field(default_factory=DecisionContext)

    # Risk and automation
    risk_level: RiskLevel = RiskLevel.MEDIUM
    automation_level: AutomationLevel = AutomationLevel.SUPERVISED

    # Status tracking
    status: DecisionStatus = DecisionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # SLA tracking
    sla_deadline: Optional[datetime] = None
    sla_warning_sent: bool = False

    # Assignment
    assigned_operator: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Review tracking
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    operator_comment: str = ""

    # Execution tracking
    executed_at: Optional[datetime] = None
    execution_result: Dict[str, Any] = field(default_factory=dict)
    execution_error: Optional[str] = None

    # Escalation tracking
    escalated: bool = False
    escalated_to: Optional[str] = None
    escalated_at: Optional[datetime] = None
    escalation_reason: str = ""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_overdue(self) -> bool:
        """Check if decision is past SLA deadline."""
        if self.sla_deadline is None:
            return False
        return datetime.utcnow() > self.sla_deadline

    def get_time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until SLA deadline."""
        if self.sla_deadline is None:
            return None
        remaining = self.sla_deadline - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def get_age(self) -> timedelta:
        """Get age of decision."""
        return datetime.utcnow() - self.created_at

    def requires_human_review(self) -> bool:
        """Check if decision requires human review."""
        return self.automation_level in [
            AutomationLevel.SUPERVISED,
            AutomationLevel.ADVISORY,
            AutomationLevel.MANUAL,
        ]

    def can_execute_autonomously(self) -> bool:
        """Check if AI can execute without human approval."""
        return self.automation_level == AutomationLevel.FULL


@dataclass
class OperatorAction:
    """
    Action taken by human operator on a decision.
    """
    # Action details
    decision_id: str
    operator_id: str
    action: str  # "approve", "reject", "escalate", "modify"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Justification
    comment: str = ""
    reasoning: str = ""

    # Modifications (if operator changed parameters)
    modifications: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    """
    Immutable audit trail entry for compliance and forensics.
    """
    # Entry identifier
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Decision reference
    decision_id: str = ""

    # Event details
    event_type: str = ""  # "decision_created", "decision_approved", "decision_executed", etc.
    event_description: str = ""

    # Actor (AI or human)
    actor_type: str = "ai"  # "ai" or "human"
    actor_id: str = ""

    # Decision snapshot (for forensics)
    decision_snapshot: Dict[str, Any] = field(default_factory=dict)

    # Context snapshot
    context_snapshot: Dict[str, Any] = field(default_factory=dict)

    # Compliance tags
    compliance_tags: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def redact_pii(self, pii_fields: List[str]) -> "AuditEntry":
        """
        Redact PII from audit entry.

        Args:
            pii_fields: List of field paths to redact (e.g., ["context_snapshot.user_email"])

        Returns:
            Redacted copy of audit entry
        """
        import copy

        redacted = copy.deepcopy(self)

        for field_path in pii_fields:
            parts = field_path.split(".")
            target = redacted

            # Navigate to parent of target field
            for part in parts[:-1]:
                if isinstance(target, dict) and part in target:
                    target = target[part]
                else:
                    break
            else:
                # Redact final field
                if isinstance(target, dict) and parts[-1] in target:
                    target[parts[-1]] = "[REDACTED]"

        return redacted
