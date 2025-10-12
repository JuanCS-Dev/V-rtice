"""
Offensive Core Module - MAXIMUS Enhanced
========================================

Core abstractions and utilities for offensive security operations
with consciousness-aware execution and ethical boundaries.

Philosophy: Tools serve the Emergent Mind.

Provides:
    - Base classes for offensive tools
    - MAXIMUS integration layer
    - Tool registry system
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
from .maximus_adapter import (
    MAXIMUSToolAdapter,
    MAXIMUSToolContext,
    OperationMode,
    EnhancedToolResult,
    EthicalContext,
    EthicalDecision
)
from .tool_registry import (
    ToolRegistry,
    ToolCategory,
    ToolInfo,
    registry,
    register_tool,
    get_tool
)

# Auto-register all tools
from . import auto_register  # noqa: F401

__all__ = [
    # Base classes
    "OffensiveTool",
    "ToolResult",
    "ToolMetadata",
    "OffensiveToolError",
    "OffensiveConfig",
    
    # Orchestration
    "OrchestrationEngine",
    "Operation",
    "OperationStep",
    "OperationResult",
    "OperationPhase",
    "OperationStatus",
    
    # MAXIMUS integration
    "MAXIMUSToolAdapter",
    "MAXIMUSToolContext",
    "OperationMode",
    "EnhancedToolResult",
    "EthicalContext",
    "EthicalDecision",
    
    # Registry
    "ToolRegistry",
    "ToolCategory",
    "ToolInfo",
    "registry",
    "register_tool",
    "get_tool"
]
