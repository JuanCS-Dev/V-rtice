"""
Reactive Fabric - HITL (Human-in-the-Loop) API Router.

RESTful endpoints for human authorization workflows and decision tracking.
Phase 1 critical requirement: human approval for ALL Level 3+ actions.

Implements "human-in-the-loop" not as "human-as-a-rubber-stamp".
Every decision tracked, audited, and analyzed for pattern recognition.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database.session import get_db_session
from ..models.hitl import (
    HITLDecision,
    HITLDecisionCreate,
    HITLDecisionUpdate,
    HITLDecisionType,
    HITLDecisionStatus,
    HITLDecisionOutcome,
    HITLApprovalLevel,
    HITLAuditLog,
    HITLMetrics
)


logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/hitl",
    tags=["Human-in-the-Loop"],
    responses={
        404: {"description": "Resource not found"},
        403: {"description": "Unauthorized decision attempt"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_hitl_service(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Dependency injection for HITL service.
    
    Args:
        session: Database session from FastAPI dependency
    
    Returns:
        Configured HITL service instance
    """
    from ..services.hitl_service import HITLService
    return HITLService(session)


# ============================================================================
# DECISION REQUEST ENDPOINTS
# ============================================================================

@router.post(
    "/decisions",
    response_model=HITLDecision,
    status_code=status.HTTP_201_CREATED,
    summary="Request Human Decision",
    description="""
    Create human authorization request for reactive fabric action.
    
    **Phase 1 Requirement:**
    ALL Level 3+ actions require human approval.
    - Level 1: Passive observation (auto-approved)
    - Level 2: Intelligence analysis (auto-approved)
    - Level 3: Asset modification (REQUIRES APPROVAL)
    - Level 4: Response action (FORBIDDEN in Phase 1)
    
    **Critical Factor:**
    Human-in-the-loop MUST NOT become human-as-a-rubber-stamp.
    Decision quality monitoring is mandatory.
    """
)
async def create_decision_request(
    decision: HITLDecisionCreate,
    service = Depends(get_hitl_service)
) -> HITLDecision:
    """
    Create human decision request.
    
    Implements Phase 1 authorization gate for critical actions.
    Every request logged and tracked for audit trail.
    
    Args:
        decision: Decision request details
        service: Injected HITL service
    
    Returns:
        Created HITLDecision with tracking ID
    
    Raises:
        HTTPException: 403 if action type forbidden in Phase 1
    """
    try:
        logger.info(
            "creating_decision_request",
            decision_type=decision.decision_type,
            approval_level=decision.required_approval_level,
            context_summary=decision.context_summary[:100] if decision.context_summary else None
        )
        
        created_decision = await service.create_decision_request(decision)
        
        logger.info(
            "decision_request_created",
            decision_id=str(created_decision.id),
            status=created_decision.status,
            requires_approval=created_decision.requires_human_approval
        )
        
        return created_decision
        
    except ValueError as e:
        # Phase 1 constraint violation
        logger.warning("phase1_decision_forbidden", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Phase 1 constraint violation: {str(e)}"
        )
    except Exception as e:
        logger.error("decision_request_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Decision request creation failed"
        )


