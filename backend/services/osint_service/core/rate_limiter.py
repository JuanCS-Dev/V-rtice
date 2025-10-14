"""Maximus OSINT Service - Rate Limiter (Token Bucket Algorithm).

This module implements a Token Bucket rate limiter for controlling request rates
to external APIs. It prevents API rate limit violations and ensures fair resource
usage across multiple concurrent operations.

Token Bucket Algorithm:
    - Bucket holds tokens representing allowed requests
    - Tokens are refilled at a constant rate
    - Each request consumes one token
    - If no tokens available, request waits until refill

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, no mocks
    - Article IV (Antifragility): Prevents cascading failures from rate limit violations

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 1.0.0
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for async operations.

    Implements the token bucket algorithm to control request rates. Tokens are
    refilled continuously at a configured rate. Each request consumes one token.
    If no tokens are available, the request waits until tokens are refilled.

    Thread-safe for async operations via asyncio.Lock.

    Usage Example:
        rate_limiter = RateLimiter(rate=2.0)  # 2 requests per second

        for i in range(10):
            await rate_limiter.acquire()
            # Make API request (guaranteed not to exceed 2 req/sec)
            print(f"Request {i}")

    Attributes:
        rate: Tokens refilled per second (e.g., 1.0 = 1 request/sec)
        tokens: Current token count (float for fractional tokens)
        last_update: Timestamp of last token refill
        lock: Async lock for thread-safe operations
    """

    def __init__(self, rate: float):
        """Initialize RateLimiter with token refill rate.

        Args:
            rate: Maximum requests per second (e.g., 1.0 = 1 req/sec, 0.5 = 1 req/2 sec)

        Raises:
            ValueError: If rate <= 0
        """
        if rate <= 0:
            raise ValueError(f"Rate must be positive, got {rate}")

        self.rate = rate
        self.tokens = rate  # Start with full bucket
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire one token, waiting if necessary.

        This method blocks until a token is available. It:
        1. Locks to ensure thread-safety
        2. Refills tokens based on elapsed time
        3. If token available, consumes it and returns immediately
        4. If no tokens, calculates wait time and sleeps

        Returns:
            None (blocks until token acquired)
        """
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(
                self.rate,  # Max bucket capacity
                self.tokens + (elapsed * self.rate),  # Add refilled tokens
            )
            self.last_update = now

            # If tokens available, consume and return immediately
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return

            # No tokens: calculate wait time until next token available
            wait_time = (1.0 - self.tokens) / self.rate
            await asyncio.sleep(wait_time)

            # After waiting, consume token
            self.tokens = 0.0
            self.last_update = time.monotonic()

    async def try_acquire(self) -> bool:
        """Try to acquire token without blocking.

        Non-blocking version of acquire(). Returns immediately.

        Returns:
            True if token acquired, False if no tokens available
        """
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Refill tokens
            self.tokens = min(
                self.rate,
                self.tokens + (elapsed * self.rate),
            )
            self.last_update = now

            # Check if token available
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True

            return False

    async def get_available_tokens(self) -> float:
        """Get current number of available tokens.

        Returns:
            Number of available tokens (float for fractional tokens)
        """
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Calculate current tokens (without consuming)
            current_tokens = min(
                self.rate,
                self.tokens + (elapsed * self.rate),
            )
            return current_tokens

    def reset(self) -> None:
        """Reset rate limiter to full bucket.

        Useful for testing or manual intervention.
        """
        self.tokens = self.rate
        self.last_update = time.monotonic()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"RateLimiter(rate={self.rate}, "
            f"tokens={self.tokens:.2f}, "
            f"last_update={self.last_update})"
        )
