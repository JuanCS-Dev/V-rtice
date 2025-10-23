"""
MIP Client - Targeted Coverage Tests

Objetivo: Cobrir mip_client/client.py (118 lines, 0% → 60%+)

Testa:
- MIPClientError e MIPTimeoutError exceptions
- MIPClient initialization
- Circuit breaker pattern (open/close)
- Retry logic com exponential backoff
- HTTP methods (health_check, evaluate, get_principle, list_principles)
- MIPClientContext manager

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

import httpx

from mip_client.client import (
    MIPClientError,
    MIPTimeoutError,
    MIPClient,
    MIPClientContext
)


# ===== EXCEPTION TESTS =====

def test_mip_client_error():
    """
    SCENARIO: Raise MIPClientError
    EXPECTED: Exception raised
    """
    with pytest.raises(MIPClientError):
        raise MIPClientError("Client error")


def test_mip_timeout_error():
    """
    SCENARIO: Raise MIPTimeoutError
    EXPECTED: Inherits from MIPClientError
    """
    with pytest.raises(MIPTimeoutError):
        raise MIPTimeoutError("Timeout")

    with pytest.raises(MIPClientError):
        raise MIPTimeoutError("Also MIPClientError")


# ===== MIP CLIENT INITIALIZATION =====

def test_mip_client_initialization_defaults():
    """
    SCENARIO: Create MIPClient with defaults
    EXPECTED: localhost:8100, timeout 30s, max_retries 3
    """
    client = MIPClient()

    assert client.base_url == "http://localhost:8100"
    assert client.timeout == 30.0
    assert client.max_retries == 3
    assert client.circuit_failures == 0
    assert client.circuit_open_until is None


def test_mip_client_initialization_custom_params():
    """
    SCENARIO: Create MIPClient with custom parameters
    EXPECTED: Uses provided values
    """
    client = MIPClient(
        base_url="http://mip:8100",
        timeout=10.0,
        max_retries=5,
        circuit_breaker_threshold=10,
        circuit_breaker_timeout=120
    )

    assert client.base_url == "http://mip:8100"
    assert client.timeout == 10.0
    assert client.max_retries == 5
    assert client.circuit_breaker_threshold == 10
    assert client.circuit_breaker_timeout == 120


def test_mip_client_strips_trailing_slash():
    """
    SCENARIO: Create MIPClient with URL ending in /
    EXPECTED: Strips trailing slash
    """
    client = MIPClient(base_url="http://mip:8100/")

    assert client.base_url == "http://mip:8100"


@pytest.mark.asyncio
async def test_mip_client_close():
    """
    SCENARIO: Close MIPClient
    EXPECTED: Closes httpx client
    """
    client = MIPClient()

    with patch.object(client.client, 'aclose', new_callable=AsyncMock) as mock_close:
        await client.close()
        mock_close.assert_called_once()


# ===== CIRCUIT BREAKER TESTS =====

def test_is_circuit_open_initially_false():
    """
    SCENARIO: Check circuit breaker status initially
    EXPECTED: Returns False (circuit closed)
    """
    client = MIPClient()

    assert client._is_circuit_open() is False


def test_is_circuit_open_when_failures_exceed_threshold():
    """
    SCENARIO: Circuit open after threshold failures
    EXPECTED: Returns True
    """
    client = MIPClient(circuit_breaker_threshold=3)

    client.circuit_open_until = datetime.now() + timedelta(seconds=60)

    assert client._is_circuit_open() is True


def test_is_circuit_open_resets_after_timeout():
    """
    SCENARIO: Circuit timeout expired
    EXPECTED: Resets circuit, returns False
    """
    client = MIPClient()

    # Set circuit open in the past
    client.circuit_open_until = datetime.now() - timedelta(seconds=10)
    client.circuit_failures = 5

    is_open = client._is_circuit_open()

    assert is_open is False
    assert client.circuit_failures == 0
    assert client.circuit_open_until is None


def test_record_failure_increments_counter():
    """
    SCENARIO: Record failure
    EXPECTED: Increments circuit_failures
    """
    client = MIPClient()

    client._record_failure()

    assert client.circuit_failures == 1


def test_record_failure_opens_circuit_at_threshold():
    """
    SCENARIO: Record failures until threshold
    EXPECTED: Opens circuit
    """
    client = MIPClient(circuit_breaker_threshold=3)

    client._record_failure()
    client._record_failure()
    client._record_failure()

    assert client.circuit_open_until is not None


def test_record_success_resets_circuit():
    """
    SCENARIO: Record success after failures
    EXPECTED: Resets circuit_failures to 0
    """
    client = MIPClient()

    client.circuit_failures = 5
    client._record_success()

    assert client.circuit_failures == 0
    assert client.circuit_open_until is None


# ===== HEALTH CHECK TESTS =====

@pytest.mark.asyncio
async def test_health_check_success():
    """
    SCENARIO: Health check succeeds
    EXPECTED: Returns health status dict
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = {"status": "healthy"}

    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
        result = await client.health_check()

        assert result == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_check_failure():
    """
    SCENARIO: Health check fails (network error)
    EXPECTED: Raises MIPClientError
    """
    client = MIPClient()

    with patch.object(client.client, 'get', side_effect=Exception("Connection error")):
        with pytest.raises(MIPClientError, match="Health check failed"):
            await client.health_check()


# ===== EVALUATE TESTS =====

