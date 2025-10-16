"""Redis client for caching and pub/sub."""

import json
from typing import Any

from redis.asyncio import Redis
from vertice_core import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._client: Redis = Redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        value = await self._client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self, key: str, value: Any, ttl: int | None = None
    ) -> None:
        """Set value in cache."""
        await self._client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self._client.delete(key)

    async def close(self) -> None:  # pragma: no cover
        """Close connection."""
        await self._client.aclose()


def create_redis_client(redis_url: str) -> RedisClient:
    """Create Redis client."""
    return RedisClient(redis_url)
