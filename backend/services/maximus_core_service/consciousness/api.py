"""Consciousness System API

FastAPI endpoints for consciousness monitoring dashboard.

Exposes real-time consciousness state, ESGT events, arousal levels,
and control endpoints for manual system interaction.

Integration:
    from consciousness.api import create_consciousness_api
    app.include_router(create_consciousness_api(consciousness_system))

Authors: Juan & Claude Code
Version: 1.0.0 - FASE V Sprint 2
"""

import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from consciousness.prometheus_metrics import get_metrics_handler

# ==================== REQUEST/RESPONSE MODELS ====================


class SalienceInput(BaseModel):
    """Salience score for manual ESGT trigger."""

    novelty: float = Field(..., ge=0.0, le=1.0, description="Novelty component [0-1]")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance component [0-1]")
    urgency: float = Field(..., ge=0.0, le=1.0, description="Urgency component [0-1]")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ArousalAdjustment(BaseModel):
    """Arousal level adjustment request."""

    delta: float = Field(..., ge=-0.5, le=0.5, description="Arousal change [-0.5, +0.5]")
    duration_seconds: float = Field(default=5.0, ge=0.1, le=60.0, description="Duration (seconds)")
    source: str = Field(default="manual", description="Source identifier")


class ConsciousnessStateResponse(BaseModel):
    """Complete consciousness state snapshot."""

    timestamp: str
    esgt_active: bool
    arousal_level: float
    arousal_classification: str
    tig_metrics: Dict[str, Any]
    recent_events_count: int
    system_health: str


class ESGTEventResponse(BaseModel):
    """ESGT ignition event."""

    event_id: str
    timestamp: str
    success: bool
    salience: Dict[str, float]
    coherence: Optional[float]
    duration_ms: Optional[float]
    nodes_participating: int
    reason: Optional[str]


class SafetyStatusResponse(BaseModel):
    """Safety protocol status (FASE VII)."""

    monitoring_active: bool
    kill_switch_active: bool
    violations_total: int
    violations_by_severity: Dict[str, int]
    last_violation: Optional[str]
    uptime_seconds: float


class SafetyViolationResponse(BaseModel):
    """Safety violation event (FASE VII)."""

    violation_id: str
    violation_type: str
    severity: str
    timestamp: str
    value_observed: float
    threshold_violated: float
    message: str
    context: Dict[str, Any]


class EmergencyShutdownRequest(BaseModel):
    """Emergency shutdown request (HITL only - FASE VII)."""

    reason: str = Field(..., min_length=10, description="Human-readable reason (min 10 chars)")
    allow_override: bool = Field(default=True, description="Allow HITL override (5s window)")


# ==================== API FACTORY ====================


