"""Thalamus Client - Shared library for Sensory Cortex services.

This module provides a simple HTTP client for sensory services to submit
their perceptions to the Digital Thalamus for Global Workspace broadcasting.

FASE 3: Enables Sensory Cortex → Digital Thalamus routing.
"""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ThalamusClient:
    """HTTP client for submitting sensory data to Digital Thalamus.

    Attributes:
        thalamus_url: Base URL of Digital Thalamus service
        sensor_id: Unique identifier for this sensor
        sensor_type: Type of sensor (visual, auditory, etc.)
        client: HTTP client instance
    """

    def __init__(
        self,
        thalamus_url: str,
        sensor_id: str,
        sensor_type: str,
        timeout: float = 10.0
    ):
        """Initialize Thalamus client.

        Args:
            thalamus_url: Base URL of Digital Thalamus (e.g., http://digital_thalamus_service:8012)
            sensor_id: Unique sensor identifier
            sensor_type: Sensor type (visual, auditory, somatosensory, chemical, vestibular)
            timeout: HTTP request timeout in seconds
        """
        self.thalamus_url = thalamus_url.rstrip("/")
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.timeout = timeout

        self.client = httpx.AsyncClient(timeout=timeout)

        logger.info(f"🔗 Thalamus client initialized: {sensor_type} → {thalamus_url}")

    async def submit_perception(
        self,
        data: Dict[str, Any],
        priority: int = 5,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit sensory perception to Digital Thalamus.

        Args:
            data: Sensory data payload
            priority: Processing priority (1-10, 10 = highest)
            timestamp: ISO timestamp (auto-generated if not provided)

        Returns:
            Response from Thalamus including broadcast status

        Raises:
            httpx.HTTPError: If submission fails
        """
        endpoint = f"{self.thalamus_url}/ingest_sensory_data"

        payload = {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "data": data,
            "priority": priority
        }

        if timestamp:
            payload["timestamp"] = timestamp

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()

            result = response.json()

            # Log broadcasting status
            if result.get("broadcasted_to_global_workspace"):
                salience = result.get("salience", 0.0)
                logger.debug(f"📡 Perception broadcasted (salience: {salience:.2f})")
            else:
                logger.debug(f"⏭️  Perception processed (not broadcasted)")

            return result

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to submit to Thalamus: {e}")
            raise

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.client.aclose()
        logger.info(f"🔌 Thalamus client closed: {self.sensor_type}")
