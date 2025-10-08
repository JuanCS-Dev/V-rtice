"""FASE 9: Memory Consolidation Service - FastAPI

REST API for long-term memory consolidation with circadian rhythm.

NO MOCKS - Production-ready memory consolidation interface.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from consolidation_core import (
    MemoryConsolidator,
    SecurityEvent,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global service instance
consolidator: Optional[MemoryConsolidator] = None
consolidation_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global consolidator, consolidation_task

    logger.info("Initializing Memory Consolidation Service...")

    # Initialize consolidator
    consolidator = MemoryConsolidator(stm_capacity=10000, consolidation_threshold=0.6, pruning_threshold=0.3)

    # Start background consolidation task (circadian rhythm)
    consolidation_task = asyncio.create_task(run_consolidation_loop())

    logger.info("Memory consolidation service initialized with circadian rhythm")

    yield

    # Stop background task
    if consolidation_task:
        consolidation_task.cancel()
        try:
            await consolidation_task
        except asyncio.CancelledError:
            pass

    logger.info("Shutting down Memory Consolidation Service...")


async def run_consolidation_loop():
    """Background task for periodic consolidation (circadian rhythm).

    Runs consolidation every 6 hours (4 cycles per day).
    """
    global consolidator

    consolidation_interval_hours = 6

    logger.info(f"Consolidation loop started (interval: {consolidation_interval_hours}h)")

    while True:
        try:
            # Wait for interval
            await asyncio.sleep(consolidation_interval_hours * 3600)

            # Run consolidation cycle
            if consolidator:
                logger.info("Running scheduled consolidation cycle...")
                cycle = consolidator.run_consolidation_cycle()
                logger.info(
                    f"Consolidation cycle {cycle.cycle_id} completed: "
                    f"{cycle.memories_consolidated} consolidated, "
                    f"{cycle.memories_pruned} pruned"
                )

        except asyncio.CancelledError:
            logger.info("Consolidation loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in consolidation loop: {e}")
            # Continue loop despite errors
            await asyncio.sleep(60)


app = FastAPI(
    title="VÉRTICE Memory Consolidation Service",
    description="Long-term memory consolidation with circadian rhythm",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# Request/Response Models
# ============================================================================


class SecurityEventRequest(BaseModel):
    """Request to ingest security event."""

    event_id: str = Field(..., description="Unique event ID")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (default: now)")
    event_type: str = Field(..., description="Event type")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity (0-1)")
    source: str = Field(..., description="Source IP or entity")
    target: str = Field(..., description="Target asset")
    indicators: List[str] = Field(..., description="Threat indicators")
    outcome: Optional[str] = Field(None, description="Event outcome (blocked, allowed, etc)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ShortTermMemoryResponse(BaseModel):
    """Response with short-term memory details."""

    event_id: str
    importance_score: float
    access_count: int
    created_at: str
    status: str


class LongTermMemoryResponse(BaseModel):
    """Response with long-term memory details."""

    memory_id: str
    pattern_type: str
    description: str
    consolidated_events_count: int
    importance: str
    created_at: str
    last_accessed: str
    access_count: int
    strength: float


class ConsolidationCycleResponse(BaseModel):
    """Response with consolidation cycle details."""

    cycle_id: str
    start_time: str
    end_time: Optional[str]
    events_processed: int
    memories_consolidated: int
    memories_pruned: int
    patterns_extracted: int
    status: str


class StatusResponse(BaseModel):
    """Service status response."""

    service: str
    status: str
    components: Dict[str, Any]
    timestamp: str


# ============================================================================
# Event Ingestion Endpoints
# ============================================================================


@app.post("/event/ingest")
async def ingest_event(request: SecurityEventRequest):
    """Ingest security event into short-term memory.

    Args:
        request: Event details

    Returns:
        Ingestion confirmation
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        # Parse timestamp
        if request.timestamp:
            timestamp = datetime.fromisoformat(request.timestamp)
        else:
            timestamp = datetime.now()

        # Create security event
        event = SecurityEvent(
            event_id=request.event_id,
            timestamp=timestamp,
            event_type=request.event_type,
            severity=request.severity,
            source=request.source,
            target=request.target,
            indicators=request.indicators,
            outcome=request.outcome,
            metadata=request.metadata,
        )

        # Ingest into consolidator
        consolidator.ingest_event(event)

        # Get importance score
        if request.event_id in consolidator.short_term_memory:
            stm = consolidator.short_term_memory[request.event_id]
            importance = stm.importance_score
        else:
            importance = 0.0

        return {
            "status": "success",
            "event_id": request.event_id,
            "importance_score": importance,
            "stm_size": len(consolidator.short_term_memory),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error ingesting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/event/batch_ingest")
async def batch_ingest_events(events: List[SecurityEventRequest]):
    """Batch ingest multiple security events.

    Args:
        events: List of events

    Returns:
        Batch ingestion confirmation
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        ingested = 0

        for request in events:
            # Parse timestamp
            if request.timestamp:
                timestamp = datetime.fromisoformat(request.timestamp)
            else:
                timestamp = datetime.now()

            # Create and ingest event
            event = SecurityEvent(
                event_id=request.event_id,
                timestamp=timestamp,
                event_type=request.event_type,
                severity=request.severity,
                source=request.source,
                target=request.target,
                indicators=request.indicators,
                outcome=request.outcome,
                metadata=request.metadata,
            )

            consolidator.ingest_event(event)
            ingested += 1

        return {
            "status": "success",
            "events_ingested": ingested,
            "stm_size": len(consolidator.short_term_memory),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in batch ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Memory Query Endpoints
# ============================================================================


@app.get("/memory/short_term", response_model=List[ShortTermMemoryResponse])
async def list_short_term_memories(min_importance: Optional[float] = None, limit: int = 100):
    """List short-term memories.

    Args:
        min_importance: Minimum importance threshold
        limit: Maximum number of memories to return

    Returns:
        List of short-term memories
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        memories = []

        for stm in consolidator.short_term_memory.values():
            # Apply filter
            if min_importance is not None and stm.importance_score < min_importance:
                continue

            memories.append(
                ShortTermMemoryResponse(
                    event_id=stm.event.event_id,
                    importance_score=stm.importance_score,
                    access_count=stm.access_count,
                    created_at=stm.created_at.isoformat(),
                    status=stm.status.value,
                )
            )

            if len(memories) >= limit:
                break

        return memories

    except Exception as e:
        logger.error(f"Error listing STM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/long_term", response_model=List[LongTermMemoryResponse])
async def list_long_term_memories(
    pattern_type: Optional[str] = None,
    min_strength: Optional[float] = None,
    limit: int = 100,
):
    """List long-term memories.

    Args:
        pattern_type: Filter by pattern type
        min_strength: Minimum memory strength
        limit: Maximum number of memories to return

    Returns:
        List of long-term memories
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        memories = []

        for ltm in consolidator.long_term_memory.values():
            # Apply filters
            if pattern_type and ltm.pattern_type != pattern_type:
                continue
            if min_strength is not None and ltm.strength < min_strength:
                continue

            memories.append(
                LongTermMemoryResponse(
                    memory_id=ltm.memory_id,
                    pattern_type=ltm.pattern_type,
                    description=ltm.description,
                    consolidated_events_count=len(ltm.consolidated_events),
                    importance=ltm.importance.value,
                    created_at=ltm.created_at.isoformat(),
                    last_accessed=ltm.last_accessed.isoformat(),
                    access_count=ltm.access_count,
                    strength=ltm.strength,
                )
            )

            if len(memories) >= limit:
                break

        return memories

    except Exception as e:
        logger.error(f"Error listing LTM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/long_term/{memory_id}", response_model=LongTermMemoryResponse)
async def get_long_term_memory(memory_id: str):
    """Retrieve specific long-term memory.

    Args:
        memory_id: Memory identifier

    Returns:
        Long-term memory details
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        # Access memory (strengthens it)
        ltm = consolidator.access_memory(memory_id)

        if ltm is None:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        return LongTermMemoryResponse(
            memory_id=ltm.memory_id,
            pattern_type=ltm.pattern_type,
            description=ltm.description,
            consolidated_events_count=len(ltm.consolidated_events),
            importance=ltm.importance.value,
            created_at=ltm.created_at.isoformat(),
            last_accessed=ltm.last_accessed.isoformat(),
            access_count=ltm.access_count,
            strength=ltm.strength,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Consolidation Control Endpoints
# ============================================================================


@app.post("/consolidation/trigger", response_model=ConsolidationCycleResponse)
async def trigger_consolidation():
    """Manually trigger consolidation cycle.

    Returns:
        Consolidation cycle details
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        logger.info("Manual consolidation trigger received")

        # Run consolidation
        cycle = consolidator.run_consolidation_cycle()

        return ConsolidationCycleResponse(
            cycle_id=cycle.cycle_id,
            start_time=cycle.start_time.isoformat(),
            end_time=cycle.end_time.isoformat() if cycle.end_time else None,
            events_processed=cycle.events_processed,
            memories_consolidated=cycle.memories_consolidated,
            memories_pruned=cycle.memories_pruned,
            patterns_extracted=cycle.patterns_extracted,
            status=cycle.status,
        )

    except Exception as e:
        logger.error(f"Error triggering consolidation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consolidation/history", response_model=List[ConsolidationCycleResponse])
async def get_consolidation_history(limit: int = 10):
    """Get consolidation cycle history.

    Args:
        limit: Maximum number of cycles to return

    Returns:
        List of consolidation cycles
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        cycles = []

        # Get recent cycles (newest first)
        recent_cycles = list(reversed(consolidator.consolidation_cycles[-limit:]))

        for cycle in recent_cycles:
            cycles.append(
                ConsolidationCycleResponse(
                    cycle_id=cycle.cycle_id,
                    start_time=cycle.start_time.isoformat(),
                    end_time=cycle.end_time.isoformat() if cycle.end_time else None,
                    events_processed=cycle.events_processed,
                    memories_consolidated=cycle.memories_consolidated,
                    memories_pruned=cycle.memories_pruned,
                    patterns_extracted=cycle.patterns_extracted,
                    status=cycle.status,
                )
            )

        return cycles

    except Exception as e:
        logger.error(f"Error getting consolidation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "memory_consolidation",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get comprehensive service status.

    Returns:
        Service status
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        status = consolidator.get_status()

        return StatusResponse(
            service="memory_consolidation",
            status="operational",
            components=status,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """Get comprehensive statistics.

    Returns:
        Service statistics
    """
    if consolidator is None:
        raise HTTPException(status_code=503, detail="Consolidator not initialized")

    try:
        status = consolidator.get_status()

        return {
            "service": "memory_consolidation",
            "timestamp": datetime.now().isoformat(),
            "events_received": status["events_received"],
            "stm_size": status["stm_size"],
            "ltm_size": status["ltm_size"],
            "consolidation_cycles": status["consolidation_cycles"],
            "patterns_extracted": status["pattern_extractor"]["patterns_extracted"],
        }

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8019, log_level="info", access_log=True)
