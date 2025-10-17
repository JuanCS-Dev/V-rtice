"""Tests for verdict repository."""

from datetime import datetime
from uuid import uuid4

import pytest

from models import Severity, Verdict, VerdictCategory, VerdictStatus
from verdict_repository import VerdictRepository


@pytest.fixture
def mock_pool():
    """Mock asyncpg pool."""

    class MockConnection:
        async def fetchrow(self, query: str, *args):
            return {"id": uuid4()}

        async def fetch(self, query: str, *args):
            return []

        async def execute(self, query: str, *args):
            return "UPDATE 1"

        async def executemany(self, query: str, args):
            pass

    class MockPool:
        def acquire(self):
            class AsyncContext:
                async def __aenter__(self):
                    return MockConnection()

                async def __aexit__(self, *args):
                    pass

            return AsyncContext()

    return MockPool()


@pytest.fixture
def verdict_repo(mock_pool):
    """Create verdict repository."""
    return VerdictRepository(mock_pool)


@pytest.fixture
def sample_verdict() -> Verdict:
    """Create sample verdict."""
    return Verdict(
        timestamp=datetime.utcnow(),
        category=VerdictCategory.DECEPTION,
        severity=Severity.CRITICAL,
        title="Test verdict",
        agents_involved=["agent_x"],
        evidence_chain=["msg_1", "msg_2"],
        confidence=0.95,
        recommended_action="ISOLATE",
    )


@pytest.mark.asyncio
async def test_verdict_repo_create(verdict_repo: VerdictRepository, sample_verdict: Verdict) -> None:
    """Test creating a verdict."""
    result = await verdict_repo.create(sample_verdict)
    assert result is not None


@pytest.mark.asyncio
async def test_verdict_repo_get_active_no_filters(verdict_repo: VerdictRepository) -> None:
    """Test get_active_verdicts without filters."""
    verdicts = await verdict_repo.get_active_verdicts(limit=100)
    assert isinstance(verdicts, list)


@pytest.mark.asyncio
async def test_verdict_repo_get_active_with_severity(verdict_repo: VerdictRepository) -> None:
    """Test get_active_verdicts with severity filter."""
    verdicts = await verdict_repo.get_active_verdicts(severity=Severity.CRITICAL, limit=50)
    assert isinstance(verdicts, list)


@pytest.mark.asyncio
async def test_verdict_repo_get_active_with_category(verdict_repo: VerdictRepository) -> None:
    """Test get_active_verdicts with category filter."""
    verdicts = await verdict_repo.get_active_verdicts(category=VerdictCategory.DECEPTION, limit=50)
    assert isinstance(verdicts, list)


@pytest.mark.asyncio
async def test_verdict_repo_get_active_with_both_filters(verdict_repo: VerdictRepository) -> None:
    """Test get_active_verdicts with both filters."""
    verdicts = await verdict_repo.get_active_verdicts(
        severity=Severity.HIGH, category=VerdictCategory.ALLIANCE, limit=25
    )
    assert isinstance(verdicts, list)


@pytest.mark.asyncio
async def test_verdict_repo_update_status(verdict_repo: VerdictRepository) -> None:
    """Test updating verdict status."""
    verdict_id = uuid4()
    result = await verdict_repo.update_status(verdict_id, VerdictStatus.MITIGATED)
    assert result is True


@pytest.mark.asyncio
async def test_verdict_repo_update_status_with_command(verdict_repo: VerdictRepository) -> None:
    """Test updating verdict status with command ID."""
    verdict_id = uuid4()
    command_id = uuid4()
    result = await verdict_repo.update_status(verdict_id, VerdictStatus.MITIGATED, command_id)
    assert result is True


@pytest.mark.asyncio
async def test_verdict_repo_batch_create(verdict_repo: VerdictRepository) -> None:
    """Test batch creating verdicts."""
    verdicts = [
        Verdict(
            timestamp=datetime.utcnow(),
            category=VerdictCategory.ALLIANCE,
            severity=Severity.MEDIUM,
            title=f"Test {i}",
            agents_involved=[f"agent_{i}"],
            evidence_chain=[f"msg_{i}"],
            confidence=0.8,
            recommended_action="MONITOR",
        )
        for i in range(3)
    ]

    count = await verdict_repo.batch_create(verdicts)
    assert count == 3


def test_verdict_repo_initialization(mock_pool) -> None:
    """Test verdict repository initialization."""
    repo = VerdictRepository(mock_pool)
    assert repo.pool is not None
