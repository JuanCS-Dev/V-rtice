"""
Unit tests for Presentation Layer - FastAPI App
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from service_template.infrastructure.config import Settings
from service_template.presentation.app import create_app, lifespan


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings."""
    return Settings(
        service_name="test-service",
        service_version="1.0.0",
        environment="development",
        port=8000,
        host="0.0.0.0",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        enable_metrics=True,
        enable_tracing=False,
        cors_origins=["http://localhost:3000"],
        log_level="INFO",
    )


@pytest.fixture
def mock_database() -> AsyncMock:
    """Create mock database."""
    db = AsyncMock()
    db.create_tables = AsyncMock()
    db.close = AsyncMock()
    return db


class TestLifespan:
    """Tests for lifespan context manager."""

    async def test_lifespan_startup_and_shutdown(
        self, mock_settings: Settings, mock_database: AsyncMock
    ) -> None:
        """Test lifespan startup and shutdown events."""
        app = FastAPI()

        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ), patch(
            "service_template.presentation.app.Database",
            return_value=mock_database,
        ):
            async with lifespan(app):
                assert hasattr(app.state, "db")
                assert app.state.db == mock_database
                mock_database.create_tables.assert_called_once()

            mock_database.close.assert_called_once()


class TestCreateApp:
    """Tests for create_app factory."""

    def test_create_app_basic_setup(self, mock_settings: Settings) -> None:
        """Test basic app creation."""
        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ):
            app = create_app()

            assert isinstance(app, FastAPI)
            assert app.title == mock_settings.service_name
            assert app.version == mock_settings.service_version

    def test_create_app_includes_router(self, mock_settings: Settings) -> None:
        """Test app includes API router."""
        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ):
            app = create_app()

            # Check router is included by verifying routes exist
            route_paths = [route.path for route in app.routes]
            assert "/api/v1/entities/" in route_paths

    def test_create_app_cors_middleware(self, mock_settings: Settings) -> None:
        """Test CORS middleware is configured."""
        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ):
            app = create_app()

            # Check CORS middleware exists by checking middleware stack
            assert len(app.user_middleware) > 0

    def test_create_app_metrics_enabled(self, mock_settings: Settings) -> None:
        """Test metrics endpoint when enabled."""
        mock_settings.enable_metrics = True

        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ):
            app = create_app()

            # Check metrics route exists
            route_paths = [route.path for route in app.routes]
            assert "/metrics" in route_paths

    def test_create_app_metrics_disabled(self, mock_settings: Settings) -> None:
        """Test metrics endpoint when disabled."""
        mock_settings.enable_metrics = False

        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ):
            app = create_app()

            # Check metrics route doesn't exist
            route_paths = [route.path for route in app.routes]
            assert "/metrics" not in route_paths

    def test_health_endpoint(self, mock_settings: Settings) -> None:
        """Test health check endpoint."""
        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ), patch("service_template.presentation.app.Database"):
            app = create_app()
            client = TestClient(app)

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == mock_settings.service_name

    def test_root_endpoint(self, mock_settings: Settings) -> None:
        """Test root endpoint."""
        with patch(
            "service_template.presentation.app.get_settings",
            return_value=mock_settings,
        ), patch("service_template.presentation.app.Database"):
            app = create_app()
            client = TestClient(app)

            response = client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == mock_settings.service_name
            assert data["version"] == mock_settings.service_version
            assert data["status"] == "running"
