from .base import BaseConnector
from typing import Dict, Any
import httpx

class ThreatIntelConnector(BaseConnector):
    """Conector para Threat Intel Service (porta 8013)"""

    def __init__(self):
        super().__init__(base_url="http://localhost:8013")

    async def health_check(self) -> bool:
        try:
            data = await self._get("/")
            return data.get("status") == "operational"
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during health check: {e}")
            return False
        except httpx.RequestError as e:
            print(f"Network error during health check: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during health check: {e}")
            return False

    async def lookup_threat(self, indicator: str) -> Dict[str, Any]:
        """Lookup threat indicator."""
        return await self._post("/api/threat/lookup", json={"indicator": indicator})