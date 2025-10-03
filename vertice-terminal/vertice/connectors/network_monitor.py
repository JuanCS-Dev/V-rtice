"""
Network Monitor Connector - Real implementation
Connects to network_monitor_service backend
"""
import httpx
from typing import Dict, Any, List, Optional
from .base import BaseConnector


class NetworkMonitorConnector(BaseConnector):
    """Connector for Network Monitor service."""

    def __init__(self, base_url: str = "http://localhost:8009"):
        super().__init__(base_url)
        self.service_name = "Network Monitor"

    async def start_monitoring(
        self,
        interface: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start network monitoring session.

        Args:
            interface: Network interface to monitor
            filters: Packet filters to apply

        Returns:
            Dict with session info
        """
        payload = {}
        if interface:
            payload["interface"] = interface
        if filters:
            payload["filters"] = filters

        response = await self.client.post("/monitor/start", json=payload)
        response.raise_for_status()
        return response.json()

    async def stop_monitoring(self, session_id: str) -> Dict[str, Any]:
        """Stop monitoring session."""
        response = await self.client.post(f"/monitor/stop/{session_id}")
        response.raise_for_status()
        return response.json()

    async def get_events(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
        event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get network events.

        Args:
            session_id: Monitoring session ID (if active)
            limit: Maximum events to return
            event_type: Filter by event type

        Returns:
            Dict with network events
        """
        params = {"limit": limit}
        if session_id:
            params["session_id"] = session_id
        if event_type:
            params["event_type"] = event_type

        response = await self.client.get("/events", params=params)
        response.raise_for_status()
        return response.json()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get network monitoring statistics."""
        response = await self.client.get("/statistics")
        response.raise_for_status()
        return response.json()

    async def get_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get network alerts.

        Args:
            severity: Filter by severity (critical, high, medium, low)
            limit: Maximum alerts to return

        Returns:
            Dict with network alerts
        """
        params = {"limit": limit}
        if severity:
            params["severity"] = severity

        response = await self.client.get("/alerts", params=params)
        response.raise_for_status()
        return response.json()

    async def block_ip(self, ip_address: str, duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Block an IP address.

        Args:
            ip_address: IP to block
            duration: Block duration in seconds (None = permanent)

        Returns:
            Dict with block confirmation
        """
        payload = {"ip_address": ip_address}
        if duration:
            payload["duration"] = duration

        response = await self.client.post("/block", json=payload)
        response.raise_for_status()
        return response.json()
