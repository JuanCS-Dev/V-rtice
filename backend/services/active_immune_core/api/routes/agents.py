"""Agent Routes - PRODUCTION-READY

REST API endpoints for agent management.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Query, Path, HTTPException, status
from api.models.agents import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    AgentStatsResponse,
    AgentAction,
    AgentActionResponse,
)
from api.core_integration import AgentService
from api.core_integration.agent_service import AgentNotFoundError, AgentServiceError

router = APIRouter()

# Service instance (initialized on startup)
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get AgentService instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate) -> AgentResponse:
    """
    Create a new agent.

    Args:
        agent_data: Agent creation data

    Returns:
        Created agent information

    Raises:
        HTTPException: If agent creation fails
    """
    service = get_agent_service()

    try:
        agent = await service.create_agent(
            agent_type=agent_data.agent_type,
            config=agent_data.config or {},
        )
        return agent

    except AgentServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status_filter: Optional[str] = Query(None, description="Filter by status", alias="status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum items to return"),
) -> AgentListResponse:
    """
    List all agents with optional filtering.

    Args:
        agent_type: Filter by agent type
        status_filter: Filter by status
        skip: Number of items to skip
        limit: Maximum items to return

    Returns:
        List of agents with statistics
    """
    service = get_agent_service()

    # Service handles all filtering, pagination, and statistics
    return await service.list_agents(
        agent_type=agent_type,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str = Path(..., description="Agent identifier"),
) -> AgentResponse:
    """
    Get agent by ID.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent information

    Raises:
        HTTPException: If agent not found
    """
    service = get_agent_service()

    try:
        agent = await service.get_agent(agent_id)
        return agent

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str = Path(..., description="Agent identifier"),
    agent_update: AgentUpdate = ...,
) -> AgentResponse:
    """
    Update agent information.

    Args:
        agent_id: Agent identifier
        agent_update: Fields to update

    Returns:
        Updated agent information

    Raises:
        HTTPException: If agent not found
    """
    service = get_agent_service()

    try:
        # Service handles the update with AgentUpdate object
        agent = await service.update_agent(agent_id, agent_update)
        return agent

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    except AgentServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str = Path(..., description="Agent identifier"),
) -> None:
    """
    Delete agent.

    Args:
        agent_id: Agent identifier

    Raises:
        HTTPException: If agent not found
    """
    service = get_agent_service()

    try:
        await service.delete_agent(agent_id)

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )


@router.get("/{agent_id}/stats", response_model=AgentStatsResponse)
async def get_agent_stats(
    agent_id: str = Path(..., description="Agent identifier"),
) -> AgentStatsResponse:
    """
    Get agent statistics.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent statistics

    Raises:
        HTTPException: If agent not found
    """
    service = get_agent_service()

    try:
        stats = await service.get_agent_stats(agent_id)
        return stats

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )


@router.post("/{agent_id}/actions", response_model=AgentActionResponse)
async def perform_agent_action(
    agent_id: str = Path(..., description="Agent identifier"),
    action: AgentAction = ...,
) -> AgentActionResponse:
    """
    Perform action on agent.

    Supported actions:
    - start: Start the agent
    - stop: Stop the agent
    - pause: Pause the agent
    - resume: Resume the agent
    - restart: Restart the agent

    Args:
        agent_id: Agent identifier
        action: Action to perform

    Returns:
        Action result

    Raises:
        HTTPException: If agent not found or action invalid
    """
    service = get_agent_service()

    valid_actions = ["start", "stop", "pause", "resume", "restart"]

    if action.action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Valid actions: {', '.join(valid_actions)}",
        )

    try:
        # Delegate to AgentService.execute_action()
        result = await service.execute_action(agent_id, action)
        return result

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    except AgentServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/types/available", response_model=List[str])
async def list_available_agent_types() -> List[str]:
    """
    List all available agent types.

    Returns:
        List of agent type names
    """
    return [
        "neutrophil",
        "macrophage",
        "nk_cell",
        "dendritic",
        "helper_t",
        "cytotoxic_t",
        "b_cell",
        "t_reg",
    ]
