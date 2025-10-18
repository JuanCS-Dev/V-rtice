"""
PFC Consciousness FastAPI Application

REST API for Prefrontal Cortex decision orchestration and history.
Provides endpoints for decision queries, analytics, and real-time streaming.

Author: Juan Carlos de Souza + Claude Code
Lei Governante: Constituição Vértice v2.7
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import sys
from pathlib import Path
consciousness_path = Path(__file__).parent.parent.parent
if str(consciousness_path) not in sys.path:
    sys.path.insert(0, str(consciousness_path))

from consciousness.prefrontal_cortex import PrefrontalCortex, OrchestratedDecision
from consciousness.persistence import DecisionRepository, DecisionQueryService
from mip.models import ActionPlan

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class OrchestrateRequest(BaseModel):
    """Request for basic decision orchestration."""
    user_id: str = Field(..., description="User UUID")
    behavioral_signals: Dict[str, Any] = Field(..., description="Behavioral metrics")
    action_description: str = Field(..., description="Action being evaluated")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "behavioral_signals": {
                    "error_count": 2,
                    "retry_count": 1,
                    "response_time_ms": 1500,
                    "task_success": False
                },
                "action_description": "User experiencing errors in task completion"
            }
        }


class OrchestrateWithPlanRequest(BaseModel):
    """Request for orchestration with ethical evaluation."""
    user_id: str = Field(..., description="User UUID")
    behavioral_signals: Dict[str, Any] = Field(..., description="Behavioral metrics")
    action_plan: ActionPlan = Field(..., description="Action plan for MIP evaluation")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "behavioral_signals": {"error_count": 0, "task_success": True},
                "action_plan": {
                    "name": "Deploy feature",
                    "description": "Deploy new feature to production",
                    "category": "reactive",
                    "steps": [{
                        "sequence_number": 1,
                        "description": "Run tests",
                        "action_type": "validation"
                    }],
                    "stakeholders": [],
                    "urgency": 0.5,
                    "risk_level": 0.3
                }
            }
        }


class DecisionResponse(BaseModel):
    """Response with orchestrated decision."""
    decision_id: str
    user_id: str
    final_decision: str
    rationale: str
    requires_escalation: bool
    confidence: float
    timestamp: str
    mental_state: Optional[Dict] = None
    detected_events: List[Dict] = []
    planned_interventions: List[Dict] = []
    constitutional_check: Optional[Dict] = None
    ethical_verdict_summary: Optional[str] = None


class DecisionListResponse(BaseModel):
    """Response with list of decisions."""
    decisions: List[DecisionResponse]
    total: int
    limit: int
    offset: int


class StatisticsResponse(BaseModel):
    """Response with decision statistics."""
    total_decisions: int
    escalated: int
    escalation_rate: float
    approval_rate: Optional[float] = None
    avg_confidence: float
    interventions_planned: int
    suffering_detected: int
    constitutional_violations: int
    mip_evaluations: Optional[int] = None
    mip_approved: Optional[int] = None
    mip_rejected: Optional[int] = None
    persisted_decisions: Optional[int] = None


class AnalyticsResponse(BaseModel):
    """Response with suffering analytics."""
    total_events: int
    affected_agents: int
    avg_severity: Optional[float] = None
    max_severity: Optional[int] = None
    critical_events: int
    by_type: List[Dict]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str
    version: str
    pfc_initialized: bool
    persistence_enabled: bool
    mip_enabled: bool


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Startup: Initialize PFC and persistence.
    Shutdown: Close connections.
    """
    logger.info("🚀 Starting PFC Consciousness API")

    # Initialize persistence (optional)
    try:
        app.state.repository = DecisionRepository(
            host="localhost",
            port=5432,
            database="vertice_consciousness",
            user="postgres",
            password="postgres"
        )
        app.state.repository.initialize()
        app.state.persistence_enabled = True
        app.state.query_service = DecisionQueryService(app.state.repository)
        logger.info("✅ Persistence layer initialized")
    except Exception as e:
        logger.warning(f"⚠️  Persistence unavailable: {e}")
        logger.warning("⚠️  Operating without database persistence")
        app.state.repository = None
        app.state.persistence_enabled = False
        app.state.query_service = None

    # Initialize PFC
    app.state.pfc = PrefrontalCortex(
        enable_mip=True,
        repository=app.state.repository
    )
    logger.info("✅ PFC initialized (MIP enabled)")

    # WebSocket connection manager
    app.state.ws_connections = set()

    logger.info("🎯 PFC Consciousness API ready")

    yield

    # Shutdown
    logger.info("🛑 Shutting down PFC Consciousness API")
    if app.state.persistence_enabled:
        app.state.repository.close()
        logger.info("✅ Persistence closed")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="PFC Consciousness API",
    description="REST API for Prefrontal Cortex decision orchestration and analytics",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler for HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "detail": str(exc),
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler for general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500,
        }
    )


