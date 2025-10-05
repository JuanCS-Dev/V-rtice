"""FASE 9: Adaptive Immunity Service - FastAPI

REST API for adaptive immunity with antibody diversification and affinity maturation.

NO MOCKS - Production-ready adaptive learning interface.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import base64

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

from adaptive_core import (
    AdaptiveImmunityController,
    ThreatSample,
    AntibodyType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instance
immunity_controller: Optional[AdaptiveImmunityController] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global immunity_controller

    logger.info("Initializing Adaptive Immunity Service...")

    # Initialize controller
    immunity_controller = AdaptiveImmunityController(
        initial_repertoire_size=100,
        mutation_rate=0.1,
        expansion_threshold=0.8
    )

    logger.info("Adaptive immunity controller initialized")

    yield

    logger.info("Shutting down Adaptive Immunity Service...")


app = FastAPI(
    title="VÉRTICE Adaptive Immunity Service",
    description="Antibody diversification and affinity maturation for adaptive threat detection",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ThreatSampleRequest(BaseModel):
    """Request to submit threat sample."""
    sample_id: str = Field(..., description="Unique sample ID")
    threat_family: str = Field(..., description="Threat family (malware, exploit, etc)")
    features: Dict[str, float] = Field(..., description="Numerical features")
    raw_data: str = Field(..., description="Base64-encoded raw data")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity (0-1)")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (default: now)")


class AntibodyResponse(BaseModel):
    """Response with antibody details."""
    antibody_id: str
    antibody_type: str
    target_family: str
    affinity_score: float
    generation: int
    parent_id: Optional[str]
    created_at: str
    match_count: int
    true_positive_count: int
    false_positive_count: int


class ClonalExpansionResponse(BaseModel):
    """Response with clonal expansion details."""
    expansion_id: str
    parent_antibody_id: str
    clones_created: int
    reason: str
    timestamp: str


class MaturationEventResponse(BaseModel):
    """Response with maturation event details."""
    event_id: str
    antibody_id: str
    mutation_type: str
    affinity_before: float
    affinity_after: float
    timestamp: str


class FeedbackRequest(BaseModel):
    """Request to provide detection feedback."""
    antibody_id: str = Field(..., description="Antibody that made detection")
    detections: Dict[str, bool] = Field(
        ...,
        description="Sample ID -> was_correct (true if correct detection)"
    )


class StatusResponse(BaseModel):
    """Service status response."""
    service: str
    status: str
    components: Dict[str, Any]
    timestamp: str


# ============================================================================
# Repertoire Initialization Endpoints
# ============================================================================

@app.post("/repertoire/initialize")
async def initialize_repertoire(samples: List[ThreatSampleRequest]):
    """Initialize antibody repertoire from threat samples.

    Args:
        samples: List of threat samples for training

    Returns:
        Initialization confirmation
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        # Convert requests to threat samples
        threat_samples = []

        for request in samples:
            # Decode raw data
            try:
                raw_data = base64.b64decode(request.raw_data)
            except Exception as e:
                logger.warning(f"Failed to decode raw_data for {request.sample_id}: {e}")
                raw_data = b""

            # Parse timestamp
            if request.timestamp:
                timestamp = datetime.fromisoformat(request.timestamp)
            else:
                timestamp = datetime.now()

            sample = ThreatSample(
                sample_id=request.sample_id,
                threat_family=request.threat_family,
                features=request.features,
                raw_data=raw_data,
                severity=request.severity,
                timestamp=timestamp
            )

            threat_samples.append(sample)

        # Initialize repertoire
        immunity_controller.initialize_repertoire(threat_samples)

        return {
            "status": "success",
            "samples_processed": len(threat_samples),
            "antibody_pool_size": len(immunity_controller.antibody_pool),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error initializing repertoire: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/repertoire/status")
async def get_repertoire_status():
    """Get repertoire status.

    Returns:
        Repertoire status
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        return {
            "repertoire_initialized": immunity_controller.repertoire_initialized,
            "antibody_pool_size": len(immunity_controller.antibody_pool),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting repertoire status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Antibody Query Endpoints
# ============================================================================

@app.get("/antibody/list", response_model=List[AntibodyResponse])
async def list_antibodies(
    target_family: Optional[str] = None,
    min_affinity: Optional[float] = None,
    limit: int = 100
):
    """List antibodies with optional filtering.

    Args:
        target_family: Filter by target family
        min_affinity: Minimum affinity threshold
        limit: Maximum number to return

    Returns:
        List of antibodies
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        antibodies = []

        for antibody in immunity_controller.antibody_pool.values():
            # Apply filters
            if target_family and antibody.target_family != target_family:
                continue
            if min_affinity is not None and antibody.affinity_score < min_affinity:
                continue

            antibodies.append(AntibodyResponse(
                antibody_id=antibody.antibody_id,
                antibody_type=antibody.antibody_type.value,
                target_family=antibody.target_family,
                affinity_score=antibody.affinity_score,
                generation=antibody.generation,
                parent_id=antibody.parent_id,
                created_at=antibody.created_at.isoformat(),
                match_count=antibody.match_count,
                true_positive_count=antibody.true_positive_count,
                false_positive_count=antibody.false_positive_count
            ))

            if len(antibodies) >= limit:
                break

        return antibodies

    except Exception as e:
        logger.error(f"Error listing antibodies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/antibody/{antibody_id}", response_model=AntibodyResponse)
async def get_antibody(antibody_id: str):
    """Get specific antibody details.

    Args:
        antibody_id: Antibody identifier

    Returns:
        Antibody details
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        if antibody_id not in immunity_controller.antibody_pool:
            raise HTTPException(
                status_code=404,
                detail=f"Antibody {antibody_id} not found"
            )

        antibody = immunity_controller.antibody_pool[antibody_id]

        return AntibodyResponse(
            antibody_id=antibody.antibody_id,
            antibody_type=antibody.antibody_type.value,
            target_family=antibody.target_family,
            affinity_score=antibody.affinity_score,
            generation=antibody.generation,
            parent_id=antibody.parent_id,
            created_at=antibody.created_at.isoformat(),
            match_count=antibody.match_count,
            true_positive_count=antibody.true_positive_count,
            false_positive_count=antibody.false_positive_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting antibody: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Adaptive Learning Endpoints
# ============================================================================

@app.post("/learning/provide_feedback")
async def provide_feedback(feedback: List[FeedbackRequest]):
    """Provide detection feedback for adaptive learning.

    Args:
        feedback: List of feedback for antibodies

    Returns:
        Feedback confirmation
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        # Organize feedback
        feedback_data = {}

        for fb in feedback:
            feedback_data[fb.antibody_id] = fb.detections

            # Update antibody stats
            if fb.antibody_id in immunity_controller.antibody_pool:
                antibody = immunity_controller.antibody_pool[fb.antibody_id]

                for sample_id, was_correct in fb.detections.items():
                    antibody.match_count += 1

                    if was_correct:
                        antibody.true_positive_count += 1
                    else:
                        antibody.false_positive_count += 1

        return {
            "status": "success",
            "antibodies_updated": len(feedback_data),
            "total_detections": sum(len(fb.detections) for fb in feedback),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error providing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learning/run_maturation")
async def run_maturation_cycle(feedback_data: Dict[str, Dict[str, bool]]):
    """Run affinity maturation cycle.

    Args:
        feedback_data: Antibody ID -> {sample_id -> was_correct}

    Returns:
        Maturation cycle results
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        logger.info("Running maturation cycle via API")

        # Get initial size
        initial_size = len(immunity_controller.antibody_pool)

        # Run maturation
        immunity_controller.run_maturation_cycle(feedback_data)

        # Get final size
        final_size = len(immunity_controller.antibody_pool)

        return {
            "status": "success",
            "antibodies_matured": len(feedback_data),
            "initial_pool_size": initial_size,
            "final_pool_size": final_size,
            "new_antibodies": final_size - initial_size,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error running maturation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learning/run_selection")
async def run_selection_cycle():
    """Run clonal selection cycle.

    Returns:
        Selection cycle results
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        logger.info("Running selection cycle via API")

        # Get initial size
        initial_size = len(immunity_controller.antibody_pool)

        # Run selection
        immunity_controller.run_selection_cycle()

        # Get final size
        final_size = len(immunity_controller.antibody_pool)

        return {
            "status": "success",
            "initial_pool_size": initial_size,
            "final_pool_size": final_size,
            "clones_created": final_size - initial_size,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error running selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# History Endpoints
# ============================================================================

@app.get("/history/maturation", response_model=List[MaturationEventResponse])
async def get_maturation_history(limit: int = 50):
    """Get affinity maturation event history.

    Args:
        limit: Maximum number of events to return

    Returns:
        List of maturation events
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        events = []

        # Get recent events (newest first)
        recent_events = list(reversed(
            immunity_controller.affinity_maturation_engine.maturation_events[-limit:]
        ))

        for event in recent_events:
            events.append(MaturationEventResponse(
                event_id=event.event_id,
                antibody_id=event.antibody_id,
                mutation_type=event.mutation_type,
                affinity_before=event.affinity_before,
                affinity_after=event.affinity_after,
                timestamp=event.timestamp.isoformat()
            ))

        return events

    except Exception as e:
        logger.error(f"Error getting maturation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/expansions", response_model=List[ClonalExpansionResponse])
async def get_expansion_history(limit: int = 50):
    """Get clonal expansion history.

    Args:
        limit: Maximum number of expansions to return

    Returns:
        List of expansions
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        expansions = []

        # Get recent expansions (newest first)
        recent_expansions = list(reversed(
            immunity_controller.clonal_selection_manager.expansions[-limit:]
        ))

        for expansion in recent_expansions:
            expansions.append(ClonalExpansionResponse(
                expansion_id=expansion.expansion_id,
                parent_antibody_id=expansion.parent_antibody_id,
                clones_created=expansion.clones_created,
                reason=expansion.reason,
                timestamp=expansion.timestamp.isoformat()
            ))

        return expansions

    except Exception as e:
        logger.error(f"Error getting expansion history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "adaptive_immunity",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get comprehensive service status.

    Returns:
        Service status
    """
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        status = immunity_controller.get_status()

        return StatusResponse(
            service="adaptive_immunity",
            status="operational",
            components=status,
            timestamp=datetime.now().isoformat()
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
    if immunity_controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")

    try:
        status = immunity_controller.get_status()

        # Compute aggregate stats
        total_matches = sum(
            ab.match_count
            for ab in immunity_controller.antibody_pool.values()
        )

        total_tp = sum(
            ab.true_positive_count
            for ab in immunity_controller.antibody_pool.values()
        )

        total_fp = sum(
            ab.false_positive_count
            for ab in immunity_controller.antibody_pool.values()
        )

        accuracy = total_tp / max(total_matches, 1)

        return {
            "service": "adaptive_immunity",
            "timestamp": datetime.now().isoformat(),
            "repertoire_initialized": status["repertoire_initialized"],
            "antibody_pool_size": status["antibody_pool_size"],
            "total_matches": total_matches,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "accuracy": accuracy,
            "maturation_events": status["affinity_maturation_engine"]["maturation_events"],
            "clonal_expansions": status["clonal_selection_manager"]["expansions_performed"]
        }

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8020,
        log_level="info",
        access_log=True
    )
