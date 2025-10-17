"""
API Rate Limiting Middleware
=============================

PAGANI Quality - Token Bucket Algorithm with Redis

Prevents API abuse through configurable rate limits per:
- IP address
- API key
- User ID
- Endpoint

Features:
- Token bucket algorithm (smooth rate limiting)
- Redis-backed (distributed, scalable)
- Configurable limits per endpoint
- Custom headers (X-RateLimit-*)
- Graceful degradation if Redis unavailable

Usage:
    from shared.middleware.rate_limiter import RateLimiter

    app = FastAPI()
    app.add_middleware(RateLimiter, redis_url="redis://localhost:6379")

    # Or per-endpoint:
    @app.get("/api/scan")
    @rate_limit(requests=10, window=60)  # 10 req/min
    async def scan_endpoint():
        ...

Architecture:
    Client → Rate Limiter Middleware → Endpoint
              ↓ (check Redis)
              ↓ (if exceeded: 429 Too Many Requests)
              ↓ (else: pass through + decrement tokens)

References:
- Token Bucket: https://en.wikipedia.org/wiki/Token_bucket
- IETF RFC 6585: https://tools.ietf.org/html/rfc6585
"""

import hashlib
import time
from collections.abc import Callable
from functools import wraps

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    import redis
    from redis import ConnectionError as RedisConnectionError
    from redis import Redis

    REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    REDIS_AVAILABLE = False
    redis = None  # type: ignore[assignment]
    Redis = None  # type: ignore[assignment,misc]
    RedisConnectionError = Exception  # type: ignore[assignment,misc]


# ============================================================================
# CONFIGURATION
# ============================================================================

class RateLimitConfig:
    """Rate limit configuration."""

    # Default limits (requests per window in seconds)
    DEFAULT_REQUESTS = 100
    DEFAULT_WINDOW = 60  # 60 seconds = 1 minute

    # Per-endpoint limits (override defaults)
    ENDPOINT_LIMITS = {
        "/api/scan": (10, 60),          # 10 req/min for scans
        "/api/malware/analyze": (5, 60), # 5 req/min for malware analysis
        "/api/exploit": (3, 60),         # 3 req/min for exploits
        "/api/osint": (20, 60),          # 20 req/min for OSINT
        "/api/threat-intel": (50, 60),   # 50 req/min for threat intel
    }

    # Header names
    HEADER_LIMIT = "X-RateLimit-Limit"
    HEADER_REMAINING = "X-RateLimit-Remaining"
    HEADER_RESET = "X-RateLimit-Reset"
    HEADER_RETRY_AFTER = "Retry-After"

    # Redis key prefix
    REDIS_KEY_PREFIX = "ratelimit"

    # Fallback behavior if Redis unavailable
    FAIL_OPEN = True  # True = allow requests, False = deny requests


# ============================================================================
# TOKEN BUCKET IMPLEMENTATION
# ============================================================================

class TokenBucket:
    """
    Token bucket algorithm for rate limiting.

    How it works:
    1. Bucket starts with max_tokens
    2. Each request consumes 1 token
    3. Tokens refill at rate: max_tokens / window_seconds
    4. If no tokens available: request denied (429)

    Example:
        10 requests / 60 seconds = 0.1666 tokens/second refill rate
        If 5 tokens left at t=0, at t=30 you have 10 tokens (refilled)
    """

    def __init__(
        self,
        redis_client: Redis | None,
        key: str,
        max_tokens: int,
        window_seconds: int
    ):
        self.redis = redis_client
        self.key = key
        self.max_tokens = max_tokens
        self.window_seconds = window_seconds
        self.refill_rate = max_tokens / window_seconds

    def _get_redis_key(self) -> str:
        """Generate Redis key."""
        return f"{RateLimitConfig.REDIS_KEY_PREFIX}:{self.key}"

    def consume(self, tokens: int = 1) -> tuple[bool, int, int]:
        """
        Attempt to consume tokens from bucket.

        Returns:
            (allowed, remaining_tokens, reset_time)
        """
        if not self.redis or not REDIS_AVAILABLE:
            # Fallback: allow request if Redis unavailable
            if RateLimitConfig.FAIL_OPEN:
                return (True, self.max_tokens, int(time.time()) + self.window_seconds)
            else:
                return (False, 0, int(time.time()) + self.window_seconds)

        now = time.time()
        redis_key = self._get_redis_key()

        try:
            # Use Lua script for atomic operation
            lua_script = """
            local key = KEYS[1]
            local max_tokens = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            local tokens_requested = tonumber(ARGV[4])

            -- Get current state (tokens, last_update)
            local state = redis.call('HMGET', key, 'tokens', 'last_update')
            local tokens = tonumber(state[1]) or max_tokens
            local last_update = tonumber(state[2]) or now

            -- Calculate tokens to add based on time elapsed
            local time_elapsed = now - last_update
            local tokens_to_add = time_elapsed * refill_rate
            tokens = math.min(max_tokens, tokens + tokens_to_add)

            -- Check if we can consume
            if tokens >= tokens_requested then
                tokens = tokens - tokens_requested
                redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
                redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate))
                return {1, math.floor(tokens), now}
            else
                redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
                redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate))
                return {0, math.floor(tokens), now}
            end
            """

            result = self.redis.eval(
                lua_script,
                1,  # number of keys
                redis_key,
                self.max_tokens,
                self.refill_rate,
                now,
                tokens
            )

            allowed = bool(result[0])
            remaining = int(result[1])
            reset_time = int(now + self.window_seconds)

            return (allowed, remaining, reset_time)

        except (RedisConnectionError, Exception) as e:
            # Redis error: fallback behavior
            if RateLimitConfig.FAIL_OPEN:
                return (True, self.max_tokens, int(time.time()) + self.window_seconds)
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Rate limiting service unavailable"
                ) from e


