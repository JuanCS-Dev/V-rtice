"""
Message Retry Logic with Exponential Backoff.

Implements intelligent retry mechanisms for failed RabbitMQ operations:
- Exponential backoff
- Jitter to avoid thundering herd
- Max retries configuration
- Retry headers (x-retries, x-first-death-queue)
- DLQ integration after exhausting retries

Features:
- Automatic retry for transient failures
- Exponential backoff with configurable parameters
- Random jitter for distributed retry timing
- Retry count tracking in message headers
- Seamless DLQ integration
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries)
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff (delay = base ** attempt)
        jitter: Whether to add random jitter to delays
        retry_exceptions: Tuple of exception types to retry
    """

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_exceptions: tuple = (ConnectionError, TimeoutError, OSError)

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given retry attempt.

        Uses exponential backoff with optional jitter:
        delay = min(initial_delay * (base ** attempt), max_delay)

        Args:
            attempt: Retry attempt number (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.initial_delay * (self.exponential_base ** attempt)

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled (±25% random variation)
        if self.jitter:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)  # Minimum 100ms

        return delay


class RetryableError(Exception):
    """Indicates an operation failed but is retryable."""

    pass


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Retry exhausted after {attempts} attempts. Last error: {last_error}"
        )


async def retry_with_backoff(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs,
) -> T:
    """
    Execute function with retry and exponential backoff.

    Args:
        func: Async function to execute
        config: Retry configuration (uses defaults if not provided)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of successful function call

    Raises:
        RetryExhaustedError: If all retries exhausted
        Exception: If non-retryable exception occurs
    """
    if config is None:
        config = RetryConfig()

    last_error: Optional[Exception] = None

    for attempt in range(config.max_retries + 1):
        try:
            # Attempt operation
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success
            if attempt > 0:
                logger.info(
                    f"Operation succeeded after {attempt} retries"
                )

            return result

        except config.retry_exceptions as e:
            last_error = e

            # Check if retries exhausted
            if attempt >= config.max_retries:
                logger.error(
                    f"Retry exhausted after {config.max_retries} attempts. "
                    f"Last error: {e}"
                )
                raise RetryExhaustedError(attempt + 1, e)

            # Calculate backoff delay
            delay = config.calculate_delay(attempt)

            logger.warning(
                f"Operation failed (attempt {attempt + 1}/{config.max_retries + 1}): {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            # Wait before retrying
            await asyncio.sleep(delay)

        except Exception as e:
            # Non-retryable exception - propagate immediately
            logger.error(f"Non-retryable error occurred: {e}")
            raise

    # Should not reach here, but for type safety
    raise RetryExhaustedError(config.max_retries + 1, last_error)


class RetryDecorator:
    """
    Decorator for automatic retries.

    Usage:
        @RetryDecorator(max_retries=3, initial_delay=1.0)
        async def publish_message():
            await client.publish(...)
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_exceptions: tuple = (ConnectionError, TimeoutError, OSError),
    ):
        """Initialize retry decorator with configuration."""
        self.config = RetryConfig(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_exceptions=retry_exceptions,
        )

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Wrap function with retry logic."""

        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, self.config, *args, **kwargs)

        return wrapper


# --- RabbitMQ-Specific Retry Headers ---


