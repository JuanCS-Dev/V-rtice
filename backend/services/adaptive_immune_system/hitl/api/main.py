"""
HITL API Main Application - FastAPI app for Human-in-the-Loop console.

Features:
- REST API for APV reviews and decisions
- WebSocket support for real-time updates
- CORS enabled for web frontend
- Health check endpoint
- Metrics endpoint for Prometheus
- Request logging middleware
- Error handling middleware
- Prometheus metrics collection
- Distributed tracing (OpenTelemetry)

Usage:
    uvicorn hitl.api.main:app --reload --port 8003
"""

import logging
import time
from typing import Any, Dict

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .endpoints import apv_review_router, decisions_router
from ..models import WebSocketMessage

# Import monitoring modules
try:
    from ..monitoring import PrometheusMiddleware, metrics, setup_tracing
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    logging.warning("Monitoring modules not available - metrics disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Adaptive Immune System - HITL API",
    description="Human-in-the-Loop interface for APV review and decision-making",
    version="1.0.0",
    docs_url="/hitl/docs",
    redoc_url="/hitl/redoc",
    openapi_url="/hitl/openapi.json",
)

# --- Middleware ---

# Prometheus metrics middleware (must be first for accurate timing)
if MONITORING_ENABLED:
    app.add_middleware(PrometheusMiddleware)

# CORS middleware (allow web frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "https://console.vertice.ai",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Any:
    """Log all HTTP requests with timing."""
    start_time = time.time()

    # Log request
    logger.info(f"→ {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(
        f"← {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)"
    )

    return response


# --- Exception Handlers ---


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "path": request.url.path,
        },
    )


# --- Routers ---

# Include API routers
app.include_router(apv_review_router)
app.include_router(decisions_router)

# --- Root Endpoints ---


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "service": "Adaptive Immune System - HITL API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/hitl/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Used by:
    - Docker healthcheck
    - Kubernetes liveness/readiness probes
    - Load balancers

    Returns:
        Status and component health
    """
    # In production: Check database, RabbitMQ, GitHub API
    components = {
        "api": "healthy",
        "database": "healthy",  # Would check: SELECT 1
        "rabbitmq": "healthy",  # Would check: channel.is_open
        "github": "healthy",  # Would check: GET /rate_limit
    }

    all_healthy = all(status == "healthy" for status in components.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "components": components,
        "timestamp": time.time(),
    }


@app.get("/metrics", tags=["Metrics"])
async def metrics_endpoint() -> Response:
    """
    Metrics endpoint for Prometheus scraping.

    Returns Prometheus-formatted metrics including:
    - HTTP request metrics (RED method)
    - Business metrics (reviews, decisions)
    - System metrics (database, cache)
    - SLO tracking metrics

    Returns:
        Prometheus text format metrics
    """
    if MONITORING_ENABLED:
        return Response(
            content=metrics.get_metrics(),
            media_type=metrics.get_content_type()
        )
    else:
        # Fallback if monitoring not enabled
        return Response(
            content="# Monitoring not enabled\n",
            media_type="text/plain"
        )


# --- WebSocket ---

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connected clients."""
        message_json = message.model_dump_json()

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket: {e}")


# Global connection manager
manager = ConnectionManager()


@app.websocket("/hitl/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time updates.

    Events:
    - new_review: New APV submitted for review
    - decision_made: Human decision submitted
    - stats_update: Dashboard statistics updated

    Usage (JavaScript):
        const ws = new WebSocket('ws://localhost:8003/hitl/ws');
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            console.log(`Event: ${msg.event_type}`, msg.data);
        };
    """
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive
            # In production: Handle incoming messages (ping/pong, subscriptions)
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")

            # Echo back (for testing)
            await websocket.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


# --- Broadcast Helper ---


async def broadcast_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Broadcast event to all WebSocket clients.

    Call this from API endpoints when events occur.

    Args:
        event_type: Event type (new_review, decision_made, stats_update)
        data: Event data

    Example:
        await broadcast_event("decision_made", {
            "apv_id": "550e8400-e29b-41d4-a716-446655440001",
            "decision": "approve",
            "reviewer": "Alice Johnson"
        })
    """
    from datetime import datetime

    message = WebSocketMessage(
        event_type=event_type,
        data=data,
        timestamp=datetime.utcnow(),
    )

    await manager.broadcast(message)
    logger.info(f"Broadcasted event: {event_type}")


# --- Startup/Shutdown Events ---


@app.on_event("startup")
async def startup_event() -> None:
    """Run on application startup."""
    logger.info("🚀 HITL API starting up...")
    logger.info("   📝 Docs: http://localhost:8003/hitl/docs")
    logger.info("   🔌 WebSocket: ws://localhost:8003/hitl/ws")
    logger.info("   📊 Metrics: http://localhost:8003/metrics")

    # Initialize tracing if enabled
    if MONITORING_ENABLED:
        setup_tracing(
            service_name="hitl-api",
            jaeger_host="localhost",
            jaeger_port=6831
        )
        logger.info("   🔍 Tracing: http://localhost:16686 (Jaeger)")
        logger.info("   ✅ Monitoring: ENABLED")
    else:
        logger.warning("   ⚠️  Monitoring: DISABLED")

    # In production: Initialize database pool, RabbitMQ connection, etc.


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Run on application shutdown."""
    logger.info("🛑 HITL API shutting down...")

    # In production: Close database pool, RabbitMQ connection, etc.


# --- Main ---

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "hitl.api.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info",
    )
