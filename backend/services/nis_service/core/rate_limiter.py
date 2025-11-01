"""Rate Limiter - Narrative Generation Rate Control.

Implements rate limiting for narrative generation to control costs and
prevent API abuse. Enforces hourly, daily, and per-service interval limits.

Rate Control Principle: Responsible resource usage and cost control
Biblical Foundation: Ecclesiastes 3:1 - "A time for everything"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import logging
import time
from typing import Any

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)


class NarrativeRateLimiter:
    """Rate limit narrative generation to control costs.

    Implements multi-level rate limiting:
    - Global hourly limit (default: 100 narratives/hour)
    - Global daily limit (default: 1000 narratives/day)
    - Per-service minimum interval (default: 60 seconds between narratives)

    Architecture:
    - Time-based sliding window for global limits
    - Per-service cooldown tracking
    - Thread-safe with asyncio.Lock
    - Prometheus metrics for monitoring
    - Automatic cleanup of old entries

    Biblical Principle: A time for everything (Ecclesiastes 3:1)
    """

    # Prometheus metrics
    requests_total = Counter(
        "mvp_narrative_requests_total",
        "Total narrative generation requests",
        ["status"],  # allowed, rate_limited
    )

    requests_in_window = Gauge(
        "mvp_narrative_requests_in_window",
        "Narrative requests in current time window",
        ["window"],  # hour, day
    )

    rate_limit_remaining = Gauge(
        "mvp_narrative_rate_limit_remaining",
        "Remaining requests before rate limit",
        ["limit_type"],  # hourly, daily
    )

    def __init__(
        self,
        max_per_hour: int = 100,
        max_per_day: int = 1000,
        min_interval_seconds: int = 60,
    ):
        """Initialize Narrative Rate Limiter.

        Args:
            max_per_hour: Maximum narratives per hour (default: 100)
            max_per_day: Maximum narratives per day (default: 1000)
            min_interval_seconds: Minimum seconds between narratives for same service (default: 60)
        """
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.min_interval = min_interval_seconds

        # Request history: list of timestamps (unix time)
        self.request_history: list[float] = []

        # Per-service last request: service -> timestamp
        self.last_request: dict[str, float] = {}

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Rate Limiter initialized: {max_per_hour}/hour, "
            f"{max_per_day}/day, {min_interval_seconds}s interval"
        )

    async def check_rate_limit(
        self, service: str | None = None
    ) -> tuple[bool, str, dict[str, Any]]:
        """Check if request is allowed by rate limits.

        Performs three checks:
        1. Global hourly limit
        2. Global daily limit
        3. Per-service minimum interval (if service specified)

        Args:
            service: Service name for per-service interval check (optional)

        Returns:
            Tuple of (allowed, reason, stats):
            - allowed: True if request should be allowed
            - reason: Explanation string (OK or rejection reason)
            - stats: Dict with rate limit statistics
        """
        now = time.time()

        async with self._lock:
            # Define time windows
            hour_ago = now - 3600  # 1 hour
            day_ago = now - 86400  # 24 hours

            # Clean old entries (older than 24 hours)
            self.request_history = [ts for ts in self.request_history if ts > day_ago]

            # Count requests in time windows
            hour_count = sum(1 for ts in self.request_history if ts > hour_ago)
            day_count = len(self.request_history)

            # Calculate remaining
            hour_remaining = max(0, self.max_per_hour - hour_count)
            day_remaining = max(0, self.max_per_day - day_count)

            # Build statistics
            stats = {
                "hour_count": hour_count,
                "day_count": day_count,
                "hour_remaining": hour_remaining,
                "day_remaining": day_remaining,
                "max_per_hour": self.max_per_hour,
                "max_per_day": self.max_per_day,
            }

            # Check 1: Hourly limit
            if hour_count >= self.max_per_hour:
                self.requests_total.labels(status="rate_limited").inc()
                logger.warning(
                    f"⏱️  Hourly rate limit reached: {hour_count}/{self.max_per_hour}"
                )
                return (
                    False,
                    f"Hourly limit reached ({hour_count}/{self.max_per_hour})",
                    stats,
                )

            # Check 2: Daily limit
            if day_count >= self.max_per_day:
                self.requests_total.labels(status="rate_limited").inc()
                logger.warning(
                    f"📅 Daily rate limit reached: {day_count}/{self.max_per_day}"
                )
                return (
                    False,
                    f"Daily limit reached ({day_count}/{self.max_per_day})",
                    stats,
                )

            # Check 3: Per-service interval (if service specified)
            if service:
                last = self.last_request.get(service, 0)
                elapsed = now - last

                if elapsed < self.min_interval:
                    remaining = self.min_interval - elapsed
                    self.requests_total.labels(status="rate_limited").inc()
                    logger.warning(
                        f"🚦 Service {service} cooldown: wait {remaining:.1f}s "
                        f"(min interval: {self.min_interval}s)"
                    )
                    stats["service_cooldown_remaining"] = remaining
                    return (
                        False,
                        f"Too soon for {service} (wait {remaining:.0f}s)",
                        stats,
                    )

            # All checks passed - allow request
            self.request_history.append(now)
            if service:
                self.last_request[service] = now

            # Update metrics
            self.requests_total.labels(status="allowed").inc()
            self.requests_in_window.labels(window="hour").set(hour_count + 1)
            self.requests_in_window.labels(window="day").set(day_count + 1)
            self.rate_limit_remaining.labels(limit_type="hourly").set(
                hour_remaining - 1
            )
            self.rate_limit_remaining.labels(limit_type="daily").set(day_remaining - 1)

            logger.debug(
                f"✅ Rate limit check passed: {hour_count + 1}/{self.max_per_hour} hourly, "
                f"{day_count + 1}/{self.max_per_day} daily"
            )

            return True, "OK", stats

    async def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status and statistics.

        Returns:
            Dict with current counts, limits, and remaining capacity
        """
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400

        async with self._lock:
            # Clean old entries
            self.request_history = [ts for ts in self.request_history if ts > day_ago]

            hour_count = sum(1 for ts in self.request_history if ts > hour_ago)
            day_count = len(self.request_history)

            return {
                "hour_count": hour_count,
                "day_count": day_count,
                "hour_remaining": max(0, self.max_per_hour - hour_count),
                "day_remaining": max(0, self.max_per_day - day_count),
                "max_per_hour": self.max_per_hour,
                "max_per_day": self.max_per_day,
                "min_interval_seconds": self.min_interval,
                "hour_percent_used": (hour_count / self.max_per_hour * 100)
                if self.max_per_hour > 0
                else 0,
                "day_percent_used": (day_count / self.max_per_day * 100)
                if self.max_per_day > 0
                else 0,
                "active_services": len(self.last_request),
            }

    async def reset_service_cooldown(self, service: str) -> None:
        """Reset cooldown for a specific service (for testing/admin).

        Args:
            service: Service name to reset
        """
        async with self._lock:
            if service in self.last_request:
                del self.last_request[service]
                logger.info(f"Reset cooldown for service: {service}")

    async def reset_all_limits(self) -> None:
        """Reset all rate limits (for testing/admin).

        Warning: This bypasses all rate limiting. Use with caution.
        """
        async with self._lock:
            self.request_history.clear()
            self.last_request.clear()
            logger.warning("⚠️  All rate limits reset (administrative action)")

    async def get_service_cooldown(self, service: str) -> dict[str, Any]:
        """Get cooldown status for a specific service.

        Args:
            service: Service name

        Returns:
            Dict with cooldown information:
            - on_cooldown: Bool
            - remaining_seconds: Float (0 if not on cooldown)
            - last_request_time: Timestamp or None
        """
        now = time.time()

        async with self._lock:
            last = self.last_request.get(service)

            if last is None:
                return {
                    "on_cooldown": False,
                    "remaining_seconds": 0.0,
                    "last_request_time": None,
                }

            elapsed = now - last
            remaining = max(0, self.min_interval - elapsed)

            return {
                "on_cooldown": remaining > 0,
                "remaining_seconds": remaining,
                "last_request_time": last,
                "elapsed_seconds": elapsed,
            }

    async def cleanup_old_entries(self) -> int:
        """Manually trigger cleanup of old entries (beyond 24 hours).

        Returns:
            Number of entries removed
        """
        now = time.time()
        day_ago = now - 86400

        async with self._lock:
            old_count = len(self.request_history)
            self.request_history = [ts for ts in self.request_history if ts > day_ago]
            removed = old_count - len(self.request_history)

            if removed > 0:
                logger.debug(f"Cleaned up {removed} old rate limit entries")

            return removed
