"""Maximus OSINT Service - Circuit Breaker Pattern.

This module implements the Circuit Breaker pattern for fail-fast behavior when
external APIs are failing repeatedly. It prevents cascading failures and allows
systems to recover gracefully.

Circuit States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Too many failures, all requests fail immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

Constitutional Compliance:
    - Article III (Zero Trust): Assume external APIs can fail
    - Article IV (Antifragility): System recovers stronger after failures

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 1.0.0
"""

import time
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, rejecting requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker for fail-fast behavior on repeated failures.

    Implements the classic circuit breaker pattern:
    1. CLOSED: All requests pass through, failures are counted
    2. OPEN: After N failures, circuit opens, all requests fail immediately
    3. HALF_OPEN: After timeout, circuit allows limited requests to test recovery
    4. Recovery: If test requests succeed, circuit closes

    This prevents hammering a failing API and allows graceful recovery.

    Usage Example:
        circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        if circuit.can_execute():
            try:
                result = await make_api_call()
                circuit.record_success()
            except Exception:
                circuit.record_failure()
        else:
            # Circuit is OPEN, fail immediately
            raise Exception("Service unavailable")

    Attributes:
        failure_threshold: Failures before circuit opens
        recovery_timeout: Seconds before attempting recovery
        state: Current circuit state (CLOSED/OPEN/HALF_OPEN)
        failure_count: Current failure count
        last_failure_time: Timestamp of last failure
        success_count_in_half_open: Successes during recovery test
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ):
        """Initialize CircuitBreaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Successes needed in HALF_OPEN to close circuit

        Raises:
            ValueError: If thresholds are invalid
        """
        if failure_threshold <= 0:
            raise ValueError(f"failure_threshold must be positive, got {failure_threshold}")
        if recovery_timeout <= 0:
            raise ValueError(f"recovery_timeout must be positive, got {recovery_timeout}")
        if success_threshold <= 0:
            raise ValueError(f"success_threshold must be positive, got {success_threshold}")

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count_in_half_open = 0

    def can_execute(self) -> bool:
        """Check if request can be executed.

        Returns:
            True if request should proceed, False if circuit is OPEN
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self.last_failure_time is None:
                return False

            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                # Transition to HALF_OPEN to test recovery
                self.state = CircuitState.HALF_OPEN
                self.success_count_in_half_open = 0
                return True

            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests during recovery test
            return True

        return False

    def record_success(self) -> None:
        """Record successful request.

        In CLOSED state: Resets failure count
        In HALF_OPEN state: Increments success count, closes circuit if threshold met
        """
        if self.state == CircuitState.CLOSED:
            # Reset failures on success
            self.failure_count = 0

        elif self.state == CircuitState.HALF_OPEN:
            # Count successes during recovery
            self.success_count_in_half_open += 1

            # If enough successes, close circuit (recovery successful)
            if self.success_count_in_half_open >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count_in_half_open = 0

    def record_failure(self) -> None:
        """Record failed request.

        In CLOSED state: Increments failure count, opens circuit if threshold met
        In HALF_OPEN state: Immediately opens circuit (recovery failed)
        """
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1

            # Open circuit if threshold exceeded
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

        elif self.state == CircuitState.HALF_OPEN:
            # Recovery failed, re-open circuit
            self.state = CircuitState.OPEN
            self.success_count_in_half_open = 0

    def reset(self) -> None:
        """Manually reset circuit to CLOSED state.

        Useful for testing or manual intervention.
        """
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count_in_half_open = 0

    def get_status(self) -> dict:
        """Get current circuit breaker status.

        Returns:
            Status dictionary with state, failure count, and timing info
        """
        status = {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

        if self.last_failure_time is not None:
            elapsed = time.time() - self.last_failure_time
            status["time_since_last_failure"] = elapsed
            status["time_until_recovery"] = max(0, self.recovery_timeout - elapsed)

        if self.state == CircuitState.HALF_OPEN:
            status["success_count_in_half_open"] = self.success_count_in_half_open
            status["success_threshold"] = self.success_threshold

        return status

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"CircuitBreaker(state={self.state.value}, "
            f"failures={self.failure_count}/{self.failure_threshold})"
        )
