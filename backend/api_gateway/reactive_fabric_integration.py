"""
Reactive Fabric API Integration Module.

Registers reactive fabric routers with FastAPI gateway.
Phase 1 implementation: passive intelligence collection with HITL authorization.
"""

from fastapi import FastAPI
import structlog

from backend.security.offensive.reactive_fabric.api import (
    deception_router,
    threat_router,
    intelligence_router,
    hitl_router
)


logger = structlog.get_logger(__name__)


def register_reactive_fabric_routes(app: FastAPI) -> None:
    """
    Register reactive fabric routers with API Gateway.
    
    Registers all Phase 1 reactive fabric endpoints:
    - Deception Assets (Sacrifice Island management)
    - Threat Events (passive observation pipeline)
    - Intelligence Reports (Phase 1 value delivery)
    - HITL Decisions (human authorization workflow)
    
    Args:
        app: FastAPI application instance
    
    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> register_reactive_fabric_routes(app)
    """
    logger.info("registering_reactive_fabric_routes")
    
    # Register Deception Asset router
    app.include_router(
        deception_router,
        prefix="/api/reactive-fabric",
        tags=["Reactive Fabric - Deception"]
    )
    logger.info("deception_router_registered", prefix="/api/reactive-fabric/deception")
    
    # Register Threat Event router
    app.include_router(
        threat_router,
        prefix="/api/reactive-fabric",
        tags=["Reactive Fabric - Threats"]
    )
    logger.info("threat_router_registered", prefix="/api/reactive-fabric/threats")
    
    # Register Intelligence router
    app.include_router(
        intelligence_router,
        prefix="/api/reactive-fabric",
        tags=["Reactive Fabric - Intelligence"]
    )
    logger.info("intelligence_router_registered", prefix="/api/reactive-fabric/intelligence")
    
    # Register HITL router
    app.include_router(
        hitl_router,
        prefix="/api/reactive-fabric",
        tags=["Reactive Fabric - HITL"]
    )
    logger.info("hitl_router_registered", prefix="/api/reactive-fabric/hitl")
    
    logger.info(
        "reactive_fabric_routes_registered",
        routers=["deception", "threats", "intelligence", "hitl"],
        phase="1",
        compliance="human_authorization_required"
    )


def get_reactive_fabric_info() -> dict:
    """
    Get reactive fabric module information.
    
    Returns:
        Module information dictionary
    """
    return {
        "module": "reactive_fabric",
        "version": "1.0.0-phase1",
        "phase": "1",
        "capabilities": {
            "deception_assets": {
                "enabled": True,
                "max_interaction_level": "MEDIUM",
                "human_approval_required": True
            },
            "threat_intelligence": {
                "enabled": True,
                "passive_only": True,
                "auto_enrichment": True
            },
            "intelligence_fusion": {
                "enabled": True,
                "ttp_discovery": True,
                "detection_rule_generation": True
            },
            "human_authorization": {
                "enabled": True,
                "rubber_stamp_detection": True,
                "required_for_level3": True
            }
        },
        "constraints": {
            "phase1_active": True,
            "automated_response": False,
            "high_interaction_deception": False,
            "level4_actions": False
        },
        "endpoints": {
            "deception": "/api/reactive-fabric/deception",
            "threats": "/api/reactive-fabric/threats",
            "intelligence": "/api/reactive-fabric/intelligence",
            "hitl": "/api/reactive-fabric/hitl"
        }
    }
