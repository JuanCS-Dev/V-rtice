"""FASE 10: Cloud Coordinator Service - API Endpoints

Centralized brain for distributed organism.
Coordinates multiple edge agents in multi-tenant environment.

NO MOCKS - Production-ready cloud coordination API.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn
import logging

from coordinator_core import (
    CloudCoordinatorController,
    AgentHealth
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cloud Coordinator Service",
    description="FASE 10: Centralized coordination for distributed edge agents",
    version="1.0.0"
)

# Initialize controller
coordinator = CloudCoordinatorController(heartbeat_timeout=60.0)


# ========================
# Request/Response Models
# ========================

class AgentRegistrationRequest(BaseModel):
    """Register new edge agent."""
    agent_id: str = Field(..., description="Unique agent identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    host: str = Field(..., description="Agent host address")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class HeartbeatRequest(BaseModel):
    """Agent heartbeat."""
    agent_id: str = Field(..., description="Agent identifier")


class EventsIngestionRequest(BaseModel):
    """Ingest events from edge agent."""
    agent_id: str = Field(..., description="Agent identifier")
    events: List[Dict[str, Any]] = Field(..., description="Events to ingest")


# ===================
# API Endpoints
# ===================

@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    logger.info("🌐 Cloud Coordinator Service starting...")
    logger.info("✅ Cloud Coordinator Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks."""
    logger.info("👋 Cloud Coordinator Service shutting down...")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "cloud_coordinator",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/agents/register")
async def register_agent(request: AgentRegistrationRequest) -> Dict[str, Any]:
    """Register new edge agent.

    Args:
        request: Agent registration details

    Returns:
        Registration confirmation
    """
    try:
        agent = coordinator.register_agent(
            agent_id=request.agent_id,
            tenant_id=request.tenant_id,
            host=request.host,
            metadata=request.metadata or {}
        )

        return {
            "status": "registered",
            "agent_id": agent.agent_id,
            "tenant_id": agent.tenant_id,
            "registered_at": agent.registered_at.isoformat(),
            "health": agent.health.value
        }
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/agents/heartbeat")
async def agent_heartbeat(request: HeartbeatRequest) -> Dict[str, Any]:
    """Record agent heartbeat.

    Args:
        request: Heartbeat request

    Returns:
        Heartbeat acknowledgment
    """
    success = coordinator.heartbeat(request.agent_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {request.agent_id} not found"
        )

    return {
        "status": "acknowledged",
        "agent_id": request.agent_id,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/events/ingest")
async def ingest_events(request: EventsIngestionRequest) -> Dict[str, Any]:
    """Ingest events from edge agent.

    Args:
        request: Events ingestion request

    Returns:
        Ingestion acknowledgment
    """
    try:
        coordinator.ingest_events(request.agent_id, request.events)

        return {
            "status": "ingested",
            "agent_id": request.agent_id,
            "events_count": len(request.events),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Event ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.get("/agents/status")
async def get_agents_status() -> Dict[str, Any]:
    """Get status of all registered agents.

    Returns:
        Agents status summary
    """
    # Check agent health
    coordinator.check_agent_health()

    agents_list = []
    for agent_id, agent in coordinator.agents.items():
        agents_list.append({
            "agent_id": agent.agent_id,
            "tenant_id": agent.tenant_id,
            "host": agent.host,
            "health": agent.health.value,
            "events_received": agent.events_received,
            "events_processed": agent.events_processed,
            "last_heartbeat": agent.last_heartbeat.isoformat(),
            "is_alive": agent.is_alive()
        })

    return {
        "total_agents": len(coordinator.agents),
        "agents": agents_list,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/coordinator/status")
async def get_coordinator_status() -> Dict[str, Any]:
    """Get coordinator status.

    Returns:
        Coordinator status
    """
    return coordinator.get_status()


@app.get("/agents/{agent_id}")
async def get_agent_details(agent_id: str) -> Dict[str, Any]:
    """Get details of specific agent.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent details
    """
    if agent_id not in coordinator.agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    agent = coordinator.agents[agent_id]

    return {
        "agent_id": agent.agent_id,
        "tenant_id": agent.tenant_id,
        "host": agent.host,
        "health": agent.health.value,
        "registered_at": agent.registered_at.isoformat(),
        "last_heartbeat": agent.last_heartbeat.isoformat(),
        "events_received": agent.events_received,
        "events_processed": agent.events_processed,
        "avg_latency_ms": agent.avg_latency_ms,
        "metadata": agent.metadata,
        "is_alive": agent.is_alive()
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8051)
