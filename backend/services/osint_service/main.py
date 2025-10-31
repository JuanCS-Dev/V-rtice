"""
osint_service - FastAPI service
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging FIRST (before any usage)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Service Registry client
try:
    from shared.vertice_registry_client import auto_register_service, RegistryClient
    REGISTRY_AVAILABLE = True
except ImportError:
    logger.warning("Service Registry client not available - running in standalone mode")
    REGISTRY_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="osint_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="osint_service",
            version=service_version
        )
        auto_update_sabbath_status("osint_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="osint_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="osint_service")
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

    logger.info("Starting osint_service...")

    # Auto-register with Service Registry
    heartbeat_task = None
    if REGISTRY_AVAILABLE:
        try:
            heartbeat_task = await auto_register_service(
                service_name="osint_service",
                port=8049,  # Internal container port
                health_endpoint="/health",
                metadata={"category": "investigation", "version": "0.1.0"}
            )
            logger.info("✅ Registered with Vértice Service Registry")
        except Exception as e:
            logger.warning(f"Failed to register with service registry: {e}")

    yield

    # Cleanup
    logger.info("Shutting down osint_service...")
    if heartbeat_task:
        heartbeat_task.cancel()
    if REGISTRY_AVAILABLE:
        try:
            await RegistryClient.deregister("osint_service")
        except:
            pass


app = FastAPI(
    title="osint_service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "osint_service"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "osint_service",
        "version": "0.1.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck

    uvicorn.run(app, host="0.0.0.0", port=8000)
