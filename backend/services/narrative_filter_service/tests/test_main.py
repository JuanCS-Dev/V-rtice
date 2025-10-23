"""Tests for main FastAPI app."""


def test_app_metadata() -> None:
    """Test app metadata."""
    from main import app

    assert app.title == "narrative-filter-service"
    assert app.version == "1.0.0"
    assert app.description == "Filtro de Narrativas Multi-Agente - 3 Camadas"


def test_lifespan_configured() -> None:
    """Test app lifespan is properly configured."""
    from main import app

    # The lifespan function is tested during app initialization
    assert hasattr(app, 'router')
    assert app.router.lifespan_context is not None


def test_health_router_included() -> None:
    """Test health router is included in app routes."""
    from main import app

    routes = [route.path for route in app.routes]
    assert any("/health" in route for route in routes)


def test_metrics_endpoint_mounted() -> None:
    """Test Prometheus metrics endpoint is mounted."""
    from main import app

    routes = [route.path for route in app.routes]
    assert any("/metrics" in route for route in routes)


def test_app_configuration() -> None:
    """Test app is configured correctly."""
    from main import app
    from config import settings

    assert app.title == settings.service_name
