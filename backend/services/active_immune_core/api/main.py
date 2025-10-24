"""FastAPI Application - PRODUCTION-READY

Main FastAPI application for Active Immune Core REST API.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..monitoring.health_checker import HealthChecker, HealthStatus
from ..monitoring.metrics_collector import MetricsCollector
from ..monitoring.prometheus_exporter import PrometheusExporter

# Import Service Registry client
try:
    from shared.vertice_registry_client import auto_register_service, RegistryClient
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False
    logger.warning("Service Registry client not available - running in standalone mode")

logger = logging.getLogger(__name__)


# Global instances (initialized in lifespan)
prometheus_exporter: Optional[PrometheusExporter] = None
health_checker: Optional[HealthChecker] = None
metrics_collector: Optional[MetricsCollector] = None
_heartbeat_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown logic.
    """
    # Startup
    logger.info("Starting Active Immune Core API...")

    global prometheus_exporter, health_checker, metrics_collector, _heartbeat_task

    # Initialize monitoring components
    prometheus_exporter = PrometheusExporter(namespace="immune_core_api")
    health_checker = HealthChecker(check_interval=30, enable_auto_check=True)
    metrics_collector = MetricsCollector(history_size=1000, aggregation_interval=60)

    # Initialize dependency health checker
    from monitoring.dependency_health import DependencyHealthChecker

    dep_health_checker = DependencyHealthChecker()

    # Register health check components
    health_checker.register_component("api", check_func=check_api_health)
    health_checker.register_component("kafka", check_func=dep_health_checker.check_kafka_health)
    health_checker.register_component("redis", check_func=dep_health_checker.check_redis_health)
    health_checker.register_component("postgres", check_func=dep_health_checker.check_postgres_health)

    # Start auto health checks
    await health_checker.start_auto_check()

    # Initialize Core System
    from api.core_integration import CoreManager
    from api.routes.websocket import get_event_bridge

    core_manager = CoreManager.get_instance()
    await core_manager.initialize()
    logger.info("✓ Core System initialized")

    # Initialize and start EventBridge
    event_bridge = get_event_bridge()
    await event_bridge.start()
    logger.info("✓ EventBridge started")

    # Auto-register with Service Registry
    if REGISTRY_AVAILABLE:
        try:
            _heartbeat_task = await auto_register_service(
                service_name="active_immune_core",
                port=8200,  # Internal container port
                health_endpoint="/health",
                metadata={"category": "immune_system", "version": "1.0.0"}
            )
            logger.info("✓ Registered with Vértice Service Registry")
        except Exception as e:
            logger.warning(f"Failed to register with service registry: {e}")

    logger.info("Active Immune Core API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Active Immune Core API...")

    # Deregister from Service Registry
    if _heartbeat_task:
        _heartbeat_task.cancel()
    if REGISTRY_AVAILABLE:
        try:
            await RegistryClient.deregister("active_immune_core")
        except:
            pass

    # Stop EventBridge
    event_bridge = get_event_bridge()
    await event_bridge.stop()
    logger.info("✓ EventBridge stopped")

    # Shutdown Core System
    core_manager = CoreManager.get_instance()
    await core_manager.stop()
    logger.info("✓ Core System shutdown")

    # Stop health checks
    await health_checker.stop_auto_check()

    logger.info("Active Immune Core API shutdown complete")


async def check_api_health():
    """Check API health"""
    # API is healthy if we can respond
    return HealthStatus.HEALTHY, {"status": "operational"}


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Active Immune Core API",
        description="Enterprise-grade REST API for biologically-inspired cyber defense system",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all requests and track metrics"""
        start_time = time.time()

        # Record request
        if prometheus_exporter:
            prometheus_exporter.record_operation_duration("request_started", 0.0)

        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            if prometheus_exporter:
                prometheus_exporter.record_api_request(
                    endpoint=request.url.path,
                    method=request.method,
                    status=response.status_code,
                    latency=duration,
                )

            # Log request
            logger.info(f"{request.method} {request.url.path} status={response.status_code} duration={duration:.3f}s")

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record error
            if prometheus_exporter:
                prometheus_exporter.record_api_request(
                    endpoint=request.url.path,
                    method=request.method,
                    status=500,
                    latency=duration,
                )

            logger.error(f"{request.method} {request.url.path} error={str(e)} duration={duration:.3f}s")

            raise

    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},  # FastAPI standard format
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": str(exc),
            },
        )

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root() -> Dict[str, Any]:
        """
        Root endpoint - API information.

        Returns:
            API metadata
        """
        return {
            "name": "Active Immune Core API",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
        }

    # Register routers
    from active_immune_core.api.routes import agents, coordination, health, lymphnode, metrics
    from active_immune_core.api.routes import websocket as websocket_events
    from active_immune_core.api.websocket import router as websocket_router
    from active_immune_core.api.routes.defensive_tools import router as defensive_router

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
    app.include_router(agents.router, prefix="/agents", tags=["agents"])
    app.include_router(coordination.router, prefix="/coordination", tags=["coordination"])
    app.include_router(lymphnode.router, prefix="/lymphnode", tags=["lymphnode"])
    app.include_router(websocket_router, tags=["websocket"])
    app.include_router(websocket_events.router, tags=["websocket-events"])
    app.include_router(defensive_router, prefix="/api", tags=["defensive-tools"])
    
    logger.info("✓ All routers registered including defensive tools")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
