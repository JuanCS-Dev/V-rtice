"""Immunis Neutrophil Service - FastAPI Wrapper

Exposes Neutrophil rapid response capabilities via REST API.

Bio-inspired first responder:
- Lightweight, ephemeral (24h TTL)
- Rapid threat response via RTE integration
- Auto-scaling based on threat load

Endpoints:
- POST /respond - Initiate rapid response to threat
- GET /status - Get neutrophil status
- GET /response/{threat_id} - Get response status for specific threat
- GET /health - Health check
- POST /self_destruct - Manual self-destruction
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from neutrophil_core import NeutrophilCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Immunis Neutrophil Service",
    version="1.0.0",
    description="Bio-inspired rapid threat response service (ephemeral, first responder)",
)

# Initialize Neutrophil core with unique ID
neutrophil_id = f"neutrophil-{uuid.uuid4().hex[:8]}"
neutrophil_core = NeutrophilCore(
    neutrophil_id=neutrophil_id,
    ttl_hours=24,
    rte_endpoint="http://vertice-rte:8026",  # Updated endpoint
)


class ThreatRequest(BaseModel):
    """Request model for threat response.

    Attributes:
        threat_id (str): Unique threat identifier
        threat_type (str): Type of threat (malware, intrusion, process_anomaly, etc.)
        severity (str): Threat severity (critical, high, medium, low)
        details (Dict[str, Any]): Threat details and metadata
    """

    threat_id: str
    threat_type: str
    severity: str
    details: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Neutrophil Service."""
    logger.info(f"🦠 Starting Immunis Neutrophil Service (ID: {neutrophil_id})...")
    logger.info(f"   Birth time: {neutrophil_core.birth_time.isoformat()}")
    logger.info(f"   Death time: {neutrophil_core.death_time.isoformat()}")
    logger.info(f"   TTL: {neutrophil_core.remaining_lifetime_seconds() / 3600:.1f} hours")
    logger.info("✅ Neutrophil Service started successfully - Ready for rapid response!")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Neutrophil Service."""
    logger.info(f"👋 Shutting down Immunis Neutrophil Service (ID: {neutrophil_id})...")

    # Generate destruction summary
    if neutrophil_core.is_alive():
        summary = await neutrophil_core.self_destruct()
        logger.info(f"   Threats engaged: {summary['threats_engaged']}")
        logger.info(f"   Actions taken: {summary['actions_taken']}")
        logger.info(f"   Lifetime: {summary['lifetime_hours']:.1f}h")

    logger.info("🛑 Neutrophil Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status with lifecycle information
    """
    is_alive = neutrophil_core.is_alive()

    return {
        "status": "healthy" if is_alive else "expired",
        "service": "immunis_neutrophil",
        "neutrophil_id": neutrophil_id,
        "is_alive": is_alive,
        "remaining_lifetime_hours": neutrophil_core.remaining_lifetime_seconds() / 3600,
        "threats_engaged": len(neutrophil_core.threats_engaged),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed neutrophil status.

    Returns:
        Dict[str, Any]: Detailed status information
    """
    return await neutrophil_core.get_status()


@app.post("/respond")
async def respond_to_threat(request: ThreatRequest) -> Dict[str, Any]:
    """Initiate rapid response to threat.

    This is the primary endpoint for threat response. When a threat is detected,
    the Neutrophil will:
    1. Determine appropriate action based on threat type and severity
    2. Execute action via RTE (Reflex Triage Engine)
    3. Record engagement for tracking

    Args:
        request (ThreatRequest): Threat details and metadata

    Returns:
        Dict[str, Any]: Response outcome with action taken and timing

    Raises:
        HTTPException: If neutrophil is expired or response fails
    """
    try:
        if not neutrophil_core.is_alive():
            raise HTTPException(
                status_code=410,  # Gone
                detail=f"Neutrophil {neutrophil_id} has expired (TTL exceeded)",
            )

        logger.info(f"Received threat response request: {request.threat_id}")

        engagement = await neutrophil_core.initiate_rapid_response(
            threat_id=request.threat_id,
            threat_type=request.threat_type,
            severity=request.severity,
            details=request.details,
        )

        return {
            "status": "success",
            "neutrophil_id": neutrophil_id,
            "engagement": engagement,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error responding to threat {request.threat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/response/{threat_id}")
async def get_response_status(threat_id: str) -> Dict[str, Any]:
    """Get status of response to specific threat.

    Args:
        threat_id (str): Threat ID to query

    Returns:
        Dict[str, Any]: Response status or 404 if not found

    Raises:
        HTTPException: If threat_id not found
    """
    status = await neutrophil_core.get_response_status(threat_id)

    if status is None:
        raise HTTPException(status_code=404, detail=f"No response found for threat {threat_id}")

    return {
        "status": "success",
        "threat_id": threat_id,
        "response_data": status,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/self_destruct")
async def trigger_self_destruct() -> Dict[str, Any]:
    """Manual self-destruction endpoint.

    Useful for:
    - Emergency shutdown
    - Resource cleanup
    - Testing TTL behavior

    Returns:
        Dict[str, Any]: Destruction summary with statistics

    Note:
        After calling this, the neutrophil will no longer respond to threats
    """
    logger.warning(f"Manual self-destruct triggered for neutrophil {neutrophil_id}")

    summary = await neutrophil_core.self_destruct()

    return {
        "status": "success",
        "message": "Neutrophil self-destructed",
        "summary": summary,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get operational metrics.

    Returns:
        Dict[str, Any]: Performance and operational metrics
    """
    status = await neutrophil_core.get_status()

    return {
        "service": "immunis_neutrophil",
        "neutrophil_id": neutrophil_id,
        "metrics": {
            "is_alive": status["is_alive"],
            "remaining_lifetime_hours": status["remaining_lifetime_seconds"] / 3600,
            "total_threats_engaged": status["threats_engaged"],
            "total_actions_taken": status["actions_taken"],
            "average_response_time_ms": (
                sum(e["response_time_ms"] for e in neutrophil_core.threats_engaged)
                / len(neutrophil_core.threats_engaged)
                if neutrophil_core.threats_engaged
                else 0
            ),
        },
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8013)
