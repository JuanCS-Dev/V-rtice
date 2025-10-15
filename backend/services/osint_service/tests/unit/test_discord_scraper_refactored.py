"""Unit tests for DiscordScraperRefactored.

Tests the production-hardened Discord Scraper with 100% coverage.

Uses mocks for Discord API to avoid real network calls.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from scrapers.discord_scraper_refactored import DiscordScraperRefactored


@pytest.fixture(autouse=True)
def mock_cache_globally(monkeypatch):
    """Global fixture to mock cache operations."""
    async def get_mock(self, key):
        return None

    async def set_mock(self, key, value):
        pass

    from core.cache_manager import CacheManager
    monkeypatch.setattr(CacheManager, "get", get_mock)
    monkeypatch.setattr(CacheManager, "set", set_mock)


class TestDiscordScraperBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_scraper_initialization_with_token(self):
        """Test scraper initializes correctly with token."""
        scraper = DiscordScraperRefactored(api_key="test_token_12345")

        assert scraper.total_scrapes == 0
        assert scraper.total_messages == 0
        assert scraper.total_guilds == 0
        assert scraper.api_key == "test_token_12345"
        assert scraper.client is None  # Lazy initialization
        assert scraper._client_ready is False

    @pytest.mark.asyncio
    async def test_scraper_initialization_without_token(self):
        """Test scraper initializes without token (will error on use)."""
        scraper = DiscordScraperRefactored()

        assert scraper.api_key is None
        assert scraper.client is None

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        repr_str = repr(scraper)

        assert "DiscordScraperRefactored" in repr_str
        assert "scrapes=0" in repr_str
        assert "messages=0" in repr_str
        assert "connected=False" in repr_str


class TestInputValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_query_without_token_raises_error(self):
        """Test querying without bot token raises ValueError."""
        scraper = DiscordScraperRefactored()  # No token

        with pytest.raises(ValueError, match="Discord bot token.*required"):
            await scraper.query(target="123456", operation="channel_history")

    @pytest.mark.asyncio
    async def test_query_with_invalid_operation_raises_error(self):
        """Test invalid operation raises ValueError."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client to avoid connection
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        scraper.client = mock_client
        scraper._client_ready = True

        with pytest.raises(ValueError, match="Invalid operation"):
            await scraper.query(target="123456", operation="invalid_op")


