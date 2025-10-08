"""
HITL Operator Interface

Interface for SOC operators to review and act on AI decisions. Provides:
- Decision review dashboard
- Approval/rejection workflows
- Decision modification
- Escalation requests
- Session management
- Operator metrics

Operator Actions:
- APPROVE: Accept AI recommendation and execute
- REJECT: Veto AI recommendation (with reasoning)
- MODIFY: Change parameters before executing
- ESCALATE: Request higher authority review

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .base import (
    HITLDecision,
    OperatorAction,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Operator Session
# ============================================================================


@dataclass
class OperatorSession:
    """
    Active operator session for decision review.
    """

    # Session details
    session_id: str
    operator_id: str
    operator_name: str
    operator_role: str  # "soc_operator", "soc_supervisor", etc.

    # Session timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    # Session metrics
    decisions_reviewed: int = 0
    decisions_approved: int = 0
    decisions_rejected: int = 0
    decisions_escalated: int = 0
    decisions_modified: int = 0

    # Current work
    active_decision_ids: list[str] = field(default_factory=list)

    # Session metadata
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get_session_duration(self) -> timedelta:
        """Get session duration."""
        return datetime.utcnow() - self.started_at

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def get_approval_rate(self) -> float:
        """Get approval rate (0.0 to 1.0)."""
        if self.decisions_reviewed == 0:
            return 0.0
        return self.decisions_approved / self.decisions_reviewed

    def get_rejection_rate(self) -> float:
        """Get rejection rate (0.0 to 1.0)."""
        if self.decisions_reviewed == 0:
            return 0.0
        return self.decisions_rejected / self.decisions_reviewed


# ============================================================================
# Operator Metrics
# ============================================================================


@dataclass
class OperatorMetrics:
    """
    Aggregate metrics for an operator.
    """

    operator_id: str

    # Lifetime stats
    total_sessions: int = 0
    total_decisions_reviewed: int = 0
    total_approved: int = 0
    total_rejected: int = 0
    total_escalated: int = 0
    total_modified: int = 0

    # Timing stats
    average_review_time: float = 0.0  # seconds
    total_session_time: float = 0.0  # seconds

    # Quality metrics
    approval_rate: float = 0.0
    rejection_rate: float = 0.0
    escalation_rate: float = 0.0

    # Risk handling
    critical_decisions_handled: int = 0
    high_risk_decisions_handled: int = 0

    def update_from_session(self, session: OperatorSession):
        """Update metrics from completed session."""
        self.total_sessions += 1
        self.total_decisions_reviewed += session.decisions_reviewed
        self.total_approved += session.decisions_approved
        self.total_rejected += session.decisions_rejected
        self.total_escalated += session.decisions_escalated
        self.total_modified += session.decisions_modified

        self.total_session_time += session.get_session_duration().total_seconds()

        # Recalculate rates
        if self.total_decisions_reviewed > 0:
            self.approval_rate = self.total_approved / self.total_decisions_reviewed
            self.rejection_rate = self.total_rejected / self.total_decisions_reviewed
            self.escalation_rate = self.total_escalated / self.total_decisions_reviewed


# ============================================================================
# Operator Interface
# ============================================================================


class OperatorInterface:
    """
    Interface for SOC operators to review and act on HITL decisions.

    Provides methods for decision review, approval, rejection, modification,
    and escalation.
    """

    def __init__(
        self,
        decision_framework=None,
        decision_queue=None,
        escalation_manager=None,
        audit_trail=None,
    ):
        """
        Initialize operator interface.

        Args:
            decision_framework: HITLDecisionFramework instance
            decision_queue: DecisionQueue instance
            escalation_manager: EscalationManager instance
            audit_trail: AuditTrail instance
        """
        self.decision_framework = decision_framework
        self.decision_queue = decision_queue
        self.escalation_manager = escalation_manager
        self.audit_trail = audit_trail

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Active sessions
        self._sessions: dict[str, OperatorSession] = {}

        # Operator metrics
        self._operator_metrics: dict[str, OperatorMetrics] = {}

        # Session timeout (default: 8 hours)
        self.session_timeout = timedelta(hours=8)

        self.logger.info("Operator Interface initialized")

    def create_session(
        self,
        operator_id: str,
        operator_name: str,
        operator_role: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> OperatorSession:
        """
        Create new operator session.

        Args:
            operator_id: Unique operator identifier
            operator_name: Operator display name
            operator_role: Operator role (soc_operator, soc_supervisor, etc.)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            OperatorSession
        """
        import uuid

        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + self.session_timeout

        session = OperatorSession(
            session_id=session_id,
            operator_id=operator_id,
            operator_name=operator_name,
            operator_role=operator_role,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._sessions[session_id] = session

        # Initialize metrics if needed
        if operator_id not in self._operator_metrics:
            self._operator_metrics[operator_id] = OperatorMetrics(operator_id=operator_id)

        self.logger.info(f"Session created: {session_id} (operator={operator_id}, role={operator_role})")

        return session

    def get_session(self, session_id: str) -> OperatorSession | None:
        """Get active session by ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            self._close_session(session_id)
            return None
        return session

    def _close_session(self, session_id: str):
        """Close session and update metrics."""
        session = self._sessions.get(session_id)
        if session:
            # Update operator metrics
            metrics = self._operator_metrics.get(session.operator_id)
            if metrics:
                metrics.update_from_session(session)

            # Remove session
            del self._sessions[session_id]

            self.logger.info(
                f"Session closed: {session_id} "
                f"(duration={session.get_session_duration()}, "
                f"decisions_reviewed={session.decisions_reviewed})"
            )

    def get_pending_decisions(
        self,
        session_id: str,
        risk_level: RiskLevel | None = None,
        limit: int = 20,
    ) -> list[HITLDecision]:
        """
        Get pending decisions for operator review.

        Args:
            session_id: Operator session ID
            risk_level: Filter by risk level (None = all)
            limit: Maximum number to return

        Returns:
            List of pending decisions
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        if self.decision_queue is None:
            self.logger.warning("Decision queue not set")
            return []

        # Get decisions from queue
        decisions = self.decision_queue.get_pending_decisions(risk_level=risk_level, operator_id=session.operator_id)

        # Sort by priority (CRITICAL first, then by SLA deadline)
        decisions.sort(
            key=lambda d: (
                4 - list(RiskLevel).index(d.risk_level),  # CRITICAL=4, LOW=1
                d.sla_deadline or datetime.max,
            )
        )

        return decisions[:limit]

    def approve_decision(self, session_id: str, decision_id: str, comment: str = "") -> dict[str, Any]:
        """
        Approve and execute decision.

        Args:
            session_id: Operator session ID
            decision_id: Decision ID to approve
            comment: Optional operator comment

        Returns:
            Result dict with execution details
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        # Get decision
        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        # Create operator action
        operator_action = OperatorAction(
            decision_id=decision_id,
            operator_id=session.operator_id,
            action="approve",
            comment=comment,
            session_id=session_id,
            ip_address=session.ip_address,
        )

        # Execute decision
        if self.decision_framework is None:
            raise RuntimeError("Decision framework not set")

        result = self.decision_framework.execute_decision(decision, operator_action)

        # Update session metrics
        session.decisions_reviewed += 1
        session.decisions_approved += 1

        # Remove from queue
        if self.decision_queue:
            self.decision_queue.remove_decision(decision_id)

        self.logger.info(f"Decision approved: {decision_id} by {session.operator_id} (executed={result.executed})")

        return {
            "decision_id": decision_id,
            "status": "approved",
            "executed": result.executed,
            "result": result.execution_output,
            "error": result.execution_error,
        }

    def reject_decision(self, session_id: str, decision_id: str, reason: str, comment: str = "") -> dict[str, Any]:
        """
        Reject decision (veto AI recommendation).

        Args:
            session_id: Operator session ID
            decision_id: Decision ID to reject
            reason: Rejection reason (required)
            comment: Additional comments

        Returns:
            Result dict
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        # Get decision
        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        # Create operator action
        operator_action = OperatorAction(
            decision_id=decision_id,
            operator_id=session.operator_id,
            action="reject",
            comment=comment,
            reasoning=reason,
            session_id=session_id,
            ip_address=session.ip_address,
        )

        # Reject decision
        if self.decision_framework is None:
            raise RuntimeError("Decision framework not set")

        self.decision_framework.reject_decision(decision, operator_action)

        # Track rejection count (for escalation)
        rejection_count = decision.metadata.get("rejection_count", 0) + 1
        decision.metadata["rejection_count"] = rejection_count

        # Update session metrics
        session.decisions_reviewed += 1
        session.decisions_rejected += 1

        # Remove from queue
        if self.decision_queue:
            self.decision_queue.remove_decision(decision_id)

        self.logger.info(f"Decision rejected: {decision_id} by {session.operator_id} (reason={reason})")

        return {
            "decision_id": decision_id,
            "status": "rejected",
            "reason": reason,
        }

    def modify_and_approve(
        self,
        session_id: str,
        decision_id: str,
        modifications: dict[str, Any],
        comment: str = "",
    ) -> dict[str, Any]:
        """
        Modify decision parameters and execute.

        Args:
            session_id: Operator session ID
            decision_id: Decision ID
            modifications: Parameter modifications
            comment: Operator comment

        Returns:
            Result dict with execution details
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        # Get decision
        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        # Create operator action with modifications
        operator_action = OperatorAction(
            decision_id=decision_id,
            operator_id=session.operator_id,
            action="modify",
            comment=comment,
            modifications=modifications,
            session_id=session_id,
            ip_address=session.ip_address,
        )

        # Execute with modifications
        if self.decision_framework is None:
            raise RuntimeError("Decision framework not set")

        result = self.decision_framework.execute_decision(decision, operator_action)

        # Update session metrics
        session.decisions_reviewed += 1
        session.decisions_approved += 1
        session.decisions_modified += 1

        # Remove from queue
        if self.decision_queue:
            self.decision_queue.remove_decision(decision_id)

        self.logger.info(
            f"Decision modified and approved: {decision_id} by {session.operator_id} (modifications={modifications})"
        )

        return {
            "decision_id": decision_id,
            "status": "modified_and_approved",
            "modifications": modifications,
            "executed": result.executed,
            "result": result.execution_output,
            "error": result.execution_error,
        }

    def escalate_decision(self, session_id: str, decision_id: str, reason: str, comment: str = "") -> dict[str, Any]:
        """
        Escalate decision to higher authority.

        Args:
            session_id: Operator session ID
            decision_id: Decision ID to escalate
            reason: Escalation reason
            comment: Additional comments

        Returns:
            Result dict with escalation details
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        # Get decision
        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        # Determine escalation target
        if self.escalation_manager is None:
            raise RuntimeError("Escalation manager not set")

        escalation_target = self.escalation_manager.get_escalation_target(session.operator_role, decision)

        # Escalate
        from .escalation_manager import EscalationType

        escalation_event = self.escalation_manager.escalate_decision(
            decision=decision,
            escalation_type=EscalationType.OPERATOR_REQUEST,
            reason=reason,
            target_role=escalation_target,
        )

        # Update session metrics
        session.decisions_reviewed += 1
        session.decisions_escalated += 1

        self.logger.info(f"Decision escalated: {decision_id} by {session.operator_id} → {escalation_target}")

        return {
            "decision_id": decision_id,
            "status": "escalated",
            "escalated_to": escalation_target,
            "escalation_event_id": escalation_event.event_id,
            "reason": reason,
        }

    def get_operator_metrics(self, operator_id: str) -> OperatorMetrics | None:
        """Get metrics for operator."""
        return self._operator_metrics.get(operator_id)

    def get_session_metrics(self, session_id: str) -> dict[str, Any] | None:
        """Get metrics for active session."""
        session = self.get_session(session_id)
        if session is None:
            return None

        return {
            "session_id": session.session_id,
            "operator_id": session.operator_id,
            "operator_name": session.operator_name,
            "operator_role": session.operator_role,
            "session_duration": session.get_session_duration().total_seconds(),
            "decisions_reviewed": session.decisions_reviewed,
            "decisions_approved": session.decisions_approved,
            "decisions_rejected": session.decisions_rejected,
            "decisions_escalated": session.decisions_escalated,
            "decisions_modified": session.decisions_modified,
            "approval_rate": session.get_approval_rate(),
            "rejection_rate": session.get_rejection_rate(),
        }

    def _get_decision(self, decision_id: str) -> HITLDecision | None:
        """Get decision from queue."""
        if self.decision_queue is None:
            return None

        queued = self.decision_queue.get_decision(decision_id)
        if queued:
            return queued.decision
        return None
