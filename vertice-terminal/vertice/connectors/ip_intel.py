from .base import BaseConnector
from typing import Dict, Any, Optional
import httpx
from ..utils.config import config
import ipaddress


class IPIntelConnector(BaseConnector):
    """Connector for the IP Intelligence Service."""

    def __init__(self):
        """
        Initializes the IPIntelConnector.
        """
        base_url = config.get("services.ip_intelligence.url", "http://localhost:8004")
        super().__init__(service_name="IP Intelligence", base_url=base_url)

    async def health_check(self) -> bool:
        """
        Checks if the IP Intelligence service is online and operational.

        Returns:
            bool: True if the service is healthy, False otherwise.
        """
        data = await self._get("/")
        if data:
            return data.get("status") == "operational"
        return False

    async def analyze_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes a given IP address for threat intelligence.

        Args:
            ip (str): The IP address to analyze.

        Raises:
            ValueError: If the provided string is not a valid IP address.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the analysis results, or None on failure.
        """
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError(f"'{ip}' is not a valid IP address.")
        return await self._post("/api/ip/analyze", data={"ip": ip})

    async def get_my_ip(self) -> Optional[str]:
        """
        Detects the public IP address of the client.

        Returns:
            Optional[str]: The detected public IP address, or None on failure.
        """
        data = await self._get("/api/ip/my-ip")
        if data:
            return data.get("detected_ip")
        return None

    async def analyze_my_ip(self) -> Optional[Dict[str, Any]]:
        """
        Detects and analyzes the client's public IP address.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the analysis results, or None on failure.
        """
        return await self._post("/api/ip/analyze-my-ip")
