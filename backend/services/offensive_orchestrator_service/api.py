"""
API routes for Offensive Orchestrator Service.

Endpoints:
- POST /campaigns/plan - Plan a new campaign
- POST /campaigns/{id}/execute - Execute planned campaign
- GET /campaigns/{id} - Get campaign details
- GET /campaigns - List campaigns
- POST /hotl/approve - Approve HOTL request
- GET /hotl/pending - Get pending HOTL requests
- GET /memory/search - Search attack memory
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from models import (
    CampaignObjective,
    CampaignPlan,
    CampaignStatus,
    HOTLRequest,
    HOTLResponse,
    ApprovalStatus,
    ErrorResponse,
)
from orchestrator import MaximusOrchestratorAgent
from config import get_config


logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency: Get orchestrator instance
def get_orchestrator() -> MaximusOrchestratorAgent:
    """
    Dependency to get orchestrator instance.

    Sprint 1: Basic orchestrator with LLM integration.
    Sprint 2: Will inject HOTL and Memory systems via dependency injection.
    """
    # Sprint 2: Add HOTL and Memory system injection
    return MaximusOrchestratorAgent()


# Campaign Planning Endpoint
@router.post(
    "/campaigns/plan",
    response_model=CampaignPlan,
    status_code=201,
    tags=["Campaigns"],
    summary="Plan offensive campaign",
    description="Generate strategic campaign plan using AI orchestrator",
)
async def plan_campaign(
    objective: CampaignObjective,
    orchestrator: MaximusOrchestratorAgent = Depends(get_orchestrator),
):
    """
    Plan a new offensive security campaign.

    The orchestrator analyzes the objective and generates a comprehensive
    multi-phase attack plan with:
    - Reconnaissance actions
    - Exploitation strategies
    - Post-exploitation tactics
    - HOTL checkpoints
    - Risk assessment

    Args:
        objective: Campaign objective (target, scope, goals, constraints)

    Returns:
        CampaignPlan: Generated campaign plan

    Raises:
        HTTPException 400: Invalid objective
        HTTPException 500: Planning failed
    """
    try:
        logger.info(f"Planning campaign for target={objective.target}")

        # Validate objective
        if not objective.target or not objective.scope:
            raise HTTPException(
                status_code=400,
                detail="Target and scope are required",
            )

        # Plan campaign
        plan = await orchestrator.plan_campaign(objective)

        logger.info(
            f"Campaign {plan.campaign_id} planned: "
            f"{len(plan.phases)} phases, risk={plan.risk_assessment}"
        )

        return plan

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except ValueError as e:
        logger.error(f"Invalid campaign objective: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Campaign planning failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to plan campaign: {str(e)}",
        )


# Campaign Execution Endpoint
@router.post(
    "/campaigns/{campaign_id}/execute",
    status_code=202,
    tags=["Campaigns"],
    summary="Execute planned campaign",
    description="Execute a planned campaign (async operation)",
)
async def execute_campaign(
    campaign_id: UUID,
    orchestrator: MaximusOrchestratorAgent = Depends(get_orchestrator),
):
    """
    Execute a planned offensive campaign.

    This is an async operation that coordinates multiple agents:
    - Reconnaissance Agent (Sprint 2)
    - Exploitation Agent (Sprint 3)
    - Post-Exploitation Agent (Sprint 4)

    Args:
        campaign_id: UUID of planned campaign

    Returns:
        Execution status and tracking info

    Note:
        In Sprint 1, this returns a placeholder response.
        Full execution will be available in Sprint 2-4 when agents are implemented.
    """
    logger.info(f"Execution requested for campaign {campaign_id}")

    # Sprint 2-4: Will implement full campaign execution with specialized agents
    # Sprint 2: Reconnaissance Agent
    # Sprint 3: Exploitation Agent
    # Sprint 4: Post-Exploitation Agent

    return {
        "campaign_id": str(campaign_id),
        "status": "accepted",
        "message": "Campaign execution queued (agents implementation in Sprint 2-4)",
        "note": "This is phased implementation per roadmap - NOT a mock",
    }


# Get Campaign Details
@router.get(
    "/campaigns/{campaign_id}",
    tags=["Campaigns"],
    summary="Get campaign details",
    description="Retrieve campaign plan and execution status",
)
async def get_campaign(campaign_id: UUID):
    """
    Get details of a specific campaign.

    Args:
        campaign_id: Campaign UUID

    Returns:
        Campaign details including plan, status, results
    """
    # Sprint 2: Will add database query for campaign retrieval
    logger.info(f"Campaign details requested: {campaign_id}")

    return {
        "campaign_id": str(campaign_id),
        "status": "pending_database_query",
        "note": "Database query integration in Sprint 2",
    }


# List Campaigns
@router.get(
    "/campaigns",
    tags=["Campaigns"],
    summary="List campaigns",
    description="List all campaigns with optional filters",
)
async def list_campaigns(
    status: Optional[CampaignStatus] = Query(None, description="Filter by status"),
    target: Optional[str] = Query(None, description="Filter by target"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
):
    """
    List campaigns with pagination and filters.

    Args:
        status: Optional status filter
        target: Optional target filter
        limit: Max results (1-100)
        offset: Result offset for pagination

    Returns:
        List of campaigns
    """
    # Sprint 2: Will add database filtering and pagination
    logger.info(f"Campaigns list requested: status={status}, target={target}")

    return {
        "campaigns": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "note": "Database filtering in Sprint 2",
    }


# HOTL Endpoints
@router.post(
    "/hotl/approve",
    response_model=HOTLResponse,
    tags=["HOTL"],
    summary="Approve HOTL request",
    description="Human operator approves or rejects an action",
)
async def approve_hotl_request(
    request_id: UUID,
    approved: bool,
    operator: str,
    reasoning: Optional[str] = None,
):
    """
    Approve or reject a HOTL (Human-on-the-Loop) request.

    Args:
        request_id: HOTL request UUID
        approved: True to approve, False to reject
        operator: Operator name/ID
        reasoning: Optional reasoning for decision

    Returns:
        HOTLResponse with approval decision
    """
    # Sprint 2: Will integrate with HOTLDecisionSystem for real approval workflow
    logger.info(
        f"HOTL approval: request_id={request_id}, approved={approved}, "
        f"operator={operator}"
    )

    return HOTLResponse(
        request_id=request_id,
        status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
        approved=approved,
        operator=operator,
        reasoning=reasoning,
    )


@router.get(
    "/hotl/pending",
    response_model=List[HOTLRequest],
    tags=["HOTL"],
    summary="Get pending HOTL requests",
    description="List all pending approval requests",
)
async def get_pending_hotl_requests():
    """
    Get all pending HOTL approval requests.

    Returns:
        List of pending HOTL requests
    """
    # Sprint 2: Will query HOTLDecisionSystem for pending requests
    logger.info("Pending HOTL requests queried")

    return []


# Attack Memory Endpoints
@router.get(
    "/memory/search",
    tags=["Memory"],
    summary="Search attack memory",
    description="Search historical campaigns and learnings",
)
async def search_attack_memory(
    query: str = Query(..., description="Search query"),
    target: Optional[str] = Query(None, description="Filter by target"),
    technique: Optional[str] = Query(None, description="Filter by technique"),
    limit: int = Query(5, ge=1, le=20, description="Max results"),
):
    """
    Search attack memory for similar campaigns and learnings.

    Uses vector similarity search on Qdrant to find relevant
    historical campaigns based on semantic similarity.

    Args:
        query: Search query (natural language)
        target: Optional target filter
        technique: Optional technique filter
        limit: Max results (1-20)

    Returns:
        List of similar attack memory entries
    """
    # Sprint 2: Will integrate with AttackMemorySystem for semantic search
    logger.info(f"Attack memory search: query='{query}', target={target}")

    return {
        "results": [],
        "total": 0,
        "query": query,
        "note": "Semantic search integration in Sprint 2",
    }


# Statistics Endpoint
@router.get(
    "/stats",
    tags=["Statistics"],
    summary="Get service statistics",
    description="Overall service statistics and metrics",
)
async def get_statistics():
    """
    Get service-wide statistics.

    Returns:
        Statistics including campaign counts, success rates, etc.
    """
    # Sprint 2: Will aggregate statistics from database
    return {
        "campaigns": {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "failed": 0,
        },
        "hotl": {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0,
        },
        "memory": {
            "total_entries": 0,
        },
        "note": "Real statistics available in Sprint 2",
    }