class TestChannelHistoryScraping:
    """Channel history scraping tests."""

    @pytest.mark.asyncio
    async def test_scrape_channel_history_success(self, monkeypatch):
        """Test successful channel history scraping."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client and channel
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.user = MagicMock(name="TestBot")

        # Mock channel with history attribute
        mock_channel = MagicMock()
        mock_channel.id = 123456

        # Mock messages
        mock_message1 = MagicMock()
        mock_message1.id = 111
        mock_message1.content = "Test message 1"
        mock_message1.author = MagicMock(id=999, name="User1", discriminator="1234", bot=False)
        mock_message1.created_at = datetime.now(timezone.utc)
        mock_message1.edited_at = None
        mock_message1.attachments = []
        mock_message1.embeds = []
        mock_message1.reactions = []

        mock_message2 = MagicMock()
        mock_message2.id = 222
        mock_message2.content = "Test message 2"
        mock_message2.author = MagicMock(id=888, name="User2", discriminator="5678", bot=False)
        mock_message2.created_at = datetime.now(timezone.utc)
        mock_message2.edited_at = None
        mock_message2.attachments = []
        mock_message2.embeds = []
        mock_message2.reactions = []

        # Mock async iterator for history
        async def mock_history(limit):
            for msg in [mock_message1, mock_message2]:
                yield msg

        mock_channel.history = mock_history
        mock_client.get_channel.return_value = mock_channel

        # Set up scraper
        scraper.client = mock_client
        scraper._client_ready = True

        # Scrape
        result = await scraper.query(target="123456", operation="channel_history", limit=10)

        # Verify
        assert result["operation"] == "channel_history"
        assert result["message_count"] == 2
        assert len(result["messages"]) == 2
        assert result["messages"][0]["content"] == "Test message 1"
        assert result["messages"][1]["content"] == "Test message 2"
        assert scraper.total_messages == 2
        assert scraper.total_scrapes == 1

    @pytest.mark.asyncio
    async def test_scrape_channel_not_found(self, monkeypatch):
        """Test scraping non-existent channel."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_channel = MagicMock(return_value=None)

        # Mock fetch_channel to raise NotFound
        import discord
        async def raise_not_found(channel_id):
            raise discord.NotFound(MagicMock(), "Channel not found")

        mock_client.fetch_channel = raise_not_found

        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="Channel.*not found"):
            await scraper.query(target="999999", operation="channel_history")

    @pytest.mark.asyncio
    async def test_scrape_channel_forbidden(self, monkeypatch):
        """Test scraping channel without permission."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)

        # Mock channel that raises Forbidden
        import discord
        mock_channel = MagicMock()

        async def raise_forbidden(limit):
            raise discord.Forbidden(MagicMock(), "Missing permissions")
            yield  # Make it a generator

        mock_channel.history = raise_forbidden
        mock_client.get_channel.return_value = mock_channel

        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="Bot lacks permission"):
            await scraper.query(target="123456", operation="channel_history")


class TestGuildInfo:
    """Guild information tests."""

    @pytest.mark.asyncio
    async def test_get_guild_info_success(self):
        """Test successful guild info retrieval."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client and guild
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)

        mock_guild = MagicMock()
        mock_guild.id = 123456
        mock_guild.name = "Test Server"
        mock_guild.description = "Test Description"
        mock_guild.member_count = 100
        mock_guild.created_at = datetime.now(timezone.utc)
        mock_guild.owner_id = 999
        mock_guild.icon = MagicMock(url="http://icon.url")
        mock_guild.banner = None
        mock_guild.text_channels = [MagicMock() for _ in range(5)]
        mock_guild.voice_channels = [MagicMock() for _ in range(2)]
        mock_guild.roles = [MagicMock() for _ in range(10)]

        mock_client.get_guild.return_value = mock_guild

        scraper.client = mock_client
        scraper._client_ready = True

        # Get guild info
        result = await scraper.query(target="123456", operation="guild_info")

        # Verify
        assert result["operation"] == "guild_info"
        assert result["guild"]["name"] == "Test Server"
        assert result["guild"]["member_count"] == 100
        assert result["guild"]["text_channels_count"] == 5
        assert result["guild"]["voice_channels_count"] == 2
        assert scraper.total_guilds == 1

    @pytest.mark.asyncio
    async def test_get_guild_not_found(self):
        """Test getting non-existent guild."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_guild.return_value = None

        # Mock fetch_guild to raise NotFound
        import discord
        async def raise_not_found(guild_id):
            raise discord.NotFound(MagicMock(), "Guild not found")

        mock_client.fetch_guild = raise_not_found

        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="Guild.*not found"):
            await scraper.query(target="999999", operation="guild_info")


class TestUserInfo:
    """User information tests."""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client and user
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)

        mock_user = MagicMock()
        mock_user.id = 123456
        mock_user.name = "TestUser"
        mock_user.discriminator = "1234"
        mock_user.bot = False
        mock_user.system = False
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.avatar = MagicMock(url="http://avatar.url")
        mock_user.banner = None

        mock_client.get_user.return_value = mock_user

        scraper.client = mock_client
        scraper._client_ready = True

        # Get user info
        result = await scraper.query(target="123456", operation="user_info")

        # Verify
        assert result["operation"] == "user_info"
        assert result["user"]["name"] == "TestUser"
        assert result["user"]["discriminator"] == "1234"
        assert result["user"]["bot"] is False

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        """Test getting non-existent user."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_user.return_value = None

        # Mock fetch_user to raise NotFound
        import discord
        async def raise_not_found(user_id):
            raise discord.NotFound(MagicMock(), "User not found")

        mock_client.fetch_user = raise_not_found

        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="User.*not found"):
            await scraper.query(target="999999", operation="user_info")


