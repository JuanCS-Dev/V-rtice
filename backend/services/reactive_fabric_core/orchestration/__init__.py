"""
Orchestration Engine for Reactive Fabric.

Correlates events from multiple collectors and identifies patterns.
Phase 1: PASSIVE orchestration only - no automated responses.
"""

from .orchestration_engine import (
    OrchestrationEngine,
    OrchestrationConfig,
    CorrelationRule,
    ThreatScore,
    OrchestrationEvent
)

__all__ = [
    "OrchestrationEngine",
    "OrchestrationConfig",
    "CorrelationRule",
    "ThreatScore",
    "OrchestrationEvent"
]