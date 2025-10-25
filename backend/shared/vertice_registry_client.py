"""
Vértice Service Registry Client - Auto-Registration Library

This library provides a simple interface for services to register themselves
with the Vértice Service Registry (RSS) automatically on startup.

Usage Example:
    ```python
    from shared.vertice_registry_client import RegistryClient
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Auto-register on startup
        await RegistryClient.register(
            service_name="osint_service",
            port=8049,
            health_endpoint="/health"
        )

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            RegistryClient.heartbeat_loop("osint_service")
        )

        yield

        # Cleanup on shutdown
        heartbeat_task.cancel()
        await RegistryClient.deregister("osint_service")

    app = FastAPI(lifespan=lifespan)
    ```

Author: Vértice Team
"""

import asyncio
import logging
import os
import socket
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Registry configuration
DEFAULT_REGISTRY_TOKEN = "titanium-registry-token"
REGISTRY_URL = os.getenv("VERTICE_REGISTRY_URL", "http://vertice-register-lb:80")
REGISTRY_AUTH_TOKEN = (
    os.getenv("VERTICE_REGISTRY_TOKEN")
    or os.getenv("REGISTRY_AUTH_TOKEN")
    or DEFAULT_REGISTRY_TOKEN
)
HEARTBEAT_INTERVAL = int(os.getenv("REGISTRY_HEARTBEAT_INTERVAL", "30"))  # seconds
REGISTRATION_TIMEOUT = int(os.getenv("REGISTRY_TIMEOUT", "5"))  # seconds
REGISTRY_TOKEN_HEADER = "X-Registry-Token"

if REGISTRY_AUTH_TOKEN == DEFAULT_REGISTRY_TOKEN:
    logger.warning(
        "Using default registry token. Set VERTICE_REGISTRY_TOKEN to a unique value for production deployments."
    )