class TestChannelInfo:
    """Channel information tests."""

    @pytest.mark.asyncio
    async def test_get_channel_info_success(self):
        """Test successful channel info retrieval."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock Discord client and channel
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)

        # Import discord.TextChannel for isinstance check
        import discord
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.id = 123456
        mock_channel.name = "general"
        mock_channel.type = MagicMock(__str__=lambda x: "text")
        mock_channel.created_at = datetime.now(timezone.utc)
        mock_channel.topic = "General chat"
        mock_channel.nsfw = False
        mock_channel.slowmode_delay = 0
        mock_channel.guild = MagicMock(id=999)

        mock_client.get_channel.return_value = mock_channel

        scraper.client = mock_client
        scraper._client_ready = True

        # Get channel info
        result = await scraper.query(target="123456", operation="channel_info")

        # Verify
        assert result["operation"] == "channel_info"
        assert result["channel"]["name"] == "general"
        assert result["channel"]["topic"] == "General chat"
        assert result["channel"]["nsfw"] is False


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_statistics_updated_after_scrapes(self):
        """Test statistics are updated after scrapes."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.user = MagicMock(name="TestBot")

        # Mock channel with messages
        mock_channel = MagicMock()
        async def mock_history(limit):
            for i in range(3):
                msg = MagicMock()
                msg.id = i
                msg.content = f"Message {i}"
                msg.author = MagicMock(id=i, name=f"User{i}", discriminator="0000", bot=False)
                msg.created_at = datetime.now(timezone.utc)
                msg.edited_at = None
                msg.attachments = []
                msg.embeds = []
                msg.reactions = []
                yield msg

        mock_channel.history = mock_history
        mock_client.get_channel.return_value = mock_channel

        scraper.client = mock_client
        scraper._client_ready = True

        # Perform scrape
        await scraper.query(target="123456", operation="channel_history", limit=10)

        # Verify statistics
        assert scraper.total_scrapes == 1
        assert scraper.total_messages == 3

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status returns correct information."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        status = await scraper.get_status()

        assert status["tool"] == "DiscordScraperRefactored"
        assert status["total_scrapes"] == 0
        assert status["total_messages"] == 0
        assert status["total_guilds"] == 0
        assert status["client_ready"] is False


class TestObservability:
    """Observability tests."""

    @pytest.mark.asyncio
    async def test_logging_configured(self):
        """Test structured logger is configured."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        assert scraper.logger is not None
        assert scraper.logger.tool_name == "DiscordScraperRefactored"

    @pytest.mark.asyncio
    async def test_metrics_configured(self):
        """Test metrics collector is configured."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        assert scraper.metrics is not None
        assert scraper.metrics.tool_name == "DiscordScraperRefactored"


