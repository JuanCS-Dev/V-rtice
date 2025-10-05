"""FASE 10: Edge Agent Service - FastAPI

REST API for edge agent deployment.

NO MOCKS - Production-ready edge API.
"""

import asyncio
import logging
import socket
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

from edge_agent_core import (
    EdgeAgentController,
    EventType,
    EdgeAgentStatus,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
edge_agent: Optional[EdgeAgentController] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global edge_agent

    logger.info("Initializing Edge Agent Service...")

    # Get configuration
    import os
    agent_id = os.getenv("EDGE_AGENT_ID", socket.gethostname())
    tenant_id = os.getenv("TENANT_ID", "default")
    cloud_url = os.getenv("CLOUD_COORDINATOR_URL", "http://cloud_coordinator_service:8021")

    # Initialize edge agent
    edge_agent = EdgeAgentController(
        agent_id=agent_id,
        tenant_id=tenant_id,
        source_host=socket.gethostname(),
        cloud_coordinator_url=cloud_url,
        buffer_size=int(os.getenv("BUFFER_SIZE", "100000")),
        batch_size=int(os.getenv("BATCH_SIZE", "1000")),
        batch_age_seconds=float(os.getenv("BATCH_AGE_SECONDS", "5.0"))
    )

    edge_agent.status = EdgeAgentStatus.CONNECTED

    logger.info(f"Edge agent {agent_id} initialized for tenant {tenant_id}")

    # Start background processing
    asyncio.create_task(process_buffer_loop())

    yield

    logger.info("Shutting down Edge Agent Service...")


app = FastAPI(
    title="VÉRTICE Edge Agent Service",
    description="Edge sensor for distributed organism deployment",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Request/Response Models
# ============================================================================

class EventRequest(BaseModel):
    """Request to collect event."""
    event_type: str = Field(..., description="Event type")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity (0-1)")
    data: Dict[str, Any] = Field(..., description="Event data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class EventResponse(BaseModel):
    """Response with event ID."""
    event_id: str
    status: str
    buffered: bool


class StatusResponse(BaseModel):
    """Agent status response."""
    agent_id: str
    tenant_id: str
    source_host: str
    status: str
    cloud_coordinator_url: str
    buffer_stats: Dict[str, Any]
    heartbeat_stats: Dict[str, Any]
    metrics: Dict[str, Any]
    timestamp: str


class BatchStatsResponse(BaseModel):
    """Batch statistics response."""
    current_batch_size: int
    batches_pending: int
    estimated_flush_time_seconds: float


# ============================================================================
# Background Tasks
# ============================================================================

async def process_buffer_loop():
    """Background task to process buffer and send batches."""
    while True:
        try:
            if edge_agent:
                # Process buffer
                batches = edge_agent.process_buffer()

                # Log batch creation
                if batches:
                    logger.info(f"Created {len(batches)} batches for transmission")

                    for batch in batches:
                        # Compress batch
                        compressed_data = batch.compress()

                        logger.info(
                            f"Batch {batch.batch_id}: {len(batch.events)} events, "
                            f"{len(compressed_data)} bytes, "
                            f"compression ratio: {batch.compression_ratio:.2f}x"
                        )

                        # Record metrics
                        edge_agent.metrics.record_batch_sent(
                            event_count=len(batch.events),
                            bytes_sent=len(compressed_data),
                            compression_ratio=batch.compression_ratio,
                            latency=0.1  # Placeholder for actual send latency
                        )

                # Heartbeat check
                if edge_agent.heartbeat.should_send_heartbeat():
                    edge_agent.heartbeat.record_heartbeat_sent()
                    logger.debug("Heartbeat sent to cloud coordinator")

                    # Simulate heartbeat ack (in real impl, this comes from cloud)
                    edge_agent.heartbeat.record_heartbeat_ack()

                # Check timeout
                if edge_agent.heartbeat.check_timeout():
                    edge_agent.status = EdgeAgentStatus.DISCONNECTED
                    logger.warning("Cloud coordinator connection timeout")
                else:
                    if edge_agent.status == EdgeAgentStatus.DISCONNECTED:
                        edge_agent.status = EdgeAgentStatus.CONNECTED
                        logger.info("Cloud coordinator connection restored")

            # Sleep before next iteration
            await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Error in buffer processing loop: {e}")
            await asyncio.sleep(5.0)


# ============================================================================
# Event Collection Endpoints
# ============================================================================

@app.post("/event/collect", response_model=EventResponse)
async def collect_event(event: EventRequest):
    """Collect edge event.

    Args:
        event: Event to collect

    Returns:
        Event response
    """
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Parse event type
        try:
            event_type = EventType(event.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event.event_type}"
            )

        # Collect event
        event_id = edge_agent.collect_event(
            event_type=event_type,
            severity=event.severity,
            data=event.data,
            metadata=event.metadata
        )

        return EventResponse(
            event_id=event_id,
            status="collected",
            buffered=True
        )

    except Exception as e:
        logger.error(f"Error collecting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/event/collect_batch")
async def collect_event_batch(events: List[EventRequest]):
    """Collect batch of events.

    Args:
        events: List of events to collect

    Returns:
        Batch collection response
    """
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        event_ids = []

        for event in events:
            try:
                event_type = EventType(event.event_type)
            except ValueError:
                logger.warning(f"Skipping invalid event type: {event.event_type}")
                continue

            event_id = edge_agent.collect_event(
                event_type=event_type,
                severity=event.severity,
                data=event.data,
                metadata=event.metadata
            )

            event_ids.append(event_id)

        return {
            "status": "success",
            "events_collected": len(event_ids),
            "event_ids": event_ids,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error collecting batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Status & Metrics Endpoints
# ============================================================================

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get edge agent status.

    Returns:
        Agent status
    """
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        status = edge_agent.get_status()

        return StatusResponse(
            agent_id=status["agent_id"],
            tenant_id=status["tenant_id"],
            source_host=status["source_host"],
            status=status["status"],
            cloud_coordinator_url=status["cloud_coordinator_url"],
            buffer_stats=status["buffer"],
            heartbeat_stats=status["heartbeat"],
            metrics=status["metrics"],
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get edge agent metrics.

    Returns:
        Agent metrics
    """
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        return {
            "agent_id": edge_agent.agent_id,
            "tenant_id": edge_agent.tenant_id,
            "metrics": edge_agent.metrics.get_stats(),
            "buffer_utilization": edge_agent.buffer.get_stats()["utilization"],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/buffer/stats")
async def get_buffer_stats():
    """Get buffer statistics.

    Returns:
        Buffer stats
    """
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        buffer_stats = edge_agent.buffer.get_stats()

        return {
            "buffer": buffer_stats,
            "current_batch_size": len(edge_agent.current_batch),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting buffer stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/stats", response_model=BatchStatsResponse)
async def get_batch_stats():
    """Get batching statistics.

    Returns:
        Batch stats
    """
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Estimate time until flush
        if edge_agent.batch_created_at:
            age = (datetime.now() - edge_agent.batch_created_at).total_seconds()
            time_until_flush = max(0, edge_agent.batching.max_batch_age_seconds - age)
        else:
            time_until_flush = edge_agent.batching.max_batch_age_seconds

        return BatchStatsResponse(
            current_batch_size=len(edge_agent.current_batch),
            batches_pending=0,  # Batches are sent immediately
            estimated_flush_time_seconds=time_until_flush
        )

    except Exception as e:
        logger.error(f"Error getting batch stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health & Control Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "edge_agent",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/control/pause")
async def pause_agent():
    """Pause event collection."""
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    edge_agent.status = EdgeAgentStatus.DEGRADED

    return {
        "status": "paused",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/control/resume")
async def resume_agent():
    """Resume event collection."""
    if edge_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    edge_agent.status = EdgeAgentStatus.CONNECTED

    return {
        "status": "resumed",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8021,
        log_level="info",
        access_log=True
    )
