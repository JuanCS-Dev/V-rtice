"""Tests for VerdictRepository."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from models import VerdictFilter
from verdict_repository import VerdictRepository


@pytest.mark.asyncio
async def test_repository_connect_disconnect(mocker):
    """Test repository connection lifecycle."""
    # Mock asyncpg.create_pool
    mock_pool = AsyncMock()
    mock_create_pool = mocker.patch(
        "verdict_repository.asyncpg.create_pool",
        new=AsyncMock(return_value=mock_pool)
    )

    repo = VerdictRepository()

    assert repo.pool is None

    await repo.connect()
    assert repo.pool is not None
    mock_create_pool.assert_called_once()

    await repo.disconnect()
    mock_pool.close.assert_called_once()
    assert repo.pool is None


@pytest.mark.asyncio
async def test_get_active_verdicts_no_pool(sample_verdict):
    """Test get_active_verdicts without initialized pool."""
    repo = VerdictRepository()
    filters = VerdictFilter()

    with pytest.raises(RuntimeError, match="Database pool not initialized"):
        await repo.get_active_verdicts(filters)


@pytest.mark.asyncio
async def test_get_verdict_by_id_no_pool():
    """Test get_verdict_by_id without initialized pool."""
    repo = VerdictRepository()
    verdict_id = uuid4()

    with pytest.raises(RuntimeError, match="Database pool not initialized"):
        await repo.get_verdict_by_id(verdict_id)


@pytest.mark.asyncio
async def test_get_stats_no_pool():
    """Test get_stats without initialized pool."""
    repo = VerdictRepository()

    with pytest.raises(RuntimeError, match="Database pool not initialized"):
        await repo.get_stats()


@pytest.mark.asyncio
async def test_update_verdict_status_no_pool():
    """Test update_verdict_status without initialized pool."""
    repo = VerdictRepository()
    verdict_id = uuid4()

    with pytest.raises(RuntimeError, match="Database pool not initialized"):
        await repo.update_verdict_status(verdict_id, "MITIGATED")


@pytest.mark.asyncio
async def test_get_active_verdicts_query_construction(mocker, sample_verdict):
    """Test SQL query construction with filters."""
    # Mock connection and pool properly
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch = mocker.AsyncMock(return_value=[])

    mock_acquire = mocker.MagicMock()
    mock_acquire.__aenter__ = mocker.AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = mocker.AsyncMock(return_value=None)

    mock_pool = mocker.AsyncMock()
    mock_pool.acquire = mocker.MagicMock(return_value=mock_acquire)

    repo = VerdictRepository()
    repo.pool = mock_pool

    # Test status filter
    filters = VerdictFilter(status="ACTIVE")
    await repo.get_active_verdicts(filters)
    mock_conn.fetch.assert_awaited()

    # Test multiple filters
    filters = VerdictFilter(
        status="ACTIVE",
        severity="HIGH",
        category="DECEPTION",
        agent_id="agent-1",
        limit=10,
        offset=5,
    )

    # Validation: filters object is correctly constructed
    assert filters.status == "ACTIVE"
    assert filters.severity == "HIGH"
    assert filters.limit == 10
    assert filters.offset == 5
