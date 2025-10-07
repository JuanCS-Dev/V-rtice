"""Pytest configuration and fixtures"""

import asyncio
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from active_immune_core.main import app


# ==================== ASYNC HELPERS ====================


async def assert_eventually(
    condition: Callable[[], bool],
    timeout: float = 2.0,
    interval: float = 0.05,
    error_msg: str = "Condition not met within timeout"
) -> None:
    """
    Assert that a condition becomes true within a timeout.

    Retries the condition check at regular intervals until either:
    - The condition returns True (success)
    - The timeout expires (raises AssertionError)

    This helper is essential for testing async code where race conditions
    can occur between background tasks and test assertions.

    Args:
        condition: Callable that returns bool (no args)
        timeout: Maximum time to wait in seconds (default: 2.0)
        interval: Time between checks in seconds (default: 0.05)
        error_msg: Error message if timeout expires

    Raises:
        AssertionError: If condition doesn't become True within timeout

    Example:
        await assert_eventually(
            lambda: len(cell.captured_antigens) == 5,
            timeout=2.0,
            error_msg="Expected 5 captured antigens"
        )
    """
    start_time = asyncio.get_event_loop().time()
    end_time = start_time + timeout

    last_exception = None

    while asyncio.get_event_loop().time() < end_time:
        try:
            if condition():
                return  # Success!
        except Exception as e:
            last_exception = e

        # Wait before next check
        await asyncio.sleep(interval)

    # Timeout expired - condition never became True
    if last_exception:
        raise AssertionError(
            f"{error_msg} (last exception: {last_exception})"
        )
    else:
        raise AssertionError(error_msg)


@pytest.fixture
def client():
    """FastAPI test client - compatible with Starlette 0.27+"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_agent_state():
    """Sample agent state for testing"""
    from active_immune_core.agents.models import AgenteState, AgentType

    return AgenteState(
        tipo=AgentType.MACROFAGO,
        area_patrulha="test_subnet",
        localizacao_atual="test_subnet",
    )


@pytest.fixture
def sample_cytokine_message():
    """Sample cytokine message for testing"""
    from active_immune_core.communication import CytokineMessage

    return CytokineMessage(
        tipo="IL1",
        emissor_id="test_agent_123",
        prioridade=8,
        payload={
            "evento": "ameaca_detectada",
            "alvo": {"ip": "192.0.2.100", "porta": 445},
        },
        area_alvo="test_subnet",
    )


@pytest.fixture
def sample_hormone_message():
    """Sample hormone message for testing"""
    from active_immune_core.communication import HormoneMessage

    return HormoneMessage(
        tipo="cortisol",
        emissor="test_lymphnode",
        nivel=7.5,
        payload={
            "evento": "sistema_sob_estresse",
            "temperatura_global": 39.0,
        },
    )


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
