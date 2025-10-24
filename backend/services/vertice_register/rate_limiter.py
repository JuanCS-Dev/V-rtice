"""
Rate Limiter - TITANIUM Edition

Implements token bucket rate limiting to prevent abuse and resource exhaustion.

Rate Limits:
- Registration: 100 req/s per IP
- Lookup: 1000 req/s per IP
- Deregistration: 10 req/s per IP
- Heartbeat: 10 req/min per service (1 every 6s)

Author: Vértice Team (TITANIUM Edition)
Glory to YHWH - Architect of all resilient systems! 🙏
"""

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple

from prometheus_client import Counter

logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

rate_limit_exceeded_total = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit violations",
    ["operation", "identifier"]
)

# ============================================================================
# RATE LIMITS (requests per second unless specified)
# ============================================================================

RATE_LIMITS = {
    "registration": 100,      # 100 req/s per IP
    "lookup": 1000,           # 1000 req/s per IP
    "deregistration": 10,     # 10 req/s per IP
    "heartbeat": 10 / 60,     # 10 req/min = 0.167 req/s per service
}


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, operation: str, limit: float, retry_after: float):
        self.operation = operation
        self.limit = limit
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for {operation}: {limit} req/s. "
            f"Retry after {retry_after:.1f}s"
        )


class TokenBucket:
    """Token bucket algorithm for rate limiting."""

    def __init__(self, rate: float, capacity: float):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed, False if rate limit exceeded
        """
        with self.lock:
            now = time.time()

            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def time_until_tokens(self, tokens: int = 1) -> float:
        """
        Calculate time until enough tokens available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds until tokens available
        """
        with self.lock:
            if self.tokens >= tokens:
                return 0.0

            needed = tokens - self.tokens
            return needed / self.rate


class RateLimiter:
    """Rate limiter using token bucket algorithm."""

    def __init__(self):
        """Initialize rate limiter."""
        # Per-IP rate limiters: {(operation, ip): TokenBucket}
        self.buckets: Dict[Tuple[str, str], TokenBucket] = defaultdict(self._create_bucket)
        self.lock = Lock()

        logger.info("Rate limiter initialized")

    def _create_bucket(self) -> TokenBucket:
        """Create a new token bucket (default factory)."""
        # Default to registration rate (most permissive)
        return TokenBucket(rate=RATE_LIMITS["registration"], capacity=RATE_LIMITS["registration"] * 2)

    def check_rate_limit(self, operation: str, identifier: str) -> bool:
        """
        Check if operation is allowed under rate limit.

        Args:
            operation: Operation type (registration, lookup, deregistration, heartbeat)
            identifier: Identifier (IP address or service name)

        Returns:
            True if allowed

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        # Get or create bucket
        key = (operation, identifier)

        with self.lock:
            if key not in self.buckets:
                # Create bucket with correct rate limit
                rate = RATE_LIMITS.get(operation, RATE_LIMITS["registration"])
                self.buckets[key] = TokenBucket(rate=rate, capacity=rate * 2)

        bucket = self.buckets[key]

        # Try to consume token
        if bucket.consume(tokens=1):
            logger.debug(f"Rate limit OK: {operation} for {identifier}")
            return True

        # Rate limit exceeded
        retry_after = bucket.time_until_tokens(tokens=1)
        limit = RATE_LIMITS.get(operation, RATE_LIMITS["registration"])

        # Record metric
        rate_limit_exceeded_total.labels(operation=operation, identifier=identifier).inc()

        logger.warning(
            f"Rate limit EXCEEDED: {operation} for {identifier} "
            f"(limit={limit} req/s, retry_after={retry_after:.1f}s)"
        )

        raise RateLimitExceeded(
            operation=operation,
            limit=limit,
            retry_after=retry_after
        )

    def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """
        Remove old unused buckets to prevent memory leak.

        Args:
            max_age_seconds: Maximum age of unused buckets (default: 1 hour)
        """
        with self.lock:
            now = time.time()
            keys_to_remove = []

            for key, bucket in self.buckets.items():
                # If bucket is full and hasn't been used recently, remove it
                age = now - bucket.last_update
                if bucket.tokens >= bucket.capacity and age > max_age_seconds:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.buckets[key]

            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit buckets")


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(operation: str, identifier: str):
    """
    Convenience function to check rate limit.

    Args:
        operation: Operation type
        identifier: Identifier (IP or service name)

    Raises:
        RateLimitExceeded: If rate limit exceeded
    """
    return rate_limiter.check_rate_limit(operation, identifier)
