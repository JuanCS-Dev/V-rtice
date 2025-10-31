"""Pytest configuration and fixtures for MABA tests.

Author: Vértice Platform Team
License: Proprietary
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from services.maba_service.api.routes import set_maba_service
from services.maba_service.main import app


@pytest.fixture
def mock_maba_service():
    """Create a mock MABA service for testing."""
    service = MagicMock()

    # Mock browser controller
    service.browser_controller = MagicMock()
    service.browser_controller.create_session = AsyncMock(
        return_value={"session_id": "test-session-123", "status": "created"}
    )
    service.browser_controller.navigate = AsyncMock(
        return_value={"status": "success", "url": "https://example.com"}
    )
    service.browser_controller.close_session = AsyncMock(
        return_value={"status": "closed"}
    )
    service.browser_controller.click = AsyncMock(
        return_value={"status": "success", "clicked": True}
    )
    service.browser_controller.type_text = AsyncMock(
        return_value={"status": "success", "typed": True}
    )
    service.browser_controller.screenshot = AsyncMock(
        return_value={"status": "success", "data": "base64_screenshot_data"}
    )
    service.browser_controller.extract_data = AsyncMock(
        return_value={
            "status": "success",
            "data": {"title": "Example Page", "price": "$99.99"},
        }
    )

    # Mock cognitive map
    service.cognitive_map = MagicMock()
    service.cognitive_map.find_element = AsyncMock(return_value="#login-button")

    # Mock health check
    service.is_healthy = MagicMock(return_value=True)
    service.health_check = AsyncMock(
        return_value={
            "status": "healthy",
            "components": {"browser": "ok", "cognitive_map": "ok", "database": "ok"},
        }
    )

    return service


@pytest.fixture
def client(mock_maba_service):
    """Create a test client with mocked MABA service."""
    set_maba_service(mock_maba_service)
    return TestClient(app)


@pytest.fixture
def sample_navigation_request():
    """Sample navigation request data."""
    return {
        "url": "https://example.com",
        "wait_until": "networkidle",
        "timeout_ms": 30000,
    }


@pytest.fixture
def sample_cognitive_map_query():
    """Sample cognitive map query data."""
    return {
        "query_type": "find_element",
        "parameters": {
            "url": "https://example.com/login",
            "description": "login button",
            "min_importance": 0.3,
        },
    }
