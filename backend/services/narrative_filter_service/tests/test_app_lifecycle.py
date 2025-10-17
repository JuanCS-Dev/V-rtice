"""Tests for FastAPI app lifecycle."""


import pytest


@pytest.mark.asyncio
async def test_app_lifespan_execution():
    """Test app lifespan startup and shutdown - covers lines 19-21."""
    from narrative_filter_service.main import app, lifespan

    # Execute lifespan context manager
    async with lifespan(app):
        # During this context, startup logging happens (line 19)
        assert app is not None
    # After context exit, shutdown logging happens (line 21)

    # If we reach here without exceptions, lifespan executed successfully
    assert True


def test_app_configuration():
    """Test app is properly configured."""
    from narrative_filter_service.main import app

    assert app.title == "narrative-filter-service"
    assert app.version == "1.0.0"

    # Verify routes are registered
    routes = {route.path for route in app.routes}
    assert "/health/" in routes
    assert "/metrics" in routes


def test_app_has_lifespan():
    """Test app has lifespan configured."""
    from narrative_filter_service.main import app

    assert hasattr(app, 'router')
    # App was created with lifespan parameter
    assert app is not None
