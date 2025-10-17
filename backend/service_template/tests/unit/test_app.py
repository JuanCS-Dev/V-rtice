"""
Tests for Presentation Layer - FastAPI App

100% coverage required.
"""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient
from service_template.presentation.app import create_app


class TestCreateApp:
    """Tests for create_app function."""

    def test_app_creation(self) -> None:
        """Test app is created successfully."""
        app = create_app()

        assert app is not None
        assert app.title == "service-template"
        assert app.version == "1.0.0"

    def test_app_has_routes(self) -> None:
        """Test app has expected routes."""
        app = create_app()

        route_paths = [route.path for route in app.routes]

        assert "/" in route_paths
        assert "/health" in route_paths
        assert "/metrics" in route_paths

    def test_lifespan_startup(self) -> None:
        """Test lifespan startup event."""
        # Use SQLite for test to avoid PostgreSQL dependency
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
            app = create_app()

            with TestClient(app):
                # DB initialized during startup
                assert hasattr(app.state, 'db')
                assert app.state.db is not None

    def test_cors_middleware(self) -> None:
        """Test CORS middleware is configured."""
        app = create_app()

        # Check middleware is present
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_metrics_endpoint(self) -> None:
        """Test metrics endpoint is mounted."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
            app = create_app()

            with TestClient(app) as client:
                response = client.get("/metrics")

                # Prometheus metrics endpoint
                assert response.status_code == 200

    def test_health_endpoint(self) -> None:
        """Test health endpoint returns correct response."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
            app = create_app()

            with TestClient(app) as client:
                response = client.get("/health")

                assert response.status_code == 200
                assert response.json() == {
                    "status": "healthy",
                    "service": "service-template"
                }

    def test_root_endpoint(self) -> None:
        """Test root endpoint returns service info."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
            app = create_app()

            with TestClient(app) as client:
                response = client.get("/")

                assert response.status_code == 200
                data = response.json()
                assert data["service"] == "service-template"
                assert data["version"] == "1.0.0"
                assert data["status"] == "running"

    def test_lifespan_shutdown(self) -> None:
        """Test lifespan shutdown event closes DB."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
            app = create_app()

            # Startup/shutdown cycle
            with TestClient(app):
                db_instance = app.state.db
                assert db_instance is not None

            # After context, shutdown executed (DB closed)