class TestClientManagement:
    """Discord client management tests."""

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing Discord client."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_closed = MagicMock(return_value=False)
        mock_client.close = AsyncMock()
        scraper.client = mock_client

        # Close
        await scraper.close()

        # Verify close was called
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_already_closed_client(self):
        """Test closing already closed client (no-op)."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock already closed client
        mock_client = MagicMock()
        mock_client.is_closed.return_value = True
        scraper.client = mock_client

        # Close (should not call close again)
        await scraper.close()

        # Verify close was NOT called
        mock_client.close.assert_not_called()


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_channel_history_with_attachments_and_reactions(self):
        """Test scraping messages with attachments and reactions."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)

        # Mock channel with complex message
        mock_channel = MagicMock()

        async def mock_history(limit):
            msg = MagicMock()
            msg.id = 1
            msg.content = "Complex message"
            msg.author = MagicMock(id=1, name="User1", discriminator="0000", bot=False)
            msg.created_at = datetime.now(timezone.utc)
            msg.edited_at = datetime.now(timezone.utc)  # Edited
            msg.attachments = [MagicMock(url="http://file1.jpg"), MagicMock(url="http://file2.png")]
            msg.embeds = [MagicMock(), MagicMock()]  # 2 embeds
            msg.reactions = [MagicMock(count=5), MagicMock(count=3)]  # 8 total reactions
            yield msg

        mock_channel.history = mock_history
        mock_client.get_channel.return_value = mock_channel

        scraper.client = mock_client
        scraper._client_ready = True

        # Scrape
        result = await scraper.query(target="123456", operation="channel_history", limit=1)

        # Verify
        message = result["messages"][0]
        assert message["edited_timestamp"] is not None
        assert len(message["attachments"]) == 2
        assert message["embeds_count"] == 2
        assert message["reactions_count"] == 8

    @pytest.mark.asyncio
    async def test_default_operation_is_channel_history(self):
        """Test default operation when not specified."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)

        mock_channel = MagicMock()
        async def mock_history(limit):
            return
            yield  # Empty generator

        mock_channel.history = mock_history
        mock_client.get_channel.return_value = mock_channel

        scraper.client = mock_client
        scraper._client_ready = True

        # Query without operation specified (should default to channel_history)
        result = await scraper.query(target="123456")

        # Verify default operation
        assert result["operation"] == "channel_history"

    @pytest.mark.asyncio
    async def test_channel_not_text_channel_raises_error(self):
        """Test error when channel is not a text channel."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)

        # Mock voice channel (not text) - explicitly no history attribute
        mock_channel = MagicMock()
        mock_channel.id = 123456
        # Remove history attribute to simulate voice channel
        del mock_channel.history

        mock_client.get_channel.return_value = mock_channel

        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="not a text channel"):
            await scraper.query(target="123456", operation="channel_history")


class TestClientInitialization:
    """Client initialization and connection tests."""

    @pytest.mark.asyncio
    async def test_ensure_client_creates_new_client(self):
        """Test _ensure_client creates Discord client when None."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Verify client is None initially
        assert scraper.client is None

        # Mock discord.Client to prevent real connection
        import discord
        with patch.object(discord, 'Client') as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.is_ready = MagicMock(return_value=True)
            mock_instance.user = MagicMock(name="TestBot")
            mock_client_class.return_value = mock_instance

            # Mock asyncio.create_task to prevent background task
            with patch('asyncio.create_task'):
                await scraper._ensure_client()

        # Verify client was created
        assert scraper.client is not None
        assert scraper._client_ready is True

    @pytest.mark.asyncio
    async def test_ensure_client_reuses_existing_client(self):
        """Test _ensure_client doesn't recreate when client exists."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Set up existing client
        mock_client = MagicMock()
        scraper.client = mock_client
        scraper._client_ready = True

        # Call _ensure_client
        await scraper._ensure_client()

        # Verify same client instance is used
        assert scraper.client is mock_client

    @pytest.mark.asyncio
    async def test_wait_for_ready_timeout(self):
        """Test _wait_for_ready raises TimeoutError on timeout."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client that never becomes ready
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=False)
        scraper.client = mock_client

        # Should raise TimeoutError
        with pytest.raises(TimeoutError, match="Discord client failed to connect"):
            await scraper._wait_for_ready(timeout=0.1)

    @pytest.mark.asyncio
    async def test_wait_for_ready_success(self):
        """Test _wait_for_ready succeeds when client becomes ready."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client that becomes ready immediately
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.user = MagicMock(name="TestBot")
        scraper.client = mock_client

        # Should succeed
        await scraper._wait_for_ready(timeout=1)

        # Verify client_ready flag set
        assert scraper._client_ready is True


