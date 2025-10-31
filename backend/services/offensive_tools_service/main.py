"""
Offensive Tools Service - MAXIMUS Integration.

Microservice exposing offensive security tools with MAXIMUS AI enhancement.
Includes reconnaissance, exploitation, and post-exploitation capabilities.

Philosophy: Surgical precision with ethical boundaries.
"""
import os
from datetime import datetime
from typing import Dict

import structlog
import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

# Import offensive tools router
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from security.offensive.api.offensive_tools import router as offensive_router

log = structlog.get_logger()

# ============================================================================
# FastAPI App Configuration
# ============================================================================

app = FastAPI(
    title="MAXIMUS Offensive Tools Service",
    description="AI-enhanced offensive security tools with ethical guardrails",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Register offensive tools router
app.include_router(offensive_router)


# ============================================================================
# Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="offensive_tools_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="offensive_tools_service",
            version=service_version
        )
        auto_update_sabbath_status("offensive_tools_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="offensive_tools_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="offensive_tools_service")
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

    log.info(
        "offensive_tools_service_starting",
        service="offensive_tools",
        version="1.0.0"
    )
    
    # Initialize tool registry
    from security.offensive.core.tool_registry import registry
    registry.discover_tools()
    
    stats = registry.get_stats()
    log.info(
        "tools_registered",
        total=stats["total_tools"],
        by_category=stats["by_category"]
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    log.info("offensive_tools_service_shutting_down")


# ============================================================================
# Root & Health Endpoints
# ============================================================================

@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["Meta"]
)
async def root() -> Dict:
    """Service root endpoint."""
    return {
        "service": "offensive_tools",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["Meta"]
)
async def health() -> Dict:
    """Comprehensive health check."""
    from security.offensive.core.tool_registry import registry

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck

    
    stats = registry.get_stats()
    
    return {
        "status": "healthy",
        "service": "offensive_tools",
        "registry": {
            "tools_total": stats["total_tools"],
            "tools_ready": stats["instantiated"],
            "categories": stats["by_category"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8010"))
    host = os.getenv("HOST", "0.0.0.0")
    
    log.info(
        "starting_offensive_tools_service",
        host=host,
        port=port
    )
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
