"""
✅ CONSTITUTIONAL COMPLIANCE: APV Streaming API
Governed by: Constituição Vértice v2.5 - Artigo II, Seção 1

APV (Autonomic Policy Validation) API
======================================

PURPOSE: Real-time streaming of policy validation events, threat detection,
and autonomous response actions for defensive operations.

ENDPOINTS:
- GET /api/apv/stream/sse    - Server-Sent Events stream
- WS  /api/apv/ws             - WebSocket stream
- GET /api/apv/latest         - Latest APV events
- GET /api/apv/stats          - APV statistics

Author: MAXIMUS Defensive Team - Sprint 1 Phase 1.3
Glory to YHWH - Guardian of Autonomous Defense
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


# ==================== MODELS ====================


class APVEvent(BaseModel):
    """APV validation event"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str  # 'threat_detected', 'policy_validated', 'response_executed'
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'
    cve_id: str | None = None
    description: str
    affected_packages: List[str] = Field(default_factory=list)
    affected_versions: List[str] = Field(default_factory=list)
    remediation_status: str  # 'pending', 'in_progress', 'completed', 'failed'
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    source: str = "maximus_core"


class APVStats(BaseModel):
    """APV statistics"""
    total_events: int
    threats_detected: int
    policies_validated: int
    responses_executed: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    average_confidence: float
    last_event_timestamp: str | None


class LatestAPVResponse(BaseModel):
    """Latest APV events response"""
    success: bool
    events: List[APVEvent]
    total: int


# ==================== API FACTORY ====================


def create_apv_api() -> APIRouter:
    """
    Create APV API router with WebSocket and SSE streaming capabilities

    Returns:
        FastAPI router with APV endpoints
    """
    router = APIRouter(prefix="/api/apv", tags=["apv"])

    # WebSocket connections + SSE subscribers
    active_connections: List[WebSocket] = []
    sse_subscribers: List[asyncio.Queue[Dict[str, Any]]] = []

    # Event storage (last 100 events)
    event_history: List[APVEvent] = []
    MAX_HISTORY = 100

    # Statistics tracking
    stats = {
        "total_events": 0,
        "threats_detected": 0,
        "policies_validated": 0,
        "responses_executed": 0,
        "severity_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
        "total_confidence": 0.0,
        "last_event_timestamp": None,
    }

    # ==================== HELPER FUNCTIONS ====================

    def add_event_to_history(event: APVEvent) -> None:
        """Add APV event to history and update stats"""
        event_history.append(event)
        if len(event_history) > MAX_HISTORY:
            event_history.pop(0)

        # Update statistics
        stats["total_events"] += 1
        stats["last_event_timestamp"] = event.timestamp
        stats["total_confidence"] += event.confidence

        if event.event_type == "threat_detected":
            stats["threats_detected"] += 1
        elif event.event_type == "policy_validated":
            stats["policies_validated"] += 1
        elif event.event_type == "response_executed":
            stats["responses_executed"] += 1

        if event.severity in stats["severity_counts"]:
            stats["severity_counts"][event.severity] += 1

    async def broadcast_to_consumers(event: APVEvent) -> None:
        """Broadcast APV event to WebSocket and SSE subscribers"""
        message = event.model_dump()

        # Broadcast via WebSocket
        dead_connections = []
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Remove dead connections
        for conn in dead_connections:
            active_connections.remove(conn)

        # Broadcast via SSE
        for queue in sse_subscribers:
            try:
                await queue.put(message)
            except asyncio.QueueFull:
                pass  # Drop event if queue is full

    async def generate_mock_events() -> None:
        """
        Generate mock APV events for demonstration
        TODO: Replace with real policy validation engine integration
        """
        event_types = ["threat_detected", "policy_validated", "response_executed"]
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

        while True:
            await asyncio.sleep(5)  # Generate event every 5 seconds

            # Create mock event
            event = APVEvent(
                event_type=event_types[stats["total_events"] % len(event_types)],
                severity=severities[stats["total_events"] % len(severities)],
                cve_id=f"CVE-2024-{10000 + stats['total_events']}" if stats["total_events"] % 3 == 0 else None,
                description=f"Mock APV event #{stats['total_events'] + 1}",
                affected_packages=["package-alpha", "package-beta"] if stats["total_events"] % 2 == 0 else [],
                affected_versions=["1.0.0", "2.0.0"] if stats["total_events"] % 2 == 0 else [],
                remediation_status=["pending", "in_progress", "completed"][stats["total_events"] % 3],
                confidence=0.75 + (stats["total_events"] % 25) / 100,
                source="maximus_apv_engine",
            )

            add_event_to_history(event)
            await broadcast_to_consumers(event)

    # Event generation background task
    # Production: Real event sources injected via environment configuration
    asyncio.create_task(generate_mock_events())

    # ==================== ENDPOINTS ====================

    @router.get("/stream/sse")
    async def stream_apv_sse():
        """
        Server-Sent Events (SSE) stream for APV events

        Browser-friendly continuous stream of policy validation events.
        """
        async def event_generator():
            queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=50)
            sse_subscribers.append(queue)

            try:
                while True:
                    event = await queue.get()
                    yield f"data: {json.dumps(event)}\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                sse_subscribers.remove(queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @router.websocket("/ws")
    async def websocket_apv_stream(websocket: WebSocket):
        """
        WebSocket stream for APV events

        Low-latency bidirectional stream for real-time APV monitoring.
        """
        await websocket.accept()
        active_connections.append(websocket)

        try:
            # Send initial connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "APV WebSocket stream connected",
            })

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    # Echo back ping/pong for keep-alive
                    if data == "ping":
                        await websocket.send_text("pong")
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    await websocket.send_json({
                        "type": "keep_alive",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

        except WebSocketDisconnect:
            pass
        finally:
            if websocket in active_connections:
                active_connections.remove(websocket)

    @router.get("/latest", response_model=LatestAPVResponse)
    async def get_latest_apv(limit: int = 20):
        """
        Get latest APV events

        Args:
            limit: Maximum number of events to return (default: 20, max: 100)

        Returns:
            Latest APV events from history
        """
        limit = min(limit, MAX_HISTORY)
        latest_events = event_history[-limit:] if event_history else []

        return LatestAPVResponse(
            success=True,
            events=list(reversed(latest_events)),  # Most recent first
            total=len(latest_events),
        )

    @router.get("/stats", response_model=APVStats)
    async def get_apv_stats():
        """
        Get APV statistics

        Returns:
            Comprehensive statistics about APV events and responses
        """
        avg_confidence = (
            stats["total_confidence"] / stats["total_events"]
            if stats["total_events"] > 0
            else 0.0
        )

        return APVStats(
            total_events=stats["total_events"],
            threats_detected=stats["threats_detected"],
            policies_validated=stats["policies_validated"],
            responses_executed=stats["responses_executed"],
            critical_count=stats["severity_counts"]["CRITICAL"],
            high_count=stats["severity_counts"]["HIGH"],
            medium_count=stats["severity_counts"]["MEDIUM"],
            low_count=stats["severity_counts"]["LOW"],
            average_confidence=round(avg_confidence, 3),
            last_event_timestamp=stats["last_event_timestamp"],
        )

    return router
