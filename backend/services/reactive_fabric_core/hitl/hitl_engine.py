"""
Human-In-The-Loop (HITL) Engine for Reactive Fabric.

Manages alerts, decision requests, and human oversight interfaces.
Phase 1: PASSIVE operation - collects decisions but doesn't execute automated responses.
"""

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field


class AlertStatus(str, Enum):
    """Alert status states."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class AlertPriority(str, Enum):
    """Alert priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DecisionType(str, Enum):
    """Types of decisions that can be requested."""

    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    QUARANTINE_FILE = "quarantine_file"
    TERMINATE_PROCESS = "terminate_process"
    REVOKE_ACCESS = "revoke_access"
    ESCALATE = "escalate"
    INVESTIGATE = "investigate"
    DISMISS = "dismiss"


class ApprovalStatus(str, Enum):
    """Approval status for decisions."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"  # Phase 2: When automated responses are enabled


class Alert(BaseModel):
    """Alert model."""

    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    source: str
    priority: AlertPriority
    status: AlertStatus = AlertStatus.PENDING
    threat_score: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    mitre_tactics: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    recommended_actions: List[DecisionType] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    notes: List[str] = Field(default_factory=list)
    related_alerts: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    """Decision request model."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_id: str
    decision_type: DecisionType
    target: Dict[str, Any]
    reason: str
    risk_level: str
    automated: bool = False  # Phase 1: Always False
    requires_approval: bool = True
    approval_timeout_minutes: int = 30
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class DecisionResponse(BaseModel):
    """Decision response model."""

    response_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    alert_id: str
    decision_type: DecisionType
    status: ApprovalStatus
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(BaseModel):
    """Audit log entry."""

    log_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    actor: str
    target: Dict[str, Any]
    result: str
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """Workflow state tracking."""

    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_id: str
    current_stage: str
    stages_completed: List[str] = Field(default_factory=list)
    decisions_pending: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HITLConfig(BaseModel):
    """HITL configuration."""

    alert_retention_days: int = 90
    max_pending_alerts: int = 1000
    escalation_threshold: float = 0.8
    auto_escalate_after_minutes: int = 60
    decision_timeout_minutes: int = 30
    require_dual_approval: bool = False
    audit_all_actions: bool = True
    alert_grouping_window_minutes: int = 15
    max_related_alerts: int = 10


