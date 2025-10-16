"""
Shared test fixtures and configuration.
"""
import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio backend for async tests."""
    return "asyncio"
