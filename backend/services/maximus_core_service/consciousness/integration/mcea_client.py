"""
MCEA Client - HTTP client for ArousalController

Fetches current arousal state from MCEA for immune system modulation.
"""

import asyncio
import logging
from typing import Optional

import httpx

from consciousness.mcea.controller import ArousalState, ArousalLevel

logger = logging.getLogger(__name__)


class MCEAClient:
    """
    HTTP client for MCEA ArousalController.

    Provides access to current arousal state for clonal selection modulation.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8100",  # MCEA service port
        timeout: float = 5.0,
    ):
        """
        Initialize MCEA client.

        Args:
            base_url: MCEA service base URL
            timeout: Request timeout (seconds)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        self._last_arousal: Optional[ArousalState] = None
        self._consecutive_failures = 0

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def get_current_arousal(self) -> Optional[ArousalState]:
        """
        Fetch current arousal state from MCEA controller.

        Returns:
            ArousalState if available, None if service unavailable

        Graceful degradation:
        - Returns last known arousal if request fails
        - Returns baseline arousal (0.5) after 3 consecutive failures
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/mcea/arousal")

            if response.status_code == 200:
                data = response.json()

                # Parse arousal state
                arousal_state = ArousalState(
                    arousal=data.get("arousal", 0.5),
                    level=ArousalLevel(data.get("level", "relaxed")),
                    threshold=data.get("threshold", 0.70),
                )

                # Cache successful result
                self._last_arousal = arousal_state
                self._consecutive_failures = 0

                return arousal_state

            else:
                logger.warning(
                    f"MCEA service returned {response.status_code}, using cached arousal"
                )
                self._consecutive_failures += 1
                return self._fallback_arousal()

        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning(f"MCEA service unavailable: {e}, using cached arousal")
            self._consecutive_failures += 1
            return self._fallback_arousal()

    def _fallback_arousal(self) -> ArousalState:
        """
        Fallback strategy when MCEA unavailable.

        Returns:
            Last known arousal if < 3 failures, baseline arousal (0.5) otherwise
        """
        if self._consecutive_failures < 3 and self._last_arousal:
            # Return cached arousal
            return self._last_arousal
        else:
            # After 3 failures, assume MCEA down - use baseline
            logger.warning("MCEA service persistently unavailable, using baseline arousal")
            return ArousalState(
                arousal=0.5,
                level=ArousalLevel.RELAXED,
                threshold=0.70,
            )

    def get_last_arousal(self) -> Optional[ArousalState]:
        """Get last successfully fetched arousal (cached)."""
        return self._last_arousal

    def is_healthy(self) -> bool:
        """Check if MCEA service is responsive."""
        return self._consecutive_failures < 3
