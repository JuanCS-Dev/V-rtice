"""
Governance API Routes - FastAPI Endpoints for HITL Operations

Provides REST API and SSE endpoints for Governance Workspace TUI.

Endpoints:
- GET  /governance/stream/{operator_id}          - SSE stream of pending decisions
- GET  /governance/health                        - Health check
- GET  /governance/pending                       - Get pending decisions count
- POST /governance/decision/{id}/approve         - Approve decision
- POST /governance/decision/{id}/reject          - Reject decision
- POST /governance/decision/{id}/escalate        - Escalate decision
- GET  /governance/session/{operator_id}/stats   - Operator metrics
- POST /governance/session/create                - Create operator session

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: Production-ready, REGRA DE OURO compliant
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# HITL imports
from hitl import (
    HITLDecision,
    DecisionQueue,
    OperatorInterface,
    DecisionStatus,
    RiskLevel,
)

# Local imports
from .sse_server import GovernanceSSEServer, SSEEvent
from .event_broadcaster import EventBroadcaster

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Request to create operator session."""
    operator_id: str = Field(..., description="Unique operator identifier")
    operator_name: str = Field(..., description="Operator display name")
    operator_role: str = Field(default="soc_operator", description="Operator role")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")


class SessionCreateResponse(BaseModel):
    """Response from session creation."""
    session_id: str
    operator_id: str
    expires_at: str
    message: str = "Session created successfully"


class DecisionActionRequest(BaseModel):
    """Request to act on a decision."""
    session_id: str = Field(..., description="Active session ID")
    reasoning: Optional[str] = Field(None, description="Reasoning for action")
    comment: Optional[str] = Field(None, description="Additional comments")


class ApproveDecisionRequest(DecisionActionRequest):
    """Request to approve a decision.

    Inherits all fields from DecisionActionRequest:
    - session_id: Operator session identifier
    - comment: Optional approval comments
    """
    ...


class RejectDecisionRequest(DecisionActionRequest):
    """Request to reject a decision."""
    reason: str = Field(..., description="Rejection reason (required)")


class EscalateDecisionRequest(DecisionActionRequest):
    """Request to escalate a decision."""
    escalation_target: Optional[str] = Field(None, description="Target role/person")
    escalation_reason: str = Field(..., description="Why escalation is needed")


class DecisionActionResponse(BaseModel):
    """Response from decision action."""
    decision_id: str
    action: str  # "approved", "rejected", "escalated"
    status: str
    message: str
    executed: Optional[bool] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    active_connections: int
    total_connections: int
    decisions_streamed: int
    queue_size: int
    timestamp: str


class PendingStatsResponse(BaseModel):
    """Pending decisions statistics."""
    total_pending: int
    by_risk_level: Dict[str, int]
    oldest_pending_seconds: Optional[int]
    sla_violations: int


class OperatorStatsResponse(BaseModel):
    """Operator statistics."""
    operator_id: str
    total_sessions: int
    total_decisions_reviewed: int
    total_approved: int
    total_rejected: int
    total_escalated: int
    approval_rate: float
    rejection_rate: float
    escalation_rate: float
    average_review_time: float


# ============================================================================
# API Router Factory
# ============================================================================

