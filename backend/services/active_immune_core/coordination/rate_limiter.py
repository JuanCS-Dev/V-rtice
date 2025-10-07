"""Rate Limiter for Lymphnode Operations

Prevents resource exhaustion from excessive clonal expansion.

Based on Token Bucket algorithm with sliding window.

Authors: Juan + Claude
Date: 2025-10-07
"""

import asyncio
import time
from typing import Dict, Optional

from coordination.exceptions import LymphnodeRateLimitError


class RateLimiter:
    """
    Token bucket rate limiter for async operations.

    Limits:
    - Max rate (operations per second)
    - Max burst (max tokens in bucket)
    """

    def __init__(
        self,
        max_rate: float = 10.0,  # 10 ops/sec
        max_burst: int = 20,  # Max 20 tokens
        refill_interval: float = 0.1,  # Refill every 100ms
    ):
        """
        Initialize rate limiter.

        Args:
            max_rate: Maximum operations per second
            max_burst: Maximum burst size (token bucket capacity)
            refill_interval: Interval to refill tokens (seconds)
        """
        self.max_rate = max_rate
        self.max_burst = max_burst
        self.refill_interval = refill_interval

        # Token bucket state
        self._tokens = float(max_burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

        # Statistics
        self.total_requests = 0
        self.total_accepted = 0
        self.total_rejected = 0

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if acquired, False if rate limited

        Raises:
            ValueError: If tokens < 1
        """
        if tokens < 1:
            raise ValueError("tokens must be >= 1")

        if tokens > self.max_burst:
            raise ValueError(f"tokens ({tokens}) exceeds max_burst ({self.max_burst})")

        async with self._lock:
            self.total_requests += 1

            # Refill tokens based on elapsed time
            now = time.monotonic()
            elapsed = now - self._last_refill

            if elapsed > 0:
                # Calculate tokens to add
                tokens_to_add = elapsed * self.max_rate
                self._tokens = min(self.max_burst, self._tokens + tokens_to_add)
                self._last_refill = now

            # Check if enough tokens available
            if self._tokens >= tokens:
                self._tokens -= tokens
                self.total_accepted += 1
                return True
            else:
                self.total_rejected += 1
                return False

    async def acquire_or_raise(self, tokens: int = 1) -> None:
        """
        Acquire tokens or raise exception.

        Args:
            tokens: Number of tokens to acquire

        Raises:
            LymphnodeRateLimitError: If rate limited
        """
        if not await self.acquire(tokens):
            raise LymphnodeRateLimitError(
                f"Rate limit exceeded: {self.max_rate} ops/sec "
                f"(burst={self.max_burst}, requested={tokens})"
            )

    async def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait for tokens to become available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum wait time (seconds), None = wait forever

        Returns:
            True if acquired, False if timeout

        Raises:
            ValueError: If tokens > max_burst
        """
        if tokens > self.max_burst:
            raise ValueError(f"tokens ({tokens}) exceeds max_burst ({self.max_burst})")

        start_time = time.monotonic()

        while True:
            if await self.acquire(tokens):
                return True

            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    return False

            # Wait a bit before retrying (adaptive backoff)
            await asyncio.sleep(self.refill_interval)

    def get_available_tokens(self) -> float:
        """Get current available tokens (approximate, no lock)"""
        return self._tokens

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        acceptance_rate = (
            self.total_accepted / self.total_requests
            if self.total_requests > 0
            else 0.0
        )

        return {
            "max_rate": self.max_rate,
            "max_burst": self.max_burst,
            "available_tokens": self._tokens,
            "total_requests": self.total_requests,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "acceptance_rate": acceptance_rate,
        }

    def reset(self) -> None:
        """Reset rate limiter state (for testing)"""
        self._tokens = float(self.max_burst)
        self._last_refill = time.monotonic()
        self.total_requests = 0
        self.total_accepted = 0
        self.total_rejected = 0


class ClonalExpansionRateLimiter:
    """
    Specialized rate limiter for clonal expansion.

    Tracks:
    - Total agents created per minute
    - Per-specialization limits
    - Resource exhaustion prevention
    """

    def __init__(
        self,
        max_clones_per_minute: int = 200,
        max_per_specialization: int = 50,
        max_total_agents: int = 1000,
    ):
        """
        Initialize clonal expansion rate limiter.

        Args:
            max_clones_per_minute: Max clones created per minute globally
            max_per_specialization: Max clones per specialization type
            max_total_agents: Max total agents (resource exhaustion limit)
        """
        # Global rate limiter (200 clones/min = ~3.3/sec)
        self.global_limiter = RateLimiter(
            max_rate=max_clones_per_minute / 60.0,
            max_burst=max_clones_per_minute,
        )

        # Per-specialization counters
        self.max_per_specialization = max_per_specialization
        self._specialization_counts: Dict[str, int] = {}
        self._specialization_lock = asyncio.Lock()

        # Resource exhaustion limit
        self.max_total_agents = max_total_agents
        self._current_total_agents = 0
        self._total_agents_lock = asyncio.Lock()

    async def check_clonal_expansion(
        self,
        especializacao: str,
        quantidade: int,
        current_total_agents: int,
    ) -> None:
        """
        Check if clonal expansion is allowed.

        Args:
            especializacao: Specialization type
            quantidade: Number of clones requested
            current_total_agents: Current total agent count

        Raises:
            LymphnodeRateLimitError: If rate limited
            LymphnodeResourceExhaustedError: If resource limit exceeded
        """
        from coordination.exceptions import LymphnodeResourceExhaustedError

        # Check global rate limit
        await self.global_limiter.acquire_or_raise(quantidade)

        # Check per-specialization limit
        async with self._specialization_lock:
            current_count = self._specialization_counts.get(especializacao, 0)
            new_count = current_count + quantidade

            if new_count > self.max_per_specialization:
                raise LymphnodeRateLimitError(
                    f"Specialization limit exceeded for '{especializacao}': "
                    f"{new_count} > {self.max_per_specialization}"
                )

            self._specialization_counts[especializacao] = new_count

        # Check total agents limit
        async with self._total_agents_lock:
            self._current_total_agents = current_total_agents
            new_total = current_total_agents + quantidade

            if new_total > self.max_total_agents:
                raise LymphnodeResourceExhaustedError(
                    f"Total agent limit exceeded: {new_total} > {self.max_total_agents}"
                )

    async def release_clones(self, especializacao: str, quantidade: int) -> None:
        """
        Release clones from specialization count (when destroyed).

        Args:
            especializacao: Specialization type
            quantidade: Number of clones destroyed
        """
        async with self._specialization_lock:
            current_count = self._specialization_counts.get(especializacao, 0)
            self._specialization_counts[especializacao] = max(0, current_count - quantidade)

    def get_stats(self) -> Dict[str, any]:
        """Get clonal expansion rate limiter statistics"""
        return {
            "global_limiter": self.global_limiter.get_stats(),
            "specialization_counts": dict(self._specialization_counts),
            "max_per_specialization": self.max_per_specialization,
            "current_total_agents": self._current_total_agents,
            "max_total_agents": self.max_total_agents,
        }
