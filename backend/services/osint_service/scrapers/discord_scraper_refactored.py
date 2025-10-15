"""Maximus OSINT Service - Discord Scraper (Production-Hardened).

Production-grade Discord scraper with real Discord API integration.

Key improvements:
- ✅ Real Discord API integration (discord.py)
- ✅ Channel message history scraping
- ✅ Server (guild) information extraction
- ✅ User profile lookups
- ✅ Structured JSON logging
- ✅ Prometheus metrics
- ✅ Inherits from BaseTool patterns

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, real Discord API
    - Article V (Prior Legislation): Observability first
    - Article VII (Antifragility): Circuit breakers, retries, graceful degradation
    - Article IX (Zero Trust): Input validation, rate limiting

Supported Operations:
    - Channel history scraping (messages with metadata)
    - Server/guild information
    - User profile lookups
    - Channel information

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 2.0.0
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import discord

from core.base_tool import BaseTool


class DiscordScraperRefactored(BaseTool):
    """Production-grade Discord scraper with real Discord API integration.

    Inherits from BaseTool to get:
    - Rate limiting (token bucket)
    - Circuit breaker (fail-fast on repeated failures)
    - Caching (Redis + in-memory)
    - Structured logging
    - Prometheus metrics
    - Automatic retries with exponential backoff

    Usage Example:
        scraper = DiscordScraperRefactored(
            api_key="YOUR_DISCORD_BOT_TOKEN",
            rate_limit=1.0,  # 1 request/second (Discord is strict)
        )

        # Scrape channel history
        result = await scraper.query(
            target="channel_id",
            operation="channel_history",
            limit=100
        )

        # Get server info
        result = await scraper.query(
            target="guild_id",
            operation="guild_info"
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 1.0,  # Discord has strict rate limits
        timeout: int = 30,
        max_retries: int = 2,
        cache_ttl: int = 1800,  # 30 minutes cache (Discord data changes frequently)
        cache_backend: str = "memory",
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """Initialize DiscordScraperRefactored.

        Args:
            api_key: Discord bot token (required for real API calls)
            rate_limit: Requests per second (1.0 = conservative)
            timeout: HTTP timeout in seconds
            max_retries: Retry attempts
            cache_ttl: Cache time-to-live in seconds (30min = reasonable)
            cache_backend: 'redis' or 'memory'
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Seconds before attempting recovery
        """
        super().__init__(
            api_key=api_key,
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout,
        )

        # Statistics
        self.total_scrapes = 0
        self.total_messages = 0
        self.total_guilds = 0

        # Discord client (lazy initialization)
        self.client: Optional[discord.Client] = None
        self._client_ready = False

        self.logger.info("discord_scraper_initialized", has_token=bool(api_key))

    async def _query_impl(self, target: str, **params) -> Dict[str, Any]:
        """Implementation of Discord scraping logic.

        Args:
            target: Channel ID, Guild ID, or User ID (depending on operation)
            **params:
                - operation: Type of operation ('channel_history', 'guild_info', 'user_info', 'channel_info')
                - limit: Max messages to fetch (for channel_history, default: 100)

        Returns:
            Scraping result dictionary

        Raises:
            ValueError: If operation is invalid or bot token missing
        """
        operation = params.get("operation", "channel_history")
        limit = params.get("limit", 100)

        if not self.api_key:
            raise ValueError("Discord bot token (api_key) is required for Discord scraping")

        # Ensure Discord client is connected
        await self._ensure_client()

        self.logger.info(
            "discord_scrape_started",
            operation=operation,
            target=target,
            limit=limit if operation == "channel_history" else None,
        )

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "target": target,
        }

        if operation == "channel_history":
            result["messages"] = await self._scrape_channel_history(target, limit)
            result["message_count"] = len(result["messages"])
            self.total_messages += result["message_count"]

        elif operation == "guild_info":
            result["guild"] = await self._get_guild_info(target)
            self.total_guilds += 1

        elif operation == "user_info":
            result["user"] = await self._get_user_info(target)

        elif operation == "channel_info":
            result["channel"] = await self._get_channel_info(target)

        else:
            raise ValueError(
                f"Invalid operation: {operation}. "
                f"Supported: channel_history, guild_info, user_info, channel_info"
            )

        self.total_scrapes += 1
        self.logger.info("discord_scrape_complete", operation=operation, scrapes=self.total_scrapes)

        return result

    async def _ensure_client(self):
        """Ensure Discord client is connected and ready."""
        if self.client is None:
            # Create client with minimal intents (read-only)
            intents = discord.Intents.default()
            intents.message_content = True  # Required to read message content
            intents.guilds = True
            intents.members = False  # Don't need member events

            self.client = discord.Client(intents=intents)

            # Start client in background
            asyncio.create_task(self.client.start(self.api_key))

            # Wait for client to be ready
            await self._wait_for_ready()

    async def _wait_for_ready(self, timeout: int = 10):
        """Wait for Discord client to be ready.

        Args:
            timeout: Max seconds to wait

        Raises:
            TimeoutError: If client doesn't connect within timeout
        """
        start = asyncio.get_event_loop().time()
        while not self.client.is_ready():
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError("Discord client failed to connect within timeout")
            await asyncio.sleep(0.1)

        self._client_ready = True
        self.logger.info("discord_client_ready", user=str(self.client.user))

    async def _scrape_channel_history(self, channel_id: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape message history from a Discord channel.

        Args:
            channel_id: Discord channel ID
            limit: Max messages to fetch

        Returns:
            List of message dictionaries
        """
        try:
            channel = self.client.get_channel(int(channel_id))
            if not channel:
                # Try fetching if not in cache
                channel = await self.client.fetch_channel(int(channel_id))

            # Check if channel has history method (duck typing for testability)
            if not (hasattr(channel, 'history') and callable(getattr(channel, 'history', None))):
                raise ValueError(f"Channel {channel_id} is not a text channel")

            messages = []
            async for message in channel.history(limit=limit):
                messages.append({
                    "id": str(message.id),
                    "content": message.content,
                    "author": {
                        "id": str(message.author.id),
                        "name": message.author.name,
                        "discriminator": message.author.discriminator,
                        "bot": message.author.bot,
                    },
                    "timestamp": message.created_at.isoformat(),
                    "edited_timestamp": message.edited_at.isoformat() if message.edited_at else None,
                    "attachments": [att.url for att in message.attachments],
                    "embeds_count": len(message.embeds),
                    "reactions_count": sum(r.count for r in message.reactions) if message.reactions else 0,
                })

            self.logger.info("channel_history_scraped", channel_id=channel_id, message_count=len(messages))
            return messages

        except discord.Forbidden:
            self.logger.error("channel_access_forbidden", channel_id=channel_id)
            raise ValueError(f"Bot lacks permission to access channel {channel_id}")
        except discord.NotFound:
            self.logger.error("channel_not_found", channel_id=channel_id)
            raise ValueError(f"Channel {channel_id} not found")
        except Exception as e:
            self.logger.error("channel_scrape_failed", channel_id=channel_id, error=str(e))
            raise

    async def _get_guild_info(self, guild_id: str) -> Dict[str, Any]:
        """Get Discord server (guild) information.

        Args:
            guild_id: Discord guild ID

        Returns:
            Guild info dictionary
        """
        try:
            guild = self.client.get_guild(int(guild_id))
            if not guild:
                guild = await self.client.fetch_guild(int(guild_id))

            return {
                "id": str(guild.id),
                "name": guild.name,
                "description": guild.description,
                "member_count": guild.member_count,
                "created_at": guild.created_at.isoformat(),
                "owner_id": str(guild.owner_id),
                "icon_url": str(guild.icon.url) if guild.icon else None,
                "banner_url": str(guild.banner.url) if guild.banner else None,
                "text_channels_count": len(guild.text_channels),
                "voice_channels_count": len(guild.voice_channels),
                "roles_count": len(guild.roles),
            }

        except discord.Forbidden:
            self.logger.error("guild_access_forbidden", guild_id=guild_id)
            raise ValueError(f"Bot lacks permission to access guild {guild_id}")
        except discord.NotFound:
            self.logger.error("guild_not_found", guild_id=guild_id)
            raise ValueError(f"Guild {guild_id} not found")

    async def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get Discord user information.

        Args:
            user_id: Discord user ID

        Returns:
            User info dictionary
        """
        try:
            user = self.client.get_user(int(user_id))
            if not user:
                user = await self.client.fetch_user(int(user_id))

            return {
                "id": str(user.id),
                "name": user.name,
                "discriminator": user.discriminator,
                "bot": user.bot,
                "system": user.system,
                "created_at": user.created_at.isoformat(),
                "avatar_url": str(user.avatar.url) if user.avatar else None,
                "banner_url": str(user.banner.url) if user.banner else None,
            }

        except discord.NotFound:
            self.logger.error("user_not_found", user_id=user_id)
            raise ValueError(f"User {user_id} not found")

    async def _get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get Discord channel information.

        Args:
            channel_id: Discord channel ID

        Returns:
            Channel info dictionary
        """
        try:
            channel = self.client.get_channel(int(channel_id))
            if not channel:
                channel = await self.client.fetch_channel(int(channel_id))

            base_info = {
                "id": str(channel.id),
                "name": channel.name,
                "type": str(channel.type),
                "created_at": channel.created_at.isoformat(),
            }

            # Add text channel specific info (duck typing)
            if hasattr(channel, 'topic'):
                base_info.update({
                    "topic": channel.topic,
                    "nsfw": channel.nsfw,
                    "slowmode_delay": channel.slowmode_delay,
                    "guild_id": str(channel.guild.id),
                })

            return base_info

        except discord.Forbidden:
            self.logger.error("channel_access_forbidden", channel_id=channel_id)
            raise ValueError(f"Bot lacks permission to access channel {channel_id}")
        except discord.NotFound:
            self.logger.error("channel_not_found", channel_id=channel_id)
            raise ValueError(f"Channel {channel_id} not found")

    async def get_status(self) -> Dict[str, Any]:
        """Get scraper status and statistics.

        Returns:
            Status dictionary with metrics
        """
        status = await self.health_check()

        status.update({
            "total_scrapes": self.total_scrapes,
            "total_messages": self.total_messages,
            "total_guilds": self.total_guilds,
            "client_ready": self._client_ready,
            "connected_user": str(self.client.user) if self.client and self.client.user else None,
        })

        return status

    async def close(self):
        """Close Discord client connection."""
        if self.client and not self.client.is_closed():
            await self.client.close()
            self.logger.info("discord_client_closed")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"DiscordScraperRefactored(scrapes={self.total_scrapes}, "
            f"messages={self.total_messages}, "
            f"connected={self._client_ready})"
        )
