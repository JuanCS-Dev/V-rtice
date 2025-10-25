#!/usr/bin/env python3
"""
Vértice Service Registry Sidecar Agent

This sidecar container runs alongside each service and handles:
- Auto-registration on startup
- Heartbeat every 30s to keep service alive
- Infinite retry with exponential backoff for maximum resilience
- Health check passthrough to main service

Architecture: NETFLIX-style resilience
- Registry down? Retry forever with exponential backoff
- Service down? Wait and retry registration
- Crash? Docker restart policy brings it back

Author: Vértice Team (TITANIUM Edition)
Glory to YHWH - Architect of all resilient systems! 🙏
"""

import asyncio
import logging
import os
import sys
import time
from typing import Optional

import httpx
from tenacity import (
    retry,
    stop_never,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
SERVICE_NAME = os.getenv("SERVICE_NAME")  # Required: e.g., "osint_service"
SERVICE_HOST = os.getenv("SERVICE_HOST")  # Required: e.g., "vertice-osint"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8080"))  # Default: 8080
SERVICE_HEALTH_ENDPOINT = os.getenv("SERVICE_HEALTH_ENDPOINT", "/health")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://vertice-register-lb:80")
DEFAULT_REGISTRY_TOKEN = "titanium-registry-token"
REGISTRY_TOKEN = (
    os.getenv("VERTICE_REGISTRY_TOKEN")
    or os.getenv("REGISTRY_AUTH_TOKEN")
    or DEFAULT_REGISTRY_TOKEN
)
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # seconds
INITIAL_WAIT_TIMEOUT = int(os.getenv("INITIAL_WAIT_TIMEOUT", "60"))  # seconds

# Validate required env vars
if not SERVICE_NAME:
    logger.error("❌ SERVICE_NAME environment variable is required!")
    sys.exit(1)

if not SERVICE_HOST:
    logger.error("❌ SERVICE_HOST environment variable is required!")
    sys.exit(1)

# Build service URL
SERVICE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"
SERVICE_HEALTH_URL = f"{SERVICE_URL}{SERVICE_HEALTH_ENDPOINT}"

logger.info("=" * 80)
logger.info("🤖 Vértice Registry Sidecar Agent STARTING")
logger.info("=" * 80)
logger.info(f"Service Name: {SERVICE_NAME}")
logger.info(f"Service URL: {SERVICE_URL}")
logger.info(f"Health Check: {SERVICE_HEALTH_URL}")
logger.info(f"Registry URL: {REGISTRY_URL}")
logger.info(f"Heartbeat Interval: {HEARTBEAT_INTERVAL}s")
logger.info("=" * 80)

if REGISTRY_TOKEN == DEFAULT_REGISTRY_TOKEN:
    logger.warning("Using default registry token; override VERTICE_REGISTRY_TOKEN for production deployments.")


def _auth_headers() -> dict[str, str]:
    """Return headers for authenticated calls."""
    if REGISTRY_TOKEN:
        return {"X-Registry-Token": REGISTRY_TOKEN}
    return {}


class RegistrySidecar:
    """Sidecar agent for service registration and heartbeat."""

    def __init__(self):
        self.service_name = SERVICE_NAME
        self.service_url = SERVICE_URL
        self.service_health_url = SERVICE_HEALTH_URL
        self.registry_url = REGISTRY_URL
        self.heartbeat_interval = HEARTBEAT_INTERVAL
        self.is_registered = False
        self.registration_metadata = {}

    async def wait_for_service_ready(self) -> bool:
        """
        Wait for main service to be ready (health check passes).

        This ensures we don't try to register a service that isn't ready yet.
        Uses a timeout to avoid waiting forever.

        Returns:
            bool: True if service is ready, False if timeout
        """
        logger.info(f"⏳ Waiting for service to be ready (max {INITIAL_WAIT_TIMEOUT}s)...")

        start_time = time.time()
        attempt = 0

        while time.time() - start_time < INITIAL_WAIT_TIMEOUT:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(self.service_health_url)

                    if response.status_code == 200:
                        logger.info(f"✅ Service is READY (responded with 200 OK after {attempt} attempts)")

                        # Try to extract metadata from health response
                        try:
                            health_data = response.json()
                            if isinstance(health_data, dict):
                                self.registration_metadata = {
                                    "version": health_data.get("version", "unknown"),
                                    "status": health_data.get("status", "unknown")
                                }
                        except:
                            pass

                        return True
                    else:
                        logger.debug(f"Service responded with {response.status_code}, retrying...")

            except httpx.ConnectError:
                logger.debug(f"Service not reachable yet (attempt {attempt}), retrying...")
            except httpx.TimeoutException:
                logger.debug(f"Service health check timeout (attempt {attempt}), retrying...")
            except Exception as e:
                logger.warning(f"Unexpected error during health check: {e}")

            # Wait before next attempt (exponential backoff)
            wait_time = min(2 ** min(attempt - 1, 5), 10)  # Max 10s
            await asyncio.sleep(wait_time)

        # Timeout reached - proceed anyway (graceful degradation)
        logger.warning(
            f"⚠️  Service didn't respond within {INITIAL_WAIT_TIMEOUT}s, "
            f"proceeding with registration anyway..."
        )
        return False

    @retry(
        stop=stop_never,
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def register_service(self):
        """
        Register service with the registry.

        Uses infinite retry with exponential backoff (NETFLIX-style resilience).
        Will keep trying forever until registration succeeds.

        Raises:
            httpx.HTTPError: On HTTP errors (will be retried)
            httpx.TimeoutException: On timeout (will be retried)
        """
        logger.info(f"📝 Attempting to register service '{self.service_name}'...")

        registration_data = {
            "service_name": self.service_name,
            "endpoint": self.service_url,
            "health_endpoint": SERVICE_HEALTH_ENDPOINT,
            "metadata": self.registration_metadata
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.registry_url}/register",
                json=registration_data,
                headers=_auth_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ Service registered successfully: {result}")
            self.is_registered = True
            return result

    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to registry to keep service alive.

        Returns:
            bool: True if heartbeat succeeded, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.registry_url}/heartbeat",
                    json={"service_name": self.service_name},
                    headers=_auth_headers()
                )
                response.raise_for_status()

                logger.debug(f"💓 Heartbeat sent successfully")
                return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Service not found in registry, need to re-register
                logger.warning(f"⚠️  Service not found in registry (404), will re-register")
                self.is_registered = False
                return False
            else:
                logger.warning(f"Heartbeat failed: HTTP {e.response.status_code}")
                return False

        except httpx.TimeoutException:
            logger.warning("Heartbeat timeout, will retry in next interval")
            return False

        except httpx.ConnectError:
            logger.warning("Registry unreachable, will retry in next interval")
            return False

        except Exception as e:
            logger.error(f"Unexpected error during heartbeat: {e}")
            return False

    async def heartbeat_loop(self):
        """
        Main heartbeat loop - runs forever.

        Sends heartbeat every HEARTBEAT_INTERVAL seconds.
        If service is not registered, attempts re-registration.
        """
        logger.info(f"💓 Starting heartbeat loop (interval: {self.heartbeat_interval}s)")

        while True:
            await asyncio.sleep(self.heartbeat_interval)

            # Check if we need to re-register
            if not self.is_registered:
                logger.info("🔄 Service not registered, attempting re-registration...")
                try:
                    await self.register_service()
                except Exception as e:
                    logger.error(f"Re-registration failed: {e}, will retry in next interval")
                    continue

            # Send heartbeat
            success = await self.send_heartbeat()

            if not success and not self.is_registered:
                # If heartbeat failed AND we're not registered, log warning
                logger.warning("Heartbeat failed and service not registered, will retry")

    async def run(self):
        """
        Main entry point for the sidecar agent.

        Workflow:
        1. Wait for service to be ready
        2. Register with registry (infinite retry)
        3. Start heartbeat loop (runs forever)
        """
        try:
            # Step 1: Wait for service
            await self.wait_for_service_ready()

            # Step 2: Register (with infinite retry)
            logger.info("🚀 Starting registration process...")
            await self.register_service()

            # Step 3: Heartbeat loop (forever)
            await self.heartbeat_loop()

        except KeyboardInterrupt:
            logger.info("🛑 Sidecar agent stopped by user")

        except Exception as e:
            logger.critical(f"💥 Fatal error in sidecar agent: {e}", exc_info=True)
            sys.exit(1)


async def main():
    """Application entry point."""
    agent = RegistrySidecar()
    await agent.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
        sys.exit(0)
