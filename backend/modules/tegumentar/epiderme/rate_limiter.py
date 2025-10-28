"""Distributed rate limiting for the epiderme layer."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from redis import exceptions as redis_exceptions
import redis.asyncio as aioredis

from ..config import TegumentarSettings

logger = logging.getLogger(__name__)


_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2]) -- tokens per second
local tokens_to_take = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local bucket = redis.call("HMGET", key, "tokens", "timestamp")
local current_tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if not current_tokens or not last_refill then
  current_tokens = capacity
  last_refill = now
end

local delta = math.max(0, now - last_refill)
local refill = delta * refill_rate
current_tokens = math.min(capacity, current_tokens + refill)
last_refill = now

if current_tokens < tokens_to_take then
  redis.call("HMSET", key, "tokens", current_tokens, "timestamp", last_refill)
  redis.call("EXPIRE", key, math.ceil(capacity / refill_rate))
  return 0
end

current_tokens = current_tokens - tokens_to_take
redis.call("HMSET", key, "tokens", current_tokens, "timestamp", last_refill)
redis.call("EXPIRE", key, math.ceil(capacity / refill_rate))
return 1
"""


class DistributedRateLimiter:
    """Token bucket rate limiter backed by Redis."""

    def __init__(self, settings: TegumentarSettings):
        self._settings = settings
        self._redis: Optional[aioredis.Redis] = None
        self._script_sha: Optional[str] = None
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        """Initialise Redis connection and register Lua script."""

        if self._redis is not None:
            return

        self._redis = aioredis.from_url(
            self._settings.redis_url, encoding="utf-8", decode_responses=True
        )
        self._script_sha = await self._redis.script_load(_TOKEN_BUCKET_LUA)
        logger.info("Rate limiter initialised with Redis %s", self._settings.redis_url)

    async def shutdown(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._script_sha = None

    async def allow(self, ip_address: str, tokens: int = 1) -> bool:
        """Return True if the request can proceed, False if rate limited."""

        if self._redis is None or self._script_sha is None:
            raise RuntimeError("Rate limiter not initialised. Call startup() first.")

        now = time.time()
        try:
            allowed = await self._redis.evalsha(
                self._script_sha,
                1,
                f"tegumentar:rate:{ip_address}",
                self._settings.rate_limit_capacity,
                self._settings.rate_limit_refill_per_second,
                tokens,
                now,
            )
            return bool(allowed)
        except redis_exceptions.NoScriptError:
            # Script evicted, reload and retry once.
            async with self._lock:
                self._script_sha = await self._redis.script_load(_TOKEN_BUCKET_LUA)
            return await self.allow(ip_address, tokens)


__all__ = ["DistributedRateLimiter"]
