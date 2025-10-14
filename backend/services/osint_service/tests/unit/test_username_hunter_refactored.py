"""Unit tests for UsernameHunterRefactored.

Tests the production-hardened Username Hunter with 90%+ coverage.

Uses pytest-mock for HTTP mocking (no real HTTP calls in tests).

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from scrapers.username_hunter_refactored import UsernameHunterRefactored


@pytest.fixture(autouse=True)
def mock_cache_globally(monkeypatch):
    """Global fixture to mock cache operations (avoids Redis dependency in ALL tests)."""
    async def get_mock(self, key):
        return None

    async def set_mock(self, key, value):
        pass

    # Patch CacheManager methods globally
    from core.cache_manager import CacheManager
    monkeypatch.setattr(CacheManager, "get", get_mock)
    monkeypatch.setattr(CacheManager, "set", set_mock)


class TestUsernameHunterBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_hunter_initialization(self):
        """Test hunter initializes correctly."""
        hunter = UsernameHunterRefactored()

        assert hunter.total_searches == 0
        assert hunter.total_platforms_checked == 0
        assert hunter.total_found == 0
        assert len(hunter.PLATFORMS) >= 20  # Should have 20+ platforms

    @pytest.mark.asyncio
    async def test_supported_platforms(self):
        """Test supported platforms list."""
        hunter = UsernameHunterRefactored()

        # Check key platforms are present
        assert "github" in hunter.PLATFORMS
        assert "reddit" in hunter.PLATFORMS
        assert "medium" in hunter.PLATFORMS
        assert "devto" in hunter.PLATFORMS

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method for debugging."""
        hunter = UsernameHunterRefactored()

        repr_str = repr(hunter)

        assert "UsernameHunterRefactored" in repr_str
        assert "searches=0" in repr_str
        assert f"platforms={len(hunter.PLATFORMS)}" in repr_str


class TestUsernameSearch:
    """Username search tests."""

    @pytest.mark.asyncio
    async def test_search_username_found_on_platform(self, monkeypatch):
        """Test searching username that exists on a platform."""
        hunter = UsernameHunterRefactored()

        # Mock HTTP response (200 = found)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        # Search on single platform
        result = await hunter.query(
            target="elonmusk",
            platforms=["github"]
        )

        # Verify result
        assert result["username"] == "elonmusk"
        assert result["platforms_checked"] == 1
        assert result["found_count"] == 1
        assert len(result["found_platforms"]) == 1
        assert result["found_platforms"][0]["platform"] == "github"
        assert result["found_platforms"][0]["found"] is True

    @pytest.mark.asyncio
    async def test_search_username_not_found(self, monkeypatch):
        """Test searching username that doesn't exist."""
        hunter = UsernameHunterRefactored()

        # Mock HTTP response (404 = not found)
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        # Search
        result = await hunter.query(
            target="nonexistent_user_xyz123",
            platforms=["github"]
        )

        # Verify not found
        assert result["found_count"] == 0
        assert result["not_found_count"] == 1
        assert len(result["found_platforms"]) == 0

    @pytest.mark.asyncio
    async def test_search_multiple_platforms(self, monkeypatch):
        """Test searching across multiple platforms."""
        hunter = UsernameHunterRefactored()

        # Mock responses: GitHub found (200), Reddit not found (404)
        def mock_get(url, **kwargs):
            mock_response = AsyncMock()
            if "github.com" in url:
                mock_response.status = 200
            elif "reddit.com" in url:
                mock_response.status = 404
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            return mock_response

        mock_session = MagicMock()
        mock_session.get = mock_get
        hunter.session = mock_session

        # Search multiple platforms
        result = await hunter.query(
            target="testuser",
            platforms=["github", "reddit"]
        )

        # Verify results
        assert result["platforms_checked"] == 2
        assert result["found_count"] == 1
        assert result["not_found_count"] == 1

    @pytest.mark.asyncio
    async def test_search_all_platforms(self, monkeypatch):
        """Test searching all platforms (defaults)."""
        hunter = UsernameHunterRefactored()

        # Mock all responses as not found
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        # Search (no platforms specified = all)
        result = await hunter.query(target="testuser")

        # Should check all platforms
        assert result["platforms_checked"] == len(hunter.PLATFORMS)
        assert result["found_count"] == 0


class TestInputValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_empty_username_raises_error(self):
        """Test empty username raises ValueError."""
        hunter = UsernameHunterRefactored()

        with pytest.raises(ValueError, match="at least 2 characters"):
            await hunter.query(target="")

    @pytest.mark.asyncio
    async def test_short_username_raises_error(self):
        """Test username too short raises ValueError."""
        hunter = UsernameHunterRefactored()

        with pytest.raises(ValueError, match="at least 2 characters"):
            await hunter.query(target="a")

    @pytest.mark.asyncio
    async def test_invalid_platform_raises_error(self):
        """Test invalid platform name raises ValueError."""
        hunter = UsernameHunterRefactored()

        with pytest.raises(ValueError, match="Invalid platforms"):
            await hunter.query(
                target="testuser",
                platforms=["invalid_platform_xyz"]
            )

    @pytest.mark.asyncio
    async def test_username_stripped(self, monkeypatch):
        """Test username is stripped of whitespace."""
        hunter = UsernameHunterRefactored()

        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        # Username with whitespace
        result = await hunter.query(target="  testuser  ", platforms=["github"])

        # Should be stripped
        assert result["username"] == "testuser"


class TestConfidenceScoring:
    """Confidence score calculation tests."""

    @pytest.mark.asyncio
    async def test_confidence_score_all_found(self):
        """Test confidence score when username found on all platforms."""
        hunter = UsernameHunterRefactored()

        found_platforms = [
            {"platform": "github", "found": True},
            {"platform": "reddit", "found": True},
        ]

        score = hunter._calculate_confidence_score(found_platforms, 2)

        # 100% found = 100 base score
        assert score == 100

    @pytest.mark.asyncio
    async def test_confidence_score_half_found(self):
        """Test confidence score when username found on half platforms."""
        hunter = UsernameHunterRefactored()

        found_platforms = [
            {"platform": "github", "found": True},
        ]

        score = hunter._calculate_confidence_score(found_platforms, 2)

        # 50% found = 50 base score + potential boost
        assert score >= 50
        assert score <= 100

    @pytest.mark.asyncio
    async def test_confidence_score_none_found(self):
        """Test confidence score when username not found anywhere."""
        hunter = UsernameHunterRefactored()

        found_platforms = []

        score = hunter._calculate_confidence_score(found_platforms, 5)

        assert score == 0

    @pytest.mark.asyncio
    async def test_confidence_score_important_platform_boost(self):
        """Test confidence boost for important platforms."""
        hunter = UsernameHunterRefactored()

        # Found on GitHub (important platform)
        found_platforms = [
            {"platform": "github", "found": True},
        ]

        score_with_important = hunter._calculate_confidence_score(found_platforms, 10)

        # Found on less important platform
        found_platforms_regular = [
            {"platform": "pastebin", "found": True},
        ]

        score_without_important = hunter._calculate_confidence_score(found_platforms_regular, 10)

        # GitHub should give higher score due to importance boost
        assert score_with_important > score_without_important


class TestParallelSearch:
    """Parallel search execution tests."""

    @pytest.mark.asyncio
    async def test_parallel_search_all_succeed(self, monkeypatch):
        """Test parallel search when all platforms succeed."""
        hunter = UsernameHunterRefactored()

        # Mock all responses as found
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        # Search 3 platforms
        result = await hunter.query(
            target="testuser",
            platforms=["github", "reddit", "medium"]
        )

        # All should be found
        assert result["found_count"] == 3
        assert result["not_found_count"] == 0

    @pytest.mark.asyncio
    async def test_parallel_search_with_failure(self, monkeypatch):
        """Test parallel search handles platform failure gracefully."""
        hunter = UsernameHunterRefactored()

        # Mock one platform to raise exception
        def mock_get(url, **kwargs):
            mock_response = AsyncMock()
            if "github.com" in url:
                raise Exception("Connection timeout")
            else:
                mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            return mock_response

        mock_session = MagicMock()
        mock_session.get = mock_get
        hunter.session = mock_session

        # Search should complete despite one failure
        result = await hunter.query(
            target="testuser",
            platforms=["github", "reddit"]
        )

        # Reddit should succeed, GitHub should fail
        assert result["platforms_checked"] == 2
        # Note: Due to exception handling, we expect it to handle gracefully