@pytest.mark.asyncio
async def test_evaluate_success():
    """
    SCENARIO: Evaluate action plan successfully
    EXPECTED: Returns verdict dict, records success
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = {
        "verdict": {"status": "approved", "aggregate_score": 0.85}
    }

    with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
        result = await client.evaluate({"action": "test"})

        assert result["verdict"]["status"] == "approved"
        assert client.circuit_failures == 0


@pytest.mark.asyncio
async def test_evaluate_circuit_breaker_open():
    """
    SCENARIO: Evaluate when circuit breaker is open
    EXPECTED: Raises MIPClientError without attempting request
    """
    client = MIPClient()

    client.circuit_open_until = datetime.now() + timedelta(seconds=60)

    with pytest.raises(MIPClientError, match="Circuit breaker is open"):
        await client.evaluate({"action": "test"})


@pytest.mark.asyncio
async def test_evaluate_timeout():
    """
    SCENARIO: Evaluate times out
    EXPECTED: Raises MIPTimeoutError after retries
    """
    client = MIPClient(max_retries=2)

    with patch.object(client.client, 'post', side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(MIPTimeoutError):
            await client.evaluate({"action": "test"})


@pytest.mark.asyncio
async def test_evaluate_http_error_4xx():
    """
    SCENARIO: Evaluate returns 4xx (client error)
    EXPECTED: Does not retry, raises MIPClientError
    """
    client = MIPClient(max_retries=3)

    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"

    error = httpx.HTTPStatusError("400", request=Mock(), response=mock_response)

    with patch.object(client.client, 'post', side_effect=error):
        with pytest.raises(MIPClientError, match="400"):
            await client.evaluate({"action": "test"})


@pytest.mark.asyncio
async def test_evaluate_retry_with_backoff():
    """
    SCENARIO: Evaluate fails twice, succeeds third time
    EXPECTED: Retries with exponential backoff
    """
    client = MIPClient(max_retries=3)

    mock_response = Mock()
    mock_response.json.return_value = {"verdict": {"status": "approved"}}

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.RequestError("Network error", request=Mock())
        return mock_response

    with patch.object(client.client, 'post', side_effect=side_effect):
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await client.evaluate({"action": "test"})

            assert result["verdict"]["status"] == "approved"
            assert call_count == 3


@pytest.mark.asyncio
async def test_evaluate_no_retry():
    """
    SCENARIO: Evaluate with retry=False
    EXPECTED: Does not retry on failure
    """
    client = MIPClient(max_retries=5)

    with patch.object(client.client, 'post', side_effect=Exception("Error")):
        with pytest.raises(MIPClientError):
            await client.evaluate({"action": "test"}, retry=False)


# ===== GET PRINCIPLE TESTS =====

@pytest.mark.asyncio
async def test_get_principle_success():
    """
    SCENARIO: Get principle by ID
    EXPECTED: Returns principle dict
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = {"id": "p1", "name": "Principle 1"}

    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
        result = await client.get_principle("p1")

        assert result["id"] == "p1"


@pytest.mark.asyncio
async def test_get_principle_failure():
    """
    SCENARIO: Get principle fails
    EXPECTED: Raises MIPClientError
    """
    client = MIPClient()

    with patch.object(client.client, 'get', side_effect=Exception("Not found")):
        with pytest.raises(MIPClientError, match="Failed to get principle"):
            await client.get_principle("p1")


# ===== LIST PRINCIPLES TESTS =====

@pytest.mark.asyncio
async def test_list_principles_no_filter():
    """
    SCENARIO: List all principles
    EXPECTED: Returns list of principles
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = [{"id": "p1"}, {"id": "p2"}]

    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
        result = await client.list_principles()

        assert len(result) == 2


@pytest.mark.asyncio
async def test_list_principles_with_level_filter():
    """
    SCENARIO: List principles filtered by level
    EXPECTED: Returns filtered principles
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = [{"id": "p1", "level": "strategic"}]

    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response) as mock_get:
        result = await client.list_principles(level="strategic")

        assert len(result) == 1
        mock_get.assert_called_once()


# ===== GET DECISION TESTS =====

@pytest.mark.asyncio
async def test_get_decision_success():
    """
    SCENARIO: Get decision by ID
    EXPECTED: Returns decision dict
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = {"decision_id": "d1", "status": "approved"}

    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
        result = await client.get_decision("d1")

        assert result["decision_id"] == "d1"


# ===== GET AUDIT TRAIL TESTS =====

@pytest.mark.asyncio
async def test_get_audit_trail_default_params():
    """
    SCENARIO: Get audit trail with defaults
    EXPECTED: Returns list of decisions
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = [{"decision_id": "d1"}, {"decision_id": "d2"}]

    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
        result = await client.get_audit_trail()

        assert len(result) == 2


@pytest.mark.asyncio
async def test_get_audit_trail_custom_pagination():
    """
    SCENARIO: Get audit trail with custom limit/offset
    EXPECTED: Uses provided pagination params
    """
    client = MIPClient()

    mock_response = Mock()
    mock_response.json.return_value = []

    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response) as mock_get:
        await client.get_audit_trail(limit=50, offset=10)

        mock_get.assert_called_once()


# ===== CONTEXT MANAGER TESTS =====

@pytest.mark.asyncio
async def test_mip_client_context_manager():
    """
    SCENARIO: Use MIPClientContext as async context manager
    EXPECTED: Opens and closes client properly
    """
    with patch.object(MIPClient, 'close', new_callable=AsyncMock) as mock_close:
        async with MIPClientContext(base_url="http://test:8100") as client:
            assert isinstance(client, MIPClient)

        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_mip_client_context_manager_with_exception():
    """
    SCENARIO: Exception inside context manager
    EXPECTED: Still closes client
    """
    with patch.object(MIPClient, 'close', new_callable=AsyncMock) as mock_close:
        try:
            async with MIPClientContext() as client:
                raise ValueError("Test error")
        except ValueError:
            pass

        mock_close.assert_called_once()
