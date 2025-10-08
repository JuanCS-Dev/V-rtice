"""
Base client for external services with graceful degradation.

Implements:
- Circuit breaker pattern
- Retry logic with exponential backoff
- Timeout handling
- Health checks
- Graceful degradation fallbacks

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class ServiceUnavailable(Exception):
    """Exception raised when service is unavailable."""

    pass


class BaseExternalClient(ABC):
    """
    Base client for external services.

    Features:
    - Circuit breaker: Opens after N consecutive failures
    - Retry logic: Exponential backoff
    - Timeout handling: Configurable timeouts
    - Health checks: Periodic availability checks
    - Graceful degradation: Fallback when service unavailable

    Usage:
        class MyClient(BaseExternalClient):
            async def degraded_fallback(self, method, endpoint, **kwargs):
                # Implement fallback behavior
                return {"status": "degraded", "data": None}

        client = MyClient(base_url="http://service:8000")
        await client.initialize()
        result = await client.request("GET", "/endpoint")
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
        enable_degraded_mode: bool = True,
    ):
        """
        Initialize base client.

        Args:
            base_url: Base URL of the service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_backoff_base: Base for exponential backoff (seconds)
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Seconds before attempting to close circuit
            enable_degraded_mode: Enable graceful degradation
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.enable_degraded_mode = enable_degraded_mode

        self._client: Optional[httpx.AsyncClient] = None
        self._failures = 0
        self._circuit_open = False
        self._circuit_opened_at: Optional[datetime] = None
        self._available = False
        self._last_health_check: Optional[datetime] = None

    async def initialize(self) -> None:
        """
        Initialize client and check service availability.

        Raises:
            ServiceUnavailable: If service is down and degraded mode disabled
        """
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )

        # Initial health check
        try:
            is_healthy = await self.health_check()
            self._available = is_healthy

            if is_healthy:
                logger.info(f"{self.__class__.__name__}: Service available at {self.base_url}")
            else:
                logger.warning(
                    f"{self.__class__.__name__}: Service unhealthy at {self.base_url}, "
                    f"degraded_mode={'enabled' if self.enable_degraded_mode else 'disabled'}"
                )

        except Exception as e:
            self._available = False
            logger.error(f"{self.__class__.__name__}: Service unavailable at {self.base_url}: {e}")

            if not self.enable_degraded_mode:
                raise ServiceUnavailable(f"Service unavailable: {self.base_url}")

    async def close(self) -> None:
        """Close client connections."""
        if self._client:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """
        Check if service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self._client.get("/health", timeout=5.0)
            self._last_health_check = datetime.now()
            return response.status_code == 200

        except Exception as e:
            logger.debug(f"{self.__class__.__name__}: Health check failed: {e}")
            return False

    async def _check_circuit_breaker(self) -> None:
        """
        Check circuit breaker state.

        If circuit is open and timeout has passed, attempt to close it
        by performing a health check.

        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        if not self._circuit_open:
            return

        # Check if timeout has passed
        if self._circuit_opened_at:
            elapsed = (datetime.now() - self._circuit_opened_at).total_seconds()

            if elapsed >= self.circuit_breaker_timeout:
                # Attempt to close circuit with health check
                logger.info(f"{self.__class__.__name__}: Attempting to close circuit breaker")

                try:
                    is_healthy = await self.health_check()

                    if is_healthy:
                        # Close circuit
                        self._circuit_open = False
                        self._circuit_opened_at = None
                        self._failures = 0
                        logger.info(f"{self.__class__.__name__}: Circuit breaker closed")
                        return

                except Exception as e:
                    logger.warning(
                        f"{self.__class__.__name__}: Health check failed during circuit breaker recovery: {e}",
                        exc_info=True,
                    )

        # Circuit still open
        raise CircuitBreakerOpen(f"Circuit breaker open for {self.__class__.__name__}")

    def _open_circuit_breaker(self) -> None:
        """Open circuit breaker."""
        self._circuit_open = True
        self._circuit_opened_at = datetime.now()
        logger.warning(f"{self.__class__.__name__}: Circuit breaker opened after {self._failures} failures")

    async def request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """
        Make HTTP request with circuit breaker and graceful degradation.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/api/v1/resource")
            **kwargs: Additional arguments for httpx request

        Returns:
            Response JSON or degraded fallback result

        Raises:
            CircuitBreakerOpen: If circuit is open and degraded mode disabled
            ServiceUnavailable: If service unavailable and degraded mode disabled
        """
        # Check circuit breaker
        try:
            await self._check_circuit_breaker()
        except CircuitBreakerOpen:
            if self.enable_degraded_mode:
                logger.debug(f"{self.__class__.__name__}: Circuit open, using degraded fallback")
                return await self.degraded_fallback(method, endpoint, **kwargs)
            else:
                raise

        # Retry loop with exponential backoff
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(method, endpoint, **kwargs)
                response.raise_for_status()

                # Success - reset failure count
                self._failures = 0
                self._available = True

                return response.json()

            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.warning(
                    f"{self.__class__.__name__}: HTTP {e.response.status_code} "
                    f"on {method} {endpoint} (attempt {attempt + 1}/{self.max_retries + 1})"
                )

                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    break

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                logger.warning(
                    f"{self.__class__.__name__}: Connection error on {method} {endpoint} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                )

            except Exception as e:
                last_exception = e
                logger.error(f"{self.__class__.__name__}: Unexpected error on {method} {endpoint}: {e}")
                break

            # Exponential backoff before retry
            if attempt < self.max_retries:
                backoff = self.retry_backoff_base**attempt
                await asyncio.sleep(backoff)

        # All retries failed
        self._failures += 1
        self._available = False

        # Open circuit breaker if threshold reached
        if self._failures >= self.circuit_breaker_threshold:
            self._open_circuit_breaker()

        # Graceful degradation
        if self.enable_degraded_mode:
            logger.info(
                f"{self.__class__.__name__}: Request failed after {self.max_retries + 1} attempts, "
                f"using degraded fallback"
            )
            return await self.degraded_fallback(method, endpoint, **kwargs)
        else:
            raise ServiceUnavailable(f"Service unavailable after {self.max_retries + 1} attempts: {last_exception}")

    @abstractmethod
    async def degraded_fallback(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """
        Fallback implementation when service is unavailable.

        Each client implements its own graceful degradation strategy.

        Args:
            method: HTTP method that failed
            endpoint: API endpoint that failed
            **kwargs: Original request kwargs

        Returns:
            Degraded response (implementation-specific)
        """
        pass

    def is_available(self) -> bool:
        """
        Check if service is currently available.

        Returns:
            True if service is available, False otherwise
        """
        return self._available and not self._circuit_open

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "service": self.__class__.__name__,
            "base_url": self.base_url,
            "available": self._available,
            "circuit_open": self._circuit_open,
            "failures": self._failures,
            "circuit_opened_at": self._circuit_opened_at.isoformat() if self._circuit_opened_at else None,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "degraded_mode_enabled": self.enable_degraded_mode,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"base_url={self.base_url}, "
            f"available={self._available}, "
            f"circuit_open={self._circuit_open}, "
            f"failures={self._failures}"
            f")"
        )
