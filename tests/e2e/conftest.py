"""Pytest configuration for E2E tests."""

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def check_services_running():
    """Verify all required services are running before tests."""
    import httpx

    services = [
        ("http://localhost:8091/health", "Narrative Filter"),
        ("http://localhost:8092/health", "Command Bus"),
        ("http://localhost:8093/health", "Verdict Engine"),
    ]

    for url, name in services:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code != 200:
                pytest.skip(f"{name} not healthy (status {response.status_code})")
        except Exception as e:
            pytest.skip(f"{name} not running: {e}")

    print("✅ All services running")


@pytest.fixture
def test_agent_id():
    """Generate unique agent ID for tests."""
    from uuid import uuid4

    return str(uuid4())


@pytest.fixture
def test_command_id():
    """Generate unique command ID for tests."""
    from uuid import uuid4

    return str(uuid4())
