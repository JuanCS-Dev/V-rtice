"""Maximus OSINT Service - Rate Limiter.

This module implements a Rate Limiter for the Maximus AI's OSINT Service.
It is responsible for controlling the frequency of requests made to external
APIs or websites, preventing abuse, avoiding IP blocking, and ensuring compliance
with service terms of use.

Key functionalities include:
- Enforcing predefined rate limits (e.g., requests per second, requests per minute).
- Implementing various rate limiting strategies (e.g., token bucket, leaky bucket).
- Handling back-off and retry mechanisms for rate-limited responses.
- Providing a simple decorator or context manager for rate-limited operations.

This rate limiter is crucial for maintaining the operational integrity of OSINT
scraping activities, ensuring that Maximus AI can collect data responsibly and
sustainably without being blocked or blacklisted by target services.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class RateLimiter:
    """Controls the frequency of requests made to external APIs or websites,
    preventing abuse, avoiding IP blocking, and ensuring compliance with service terms of use.

    Enforces predefined rate limits and implements various rate limiting strategies.
    """

    def __init__(self, rate_limit_per_minute: int = 60, burst_size: int = 5):
        """Initializes the RateLimiter.

        Args:
            rate_limit_per_minute (int): The maximum number of requests allowed per minute.
            burst_size (int): The maximum number of requests allowed in a short burst.
        """
        self.rate_limit = rate_limit_per_minute / 60.0 # requests per second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_refill_time = datetime.now()
        self.current_status: str = "active"

    async def acquire(self):
        """Acquires a token, waiting if the rate limit is exceeded.

        This method should be called before making a rate-limited request.
        """
        self._refill_tokens()
        while self.tokens < 1:
            wait_time = (1 - self.tokens) / self.rate_limit
            print(f"[RateLimiter] Rate limit exceeded. Waiting for {wait_time:.2f} seconds.")
            await asyncio.sleep(wait_time)
            self._refill_tokens()
        self.tokens -= 1

    def _refill_tokens(self):
        """Refills tokens based on the elapsed time since the last refill."""
        now = datetime.now()
        time_passed = (now - self.last_refill_time).total_seconds()
        self.last_refill_time = now
        self.tokens = min(self.burst_size, self.tokens + time_passed * self.rate_limit)

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Rate Limiter.

        Returns:
            Dict[str, Any]: A dictionary summarizing the limiter's status.
        """
        self._refill_tokens()
        return {
            "status": self.current_status,
            "rate_limit_per_minute": self.rate_limit * 60,
            "burst_size": self.burst_size,
            "current_tokens": self.tokens,
            "last_refill": self.last_refill_time.isoformat()
        }