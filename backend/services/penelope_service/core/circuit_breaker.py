"""Circuit Breaker - Auto-Healing Protection.

Implements circuit breaker pattern to prevent runaway auto-healing operations.
Protects services from repeated failed healing attempts that could cause cascading failures.

Circuit Breaker Pattern: Prevents cascading failures by stopping operations after threshold
Biblical Foundation: Proverbs 14:15 - "The prudent gives thought to his steps"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import logging
import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class HealingCircuitBreaker:
    """Circuit breaker for auto-healing operations.

    Implements three-state circuit breaker (Closed, Open, Half-Open) to protect
    services from repeated failed healing attempts.

    States:
    - CLOSED: Normal operation, healing allowed
    - OPEN: Too many failures, healing blocked (cooldown period)
    - HALF_OPEN: Testing recovery, one attempt allowed

    Architecture:
    - Failure tracking with sliding time window
    - Configurable thresholds and cooldown periods
    - Per-service state management
    - Thread-safe with asyncio.Lock
    - Prometheus metrics for monitoring

    Biblical Principle: Prudent consideration (Proverbs 14:15)
    """

    # Prometheus metrics
    circuit_state_gauge = Gauge(
        "penelope_circuit_breaker_state",
        "Circuit breaker state (0=closed, 1=open, 2=half_open)",
        ["service"],
    )

    healing_blocked_total = Counter(
        "penelope_healing_blocked_total",
        "Total healing attempts blocked by circuit breaker",
        ["service"],
    )

    healing_allowed_total = Counter(
        "penelope_healing_allowed_total",
        "Total healing attempts allowed by circuit breaker",
        ["service"],
    )

    circuit_transitions_total = Counter(
        "penelope_circuit_transitions_total",
        "Circuit breaker state transitions",
        ["service", "from_state", "to_state"],
    )

    failure_count_gauge = Gauge(
        "penelope_circuit_breaker_failures",
        "Current failure count in window",
        ["service"],
    )

    def __init__(
        self,
        failure_threshold: int = 3,
        window_minutes: int = 15,
        cooldown_minutes: int = 60,
    ):
        """Initialize Circuit Breaker.

        Args:
            failure_threshold: Number of failures before opening circuit (default: 3)
            window_minutes: Time window for counting failures (default: 15)
            cooldown_minutes: Cooldown period before half-open (default: 60)
        """
        self.failure_threshold = failure_threshold
        self.window_minutes = window_minutes
        self.cooldown_minutes = cooldown_minutes

        # State tracking (per service)
        self.failures: dict[str, list[float]] = {}  # service -> failure timestamps
        self.state: dict[str, str] = {}  # service -> state (closed, open, half_open)
        self.opened_at: dict[str, float] = {}  # service -> timestamp when opened

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit Breaker initialized: threshold={failure_threshold}, "
            f"window={window_minutes}m, cooldown={cooldown_minutes}m"
        )

    async def is_allowed(self, service: str) -> tuple[bool, str]:
        """Check if healing is allowed for service.

        Args:
            service: Service name

        Returns:
            Tuple of (allowed, reason):
            - allowed: True if healing should proceed
            - reason: Explanation string
        """
        async with self._lock:
            state = self.state.get(service, "closed")

            # State: CLOSED (normal operation)
            if state == "closed":
                self.healing_allowed_total.labels(service=service).inc()
                return True, "Circuit closed (normal operation)"

            # State: OPEN (blocked, in cooldown)
            if state == "open":
                # Check if cooldown period has expired
                elapsed_minutes = (time.time() - self.opened_at[service]) / 60
                if elapsed_minutes >= self.cooldown_minutes:
                    # Transition to half-open
                    await self._transition_state(service, "open", "half_open")
                    self.healing_allowed_total.labels(service=service).inc()
                    logger.info(
                        f"🔄 Circuit breaker HALF-OPEN for {service} "
                        f"(after {elapsed_minutes:.1f}m cooldown)"
                    )
                    return True, "Circuit half-open (testing recovery)"
                else:
                    # Still in cooldown
                    remaining = self.cooldown_minutes - elapsed_minutes
                    self.healing_blocked_total.labels(service=service).inc()
                    logger.warning(
                        f"🚫 Healing blocked for {service}: circuit OPEN "
                        f"(cooldown remaining: {remaining:.1f}m)"
                    )
                    return (
                        False,
                        f"Circuit open (cooldown: {remaining:.0f}m remaining)",
                    )

            # State: HALF_OPEN (testing recovery)
            if state == "half_open":
                self.healing_allowed_total.labels(service=service).inc()
                logger.debug(
                    f"🧪 Circuit breaker HALF-OPEN: allowing test attempt for {service}"
                )
                return True, "Circuit half-open (testing recovery)"

            # Unknown state (defensive)
            logger.error(f"Unknown circuit breaker state for {service}: {state}")
            return False, f"Unknown state: {state}"

    async def record_failure(self, service: str, error: str | None = None) -> None:
        """Record healing failure and potentially open circuit.

        Args:
            service: Service name
            error: Optional error message for logging
        """
        now = time.time()

        async with self._lock:
            # Initialize failure tracking
            if service not in self.failures:
                self.failures[service] = []

            # Add failure timestamp
            self.failures[service].append(now)

            # Clean old failures (outside time window)
            window_start = now - (self.window_minutes * 60)
            self.failures[service] = [
                ts for ts in self.failures[service] if ts > window_start
            ]

            failure_count = len(self.failures[service])
            self.failure_count_gauge.labels(service=service).set(failure_count)

            current_state = self.state.get(service, "closed")

            # Log failure
            logger.warning(
                f"⚠️  Healing failure for {service}: {error or 'Unknown error'} "
                f"({failure_count}/{self.failure_threshold} in {self.window_minutes}m)"
            )

            # Check if threshold exceeded
            if failure_count >= self.failure_threshold:
                if current_state != "open":
                    # Open circuit
                    await self._transition_state(service, current_state, "open")
                    self.opened_at[service] = now

                    logger.error(
                        f"🚨 Circuit breaker OPENED for {service}: "
                        f"{failure_count} failures in {self.window_minutes} minutes. "
                        f"Healing blocked for {self.cooldown_minutes} minutes."
                    )

            # Half-open state failure -> back to open
            elif current_state == "half_open":
                await self._transition_state(service, "half_open", "open")
                self.opened_at[service] = now

                logger.warning(
                    f"🔄 Circuit breaker re-OPENED for {service}: "
                    f"Test attempt failed. Cooldown reset."
                )

    async def record_success(self, service: str) -> None:
        """Record healing success and potentially close circuit.

        Args:
            service: Service name
        """
        async with self._lock:
            current_state = self.state.get(service, "closed")

            # Half-open success -> close circuit
            if current_state == "half_open":
                await self._transition_state(service, "half_open", "closed")

                # Clear failure history
                if service in self.failures:
                    self.failures[service] = []
                    self.failure_count_gauge.labels(service=service).set(0)

                logger.info(
                    f"✅ Circuit breaker CLOSED for {service}: "
                    f"Test attempt succeeded, normal operation resumed"
                )

            # Closed success -> just log
            elif current_state == "closed":
                logger.debug(f"✅ Healing success for {service} (circuit closed)")

    async def get_status(self, service: str) -> dict[str, Any]:
        """Get circuit breaker status for service.

        Args:
            service: Service name

        Returns:
            Dict with circuit breaker status:
            - state: Current state (closed, open, half_open)
            - failure_count: Current failures in window
            - failure_threshold: Configured threshold
            - opened_at: Timestamp when opened (if open)
            - cooldown_remaining: Minutes remaining in cooldown (if open)
        """
        async with self._lock:
            state = self.state.get(service, "closed")
            failure_count = len(self.failures.get(service, []))

            status = {
                "state": state,
                "failure_count": failure_count,
                "failure_threshold": self.failure_threshold,
                "window_minutes": self.window_minutes,
                "cooldown_minutes": self.cooldown_minutes,
            }

            if state == "open" and service in self.opened_at:
                elapsed_minutes = (time.time() - self.opened_at[service]) / 60
                remaining = max(0, self.cooldown_minutes - elapsed_minutes)
                status["opened_at"] = self.opened_at[service]
                status["cooldown_remaining_minutes"] = remaining

            return status

    async def reset_circuit(self, service: str) -> None:
        """Manually reset circuit breaker for service (for testing/admin).

        Args:
            service: Service name
        """
        async with self._lock:
            old_state = self.state.get(service, "closed")

            if service in self.failures:
                self.failures[service] = []
                self.failure_count_gauge.labels(service=service).set(0)

            if service in self.state:
                await self._transition_state(service, old_state, "closed")

            if service in self.opened_at:
                del self.opened_at[service]

            logger.warning(
                f"⚠️  Circuit breaker manually RESET for {service} "
                f"(previous state: {old_state})"
            )

    async def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """Get status for all tracked services.

        Returns:
            Dict of service -> status
        """
        async with self._lock:
            all_services = set(self.state.keys()) | set(self.failures.keys())

            statuses = {}
            for service in all_services:
                statuses[service] = await self.get_status(service)

            return statuses

    async def cleanup_old_entries(self) -> int:
        """Remove failure entries older than window (for memory management).

        Returns:
            Number of services cleaned
        """
        now = time.time()
        window_start = now - (self.window_minutes * 60)
        cleaned = 0

        async with self._lock:
            for service in list(self.failures.keys()):
                old_count = len(self.failures[service])
                self.failures[service] = [
                    ts for ts in self.failures[service] if ts > window_start
                ]
                new_count = len(self.failures[service])

                if old_count != new_count:
                    cleaned += 1
                    self.failure_count_gauge.labels(service=service).set(new_count)

        if cleaned > 0:
            logger.debug(f"Cleaned old failure entries for {cleaned} services")

        return cleaned

    async def _transition_state(
        self, service: str, from_state: str, to_state: str
    ) -> None:
        """Internal method to transition circuit breaker state.

        Updates state, metrics, and logs transition.

        Args:
            service: Service name
            from_state: Current state
            to_state: New state
        """
        self.state[service] = to_state

        # Update metrics
        state_value = {"closed": 0, "open": 1, "half_open": 2}.get(to_state, -1)
        self.circuit_state_gauge.labels(service=service).set(state_value)

        self.circuit_transitions_total.labels(
            service=service, from_state=from_state, to_state=to_state
        ).inc()

        logger.info(
            f"Circuit breaker state transition for {service}: {from_state} -> {to_state}"
        )
