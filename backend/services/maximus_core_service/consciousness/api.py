"""Consciousness System API

FastAPI endpoints for consciência monitoring dashboard incluindo streaming
em tempo real via WebSocket e Server-Sent Events (SSE).

Expose:
    - Estado atual (REST)
    - Eventos ESGT, ajustes de arousal (REST)
    - Stream contínuo para cockpit/TUI (`/stream/sse`, `/ws`)

Integration:
    from consciousness.api import create_consciousness_api
    app.include_router(create_consciousness_api(consciousness_system))

Autores: Juan & Claude Code
Versão: 1.1.0 - Sprint 2.2 (Streaming)
"""

import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from consciousness.prometheus_metrics import get_metrics_handler

# ==================== REQUEST/RESPONSE MODELS ====================


class SalienceInput(BaseModel):
    """Salience score for manual ESGT trigger."""

    novelty: float = Field(..., ge=0.0, le=1.0, description="Novelty component [0-1]")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance component [0-1]")
    urgency: float = Field(..., ge=0.0, le=1.0, description="Urgency component [0-1]")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


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
    tig_metrics: dict[str, Any]
    recent_events_count: int
    system_health: str


class ESGTEventResponse(BaseModel):
    """ESGT ignition event."""

    event_id: str
    timestamp: str
    success: bool
    salience: dict[str, float]
    coherence: float | None
    duration_ms: float | None
    nodes_participating: int
    reason: str | None


class SafetyStatusResponse(BaseModel):
    """Safety protocol status (FASE VII)."""

    monitoring_active: bool
    kill_switch_active: bool
    violations_total: int
    violations_by_severity: dict[str, int]
    last_violation: str | None
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
    context: dict[str, Any]


class EmergencyShutdownRequest(BaseModel):
    """Emergency shutdown request (HITL only - FASE VII)."""

    reason: str = Field(..., min_length=10, description="Human-readable reason (min 10 chars)")
    allow_override: bool = Field(default=True, description="Allow HITL override (5s window)")


# ==================== API FACTORY ====================


