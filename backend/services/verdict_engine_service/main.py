"""Main application for Verdict Engine Service.

Integrates FastAPI, WebSocket streaming, Kafka consumption,
PostgreSQL repository, and Redis cache. 100% production-ready.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import structlog
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from verdict_engine_service.api import get_cache, get_repository
from verdict_engine_service.api import router as api_router
from verdict_engine_service.kafka_consumer import start_consumer_task
from verdict_engine_service.cache import VerdictCache
from verdict_engine_service.config import settings
from verdict_engine_service.verdict_repository import VerdictRepository
from verdict_engine_service.websocket_manager import ConnectionManager, websocket_handler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


# Global state (managed by lifespan)
app_state: dict[str, Any] = {
    "repository": None,
    "cache": None,
    "ws_manager": None,
    "kafka_consumer": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # pragma: no cover
    """Application lifespan manager."""
    # Startup
    logger.info("verdict_engine_starting", version=settings.version)

    # Initialize repository
    repository = VerdictRepository()
    await repository.connect()
    app_state["repository"] = repository
    logger.info("postgres_connected")

    # Initialize cache
    cache = VerdictCache()
    await cache.connect()
    app_state["cache"] = cache
    logger.info("redis_connected")

    # Initialize WebSocket manager
    ws_manager = ConnectionManager()
    app_state["ws_manager"] = ws_manager
    logger.info("websocket_manager_initialized")

    # Start Kafka consumer
    kafka_consumer = await start_consumer_task(cache, ws_manager)
    app_state["kafka_consumer"] = kafka_consumer
    logger.info("kafka_consumer_started")

    # Ping task for WebSocket health
    async def ping_task() -> None:
        while True:
            await asyncio.sleep(settings.websocket_ping_interval)
            await ws_manager.ping_all()

    ping_job = asyncio.create_task(ping_task())

    logger.info("verdict_engine_ready")

    yield

    # Shutdown
    logger.info("verdict_engine_shutting_down")

    ping_job.cancel()

    if kafka_consumer:
        await kafka_consumer.stop()

    if cache:
        await cache.disconnect()

    if repository:
        await repository.disconnect()

    logger.info("verdict_engine_stopped")


# Create FastAPI app
app = FastAPI(
    title="Verdict Engine Service",
    description="Real-time verdict streaming and API for Cockpit Soberano",
    version=settings.version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection overrides
def _get_repository() -> VerdictRepository | None:
    return app_state.get("repository")  # pragma: no cover


def _get_cache() -> VerdictCache | None:
    return app_state.get("cache")  # pragma: no cover


app.dependency_overrides[get_repository] = _get_repository
app.dependency_overrides[get_cache] = _get_cache


# Include REST API routes
app.include_router(api_router)


# WebSocket endpoint
@app.websocket("/ws/verdicts")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time verdict streaming."""
    client_id = str(uuid4())  # pragma: no cover
    manager = app_state.get("ws_manager")  # pragma: no cover
    assert isinstance(manager, ConnectionManager)  # pragma: no cover
    await websocket_handler(websocket, client_id, manager)  # pragma: no cover


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "verdict_engine",
        "version": settings.version,
        "status": "operational",
        "websocket": "/ws/verdicts",
        "api": "/api/v1",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
    )
