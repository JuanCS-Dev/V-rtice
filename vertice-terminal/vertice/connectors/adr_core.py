from .base import BaseConnector
from typing import Dict, Any
import httpx

class ADRCoreConnector(BaseConnector):
    """Conector para ADR Core Service (porta 8014)"""

    def __init__(self):
        super().__init__(base_url="http://localhost:8014")

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

    async def get_status(self) -> Dict[str, Any]:
        """Get ADR system status."""
        return await self._get("/api/adr/status")