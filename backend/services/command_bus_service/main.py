"""FastAPI application for Command Bus Service."""

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
    logger.info("command_bus_startup", version="1.0.0", port=settings.port)
    yield
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
