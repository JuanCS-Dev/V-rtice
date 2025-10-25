"""
Dynamic Service Router for API Gateway

This module provides dynamic service routing by querying the Vértice Service
Registry (RSS) in real-time instead of using hardcoded URLs.

Architecture:
- Query registry for service locations
- Local cache (5s TTL) for performance
- Fallback to environment variables for backward compatibility
- Circuit breaker for registry failures

Author: Vértice Team
"""

import logging
import os
import time
from typing import Dict, Optional

import httpx
from cachetools import TTLCache

# Import service name mapping for backward compatibility
try:
    from service_mapping import env_var_to_service_name, SERVICE_NAME_MAPPING
except ImportError:
    # Fallback if mapping file doesn't exist
    def env_var_to_service_name(name: str) -> str:
        return name.lower().replace("_url", "").replace("_endpoint", "") + "_service"
    SERVICE_NAME_MAPPING = {}

logger = logging.getLogger(__name__)

# Registry configuration
# NOTE: Use internal Docker port 80 (not 8888 which is external/host port)
DEFAULT_REGISTRY_TOKEN = "titanium-registry-token"
REGISTRY_URL = os.getenv("VERTICE_REGISTRY_URL", "http://vertice-register-lb:80")
REGISTRY_AUTH_TOKEN = (
    os.getenv("VERTICE_REGISTRY_TOKEN")
    or os.getenv("REGISTRY_AUTH_TOKEN")
    or DEFAULT_REGISTRY_TOKEN
)
CACHE_TTL_SECONDS = int(os.getenv("GATEWAY_CACHE_TTL", "5"))
REGISTRY_TIMEOUT = int(os.getenv("REGISTRY_TIMEOUT", "2"))
REGISTRY_HEADERS = {"X-Registry-Token": REGISTRY_AUTH_TOKEN} if REGISTRY_AUTH_TOKEN else {}

if REGISTRY_AUTH_TOKEN == DEFAULT_REGISTRY_TOKEN:
    logger.warning(
        "Gateway using default registry token. Override VERTICE_REGISTRY_TOKEN for hardened deployments."
    )

# Local cache for service lookups (5s TTL)
_service_cache = TTLCache(maxsize=200, ttl=CACHE_TTL_SECONDS)

# Circuit breaker state
_circuit_breaker_failures = 0
_circuit_breaker_threshold = 3
_circuit_breaker_open = False
_circuit_breaker_opened_at = 0
_circuit_breaker_timeout = 30  # seconds


class ServiceNotFoundError(Exception):
    """Raised when service cannot be found in registry or env vars."""
    pass


def normalize_service_name(service_name: str) -> str:
    """
    Normalize service name to registry format.

    Handles legacy env var names (e.g., "MAXIMUS_CORE_SERVICE_URL")
    and converts them to registry service names (e.g., "maximus_core_service").

    Args:
        service_name: Service name or env var name

    Returns:
        Normalized service name for registry lookup
    """
    # If it's already lowercase with underscores, likely already normalized
    if service_name.islower() and "_service" in service_name:
        return service_name

    # If it's uppercase (env var style), use mapping
    if service_name.isupper():
        try:
            return env_var_to_service_name(service_name)
        except Exception:
            # Fallback: lowercase + _service suffix
            return service_name.lower().replace("_url", "").replace("_endpoint", "") + "_service"

    # Default: assume it's already correct
    return service_name