def create_governance_api(
    decision_queue: DecisionQueue,
    operator_interface: OperatorInterface,
    sse_server: Optional[GovernanceSSEServer] = None,
    event_broadcaster: Optional[EventBroadcaster] = None,
) -> APIRouter:
    """
    Create FastAPI router for Governance API.

    Args:
        decision_queue: HITL DecisionQueue instance
        operator_interface: HITL OperatorInterface instance
        sse_server: GovernanceSSEServer instance (created if None)
        event_broadcaster: EventBroadcaster instance (created if None)

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/governance", tags=["governance"])

    # Initialize SSE server if not provided
    if sse_server is None:
        sse_server = GovernanceSSEServer(
            decision_queue=decision_queue,
            poll_interval=1.0,
            heartbeat_interval=30,
        )
        logger.info("Created new GovernanceSSEServer instance")

    # Initialize event broadcaster if not provided
    if event_broadcaster is None:
        event_broadcaster = EventBroadcaster(sse_server.connection_manager)
        logger.info("Created new EventBroadcaster instance")

    # ========================================================================
    # SSE Streaming Endpoint
    # ========================================================================

    @router.get("/stream/{operator_id}")
    async def stream_governance_events(
        operator_id: str,
        session_id: str = Query(..., description="Active session ID"),
    ):
        """
        Stream governance events via Server-Sent Events.

        This endpoint provides real-time streaming of pending HITL decisions
        to the operator's TUI.

        Args:
            operator_id: Operator identifier
            session_id: Active session ID

        Returns:
            StreamingResponse with SSE events
        """
        # Validate session
        session = operator_interface.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired session: {session_id}",
            )

        if session.operator_id != operator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator ID does not match session",
            )

        logger.info(f"SSE stream started for operator {operator_id} (session={session_id})")

        async def event_generator():
            """Generate SSE events."""
            try:
                async for sse_event in sse_server.stream_decisions(operator_id, session_id):
                    yield sse_event.to_sse_format()

            except Exception as e:
                logger.error(f"SSE stream error for {operator_id}: {e}", exc_info=True)
                # Send error event
                error_event = SSEEvent(
                    event_type="error",
                    event_id=f"error_{datetime.now(timezone.utc).timestamp()}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    data={"error": str(e), "message": "Stream error occurred"},
                )
                yield error_event.to_sse_format()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    # ========================================================================
    # Health and Stats Endpoints
    # ========================================================================

    @router.get("/health", response_model=HealthResponse)
    async def get_health():
        """
        Get server health status.

        Returns:
            Health metrics
        """
        health = sse_server.get_health()
        return HealthResponse(**health)

    @router.get("/pending", response_model=PendingStatsResponse)
    async def get_pending_stats():
        """
        Get statistics about pending decisions.

        Returns:
            Pending decisions statistics
        """
        pending = decision_queue.get_pending_decisions()

        # Calculate stats
        total = len(pending)
        by_risk = {level.value: 0 for level in RiskLevel}

        oldest_pending_seconds = None
        if pending:
            for decision in pending:
                by_risk[decision.risk_level.value] += 1

            # Find oldest decision
            oldest = min(pending, key=lambda d: d.created_at)
            age = (datetime.now(timezone.utc) - oldest.created_at).total_seconds()
            oldest_pending_seconds = int(age)

        # Count SLA violations
        sla_violations = sum(
            1 for d in pending
            if d.sla_deadline and datetime.now(timezone.utc) > d.sla_deadline
        )

        return PendingStatsResponse(
            total_pending=total,
            by_risk_level=by_risk,
            oldest_pending_seconds=oldest_pending_seconds,
            sla_violations=sla_violations,
        )

    # ========================================================================
    # Session Management
    # ========================================================================

    @router.post("/session/create", response_model=SessionCreateResponse)
    async def create_session(request: SessionCreateRequest):
        """
        Create new operator session.

        Args:
            request: Session creation request

        Returns:
            Session details
        """
        try:
            session = operator_interface.create_session(
                operator_id=request.operator_id,
                operator_name=request.operator_name,
                operator_role=request.operator_role,
                ip_address=request.ip_address,
                user_agent=request.user_agent,
            )

            return SessionCreateResponse(
                session_id=session.session_id,
                operator_id=session.operator_id,
                expires_at=session.expires_at.isoformat() if session.expires_at else "",
            )

        except Exception as e:
            logger.error(f"Session creation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create session: {str(e)}",
            )

    @router.get("/session/{operator_id}/stats", response_model=OperatorStatsResponse)
    async def get_operator_stats(operator_id: str):
        """
        Get operator statistics.

        Args:
            operator_id: Operator identifier

        Returns:
            Operator metrics
        """
        # Get aggregated metrics from closed sessions
        metrics = operator_interface._operator_metrics.get(operator_id)

        # Find active sessions for this operator
        active_sessions = [
            session for session in operator_interface._sessions.values()
            if session.operator_id == operator_id
        ]

        # If no metrics and no active sessions, return zeros
        if metrics is None and not active_sessions:
            return OperatorStatsResponse(
                operator_id=operator_id,
                total_sessions=0,
                total_decisions_reviewed=0,
                total_approved=0,
                total_rejected=0,
                total_escalated=0,
                approval_rate=0.0,
                rejection_rate=0.0,
                escalation_rate=0.0,
                average_review_time=0.0,
            )

        # Aggregate stats from closed sessions + active sessions
        total_sessions = metrics.total_sessions if metrics else 0
        total_sessions += len(active_sessions)  # Add active sessions

        total_reviewed = metrics.total_decisions_reviewed if metrics else 0
        total_approved = metrics.total_approved if metrics else 0
        total_rejected = metrics.total_rejected if metrics else 0
        total_escalated = metrics.total_escalated if metrics else 0

        # Add stats from active sessions
        for session in active_sessions:
            total_reviewed += session.decisions_reviewed
            total_approved += session.decisions_approved
            total_rejected += session.decisions_rejected
            total_escalated += session.decisions_escalated

        # Calculate rates
        approval_rate = total_approved / total_reviewed if total_reviewed > 0 else 0.0
        rejection_rate = total_rejected / total_reviewed if total_reviewed > 0 else 0.0
        escalation_rate = total_escalated / total_reviewed if total_reviewed > 0 else 0.0

        # Average review time (from aggregated metrics only)
        avg_review_time = metrics.average_review_time if metrics else 0.0

        return OperatorStatsResponse(
            operator_id=operator_id,
            total_sessions=total_sessions,
            total_decisions_reviewed=total_reviewed,
            total_approved=total_approved,
            total_rejected=total_rejected,
            total_escalated=total_escalated,
            approval_rate=approval_rate,
            rejection_rate=rejection_rate,
            escalation_rate=escalation_rate,
            average_review_time=avg_review_time,
        )

    # ========================================================================
    # Decision Actions
    # ========================================================================

    @router.post("/decision/{decision_id}/approve", response_model=DecisionActionResponse)
    async def approve_decision(decision_id: str, request: ApproveDecisionRequest):
        """
        Approve a pending decision.

        Args:
            decision_id: Decision ID to approve
            request: Approval request

        Returns:
            Action result
        """
        try:
            result = operator_interface.approve_decision(
                session_id=request.session_id,
                decision_id=decision_id,
                comment=request.comment or "",
            )

            # Notify via SSE
            await sse_server.notify_decision_resolved(
                decision_id=decision_id,
                status=DecisionStatus.APPROVED,
                operator_id=operator_interface.get_session(request.session_id).operator_id,
            )

            return DecisionActionResponse(
                decision_id=decision_id,
                action="approved",
                status=result.get("status", "approved"),
                message=f"Decision {decision_id} approved and executed",
                executed=result.get("executed"),
                result=result.get("result"),
                error=result.get("error"),
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Approve failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Approval failed: {str(e)}",
            )

    @router.post("/decision/{decision_id}/reject", response_model=DecisionActionResponse)
    async def reject_decision(decision_id: str, request: RejectDecisionRequest):
        """
        Reject a pending decision.

        Args:
            decision_id: Decision ID to reject
            request: Rejection request

        Returns:
            Action result
        """
        try:
            result = operator_interface.reject_decision(
                session_id=request.session_id,
                decision_id=decision_id,
                reason=request.reason,
                comment=request.comment or "",
            )

            # Notify via SSE
            await sse_server.notify_decision_resolved(
                decision_id=decision_id,
                status=DecisionStatus.REJECTED,
                operator_id=operator_interface.get_session(request.session_id).operator_id,
            )

            return DecisionActionResponse(
                decision_id=decision_id,
                action="rejected",
                status="rejected",
                message=f"Decision {decision_id} rejected",
                executed=False,
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Reject failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rejection failed: {str(e)}",
            )

    @router.post("/decision/{decision_id}/escalate", response_model=DecisionActionResponse)
    async def escalate_decision(decision_id: str, request: EscalateDecisionRequest):
        """
        Escalate a pending decision to higher authority.

        Args:
            decision_id: Decision ID to escalate
            request: Escalation request

        Returns:
            Action result
        """
        try:
            result = operator_interface.escalate_decision(
                session_id=request.session_id,
                decision_id=decision_id,
                reason=request.escalation_reason,
                comment=request.comment or "",
            )

            # Notify via SSE
            await sse_server.notify_decision_resolved(
                decision_id=decision_id,
                status=DecisionStatus.ESCALATED,
                operator_id=operator_interface.get_session(request.session_id).operator_id,
            )

            return DecisionActionResponse(
                decision_id=decision_id,
                action="escalated",
                status="escalated",
                message=f"Decision {decision_id} escalated",
                executed=False,
                result=result,
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Escalate failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Escalation failed: {str(e)}",
            )

    # ========================================================================
    # Test / Development Endpoints
    # ========================================================================

    @router.post("/test/enqueue")
    async def enqueue_test_decision(decision_dict: Dict):
        """
        Enqueue a test decision (for E2E testing only).

        WARNING: This endpoint is for testing purposes only.
        In production, decisions are enqueued by MAXIMUS internally.

        Args:
            decision_dict: Dictionary with decision data

        Returns:
            Enqueue result
        """
        try:
            # Import required types
            from hitl import DecisionContext, AutomationLevel, ActionType
            from datetime import datetime, timedelta, timezone

            # Parse decision dict into HITLDecision
            context_dict = decision_dict.get("context", {})
            context = DecisionContext(
                action_type=ActionType(context_dict.get("action_type", "block_ip")),
                action_params=context_dict.get("action_params", {}),
                ai_reasoning=context_dict.get("ai_reasoning", ""),
                confidence=context_dict.get("confidence", 0.0),
                threat_score=context_dict.get("threat_score", 0.0),
                threat_type=context_dict.get("threat_type", "unknown"),
                metadata=context_dict.get("metadata", {}),
            )

            decision = HITLDecision(
                decision_id=decision_dict.get("decision_id", f"test_{datetime.now(timezone.utc).timestamp()}"),
                context=context,
                risk_level=RiskLevel(decision_dict.get("risk_level", "high")),
                automation_level=AutomationLevel(decision_dict.get("automation_level", "supervised")),
                created_at=datetime.now(timezone.utc),
                sla_deadline=datetime.now(timezone.utc) + timedelta(minutes=10),
                status=DecisionStatus.PENDING,
            )

            # Enqueue decision
            decision_queue.enqueue(decision)

            # Broadcast to connected operators
            await event_broadcaster.broadcast_decision_pending(decision)

            logger.info(f"Test decision enqueued: {decision.decision_id}")

            return {
                "status": "success",
                "decision_id": decision.decision_id,
                "risk_level": decision.risk_level.value,
                "message": "Test decision enqueued successfully",
            }

        except Exception as e:
            logger.error(f"Failed to enqueue test decision: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Enqueue failed: {str(e)}",
            )

    logger.info("Governance API routes configured")
    return router
