"""HTTP client for inter-service communication."""

from collections.abc import Mapping
from typing import Any

import httpx
from vertice_core import ServiceUnavailableError


class ServiceClient:
    """Async HTTP client for calling other Vértice services."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "ServiceClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"X-API-Key": self.api_key} if self.api_key else {},
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()

    async def get(
        self, path: str, **kwargs: Mapping[str, Any] | str | int | bool
    ) -> dict[str, Any]:  # pragma: no cover
        """GET request."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with.")

        try:
            response = await self._client.get(path, **kwargs)  # type: ignore[arg-type]
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                raise ServiceUnavailableError(self.base_url, str(e)) from e
            raise
        except httpx.RequestError as e:
            raise ServiceUnavailableError(self.base_url, str(e)) from e

    async def post(
        self, path: str, **kwargs: Mapping[str, Any] | str | int | bool
    ) -> dict[str, Any]:  # pragma: no cover
        """POST request."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with.")

        try:
            response = await self._client.post(path, **kwargs)  # type: ignore[arg-type]
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                raise ServiceUnavailableError(self.base_url, str(e)) from e
            raise
        except httpx.RequestError as e:
            raise ServiceUnavailableError(self.base_url, str(e)) from e
