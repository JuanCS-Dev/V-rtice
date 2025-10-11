"""pytest configuration for BAS service tests."""

import os
import sys
from pathlib import Path

import pytest

# Add service root to path
service_root = Path(__file__).parent.parent
sys.path.insert(0, str(service_root))

# Set test environment
os.environ["MAXIMUS_ENV"] = "test"
os.environ["BAS_SAFE_MODE"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Setup test environment."""
    # Ensure we're in test mode
    assert os.getenv("MAXIMUS_ENV") == "test"
    assert os.getenv("BAS_SAFE_MODE") == "true"
    
    yield
    
    # Cleanup after all tests
    pass


@pytest.fixture
def mock_target_service():
    """Mock target service for safe testing."""
    return {
        "name": "test_service",
        "host": "localhost",
        "port": 9999,
        "safe": True
    }
