"""
Nmap Service Connector - Real implementation
Connects to nmap_service backend for network scanning
"""
import httpx
from typing import Dict, Any, Optional
from .base import BaseConnector


class NmapConnector(BaseConnector):
    """Connector for Nmap scanning service."""

    def __init__(self, base_url: str = "http://localhost:8010"):
        super().__init__(base_url)
        self.service_name = "Nmap Service"

    async def scan_ports(
        self,
        target: str,
        ports: Optional[str] = None,
        scan_type: str = "quick"
    ) -> Dict[str, Any]:
        """
        Perform port scan on target.

        Args:
            target: IP or hostname to scan
            ports: Port range (e.g., "1-1000", "22,80,443")
            scan_type: Type of scan (quick, full, stealth)

        Returns:
            Dict with scan results
        """
        payload = {
            "target": target,
            "scan_type": scan_type
        }
        if ports:
            payload["ports"] = ports

        response = await self.client.post("/scan/ports", json=payload, timeout=60.0)
        response.raise_for_status()
        return response.json()

    async def scan_nmap(
        self,
        target: str,
        arguments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform custom nmap scan with arguments.

        Args:
            target: IP or hostname to scan
            arguments: Custom nmap arguments (e.g., "-sV -sC")

        Returns:
            Dict with scan results
        """
        payload = {
            "target": target
        }
        if arguments:
            payload["arguments"] = arguments

        response = await self.client.post("/scan/nmap", json=payload, timeout=120.0)
        response.raise_for_status()
        return response.json()

    async def scan_network(
        self,
        network: str = "192.168.1.0/24"
    ) -> Dict[str, Any]:
        """
        Perform network discovery scan.

        Args:
            network: Network CIDR (e.g., "192.168.1.0/24")

        Returns:
            Dict with discovered hosts
        """
        payload = {"network": network}
        response = await self.client.post("/scan/network", json=payload, timeout=180.0)
        response.raise_for_status()
        return response.json()

    async def get_scan_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get scan history."""
        response = await self.client.get(f"/scan/history?limit={limit}")
        response.raise_for_status()
        return response.json()