def create_consciousness_api(consciousness_system: dict[str, Any]) -> APIRouter:
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

    # WebSocket connections + SSE subscribers
    active_connections: list[WebSocket] = []
    sse_subscribers: list[asyncio.Queue[dict[str, Any]]] = []

    # Event history (last 100 events)
    event_history: list[dict[str, Any]] = []
    MAX_HISTORY = 100

    # ==================== HELPER FUNCTIONS ====================

    def add_event_to_history(event: Any) -> None:
        """Add ESGT event to history."""
        event_dict = asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event)
        event_dict["timestamp"] = datetime.now().isoformat()
        event_history.append(event_dict)
        if len(event_history) > MAX_HISTORY:
            event_history.pop(0)

    async def broadcast_to_consumers(message: dict[str, Any]) -> None:
        """Broadcast mensagem para WebSockets e SSE subscribers."""
        # Broadcast via WebSocket
        dead_connections = []
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except Exception:  # pragma: no cover - requires failing WebSocket (integration test)
                dead_connections.append(connection)

        # Remove dead connections
        for connection in dead_connections:  # pragma: no cover - requires failing WebSocket (integration test)
            active_connections.remove(connection)

        # Propagar para SSE subscribers
        if sse_subscribers:  # pragma: no cover - requires live SSE connection (integration test)
            serialized = message | {"timestamp": message.get("timestamp", datetime.now().isoformat())}
            for queue in list(sse_subscribers):
                try:
                    queue.put_nowait(serialized)
                except asyncio.QueueFull:
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                    try:
                        queue.put_nowait(serialized)
                    except asyncio.QueueFull:
                        continue

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
            tig_metrics_raw = tig.get_metrics() if hasattr(tig, "get_metrics") else {}
            # Convert FabricMetrics dataclass to dict if needed
            tig_metrics = asdict(tig_metrics_raw) if hasattr(tig_metrics_raw, "__dataclass_fields__") else tig_metrics_raw
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

    @router.get("/esgt/events", response_model=list[ESGTEventResponse])
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
                "temporal_contribution": arousal_state.temporal_contribution,
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
            await broadcast_to_consumers(
                {
                    "type": "esgt_event",
                    "event": asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event),
                }
            )

            return {
                "success": event.success,
                "event_id": event.event_id,
                "coherence": event.achieved_coherence,
                "duration_ms": event.time_to_sync_ms,
                "reason": getattr(event, "reason", None),
                "timestamp": datetime.now().isoformat(),
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
            await broadcast_to_consumers(
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

    @router.get("/safety/violations", response_model=list[SafetyViolationResponse])
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

    # ==================== REACTIVE FABRIC ENDPOINTS (Sprint 3) ====================

    @router.get("/reactive-fabric/metrics")
    async def get_reactive_fabric_metrics():
        """Get latest Reactive Fabric metrics (Sprint 3).

        Returns:
            Latest system metrics from MetricsCollector

        Raises:
            HTTPException: If orchestrator not available
        """
        try:
            system = consciousness_system.get("system")

            if not system or not hasattr(system, 'orchestrator'):
                raise HTTPException(
                    status_code=503,
                    detail="Reactive Fabric orchestrator not initialized"
                )

            # Collect latest metrics
            metrics = await system.orchestrator.metrics_collector.collect()

            return {
                "timestamp": metrics.timestamp,
                "tig": {
                    "node_count": metrics.tig_node_count,
                    "edge_count": metrics.tig_edge_count,
                    "avg_latency_us": metrics.tig_avg_latency_us,
                    "coherence": metrics.tig_coherence,
                },
                "esgt": {
                    "event_count": metrics.esgt_event_count,
                    "success_rate": metrics.esgt_success_rate,
                    "frequency_hz": metrics.esgt_frequency_hz,
                    "avg_coherence": metrics.esgt_avg_coherence,
                },
                "arousal": {
                    "level": metrics.arousal_level,
                    "classification": metrics.arousal_classification,
                    "stress": metrics.arousal_stress,
                    "need": metrics.arousal_need,
                },
                "pfc": {
                    "signals_processed": metrics.pfc_signals_processed,
                    "actions_generated": metrics.pfc_actions_generated,
                    "approval_rate": metrics.pfc_approval_rate,
                },
                "tom": {
                    "total_agents": metrics.tom_total_agents,
                    "total_beliefs": metrics.tom_total_beliefs,
                    "cache_hit_rate": metrics.tom_cache_hit_rate,
                },
                "safety": {
                    "violations": metrics.safety_violations,
                    "kill_switch_active": metrics.kill_switch_active,
                },
                "health_score": metrics.health_score,
                "collection_duration_ms": metrics.collection_duration_ms,
                "errors": metrics.errors,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving reactive fabric metrics: {str(e)}")

    @router.get("/reactive-fabric/events")
    async def get_reactive_fabric_events(limit: int = 20):
        """Get recent Reactive Fabric events (Sprint 3).

        Args:
            limit: Maximum events to return (1-100)

        Returns:
            Recent consciousness events from EventCollector

        Raises:
            HTTPException: If orchestrator not available
        """
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

        try:
            system = consciousness_system.get("system")

            if not system or not hasattr(system, 'orchestrator'):
                raise HTTPException(
                    status_code=503,
                    detail="Reactive Fabric orchestrator not initialized"
                )

            # Get recent events
            events = system.orchestrator.event_collector.get_recent_events(limit=limit)

            return {
                "events": [
                    {
                        "event_id": e.event_id,
                        "type": e.event_type.value,
                        "severity": e.severity.value,
                        "timestamp": e.timestamp,
                        "source": e.source,
                        "data": e.data,
                        "salience": {
                            "novelty": e.novelty,
                            "relevance": e.relevance,
                            "urgency": e.urgency,
                        },
                        "processed": e.processed,
                        "esgt_triggered": e.esgt_triggered,
                    }
                    for e in events
                ],
                "total_count": len(events),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving reactive fabric events: {str(e)}")

    @router.get("/reactive-fabric/orchestration")
    async def get_reactive_fabric_orchestration():
        """Get Reactive Fabric orchestration status (Sprint 3).

        Returns:
            DataOrchestrator statistics and recent decisions

        Raises:
            HTTPException: If orchestrator not available
        """
        try:
            system = consciousness_system.get("system")

            if not system or not hasattr(system, 'orchestrator'):
                raise HTTPException(
                    status_code=503,
                    detail="Reactive Fabric orchestrator not initialized"
                )

            orchestrator = system.orchestrator

            # Get orchestration stats
            stats = orchestrator.get_orchestration_stats()

            # Get recent decisions
            recent_decisions = orchestrator.get_recent_decisions(limit=10)

            return {
                "status": {
                    "running": orchestrator._running,
                    "collection_interval_ms": orchestrator.collection_interval_ms,
                    "salience_threshold": orchestrator.salience_threshold,
                },
                "statistics": stats,
                "recent_decisions": [
                    {
                        "timestamp": d.timestamp,
                        "should_trigger": d.should_trigger_esgt,
                        "salience": {
                            "novelty": d.salience.novelty,
                            "relevance": d.salience.relevance,
                            "urgency": d.salience.urgency,
                            "total": d.salience.compute_total(),
                        },
                        "reason": d.reason,
                        "confidence": d.confidence,
                        "triggering_events_count": len(d.triggering_events),
                        "health_score": d.metrics_snapshot.health_score,
                    }
                    for d in recent_decisions
                ],
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving orchestration status: {str(e)}")

    # ==================== PROMETHEUS METRICS ENDPOINT (FASE VII) ====================

    router.add_route("/metrics", get_metrics_handler(), methods=["GET"])

    # ==================== SSE STREAM ====================

    async def _sse_event_stream(request: Request, queue: asyncio.Queue[dict[str, Any]]):  # pragma: no cover - requires live HTTP streaming (integration test)
        """Gerador SSE que transmite eventos enquanto a conexão permanecer ativa."""

        heartbeat_interval = 15.0
        last_heartbeat = asyncio.get_event_loop().time()

        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=heartbeat_interval)
                except asyncio.TimeoutError:
                    now_iso = datetime.now().isoformat()
                    message = {"type": "heartbeat", "timestamp": now_iso}

                payload = f"data: {json.dumps(message)}\n\n"
                yield payload.encode("utf-8")

                last_heartbeat = asyncio.get_event_loop().time()

                # Enforce heartbeat in case of quiet stream
                if asyncio.get_event_loop().time() - last_heartbeat >= heartbeat_interval:
                    heartbeat = {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                    yield f"data: {json.dumps(heartbeat)}\n\n".encode("utf-8")
        finally:
            if queue in sse_subscribers:
                sse_subscribers.remove(queue)

    @router.get("/stream/sse")
    async def stream_sse(request: Request):  # pragma: no cover - StreamingResponse blocks TestClient (integration test)
        """Endpoint SSE para cockpit e frontend React."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=250)
        sse_subscribers.append(queue)

        initial_state = {
            "type": "connection_ack",
            "timestamp": datetime.now().isoformat(),
            "recent_events": len(event_history),
        }
        queue.put_nowait(initial_state)

        return StreamingResponse(
            _sse_event_stream(request, queue),
            media_type="text/event-stream",
        )

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
                except TimeoutError:  # pragma: no cover - TestClient doesn't support timeout control (integration test)
                    # Send heartbeat
                    await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})

        except WebSocketDisconnect:
            active_connections.remove(websocket)
        except Exception as e:  # pragma: no cover - general exception handler (integration test)
            print(f"WebSocket error: {e}")
            if websocket in active_connections:
                active_connections.remove(websocket)

    # ==================== BACKGROUND BROADCAST LOOP ====================

    async def _periodic_state_broadcast():  # pragma: no cover - infinite background loop (integration test)
        """Envia snapshot periódico do estado para consumidores."""
        while True:
            await asyncio.sleep(5.0)
            try:
                if not consciousness_system:
                    continue

                tig = consciousness_system.get("tig")
                esgt = consciousness_system.get("esgt")
                arousal = consciousness_system.get("arousal")

                arousal_state = None
                if arousal and hasattr(arousal, "get_current_arousal"):
                    arousal_state = arousal.get_current_arousal()

                snapshot = {
                    "type": "state_snapshot",
                    "timestamp": datetime.now().isoformat(),
                    "arousal": getattr(arousal_state, "arousal", None),
                    "esgt_active": getattr(esgt, "_running", False),
                    "events_count": len(event_history),
                }
                await broadcast_to_consumers(snapshot)
            except Exception:
                continue

    background_tasks: list[asyncio.Task] = []

    @router.on_event("startup")
    async def _start_background_tasks():  # pragma: no cover - TestClient doesn't trigger FastAPI lifecycle (integration test)
        background_tasks.append(asyncio.create_task(_periodic_state_broadcast()))

    @router.on_event("shutdown")
    async def _stop_background_tasks():  # pragma: no cover - TestClient doesn't trigger FastAPI lifecycle (integration test)
        for task in background_tasks:
            task.cancel()
        background_tasks.clear()

    return router
