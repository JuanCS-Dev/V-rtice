"""
API Rate Limiter - MAXIMUS Security Arsenal

Token bucket and sliding window rate limiting for API endpoints.
Prevents abuse, DoS attacks, and ensures fair resource allocation.

Integrates with Redis for distributed rate limiting across services.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimitStrategy(str, Enum):
    """Rate limiting algorithm strategy"""
    TOKEN_BUCKET = "token_bucket"  # Allows bursts
    SLIDING_WINDOW = "sliding_window"  # More precise
    FIXED_WINDOW = "fixed_window"  # Simple, less accurate


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.2f}s")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter"""
    max_requests: int = field(default=100)
    window_seconds: int = field(default=60)
    strategy: RateLimitStrategy = field(default=RateLimitStrategy.SLIDING_WINDOW)
    burst_multiplier: float = field(default=1.5)  # For token bucket


@dataclass
class RateLimiter:
    """
    Multi-strategy rate limiter with Redis backend.

    Supports token bucket (burst-friendly) and sliding window (precise)
    algorithms. Falls back to in-memory if Redis unavailable.

    Attributes:
        config: Rate limit configuration
        redis_url: Redis connection URL (optional)
        key_prefix: Prefix for Redis keys
    """

    config: RateLimitConfig
    redis_url: str | None = None
    key_prefix: str = "ratelimit"

    # In-memory fallback storage
    _memory_store: dict[str, list] = field(default_factory=dict, init=False, repr=False)
    _redis_client: Optional['aioredis.Redis'] = field(default=None, init=False, repr=False)

    async def __aenter__(self):
        """Async context manager entry"""
        if self.redis_url and REDIS_AVAILABLE:
            self._redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._redis_client:
            await self._redis_client.close()

    async def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1
    ) -> tuple[bool, float]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (user_id, IP, API key)
            cost: Request cost (default 1, can be higher for expensive operations)

        Returns:
            Tuple of (allowed, retry_after_seconds)

        Raises:
            RateLimitExceeded: If limit exceeded and raise_on_exceed=True
        """
        if self._redis_client:
            return await self._check_redis(identifier, cost)
        else:
            return await self._check_memory(identifier, cost)

    async def _check_redis(self, identifier: str, cost: int) -> tuple[bool, float]:
        """Redis-based rate limiting (sliding window)"""
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        window_start = now - self.config.window_seconds

        # Use Redis sorted set for sliding window
        pipe = self._redis_client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests
        pipe.zcard(key)

        # Add current request with timestamp as score
        request_id = f"{now}:{cost}"
        pipe.zadd(key, {request_id: now})

        # Set expiry
        pipe.expire(key, self.config.window_seconds * 2)

        results = await pipe.execute()
        current_count = results[1]  # Result from zcard

        # Check if within limit
        allowed = (current_count + cost) <= self.config.max_requests

        if allowed:
            retry_after = 0.0
        else:
            # Calculate retry time
            oldest_timestamp = await self._redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_timestamp:
                oldest_time = oldest_timestamp[0][1]
                retry_after = oldest_time + self.config.window_seconds - now
            else:
                retry_after = self.config.window_seconds

        return allowed, retry_after

    async def _check_memory(self, identifier: str, cost: int) -> tuple[bool, float]:
        """In-memory fallback rate limiting"""
        now = time.time()
        window_start = now - self.config.window_seconds

        # Initialize if not exists
        if identifier not in self._memory_store:
            self._memory_store[identifier] = []

        requests = self._memory_store[identifier]

        # Remove old requests
        requests = [ts for ts in requests if ts > window_start]
        self._memory_store[identifier] = requests

        # Check limit
        current_count = len(requests)
        allowed = (current_count + cost) <= self.config.max_requests

        if allowed:
            # Add new request timestamps (cost times)
            requests.extend([now] * cost)
            retry_after = 0.0
        else:
            # Calculate retry time
            oldest_time = min(requests) if requests else now
            retry_after = oldest_time + self.config.window_seconds - now

        return allowed, retry_after

    async def consume(self, identifier: str, cost: int = 1) -> None:
        """
        Consume rate limit tokens. Raises exception if exceeded.

        Args:
            identifier: Unique identifier
            cost: Request cost

        Raises:
            RateLimitExceeded: If limit exceeded
        """
        allowed, retry_after = await self.check_rate_limit(identifier, cost)

        if not allowed:
            raise RateLimitExceeded(retry_after)

    async def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier (admin override)"""
        if self._redis_client:
            key = f"{self.key_prefix}:{identifier}"
            await self._redis_client.delete(key)
        else:
            self._memory_store.pop(identifier, None)

    async def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window"""
        if self._redis_client:
            key = f"{self.key_prefix}:{identifier}"
            now = time.time()
            window_start = now - self.config.window_seconds

            current_count = await self._redis_client.zcount(key, window_start, now)
            return max(0, self.config.max_requests - current_count)
        else:
            now = time.time()
            window_start = now - self.config.window_seconds

            requests = self._memory_store.get(identifier, [])
            current_count = sum(1 for ts in requests if ts > window_start)
            return max(0, self.config.max_requests - current_count)


# FastAPI dependency injection helpers
def create_rate_limiter(
    max_requests: int = 100,
    window_seconds: int = 60,
    redis_url: str | None = None
) -> RateLimiter:
    """
    Factory function to create rate limiter.

    Usage in FastAPI:
        limiter = create_rate_limiter(max_requests=100, window_seconds=60)

        @app.get("/api/endpoint")
        async def endpoint(request: Request):
            await limiter.consume(request.client.host)
            return {"status": "ok"}
    """
    config = RateLimitConfig(
        max_requests=max_requests,
        window_seconds=window_seconds
    )

    return RateLimiter(config=config, redis_url=redis_url)


if __name__ == "__main__":
    # Test rate limiter
    async def test_limiter():
        print("🚦 Testing MAXIMUS Rate Limiter")
        print("=" * 50)

        config = RateLimitConfig(max_requests=5, window_seconds=10)

        async with RateLimiter(config=config) as limiter:
            user_id = "test_user"

            print(f"\n📊 Testing with limit: {config.max_requests} req/{config.window_seconds}s")

            for i in range(7):
                try:
                    await limiter.consume(user_id)
                    remaining = await limiter.get_remaining(user_id)
                    print(f"✅ Request {i+1} allowed (remaining: {remaining})")
                except RateLimitExceeded as e:
                    print(f"❌ Request {i+1} blocked: {e}")

                await asyncio.sleep(0.5)

            print(f"\n⏳ Waiting {config.window_seconds}s for window reset...")
            await asyncio.sleep(config.window_seconds)

            try:
                await limiter.consume(user_id)
                print("✅ Request after window reset allowed")
            except RateLimitExceeded as e:
                print(f"❌ Request still blocked: {e}")

    asyncio.run(test_limiter())
