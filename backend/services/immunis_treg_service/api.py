"""FASE 9: Regulatory T-Cells (Treg) Service - FastAPI

REST API for false positive suppression and tolerance learning.

NO MOCKS - Production-ready immune tolerance interface.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from treg_core import (
    AlertSeverity,
    SecurityAlert,
    TregController,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global service instance
treg_controller: Optional[TregController] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global treg_controller

    logger.info("Initializing Regulatory T-Cells (Treg) Service...")

    # Initialize Treg controller
    treg_controller = TregController(tolerance_threshold=0.7, suppression_threshold=0.7)

    logger.info("Treg controller initialized")

    yield

    logger.info("Shutting down Treg Service...")


app = FastAPI(
    title="VÉRTICE Regulatory T-Cells (Treg) Service",
    description="False positive suppression and immune tolerance learning",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# Request/Response Models
# ============================================================================


class SecurityAlertRequest(BaseModel):
    """Request to evaluate security alert."""

    alert_id: str = Field(..., description="Unique alert ID")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (default: now)")
    alert_type: str = Field(..., description="Alert type (port_scan, malware, etc)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    source_ip: str = Field(..., description="Source IP address")
    target_asset: str = Field(..., description="Target asset identifier")
    indicators: List[str] = Field(..., description="Threat indicators")
    raw_score: float = Field(..., ge=0.0, le=1.0, description="Detection score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SuppressionDecisionResponse(BaseModel):
    """Response with suppression decision."""

    alert_id: str
    decision: str
    confidence: float
    suppression_score: float
    rationale: List[str]
    tolerance_profiles_consulted: List[str]
    timestamp: str


class EntityObservationRequest(BaseModel):
    """Request to observe entity behavior."""

    entity_id: str = Field(..., description="Entity identifier")
    entity_type: str = Field(..., description="Entity type (source_ip, user, asset)")
    behavioral_features: Dict[str, float] = Field(..., description="Behavioral features (numeric)")


class FeedbackRequest(BaseModel):
    """Request to provide feedback on alert."""

    alert_id: str = Field(..., description="Alert identifier")
    was_false_positive: bool = Field(..., description="Whether alert was false positive")
    entities_involved: List[Dict[str, str]] = Field(
        ..., description="Entities involved (list of {entity_id, entity_type})"
    )


class ToleranceProfileResponse(BaseModel):
    """Response with tolerance profile."""

    entity_id: str
    entity_type: str
    first_seen: str
    last_seen: str
    total_observations: int
    alert_history_count: int
    false_positive_count: int
    true_positive_count: int
    tolerance_score: float
    updated_at: str


class StatusResponse(BaseModel):
    """Service status response."""

    service: str
    status: str
    components: Dict[str, Any]
    timestamp: str


# ============================================================================
# Alert Evaluation Endpoints
# ============================================================================


@app.post("/alert/evaluate", response_model=SuppressionDecisionResponse)
async def evaluate_alert(request: SecurityAlertRequest):
    """Evaluate security alert for potential suppression.

    Args:
        request: Alert details

    Returns:
        Suppression decision
    """
    if treg_controller is None:
        raise HTTPException(status_code=503, detail="Treg controller not initialized")

    try:
        # Parse severity
        try:
            severity = AlertSeverity(request.severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {request.severity}")

        # Parse timestamp
        if request.timestamp:
            timestamp = datetime.fromisoformat(request.timestamp)
        else:
            timestamp = datetime.now()

        # Create security alert
        alert = SecurityAlert(
            alert_id=request.alert_id,
            timestamp=timestamp,
            alert_type=request.alert_type,
            severity=severity,
            source_ip=request.source_ip,
            target_asset=request.target_asset,
            indicators=request.indicators,
            raw_score=request.raw_score,
            metadata=request.metadata,
        )

        # Process through Treg
        decision = treg_controller.process_alert(alert)

        return SuppressionDecisionResponse(
            alert_id=decision.alert_id,
            decision=decision.decision.value,
            confidence=decision.confidence,
            suppression_score=decision.suppression_score,
            rationale=decision.rationale,
            tolerance_profiles_consulted=decision.tolerance_profiles_consulted,
            timestamp=decision.timestamp.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Tolerance Learning Endpoints
# ============================================================================


@app.post("/tolerance/observe")
async def observe_entity_behavior(request: EntityObservationRequest):
    """Observe entity behavior for tolerance learning.

    Args:
        request: Entity observation

    Returns:
        Observation confirmation
    """
    if treg_controller is None:
        raise HTTPException(status_code=503, detail="Treg controller not initialized")

    try:
        # Observe entity
        treg_controller.observe_entity(
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            behavioral_features=request.behavioral_features,
        )

        return {
            "status": "success",
            "entity_id": request.entity_id,
            "entity_type": request.entity_type,
            "features_count": len(request.behavioral_features),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error observing entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tolerance/profile/{entity_id}", response_model=ToleranceProfileResponse)
async def get_tolerance_profile(entity_id: str):
    """Retrieve tolerance profile for entity.

    Args:
        entity_id: Entity identifier

    Returns:
        Tolerance profile
    """
    if treg_controller is None:
        raise HTTPException(status_code=503, detail="Treg controller not initialized")

    try:
        # Get profile
        if entity_id not in treg_controller.tolerance_learner.tolerance_profiles:
            raise HTTPException(status_code=404, detail=f"No tolerance profile for {entity_id}")

        profile = treg_controller.tolerance_learner.tolerance_profiles[entity_id]

        return ToleranceProfileResponse(
            entity_id=profile.entity_id,
            entity_type=profile.entity_type,
            first_seen=profile.first_seen.isoformat(),
            last_seen=profile.last_seen.isoformat(),
            total_observations=profile.total_observations,
            alert_history_count=len(profile.alert_history),
            false_positive_count=profile.false_positive_count,
            true_positive_count=profile.true_positive_count,
            tolerance_score=profile.tolerance_score,
            updated_at=profile.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tolerance profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tolerance/profiles", response_model=List[ToleranceProfileResponse])
async def list_tolerance_profiles(
    min_tolerance: Optional[float] = None,
    max_tolerance: Optional[float] = None,
    limit: int = 100,
):
    """List tolerance profiles with optional filtering.

    Args:
        min_tolerance: Minimum tolerance score
        max_tolerance: Maximum tolerance score
        limit: Maximum number of profiles to return

    Returns:
        List of tolerance profiles
    """
    if treg_controller is None:
        raise HTTPException(status_code=503, detail="Treg controller not initialized")

    try:
        profiles = []

        for profile in treg_controller.tolerance_learner.tolerance_profiles.values():
            # Apply filters
            if min_tolerance is not None and profile.tolerance_score < min_tolerance:
                continue
            if max_tolerance is not None and profile.tolerance_score > max_tolerance:
                continue

            profiles.append(
                ToleranceProfileResponse(
                    entity_id=profile.entity_id,
                    entity_type=profile.entity_type,
                    first_seen=profile.first_seen.isoformat(),
                    last_seen=profile.last_seen.isoformat(),
                    total_observations=profile.total_observations,
                    alert_history_count=len(profile.alert_history),
                    false_positive_count=profile.false_positive_count,
                    true_positive_count=profile.true_positive_count,
                    tolerance_score=profile.tolerance_score,
                    updated_at=profile.updated_at.isoformat(),
                )
            )

            if len(profiles) >= limit:
                break

        return profiles

    except Exception as e:
        logger.error(f"Error listing tolerance profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Feedback Endpoints
# ============================================================================


@app.post("/feedback/provide")
async def provide_feedback(request: FeedbackRequest):
    """Provide feedback on alert outcome for learning.

    Args:
        request: Feedback details

    Returns:
        Feedback confirmation
    """
    if treg_controller is None:
        raise HTTPException(status_code=503, detail="Treg controller not initialized")

    try:
        # Convert entities to tuples
        entities = [(entity["entity_id"], entity["entity_type"]) for entity in request.entities_involved]

        # Provide feedback
        treg_controller.provide_feedback(
            alert_id=request.alert_id,
            was_false_positive=request.was_false_positive,
            entities_involved=entities,
        )

        return {
            "status": "success",
            "alert_id": request.alert_id,
            "was_false_positive": request.was_false_positive,
            "entities_updated": len(entities),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error providing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "immunis_treg",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get comprehensive service status.

    Returns:
        Service status
    """
    if treg_controller is None:
        raise HTTPException(status_code=503, detail="Treg controller not initialized")

    try:
        status = treg_controller.get_status()

        return StatusResponse(
            service="immunis_treg",
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
    if treg_controller is None:
        raise HTTPException(status_code=503, detail="Treg controller not initialized")

    try:
        status = treg_controller.get_status()

        learner = status["tolerance_learner"]
        suppressor = status["fp_suppressor"]

        return {
            "service": "immunis_treg",
            "timestamp": datetime.now().isoformat(),
            "alerts_processed": status["alerts_processed"],
            "tolerance_profiles": learner["total_profiles"],
            "high_tolerance_entities": learner["high_tolerance_entities"],
            "low_tolerance_entities": learner["low_tolerance_entities"],
            "alerts_suppressed": suppressor["alerts_suppressed"],
            "alerts_allowed": suppressor["alerts_allowed"],
            "suppression_rate": suppressor["suppression_rate"],
        }

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8018, log_level="info", access_log=True)
