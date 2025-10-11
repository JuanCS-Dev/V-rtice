"""
Pytest configuration for Eureka tests.

Ensures proper PYTHONPATH setup for imports within test modules.
"""

import sys
from pathlib import Path

# Add Eureka service root to PYTHONPATH for absolute imports
eureka_root = Path(__file__).parent.parent
if str(eureka_root) not in sys.path:
    sys.path.insert(0, str(eureka_root))

import pytest


# Common fixtures can be added here
@pytest.fixture
def sample_cve_id() -> str:
    """Sample CVE ID for testing."""
    return "CVE-2024-1234"


@pytest.fixture
def sample_package_name() -> str:
    """Sample package name for testing."""
    return "requests"
