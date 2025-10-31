"""FastAPI application for Narrative Filter Service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from prometheus_client import make_asgi_app

import health_api
from config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="narrative_filter_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="narrative_filter_service",
            version=service_version
        )
        auto_update_sabbath_status("narrative_filter_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="narrative_filter_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="narrative_filter_service")
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

    logger.info("narrative_filter_startup", version="1.0.0", port=settings.port)
    yield
    logger.info("narrative_filter_shutdown")


app = FastAPI(
    title=settings.service_name,
    version="1.0.0",
    description="Filtro de Narrativas Multi-Agente - 3 Camadas",
    lifespan=lifespan,
)

# Health endpoint
app.include_router(health_api.router, prefix="/health", tags=["health"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


    uvicorn.run(app, host=settings.host, port=settings.port)
