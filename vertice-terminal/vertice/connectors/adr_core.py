from .base import BaseConnector
from typing import Dict, Any, Optional
import httpx
import os


class ADRCoreConnector(BaseConnector):
    """Connector for the ADR (Automated Detection and Response) Core Service."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initializes the ADRCoreConnector.

        Args:
            base_url (str, optional): The base URL of the service. Defaults to env var or localhost.
        """
        if base_url is None:
            base_url = os.getenv("ADR_CORE_SERVICE_URL", "http://localhost:8011")
        super().__init__(service_name="ADR Core", base_url=base_url)

    async def health_check(self) -> bool:
        """
        Checks if the ADR Core service is online and operational.

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

    async def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current operational status of the ADR system.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the system status.
        """
        return await self._get("/api/adr/status")