def create_consciousness_api(consciousness_system: Dict[str, Any]) -> APIRouter:
    """Create consciousness API router.

    Args:
        consciousness_system: Dict with keys:
            - 'tig': TIGFabric instance
            - 'esgt': ESGTCoordinator instance
            - 'arousal': ArousalController instance

    Returns:
        FastAPI router with consciousness endpoints
    """
    router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])

    # WebSocket connections for real-time streaming
    active_connections: List[WebSocket] = []

    # Event history (last 100 events)
    event_history: List[Dict[str, Any]] = []
    MAX_HISTORY = 100

    # ==================== HELPER FUNCTIONS ====================

    def add_event_to_history(event: Any) -> None:
        """Add ESGT event to history."""
        event_dict = asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event)
        event_dict["timestamp"] = datetime.now().isoformat()
        event_history.append(event_dict)
        if len(event_history) > MAX_HISTORY:
            event_history.pop(0)

    async def broadcast_to_websockets(message: Dict[str, Any]) -> None:
        """Broadcast message to all connected WebSocket clients."""
        dead_connections = []
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Remove dead connections
        for connection in dead_connections:
            active_connections.remove(connection)

    # ==================== REST ENDPOINTS ====================

    @router.get("/state", response_model=ConsciousnessStateResponse)
    async def get_consciousness_state():
        """Get current complete consciousness state."""
        try:
            tig = consciousness_system.get("tig")
            esgt = consciousness_system.get("esgt")
            arousal = consciousness_system.get("arousal")

            if not all([tig, esgt, arousal]):
                raise HTTPException(status_code=503, detail="Consciousness system not fully initialized")

            # Get metrics
            tig_metrics = tig.get_metrics() if hasattr(tig, "get_metrics") else {}
            arousal_state = arousal.get_current_arousal() if hasattr(arousal, "get_current_arousal") else None

            return ConsciousnessStateResponse(
                timestamp=datetime.now().isoformat(),
                esgt_active=esgt._running if hasattr(esgt, "_running") else False,
                arousal_level=arousal_state.arousal if arousal_state else 0.5,
                arousal_classification=arousal_state.level.value
                if arousal_state and hasattr(arousal_state.level, "value")
                else "UNKNOWN",
                tig_metrics=tig_metrics,
                recent_events_count=len(event_history),
                system_health="HEALTHY" if all([tig, esgt, arousal]) else "DEGRADED",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving state: {str(e)}")

    @router.get("/esgt/events", response_model=List[ESGTEventResponse])
    async def get_esgt_events(limit: int = 20):
        """Get recent ESGT events.

        Args:
            limit: Maximum number of events to return (default 20)
        """
        if limit < 1 or limit > MAX_HISTORY:
            raise HTTPException(status_code=400, detail=f"Limit must be between 1 and {MAX_HISTORY}")

        # Return most recent events
        events = event_history[-limit:]

        return [
            ESGTEventResponse(
                event_id=evt.get("event_id", "unknown"),
                timestamp=evt.get("timestamp", datetime.now().isoformat()),
                success=evt.get("success", False),
                salience={
                    "novelty": evt.get("salience", {}).get("novelty", 0),
                    "relevance": evt.get("salience", {}).get("relevance", 0),
                    "urgency": evt.get("salience", {}).get("urgency", 0),
                },
                coherence=evt.get("coherence_achieved"),
                duration_ms=evt.get("duration_ms"),
                nodes_participating=len(evt.get("nodes_participating", [])),
                reason=evt.get("reason"),
            )
            for evt in events
        ]

    @router.get("/arousal")
    async def get_arousal_state():
        """Get current arousal state."""
        try:
            arousal = consciousness_system.get("arousal")
            if not arousal:
                raise HTTPException(status_code=503, detail="Arousal controller not initialized")

            arousal_state = arousal.get_current_arousal()
            if not arousal_state:
                return {"error": "No arousal state available"}

            return {
                "arousal": arousal_state.arousal,
                "level": arousal_state.level.value
                if hasattr(arousal_state.level, "value")
                else str(arousal_state.level),
                "baseline": arousal_state.baseline_arousal,
                "need_contribution": arousal_state.need_contribution,
                "stress_contribution": arousal_state.stress_contribution,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving arousal: {str(e)}")

    @router.post("/esgt/trigger")
    async def trigger_esgt(salience: SalienceInput):
        """Manually trigger ESGT ignition.

        Args:
            salience: Salience scores for ignition trigger

        Returns:
            ESGT event result
        """
        try:
            esgt = consciousness_system.get("esgt")
            if not esgt:
                raise HTTPException(status_code=503, detail="ESGT coordinator not initialized")

            # Import SalienceScore
            from consciousness.esgt.coordinator import SalienceScore

            # Create salience score
            salience_score = SalienceScore(
                novelty=salience.novelty, relevance=salience.relevance, urgency=salience.urgency
            )

            # Trigger ESGT
            event = await esgt.initiate_esgt(salience_score, salience.context)

            # Add to history
            add_event_to_history(event)

            # Broadcast to WebSocket clients
            await broadcast_to_websockets(
                {
                    "type": "esgt_event",
                    "event": asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event),
                }
            )

            return {
                "success": event.success,
                "event_id": event.event_id,
                "coherence": event.coherence_achieved,
                "duration_ms": event.duration_ms,
                "reason": event.reason,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error triggering ESGT: {str(e)}")

    @router.post("/arousal/adjust")
    async def adjust_arousal(adjustment: ArousalAdjustment):
        """Adjust arousal level.

        Args:
            adjustment: Arousal adjustment parameters

        Returns:
            New arousal state
        """
        try:
            arousal = consciousness_system.get("arousal")
            if not arousal:
                raise HTTPException(status_code=503, detail="Arousal controller not initialized")

            # Request modulation
            arousal.request_modulation(
                source=adjustment.source, delta=adjustment.delta, duration_seconds=adjustment.duration_seconds
            )

            # Get new state
            await asyncio.sleep(0.1)  # Give time for modulation to apply
            new_state = arousal.get_current_arousal()

            # Broadcast to WebSocket clients
            await broadcast_to_websockets(
                {
                    "type": "arousal_change",
                    "arousal": new_state.arousal,
                    "level": new_state.level.value if hasattr(new_state.level, "value") else str(new_state.level),
                }
            )

            return {
                "arousal": new_state.arousal,
                "level": new_state.level.value if hasattr(new_state.level, "value") else str(new_state.level),
                "delta_applied": adjustment.delta,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error adjusting arousal: {str(e)}")

    @router.get("/metrics")
    async def get_metrics():
        """Get consciousness system metrics."""
        try:
            tig = consciousness_system.get("tig")
            esgt = consciousness_system.get("esgt")

            metrics = {}

            if tig and hasattr(tig, "get_metrics"):
                metrics["tig"] = tig.get_metrics()

            if esgt and hasattr(esgt, "get_metrics"):
                metrics["esgt"] = esgt.get_metrics()

            metrics["events_count"] = len(event_history)
            metrics["timestamp"] = datetime.now().isoformat()

            return metrics
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

    # ==================== SAFETY PROTOCOL ENDPOINTS (FASE VII) ====================

    @router.get("/safety/status", response_model=SafetyStatusResponse)
    async def get_safety_status():
        """Get safety protocol status.

        Returns:
            Complete safety protocol status including violations and kill switch state

        Raises:
            HTTPException: If safety protocol is not enabled or not initialized
        """
        try:
            system = consciousness_system.get("system")

            if not system:
                raise HTTPException(status_code=503, detail="Consciousness system not initialized")

            status = system.get_safety_status()

            if not status:
                raise HTTPException(status_code=503, detail="Safety protocol not enabled in this system")

            return SafetyStatusResponse(**status)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving safety status: {str(e)}")

    @router.get("/safety/violations", response_model=List[SafetyViolationResponse])
    async def get_safety_violations(limit: int = 100):
        """Get recent safety violations.

        Args:
            limit: Maximum number of violations to return (1-1000)

        Returns:
            List of recent safety violations, ordered by timestamp

        Raises:
            HTTPException: If safety protocol is not enabled
        """
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

        try:
            system = consciousness_system.get("system")

            if not system:
                raise HTTPException(status_code=503, detail="Consciousness system not initialized")

            violations = system.get_safety_violations(limit=limit)

            return [
                SafetyViolationResponse(
                    violation_id=v.violation_id,
                    violation_type=v.violation_type.value,
                    severity=v.severity.value,
                    timestamp=v.timestamp.isoformat(),
                    value_observed=v.value_observed,
                    threshold_violated=v.threshold_violated,
                    message=v.message,
                    context=v.context,
                )
                for v in violations
            ]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving violations: {str(e)}")

    @router.post("/safety/emergency-shutdown")
    async def execute_emergency_shutdown(request: EmergencyShutdownRequest):
        """Execute emergency shutdown (HITL only).

        This endpoint triggers the kill switch protocol. If allow_override is True,
        HITL has 5 seconds to override. Otherwise, shutdown is immediate.

        **WARNING**: This is a destructive operation that stops the consciousness system.

        Args:
            request: Emergency shutdown request with reason

        Returns:
            Status of shutdown execution

        Raises:
            HTTPException: If safety protocol is not enabled
        """
        try:
            system = consciousness_system.get("system")

            if not system:
                raise HTTPException(status_code=503, detail="Consciousness system not initialized")

            shutdown_executed = await system.execute_emergency_shutdown(reason=request.reason)

            return {
                "success": True,
                "shutdown_executed": shutdown_executed,
                "message": ("Emergency shutdown executed" if shutdown_executed else "HITL overrode shutdown"),
                "timestamp": datetime.now().isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error executing emergency shutdown: {str(e)}")

    # ==================== PROMETHEUS METRICS ENDPOINT (FASE VII) ====================

    # Add Prometheus /metrics endpoint
    router.add_route("/metrics", get_metrics_handler(), methods=["GET"])

    # ==================== WEBSOCKET ENDPOINT ====================

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time consciousness state streaming."""
        await websocket.accept()
        active_connections.append(websocket)

        try:
            # Send initial state
            consciousness_system.get("tig")
            esgt = consciousness_system.get("esgt")
            arousal = consciousness_system.get("arousal")

            if arousal:
                arousal_state = arousal.get_current_arousal()
                await websocket.send_json(
                    {
                        "type": "initial_state",
                        "arousal": arousal_state.arousal if arousal_state else 0.5,
                        "events_count": len(event_history),
                        "esgt_active": esgt._running if esgt and hasattr(esgt, "_running") else False,
                    }
                )

            # Keep connection alive and listen for client messages
            while True:
                try:
                    # Wait for client message (ping/pong for keepalive)
                    await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                    # Echo back (simple ping/pong)
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})

        except WebSocketDisconnect:
            active_connections.remove(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
            if websocket in active_connections:
                active_connections.remove(websocket)

    return router
