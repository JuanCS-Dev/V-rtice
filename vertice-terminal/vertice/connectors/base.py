import httpx
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """
    Base class for all service connectors in the Vertice CLI.
    Provides asynchronous HTTP request methods and enforces a health check.
    """

    def __init__(self, service_name: str, base_url: str, timeout: int = 10):
        """
        Initializes the BaseConnector with a service name, base URL and timeout.

        Args:
            service_name (str): The name of the service (for error messages).
            base_url (str): The base URL of the microservice.
            timeout (int): The default timeout for HTTP requests in seconds.
        """
        self.service_name = service_name
        self.base_url = base_url
        # Using AsyncClient for asynchronous operations as per blueprint
        self.client = httpx.AsyncClient(timeout=timeout)

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Abstract method to check if the connected service is online and operational.
        Must be implemented by concrete connector classes.

        Returns:
            bool: True if the service is healthy, False otherwise.
        """
        pass

    async def _get(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Performs an asynchronous GET request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint relative to the base_url.
            **kwargs: Additional keyword arguments to pass to httpx.AsyncClient.get().

        Returns:
            Optional[Dict[str, Any]]: The JSON response from the API, or None if an error occurred.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()  # Raises HTTPStatusError for bad responses (4xx or 5xx)
            return response.json()
        except httpx.RequestError as exc:
            # More specific error handling for network issues
            print(f"Erro de rede ao acessar {url}: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            # Error handling for bad HTTP responses
            print(
                f"Erro da API em {url} - Status {exc.response.status_code}: {exc.response.text}"
            )
            return None
        except Exception as exc:
            # Generic error handling
            print(f"Erro inesperado ao fazer GET para {url}: {exc}")
            return None

    async def _post(
        self, endpoint: str, data: Optional[Dict] = None, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Performs an asynchronous POST request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint relative to the base_url.
            data (Optional[Dict]): The JSON payload to send with the request.
            **kwargs: Additional keyword arguments to pass to httpx.AsyncClient.post().

        Returns:
            Optional[Dict[str, Any]]: The JSON response from the API, or None if an error occurred.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.post(url, json=data, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            print(f"Erro de rede ao acessar {url}: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            print(
                f"Erro da API em {url} - Status {exc.response.status_code}: {exc.response.text}"
            )
            return None
        except Exception as exc:
            print(f"Erro inesperado ao fazer POST para {url}: {exc}")
            return None

    async def close(self):
        """
        Closes the underlying HTTP client session.
        Should be called when the connector is no longer needed.
        """
        await self.client.aclose()
