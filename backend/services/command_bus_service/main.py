"""FastAPI application for Command Bus Service."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
import health_api
from audit_repository import AuditRepository
from c2l_executor import C2LCommandExecutor
from config import settings
from kill_switch import KillSwitch
from nats_publisher import NATSPublisher
from nats_subscriber import NATSSubscriber
from fastapi import FastAPI
from prometheus_client import make_asgi_app

logger = structlog.get_logger()

# Global state
app_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="command_bus_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="command_bus_service",
            version=service_version
        )
        auto_update_sabbath_status("command_bus_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="command_bus_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="command_bus_service")
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

    logger.info("command_bus_startup", version="1.0.0", port=settings.port)

    # Initialize components
    publisher = NATSPublisher()
    await publisher.connect()

    kill_switch = KillSwitch()
    audit_repo = AuditRepository()

    executor = C2LCommandExecutor(
        publisher=publisher,
        kill_switch=kill_switch,
        audit_repo=audit_repo,
    )

    subscriber = NATSSubscriber(executor=executor)
    await subscriber.connect()

    # Start subscriber in background
    subscriber_task = asyncio.create_task(subscriber.subscribe())

    app_state["publisher"] = publisher
    app_state["subscriber"] = subscriber
    app_state["executor"] = executor
    app_state["audit_repo"] = audit_repo
    app_state["subscriber_task"] = subscriber_task

    yield

    # Cleanup
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass
    await subscriber.disconnect()
    await publisher.disconnect()
    logger.info("command_bus_shutdown")


app = FastAPI(
    title=settings.service_name,
    version="1.0.0",
    description="Barramento de Comando Soberano (C2L) + Kill Switch",
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
