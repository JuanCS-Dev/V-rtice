"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_connector():
    """Mock connector for testing."""
    connector = Mock()
    connector.health_check = AsyncMock(return_value=True)
    connector.close = AsyncMock()
    return connector

@pytest.fixture
def sample_ip_result():
    """Sample IP analysis result."""
    return {
        "ip": "8.8.8.8",
        "status": "success",
        "reputation": "clean",
        "location": "US"
    }
