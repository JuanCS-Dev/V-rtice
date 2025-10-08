"""API Models - PRODUCTION-READY

Pydantic models for request/response validation.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from .agents import (
    AgentCreate,
    AgentListResponse,
    AgentResponse,
    AgentStatsResponse,
    AgentUpdate,
)
from .common import (
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    SuccessResponse,
)
from .coordination import (
    ConsensusProposal,
    ConsensusResponse,
    ElectionResponse,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
)

__all__ = [
    # Agents
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "AgentListResponse",
    "AgentStatsResponse",
    # Coordination
    "TaskCreate",
    "TaskResponse",
    "TaskListResponse",
    "ElectionResponse",
    "ConsensusProposal",
    "ConsensusResponse",
    # Common
    "HealthResponse",
    "MetricsResponse",
    "ErrorResponse",
    "SuccessResponse",
]
