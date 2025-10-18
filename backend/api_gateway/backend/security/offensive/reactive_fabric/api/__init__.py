"""
Reactive Fabric - API Module.

FastAPI routers for RESTful access to reactive fabric services.
Phase 1 compliant: all critical operations require HITL authorization.
"""

from .deception_router import router as deception_router
from .threat_router import router as threat_router
from .intelligence_router import router as intelligence_router
from .hitl_router import router as hitl_router


__all__ = [
    "deception_router",
    "threat_router",
    "intelligence_router",
    "hitl_router",
]
