"""Lymphnode Routes - PRODUCTION-READY

REST API endpoints for lymphnode coordination operations.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Path, status

from api.core_integration import CoordinationService
from api.core_integration.coordination_service import (
    AgentNotFoundForCloneError,
    CoordinationServiceError,
    LymphnodeNotAvailableError,
)
from api.models.coordination import (
    CloneRequest,
    CloneResponse,
    HomeostaticStateResponse,
    LymphnodeMetrics,
)

router = APIRouter()

# Service instance (initialized on startup)
_coordination_service: Optional[CoordinationService] = None


def get_coordination_service() -> CoordinationService:
    """Get CoordinationService instance."""
    global _coordination_service
    if _coordination_service is None:
        _coordination_service = CoordinationService()
    return _coordination_service


# ==================== CLONAL EXPANSION ====================


@router.post("/clone", response_model=CloneResponse, status_code=status.HTTP_201_CREATED)
async def clone_agent(clone_request: CloneRequest) -> CloneResponse:
    """
    Clone an agent with optional specialization (clonal expansion).

    This creates multiple specialized clones of a high-performing agent
    to respond to specific threats.

    Args:
        clone_request: Clone creation parameters

    Returns:
        Clone creation result with clone IDs

    Raises:
        HTTPException: If cloning fails
    """
    service = get_coordination_service()

    try:
        clone_response = await service.clone_agent(
            agent_id=clone_request.agent_id,
            especializacao=clone_request.especializacao,
            num_clones=clone_request.num_clones,
            mutate=clone_request.mutate,
            mutation_rate=clone_request.mutation_rate,
        )

        return clone_response

    except LymphnodeNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Lymphnode unavailable: {e}",
        )
    except AgentNotFoundForCloneError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except CoordinationServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloning failed: {e}",
        )


@router.delete("/clones/{especializacao}", status_code=status.HTTP_200_OK)
async def destroy_clones(
    especializacao: str = Path(..., description="Specialization to destroy"),
) -> dict:
    """
    Destroy clones by specialization (apoptosis).

    This triggers programmed cell death for all clones with a specific
    specialization, useful for cleanup after threat neutralization.

    Args:
        especializacao: Specialization identifier

    Returns:
        Number of clones destroyed

    Raises:
        HTTPException: If destruction fails
    """
    service = get_coordination_service()

    try:
        num_destroyed = await service.destroy_clones(especializacao)

        return {
            "especializacao": especializacao,
            "num_destroyed": num_destroyed,
            "message": f"Destroyed {num_destroyed} clones",
        }

    except LymphnodeNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Lymphnode unavailable: {e}",
        )
    except CoordinationServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clone destruction failed: {e}",
        )


# ==================== METRICS & STATUS ====================


@router.get("/metrics", response_model=LymphnodeMetrics)
async def get_lymphnode_metrics() -> LymphnodeMetrics:
    """
    Get lymphnode metrics and operational statistics.

    Returns:
        Lymphnode metrics including agent counts, threats, clones, etc.

    Raises:
        HTTPException: If metrics retrieval fails
    """
    service = get_coordination_service()

    try:
        metrics = await service.get_lymphnode_metrics()
        return metrics

    except LymphnodeNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Lymphnode unavailable: {e}",
        )
    except CoordinationServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {e}",
        )


@router.get("/homeostatic-state", response_model=HomeostaticStateResponse)
async def get_homeostatic_state() -> HomeostaticStateResponse:
    """
    Get current homeostatic state.

    The homeostatic state represents the system's stress level and
    recommended response actions:
    - REPOUSO: System at rest
    - VIGILÂNCIA: Low-level monitoring
    - ATENÇÃO: Moderate alert
    - ATIVAÇÃO: Significant stress
    - INFLAMAÇÃO: Critical stress

    Returns:
        Homeostatic state with description and recommended actions

    Raises:
        HTTPException: If state retrieval fails
    """
    service = get_coordination_service()

    try:
        state = await service.get_homeostatic_state()
        return state

    except LymphnodeNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Lymphnode unavailable: {e}",
        )
    except CoordinationServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"State retrieval failed: {e}",
        )
