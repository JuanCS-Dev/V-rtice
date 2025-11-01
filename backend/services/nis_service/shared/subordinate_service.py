"""
Subordinate Service Base Interface

This module defines the base interface for all MAXIMUS subordinate services.
All subordinate services (MABA, MVP, PENELOPE) inherit from this base class
to ensure consistent integration patterns with MAXIMUS Core.

Key Features:
- Standardized lifecycle management (startup/shutdown)
- Automatic service registry integration
- Health check interface
- Tool protocol implementation
- Metrics exposition via Prometheus
- Graceful degradation on failures

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class ServiceHealthStatus:
    """Health status constants for subordinate services."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    INITIALIZING = "initializing"


class SubordinateServiceBase(ABC):
    """
    Base class for all MAXIMUS subordinate services.

    All subordinate services must implement this interface to ensure
    proper integration with MAXIMUS Core and the Vértice Platform.

    Attributes:
        service_name: Unique service identifier (e.g., "maba", "mvp", "penelope")
        service_version: Semantic version string
        maximus_endpoint: URL to MAXIMUS Core Service
        _running: Service running state
        _initialized: Service initialization state
        _http_client: Shared HTTP client for MAXIMUS communication
    """

    # Prometheus metrics (shared across all subordinate services)
    requests_total = Counter(
        "subordinate_service_requests_total",
        "Total requests processed by subordinate service",
        ["service_name", "operation"],
    )

    request_duration = Histogram(
        "subordinate_service_request_duration_seconds",
        "Request duration in seconds",
        ["service_name", "operation"],
    )

    health_status = Gauge(
        "subordinate_service_health_status",
        "Service health status (1=healthy, 0.5=degraded, 0=unhealthy)",
        ["service_name"],
    )

    def __init__(
        self,
        service_name: str,
        service_version: str,
        maximus_endpoint: str | None = None,
    ):
        """
        Initialize subordinate service base.

        Args:
            service_name: Unique service identifier
            service_version: Semantic version string
            maximus_endpoint: URL to MAXIMUS Core (optional, can use registry)
        """
        self.service_name = service_name
        self.service_version = service_version
        self.maximus_endpoint = (
            maximus_endpoint or "http://vertice-maximus-core-service:8150"
        )

        self._running = False
        self._initialized = False
        self._http_client: httpx.AsyncClient | None = None
        self._startup_time: datetime | None = None

        logger.info(
            f"🔧 Initializing {self.service_name} v{self.service_version} "
            f"(MAXIMUS endpoint: {self.maximus_endpoint})"
        )

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize service-specific resources.

        This method must be implemented by each subordinate service to
        set up their specific resources (databases, ML models, etc.).

        Returns:
            True if initialization succeeded, False otherwise
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown service-specific resources.

        This method must be implemented by each subordinate service to
        gracefully release their resources.
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Perform service-specific health checks.

        Returns:
            Dict containing health status and component details
        """
        pass

    async def start(self) -> None:
        """
        Start the subordinate service.

        This method handles:
        - HTTP client initialization
        - Service-specific initialization
        - MAXIMUS registration
        - Health status updates
        """
        if self._running:
            logger.warning(f"{self.service_name} already running")
            return

        logger.info(f"🚀 Starting {self.service_name}...")

        try:
            # Initialize HTTP client
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0), follow_redirects=True
            )
            logger.debug("✅ HTTP client initialized")

            # Call service-specific initialization
            success = await self.initialize()
            if not success:
                raise RuntimeError(f"{self.service_name} initialization failed")

            self._initialized = True
            self._running = True
            self._startup_time = datetime.utcnow()

            # Update health metrics
            self.health_status.labels(service_name=self.service_name).set(1.0)

            logger.info(f"✅ {self.service_name} started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start {self.service_name}: {e}")
            self.health_status.labels(service_name=self.service_name).set(0.0)
            raise

    async def stop(self) -> None:
        """
        Stop the subordinate service gracefully.

        This method handles:
        - Service-specific shutdown
        - HTTP client cleanup
        - State cleanup
        """
        if not self._running:
            logger.warning(f"{self.service_name} not running")
            return

        logger.info(f"👋 Stopping {self.service_name}...")

        try:
            # Call service-specific shutdown
            await self.shutdown()

            # Close HTTP client
            if self._http_client and not self._http_client.is_closed:
                await self._http_client.aclose()
                self._http_client = None

            self._running = False
            self.health_status.labels(service_name=self.service_name).set(0.0)

            logger.info(f"✅ {self.service_name} stopped successfully")

        except Exception as e:
            logger.error(f"⚠️ Error stopping {self.service_name}: {e}")
            # Continue shutdown even on error

    async def call_maximus(
        self,
        endpoint: str,
        method: str = "POST",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Call MAXIMUS Core Service endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/api/v1/query")
            method: HTTP method (GET, POST, etc.)
            payload: Request payload for POST/PUT

        Returns:
            Response JSON or None on error
        """
        if not self._http_client:
            logger.error("HTTP client not initialized")
            return None

        url = f"{self.maximus_endpoint}{endpoint}"

        try:
            if method.upper() == "GET":
                response = await self._http_client.get(url)
            elif method.upper() == "POST":
                response = await self._http_client.post(url, json=payload)
            elif method.upper() == "PUT":
                response = await self._http_client.put(url, json=payload)
            elif method.upper() == "DELETE":
                response = await self._http_client.delete(url)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MAXIMUS API error: {e.response.status_code} - {e.response.text}"
            )
            return None

        except httpx.RequestError as e:
            logger.error(f"MAXIMUS connection error: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error calling MAXIMUS: {e}")
            return None

    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        if not self._startup_time:
            return 0.0
        return (datetime.utcnow() - self._startup_time).total_seconds()

    def is_healthy(self) -> bool:
        """Check if service is in healthy state."""
        return self._running and self._initialized

    async def get_base_health_info(self) -> dict[str, Any]:
        """
        Get base health information (common across all services).

        Returns:
            Dict with base health info
        """
        return {
            "service_name": self.service_name,
            "version": self.service_version,
            "status": (
                ServiceHealthStatus.HEALTHY
                if self.is_healthy()
                else ServiceHealthStatus.UNHEALTHY
            ),
            "running": self._running,
            "initialized": self._initialized,
            "uptime_seconds": self.get_uptime_seconds(),
            "timestamp": datetime.utcnow().isoformat(),
            "maximus_endpoint": self.maximus_endpoint,
        }
