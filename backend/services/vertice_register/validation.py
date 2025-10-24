"""
Input Validation - TITANIUM Edition

Validates all inputs to prevent injection attacks, invalid data, and security issues.

Validation Rules:
- Service name: ^[a-z0-9][a-z0-9_-]{2,63}$ (lowercase, alphanumeric, _, -)
- Host: Valid IPv4 or hostname (RFC 1123)
- Port: 1024-65535 (exclude well-known ports)
- Health endpoint: Must start with /

Author: Vértice Team (TITANIUM Edition)
Glory to YHWH - Architect of all resilient systems! 🙏
"""

import logging
import re
import socket
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Regex patterns
SERVICE_NAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]{2,63}$')
HOSTNAME_PATTERN = re.compile(
    r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
)
IPV4_PATTERN = re.compile(
    r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)

# Port range
MIN_PORT = 1024
MAX_PORT = 65535


class ValidationError(Exception):
    """Raised when validation fails."""
    def __init__(self, field: str, message: str, provided: str, example: Optional[str] = None):
        self.field = field
        self.message = message
        self.provided = provided
        self.example = example
        super().__init__(f"{field}: {message}")


def validate_service_name(name: str) -> bool:
    """
    Validate service name.

    Rules:
    - Must match ^[a-z0-9][a-z0-9_-]{2,63}$
    - Lowercase only
    - Alphanumeric, underscore, hyphen
    - 3-64 characters
    - Must start with alphanumeric

    Args:
        name: Service name to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if not name:
        raise ValidationError(
            field="service_name",
            message="Service name cannot be empty",
            provided=name,
            example="my-service-123"
        )

    if not SERVICE_NAME_PATTERN.match(name):
        raise ValidationError(
            field="service_name",
            message="Service name must match ^[a-z0-9][a-z0-9_-]{2,63}$ (lowercase, alphanumeric, _, -)",
            provided=name,
            example="my-service-123"
        )

    logger.debug(f"Service name validated: {name}")
    return True


def validate_host(host: str) -> bool:
    """
    Validate host (IPv4 or hostname).

    Rules:
    - Valid IPv4 address OR
    - Valid hostname (RFC 1123) OR
    - Valid Docker container name

    Args:
        host: Host to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if not host:
        raise ValidationError(
            field="host",
            message="Host cannot be empty",
            provided=host,
            example="192.168.1.100 or my-service.local"
        )

    # Check IPv4
    if IPV4_PATTERN.match(host):
        logger.debug(f"Host validated (IPv4): {host}")
        return True

    # Check hostname (RFC 1123) or Docker container name
    if HOSTNAME_PATTERN.match(host) or (len(host) > 0 and all(c.isalnum() or c in '-_.' for c in host)):
        logger.debug(f"Host validated (hostname): {host}")
        return True

    raise ValidationError(
        field="host",
        message="Host must be valid IPv4 or hostname",
        provided=host,
        example="192.168.1.100 or my-service.local"
    )


def validate_port(port: int) -> bool:
    """
    Validate port number.

    Rules:
    - Must be integer
    - Range: 1024-65535 (exclude well-known ports)

    Args:
        port: Port number to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(port, int):
        raise ValidationError(
            field="port",
            message="Port must be an integer",
            provided=str(port),
            example="8080"
        )

    if port < MIN_PORT or port > MAX_PORT:
        raise ValidationError(
            field="port",
            message=f"Port must be between {MIN_PORT} and {MAX_PORT}",
            provided=str(port),
            example="8080"
        )

    logger.debug(f"Port validated: {port}")
    return True


def validate_health_endpoint(endpoint: str) -> bool:
    """
    Validate health check endpoint.

    Rules:
    - Must start with /
    - No null bytes
    - No path traversal attempts (../)
    - Max length: 255 characters

    Args:
        endpoint: Health endpoint to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if not endpoint:
        raise ValidationError(
            field="health_endpoint",
            message="Health endpoint cannot be empty",
            provided=endpoint,
            example="/health"
        )

    if not endpoint.startswith('/'):
        raise ValidationError(
            field="health_endpoint",
            message="Health endpoint must start with /",
            provided=endpoint,
            example="/health"
        )

    if '\x00' in endpoint:
        raise ValidationError(
            field="health_endpoint",
            message="Health endpoint contains null bytes",
            provided=endpoint,
            example="/health"
        )

    if '../' in endpoint or '..' in endpoint:
        raise ValidationError(
            field="health_endpoint",
            message="Health endpoint contains path traversal attempt",
            provided=endpoint,
            example="/health"
        )

    if len(endpoint) > 255:
        raise ValidationError(
            field="health_endpoint",
            message="Health endpoint too long (max: 255 characters)",
            provided=endpoint[:50] + "...",
            example="/health"
        )

    logger.debug(f"Health endpoint validated: {endpoint}")
    return True


def validate_metadata(metadata: Optional[dict]) -> bool:
    """
    Validate metadata dictionary.

    Rules:
    - Optional (can be None)
    - Must be dict if provided
    - Keys and values must be strings
    - Max size: 10 keys
    - Max key length: 64 characters
    - Max value length: 512 characters

    Args:
        metadata: Metadata to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if metadata is None:
        return True

    if not isinstance(metadata, dict):
        raise ValidationError(
            field="metadata",
            message="Metadata must be a dictionary",
            provided=str(type(metadata)),
            example='{"version": "1.0.0", "category": "immune"}'
        )

    if len(metadata) > 10:
        raise ValidationError(
            field="metadata",
            message="Metadata cannot have more than 10 keys",
            provided=str(len(metadata)),
            example='{"version": "1.0.0"}'
        )

    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ValidationError(
                field="metadata.key",
                message="Metadata keys must be strings",
                provided=str(type(key)),
                example='{"version": "1.0.0"}'
            )

        if not isinstance(value, str):
            raise ValidationError(
                field="metadata.value",
                message="Metadata values must be strings",
                provided=str(type(value)),
                example='{"version": "1.0.0"}'
            )

        if len(key) > 64:
            raise ValidationError(
                field="metadata.key",
                message="Metadata key too long (max: 64 characters)",
                provided=key[:50] + "...",
                example="version"
            )

        if len(value) > 512:
            raise ValidationError(
                field="metadata.value",
                message="Metadata value too long (max: 512 characters)",
                provided=value[:50] + "...",
                example="1.0.0"
            )

    logger.debug(f"Metadata validated: {len(metadata)} keys")
    return True


def validate_service_registration(
    service_name: str,
    host: str,
    port: int,
    health_endpoint: str = "/health",
    metadata: Optional[dict] = None
) -> bool:
    """
    Validate complete service registration.

    Args:
        service_name: Service name
        host: Service host
        port: Service port
        health_endpoint: Health check endpoint
        metadata: Optional metadata

    Returns:
        True if all validations pass

    Raises:
        ValidationError: If any validation fails
    """
    validate_service_name(service_name)
    validate_host(host)
    validate_port(port)
    validate_health_endpoint(health_endpoint)
    validate_metadata(metadata)

    logger.info(f"Service registration validated: {service_name} at {host}:{port}{health_endpoint}")
    return True