class MessageRetryHeaders:
    """
    Manages retry headers for RabbitMQ messages.

    Headers:
    - x-retries: Number of times message has been retried
    - x-first-death-queue: Original queue before retries
    - x-retry-reason: Reason for last retry
    - x-first-death-time: First failure timestamp
    """

    @staticmethod
    def get_retry_count(headers: Optional[dict]) -> int:
        """
        Get retry count from message headers.

        Args:
            headers: Message headers

        Returns:
            Retry count (0 if not present)
        """
        if headers is None:
            return 0

        return headers.get("x-retries", 0)

    @staticmethod
    def increment_retry_count(headers: Optional[dict]) -> dict:
        """
        Increment retry count in headers.

        Args:
            headers: Existing headers (can be None)

        Returns:
            Updated headers with incremented retry count
        """
        if headers is None:
            headers = {}

        current_retries = headers.get("x-retries", 0)
        headers["x-retries"] = current_retries + 1

        # Add first death time if not present
        if "x-first-death-time" not in headers:
            headers["x-first-death-time"] = int(time.time())

        return headers

    @staticmethod
    def add_retry_metadata(
        headers: Optional[dict],
        original_queue: str,
        retry_reason: str,
    ) -> dict:
        """
        Add retry metadata to headers.

        Args:
            headers: Existing headers
            original_queue: Original queue name
            retry_reason: Reason for retry

        Returns:
            Updated headers with retry metadata
        """
        if headers is None:
            headers = {}

        # Increment retry count
        headers = MessageRetryHeaders.increment_retry_count(headers)

        # Add original queue if not present
        if "x-first-death-queue" not in headers:
            headers["x-first-death-queue"] = original_queue

        # Add retry reason
        headers["x-retry-reason"] = retry_reason
        headers["x-last-retry-time"] = int(time.time())

        return headers

    @staticmethod
    def should_retry(
        headers: Optional[dict],
        max_retries: int = 3,
    ) -> bool:
        """
        Check if message should be retried.

        Args:
            headers: Message headers
            max_retries: Maximum retry attempts

        Returns:
            True if should retry, False if should send to DLQ
        """
        retry_count = MessageRetryHeaders.get_retry_count(headers)
        return retry_count < max_retries

    @staticmethod
    def calculate_retry_delay(
        headers: Optional[dict],
        config: Optional[RetryConfig] = None,
    ) -> float:
        """
        Calculate delay before next retry.

        Args:
            headers: Message headers
            config: Retry configuration

        Returns:
            Delay in seconds
        """
        if config is None:
            config = RetryConfig()

        retry_count = MessageRetryHeaders.get_retry_count(headers)
        return config.calculate_delay(retry_count)


# --- Context Manager for Retry ---


class RetryContext:
    """
    Context manager for retry operations.

    Usage:
        retry_ctx = RetryContext(max_retries=3)

        async with retry_ctx:
            await rabbitmq_client.publish(...)

        if retry_ctx.failed:
            print(f"Failed after {retry_ctx.attempts} attempts")
    """

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        operation_name: str = "operation",
    ):
        """
        Initialize retry context.

        Args:
            config: Retry configuration
            operation_name: Name for logging
        """
        self.config = config or RetryConfig()
        self.operation_name = operation_name

        self.attempts = 0
        self.failed = False
        self.last_error: Optional[Exception] = None

    async def __aenter__(self):
        """Enter context."""
        self.attempts = 0
        self.failed = False
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context with retry logic."""
        if exc_type is None:
            # Success
            return False

        # Check if should retry
        if not isinstance(exc_val, self.config.retry_exceptions):
            # Non-retryable exception
            logger.error(
                f"{self.operation_name} - non-retryable error: {exc_val}"
            )
            return False

        # Record attempt
        self.attempts += 1
        self.last_error = exc_val

        # Check if retries exhausted
        if self.attempts >= self.config.max_retries:
            self.failed = True
            logger.error(
                f"{self.operation_name} - retry exhausted after {self.attempts} attempts"
            )
            return False

        # Retry
        delay = self.config.calculate_delay(self.attempts - 1)
        logger.warning(
            f"{self.operation_name} - retry {self.attempts}/{self.config.max_retries}, "
            f"delay={delay:.2f}s"
        )

        await asyncio.sleep(delay)
        return True  # Suppress exception and retry


# --- Exponential Backoff Iterator ---


class ExponentialBackoff:
    """
    Iterator for exponential backoff delays.

    Usage:
        backoff = ExponentialBackoff()
        for delay in backoff:
            try:
                await operation()
                break
            except Exception:
                await asyncio.sleep(delay)
    """

    def __init__(
        self,
        initial: float = 1.0,
        maximum: float = 60.0,
        base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize exponential backoff.

        Args:
            initial: Initial delay
            maximum: Maximum delay
            base: Exponential base
            jitter: Add random jitter
        """
        self.initial = initial
        self.maximum = maximum
        self.base = base
        self.jitter = jitter
        self._attempt = 0

    def __iter__(self):
        """Return iterator."""
        return self

    def __next__(self) -> float:
        """Get next delay value."""
        delay = self.initial * (self.base ** self._attempt)
        delay = min(delay, self.maximum)

        if self.jitter:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)

        self._attempt += 1
        return delay

    def reset(self):
        """Reset to initial state."""
        self._attempt = 0
