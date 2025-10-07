"""API Models - PRODUCTION-READY

Pydantic models for request/response validation.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from .agents import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    AgentStatsResponse,
)
from .coordination import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    ElectionResponse,
    ConsensusProposal,
    ConsensusResponse,
)
from .common import (
    HealthResponse,
    MetricsResponse,
    ErrorResponse,
    SuccessResponse,
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
