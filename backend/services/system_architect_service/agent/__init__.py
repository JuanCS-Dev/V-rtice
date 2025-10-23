"""System Architect Agent - Continuous architectural analysis.

This module provides the SystemArchitectAgent for macro-level platform analysis.

Two versions available:
- SystemArchitectAgent: Full version with Kafka/Redis (requires infrastructure)
- SystemArchitectAgentStandalone: Standalone version (works immediately, uses logging)
"""

try:
    from .system_architect_agent import SystemArchitectAgent
    FULL_VERSION_AVAILABLE = True
except ImportError:
    FULL_VERSION_AVAILABLE = False

from .system_architect_agent_standalone import SystemArchitectAgentStandalone

__all__ = ["SystemArchitectAgentStandalone"]

if FULL_VERSION_AVAILABLE:
    __all__.append("SystemArchitectAgent")