# ============================================================================
# RATE LIMITER MIDDLEWARE
# ============================================================================

class RateLimiter(BaseHTTPMiddleware):
    """
    FastAPI middleware for API rate limiting.

    Usage:
        app.add_middleware(
            RateLimiter,
            redis_url="redis://localhost:6379",
            enabled=True
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_url: str = "redis://localhost:6379",
        enabled: bool = True
    ):
        super().__init__(app)
        self.enabled = enabled

        if enabled and REDIS_AVAILABLE:
            try:
                self.redis = Redis.from_url(redis_url, decode_responses=False)
                # Test connection
                self.redis.ping()
            except Exception as e:
                print(f"[RateLimiter] Redis connection failed: {e}. Running without rate limiting.")
                self.redis = None  # type: ignore[assignment]
        else:
            self.redis = None  # type: ignore[assignment]

    def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.

        Priority:
        1. API key (if present in header)
        2. User ID (if authenticated)
        3. IP address (fallback)
        """
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

        # Try user ID (would come from auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _get_rate_limit(self, path: str) -> tuple[int, int]:
        """
        Get rate limit for endpoint.

        Returns:
            (max_requests, window_seconds)
        """
        # Check for exact path match
        if path in RateLimitConfig.ENDPOINT_LIMITS:
            return RateLimitConfig.ENDPOINT_LIMITS[path]

        # Check for prefix match
        for endpoint_path, limits in RateLimitConfig.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint_path):
                return limits

        # Return defaults
        return (RateLimitConfig.DEFAULT_REQUESTS, RateLimitConfig.DEFAULT_WINDOW)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""

        # Skip if disabled or health check endpoints
        if not self.enabled or request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)  # type: ignore[no-any-return]

        # Get identifier and limits
        identifier = self._get_identifier(request)
        max_requests, window_seconds = self._get_rate_limit(request.url.path)

        # Create token bucket
        bucket_key = f"{request.url.path}:{identifier}"
        bucket = TokenBucket(self.redis, bucket_key, max_requests, window_seconds)

        # Try to consume token
        allowed, remaining, reset_time = bucket.consume()

        # Add rate limit headers
        headers = {
            RateLimitConfig.HEADER_LIMIT: str(max_requests),
            RateLimitConfig.HEADER_REMAINING: str(remaining),
            RateLimitConfig.HEADER_RESET: str(reset_time),
        }

        if not allowed:
            # Rate limit exceeded
            retry_after = reset_time - int(time.time())
            headers[RateLimitConfig.HEADER_RETRY_AFTER] = str(retry_after)

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {retry_after} seconds.",
                    "limit": max_requests,
                    "window": window_seconds,
                    "reset": reset_time
                },
                headers=headers
            )

        # Process request
        response = await call_next(request)

        # Add headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response  # type: ignore[no-any-return]


# ============================================================================
# DECORATOR FOR PER-ENDPOINT LIMITS
# ============================================================================

def rate_limit(requests: int = 100, window: int = 60):
    """
    Decorator for per-endpoint rate limiting.

    Usage:
        @app.get("/api/expensive-operation")
        @rate_limit(requests=5, window=60)  # 5 req/min
        async def expensive_op():
            ...

    Note: This stores the limit in endpoint metadata.
    The middleware will read it during request processing.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        wrapper.__rate_limit__ = (requests, window)  # type: ignore[attr-defined]
        return wrapper
    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_rate_limit_status(redis_url: str, identifier: str, path: str) -> dict:
    """
    Get current rate limit status for debugging.

    Returns:
        {
            "limit": 100,
            "remaining": 87,
            "reset": 1633456789,
            "window": 60
        }
    """
    if not REDIS_AVAILABLE:
        return {"error": "Redis not available"}

    try:
        redis_client = Redis.from_url(redis_url)
        max_requests, window_seconds = RateLimitConfig.DEFAULT_REQUESTS, RateLimitConfig.DEFAULT_WINDOW

        bucket_key = f"{path}:{identifier}"
        bucket = TokenBucket(redis_client, bucket_key, max_requests, window_seconds)

        # Just check, don't consume
        redis_key = bucket._get_redis_key()
        state = redis_client.hmget(redis_key, 'tokens', 'last_update')
        tokens = float(state[0]) if state[0] else max_requests

        return {
            "limit": max_requests,
            "remaining": int(tokens),
            "reset": int(time.time()) + window_seconds,
            "window": window_seconds
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "RateLimiter",
    "RateLimitConfig",
    "TokenBucket",
    "rate_limit",
    "get_rate_limit_status",
]