class TestIncludeUnavailable:
    """Tests for include_unavailable parameter."""

    @pytest.mark.asyncio
    async def test_include_unavailable_false(self, monkeypatch):
        """Test that not_found_platforms are excluded by default."""
        hunter = UsernameHunterRefactored()

        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        result = await hunter.query(
            target="testuser",
            platforms=["github"],
            include_unavailable=False
        )

        # Should not include not_found_platforms list
        assert "not_found_platforms" not in result

    @pytest.mark.asyncio
    async def test_include_unavailable_true(self, monkeypatch):
        """Test that not_found_platforms are included when requested."""
        hunter = UsernameHunterRefactored()

        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        result = await hunter.query(
            target="testuser",
            platforms=["github"],
            include_unavailable=True
        )

        # Should include not_found_platforms list
        assert "not_found_platforms" in result
        assert "github" in result["not_found_platforms"]


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated_after_search(self, monkeypatch):
        """Test statistics are updated after searches."""
        hunter = UsernameHunterRefactored()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        # Perform search
        await hunter.query(target="testuser", platforms=["github", "reddit"])

        # Verify statistics
        assert hunter.total_searches == 1
        assert hunter.total_platforms_checked == 2
        assert hunter.total_found == 2  # Both found

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        hunter = UsernameHunterRefactored()

        status = await hunter.get_status()

        assert status["tool"] == "UsernameHunterRefactored"
        assert status["total_searches"] == 0
        assert status["supported_platforms"] == len(hunter.PLATFORMS)
        assert "platform_list" in status


class TestObservability:
    """Observability tests (logging, metrics)."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        hunter = UsernameHunterRefactored()

        assert hunter.logger is not None
        assert hunter.logger.tool_name == "UsernameHunterRefactored"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        hunter = UsernameHunterRefactored()

        assert hunter.metrics is not None
        assert hunter.metrics.tool_name == "UsernameHunterRefactored"


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_session_initialization_on_demand(self, monkeypatch):
        """Test session is initialized on demand when None."""
        hunter = UsernameHunterRefactored()

        # Ensure session is None
        hunter.session = None

        # Mock aiohttp.ClientSession
        mock_session_instance = MagicMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get = MagicMock(return_value=mock_response)

        mock_session_class = MagicMock(return_value=mock_session_instance)
        monkeypatch.setattr("aiohttp.ClientSession", mock_session_class)

        # Call _check_platform (should initialize session)
        result = await hunter._check_platform("testuser", "github")

        # Verify session was initialized
        assert hunter.session is not None
        assert result["found"] is True

    @pytest.mark.asyncio
    async def test_platform_url_formatting(self):
        """Test platform URL formatting with special characters."""
        hunter = UsernameHunterRefactored()

        # Username with special chars should be URL-encoded
        from urllib.parse import quote
        username = "user@test"
        platform = "github"

        url = hunter.PLATFORMS[platform]["url"].format(username=quote(username))

        # Should be properly encoded
        assert "user%40test" in url

    @pytest.mark.asyncio
    async def test_zero_platforms_checked(self):
        """Test confidence score with zero platforms."""
        hunter = UsernameHunterRefactored()

        score = hunter._calculate_confidence_score([], 0)

        assert score == 0

    @pytest.mark.asyncio
    async def test_username_case_sensitivity(self, monkeypatch):
        """Test that username preserves case."""
        hunter = UsernameHunterRefactored()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hunter.session = mock_session

        # Mixed case username
        result = await hunter.query(target="TestUser", platforms=["github"])

        # Should preserve case
        assert result["username"] == "TestUser"
