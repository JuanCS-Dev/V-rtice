"""Tests for semantic repository."""

from datetime import datetime
from uuid import uuid4

import pytest
from models import IntentClassification, SemanticRepresentation
from repository import SemanticRepository


@pytest.fixture
def mock_pool():
    """Mock asyncpg pool for testing."""

    class MockConnection:
        async def fetchrow(self, query: str, *args):
            if "WHERE message_id" in query:
                return None  # Simulate not found
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
def repository(mock_pool):
    """Create repository with mock pool."""
    return SemanticRepository(mock_pool)


@pytest.fixture
def sample_representation() -> SemanticRepresentation:
    """Create sample semantic representation."""
    return SemanticRepresentation(
        message_id="msg_test",
        source_agent_id="agent_test",
        timestamp=datetime.utcnow(),
        content_embedding=[0.1] * 384,
        intent_classification=IntentClassification.COOPERATIVE,
        intent_confidence=0.85,
        raw_content="Test message",
        provenance_chain=["msg_prev"],
    )


@pytest.mark.asyncio
async def test_repository_create(repository: SemanticRepository, sample_representation: SemanticRepresentation) -> None:
    """Test creating a semantic representation."""
    result = await repository.create(sample_representation)
    assert result is not None


@pytest.mark.asyncio
async def test_repository_batch_create(repository: SemanticRepository) -> None:
    """Test batch creating semantic representations."""
    representations = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_test",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.NEUTRAL,
            intent_confidence=0.7,
            raw_content=f"Message {i}",
        )
        for i in range(5)
    ]

    count = await repository.batch_create(representations)
    assert count == 5


def test_semantic_representation_fields(sample_representation: SemanticRepresentation) -> None:
    """Test semantic representation field validation."""
    assert len(sample_representation.content_embedding) == 384
    assert 0 <= sample_representation.intent_confidence <= 1
    assert sample_representation.message_id == "msg_test"
    assert len(sample_representation.provenance_chain) == 1


@pytest.mark.asyncio
async def test_repository_get_by_agent(repository: SemanticRepository) -> None:
    """Test get_by_agent method."""
    # This is a mock test - actual DB connection would be tested in integration tests
    results = await repository.get_by_agent("agent_test", limit=50)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_repository_get_by_message_id(repository: SemanticRepository) -> None:
    """Test get_by_message_id returns None when not found."""
    result = await repository.get_by_message_id("nonexistent_message")
    assert result is None


def test_repository_initialization(mock_pool) -> None:
    """Test repository initialization."""
    repo = SemanticRepository(mock_pool)
    assert repo.pool is not None


@pytest.mark.asyncio
async def test_repository_get_by_agent_with_since(repository: SemanticRepository) -> None:
    """Test get_by_agent with since parameter."""
    from datetime import datetime, timedelta

    since = datetime.utcnow() - timedelta(days=1)
    results = await repository.get_by_agent("agent_test", limit=10, since=since)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_create_pool() -> None:
    """Test create_pool function."""
    from repository import create_pool
    # Mock test - actual pool creation requires DB
    # This tests that the function exists and is callable
    assert callable(create_pool)
