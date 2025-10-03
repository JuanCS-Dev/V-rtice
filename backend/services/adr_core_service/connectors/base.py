"""
Base Connector - Abstract base for all ADR connectors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base class for ADR connectors

    All connectors must implement:
    - connect(): Establish connection to external service
    - disconnect(): Clean up resources
    - health_check(): Verify service is reachable
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connector with configuration

        Args:
            config: Configuration dict containing:
                - endpoint: Service endpoint URL
                - timeout: Request timeout in seconds
                - api_key: Optional API key
                - enabled: Whether connector is enabled
        """
        self.config = config
        self.endpoint = config.get('endpoint')
        self.timeout = config.get('timeout', 30.0)
        self.api_key = config.get('api_key')
        self.enabled = config.get('enabled', True)

        self.client: Optional[httpx.AsyncClient] = None
        self.connected = False

        logger.info(f"Initialized {self.__class__.__name__} for {self.endpoint}")

    async def connect(self):
        """Establish connection to external service"""
        if not self.enabled:
            logger.warning(f"{self.__class__.__name__} is disabled")
            return

        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"

            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers
            )

            # Verify connection
            await self.health_check()
            self.connected = True

            logger.info(f"✅ Connected to {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"❌ Failed to connect {self.__class__.__name__}: {e}")
            self.connected = False

    async def disconnect(self):
        """Clean up resources and close connections"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
        logger.info(f"Disconnected from {self.__class__.__name__}")

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if external service is reachable

        Returns:
            True if service is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich detection/threat data with external intelligence

        Args:
            data: Raw detection/threat data

        Returns:
            Enriched data with additional context
        """
        pass

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to external service

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response data or None if failed
        """
        if not self.client:
            logger.error(f"{self.__class__.__name__} not connected")
            return None

        try:
            url = f"{self.endpoint}{endpoint}"

            if method.upper() == 'GET':
                response = await self.client.get(url, params=params)
            elif method.upper() == 'POST':
                response = await self.client.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = await self.client.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = await self.client.delete(url, params=params)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.warning(
                    f"{self.__class__.__name__} request failed: "
                    f"{response.status_code} {response.text}"
                )
                return None

        except httpx.RequestError as e:
            logger.error(f"{self.__class__.__name__} request error: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__} unexpected error: {e}")
            return None

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"endpoint={self.endpoint} "
            f"enabled={self.enabled} "
            f"connected={self.connected}>"
        )
