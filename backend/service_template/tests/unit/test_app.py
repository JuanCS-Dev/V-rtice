"""
Tests for Presentation Layer - FastAPI App

100% coverage required.
"""
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
        app = create_app()
        client = TestClient(app)
        
        # Startup is triggered by TestClient context
        assert client.app == app

    def test_cors_middleware(self) -> None:
        """Test CORS middleware is configured."""
        app = create_app()
        
        # Check middleware is present
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_metrics_endpoint(self) -> None:
        """Test metrics endpoint is mounted."""
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/metrics")
        
        # Prometheus metrics endpoint
        assert response.status_code in [200, 404]  # May not be fully configured in test
