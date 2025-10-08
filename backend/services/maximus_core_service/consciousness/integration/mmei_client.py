"""
MMEI Client - HTTP client for InternalStateMonitor

Fetches current needs from MMEI interoception monitor for immune system integration.
"""

import logging

import httpx

from consciousness.mmei.monitor import AbstractNeeds

logger = logging.getLogger(__name__)


class MMEIClient:
    """
    HTTP client for MMEI InternalStateMonitor.

    Provides access to current abstract needs for immune system integration.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8100",  # MMEI service port
        timeout: float = 5.0,
    ):
        """
        Initialize MMEI client.

        Args:
            base_url: MMEI service base URL
            timeout: Request timeout (seconds)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        self._last_needs: AbstractNeeds | None = None
        self._consecutive_failures = 0

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def get_current_needs(self) -> AbstractNeeds | None:
        """
        Fetch current abstract needs from MMEI monitor.

        Returns:
            AbstractNeeds if available, None if service unavailable

        Graceful degradation:
        - Returns last known needs if request fails
        - Returns None after 3 consecutive failures
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/mmei/needs")

            if response.status_code == 200:
                data = response.json()

                # Parse needs
                needs = AbstractNeeds(
                    rest_need=data.get("rest_need", 0.0),
                    repair_need=data.get("repair_need", 0.0),
                    efficiency_need=data.get("efficiency_need", 0.0),
                    connectivity_need=data.get("connectivity_need", 0.0),
                    curiosity_drive=data.get("curiosity_drive", 0.0),
                )

                # Cache successful result
                self._last_needs = needs
                self._consecutive_failures = 0

                return needs

            logger.warning(f"MMEI service returned {response.status_code}, using cached needs")
            self._consecutive_failures += 1
            return self._fallback_needs()

        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning(f"MMEI service unavailable: {e}, using cached needs")
            self._consecutive_failures += 1
            return self._fallback_needs()

    def _fallback_needs(self) -> AbstractNeeds | None:
        """
        Fallback strategy when MMEI unavailable.

        Returns:
            Last known needs if < 3 failures, None otherwise
        """
        if self._consecutive_failures < 3:
            # Return cached needs
            return self._last_needs
        # After 3 failures, assume MMEI down
        logger.error("MMEI service persistently unavailable, returning None")
        return None

    def get_last_needs(self) -> AbstractNeeds | None:
        """Get last successfully fetched needs (cached)."""
        return self._last_needs

    def is_healthy(self) -> bool:
        """Check if MMEI service is responsive."""
        return self._consecutive_failures < 3
