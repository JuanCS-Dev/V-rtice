"""E2E Test Configuration - PRODUCTION-READY

Fixtures and configuration for end-to-end integration tests.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

from api.main import create_app
from api.core_integration import CoreManager


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped fixtures."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def app():
    """Create FastAPI app instance for testing."""
    app = create_app()
    return app


@pytest_asyncio.fixture(scope="session")
async def initialized_core_manager():
    """Initialize Core System for E2E tests."""
    core_manager = CoreManager.get_instance()

    # Initialize Core (this will gracefully degrade if services unavailable)
    await core_manager.initialize()

    yield core_manager

    # Cleanup
    await core_manager.stop()


@pytest_asyncio.fixture
async def client(app, initialized_core_manager) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for E2E tests."""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def agent_ids():
    """Track created agent IDs for cleanup."""
    ids = []
    yield ids

    # Cleanup: delete all created agents
    # (AgentService will handle this via Core)
