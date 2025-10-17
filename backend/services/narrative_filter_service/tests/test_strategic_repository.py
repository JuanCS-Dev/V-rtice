"""Tests for strategic repositories."""

from uuid import uuid4

import pytest

from narrative_filter_service.models import Alliance, PatternType, StrategicPattern
from narrative_filter_service.strategic_repository import AllianceRepository, StrategicPatternRepository


@pytest.fixture
def mock_pool():
    """Mock asyncpg pool."""

    class MockConnection:
        async def fetchrow(self, query: str, *args):
            return {"id": uuid4()}

        async def fetch(self, query: str, *args):
            return []

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
def pattern_repo(mock_pool):
    """Create pattern repository."""
    return StrategicPatternRepository(mock_pool)


@pytest.fixture
def alliance_repo(mock_pool):
    """Create alliance repository."""
    return AllianceRepository(mock_pool)


@pytest.fixture
def sample_pattern() -> StrategicPattern:
    """Create sample strategic pattern."""
    return StrategicPattern(
        pattern_type=PatternType.ALLIANCE,
        agents_involved=["agent_a", "agent_b"],
        evidence_messages=["msg_1", "msg_2"],
        mutual_information=0.85,
    )


@pytest.fixture
def sample_alliance() -> Alliance:
    """Create sample alliance."""
    return Alliance(
        agent_a="agent_a",
        agent_b="agent_b",
        strength=0.9,
        interaction_count=10,
    )


@pytest.mark.asyncio
async def test_pattern_repo_create(pattern_repo: StrategicPatternRepository, sample_pattern: StrategicPattern) -> None:
    """Test creating a strategic pattern."""
    result = await pattern_repo.create(sample_pattern)
    assert result is not None


@pytest.mark.asyncio
async def test_pattern_repo_get_recent_no_filter(pattern_repo: StrategicPatternRepository) -> None:
    """Test get_recent_patterns without filter."""
    patterns = await pattern_repo.get_recent_patterns(hours=24, limit=100)
    assert isinstance(patterns, list)


@pytest.mark.asyncio
async def test_pattern_repo_get_recent_with_filter(pattern_repo: StrategicPatternRepository) -> None:
    """Test get_recent_patterns with pattern_type filter."""
    patterns = await pattern_repo.get_recent_patterns(
        pattern_type=PatternType.ALLIANCE,
        hours=24,
        limit=50
    )
    assert isinstance(patterns, list)


@pytest.mark.asyncio
async def test_pattern_repo_batch_create(pattern_repo: StrategicPatternRepository) -> None:
    """Test batch create patterns."""
    patterns = [
        StrategicPattern(
            pattern_type=PatternType.DECEPTION,
            agents_involved=[f"agent_{i}"],
            evidence_messages=[f"msg_{i}"],
            deception_score=0.7,
        )
        for i in range(5)
    ]

    count = await pattern_repo.batch_create(patterns)
    assert count == 5


@pytest.mark.asyncio
async def test_alliance_repo_upsert(alliance_repo: AllianceRepository, sample_alliance: Alliance) -> None:
    """Test upserting an alliance."""
    result = await alliance_repo.upsert(sample_alliance)
    assert result is not None


@pytest.mark.asyncio
async def test_alliance_repo_get_active_no_filter(alliance_repo: AllianceRepository) -> None:
    """Test get_active_alliances without agent filter."""
    alliances = await alliance_repo.get_active_alliances()
    assert isinstance(alliances, list)


@pytest.mark.asyncio
async def test_alliance_repo_get_active_with_filter(alliance_repo: AllianceRepository) -> None:
    """Test get_active_alliances with agent filter."""
    alliances = await alliance_repo.get_active_alliances(agent_id="agent_a")
    assert isinstance(alliances, list)


def test_pattern_repo_initialization(mock_pool) -> None:
    """Test pattern repository initialization."""
    repo = StrategicPatternRepository(mock_pool)
    assert repo.pool is not None


def test_alliance_repo_initialization(mock_pool) -> None:
    """Test alliance repository initialization."""
    repo = AllianceRepository(mock_pool)
    assert repo.pool is not None
