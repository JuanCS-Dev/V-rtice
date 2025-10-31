"""
Main FastAPI application for Offensive Orchestrator Service.

Provides REST API for:
- Campaign planning and execution
- HOTL approval workflows
- Attack memory queries
- Service health and metrics
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from config import get_config
from models import HealthResponse
from api import router as api_router
from memory import AttackMemorySystem
from hotl_system import HOTLDecisionSystem


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="offensive_orchestrator_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="offensive_orchestrator_service",
            version=service_version
        )
        auto_update_sabbath_status("offensive_orchestrator_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="offensive_orchestrator_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="offensive_orchestrator_service")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {e}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()

    Application lifespan manager.

    Handles startup and shutdown:
    - Startup: Initialize DB connections, LLM clients, monitoring
    - Shutdown: Cleanup connections, flush logs
    """
    # Startup
    logger.info("🚀 Offensive Orchestrator Service starting...")

    config = get_config()
    logger.info(f"Configuration loaded: service_port={config.port}, llm_model={config.llm.model}")

    # Initialize Attack Memory System (PostgreSQL + Qdrant)
    try:
        memory_system = AttackMemorySystem()
        await memory_system.initialize()
        app.state.memory_system = memory_system
        logger.info("✅ Attack Memory System initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Attack Memory System: {e}", exc_info=True)
        # Continue startup even if memory system fails (graceful degradation)
        app.state.memory_system = None

    # Initialize HOTL Decision System
    try:
        hotl_system = HOTLDecisionSystem()
        app.state.hotl_system = hotl_system
        logger.info("✅ HOTL Decision System initialized")
    except Exception as e:
        logger.error(f"Failed to initialize HOTL System: {e}", exc_info=True)
        app.state.hotl_system = None

    logger.info("✅ Offensive Orchestrator Service ready")

    yield

    # Shutdown
    logger.info("🛑 Offensive Orchestrator Service shutting down...")

    # Cleanup Attack Memory System
    if hasattr(app.state, 'memory_system') and app.state.memory_system:
        try:
            app.state.memory_system.close()
            logger.info("✅ Attack Memory System closed")
        except Exception as e:
            logger.error(f"Error closing Attack Memory System: {e}")

    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Offensive Orchestrator Service",
    description="MAXIMUS AI-Driven Offensive Security Operations Orchestrator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware (configure based on environment)
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Restrict via environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions gracefully."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns service status and metadata.
    Used by Kubernetes liveness/readiness probes.
    """
    return HealthResponse(
        status="healthy",
        service="offensive_orchestrator_service",
        version="1.0.0",
        timestamp=datetime.utcnow(),
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service info."""
    return {
        "service": "offensive_orchestrator_service",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "api": "/api/v1",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


    config = get_config()

    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.log_level.lower(),
        access_log=True,
    )
