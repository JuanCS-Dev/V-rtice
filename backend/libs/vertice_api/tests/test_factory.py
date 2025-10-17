"""Tests for vertice_api.factory module."""

from fastapi.testclient import TestClient
from vertice_api.factory import create_app
from vertice_core import BaseServiceSettings


class TestCreateApp:
    """Tests for create_app factory."""

    def test_creates_fastapi_app(self) -> None:
        """Test that factory creates FastAPI app."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            otel_enabled=False,
        )
        app = create_app(settings)

        assert app is not None
        assert app.title == "test"

    def test_includes_health_endpoints(self) -> None:
        """Test that health endpoints are included."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            otel_enabled=False,
        )
        app = create_app(settings)
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200

        response = client.get("/health/live")
        assert response.status_code == 200

    def test_custom_title_and_description(self) -> None:
        """Test custom title and description."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            otel_enabled=False,
        )
        app = create_app(
            settings,
            title="Custom Title",
            description="Custom Description",
        )

        assert app.title == "Custom Title"
        assert app.description == "Custom Description"

    def test_docs_disabled_in_production(self) -> None:
        """Test that docs are disabled in production."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            environment="production",
            otel_enabled=False,
        )
        app = create_app(settings)

        assert app.docs_url is None
        assert app.redoc_url is None
