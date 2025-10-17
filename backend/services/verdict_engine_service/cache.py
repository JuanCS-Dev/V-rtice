"""Redis cache for verdicts.

Provides fast access to recent verdicts and stats.
TTL-based expiration, JSON serialization.
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from config import settings
from models import Verdict, VerdictStats


class VerdictCache:
    """Redis cache for verdicts."""

    def __init__(self) -> None:
        """Initialize cache client."""
        self.client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None

    def _serialize(self, obj: Any) -> str:
        """Serialize Pydantic models to JSON."""
        if isinstance(obj, Verdict | VerdictStats):
            data = obj.model_dump(mode="json")
            return json.dumps(self._encode_special_types(data))
        return json.dumps(obj)

    def _encode_special_types(self, data: Any) -> Any:
        """Encode special types for JSON."""
        if isinstance(data, dict):
            return {k: self._encode_special_types(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._encode_special_types(item) for item in data]
        if isinstance(data, UUID | Decimal):
            return str(data)
        if isinstance(data, datetime):
            return data.isoformat()
        return data

    def _deserialize(self, data: str, model_class: type) -> Any:
        """Deserialize JSON to Pydantic model."""
        parsed = json.loads(data)
        return model_class(**parsed)

    async def cache_verdict(self, verdict: Verdict) -> None:
        """Cache single verdict."""
        if not self.client:
            return

        key = f"verdict:{verdict.id}"
        await self.client.setex(
            key,
            settings.redis_cache_ttl,
            self._serialize(verdict),
        )

    async def get_verdict(self, verdict_id: UUID) -> Verdict | None:
        """Get verdict from cache."""
        if not self.client:
            return None

        key = f"verdict:{verdict_id}"
        data = await self.client.get(key)

        return self._deserialize(data, Verdict) if data else None

    async def cache_stats(self, stats: VerdictStats) -> None:
        """Cache verdict statistics."""
        if not self.client:
            return

        key = "verdict:stats"
        await self.client.setex(
            key,
            settings.redis_cache_ttl,
            self._serialize(stats),
        )

    async def get_stats(self) -> VerdictStats | None:
        """Get stats from cache."""
        if not self.client:
            return None

        key = "verdict:stats"
        data = await self.client.get(key)

        return self._deserialize(data, VerdictStats) if data else None

    async def invalidate_verdict(self, verdict_id: UUID) -> None:
        """Invalidate cached verdict."""
        if not self.client:
            return

        key = f"verdict:{verdict_id}"
        await self.client.delete(key)

    async def invalidate_stats(self) -> None:
        """Invalidate cached stats."""
        if not self.client:
            return

        await self.client.delete("verdict:stats")
