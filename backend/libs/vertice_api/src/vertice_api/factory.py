"""FastAPI application factory."""

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vertice_core import BaseServiceSettings, get_logger, instrument_fastapi, setup_tracing

from .health import create_health_router
from .middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware


def create_app(
    settings: BaseServiceSettings,
    title: str | None = None,
    description: str | None = None,
    dependency_checks: dict[str, Any] | None = None,
) -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title=title or settings.service_name,
        description=description or f"{settings.service_name} API",
        version=settings.service_version,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    logger = get_logger(settings.service_name, level=settings.log_level)

    if settings.otel_enabled:  # pragma: no cover
        setup_tracing(
            settings.service_name,
            settings.service_version,
            endpoint=settings.otel_endpoint,
        )
        instrument_fastapi(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware, logger=logger)

    health_router = create_health_router(
        settings.service_name,
        settings.service_version,
        dependency_checks=dependency_checks,
    )
    app.include_router(health_router)

    @app.on_event("startup")  # pragma: no cover
    async def startup_event() -> None:
        """Log startup."""
        logger.info(
            "service_starting",
            service=settings.service_name,
            version=settings.service_version,
            environment=settings.environment,
            port=settings.port,
        )

    @app.on_event("shutdown")  # pragma: no cover
    async def shutdown_event() -> None:
        """Log shutdown."""
        logger.info("service_shutting_down", service=settings.service_name)

    return app
