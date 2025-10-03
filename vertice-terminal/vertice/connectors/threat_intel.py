"""
Threat Intelligence Connector - PRODUCTION READY
Connects to threat_intel_service backend (port 8013)
"""

import httpx
import os
from typing import Dict, Any, List, Optional
from .base import BaseConnector


class ThreatIntelConnector(BaseConnector):
    """Connector for Threat Intelligence Service."""

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = os.getenv("THREAT_INTEL_SERVICE_URL", "http://localhost:8013")
        super().__init__(service_name="Threat Intelligence", base_url=base_url)

    async def health_check(self) -> bool:
        """
        Checks if the Threat Intelligence service is online and operational.

        Returns:
            bool: True if the service is healthy, False otherwise.
        """
        try:
            response = await self.client.get(f"{self.base_url}/")
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "operational"
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False

    async def search_threat(self, indicator: str) -> Optional[Dict[str, Any]]:
        """
        Search for threat intelligence on an indicator.

        Args:
            indicator: IOC to search (IP, domain, hash, email, URL)

        Returns:
            Optional[Dict[str, Any]]: A dictionary with threat intelligence data, or None on failure.
        """
        payload = {"indicator": indicator}
        return await self._post("/api/threat/search", data=payload, timeout=30.0)

    async def lookup_threat(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Lookup threat indicator (alias for search_threat)."""
        return await self.search_threat(indicator)

    async def get_threat_timeline(
        self, incident_id: str, timeframe: str = "24h"
    ) -> Optional[Dict[str, Any]]:
        """
        Get threat activity timeline for an incident.

        Args:
            incident_id: Incident identifier
            timeframe: Time window (1h, 24h, 7d, 30d)

        Returns:
            Optional[Dict[str, Any]]: A dictionary with timeline events, or None on failure.
        """
        params = {"incident_id": incident_id, "timeframe": timeframe}
        return await self._get("/api/threat/timeline", params=params)

    async def pivot_analysis(
        self, ioc: str, depth: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Perform pivot analysis on an IOC.

        Args:
            ioc: IOC to pivot on
            depth: Analysis depth (1-3)

        Returns:
            Optional[Dict[str, Any]]: A dictionary with related entities, or None on failure.
        """
        payload = {"ioc": ioc, "depth": min(depth, 3)}  # Cap at 3
        return await self._post("/api/threat/pivot", data=payload, timeout=60.0)

    async def correlate_threats(self, ioc1: str, ioc2: str) -> Optional[Dict[str, Any]]:
        """
        Correlate two IOCs to find relationships.

        Args:
            ioc1: First IOC
            ioc2: Second IOC

        Returns:
            Optional[Dict[str, Any]]: A dictionary with correlation data, or None on failure.
        """
        payload = {"ioc1": ioc1, "ioc2": ioc2}
        return await self._post("/api/threat/correlate", data=payload, timeout=30.0)

    async def get_threat_feeds(self) -> Optional[Dict[str, Any]]:
        """Get active threat intelligence feeds."""
        return await self._get("/api/feeds")

    async def submit_ioc(
        self, ioc: str, ioc_type: str, tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Submit a new IOC to the threat database.

        Args:
            ioc: The indicator value
            ioc_type: Type (ip, domain, hash, email, url)
            tags: Optional tags for classification

        Returns:
            Optional[Dict[str, Any]]: A dictionary with submission result, or None on failure.
        """
        payload: Dict[str, Any] = {"ioc": ioc, "type": ioc_type}
        if tags:
            payload["tags"] = tags

        return await self._post("/api/ioc/submit", data=payload)
