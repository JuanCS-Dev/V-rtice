"""
Offensive Core Module
====================

Core abstractions and utilities for offensive security operations.

Provides:
    - Base classes for offensive tools
    - Common exceptions
    - Shared utilities
    - Configuration management
    - Orchestration engine
"""

from .base import OffensiveTool, ToolResult, ToolMetadata
from .exceptions import OffensiveToolError
from .config import OffensiveConfig
from .orchestration import (
    OrchestrationEngine,
    Operation,
    OperationStep,
    OperationResult,
    OperationPhase,
    OperationStatus
)

__all__ = [
    "OffensiveTool",
    "ToolResult",
    "ToolMetadata",
    "OffensiveToolError",
    "OffensiveConfig",
    "OrchestrationEngine",
    "Operation",
    "OperationStep",
    "OperationResult",
    "OperationPhase",
    "OperationStatus"
]