async def get_service_url(service_name: str, use_cache: bool = True) -> str:
    """
    Get service URL dynamically from registry.

    Resolution order:
    1. Normalize service name (handle legacy env vars)
    2. Local cache (if enabled and fresh)
    3. Service Registry (RSS)
    4. Environment variable (fallback for backward compatibility)
    5. Raise ServiceNotFoundError

    Args:
        service_name: Service identifier (e.g., "osint_service", "MAXIMUS_CORE_SERVICE_URL")
        use_cache: Whether to use local cache (default: True)

    Returns:
        Service endpoint URL

    Raises:
        ServiceNotFoundError: If service cannot be located
    """
    global _circuit_breaker_failures, _circuit_breaker_open, _circuit_breaker_opened_at

    # Normalize service name (handles legacy env vars)
    service_name = normalize_service_name(service_name)

    # 1. Check local cache (fast path)
    if use_cache and service_name in _service_cache:
        url = _service_cache[service_name]
        logger.debug(f"Cache HIT: {service_name} -> {url}")
        return url

    # 2. Check if circuit breaker should transition to half-open
    if _circuit_breaker_open:
        elapsed = time.time() - _circuit_breaker_opened_at
        if elapsed > _circuit_breaker_timeout:
            logger.info("Circuit breaker transitioning to HALF_OPEN")
            _circuit_breaker_open = False
            _circuit_breaker_failures = 0
        else:
            logger.warning(f"Circuit breaker OPEN, using fallback for {service_name}")
            return _fallback_env_lookup(service_name)

    # 3. Query Service Registry
    try:
        async with httpx.AsyncClient(timeout=REGISTRY_TIMEOUT) as client:
            response = await client.get(
                f"{REGISTRY_URL}/services/{service_name}",
                headers=REGISTRY_HEADERS
            )
            response.raise_for_status()

            service_data = response.json()
            endpoint = service_data.get("endpoint")

            if not endpoint:
                raise ValueError("Service data missing 'endpoint' field")

            # Cache the result
            _service_cache[service_name] = endpoint

            # Reset circuit breaker on success
            if _circuit_breaker_failures > 0:
                logger.info(f"Registry query succeeded, resetting failures ({_circuit_breaker_failures} -> 0)")
                _circuit_breaker_failures = 0

            logger.debug(f"Registry query: {service_name} -> {endpoint}")
            return endpoint

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # Service not found in registry, try fallback
            logger.warning(f"Service '{service_name}' not found in registry (404)")
            return _fallback_env_lookup(service_name)
        else:
            # Other HTTP error, increment circuit breaker
            _on_registry_failure(f"HTTP {e.response.status_code}")
            return _fallback_env_lookup(service_name)

    except (httpx.RequestError, httpx.TimeoutException) as e:
        # Network error, increment circuit breaker
        _on_registry_failure(f"{type(e).__name__}")
        return _fallback_env_lookup(service_name)

    except Exception as e:
        logger.error(f"Unexpected error querying registry for '{service_name}': {e}")
        return _fallback_env_lookup(service_name)


def _on_registry_failure(error_type: str):
    """Handle registry failure and update circuit breaker."""
    global _circuit_breaker_failures, _circuit_breaker_open, _circuit_breaker_opened_at

    _circuit_breaker_failures += 1
    logger.warning(
        f"Registry failure ({_circuit_breaker_failures}/{_circuit_breaker_threshold}): {error_type}"
    )

    if _circuit_breaker_failures >= _circuit_breaker_threshold:
        if not _circuit_breaker_open:
            _circuit_breaker_open = True
            _circuit_breaker_opened_at = time.time()
            logger.critical(
                f"🔴 CIRCUIT BREAKER OPENED - Registry unreachable, "
                f"using env var fallbacks for {_circuit_breaker_timeout}s"
            )


def _fallback_env_lookup(service_name: str) -> str:
    """
    Fallback to environment variable lookup.

    This provides backward compatibility and degraded mode operation
    when the Service Registry is unavailable.

    Args:
        service_name: Service identifier

    Returns:
        Service URL from environment variable

    Raises:
        ServiceNotFoundError: If service not found in env vars either
    """
    # Try common naming conventions
    env_var_names = [
        f"{service_name.upper()}_URL",
        f"{service_name.upper()}_SERVICE_URL",
        f"{service_name.upper()}_ENDPOINT"
    ]

    for env_var in env_var_names:
        url = os.getenv(env_var)
        if url:
            logger.info(f"Fallback ENV VAR: {service_name} -> {url} (from {env_var})")
            # Cache the fallback URL too (with shorter TTL)
            _service_cache[service_name] = url
            return url

    # Last resort: raise error
    raise ServiceNotFoundError(
        f"Service '{service_name}' not found in registry or environment variables. "
        f"Tried env vars: {', '.join(env_var_names)}"
    )


def get_circuit_breaker_status() -> Dict:
    """Get current circuit breaker status (for monitoring/debugging)."""
    return {
        "open": _circuit_breaker_open,
        "failures": _circuit_breaker_failures,
        "threshold": _circuit_breaker_threshold,
        "opened_at": _circuit_breaker_opened_at if _circuit_breaker_open else None
    }


def get_cache_stats() -> Dict:
    """Get cache statistics (for monitoring/debugging)."""
    return {
        "size": len(_service_cache),
        "max_size": _service_cache.maxsize,
        "ttl": _service_cache.ttl,
        "services": list(_service_cache.keys())
    }


def clear_cache():
    """Clear the service cache (for testing/admin operations)."""
    _service_cache.clear()
    logger.info("Service cache cleared")