@router.get(
    "/decisions",
    response_model=List[HITLDecision],
    summary="List Decision Requests",
    description="Retrieve human decision requests with filtering."
)
async def list_decision_requests(
    status_filter: Optional[HITLDecisionStatus] = Query(None, description="Filter by status", alias="status"),
    decision_type: Optional[HITLDecisionType] = Query(None, description="Filter by decision type"),
    approval_level: Optional[HITLApprovalLevel] = Query(None, description="Filter by approval level"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned analyst"),
    pending_only: bool = Query(False, description="Only pending decisions"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    service = Depends(get_hitl_service)
) -> List[HITLDecision]:
    """
    List decision requests with filtering.
    
    Primary interface for analyst decision queue.
    
    Args:
        status_filter: Optional status filter
        decision_type: Optional decision type filter
        approval_level: Optional approval level filter
        assigned_to: Optional analyst filter
        pending_only: Only pending decisions
        skip: Pagination offset
        limit: Results per page
        service: Injected HITL service
    
    Returns:
        List of HITLDecision
    """
    try:
        logger.debug(
            "listing_decision_requests",
            status=status_filter,
            decision_type=decision_type,
            pending_only=pending_only
        )
        
        decisions = await service.list_decision_requests(
            status=status_filter,
            decision_type=decision_type,
            approval_level=approval_level,
            assigned_to=assigned_to,
            pending_only=pending_only,
            skip=skip,
            limit=limit
        )
        
        logger.info("decision_requests_retrieved", count=len(decisions))
        return decisions
        
    except Exception as e:
        logger.error("decision_listing_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve decision requests"
        )


@router.get(
    "/decisions/{decision_id}",
    response_model=HITLDecision,
    summary="Get Decision Request",
    description="Retrieve specific decision request with full context."
)
async def get_decision_request(
    decision_id: UUID,
    include_audit_trail: bool = Query(False, description="Include full audit trail"),
    service = Depends(get_hitl_service)
) -> HITLDecision:
    """
    Retrieve specific decision request.
    
    Args:
        decision_id: Decision UUID
        include_audit_trail: Include audit log
        service: Injected HITL service
    
    Returns:
        HITLDecision with full context
    
    Raises:
        HTTPException: 404 if decision not found
    """
    try:
        decision = await service.get_decision_request(
            decision_id=decision_id,
            include_audit_trail=include_audit_trail
        )
        
        if not decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found"
            )
        
        return decision
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("decision_retrieval_failed", decision_id=str(decision_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve decision request"
        )


# ============================================================================
# DECISION APPROVAL ENDPOINTS
# ============================================================================

@router.post(
    "/decisions/{decision_id}/approve",
    response_model=HITLDecision,
    summary="Approve Decision Request",
    description="""
    Approve pending decision request.
    
    **Authorization Requirements:**
    - Analyst identity verification
    - Training certification check
    - Authorization level validation
    - Rationale documentation
    
    **Audit Trail:**
    All approvals logged with:
    - Analyst identity
    - Timestamp (nanosecond precision)
    - Decision rationale
    - Context analysis
    """
)
async def approve_decision_request(
    decision_id: UUID,
    analyst_id: str = Query(..., description="Analyst identifier"),
    rationale: str = Query(..., description="Approval rationale"),
    confidence: float = Query(..., ge=0.0, le=1.0, description="Decision confidence"),
    service = Depends(get_hitl_service)
) -> HITLDecision:
    """
    Approve decision request with audit trail.
    
    Args:
        decision_id: Decision UUID
        analyst_id: Approving analyst identifier
        rationale: Approval rationale
        confidence: Analyst confidence in decision
        service: Injected HITL service
    
    Returns:
        Approved HITLDecision
    
    Raises:
        HTTPException: 404 if decision not found
        HTTPException: 403 if analyst unauthorized
    """
    try:
        logger.info(
            "approving_decision",
            decision_id=str(decision_id),
            analyst_id=analyst_id,
            confidence=confidence
        )
        
        approved = await service.approve_decision(
            decision_id=decision_id,
            analyst_id=analyst_id,
            rationale=rationale,
            confidence=confidence
        )
        
        if not approved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found"
            )
        
        logger.info(
            "decision_approved",
            decision_id=str(decision_id),
            analyst_id=analyst_id,
            outcome=approved.outcome
        )
        
        return approved
        
    except HTTPException:
        raise
    except PermissionError as e:
        logger.warning("unauthorized_approval_attempt", decision_id=str(decision_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst unauthorized for this approval level"
        )
    except Exception as e:
        logger.error("decision_approval_failed", decision_id=str(decision_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Decision approval failed"
        )


@router.post(
    "/decisions/{decision_id}/reject",
    response_model=HITLDecision,
    summary="Reject Decision Request",
    description="Reject pending decision request with rationale."
)
async def reject_decision_request(
    decision_id: UUID,
    analyst_id: str = Query(..., description="Analyst identifier"),
    rationale: str = Query(..., description="Rejection rationale"),
    service = Depends(get_hitl_service)
) -> HITLDecision:
    """
    Reject decision request.
    
    Args:
        decision_id: Decision UUID
        analyst_id: Rejecting analyst identifier
        rationale: Rejection rationale
        service: Injected HITL service
    
    Returns:
        Rejected HITLDecision
    
    Raises:
        HTTPException: 404 if decision not found
    """
    try:
        logger.info(
            "rejecting_decision",
            decision_id=str(decision_id),
            analyst_id=analyst_id
        )
        
        rejected = await service.reject_decision(
            decision_id=decision_id,
            analyst_id=analyst_id,
            rationale=rationale
        )
        
        if not rejected:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found"
            )
        
        logger.info(
            "decision_rejected",
            decision_id=str(decision_id),
            analyst_id=analyst_id
        )
        
        return rejected
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("decision_rejection_failed", decision_id=str(decision_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Decision rejection failed"
        )


@router.post(
    "/decisions/{decision_id}/defer",
    response_model=HITLDecision,
    summary="Defer Decision Request",
    description="Defer decision request for escalation or additional context."
)
async def defer_decision_request(
    decision_id: UUID,
    analyst_id: str = Query(..., description="Analyst identifier"),
    reason: str = Query(..., description="Deferral reason"),
    escalate_to: Optional[str] = Query(None, description="Escalation target"),
    service = Depends(get_hitl_service)
) -> HITLDecision:
    """
    Defer decision request.
    
    Args:
        decision_id: Decision UUID
        analyst_id: Analyst identifier
        reason: Deferral reason
        escalate_to: Optional escalation target
        service: Injected HITL service
    
    Returns:
        Deferred HITLDecision
    
    Raises:
        HTTPException: 404 if decision not found
    """
    try:
        logger.info(
            "deferring_decision",
            decision_id=str(decision_id),
            analyst_id=analyst_id,
            escalate_to=escalate_to
        )
        
        deferred = await service.defer_decision(
            decision_id=decision_id,
            analyst_id=analyst_id,
            reason=reason,
            escalate_to=escalate_to
        )
        
        if not deferred:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found"
            )
        
        logger.info("decision_deferred", decision_id=str(decision_id))
        return deferred
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("decision_deferral_failed", decision_id=str(decision_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Decision deferral failed"
        )


# ============================================================================
# AUDIT & COMPLIANCE ENDPOINTS
# ============================================================================

@router.get(
    "/decisions/{decision_id}/audit",
    response_model=List[HITLAuditLog],
    summary="Get Decision Audit Trail",
    description="Retrieve complete audit trail for decision request."
)
async def get_decision_audit_trail(
    decision_id: UUID,
    service = Depends(get_hitl_service)
) -> List[HITLAuditLog]:
    """
    Retrieve audit trail for decision.
    
    Critical for compliance and post-incident analysis.
    
    Args:
        decision_id: Decision UUID
        service: Injected HITL service
    
    Returns:
        List of HITLAuditLog entries
    
    Raises:
        HTTPException: 404 if decision not found
    """
    try:
        audit_trail = await service.get_audit_trail(decision_id)
        
        if audit_trail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found"
            )
        
        logger.info("audit_trail_retrieved", decision_id=str(decision_id), entries=len(audit_trail))
        return audit_trail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_retrieval_failed", decision_id=str(decision_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit trail retrieval failed"
        )


@router.get(
    "/audit/analyst/{analyst_id}",
    response_model=List[HITLDecision],
    summary="Get Analyst Decision History",
    description="""
    Retrieve all decisions by specific analyst.
    
    **Quality Monitoring:**
    Enables pattern analysis of analyst decision quality:
    - Approval/rejection ratios
    - Average confidence scores
    - Decision time metrics
    - False positive rates
    
    **Critical Factor:**
    Prevents "human-as-a-rubber-stamp" degradation.
    """
)
async def get_analyst_decision_history(
    analyst_id: str,
    start_date: Optional[datetime] = Query(None, description="History start date"),
    end_date: Optional[datetime] = Query(None, description="History end date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service = Depends(get_hitl_service)
) -> List[HITLDecision]:
    """
    Get analyst decision history.
    
    Args:
        analyst_id: Analyst identifier
        start_date: Optional start date
        end_date: Optional end date
        skip: Pagination offset
        limit: Results per page
        service: Injected HITL service
    
    Returns:
        List of HITLDecision by analyst
    """
    try:
        history = await service.get_analyst_history(
            analyst_id=analyst_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        logger.info("analyst_history_retrieved", analyst_id=analyst_id, count=len(history))
        return history
        
    except Exception as e:
        logger.error("analyst_history_failed", analyst_id=analyst_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analyst history retrieval failed"
        )


# ============================================================================
# METRICS & QUALITY MONITORING
# ============================================================================

@router.get(
    "/metrics",
    response_model=HITLMetrics,
    summary="HITL Decision Metrics",
    description="""
    Human-in-the-loop decision quality metrics.
    
    **Quality Indicators:**
    - Decision latency (request → approval time)
    - Approval/rejection ratios
    - Average confidence scores
    - Escalation rates
    - Analyst workload distribution
    
    **Critical Success Factor:**
    Maintaining high-quality human decisions is mandatory.
    Rubber-stamp patterns trigger escalation protocols.
    """
)
async def get_hitl_metrics(
    start_date: Optional[datetime] = Query(None, description="Metrics period start"),
    end_date: Optional[datetime] = Query(None, description="Metrics period end"),
    analyst_id: Optional[str] = Query(None, description="Filter by analyst"),
    service = Depends(get_hitl_service)
) -> HITLMetrics:
    """
    Get HITL decision metrics.
    
    Args:
        start_date: Optional period start
        end_date: Optional period end
        analyst_id: Optional analyst filter
        service: Injected HITL service
    
    Returns:
        HITLMetrics with quality indicators
    """
    try:
        logger.info("retrieving_hitl_metrics", analyst_id=analyst_id)
        
        metrics = await service.get_metrics(
            start_date=start_date,
            end_date=end_date,
            analyst_id=analyst_id
        )
        
        logger.info(
            "hitl_metrics_retrieved",
            total_decisions=metrics.total_decisions,
            avg_confidence=metrics.average_confidence_score,
            avg_latency_seconds=metrics.average_decision_latency_seconds
        )
        
        return metrics
        
    except Exception as e:
        logger.error("metrics_retrieval_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics retrieval failed"
        )


@router.get(
    "/quality/rubber-stamp-detection",
    response_model=dict,
    summary="Detect Rubber-Stamp Patterns",
    description="""
    Analyze decision patterns for rubber-stamp indicators.
    
    **Warning Signs:**
    - Approval rate >95%
    - Decision latency <30 seconds
    - Low confidence variance
    - Identical rationales
    - No deferrals/escalations
    
    **Escalation Trigger:**
    Detected rubber-stamp patterns trigger training review.
    """
)
async def detect_rubber_stamp_patterns(
    analyst_id: Optional[str] = Query(None, description="Analyze specific analyst"),
    lookback_days: int = Query(30, ge=1, le=365, description="Analysis period"),
    service = Depends(get_hitl_service)
) -> dict:
    """
    Detect rubber-stamp decision patterns.
    
    Args:
        analyst_id: Optional analyst to analyze
        lookback_days: Analysis period
        service: Injected HITL service
    
    Returns:
        Rubber-stamp analysis with risk indicators
    """
    try:
        logger.info("detecting_rubber_stamp_patterns", analyst_id=analyst_id)
        
        analysis = await service.detect_rubber_stamp_patterns(
            analyst_id=analyst_id,
            lookback_days=lookback_days
        )
        
        logger.info(
            "rubber_stamp_analysis_complete",
            risk_level=analysis.get("risk_level"),
            approval_rate=analysis.get("approval_rate")
        )
        
        return analysis
        
    except Exception as e:
        logger.error("rubber_stamp_detection_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rubber-stamp detection failed"
        )


# ============================================================================
# TRAINING & CERTIFICATION
# ============================================================================

@router.get(
    "/analysts/{analyst_id}/certification",
    response_model=dict,
    summary="Get Analyst Certification Status",
    description="""
    Retrieve analyst training and certification status.
    
    **Required Certifications:**
    - Phase 1 Protocol Training
    - Deception Asset Management
    - Threat Intelligence Analysis
    - Incident Response Basics
    
    **Recertification:**
    Annual recertification mandatory for authorization maintenance.
    """
)
async def get_analyst_certification(
    analyst_id: str,
    service = Depends(get_hitl_service)
) -> dict:
    """
    Get analyst certification status.
    
    Args:
        analyst_id: Analyst identifier
        service: Injected HITL service
    
    Returns:
        Certification status and training records
    
    Raises:
        HTTPException: 404 if analyst not found
    """
    try:
        certification = await service.get_analyst_certification(analyst_id)
        
        if not certification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analyst {analyst_id} not found"
            )
        
        logger.info("certification_retrieved", analyst_id=analyst_id)
        return certification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("certification_retrieval_failed", analyst_id=analyst_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Certification retrieval failed"
        )


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@router.get(
    "/health",
    summary="HITL Module Health",
    description="Health check for human-in-the-loop module."
)
async def hitl_health() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Health status with decision queue metrics
    """
    return {
        "status": "healthy",
        "module": "human_in_the_loop",
        "phase": "1",
        "authorization": "required",
        "rubber_stamp_prevention": "active"
    }
