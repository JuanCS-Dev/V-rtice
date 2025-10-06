"""FASE 10: Edge Agent Service

Edge sensor for distributed organism deployment.
Collects events locally and syncs to cloud brain.

NO MOCKS - Production-ready edge deployment.
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Team"

from .edge_agent_core import (
    BatchingStrategy,
    EdgeAgentController,
    EdgeAgentStatus,
    Event,
    EventBatch,
    EventType,
    HeartbeatManager,
    LocalBuffer,
    LocalMetrics,
    RetryLogic,
)

__all__ = [
    "EventType",
    "EdgeAgentStatus",
    "Event",
    "EventBatch",
    "LocalBuffer",
    "BatchingStrategy",
    "HeartbeatManager",
    "RetryLogic",
    "LocalMetrics",
    "EdgeAgentController",
]
