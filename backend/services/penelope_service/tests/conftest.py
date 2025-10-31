"""PENELOPE Service Test Fixtures.

Common test fixtures for PENELOPE service testing.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_sophia_engine():
    """Mock Sophia Engine for testing."""
    mock = MagicMock()
    mock.analyze_anomaly = AsyncMock(
        return_value={
            "diagnosis": "High CPU usage detected",
            "severity": "medium",
            "recommended_action": "Scale horizontally",
        }
    )
    return mock


@pytest.fixture
def mock_praotes_validator():
    """Mock Praotes Validator for testing."""
    mock = MagicMock()
    mock.validate_patch = AsyncMock(
        return_value={
            "approved": True,
            "risk_level": "low",
            "validation_checks": ["syntax_ok", "no_destructive_operations"],
        }
    )
    return mock


@pytest.fixture
def mock_tapeinophrosyne_monitor():
    """Mock Tapeinophrosyne Monitor for testing."""
    mock = MagicMock()
    mock.get_confidence_score = MagicMock(return_value=0.85)
    return mock


@pytest.fixture
def mock_wisdom_base():
    """Mock Wisdom Base for testing."""
    mock = MagicMock()
    mock.query_precedent = AsyncMock(
        return_value={
            "similar_cases": 5,
            "success_rate": 0.92,
            "recommended_solution": "Apply rate limiting",
        }
    )
    return mock


@pytest.fixture
def mock_observability_client():
    """Mock Observability Client for testing."""
    mock = MagicMock()
    mock.get_metrics = AsyncMock(
        return_value={"cpu_usage": 85.5, "memory_usage": 72.3, "request_rate": 1250}
    )
    return mock


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from main import app

    return TestClient(app)


@pytest.fixture
def client(test_client):
    """Alias for test_client for compatibility."""
    return test_client
