from .base import BaseConnector
from typing import Dict, Any
import httpx
from ..utils.config import config

class IPIntelConnector(BaseConnector):
    """Conector para IP Intelligence Service"""

    def __init__(self):
        base_url = config.get("services.ip_intelligence.url", "http://localhost:8004")
        super().__init__(service_name="IP Intelligence", base_url=base_url)

    async def health_check(self) -> bool:
        try:
            data = await self._get("/")
            return data.get("status") == "operational"
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors specifically
            print(f"HTTP error during health check: {e}")
            return False
        except httpx.RequestError as e:
            # Handle network errors specifically
            print(f"Network error during health check: {e}")
            return False
        except Exception as e:
            # Catch any other unexpected errors
            print(f"An unexpected error occurred during health check: {e}")
            return False

    async def analyze_ip(self, ip: str) -> Dict[str, Any]:
        """Analisa IP"""
        return await self._post("/api/ip/analyze", json={"ip": ip})

    async def get_my_ip(self) -> str:
        """Detecta IP público"""
        data = await self._get("/api/ip/my-ip")
        return data.get("detected_ip")

    async def analyze_my_ip(self) -> Dict[str, Any]:
        """Detecta e analisa IP público"""
        return await self._post("/api/ip/analyze-my-ip")