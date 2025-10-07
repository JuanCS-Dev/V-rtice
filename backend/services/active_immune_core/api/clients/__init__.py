"""
External service clients with graceful degradation.

This module provides clients for integrating with external services
in the Vértice ecosystem:
- Treg Service (Regulatory T-cells)
- Memory Consolidation Service
- Adaptive Immunity Service
- Governance Workspace (HITL)
- IP Intelligence Service

All clients implement graceful degradation and circuit breaker patterns.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.
"""

from .base_client import BaseExternalClient
from .treg_client import TregClient
from .memory_client import MemoryClient
from .adaptive_immunity_client import AdaptiveImmunityClient
from .governance_client import GovernanceClient
from .ip_intel_client import IPIntelClient

__all__ = [
    "BaseExternalClient",
    "TregClient",
    "MemoryClient",
    "AdaptiveImmunityClient",
    "GovernanceClient",
    "IPIntelClient",
]
