"""FastAPI application for Narrative Filter Service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from narrative_filter_service import health_api
from narrative_filter_service.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager."""
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

    uvicorn.run(app, host=settings.host, port=settings.port)