# ============================================================================
# Helper Functions
# ============================================================================

def decision_to_response(decision: OrchestratedDecision) -> DecisionResponse:
    """Convert OrchestratedDecision to API response."""
    mental_state_dict = None
    if decision.mental_state:
        mental_state_dict = {
            "emotional_state": decision.mental_state.emotional_state.value,
            "intent": decision.mental_state.intent,
            "needs_assistance": decision.mental_state.needs_assistance,
            "confidence": decision.mental_state.confidence,
        }

    events_list = [
        {
            "agent_id": str(e.agent_id),
            "event_type": e.event_type.value,
            "severity": e.severity,
            "description": e.description,
        }
        for e in decision.detected_events
    ]

    interventions_list = [
        {
            "plan_id": str(p.plan_id),
            "intervention_type": p.intervention_type.value,
            "priority": p.priority,
            "actions": p.actions,
        }
        for p in decision.planned_interventions
    ]

    ethical_summary = None
    if decision.ethical_verdict:
        ethical_summary = f"{decision.ethical_verdict.status.value} (score: {decision.ethical_verdict.aggregate_score:.2f})"

    return DecisionResponse(
        decision_id=str(decision.decision_id),
        user_id=str(decision.user_id),
        final_decision=decision.final_decision,
        rationale=decision.rationale,
        requires_escalation=decision.requires_escalation,
        confidence=decision.confidence,
        timestamp=decision.timestamp.isoformat(),
        mental_state=mental_state_dict,
        detected_events=events_list,
        planned_interventions=interventions_list,
        constitutional_check=decision.constitutional_check,
        ethical_verdict_summary=ethical_summary,
    )


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": "PFC Consciousness API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Verifies service status, PFC, and persistence availability.
    """
    return HealthResponse(
        status="healthy",
        service="PFC Consciousness API",
        version="1.0.0",
        pfc_initialized=app.state.pfc is not None,
        persistence_enabled=app.state.persistence_enabled,
        mip_enabled=app.state.pfc.enable_mip if app.state.pfc else False,
    )


@app.post(
    "/orchestrate",
    response_model=DecisionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Orchestration"],
    summary="Orchestrate decision (basic)",
    description="Orchestrate decision using ToM + Compassion + DDL (without MIP evaluation)",
)
async def orchestrate_decision(request: OrchestrateRequest):
    """
    Orchestrate a basic decision.

    Pipeline: ToM → Compassion → DDL → PFC

    Args:
        request: OrchestrateRequest with user signals

    Returns:
        DecisionResponse with orchestrated decision
    """
    try:
        pfc: PrefrontalCortex = app.state.pfc

        decision = pfc.orchestrate_decision(
            user_id=UUID(request.user_id),
            behavioral_signals=request.behavioral_signals,
            action_description=request.action_description
        )

        # Broadcast to WebSocket clients
        await broadcast_decision(decision)

        return decision_to_response(decision)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Orchestration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failed: {str(e)}"
        )


@app.post(
    "/orchestrate-with-plan",
    response_model=DecisionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Orchestration"],
    summary="Orchestrate decision with MIP",
    description="Full ethical pipeline: ToM → Compassion → DDL → MIP → PFC",
)
async def orchestrate_with_plan(request: OrchestrateWithPlanRequest):
    """
    Orchestrate decision with MIP evaluation.

    Full pipeline: ToM → Compassion → DDL → MIP → PFC

    Args:
        request: OrchestrateWithPlanRequest with action plan

    Returns:
        DecisionResponse with full ethical evaluation
    """
    try:
        pfc: PrefrontalCortex = app.state.pfc

        if not pfc.enable_mip:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MIP not enabled"
            )

        decision = pfc.orchestrate_with_plan(
            user_id=UUID(request.user_id),
            behavioral_signals=request.behavioral_signals,
            action_plan=request.action_plan
        )

        # Broadcast to WebSocket clients
        await broadcast_decision(decision)

        return decision_to_response(decision)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Orchestration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failed: {str(e)}"
        )


@app.get(
    "/decisions/{decision_id}",
    response_model=DecisionResponse,
    tags=["Decisions"],
    summary="Get decision by ID",
)
async def get_decision(decision_id: UUID):
    """
    Retrieve decision by ID.

    Args:
        decision_id: Decision UUID

    Returns:
        DecisionResponse or 404
    """
    pfc: PrefrontalCortex = app.state.pfc

    # Try in-memory first
    decision = pfc.get_decision(decision_id)

    if decision:
        return decision_to_response(decision)

    # Try persistence if available
    if app.state.persistence_enabled:
        repo: DecisionRepository = app.state.repository
        decision_dict = repo.get_decision(decision_id)

        if decision_dict:
            # Convert dict to response (simplified)
            return DecisionResponse(
                decision_id=decision_dict["decision_id"],
                user_id=decision_dict["user_id"],
                final_decision=decision_dict["final_decision"],
                rationale=decision_dict["rationale"],
                requires_escalation=decision_dict["requires_escalation"],
                confidence=decision_dict["confidence"],
                timestamp=decision_dict["timestamp"].isoformat(),
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Decision {decision_id} not found"
    )


@app.get(
    "/decisions/user/{user_id}",
    response_model=DecisionListResponse,
    tags=["Decisions"],
    summary="Get decisions for user",
)
async def get_user_decisions(
    user_id: UUID,
    limit: int = 10,
    offset: int = 0
):
    """
    Get decision history for a user.

    Args:
        user_id: User UUID
        limit: Maximum results
        offset: Offset for pagination

    Returns:
        DecisionListResponse with user decisions
    """
    # Try persistence first if available
    if app.state.persistence_enabled:
        repo: DecisionRepository = app.state.repository
        decisions_dicts = repo.get_decisions_for_user(user_id, limit=limit, offset=offset)

        decisions = [
            DecisionResponse(
                decision_id=d["decision_id"],
                user_id=d["user_id"],
                final_decision=d["final_decision"],
                rationale=d["rationale"],
                requires_escalation=d["requires_escalation"],
                confidence=d["confidence"],
                timestamp=d["timestamp"].isoformat(),
            )
            for d in decisions_dicts
        ]

        return DecisionListResponse(
            decisions=decisions,
            total=len(decisions),
            limit=limit,
            offset=offset
        )

    # Fallback to in-memory
    pfc: PrefrontalCortex = app.state.pfc
    decisions_obj = pfc.get_decisions_for_user(user_id, limit=limit)

    decisions = [decision_to_response(d) for d in decisions_obj]

    return DecisionListResponse(
        decisions=decisions,
        total=len(decisions),
        limit=limit,
        offset=offset
    )


@app.get(
    "/decisions/escalated",
    response_model=DecisionListResponse,
    tags=["Decisions"],
    summary="Get escalated decisions",
)
async def get_escalated_decisions(
    since_hours: Optional[int] = None,
    limit: int = 100
):
    """
    Get decisions requiring escalation.

    Args:
        since_hours: Only decisions from last N hours
        limit: Maximum results

    Returns:
        DecisionListResponse with escalated decisions
    """
    if not app.state.persistence_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistence not available"
        )

    since = None
    if since_hours:
        since = datetime.utcnow() - timedelta(hours=since_hours)

    repo: DecisionRepository = app.state.repository
    decisions_dicts = repo.get_escalated_decisions(since=since, limit=limit)

    decisions = [
        DecisionResponse(
            decision_id=d["decision_id"],
            user_id=d["user_id"],
            final_decision=d["final_decision"],
            rationale=d["rationale"],
            requires_escalation=d["requires_escalation"],
            confidence=d["confidence"],
            timestamp=d["timestamp"].isoformat(),
        )
        for d in decisions_dicts
    ]

    return DecisionListResponse(
        decisions=decisions,
        total=len(decisions),
        limit=limit,
        offset=0
    )


@app.get(
    "/statistics",
    response_model=StatisticsResponse,
    tags=["Analytics"],
    summary="Get decision statistics",
)
async def get_statistics(
    user_id: Optional[UUID] = None,
    since_hours: Optional[int] = None
):
    """
    Get decision statistics.

    Args:
        user_id: Filter by user (optional)
        since_hours: Only decisions from last N hours (optional)

    Returns:
        StatisticsResponse with aggregated statistics
    """
    # Try persistence if available
    if app.state.persistence_enabled and (user_id or since_hours):
        service: DecisionQueryService = app.state.query_service

        since = None
        if since_hours:
            since = datetime.utcnow() - timedelta(hours=since_hours)

        stats = service.get_decision_statistics(user_id=user_id, since=since)

        return StatisticsResponse(
            total_decisions=stats["total_decisions"],
            escalated=stats["escalated"],
            escalation_rate=stats.get("escalation_rate", 0.0),
            approval_rate=stats.get("approval_rate"),
            avg_confidence=stats.get("avg_confidence", 0.0),
            interventions_planned=stats.get("interventions", 0),
            suffering_detected=0,  # Not in DB stats
            constitutional_violations=0,  # Not in DB stats
        )

    # Fallback to in-memory PFC stats
    pfc: PrefrontalCortex = app.state.pfc
    stats = pfc.get_statistics()

    return StatisticsResponse(
        total_decisions=stats["total_decisions"],
        escalated=stats["escalated"],
        escalation_rate=stats.get("escalation_rate", 0.0),
        avg_confidence=0.0,  # Not in in-memory stats
        interventions_planned=stats["interventions_planned"],
        suffering_detected=stats["suffering_detected"],
        constitutional_violations=stats["constitutional_violations"],
        mip_evaluations=stats.get("mip_evaluations"),
        mip_approved=stats.get("mip_approved"),
        mip_rejected=stats.get("mip_rejected"),
        persisted_decisions=stats.get("persisted_decisions"),
    )


@app.get(
    "/analytics/suffering",
    response_model=AnalyticsResponse,
    tags=["Analytics"],
    summary="Get suffering analytics",
)
async def get_suffering_analytics(since_hours: Optional[int] = None):
    """
    Get suffering detection analytics.

    Args:
        since_hours: Only events from last N hours (optional)

    Returns:
        AnalyticsResponse with suffering metrics
    """
    if not app.state.persistence_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistence not available"
        )

    since = None
    if since_hours:
        since = datetime.utcnow() - timedelta(hours=since_hours)

    service: DecisionQueryService = app.state.query_service
    analytics = service.get_suffering_analytics(since=since)

    return AnalyticsResponse(
        total_events=analytics["total_events"],
        affected_agents=analytics.get("affected_agents", 0),
        avg_severity=analytics.get("avg_severity"),
        max_severity=analytics.get("max_severity"),
        critical_events=analytics.get("critical_events", 0),
        by_type=analytics.get("by_type", []),
    )


# ============================================================================
# WebSocket for Real-time Decisions
# ============================================================================

async def broadcast_decision(decision: OrchestratedDecision):
    """Broadcast decision to all WebSocket clients."""
    if not app.state.ws_connections:
        return

    message = {
        "type": "decision",
        "decision_id": str(decision.decision_id),
        "user_id": str(decision.user_id),
        "final_decision": decision.final_decision,
        "requires_escalation": decision.requires_escalation,
        "timestamp": decision.timestamp.isoformat(),
    }

    # Broadcast to all connections
    disconnected = set()
    for ws in app.state.ws_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.add(ws)

    # Remove disconnected clients
    app.state.ws_connections -= disconnected


@app.websocket("/ws/decisions")
async def websocket_decisions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time decision streaming.

    Clients receive decision notifications as they're made.
    """
    await websocket.accept()
    app.state.ws_connections.add(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to PFC decision stream"
        })

        # Keep connection alive
        while True:
            # Wait for client ping (or timeout)
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    finally:
        app.state.ws_connections.discard(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=True,
    )
