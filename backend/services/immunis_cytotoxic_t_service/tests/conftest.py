"""Pytest configuration and fixtures for immunis_cytotoxic_t_service tests."""

import pytest
from httpx import ASGITransport, AsyncClient

# Import app at module level
import sys
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_cytotoxic_t_service")
from api import app


@pytest.fixture
async def client():
    """Async HTTP client for testing FastAPI endpoints.

    Uses httpx.AsyncClient with ASGITransport for FastAPI 0.104+ compatibility.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
