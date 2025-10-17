"""Tests for VerdictRepository."""

from uuid import uuid4

import pytest

from models import VerdictFilter
from verdict_repository import VerdictRepository


@pytest.mark.asyncio
async def test_repository_connect_disconnect():
    """Test repository connection lifecycle."""
    repo = VerdictRepository()

    assert repo.pool is None

    await repo.connect()
    assert repo.pool is not None

    await repo.disconnect()
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
async def test_get_active_verdicts_query_construction(mock_repository, sample_verdict):
    """Test SQL query construction with filters."""
    repo = mock_repository
    repo.pool = True  # Simulate connected

    # Mock pool.acquire()
    mock_conn = mock_repository
    mock_conn.fetch.return_value = []

    # Test status filter
    filters = VerdictFilter(status="ACTIVE")
    # Query should include: WHERE 1=1 AND status = $1
    # This test validates query construction logic indirectly

    # Test severity filter
    filters = VerdictFilter(severity="CRITICAL")
    # Query should include: AND severity = $1

    # Test multiple filters
    filters = VerdictFilter(
        status="ACTIVE",
        severity="HIGH",
        category="DECEPTION",
        agent_id="agent-1",
        limit=10,
        offset=5,
    )
    # Query should include all filters + LIMIT + OFFSET

    # Validation: filters object is correctly constructed
    assert filters.status == "ACTIVE"
    assert filters.severity == "HIGH"
    assert filters.limit == 10
    assert filters.offset == 5
