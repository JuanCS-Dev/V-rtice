"""
Decision Management Endpoints
HITL decision queue and workflow management
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

try:
    from .hitl_backend import (
        UserInDB,
        DecisionRequest,
        DecisionResponse,
        DecisionCreate,
        DecisionStatus,
        DecisionPriority,
        ActionType,
        get_current_active_analyst,
        get_current_user,
        db
    )
except ImportError:
    from hitl_backend import (
        UserInDB,
        DecisionRequest,
        DecisionResponse,
        DecisionCreate,
        DecisionStatus,
        DecisionPriority,
        ActionType,
        get_current_active_analyst,
        get_current_user,
        db
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


# ============================================================================
# ADDITIONAL MODELS
# ============================================================================

class DecisionFilters(BaseModel):
    """Filters for decision queries"""
    priority: Optional[DecisionPriority] = None
    status: Optional[DecisionStatus] = None
    threat_level: Optional[str] = None
    min_confidence: Optional[float] = None
    limit: int = 50


class DecisionStats(BaseModel):
    """Decision statistics"""
    total_pending: int
    critical_pending: int
    high_pending: int
    medium_pending: int
    low_pending: int
    total_completed: int
    avg_response_time_minutes: float
    decisions_last_24h: int


# ============================================================================
# DECISION QUEUE ENDPOINTS
# ============================================================================

@router.post("/submit", response_model=Dict[str, str])
async def submit_decision_request(
    decision: DecisionRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Submit new decision request (from CANDI)

    Args:
        decision: Decision request data
        current_user: Current user

    Returns:
        Success message with analysis ID
    """
    # Check if decision already exists
    existing = db.get_decision(decision.analysis_id)
    if existing:
        raise HTTPException(status_code=400, detail="Decision already exists")

    # Add to queue
    db.add_decision(decision)

    # Audit log
    db.audit("DECISION_SUBMITTED", current_user.username, {
        "analysis_id": decision.analysis_id,
        "priority": decision.priority.value,
        "threat_level": decision.threat_level
    })

    logger.info(
        f"Decision submitted: {decision.analysis_id} "
        f"(priority: {decision.priority.value}, threat: {decision.threat_level})"
    )

    return {
        "message": "Decision request submitted successfully",
        "analysis_id": decision.analysis_id
    }


@router.get("/pending", response_model=List[DecisionRequest])
async def get_pending_decisions(
    priority: Optional[DecisionPriority] = None,
    limit: int = Query(50, le=100),
    current_analyst: UserInDB = Depends(get_current_active_analyst)
):
    """
    Get pending decisions

    Args:
        priority: Filter by priority
        limit: Maximum number of results
        current_analyst: Current analyst user

    Returns:
        List of pending decisions
    """
    pending = db.get_pending_decisions(priority)

    return pending[:limit]


@router.get("/{analysis_id}", response_model=DecisionRequest)
async def get_decision(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get specific decision request

    Args:
        analysis_id: Analysis ID
        current_user: Current user

    Returns:
        Decision request
    """
    decision = db.get_decision(analysis_id)

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision


@router.post("/{analysis_id}/decide", response_model=DecisionResponse)
async def make_decision(
    analysis_id: str,
    decision_data: DecisionCreate,
    current_analyst: UserInDB = Depends(get_current_active_analyst)
):
    """
    Make decision on request

    Args:
        analysis_id: Analysis ID
        decision_data: Decision data
        current_analyst: Current analyst user

    Returns:
        Decision response
    """
    # Get decision request
    request = db.get_decision(analysis_id)
    if not request:
        raise HTTPException(status_code=404, detail="Decision request not found")

    # Check if already decided
    if analysis_id in db.responses:
        raise HTTPException(status_code=400, detail="Decision already made")

    # Validate escalation
    if decision_data.status == DecisionStatus.ESCALATED:
        if not decision_data.escalation_reason:
            raise HTTPException(status_code=400, detail="Escalation reason required")

    # Create response
    response = DecisionResponse(
        decision_id=analysis_id,
        status=decision_data.status,
        approved_actions=decision_data.approved_actions,
        notes=decision_data.notes,
        decided_by=current_analyst.username,
        decided_at=datetime.now(),
        escalation_reason=decision_data.escalation_reason
    )

    db.add_response(response)

    # Audit log
    db.audit("DECISION_MADE", current_analyst.username, {
        "analysis_id": analysis_id,
        "status": decision_data.status.value,
        "actions": [a.value for a in decision_data.approved_actions]
    })

    logger.info(
        f"Decision made on {analysis_id} by {current_analyst.username}: "
        f"{decision_data.status.value}"
    )

    return response


@router.get("/{analysis_id}/response", response_model=DecisionResponse)
async def get_decision_response(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get decision response

    Args:
        analysis_id: Analysis ID
        current_user: Current user

    Returns:
        Decision response
    """
    response = db.responses.get(analysis_id)

    if not response:
        raise HTTPException(status_code=404, detail="Decision response not found")

    return response


@router.get("/stats/summary", response_model=DecisionStats)
async def get_decision_stats(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get decision statistics

    Args:
        current_user: Current user

    Returns:
        Decision statistics
    """
    pending = db.get_pending_decisions()

    # Count by priority
    critical = len([d for d in pending if d.priority == DecisionPriority.CRITICAL])
    high = len([d for d in pending if d.priority == DecisionPriority.HIGH])
    medium = len([d for d in pending if d.priority == DecisionPriority.MEDIUM])
    low = len([d for d in pending if d.priority == DecisionPriority.LOW])

    # Calculate response time (simplified)
    completed = db.responses.values()
    if completed:
        response_times = []
        for response in completed:
            request = db.get_decision(response.decision_id)
            if request:
                delta = (response.decided_at - request.created_at).total_seconds() / 60
                response_times.append(delta)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
    else:
        avg_response_time = 0.0

    # Decisions in last 24h
    cutoff = datetime.now() - timedelta(hours=24)
    recent = len([d for d in db.decisions.values() if d.created_at > cutoff])

    return DecisionStats(
        total_pending=len(pending),
        critical_pending=critical,
        high_pending=high,
        medium_pending=medium,
        low_pending=low,
        total_completed=len(db.responses),
        avg_response_time_minutes=avg_response_time,
        decisions_last_24h=recent
    )


@router.post("/{analysis_id}/escalate", response_model=DecisionResponse)
async def escalate_decision(
    analysis_id: str,
    escalation_reason: str,
    current_analyst: UserInDB = Depends(get_current_active_analyst)
):
    """
    Escalate decision to higher authority

    Args:
        analysis_id: Analysis ID
        escalation_reason: Reason for escalation
        current_analyst: Current analyst user

    Returns:
        Decision response
    """
    request = db.get_decision(analysis_id)
    if not request:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Create escalation response
    response = DecisionResponse(
        decision_id=analysis_id,
        status=DecisionStatus.ESCALATED,
        approved_actions=[],
        notes=f"Escalated by {current_analyst.username}",
        decided_by=current_analyst.username,
        decided_at=datetime.now(),
        escalation_reason=escalation_reason
    )

    db.add_response(response)

    # Audit log
    db.audit("DECISION_ESCALATED", current_analyst.username, {
        "analysis_id": analysis_id,
        "reason": escalation_reason
    })

    logger.warning(f"Decision escalated: {analysis_id} - {escalation_reason}")

    return response


# ============================================================================
# IMPORT IN MAIN APP
# ============================================================================

# Make sure to import this router in hitl_backend.py:
# from .decision_endpoints import router as decision_router
# app.include_router(decision_router)
