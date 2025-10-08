"""Core Integration - PRODUCTION-READY

Integration layer between REST API (FASE 2) and Core System (FASE 1).

This module provides:
- CoreManager: Singleton to manage Core System lifecycle
- AgentService: Wrapper for AgentFactory (agent CRUD operations)
- CoordinationService: Wrapper for Lymphnode (coordination operations)
- EventBridge: Cytokines/Hormones → WebSocket bridge
- HealthBridge: Core health → API health aggregation

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from .agent_service import AgentService
from .coordination_service import CoordinationService
from .core_manager import CoreManager
from .event_bridge import EventBridge

__all__ = ["CoreManager", "AgentService", "CoordinationService", "EventBridge"]
