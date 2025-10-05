"""FASE 8: Predictive Threat Hunting Service - FastAPI

REST API for attack prediction, vulnerability forecasting, and hunting recommendations.

NO MOCKS - Production-ready predictive intelligence interface.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

from predictive_core import (
    AttackPredictor,
    VulnerabilityForecaster,
    ProactiveHunter,
    ThreatEvent,
    ThreatType,
    ConfidenceLevel,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
attack_predictor: Optional[AttackPredictor] = None
vuln_forecaster: Optional[VulnerabilityForecaster] = None
proactive_hunter: Optional[ProactiveHunter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global attack_predictor, vuln_forecaster, proactive_hunter

    logger.info("Initializing Predictive Threat Hunting Service...")

    # Initialize all components
    attack_predictor = AttackPredictor()
    vuln_forecaster = VulnerabilityForecaster()
    proactive_hunter = ProactiveHunter()

    logger.info("All predictive components initialized")

    yield

    logger.info("Shutting down Predictive Threat Hunting Service...")


app = FastAPI(
    title="VÉRTICE Predictive Threat Hunting Service",
    description="Attack prediction and vulnerability forecasting for proactive defense",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ThreatEventRequest(BaseModel):
    """Request to ingest threat event."""
    event_id: str = Field(..., description="Unique event ID")
    threat_type: str = Field(..., description="Threat type (reconnaissance, exploitation, etc)")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (default: now)")
    source_ip: str = Field(..., description="Source IP address")
    target_asset: str = Field(..., description="Target asset identifier")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity score (0-1)")
    indicators: List[str] = Field(default_factory=list, description="Threat indicators")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PredictAttacksRequest(BaseModel):
    """Request for attack predictions."""
    time_horizon_hours: int = Field(24, ge=1, le=168, description="Prediction window (1-168 hours)")
    min_confidence: float = Field(0.6, ge=0.0, le=1.0, description="Minimum confidence threshold")


class AttackPredictionResponse(BaseModel):
    """Response with attack prediction."""
    prediction_id: str
    threat_type: str
    predicted_time: str
    predicted_targets: List[str]
    probability: float
    confidence: str
    indicators: List[str]
    recommended_actions: List[str]
    timestamp: str


class VulnerabilityRegistrationRequest(BaseModel):
    """Request to register vulnerability."""
    cve_id: str = Field(..., description="CVE identifier")
    cvss_score: float = Field(..., ge=0.0, le=10.0, description="CVSS v3 score")
    published_date: str = Field(..., description="ISO timestamp of publication")
    affected_assets: List[str] = Field(..., description="Affected asset identifiers")
    exploit_available: bool = Field(False, description="Public exploit available")
    patch_available: bool = Field(False, description="Patch available")


class TrendingScoreUpdate(BaseModel):
    """Request to update trending score."""
    cve_id: str = Field(..., description="CVE identifier")
    mentions: int = Field(0, ge=0, description="Exploit-DB/forum mentions (last 7 days)")
    dark_web_chatter: int = Field(0, ge=0, description="Dark web discussions (last 7 days)")


class ForecastVulnerabilitiesRequest(BaseModel):
    """Request for vulnerability forecasts."""
    time_horizon_days: int = Field(30, ge=1, le=365, description="Forecast window (1-365 days)")
    min_probability: float = Field(0.5, ge=0.0, le=1.0, description="Minimum probability threshold")


class VulnerabilityForecastResponse(BaseModel):
    """Response with vulnerability forecast."""
    cve_id: str
    vulnerability_name: str
    cvss_score: float
    exploit_probability: float
    estimated_exploitation_date: str
    affected_assets: List[str]
    mitigation_priority: int
    trending_score: float
    timestamp: str


class HuntingRecommendationResponse(BaseModel):
    """Response with hunting recommendation."""
    recommendation_id: str
    hunt_type: str
    target_assets: List[str]
    search_queries: List[str]
    rationale: str
    priority: int
    estimated_effort_hours: float
    potential_findings: List[str]
    timestamp: str


class HuntExecutionRequest(BaseModel):
    """Request to record hunt execution."""
    recommendation_id: str = Field(..., description="Recommendation ID")
    findings_count: int = Field(..., ge=0, description="Number of findings discovered")


class StatusResponse(BaseModel):
    """Service status response."""
    service: str
    status: str
    components: Dict[str, Dict[str, Any]]
    timestamp: str


# ============================================================================
# Attack Prediction Endpoints
# ============================================================================

@app.post("/prediction/ingest_event")
async def ingest_threat_event(request: ThreatEventRequest):
    """Ingest historical threat event for pattern learning.

    Args:
        request: Threat event details

    Returns:
        Ingestion confirmation
    """
    if attack_predictor is None:
        raise HTTPException(status_code=503, detail="Attack predictor not initialized")

    try:
        # Parse threat type
        try:
            threat_type = ThreatType(request.threat_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid threat type: {request.threat_type}"
            )

        # Parse timestamp
        if request.timestamp:
            timestamp = datetime.fromisoformat(request.timestamp)
        else:
            timestamp = datetime.now()

        # Create threat event
        event = ThreatEvent(
            event_id=request.event_id,
            threat_type=threat_type,
            timestamp=timestamp,
            source_ip=request.source_ip,
            target_asset=request.target_asset,
            severity=request.severity,
            indicators=request.indicators,
            metadata=request.metadata
        )

        # Ingest event
        attack_predictor.ingest_threat_event(event)

        return {
            "status": "success",
            "event_id": request.event_id,
            "threat_type": threat_type.value,
            "timestamp": timestamp.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting threat event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prediction/predict", response_model=List[AttackPredictionResponse])
async def predict_attacks(request: PredictAttacksRequest):
    """Generate attack predictions.

    Args:
        request: Prediction parameters

    Returns:
        List of attack predictions
    """
    if attack_predictor is None:
        raise HTTPException(status_code=503, detail="Attack predictor not initialized")

    try:
        # Generate predictions
        predictions = attack_predictor.predict_attacks(
            time_horizon_hours=request.time_horizon_hours,
            min_confidence=request.min_confidence
        )

        # Convert to response models
        responses = [
            AttackPredictionResponse(
                prediction_id=pred.prediction_id,
                threat_type=pred.threat_type.value,
                predicted_time=pred.predicted_time.isoformat(),
                predicted_targets=pred.predicted_targets,
                probability=pred.probability,
                confidence=pred.confidence.value,
                indicators=pred.indicators,
                recommended_actions=pred.recommended_actions,
                timestamp=pred.timestamp.isoformat()
            )
            for pred in predictions
        ]

        return responses

    except Exception as e:
        logger.error(f"Error predicting attacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prediction/validate")
async def validate_prediction(
    prediction_id: str,
    actual_occurred: bool
):
    """Validate prediction accuracy (for learning).

    Args:
        prediction_id: Prediction to validate
        actual_occurred: Whether attack actually occurred

    Returns:
        Validation confirmation
    """
    if attack_predictor is None:
        raise HTTPException(status_code=503, detail="Attack predictor not initialized")

    try:
        attack_predictor.validate_prediction(prediction_id, actual_occurred)

        return {
            "status": "success",
            "prediction_id": prediction_id,
            "actual_occurred": actual_occurred,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error validating prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Vulnerability Forecasting Endpoints
# ============================================================================

@app.post("/vulnerability/register")
async def register_vulnerability(request: VulnerabilityRegistrationRequest):
    """Register vulnerability in forecasting database.

    Args:
        request: Vulnerability details

    Returns:
        Registration confirmation
    """
    if vuln_forecaster is None:
        raise HTTPException(status_code=503, detail="Vulnerability forecaster not initialized")

    try:
        # Parse publication date
        published_date = datetime.fromisoformat(request.published_date)

        # Register vulnerability
        vuln_forecaster.register_vulnerability(
            cve_id=request.cve_id,
            cvss_score=request.cvss_score,
            published_date=published_date,
            affected_assets=request.affected_assets,
            exploit_available=request.exploit_available,
            patch_available=request.patch_available
        )

        return {
            "status": "success",
            "cve_id": request.cve_id,
            "cvss_score": request.cvss_score,
            "affected_assets_count": len(request.affected_assets),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error registering vulnerability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vulnerability/update_trending")
async def update_trending_score(request: TrendingScoreUpdate):
    """Update vulnerability trending score.

    Args:
        request: Trending data

    Returns:
        Update confirmation
    """
    if vuln_forecaster is None:
        raise HTTPException(status_code=503, detail="Vulnerability forecaster not initialized")

    try:
        vuln_forecaster.update_trending_score(
            cve_id=request.cve_id,
            mentions=request.mentions,
            dark_web_chatter=request.dark_web_chatter
        )

        return {
            "status": "success",
            "cve_id": request.cve_id,
            "mentions": request.mentions,
            "dark_web_chatter": request.dark_web_chatter,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error updating trending score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vulnerability/forecast", response_model=List[VulnerabilityForecastResponse])
async def forecast_vulnerabilities(request: ForecastVulnerabilitiesRequest):
    """Generate vulnerability exploitation forecasts.

    Args:
        request: Forecast parameters

    Returns:
        List of vulnerability forecasts
    """
    if vuln_forecaster is None:
        raise HTTPException(status_code=503, detail="Vulnerability forecaster not initialized")

    try:
        # Generate forecasts
        forecasts = vuln_forecaster.forecast_exploitations(
            time_horizon_days=request.time_horizon_days,
            min_probability=request.min_probability
        )

        # Convert to response models
        responses = [
            VulnerabilityForecastResponse(
                cve_id=forecast.cve_id,
                vulnerability_name=forecast.vulnerability_name,
                cvss_score=forecast.cvss_score,
                exploit_probability=forecast.exploit_probability,
                estimated_exploitation_date=forecast.estimated_exploitation_date.isoformat(),
                affected_assets=forecast.affected_assets,
                mitigation_priority=forecast.mitigation_priority,
                trending_score=forecast.trending_score,
                timestamp=forecast.timestamp.isoformat()
            )
            for forecast in forecasts
        ]

        return responses

    except Exception as e:
        logger.error(f"Error forecasting vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Proactive Hunting Endpoints
# ============================================================================

@app.post("/hunt/recommendations", response_model=List[HuntingRecommendationResponse])
async def generate_hunting_recommendations():
    """Generate hunting recommendations from current predictions and forecasts.

    Returns:
        List of hunting recommendations
    """
    if attack_predictor is None or vuln_forecaster is None or proactive_hunter is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Get current predictions
        predictions = attack_predictor.predict_attacks(
            time_horizon_hours=24,
            min_confidence=0.6
        )

        # Get current forecasts
        forecasts = vuln_forecaster.forecast_exploitations(
            time_horizon_days=30,
            min_probability=0.5
        )

        # Generate recommendations
        recommendations = proactive_hunter.generate_hunting_recommendations(
            predictions=predictions,
            forecasts=forecasts
        )

        # Convert to response models
        responses = [
            HuntingRecommendationResponse(
                recommendation_id=rec.recommendation_id,
                hunt_type=rec.hunt_type,
                target_assets=rec.target_assets,
                search_queries=rec.search_queries,
                rationale=rec.rationale,
                priority=rec.priority,
                estimated_effort_hours=rec.estimated_effort_hours,
                potential_findings=rec.potential_findings,
                timestamp=rec.timestamp.isoformat()
            )
            for rec in recommendations
        ]

        return responses

    except Exception as e:
        logger.error(f"Error generating hunting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/hunt/execute")
async def record_hunt_execution(request: HuntExecutionRequest):
    """Record hunt execution and findings.

    Args:
        request: Hunt execution details

    Returns:
        Recording confirmation
    """
    if proactive_hunter is None:
        raise HTTPException(status_code=503, detail="Proactive hunter not initialized")

    try:
        proactive_hunter.record_hunt_execution(
            recommendation_id=request.recommendation_id,
            findings_count=request.findings_count
        )

        return {
            "status": "success",
            "recommendation_id": request.recommendation_id,
            "findings_count": request.findings_count,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error recording hunt execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "predictive_threat_hunting",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get comprehensive service status.

    Returns:
        Status of all components
    """
    components = {}

    # Attack predictor status
    if attack_predictor is not None:
        components["attack_predictor"] = attack_predictor.get_status()

    # Vulnerability forecaster status
    if vuln_forecaster is not None:
        components["vulnerability_forecaster"] = vuln_forecaster.get_status()

    # Proactive hunter status
    if proactive_hunter is not None:
        components["proactive_hunter"] = proactive_hunter.get_status()

    return StatusResponse(
        service="predictive_threat_hunting",
        status="operational",
        components=components,
        timestamp=datetime.now().isoformat()
    )


@app.get("/stats")
async def get_statistics():
    """Get comprehensive statistics.

    Returns:
        Combined statistics from all components
    """
    stats = {
        "service": "predictive_threat_hunting",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # Gather stats from all components
    if attack_predictor is not None:
        status = attack_predictor.get_status()
        stats["components"]["attack_predictor"] = {
            "threat_events": status["threat_events_ingested"],
            "predictions_made": status["predictions_made"],
            "accuracy": status["accuracy"]
        }

    if vuln_forecaster is not None:
        status = vuln_forecaster.get_status()
        stats["components"]["vulnerability_forecaster"] = {
            "vulnerabilities_tracked": status["vulnerabilities_tracked"],
            "forecasts_made": status["forecasts_made"]
        }

    if proactive_hunter is not None:
        status = proactive_hunter.get_status()
        stats["components"]["proactive_hunter"] = {
            "recommendations_generated": status["recommendations_generated"],
            "hunts_executed": status["hunts_executed"],
            "findings_discovered": status["findings_discovered"],
            "hit_rate": status["hit_rate"]
        }

    return stats


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8016,
        log_level="info",
        access_log=True
    )
