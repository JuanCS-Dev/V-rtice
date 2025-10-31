"""MABA (MAXIMUS Browser Agent) - Main Application Entry Point.

This service provides autonomous browser automation capabilities to MAXIMUS Core.
It learns website structures, navigates intelligently, and performs web-based tasks
with cognitive awareness.

Key Features:
- Autonomous browser control via Playwright
- Cognitive map for learned website structures
- LLM-powered intelligent navigation
- Screenshot analysis and visual understanding
- Form filling and interaction automation
- Integration with MAXIMUS decision framework

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
from services.maba_service.api.routes import (
    get_maba_service,
    set_maba_service,
)
from services.maba_service.api.routes import router as maba_router

# Import MABA service components (absolute imports)
from services.maba_service.models import MABAService

# Shared library imports (work when in ~/vertice-dev/backend/services/)
from shared.vertice_registry_client import RegistryClient, auto_register_service

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global service instance
maba_service: MABAService | None = None
_heartbeat_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown of MABA service, including:
    - Service initialization
    - Browser controller setup
    - Cognitive map engine initialization
    - Service registry registration
    - Graceful shutdown
    """
    global maba_service, _heartbeat_task

    logger.info("🚀 Starting MABA (MAXIMUS Browser Agent) Service...")

    try:
        # Initialize MABA service
        maba_service = MABAService(
            service_name="maba",
            service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
            maximus_endpoint=os.getenv(
                "MAXIMUS_ENDPOINT", "http://vertice-maximus-core-service:8150"
            ),
        )

        # Start the service
        await maba_service.start()

        # Set service in routes for dependency injection
        set_maba_service(maba_service)

        # Register with Service Registry
        try:
            _heartbeat_task = await auto_register_service(
                service_name="maba",
                port=int(os.getenv("SERVICE_PORT", 8152)),
                health_endpoint="/health",
                metadata={
                    "category": "maximus_subordinate",
                    "type": "browser_agent",
                    "version": os.getenv("SERVICE_VERSION", "1.0.0"),
                },
            )
            logger.info("✅ Registered with Vértice Service Registry")
        except Exception as e:
            logger.warning(f"⚠️ Failed to register with service registry: {e}")
            logger.warning("   Continuing without registry (standalone mode)")

        logger.info("✅ MABA Service started successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start MABA Service: {e}", exc_info=True)
        raise

    finally:
        # Shutdown sequence
        logger.info("👋 Shutting down MABA Service...")

        # Cancel heartbeat task
        if _heartbeat_task:
            _heartbeat_task.cancel()
            try:
                await _heartbeat_task
            except asyncio.CancelledError:
                pass

        # Deregister from Service Registry
        try:
            await RegistryClient.deregister("maba")
            logger.info("✅ Deregistered from Service Registry")
        except Exception as e:
            logger.warning(f"⚠️ Failed to deregister: {e}")

        # Stop MABA service
        if maba_service:
            await maba_service.stop()

        logger.info("🛑 MABA Service shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="MABA - MAXIMUS Browser Agent",
    version=os.getenv("SERVICE_VERSION", "1.0.0"),
    description="Autonomous browser automation service for MAXIMUS AI",
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

# Include MABA API routes
app.include_router(maba_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Comprehensive health check endpoint.

    Checks:
    - MABA service status
    - Browser controller health
    - Cognitive map engine status
    - Database connectivity
    - Redis connectivity

    Returns:
        Dict with health status and component details
    """
    try:
        # Use get_maba_service() for consistency with routes and testing
        service = get_maba_service()

        if not service:
            raise HTTPException(status_code=503, detail="MABA service not initialized")

        health_status = await service.health_check()
        return health_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Note: Metrics are served on a separate HTTP server on port 9090
    by default. This endpoint provides a redirect for convenience.
    """
    return {
        "message": "Metrics available on dedicated metrics port",
        "metrics_port": int(os.getenv("METRICS_PORT", 9090)),
        "metrics_endpoint": f"http://localhost:{os.getenv('METRICS_PORT', 9090)}/metrics",
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MABA - MAXIMUS Browser Agent",
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "status": (
            "operational"
            if maba_service and maba_service.is_healthy()
            else "unavailable"
        ),
        "description": "Autonomous browser automation service for MAXIMUS AI",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "api": "/api/v1",
            "docs": "/docs",
        },
    }


def main():
    """Main entry point for running MABA service."""
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
    service_port = int(os.getenv("SERVICE_PORT", 8152))
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