class RegistryClient:
    """Client for interacting with Vértice Service Registry."""

    _http_client: Optional[httpx.AsyncClient] = None

    @classmethod
    def _get_client(cls) -> httpx.AsyncClient:
        """Get or create HTTP client (singleton)."""
        if cls._http_client is None or cls._http_client.is_closed:
            cls._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(REGISTRATION_TIMEOUT),
                follow_redirects=True
            )
        return cls._http_client

    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        """Return default headers for registry communication."""
        if REGISTRY_AUTH_TOKEN:
            return {REGISTRY_TOKEN_HEADER: REGISTRY_AUTH_TOKEN}
        return {}

    @classmethod
    async def close(cls):
        """Close HTTP client."""
        if cls._http_client and not cls._http_client.is_closed:
            await cls._http_client.aclose()
            cls._http_client = None

    @classmethod
    def _get_hostname(cls) -> str:
        """Get container/host name."""
        return socket.gethostname()

    @classmethod
    def _build_endpoint(cls, port: int) -> str:
        """Build service endpoint URL."""
        hostname = cls._get_hostname()
        return f"http://{hostname}:{port}"

    @classmethod
    async def register(
        cls,
        service_name: str,
        port: int,
        health_endpoint: str = "/health",
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Register service with the registry.

        Args:
            service_name: Unique service identifier
            port: Service port number
            health_endpoint: Health check endpoint path
            metadata: Optional service metadata

        Returns:
            True if registration succeeded, False otherwise
        """
        endpoint = cls._build_endpoint(port)

        payload = {
            "service_name": service_name,
            "endpoint": endpoint,
            "health_endpoint": health_endpoint,
            "metadata": metadata or {}
        }

        try:
            client = cls._get_client()
            response = await client.post(
                f"{REGISTRY_URL}/register",
                json=payload,
                headers=cls._get_headers()
            )
            response.raise_for_status()

            logger.info(
                f"✅ Service '{service_name}' registered with registry: {endpoint}"
            )
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ Failed to register '{service_name}': "
                f"HTTP {e.response.status_code} - {e.response.text}"
            )
            return False

        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(
                f"❌ Failed to register '{service_name}': "
                f"Registry unreachable - {type(e).__name__}: {e}"
            )
            logger.warning(
                "Service will operate WITHOUT registry (standalone mode)"
            )
            return False

        except Exception as e:
            logger.error(
                f"❌ Unexpected error registering '{service_name}': {e}"
            )
            return False

    @classmethod
    async def heartbeat(cls, service_name: str) -> bool:
        """
        Send heartbeat to refresh service TTL.

        Args:
            service_name: Service identifier

        Returns:
            True if heartbeat succeeded, False otherwise
        """
        payload = {"service_name": service_name}

        try:
            client = cls._get_client()
            response = await client.post(
                f"{REGISTRY_URL}/heartbeat",
                json=payload,
                headers=cls._get_headers()
            )
            response.raise_for_status()
            logger.debug(f"💓 Heartbeat sent for '{service_name}'")
            return True

        except Exception as e:
            logger.warning(f"Heartbeat failed for '{service_name}': {e}")
            return False

    @classmethod
    async def heartbeat_loop(cls, service_name: str):
        """
        Background task to send periodic heartbeats.

        Args:
            service_name: Service identifier
        """
        logger.info(
            f"Starting heartbeat loop for '{service_name}' "
            f"(interval={HEARTBEAT_INTERVAL}s)"
        )

        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                success = await cls.heartbeat(service_name)

                if not success:
                    logger.warning(
                        f"Heartbeat failed for '{service_name}', "
                        "service may be deregistered soon"
                    )

            except asyncio.CancelledError:
                logger.info(f"Heartbeat loop cancelled for '{service_name}'")
                break

            except Exception as e:
                logger.error(f"Heartbeat loop error for '{service_name}': {e}")
                # Continue loop even on error

    @classmethod
    async def deregister(cls, service_name: str) -> bool:
        """
        Deregister service from registry.

        Args:
            service_name: Service identifier

        Returns:
            True if deregistration succeeded, False otherwise
        """
        try:
            client = cls._get_client()
            response = await client.delete(
                f"{REGISTRY_URL}/deregister/{service_name}",
                headers=cls._get_headers()
            )
            response.raise_for_status()

            logger.info(f"✅ Service '{service_name}' deregistered from registry")
            return True

        except Exception as e:
            logger.warning(f"Failed to deregister '{service_name}': {e}")
            return False

    @classmethod
    async def get_service(cls, service_name: str) -> Optional[Dict]:
        """
        Look up a service in the registry.

        Args:
            service_name: Service identifier

        Returns:
            Service information dict or None if not found
        """
        try:
            client = cls._get_client()
            response = await client.get(
                f"{REGISTRY_URL}/services/{service_name}",
                headers=cls._get_headers()
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Service '{service_name}' not found in registry")
            else:
                logger.error(f"Failed to lookup '{service_name}': HTTP {e.response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Failed to lookup '{service_name}': {e}")
            return None

    @classmethod
    async def list_services(cls) -> list:
        """
        List all registered services.

        Returns:
            List of service names
        """
        try:
            client = cls._get_client()
            response = await client.get(
                f"{REGISTRY_URL}/services",
                headers=cls._get_headers()
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []


# Convenience function for FastAPI lifespan
async def auto_register_service(
    service_name: str,
    port: int,
    health_endpoint: str = "/health",
    metadata: Optional[Dict[str, str]] = None
) -> asyncio.Task:
    """
    Convenience function to register service and start heartbeat task.

    This function combines registration + heartbeat loop in one call.

    Args:
        service_name: Service identifier
        port: Service port
        health_endpoint: Health check path
        metadata: Optional metadata

    Returns:
        Heartbeat task (should be cancelled on shutdown)

    Example:
        ```python
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            heartbeat_task = await auto_register_service(
                service_name="my_service",
                port=8000
            )
            yield
            heartbeat_task.cancel()
            await RegistryClient.deregister("my_service")
        ```
    """
    # Register service
    await RegistryClient.register(
        service_name=service_name,
        port=port,
        health_endpoint=health_endpoint,
        metadata=metadata
    )

    # Start heartbeat loop
    heartbeat_task = asyncio.create_task(
        RegistryClient.heartbeat_loop(service_name)
    )

    return heartbeat_task
