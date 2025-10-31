"""MVP (MAXIMUS Vision Protocol) - Main Application Entry Point.

This service generates real-time narrative intelligence for MAXIMUS by observing
system metrics and creating human-readable stories about system behavior, performance,
and emerging patterns.

Key Features:
- Real-time system metrics observation (Prometheus)
- LLM-powered narrative generation (Claude)
- Time series data analysis and visualization
- Anomaly detection and alert generation
- Executive briefings and status reports
- Integration with MAXIMUS consciousness

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import start_http_server
from api.routes import (
    get_mvp_service,
    set_mvp_service,
)
from api.routes import router as mvp_router

# Import MVP service components
from models import MVPService

# Shared library imports (work when in ~/vertice-dev/backend/services/)
from shared.vertice_registry_client import RegistryClient, auto_register_service

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global service instance
mvp_service: MVPService | None = None
_heartbeat_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown of MVP service.
    """
    global mvp_service, _heartbeat_task

    logger.info("🚀 Starting MVP (MAXIMUS Vision Protocol) Service...")

    try:
        # Initialize MVP service
        mvp_service = MVPService(
            service_name="mvp",
            service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
            maximus_endpoint=os.getenv(
                "MAXIMUS_ENDPOINT", "http://vertice-maximus-core-service:8150"
            ),
        )

        # Start the service
        await mvp_service.start()

        # Set service in routes for dependency injection
        set_mvp_service(mvp_service)

        # Register with Service Registry
        try:
            _heartbeat_task = await auto_register_service(
                service_name="mvp",
                port=int(os.getenv("SERVICE_PORT", 8153)),
                health_endpoint="/health",
                metadata={
                    "category": "maximus_subordinate",
                    "type": "vision_protocol",
                    "version": os.getenv("SERVICE_VERSION", "1.0.0"),
                },
            )
            logger.info("✅ Registered with Vértice Service Registry")
        except Exception as e:
            logger.warning(f"⚠️ Failed to register with service registry: {e}")
            logger.warning("   Continuing without registry (standalone mode)")

        logger.info("✅ MVP Service started successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start MVP Service: {e}", exc_info=True)
        raise

    finally:
        # Shutdown sequence
        logger.info("👋 Shutting down MVP Service...")

        # Cancel heartbeat task
        if _heartbeat_task:
            _heartbeat_task.cancel()
            try:
                await _heartbeat_task
            except asyncio.CancelledError:
                pass

        # Deregister from Service Registry
        try:
            await RegistryClient.deregister("mvp")
            logger.info("✅ Deregistered from Service Registry")
        except Exception as e:
            logger.warning(f"⚠️ Failed to deregister: {e}")

        # Stop MVP service
        if mvp_service:
            await mvp_service.stop()

        logger.info("🛑 MVP Service shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="MVP - MAXIMUS Vision Protocol",
    version=os.getenv("SERVICE_VERSION", "1.0.0"),
    description="Real-time narrative intelligence for MAXIMUS AI",
    lifespan=lifespan,
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include MVP API routes
app.include_router(mvp_router, prefix="/api/v1")

# Include WebSocket routes
from websocket_routes import router as websocket_router

app.include_router(websocket_router)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Comprehensive health check endpoint."""
    try:
        # Use get_mvp_service() for consistency with routes and testing
        service = get_mvp_service()

        if not service:
            raise HTTPException(status_code=503, detail="MVP service not initialized")

        health_status = await service.health_check()
        return health_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return {
        "message": "Metrics available on dedicated metrics port",
        "metrics_port": int(os.getenv("METRICS_PORT", 9090)),
        "metrics_endpoint": f"http://localhost:{os.getenv('METRICS_PORT', 9090)}/metrics",
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MVP - MAXIMUS Vision Protocol",
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "status": (
            "operational" if mvp_service and mvp_service.is_healthy() else "unavailable"
        ),
        "description": "Real-time narrative intelligence for MAXIMUS AI",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "api": "/api/v1",
            "docs": "/docs",
        },
    }


def main():
    """Main entry point for running MVP service."""
    # Ensure Prometheus multiprocess directory exists
    prom_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus")
    os.makedirs(prom_dir, exist_ok=True)

    # Start Prometheus metrics server on separate port
    metrics_port = int(os.getenv("METRICS_PORT", 9090))
    try:
        start_http_server(metrics_port)
        logger.info(f"📈 Prometheus metrics server started on port {metrics_port}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start metrics server: {e}")

    # Run FastAPI application
    service_host = os.getenv("SERVICE_HOST", "0.0.0.0")
    service_port = int(os.getenv("SERVICE_PORT", 8153))
    workers = int(os.getenv("WORKER_PROCESSES", 1))

    uvicorn.run(
        app,
        host=service_host,
        port=service_port,
        workers=workers,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        timeout_keep_alive=75,
    )


if __name__ == "__main__":
    main()
