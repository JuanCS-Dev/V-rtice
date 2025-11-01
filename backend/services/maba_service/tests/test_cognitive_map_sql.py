"""
Tests for PostgreSQL-based Cognitive Map

Tests the SQL alternative to Neo4j for cognitive map operations.

Biblical Foundation:
- Ecclesiastes 7:12: "Wisdom preserves the life of him who has it"
"""

# Mock asyncpg since we don't have real DB in tests
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_pool():
    """Mock AsyncPG pool."""
    pool = AsyncMock()
    conn = AsyncMock()

    # Mock fetchrow to return dict-like objects
    conn.fetchrow = AsyncMock(return_value={"id": "test-id", "selector": "#test"})
    conn.fetchval = AsyncMock(return_value=100)
    conn.fetch = AsyncMock(return_value=[])
    conn.execute = AsyncMock()

    # Mock acquire context manager
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    pool.close = AsyncMock()

    return pool


@pytest.fixture
async def cognitive_map_sql(mock_pool):
    """Create CognitiveMapSQL instance with mocked pool."""
    with patch(
        "core.cognitive_map_sql.asyncpg.create_pool",
        new_callable=AsyncMock,
        return_value=mock_pool,
    ):
        from core.cognitive_map_sql import CognitiveMapSQL

        engine = CognitiveMapSQL(
            db_host="localhost",
            db_port=5432,
            db_name="test_db",
            db_user="test_user",
            db_password="test_password",
        )

        await engine.initialize()
        yield engine
        await engine.close()


class TestInitialization:
    """Test SQL cognitive map initialization."""

    @pytest.mark.asyncio
    async def test_initialize_creates_schema(self, cognitive_map_sql):
        """
        GIVEN: Fresh CognitiveMapSQL instance
        WHEN: initialize() is called
        THEN: Schema is created and _initialized is True
        """
        assert cognitive_map_sql._initialized is True
        assert cognitive_map_sql.pool is not None


class TestPageStorage:
    """Test page storage operations."""

    @pytest.mark.asyncio
    async def test_store_page_without_elements(self, cognitive_map_sql):
        """
        GIVEN: Valid URL and title
        WHEN: store_page() called without elements
        THEN: Returns True
        """
        result = await cognitive_map_sql.store_page(
            url="https://example.com/test", title="Test Page"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_store_page_with_elements(self, cognitive_map_sql):
        """
        GIVEN: Page with elements
        WHEN: store_page() called with elements
        THEN: Returns True and stores elements
        """
        elements = [
            {
                "selector": "#button-1",
                "tag": "button",
                "text": "Click me",
                "attributes": {"class": "btn"},
            }
        ]

        result = await cognitive_map_sql.store_page(
            url="https://example.com/test", title="Test Page", elements=elements
        )

        assert result is True


class TestNavigation:
    """Test navigation storage."""

    @pytest.mark.asyncio
    async def test_store_navigation(self, cognitive_map_sql):
        """
        GIVEN: Two pages exist
        WHEN: store_navigation() called
        THEN: Returns True
        """
        result = await cognitive_map_sql.store_navigation(
            from_url="https://example.com/page1",
            to_url="https://example.com/page2",
            action="click",
            selector="#next",
        )

        assert result is True


class TestElementOperations:
    """Test element finding and interaction recording."""

    @pytest.mark.asyncio
    async def test_find_element_by_description(self, cognitive_map_sql):
        """
        GIVEN: Page with elements
        WHEN: find_element() called with description
        THEN: Returns selector if found
        """
        selector = await cognitive_map_sql.find_element(
            url="https://example.com/test", description="button", min_importance=0.3
        )

        assert selector == "#test"

    @pytest.mark.asyncio
    async def test_record_interaction(self, cognitive_map_sql):
        """
        GIVEN: Element exists
        WHEN: record_interaction() called
        THEN: Returns True and updates stats
        """
        result = await cognitive_map_sql.record_interaction(
            url="https://example.com/test",
            selector="#button",
            interaction_type="click",
            success=True,
        )

        assert result is True


class TestPathFinding:
    """Test navigation path finding."""

    @pytest.mark.asyncio
    async def test_get_navigation_path(self, cognitive_map_sql):
        """
        GIVEN: Navigation edges exist
        WHEN: get_navigation_path() called
        THEN: Returns path or None
        """
        path = await cognitive_map_sql.get_navigation_path(
            from_url="https://example.com/start", to_url="https://example.com/end"
        )

        # With mocked empty fetch, should return None
        assert path is None


class TestSimilarPages:
    """Test similar page finding."""

    @pytest.mark.asyncio
    async def test_get_similar_pages(self, cognitive_map_sql):
        """
        GIVEN: Pages exist in same domain
        WHEN: get_similar_pages() called
        THEN: Returns list of URLs
        """
        similar = await cognitive_map_sql.get_similar_pages(
            url="https://example.com/page1", limit=5
        )

        assert isinstance(similar, list)


class TestStats:
    """Test statistics retrieval."""

    @pytest.mark.asyncio
    async def test_get_stats(self, cognitive_map_sql):
        """
        GIVEN: Cognitive map with data
        WHEN: get_stats() called
        THEN: Returns stats dict
        """
        stats = await cognitive_map_sql.get_stats()

        assert "pages" in stats
        assert "elements" in stats
        assert "navigations" in stats
        assert stats["storage_backend"] == "postgresql"
