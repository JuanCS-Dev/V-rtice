"""Pytest fixtures for vertice_api tests."""

import pytest
from vertice_core import BaseServiceSettings


@pytest.fixture()
def test_settings() -> BaseServiceSettings:
    """Create test settings."""
    return BaseServiceSettings(
        service_name="test_service",
        service_version="1.0.0",
        port=8000,
        environment="development",
        log_level="INFO",
        otel_enabled=False,
    )
