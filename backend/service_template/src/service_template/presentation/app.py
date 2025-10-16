"""
Presentation Layer - FastAPI Application

Main FastAPI application with middleware and configuration.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from ..infrastructure.config import get_settings
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    settings = get_settings()

    # Startup
    print(f"🚀 Starting {settings.service_name} v{settings.service_version}")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔌 Port: {settings.port}")

    yield

    # Shutdown
    print(f"👋 Shutting down {settings.service_name}")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version,
        description="Clean Architecture service template for Vértice MAXIMUS",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(router)

    # Metrics endpoint
    if settings.enable_metrics:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # Health check
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.service_name}

    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {
            "service": settings.service_name,
            "version": settings.service_version,
            "status": "running",
        }

    return app