class TestFetchFallbacks:
    """Tests for fetch fallback paths (when get_* returns None)."""

    @pytest.mark.asyncio
    async def test_guild_fetch_fallback_success(self):
        """Test guild_info uses fetch_guild when get_guild returns None."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_guild.return_value = None  # Not in cache

        # Mock fetch_guild to return guild
        mock_guild = MagicMock()
        mock_guild.id = 123456
        mock_guild.name = "Fetched Guild"
        mock_guild.description = "Fetched from API"
        mock_guild.member_count = 50
        mock_guild.created_at = datetime.now(timezone.utc)
        mock_guild.owner_id = 999
        mock_guild.icon = None
        mock_guild.banner = None
        mock_guild.text_channels = []
        mock_guild.voice_channels = []
        mock_guild.roles = []

        async def mock_fetch_guild(guild_id):
            return mock_guild

        mock_client.fetch_guild = mock_fetch_guild
        scraper.client = mock_client
        scraper._client_ready = True

        # Get guild info
        result = await scraper.query(target="123456", operation="guild_info")

        # Verify fetch was used
        assert result["guild"]["name"] == "Fetched Guild"

    @pytest.mark.asyncio
    async def test_guild_fetch_fallback_forbidden(self):
        """Test guild_info handles Forbidden on fetch_guild."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_guild.return_value = None

        # Mock fetch_guild to raise Forbidden
        import discord
        async def raise_forbidden(guild_id):
            raise discord.Forbidden(MagicMock(), "Missing permissions")

        mock_client.fetch_guild = raise_forbidden
        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="Bot lacks permission to access guild"):
            await scraper.query(target="123456", operation="guild_info")

    @pytest.mark.asyncio
    async def test_channel_fetch_fallback_success(self):
        """Test channel_info uses fetch_channel when get_channel returns None."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_channel.return_value = None  # Not in cache

        # Mock fetch_channel to return channel
        mock_channel = MagicMock()
        mock_channel.id = 123456
        mock_channel.name = "fetched-channel"
        mock_channel.type = MagicMock(__str__=lambda x: "voice")
        mock_channel.created_at = datetime.now(timezone.utc)
        # No topic attribute (voice channel) - explicitly delete to simulate
        del mock_channel.topic

        async def mock_fetch_channel(channel_id):
            return mock_channel

        mock_client.fetch_channel = mock_fetch_channel
        scraper.client = mock_client
        scraper._client_ready = True

        # Get channel info
        result = await scraper.query(target="123456", operation="channel_info")

        # Verify fetch was used
        assert result["channel"]["name"] == "fetched-channel"
        assert result["channel"]["type"] == "voice"
        assert "topic" not in result["channel"]  # Voice channel has no topic

    @pytest.mark.asyncio
    async def test_channel_fetch_fallback_forbidden(self):
        """Test channel_info handles Forbidden on fetch_channel."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_channel.return_value = None

        # Mock fetch_channel to raise Forbidden
        import discord
        async def raise_forbidden(channel_id):
            raise discord.Forbidden(MagicMock(), "Missing permissions")

        mock_client.fetch_channel = raise_forbidden
        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="Bot lacks permission to access channel"):
            await scraper.query(target="123456", operation="channel_info")

    @pytest.mark.asyncio
    async def test_channel_fetch_fallback_not_found(self):
        """Test channel_info handles NotFound on fetch_channel."""
        scraper = DiscordScraperRefactored(api_key="test_token")

        # Mock client
        mock_client = MagicMock()
        mock_client.is_ready = MagicMock(return_value=True)
        mock_client.get_channel.return_value = None

        # Mock fetch_channel to raise NotFound
        import discord
        async def raise_not_found(channel_id):
            raise discord.NotFound(MagicMock(), "Channel not found")

        mock_client.fetch_channel = raise_not_found
        scraper.client = mock_client
        scraper._client_ready = True

        # Should raise ValueError
        with pytest.raises(ValueError, match="Channel.*not found"):
            await scraper.query(target="999999", operation="channel_info")
