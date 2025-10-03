"""
Threat Intelligence Connector - PRODUCTION READY
Connects to threat_intel_service backend (port 8013)
"""
import httpx
from typing import Dict, Any, List, Optional
from .base import BaseConnector


class ThreatIntelConnector(BaseConnector):
    """Connector for Threat Intelligence Service."""

    def __init__(self, base_url: str = "http://localhost:8013"):
        super().__init__(base_url)
        self.service_name = "Threat Intelligence"

    async def search_threat(self, indicator: str) -> Dict[str, Any]:
        """
        Search for threat intelligence on an indicator.

        Args:
            indicator: IOC to search (IP, domain, hash, email, URL)

        Returns:
            Dict with threat intelligence data
        """
        payload = {"indicator": indicator}
        response = await self.client.post("/api/threat/search", json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()

    async def lookup_threat(self, indicator: str) -> Dict[str, Any]:
        """Lookup threat indicator (alias for search_threat)."""
        return await self.search_threat(indicator)

    async def get_threat_timeline(
        self,
        incident_id: str,
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """
        Get threat activity timeline for an incident.

        Args:
            incident_id: Incident identifier
            timeframe: Time window (1h, 24h, 7d, 30d)

        Returns:
            Dict with timeline events
        """
        params = {
            "incident_id": incident_id,
            "timeframe": timeframe
        }
        response = await self.client.get("/api/threat/timeline", params=params)
        response.raise_for_status()
        return response.json()

    async def pivot_analysis(
        self,
        ioc: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Perform pivot analysis on an IOC.

        Args:
            ioc: IOC to pivot on
            depth: Analysis depth (1-3)

        Returns:
            Dict with related entities
        """
        payload = {
            "ioc": ioc,
            "depth": min(depth, 3)  # Cap at 3
        }
        response = await self.client.post("/api/threat/pivot", json=payload, timeout=60.0)
        response.raise_for_status()
        return response.json()

    async def correlate_threats(
        self,
        ioc1: str,
        ioc2: str
    ) -> Dict[str, Any]:
        """
        Correlate two IOCs to find relationships.

        Args:
            ioc1: First IOC
            ioc2: Second IOC

        Returns:
            Dict with correlation data
        """
        payload = {
            "ioc1": ioc1,
            "ioc2": ioc2
        }
        response = await self.client.post("/api/threat/correlate", json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()

    async def get_threat_feeds(self) -> Dict[str, Any]:
        """Get active threat intelligence feeds."""
        response = await self.client.get("/api/feeds")
        response.raise_for_status()
        return response.json()

    async def submit_ioc(
        self,
        ioc: str,
        ioc_type: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Submit a new IOC to the threat database.

        Args:
            ioc: The indicator value
            ioc_type: Type (ip, domain, hash, email, url)
            tags: Optional tags for classification

        Returns:
            Dict with submission result
        """
        payload = {
            "ioc": ioc,
            "type": ioc_type
        }
        if tags:
            payload["tags"] = tags

        response = await self.client.post("/api/ioc/submit", json=payload)
        response.raise_for_status()
        return response.json()
