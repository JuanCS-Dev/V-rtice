"""
Nmap Service Connector - Real implementation
Connects to nmap_service backend for network scanning
"""

import httpx
import os
from typing import Dict, Any, Optional
from .base import BaseConnector


class NmapConnector(BaseConnector):
    """Connector for Nmap scanning service."""

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = os.getenv("NMAP_SERVICE_URL", "http://localhost:8010")
        super().__init__(service_name="Nmap Service", base_url=base_url)

    async def health_check(self) -> bool:
        """
        Checks if the Nmap service is online and operational.

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

    async def scan_ports(
        self, target: str, ports: Optional[str] = None, scan_type: str = "quick"
    ) -> Optional[Dict[str, Any]]:
        """
        Perform port scan on target.

        Args:
            target: IP or hostname to scan
            ports: Port range (e.g., "1-1000", "22,80,443")
            scan_type: Type of scan (quick, full, stealth)

        Returns:
            Optional[Dict[str, Any]]: A dictionary with scan results, or None on failure.
        """
        payload = {"target": target, "scan_type": scan_type}
        if ports:
            payload["ports"] = ports
        return await self._post("/scan/ports", data=payload, timeout=60.0)

    async def scan_nmap(
        self, target: str, arguments: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Perform custom nmap scan with arguments.

        Args:
            target: IP or hostname to scan
            arguments: Custom nmap arguments (e.g., "-sV -sC")

        Returns:
            Optional[Dict[str, Any]]: A dictionary with scan results, or None on failure.
        """
        payload = {"target": target}
        if arguments:
            payload["arguments"] = arguments
        return await self._post("/scan/nmap", data=payload, timeout=120.0)

    async def scan_network(
        self, network: str = "192.168.1.0/24"
    ) -> Optional[Dict[str, Any]]:
        """
        Perform network discovery scan.

        Args:
            network: Network CIDR (e.g., "192.168.1.0/24")

        Returns:
            Optional[Dict[str, Any]]: A dictionary with discovered hosts, or None on failure.
        """
        payload = {"network": network}
        return await self._post("/scan/network", data=payload, timeout=180.0)

    async def get_scan_history(self, limit: int = 10) -> Optional[Dict[str, Any]]:
        """Get scan history."""
        return await self._get(f"/scan/history?limit={limit}")
