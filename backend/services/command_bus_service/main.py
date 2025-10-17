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

    uvicorn.run(app, host=settings.host, port=settings.port)
