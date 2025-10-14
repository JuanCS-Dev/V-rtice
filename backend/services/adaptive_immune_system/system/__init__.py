"""
System Module - Cross-cutting system coordination.

Provides centralized coordination for system-wide operations:
- Decision execution from HITL
- Status synchronization
- Workflow orchestration
"""

from .decision_executor import DecisionExecutor

__all__ = ["DecisionExecutor"]
