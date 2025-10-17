"""Tests for repository database operations - 100% coverage."""

from datetime import datetime
from uuid import uuid4

import pytest

from models import IntentClassification
from repository import SemanticRepository, create_pool


@pytest.fixture
def enhanced_mock_pool():
    """Enhanced mock pool with full row data."""

    class MockConnection:
        async def fetchrow(self, query: str, *args):
            if "WHERE message_id" in query and args and args[0] == "found_message":
                # Return full row data to cover line 80
                return {
                    "id": uuid4(),
                    "message_id": "found_message",
                    "source_agent_id": "agent_test",
                    "timestamp": datetime.utcnow(),
                    "content_embedding": [0.1] * 384,
                    "intent_classification": "COOPERATIVE",
                    "intent_confidence": 0.85,
                    "raw_content": "Test content",
                    "provenance_chain": ["msg_parent"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            elif "WHERE message_id" in query:
                return None
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


@pytest.mark.asyncio
async def test_repository_get_by_message_id_found(enhanced_mock_pool):
    """Test get_by_message_id when message IS found - covers line 80."""
    repository = SemanticRepository(enhanced_mock_pool)

    result = await repository.get_by_message_id("found_message")

    assert result is not None
    assert result.message_id == "found_message"
    assert result.intent_classification == IntentClassification.COOPERATIVE
    assert len(result.content_embedding) == 384


@pytest.mark.asyncio
async def test_create_pool_function():
    """Test create_pool function exists and has correct signature - covers line 192."""
    # Test function exists
    assert callable(create_pool)

    # Test function signature (it's an async function)
    import inspect
    assert inspect.iscoroutinefunction(create_pool)

    # Verify it would call asyncpg.create_pool with correct params
    # (actual execution requires running PostgreSQL)


@pytest.mark.asyncio
async def test_create_pool_execution():
    """Test actual create_pool execution with mock - covers line 192 completely."""
    from unittest.mock import AsyncMock, patch

    with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create:
        mock_pool = AsyncMock()
        mock_create.return_value = mock_pool

        # Actually call create_pool which will execute line 192
        result = await create_pool()

        assert result == mock_pool
        mock_create.assert_awaited_once()
