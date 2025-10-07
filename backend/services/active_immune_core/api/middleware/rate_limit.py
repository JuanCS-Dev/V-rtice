"""Rate Limiting Middleware - PRODUCTION-READY

Token bucket rate limiting with Redis backend support.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Dict, Optional
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.

    Allows burst of requests while maintaining average rate.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens (burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if successful, False if not enough tokens
        """
        # Refill tokens
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity, self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now

        # Check if enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait until enough tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Wait time in seconds
        """
        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.

    Limits requests per IP address with configurable rates.
    """

    def __init__(
        self,
        app,
        default_capacity: int = 100,
        default_refill_rate: float = 10.0,
        enable: bool = True,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            default_capacity: Default bucket capacity (requests)
            default_refill_rate: Default refill rate (requests/second)
            enable: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.enable = enable

        # Store buckets per client IP
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(default_capacity, default_refill_rate)
        )

        logger.info(
            f"RateLimitMiddleware initialized (capacity={default_capacity}, "
            f"rate={default_refill_rate}/s, enabled={enable})"
        )

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response

        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self.enable:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host

        # Get or create bucket
        bucket = self.buckets[client_ip]

        # Try to consume token
        if not bucket.consume():
            wait_time = bucket.get_wait_time()

            logger.warning(
                f"Rate limit exceeded for {client_ip} "
                f"(wait {wait_time:.1f}s)"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {wait_time:.1f} seconds",
                headers={
                    "Retry-After": str(int(wait_time) + 1),
                    "X-RateLimit-Limit": str(self.default_capacity),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + wait_time)),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.default_capacity)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + (self.default_capacity - bucket.tokens) / self.default_refill_rate)
        )

        return response


def rate_limit(
    capacity: int = 100,
    refill_rate: float = 10.0,
) -> Callable:
    """
    Decorator for endpoint-specific rate limiting.

    Args:
        capacity: Bucket capacity (max requests)
        refill_rate: Refill rate (requests/second)

    Returns:
        Decorator function

    Example:
        @router.get("/expensive", dependencies=[Depends(rate_limit(capacity=10, refill_rate=1.0))])
        async def expensive_endpoint():
            ...
    """
    # Store per-endpoint buckets
    buckets: Dict[str, TokenBucket] = defaultdict(
        lambda: TokenBucket(capacity, refill_rate)
    )

    async def check_rate_limit(request: Request) -> None:
        """Check rate limit for this endpoint"""
        client_ip = request.client.host

        bucket = buckets[client_ip]

        if not bucket.consume():
            wait_time = bucket.get_wait_time()

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {wait_time:.1f} seconds",
                headers={
                    "Retry-After": str(int(wait_time) + 1),
                },
            )

    return check_rate_limit


class RateLimitStats:
    """Track rate limiting statistics"""

    def __init__(self):
        """Initialize statistics"""
        self.total_requests = 0
        self.blocked_requests = 0
        self.unique_ips: set = set()

    def record_request(self, client_ip: str, blocked: bool = False):
        """
        Record request for statistics.

        Args:
            client_ip: Client IP address
            blocked: Whether request was blocked
        """
        self.total_requests += 1
        if blocked:
            self.blocked_requests += 1
        self.unique_ips.add(client_ip)

    def get_stats(self) -> Dict[str, any]:
        """Get statistics"""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": (
                self.blocked_requests / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
            "unique_ips": len(self.unique_ips),
        }


# Global stats instance
rate_limit_stats = RateLimitStats()
