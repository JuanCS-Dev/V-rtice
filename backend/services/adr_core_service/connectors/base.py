"""Base Connector module for the ADR Core Service.

This module defines the abstract base class `BaseConnector` that all specific
connectors must inherit from. It provides a common interface for connecting
to external services, handling configuration, and making HTTP requests.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base class for all external service connectors.

    This class provides a standardized structure for connectors that integrate
    with external APIs. It includes methods for connection management, health
    checks, and a generic HTTP request handler.

    Subclasses must implement the `health_check` and `enrich` methods.

    Attributes:
        config (Dict[str, Any]): The configuration dictionary for the connector.
        endpoint (str): The base URL of the external service.
        timeout (float): The timeout for HTTP requests in seconds.
        api_key (Optional[str]): The API key for authentication, if required.
        enabled (bool): A flag to enable or disable the connector.
        client (Optional[httpx.AsyncClient]): The HTTP client for making requests.
        connected (bool): The current connection status.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initializes the BaseConnector with its configuration.

        Args:
            config (Dict[str, Any]): A dictionary containing configuration such as
                `endpoint`, `timeout`, `api_key`, and `enabled`.
        """
        self.config = config
        self.endpoint = config.get('endpoint')
        self.timeout = config.get('timeout', 30.0)
        self.api_key = config.get('api_key')
        self.enabled = config.get('enabled', True)

        self.client: Optional[httpx.AsyncClient] = None
        self.connected = False

        logger.info(f"Initialized {self.__class__.__name__} for endpoint: {self.endpoint}")

    async def connect(self):
        """Establishes and verifies the connection to the external service.

        If the connector is enabled, it creates an `httpx.AsyncClient` and performs
        an initial health check to verify connectivity.
        """
        if not self.enabled:
            logger.warning(f"{self.__class__.__name__} is disabled and will not connect.")
            return

        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"

            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers
            )

            # Perform an initial health check to confirm connectivity.
            await self.health_check()
            self.connected = True

            logger.info(f"Successfully connected to {self.__class__.__name__}.")
        except Exception as e:
            logger.error(f"Failed to connect to {self.__class__.__name__}: {e}")
            self.connected = False
            if self.client:
                await self.client.aclose()
                self.client = None

    async def disconnect(self):
        """Closes the connection and cleans up resources.

        This method gracefully closes the `httpx.AsyncClient` if it exists.
        """
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
        logger.info(f"Disconnected from {self.__class__.__name__}.")

    @abstractmethod
    async def health_check(self) -> bool:
        """Performs a health check of the external service.

        This method must be implemented by subclasses to verify that the
        external service is reachable and operational.

        Returns:
            bool: True if the service is healthy, False otherwise.
        """
        pass

    @abstractmethod
    async def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches detection data with information from the external service.

        This is the primary method for data enrichment and must be implemented
        by all concrete connector subclasses.

        Args:
            data (Dict[str, Any]): The raw detection or threat data to be enriched.

        Returns:
            Dict[str, Any]: The enriched data with additional context.
        """
        pass

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Makes a generic HTTP request to the external service.

        This helper method handles GET, POST, PUT, and DELETE requests, including
        error handling and response parsing.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            endpoint (str): The API endpoint path to append to the base URL.
            data (Optional[Dict[str, Any]], optional): The request body for POST/PUT.
                Defaults to None.
            params (Optional[Dict[str, Any]], optional): URL query parameters.
                Defaults to None.

        Returns:
            Optional[Dict[str, Any]]: The JSON response as a dictionary, or None
                if the request fails or returns a non-2xx status code.
        """
        if not self.client or not self.connected:
            logger.error(f"{self.__class__.__name__} is not connected. Cannot make request.")
            return None

        try:
            url = f"{self.endpoint}{endpoint}"

            response = await self.client.request(method.upper(), url, json=data, params=params)

            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"{self.__class__.__name__} request failed with status {e.response.status_code}: "
                f"{e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logger.error(f"{self.__class__.__name__} request error: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__} encountered an unexpected error: {e}")
            return None

    def __repr__(self):
        """Provides a string representation of the connector's state."""
        return (
            f"<{self.__class__.__name__} "
            f"endpoint={self.endpoint} "
            f"enabled={self.enabled} "
            f"connected={self.connected}>"
        )