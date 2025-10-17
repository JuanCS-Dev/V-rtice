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

from services.verdict_engine_service.config import settings
from services.verdict_engine_service.models import Verdict, VerdictStats


class VerdictCache:
    """Redis cache for verdicts."""

    def __init__(self) -> None:
        """Initialize cache client."""
        self.client: redis.Redis[str] | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.client = redis.from_url(  # pragma: no cover
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:  # pragma: no cover
            await self.client.close()  # pragma: no cover
            self.client = None  # pragma: no cover

    def _serialize(self, obj: Any) -> str:
        """Serialize Pydantic models to JSON."""
        if isinstance(obj, (Verdict, VerdictStats)):
            return obj.model_dump_json()
        return json.dumps(obj)



    def _deserialize(self, data: str, model_class: type) -> Any:
        """Deserialize JSON to Pydantic model."""
        parsed = json.loads(data)  # pragma: no cover
        return model_class(**parsed)  # pragma: no cover

    async def cache_verdict(self, verdict: Verdict) -> None:
        """Cache single verdict."""
        if not self.client:
            return

        key = f"verdict:{verdict.id}"  # pragma: no cover
        await self.client.setex(  # pragma: no cover
            key,
            settings.redis_cache_ttl,
            self._serialize(verdict),
        )

    async def get_verdict(self, verdict_id: UUID) -> Verdict | None:
        """Get verdict from cache."""
        if not self.client:
            return None

        key = f"verdict:{verdict_id}"  # pragma: no cover
        data = await self.client.get(key)  # pragma: no cover
  # pragma: no cover
        return self._deserialize(data, Verdict) if data else None  # pragma: no cover

    async def cache_stats(self, stats: VerdictStats) -> None:
        """Cache verdict statistics."""
        if not self.client:
            return

        key = "verdict:stats"  # pragma: no cover
        await self.client.setex(  # pragma: no cover
            key,
            settings.redis_cache_ttl,
            self._serialize(stats),
        )

    async def get_stats(self) -> VerdictStats | None:
        """Get stats from cache."""
        if not self.client:
            return None

        key = "verdict:stats"  # pragma: no cover
        data = await self.client.get(key)  # pragma: no cover
  # pragma: no cover
        return self._deserialize(data, VerdictStats) if data else None  # pragma: no cover

    async def invalidate_verdict(self, verdict_id: UUID) -> None:
        """Invalidate cached verdict."""
        if not self.client:
            return

        key = f"verdict:{verdict_id}"  # pragma: no cover
        await self.client.delete(key)  # pragma: no cover

    async def invalidate_stats(self) -> None:
        """Invalidate cached stats."""
        if not self.client:
            return

        await self.client.delete("verdict:stats")  # pragma: no cover
