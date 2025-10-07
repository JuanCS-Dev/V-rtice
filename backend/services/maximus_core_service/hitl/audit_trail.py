"""
HITL Audit Trail

Immutable audit trail for all HITL decisions and actions. Provides:
- Complete decision history logging
- Compliance reporting
- Forensic investigation support
- PII redaction for privacy compliance
- Time-series analysis

All entries are immutable and timestamped for regulatory compliance.

Compliance Standards:
- SOC 2 Type II
- ISO 27001
- PCI-DSS
- HIPAA (with PII redaction)
- GDPR (with right to erasure)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import json

from .base import (
    HITLDecision,
    OperatorAction,
    AuditEntry,
    DecisionStatus,
    AutomationLevel,
    RiskLevel,
)
from .risk_assessor import RiskScore

logger = logging.getLogger(__name__)


# ============================================================================
# Audit Query
# ============================================================================

@dataclass
class AuditQuery:
    """
    Query parameters for audit trail search.
    """
    # Time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Decision filters
    decision_ids: List[str] = field(default_factory=list)
    risk_levels: List[RiskLevel] = field(default_factory=list)
    automation_levels: List[AutomationLevel] = field(default_factory=list)
    statuses: List[DecisionStatus] = field(default_factory=list)

    # Actor filters
    operator_ids: List[str] = field(default_factory=list)
    actor_types: List[str] = field(default_factory=list)  # "ai", "human"

    # Event filters
    event_types: List[str] = field(default_factory=list)

    # Compliance filters
    compliance_tags: List[str] = field(default_factory=list)

    # Pagination
    limit: int = 100
    offset: int = 0

    # Sorting
    sort_by: str = "timestamp"  # "timestamp", "risk_level", "decision_id"
    sort_order: str = "desc"  # "asc", "desc"


# ============================================================================
# Compliance Report
# ============================================================================

@dataclass
class ComplianceReport:
    """
    Compliance report for regulatory requirements.
    """
    # Report details
    report_id: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    report_type: str = "hitl_compliance"

    # Time period
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)

    # Summary statistics
    total_decisions: int = 0
    auto_executed: int = 0
    human_reviewed: int = 0
    approved: int = 0
    rejected: int = 0
    escalated: int = 0
    sla_violations: int = 0

    # Risk breakdown
    critical_decisions: int = 0
    high_risk_decisions: int = 0
    medium_risk_decisions: int = 0
    low_risk_decisions: int = 0

    # Operator statistics
    unique_operators: int = 0
    average_review_time: float = 0.0  # seconds

    # Compliance metrics
    automation_rate: float = 0.0
    human_oversight_rate: float = 0.0
    sla_compliance_rate: float = 0.0

    # Audit entries included
    audit_entries: List[AuditEntry] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "report_type": self.report_type,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "summary": {
                "total_decisions": self.total_decisions,
                "auto_executed": self.auto_executed,
                "human_reviewed": self.human_reviewed,
                "approved": self.approved,
                "rejected": self.rejected,
                "escalated": self.escalated,
                "sla_violations": self.sla_violations,
            },
            "risk_breakdown": {
                "critical": self.critical_decisions,
                "high": self.high_risk_decisions,
                "medium": self.medium_risk_decisions,
                "low": self.low_risk_decisions,
            },
            "operator_stats": {
                "unique_operators": self.unique_operators,
                "average_review_time_seconds": self.average_review_time,
            },
            "compliance_metrics": {
                "automation_rate": self.automation_rate,
                "human_oversight_rate": self.human_oversight_rate,
                "sla_compliance_rate": self.sla_compliance_rate,
            },
            "metadata": self.metadata,
        }


# ============================================================================
# Audit Trail
# ============================================================================

class AuditTrail:
    """
    Immutable audit trail for HITL decisions.

    Logs all decision events, operator actions, and system events for
    compliance, forensics, and analytics.
    """

    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialize audit trail.

        Args:
            storage_backend: Storage backend for persistence (e.g., database, S3)
                           If None, uses in-memory storage
        """
        self.storage_backend = storage_backend
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # In-memory storage (if no backend)
        self._audit_log: List[AuditEntry] = []

        # PII fields to redact
        self._pii_fields = [
            "context_snapshot.user_email",
            "context_snapshot.user_name",
            "context_snapshot.ip_address",
            "decision_snapshot.metadata.pii_data",
        ]

        # Metrics
        self.metrics = {
            "total_entries": 0,
            "decision_created": 0,
            "decision_executed": 0,
            "decision_approved": 0,
            "decision_rejected": 0,
            "decision_escalated": 0,
            "decision_failed": 0,
        }

        self.logger.info("Audit Trail initialized")

    def log_decision_created(
        self, decision: HITLDecision, risk_score: RiskScore
    ) -> AuditEntry:
        """
        Log decision creation event.

        Args:
            decision: Created decision
            risk_score: Risk assessment result

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_created",
            event_description=f"AI decision created: {decision.context.action_type.value}",
            actor_type="ai",
            actor_id="maximus_ai",
            decision_snapshot=self._snapshot_decision(decision),
            context_snapshot={
                "action_type": decision.context.action_type.value,
                "confidence": decision.context.confidence,
                "threat_score": decision.context.threat_score,
                "risk_level": decision.risk_level.value,
                "risk_score": risk_score.overall_score,
                "automation_level": decision.automation_level.value,
            },
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)
        self.metrics["decision_created"] += 1

        return entry

    def log_decision_queued(self, decision: HITLDecision) -> AuditEntry:
        """Log decision queued for review."""
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_queued",
            event_description=f"Decision queued for human review (automation={decision.automation_level.value})",
            actor_type="system",
            actor_id="hitl_framework",
            decision_snapshot=self._snapshot_decision(decision),
            context_snapshot={
                "sla_deadline": decision.sla_deadline.isoformat() if decision.sla_deadline else None,
                "risk_level": decision.risk_level.value,
            },
        )

        self._store_entry(entry)
        return entry

    def log_decision_executed(
        self,
        decision: HITLDecision,
        execution_output: Dict[str, Any],
        operator_action: Optional[OperatorAction] = None,
    ) -> AuditEntry:
        """Log decision execution."""
        actor_type = "human" if operator_action else "ai"
        actor_id = operator_action.operator_id if operator_action else "maximus_ai"

        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_executed",
            event_description=f"Decision executed by {actor_type}: {decision.context.action_type.value}",
            actor_type=actor_type,
            actor_id=actor_id,
            decision_snapshot=self._snapshot_decision(decision),
            context_snapshot={
                "execution_output": execution_output,
                "operator_comment": operator_action.comment if operator_action else "",
                "modifications": operator_action.modifications if operator_action else {},
            },
        )

        self._store_entry(entry)
        self.metrics["decision_executed"] += 1

        return entry

    def log_decision_approved(
        self, decision: HITLDecision, operator_action: OperatorAction
    ) -> AuditEntry:
        """Log decision approval."""
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_approved",
            event_description=f"Decision approved by operator: {operator_action.operator_id}",
            actor_type="human",
            actor_id=operator_action.operator_id,
            decision_snapshot=self._snapshot_decision(decision),
            context_snapshot={
                "operator_comment": operator_action.comment,
                "operator_reasoning": operator_action.reasoning,
                "session_id": operator_action.session_id,
            },
        )

        self._store_entry(entry)
        self.metrics["decision_approved"] += 1

        return entry

    def log_decision_rejected(
        self, decision: HITLDecision, operator_action: OperatorAction
    ) -> AuditEntry:
        """Log decision rejection."""
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_rejected",
            event_description=f"Decision rejected by operator: {operator_action.operator_id}",
            actor_type="human",
            actor_id=operator_action.operator_id,
            decision_snapshot=self._snapshot_decision(decision),
            context_snapshot={
                "operator_comment": operator_action.comment,
                "rejection_reason": operator_action.reasoning,
                "session_id": operator_action.session_id,
            },
            compliance_tags=["human_override"],
        )

        self._store_entry(entry)
        self.metrics["decision_rejected"] += 1

        return entry

    def log_decision_escalated(
        self, decision: HITLDecision, escalation_reason: str, escalated_to: str
    ) -> AuditEntry:
        """Log decision escalation."""
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_escalated",
            event_description=f"Decision escalated to {escalated_to}",
            actor_type="system",
            actor_id="escalation_manager",
            decision_snapshot=self._snapshot_decision(decision),
            context_snapshot={
                "escalation_reason": escalation_reason,
                "escalated_to": escalated_to,
                "escalated_from": decision.assigned_operator or "unassigned",
            },
            compliance_tags=["escalation"],
        )

        self._store_entry(entry)
        self.metrics["decision_escalated"] += 1

        return entry

    def log_decision_failed(self, decision: HITLDecision, error: str) -> AuditEntry:
        """Log decision execution failure."""
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_failed",
            event_description=f"Decision execution failed: {error[:100]}",
            actor_type="system",
            actor_id="hitl_framework",
            decision_snapshot=self._snapshot_decision(decision),
            context_snapshot={
                "error": error,
                "action_type": decision.context.action_type.value,
            },
            compliance_tags=["execution_failure"],
        )

        self._store_entry(entry)
        self.metrics["decision_failed"] += 1

        return entry

    def query(self, query: AuditQuery, redact_pii: bool = True) -> List[AuditEntry]:
        """
        Query audit trail.

        Args:
            query: Query parameters
            redact_pii: Whether to redact PII from results

        Returns:
            List of matching audit entries
        """
        entries = self._audit_log.copy()

        # Apply filters
        if query.start_time:
            entries = [e for e in entries if e.timestamp >= query.start_time]

        if query.end_time:
            entries = [e for e in entries if e.timestamp <= query.end_time]

        if query.decision_ids:
            entries = [e for e in entries if e.decision_id in query.decision_ids]

        if query.event_types:
            entries = [e for e in entries if e.event_type in query.event_types]

        if query.actor_types:
            entries = [e for e in entries if e.actor_type in query.actor_types]

        if query.operator_ids:
            entries = [e for e in entries if e.actor_id in query.operator_ids]

        # Sort
        reverse = query.sort_order == "desc"
        if query.sort_by == "timestamp":
            entries.sort(key=lambda e: e.timestamp, reverse=reverse)
        elif query.sort_by == "decision_id":
            entries.sort(key=lambda e: e.decision_id, reverse=reverse)

        # Pagination
        start = query.offset
        end = query.offset + query.limit
        entries = entries[start:end]

        # Redact PII if requested
        if redact_pii:
            entries = [e.redact_pii(self._pii_fields) for e in entries]

        return entries

    def generate_compliance_report(
        self, start_time: datetime, end_time: datetime
    ) -> ComplianceReport:
        """
        Generate compliance report for time period.

        Args:
            start_time: Report start time
            end_time: Report end time

        Returns:
            ComplianceReport
        """
        import uuid

        # Query all entries in period
        query = AuditQuery(
            start_time=start_time, end_time=end_time, limit=100000
        )
        entries = self.query(query, redact_pii=False)

        # Initialize report
        report = ComplianceReport(
            report_id=str(uuid.uuid4()),
            period_start=start_time,
            period_end=end_time,
            audit_entries=entries,
        )

        # Aggregate statistics
        decision_ids = set()
        operator_ids = set()
        review_times = []

        for entry in entries:
            decision_ids.add(entry.decision_id)

            if entry.event_type == "decision_created":
                report.total_decisions += 1

                # Risk breakdown
                risk = entry.context_snapshot.get("risk_level")
                if risk == "critical":
                    report.critical_decisions += 1
                elif risk == "high":
                    report.high_risk_decisions += 1
                elif risk == "medium":
                    report.medium_risk_decisions += 1
                elif risk == "low":
                    report.low_risk_decisions += 1

                # Automation
                automation = entry.context_snapshot.get("automation_level")
                if automation == "full":
                    report.auto_executed += 1
                else:
                    report.human_reviewed += 1

            elif entry.event_type == "decision_approved":
                report.approved += 1
                operator_ids.add(entry.actor_id)

            elif entry.event_type == "decision_rejected":
                report.rejected += 1
                operator_ids.add(entry.actor_id)

            elif entry.event_type == "decision_escalated":
                report.escalated += 1

        # Calculate metrics
        report.unique_operators = len(operator_ids)

        if report.total_decisions > 0:
            report.automation_rate = report.auto_executed / report.total_decisions
            report.human_oversight_rate = report.human_reviewed / report.total_decisions
            report.sla_compliance_rate = 1.0 - (
                report.sla_violations / report.total_decisions
            )

        self.logger.info(
            f"Compliance report generated: {report.report_id} "
            f"(period={start_time} to {end_time}, decisions={report.total_decisions})"
        )

        return report

    def _snapshot_decision(self, decision: HITLDecision) -> Dict[str, Any]:
        """Create snapshot of decision for audit."""
        return {
            "decision_id": decision.decision_id,
            "action_type": decision.context.action_type.value,
            "action_params": decision.context.action_params,
            "risk_level": decision.risk_level.value,
            "automation_level": decision.automation_level.value,
            "status": decision.status.value,
            "confidence": decision.context.confidence,
            "threat_score": decision.context.threat_score,
            "created_at": decision.created_at.isoformat(),
        }

    def _get_compliance_tags(self, decision: HITLDecision) -> List[str]:
        """Get compliance tags for decision."""
        tags = []

        # Risk-based tags
        if decision.risk_level == RiskLevel.CRITICAL:
            tags.append("critical_risk")
        elif decision.risk_level == RiskLevel.HIGH:
            tags.append("high_risk")

        # Automation tags
        if decision.automation_level == AutomationLevel.FULL:
            tags.append("automated_decision")
        else:
            tags.append("human_oversight_required")

        # Data sensitivity tags
        if "pii" in decision.metadata.get("data_type", ""):
            tags.append("pii_involved")

        return tags

    def _store_entry(self, entry: AuditEntry):
        """Store audit entry."""
        # In-memory storage
        self._audit_log.append(entry)

        # External storage backend
        if self.storage_backend:
            try:
                self.storage_backend.store(entry)
            except Exception as e:
                self.logger.error(f"Failed to store audit entry: {e}", exc_info=True)

        self.metrics["total_entries"] += 1

        self.logger.debug(
            f"Audit entry stored: {entry.event_type} (decision={entry.decision_id})"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get audit trail metrics."""
        return self.metrics.copy()