class HITLEngine:
    """Human-In-The-Loop engine for managing alerts and decisions."""

    def __init__(self, config: HITLConfig = None):
        """Initialize HITL engine."""
        self.config = config or HITLConfig()
        self.alerts: Dict[str, Alert] = {}
        self.decision_requests: Dict[str, DecisionRequest] = {}
        self.decision_responses: Dict[str, DecisionResponse] = {}
        self.audit_logs: List[AuditLog] = []
        self.workflows: Dict[str, WorkflowState] = {}

        # Tracking
        self.alerts_by_status: Dict[AlertStatus, Set[str]] = defaultdict(set)
        self.alerts_by_priority: Dict[AlertPriority, Set[str]] = defaultdict(set)
        self.pending_decisions: Set[str] = set()

        # Metrics
        self.total_alerts = 0
        self.total_decisions = 0
        self.escalation_count = 0

        # Running state
        self._running = False
        self._cleanup_task = None

    async def create_alert(
        self,
        title: str,
        description: str,
        source: str,
        priority: AlertPriority,
        threat_score: float,
        entities: Dict[str, Any] = None,
        evidence: List[Dict[str, Any]] = None,
        mitre_tactics: List[str] = None,
        mitre_techniques: List[str] = None
    ) -> Alert:
        """Create a new alert."""
        # Check alert limit
        if len(self.alerts) >= self.config.max_pending_alerts:
            # Remove oldest resolved alerts
            await self._cleanup_old_alerts()

        alert = Alert(
            title=title,
            description=description,
            source=source,
            priority=priority,
            threat_score=threat_score,
            entities=entities or {},
            evidence=evidence or [],
            mitre_tactics=mitre_tactics or [],
            mitre_techniques=mitre_techniques or []
        )

        # Determine recommended actions based on threat
        alert.recommended_actions = self._determine_recommended_actions(
            priority, threat_score, entities
        )

        # Check for related alerts
        related = await self._find_related_alerts(alert)
        if related:
            alert.related_alerts = [r.alert_id for r in related[:self.config.max_related_alerts]]

        # Store alert
        self.alerts[alert.alert_id] = alert
        self.alerts_by_status[alert.status].add(alert.alert_id)
        self.alerts_by_priority[alert.priority].add(alert.alert_id)

        self.total_alerts += 1

        # Check if auto-escalation needed
        if threat_score >= self.config.escalation_threshold:
            await self._auto_escalate(alert)

        # Log creation
        await self._audit_log(
            action="alert_created",
            actor="system",
            target={"alert_id": alert.alert_id},
            result="success",
            details={"title": title, "priority": priority.value}
        )

        return alert

    async def acknowledge_alert(
        self,
        alert_id: str,
        assigned_to: str,
        notes: str = None
    ) -> bool:
        """Acknowledge an alert."""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]

        # Update status
        self.alerts_by_status[alert.status].discard(alert_id)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.assigned_to = assigned_to
        self.alerts_by_status[alert.status].add(alert_id)

        if notes:
            alert.notes.append(f"[{assigned_to}] {notes}")

        # Log acknowledgment
        await self._audit_log(
            action="alert_acknowledged",
            actor=assigned_to,
            target={"alert_id": alert_id},
            result="success",
            details={"notes": notes}
        )

        return True

    async def update_alert_status(
        self,
        alert_id: str,
        status: AlertStatus,
        actor: str,
        notes: str = None
    ) -> bool:
        """Update alert status."""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        old_status = alert.status

        # Update status
        self.alerts_by_status[old_status].discard(alert_id)
        alert.status = status
        self.alerts_by_status[status].add(alert_id)

        # Update timestamps
        if status == AlertStatus.RESOLVED:
            alert.resolved_at = datetime.utcnow()

        if notes:
            alert.notes.append(f"[{actor}] {notes}")

        # Log status change
        await self._audit_log(
            action="alert_status_changed",
            actor=actor,
            target={"alert_id": alert_id},
            result="success",
            details={
                "old_status": old_status.value,
                "new_status": status.value,
                "notes": notes
            }
        )

        return True

    async def request_decision(
        self,
        alert_id: str,
        decision_type: DecisionType,
        target: Dict[str, Any],
        reason: str,
        risk_level: str = "medium"
    ) -> DecisionRequest:
        """Request a decision for an alert."""
        if alert_id not in self.alerts:
            raise ValueError(f"Alert {alert_id} not found")

        request = DecisionRequest(
            alert_id=alert_id,
            decision_type=decision_type,
            target=target,
            reason=reason,
            risk_level=risk_level,
            expires_at=datetime.utcnow() + timedelta(
                minutes=self.config.decision_timeout_minutes
            )
        )

        self.decision_requests[request.request_id] = request
        self.pending_decisions.add(request.request_id)
        self.total_decisions += 1

        # Create workflow if needed
        if alert_id not in self.workflows:
            workflow = WorkflowState(
                alert_id=alert_id,
                current_stage="decision_pending"
            )
            self.workflows[alert_id] = workflow

        self.workflows[alert_id].decisions_pending.append(request.request_id)

        # Log request
        await self._audit_log(
            action="decision_requested",
            actor="system",
            target={"request_id": request.request_id, "alert_id": alert_id},
            result="success",
            details={
                "decision_type": decision_type.value,
                "target": target,
                "reason": reason
            }
        )

        return request

    async def approve_decision(
        self,
        request_id: str,
        approver: str,
        notes: str = None
    ) -> DecisionResponse:
        """Approve a decision request."""
        if request_id not in self.decision_requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.decision_requests[request_id]

        # Check if expired
        if request.expires_at and datetime.utcnow() > request.expires_at:
            response = DecisionResponse(
                request_id=request_id,
                alert_id=request.alert_id,
                decision_type=request.decision_type,
                status=ApprovalStatus.EXPIRED
            )
        else:
            response = DecisionResponse(
                request_id=request_id,
                alert_id=request.alert_id,
                decision_type=request.decision_type,
                status=ApprovalStatus.APPROVED,
                approver=approver,
                approved_at=datetime.utcnow()
            )

            # Phase 1: Log but don't execute
            response.execution_result = {
                "phase": "1",
                "action": "logged_only",
                "would_execute": request.decision_type.value,
                "target": request.target
            }

        self.decision_responses[response.response_id] = response
        self.pending_decisions.discard(request_id)

        # Update workflow
        if request.alert_id in self.workflows:
            workflow = self.workflows[request.alert_id]
            workflow.decisions_pending.remove(request_id)
            workflow.stages_completed.append(f"decision_{request.decision_type.value}")
            workflow.updated_at = datetime.utcnow()

        # Add note to alert
        if request.alert_id in self.alerts and notes:
            self.alerts[request.alert_id].notes.append(
                f"[{approver}] Approved: {request.decision_type.value} - {notes}"
            )

        # Log approval
        await self._audit_log(
            action="decision_approved",
            actor=approver,
            target={"request_id": request_id, "alert_id": request.alert_id},
            result="success",
            details={
                "decision_type": request.decision_type.value,
                "notes": notes
            }
        )

        return response

    async def reject_decision(
        self,
        request_id: str,
        rejector: str,
        reason: str
    ) -> DecisionResponse:
        """Reject a decision request."""
        if request_id not in self.decision_requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.decision_requests[request_id]

        response = DecisionResponse(
            request_id=request_id,
            alert_id=request.alert_id,
            decision_type=request.decision_type,
            status=ApprovalStatus.REJECTED,
            approver=rejector,
            rejection_reason=reason
        )

        self.decision_responses[response.response_id] = response
        self.pending_decisions.discard(request_id)

        # Update workflow
        if request.alert_id in self.workflows:
            workflow = self.workflows[request.alert_id]
            workflow.decisions_pending.remove(request_id)
            workflow.updated_at = datetime.utcnow()

        # Add note to alert
        if request.alert_id in self.alerts:
            self.alerts[request.alert_id].notes.append(
                f"[{rejector}] Rejected: {request.decision_type.value} - {reason}"
            )

        # Log rejection
        await self._audit_log(
            action="decision_rejected",
            actor=rejector,
            target={"request_id": request_id, "alert_id": request.alert_id},
            result="success",
            details={
                "decision_type": request.decision_type.value,
                "reason": reason
            }
        )

        return response

    async def get_pending_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get pending alerts."""
        pending_ids = self.alerts_by_status[AlertStatus.PENDING]

        if priority:
            # Filter by priority
            priority_ids = self.alerts_by_priority[priority]
            alert_ids = pending_ids.intersection(priority_ids)
        else:
            alert_ids = pending_ids

        alerts = [self.alerts[aid] for aid in alert_ids if aid in self.alerts]

        # Sort by priority and timestamp
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3,
            AlertPriority.INFO: 4
        }

        alerts.sort(
            key=lambda a: (priority_order[a.priority], a.created_at)
        )

        return alerts[:limit]

    async def get_pending_decisions(self) -> List[DecisionRequest]:
        """Get pending decision requests."""
        requests = []
        expired_requests = []

        # Use list() to create a copy to avoid iterator issues
        for request_id in list(self.pending_decisions):
            if request_id in self.decision_requests:
                request = self.decision_requests[request_id]

                # Check if expired
                if request.expires_at and datetime.utcnow() > request.expires_at:
                    # Mark for later processing
                    expired_requests.append(request_id)
                else:
                    requests.append(request)

        # Process expired requests after iteration
        for request_id in expired_requests:
            self.pending_decisions.discard(request_id)
            request = self.decision_requests[request_id]

            response = DecisionResponse(
                request_id=request_id,
                alert_id=request.alert_id,
                decision_type=request.decision_type,
                status=ApprovalStatus.EXPIRED
            )
            self.decision_responses[response.response_id] = response

        return requests

    async def get_alert_timeline(self, alert_id: str) -> List[Dict[str, Any]]:
        """Get timeline of events for an alert."""
        if alert_id not in self.alerts:
            return []

        timeline = []
        alert = self.alerts[alert_id]

        # Alert creation
        timeline.append({
            "timestamp": alert.created_at,
            "event": "alert_created",
            "details": {
                "title": alert.title,
                "priority": alert.priority.value,
                "threat_score": alert.threat_score
            }
        })

        # Acknowledgment
        if alert.acknowledged_at:
            timeline.append({
                "timestamp": alert.acknowledged_at,
                "event": "alert_acknowledged",
                "details": {"assigned_to": alert.assigned_to}
            })

        # Decision requests
        for request in self.decision_requests.values():
            if request.alert_id == alert_id:
                timeline.append({
                    "timestamp": request.created_at,
                    "event": "decision_requested",
                    "details": {
                        "type": request.decision_type.value,
                        "target": request.target
                    }
                })

        # Decision responses
        for response in self.decision_responses.values():
            if response.alert_id == alert_id:
                timeline.append({
                    "timestamp": response.created_at,
                    "event": f"decision_{response.status.value}",
                    "details": {
                        "type": response.decision_type.value,
                        "approver": response.approver
                    }
                })

        # Resolution
        if alert.resolved_at:
            timeline.append({
                "timestamp": alert.resolved_at,
                "event": "alert_resolved",
                "details": {"status": alert.status.value}
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return timeline

    async def get_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filters."""
        logs = self.audit_logs

        # Apply filters
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]

        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        if actor:
            logs = [log for log in logs if log.actor == actor]

        if action:
            logs = [log for log in logs if log.action == action]

        # Sort by timestamp descending
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[:limit]

    def _determine_recommended_actions(
        self,
        priority: AlertPriority,
        threat_score: float,
        entities: Dict[str, Any]
    ) -> List[DecisionType]:
        """Determine recommended actions based on alert details."""
        actions = []

        # Always recommend investigation
        actions.append(DecisionType.INVESTIGATE)

        # Handle None entities
        if entities is None:
            entities = {}

        # Based on priority and score
        if priority == AlertPriority.CRITICAL or threat_score >= 0.8:
            if "ip" in entities:
                actions.append(DecisionType.BLOCK_IP)
            if "hostname" in entities:
                actions.append(DecisionType.ISOLATE_HOST)
            if "process" in entities:
                actions.append(DecisionType.TERMINATE_PROCESS)
            if "user" in entities:
                actions.append(DecisionType.REVOKE_ACCESS)
            actions.append(DecisionType.ESCALATE)

        elif priority == AlertPriority.HIGH or threat_score >= 0.6:
            if "ip" in entities:
                actions.append(DecisionType.BLOCK_IP)
            if "file_hash" in entities:
                actions.append(DecisionType.QUARANTINE_FILE)

        return actions

    async def _find_related_alerts(self, alert: Alert) -> List[Alert]:
        """Find alerts related to the given alert."""
        related = []

        # Time window for correlation
        window_start = alert.created_at - timedelta(
            minutes=self.config.alert_grouping_window_minutes
        )

        for other_id, other in self.alerts.items():
            if other_id == alert.alert_id:
                continue

            # Check time window
            if other.created_at < window_start:
                continue

            # Check for common entities
            common_entities = set(alert.entities.keys()) & set(other.entities.keys())
            if common_entities:
                # Check if values match
                for key in common_entities:
                    if alert.entities[key] == other.entities[key]:
                        related.append(other)
                        break

            # Check for same source
            elif alert.source == other.source:
                related.append(other)

        return related

    async def _auto_escalate(self, alert: Alert):
        """Auto-escalate high-threat alerts."""
        # Update status
        self.alerts_by_status[alert.status].discard(alert.alert_id)
        alert.status = AlertStatus.ESCALATED
        self.alerts_by_status[alert.status].add(alert.alert_id)

        self.escalation_count += 1

        # Log escalation
        await self._audit_log(
            action="alert_auto_escalated",
            actor="system",
            target={"alert_id": alert.alert_id},
            result="success",
            details={
                "threat_score": alert.threat_score,
                "priority": alert.priority.value
            }
        )

    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts."""
        cutoff = datetime.utcnow() - timedelta(days=self.config.alert_retention_days)

        to_remove = []
        for alert_id, alert in self.alerts.items():
            if alert.status == AlertStatus.RESOLVED and alert.resolved_at:
                if alert.resolved_at < cutoff:
                    to_remove.append(alert_id)

        for alert_id in to_remove:
            alert = self.alerts.pop(alert_id)
            self.alerts_by_status[alert.status].discard(alert_id)
            self.alerts_by_priority[alert.priority].discard(alert_id)

    async def _audit_log(
        self,
        action: str,
        actor: str,
        target: Dict[str, Any],
        result: str,
        details: Dict[str, Any] = None
    ):
        """Create an audit log entry."""
        if not self.config.audit_all_actions:
            return

        log = AuditLog(
            action=action,
            actor=actor,
            target=target,
            result=result,
            details=details or {}
        )

        self.audit_logs.append(log)

        # Limit audit log size
        if len(self.audit_logs) > 10000:
            self.audit_logs = self.audit_logs[-5000:]

    async def start(self):
        """Start HITL engine."""
        self._running = True

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        await self._audit_log(
            action="engine_started",
            actor="system",
            target={},
            result="success",
            details={}
        )

    async def stop(self):
        """Stop HITL engine."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await self._audit_log(
            action="engine_stopped",
            actor="system",
            target={},
            result="success",
            details={
                "total_alerts": self.total_alerts,
                "total_decisions": self.total_decisions
            }
        )

    async def _periodic_cleanup(self):
        """Periodic cleanup of old data."""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self._cleanup_old_alerts()

                # Check for stale pending alerts
                now = datetime.utcnow()
                for alert_id in list(self.alerts_by_status[AlertStatus.PENDING]):
                    if alert_id in self.alerts:
                        alert = self.alerts[alert_id]
                        age_minutes = (now - alert.created_at).total_seconds() / 60

                        if age_minutes > self.config.auto_escalate_after_minutes:
                            await self._auto_escalate(alert)

            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Continue cleanup even on errors

    def get_metrics(self) -> Dict[str, Any]:
        """Get HITL metrics."""
        return {
            "running": self._running,
            "total_alerts": self.total_alerts,
            "active_alerts": len(self.alerts),
            "pending_alerts": len(self.alerts_by_status[AlertStatus.PENDING]),
            "acknowledged_alerts": len(self.alerts_by_status[AlertStatus.ACKNOWLEDGED]),
            "resolved_alerts": len(self.alerts_by_status[AlertStatus.RESOLVED]),
            "escalated_alerts": len(self.alerts_by_status[AlertStatus.ESCALATED]),
            "total_decisions": self.total_decisions,
            "pending_decisions": len(self.pending_decisions),
            "escalation_count": self.escalation_count,
            "audit_logs": len(self.audit_logs),
            "active_workflows": len(self.workflows)
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"HITLEngine(running={self._running}, "
            f"alerts={len(self.alerts)}, "
            f"pending_decisions={len(self.pending_decisions)}, "
            f"audit_logs={len(self.audit_logs)})"
        )