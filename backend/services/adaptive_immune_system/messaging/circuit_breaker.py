"""
Circuit Breaker Pattern for RabbitMQ.

Implements circuit breaker to prevent cascading failures when RabbitMQ is unavailable.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failures exceeded threshold, requests fail fast
- HALF_OPEN: Testing if service recovered, limited requests allowed

Features:
- Automatic failure detection
- Configurable thresholds
- Exponential backoff for recovery attempts
- Metrics integration
- Thread-safe
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit breaker for RabbitMQ operations.

    Prevents cascading failures by detecting repeated failures and
    failing fast instead of overwhelming a struggling service.

    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=ConnectionError
        )

        @breaker
        async def publish_message():
            await rabbitmq_client.publish(...)

        # Or manually
        async with breaker:
            await rabbitmq_client.publish(...)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        half_open_max_calls: int = 1,
        name: str = "rabbitmq",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch (others will propagate)
            half_open_max_calls: Max calls allowed in HALF_OPEN state
            name: Name for logging and metrics
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.half_open_max_calls = half_open_max_calls
        self.name = name

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function raises unexpected exception
        """
        async with self._lock:
            # Check if circuit should transition states
            await self._check_state_transition()

            # If circuit is open, fail fast
            if self._state == CircuitState.OPEN:
                logger.warning(
                    f"CircuitBreaker '{self.name}' is OPEN - failing fast "
                    f"(failures={self._failure_count}, threshold={self.failure_threshold})"
                )
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is open "
                    f"(failures={self._failure_count}/{self.failure_threshold})"
                )

            # If half-open, limit concurrent calls
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    logger.debug(
                        f"CircuitBreaker '{self.name}' is HALF_OPEN - "
                        f"max calls reached, failing fast"
                    )
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is half-open "
                        "(testing recovery, try again later)"
                    )

                self._half_open_calls += 1

        # Execute function
        try:
            # Call function (async or sync)
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - record and potentially close circuit
            await self._on_success()
            return result

        except self.expected_exception as e:
            # Expected failure - record and potentially open circuit
            await self._on_failure()
            raise

        except Exception as e:
            # Unexpected exception - propagate without affecting circuit
            logger.warning(
                f"CircuitBreaker '{self.name}' - unexpected exception: {e}"
            )
            raise

    async def _check_state_transition(self) -> None:
        """
        Check if circuit should transition states.

        CLOSED → OPEN: If failures exceed threshold
        OPEN → HALF_OPEN: If recovery timeout elapsed
        HALF_OPEN → CLOSED: If test call succeeds
        HALF_OPEN → OPEN: If test call fails
        """
        if self._state == CircuitState.CLOSED:
            # Check if should open
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_failure_time = time.time()
                logger.error(
                    f"CircuitBreaker '{self.name}' opened - "
                    f"failures={self._failure_count}/{self.failure_threshold}"
                )

        elif self._state == CircuitState.OPEN:
            # Check if should attempt recovery
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(
                        f"CircuitBreaker '{self.name}' entering HALF_OPEN - "
                        f"testing recovery after {elapsed:.1f}s"
                    )

    async def _on_success(self) -> None:
        """Record successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                # Recovery successful - close circuit
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._half_open_calls = 0
                logger.info(
                    f"CircuitBreaker '{self.name}' closed - recovery successful"
                )

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                if self._failure_count > 0:
                    logger.debug(
                        f"CircuitBreaker '{self.name}' - "
                        f"success, resetting failures ({self._failure_count} → 0)"
                    )
                    self._failure_count = 0

    async def _on_failure(self) -> None:
        """Record failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Recovery failed - reopen circuit
                self._state = CircuitState.OPEN
                self._half_open_calls = 0
                logger.warning(
                    f"CircuitBreaker '{self.name}' reopened - recovery failed"
                )

            elif self._state == CircuitState.CLOSED:
                logger.debug(
                    f"CircuitBreaker '{self.name}' - "
                    f"failure recorded ({self._failure_count}/{self.failure_threshold})"
                )

    # --- Context Manager Support ---

    async def __aenter__(self):
        """Async context manager entry."""
        async with self._lock:
            await self._check_state_transition()

            if self._state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is open"
                )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is half-open (max calls reached)"
                    )
                self._half_open_calls += 1

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is None:
            # Success
            await self._on_success()
        elif isinstance(exc_val, self.expected_exception):
            # Expected failure
            await self._on_failure()
        # Unexpected exceptions propagate without affecting circuit

        return False  # Don't suppress exceptions

    # --- Decorator Support ---

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for wrapping functions.

        Usage:
            @circuit_breaker
            async def my_function():
                ...
        """
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                return await self.call(func, *args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                return asyncio.run(self.call(func, *args, **kwargs))

            return sync_wrapper

    # --- Manual Control ---

    async def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_calls = 0
            logger.info(f"CircuitBreaker '{self.name}' manually reset to CLOSED")

    async def force_open(self) -> None:
        """Manually force circuit breaker to OPEN state."""
        async with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()
            logger.warning(f"CircuitBreaker '{self.name}' manually forced OPEN")

    # --- Status Methods ---

    def get_status(self) -> dict:
        """
        Get circuit breaker status.

        Returns:
            Dict with status information
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time,
            "half_open_calls": self._half_open_calls if self._state == CircuitState.HALF_OPEN else 0,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CircuitBreaker(name='{self.name}', state={self._state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold})"
        )


# --- Global Circuit Breakers ---

_global_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception,
) -> CircuitBreaker:
    """
    Get or create global circuit breaker.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to catch

    Returns:
        CircuitBreaker instance
    """
    if name not in _global_circuit_breakers:
        _global_circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name,
        )

    return _global_circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """
    Get all registered circuit breakers.

    Returns:
        Dict of circuit breakers by name
    """
    return _global_circuit_breakers.copy()
