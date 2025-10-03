"""
Network Monitor Connector - Real implementation
Connects to network_monitor_service backend
"""

import httpx
import os
from typing import Dict, Any, Optional
from .base import BaseConnector


class NetworkMonitorConnector(BaseConnector):
    """Connector for Network Monitor service."""

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = os.getenv("NETWORK_MONITOR_SERVICE_URL", "http://localhost:8009")
        super().__init__(service_name="Network Monitor", base_url=base_url)

    async def health_check(self) -> bool:
        """
        Checks if the Network Monitor service is online and operational.

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

    async def start_monitoring(
        self, interface: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Start network monitoring session.

        Args:
            interface: Network interface to monitor
            filters: Packet filters to apply

        Returns:
            Optional[Dict[str, Any]]: A dictionary with session info, or None on failure.
        """
        payload: Dict[str, Any] = {}
        if interface:
            payload["interface"] = interface
        if filters:
            payload["filters"] = filters
        return await self._post("/monitor/start", data=payload)

    async def stop_monitoring(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Stop monitoring session."""
        return await self._post(f"/monitor/stop/{session_id}")

    async def get_events(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get network events.

        Args:
            session_id: Monitoring session ID (if active)
            limit: Maximum events to return
            event_type: Filter by event type

        Returns:
            Optional[Dict[str, Any]]: A dictionary with network events, or None on failure.
        """
        params: Dict[str, Any] = {"limit": limit}
        if session_id:
            params["session_id"] = session_id
        if event_type:
            params["event_type"] = event_type
        return await self._get("/events", params=params)

    async def get_statistics(self) -> Optional[Dict[str, Any]]:
        """Get network monitoring statistics."""
        return await self._get("/statistics")

    async def get_alerts(
        self, severity: Optional[str] = None, limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get network alerts.

        Args:
            severity: Filter by severity (critical, high, medium, low)
            limit: Maximum alerts to return

        Returns:
            Optional[Dict[str, Any]]: A dictionary with network alerts, or None on failure.
        """
        params: Dict[str, Any] = {"limit": limit}
        if severity:
            params["severity"] = severity
        return await self._get("/alerts", params=params)

    async def block_ip(
        self, ip_address: str, duration: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Block an IP address.

        Args:
            ip_address: IP to block
            duration: Block duration in seconds (None = permanent)

        Returns:
            Optional[Dict[str, Any]]: A dictionary with block confirmation, or None on failure.
        """
        payload: Dict[str, Any] = {"ip_address": ip_address}
        if duration:
            payload["duration"] = duration
        return await self._post("/block", data=payload)
