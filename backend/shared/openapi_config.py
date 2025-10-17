"""
Vértice Platform - OpenAPI/Swagger Configuration
=================================================

This module provides standardized OpenAPI configuration for all FastAPI services
in the Vértice platform. It ensures consistent API documentation, metadata, and
descriptions across all 67+ microservices.

Features:
    - Standardized OpenAPI metadata (title, version, description)
    - Custom tags for endpoint categorization
    - Security schemes (API Key, OAuth2, JWT)
    - Contact information and licensing
    - Server configurations for different environments
    - Reusable response models and examples

Usage:
    >>> from fastapi import FastAPI
    >>> from shared.openapi_config import create_openapi_config
    >>>
    >>> app = FastAPI(**create_openapi_config(
    >>>     service_name="Maximus Core Service",
    >>>     service_description="Central AI reasoning engine",
    >>>     version="1.0.0"
    >>> ))

Author: Vértice Platform Team
License: Proprietary
"""

from typing import Any, Dict, List, Optional

from .constants import ServicePorts

# ============================================================================
# CONTACT & LICENSE INFORMATION
# ============================================================================

CONTACT_INFO = {
    "name": "Vértice Platform Team",
    "email": "dev@vertice.security",
    "url": "https://vertice.security",
}

LICENSE_INFO = {
    "name": "Proprietary",
    "url": "https://vertice.security/license",
}


# ============================================================================
# SERVER CONFIGURATIONS
# ============================================================================


def get_servers(service_port: int) -> List[Dict[str, str]]:
    """Get server configurations for different environments.

    Args:
        service_port: Port number for the service

    Returns:
        List of server configurations
    """
    return [
        {
            "url": f"http://localhost:{service_port}",
            "description": "Development server (local)",
        },
        {
            "url": f"http://127.0.0.1:{service_port}",
            "description": "Development server (loopback)",
        },
        {
            "url": f"http://vertice-platform:{service_port}",
            "description": "Docker Compose internal network",
        },
        {
            "url": "https://api.vertice.security",
            "description": "Production server (via API Gateway)",
        },
    ]


# ============================================================================
# SECURITY SCHEMES
# ============================================================================

SECURITY_SCHEMES = {
    "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API Key authentication",
    },
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT Bearer token authentication",
    },
    "OAuth2": {
        "type": "oauth2",
        "flows": {
            "authorizationCode": {
                "authorizationUrl": "https://api.vertice.security/oauth2/authorize",
                "tokenUrl": "https://api.vertice.security/oauth2/token",
                "scopes": {
                    "read": "Read access to resources",
                    "write": "Write access to resources",
                    "admin": "Administrative access",
                },
            }
        },
    },
}


# ============================================================================
# COMMON TAGS
# ============================================================================

COMMON_TAGS = [
    {
        "name": "Health",
        "description": "Service health check and status endpoints",
    },
    {
        "name": "Analysis",
        "description": "Threat analysis and detection endpoints",
    },
    {
        "name": "Scan",
        "description": "Security scanning operations",
    },
    {
        "name": "Investigation",
        "description": "Incident investigation and forensics",
    },
    {
        "name": "Intelligence",
        "description": "Threat intelligence and OSINT",
    },
    {
        "name": "Response",
        "description": "Automated response and remediation",
    },
    {
        "name": "Reporting",
        "description": "Reports and analytics",
    },
    {
        "name": "Configuration",
        "description": "Service configuration and settings",
    },
]


# ============================================================================
# OPENAPI CONFIG BUILDER
# ============================================================================


def create_openapi_config(
    service_name: str,
    service_description: str,
    version: str = "1.0.0",
    service_port: Optional[int] = None,
    tags: Optional[List[Dict[str, str]]] = None,
    include_security: bool = True,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create standardized OpenAPI configuration for a FastAPI service.

    Args:
        service_name: Name of the service (e.g., "Maximus Core Service")
        service_description: Detailed description of the service
        version: API version (default: "1.0.0")
        service_port: Port number for server URLs (optional)
        tags: Custom tags for endpoint categorization (default: COMMON_TAGS)
        include_security: Include security schemes (default: True)
        additional_metadata: Additional OpenAPI metadata

    Returns:
        Dictionary with OpenAPI configuration for FastAPI

    Example:
        >>> config = create_openapi_config(
        >>>     service_name="IP Intelligence Service",
        >>>     service_description="IP reputation and geolocation analysis",
        >>>     version="2.1.0",
        >>>     service_port=8002,
        >>> )
        >>> app = FastAPI(**config)
    """
    config = {
        "title": service_name,
        "description": service_description,
        "version": version,
        "contact": CONTACT_INFO,
        "license_info": LICENSE_INFO,
        "openapi_tags": tags or COMMON_TAGS,
    }

    # Add servers if port provided
    if service_port:
        config["servers"] = get_servers(service_port)

    # Build OpenAPI schema with custom components
    def custom_openapi():
        """Generate custom OpenAPI schema with security schemes."""
        from fastapi.openapi.utils import get_openapi

        if hasattr(custom_openapi, "openapi_schema"):
            return custom_openapi.openapi_schema

        openapi_schema = get_openapi(
            title=service_name,
            version=version,
            description=service_description,
            routes=app.routes,
            tags=tags or COMMON_TAGS,
            servers=get_servers(service_port) if service_port else None,
        )

        # Add security schemes
        if include_security:
            openapi_schema["components"] = openapi_schema.get("components", {})
            openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES

        # Add additional metadata
        if additional_metadata:
            openapi_schema.update(additional_metadata)

        # Add external documentation
        openapi_schema["externalDocs"] = {
            "description": "Vértice Platform Documentation",
            "url": "https://docs.vertice.security",
        }

        custom_openapi.openapi_schema = openapi_schema
        return openapi_schema

    config["openapi_schema"] = custom_openapi

    return config


# ============================================================================
# SERVICE-SPECIFIC CONFIGS
# ============================================================================


def get_maximus_core_config() -> Dict[str, Any]:
    """Get OpenAPI config for Maximus Core Service."""
    return create_openapi_config(
        service_name="Maximus Core Service",
        service_description=(
            "**Central AI Reasoning Engine** for the Vértice cybersecurity platform.\n\n"
            "Maximus Core provides:\n"
            "- Multi-modal threat analysis\n"
            "- Autonomous decision-making\n"
            "- Cross-service orchestration\n"
            "- Memory consolidation and learning\n"
            "- Ethical reasoning framework\n\n"
            "This service is the cognitive center of the Vértice AI system, coordinating "
            "all other microservices and maintaining situational awareness."
        ),
        version="3.0.0",
        service_port=ServicePorts.MAXIMUS_CORE,
        tags=[
            {"name": "Analysis", "description": "Threat analysis operations"},
            {"name": "Memory", "description": "Memory and knowledge management"},
            {"name": "Reasoning", "description": "AI reasoning and decision-making"},
            {"name": "Orchestration", "description": "Service orchestration"},
            {"name": "Health", "description": "Service health and status"},
        ],
    )


def get_ip_intelligence_config() -> Dict[str, Any]:
    """Get OpenAPI config for IP Intelligence Service."""
    return create_openapi_config(
        service_name="IP Intelligence Service",
        service_description=(
            "**IP Reputation and Geolocation Analysis** service.\n\n"
            "Provides comprehensive IP address intelligence including:\n"
            "- Reputation scoring (AbuseIPDB, GreyNoise, etc.)\n"
            "- Geolocation and ASN information\n"
            "- Historical threat data\n"
            "- Threat actor attribution\n"
            "- Real-time blacklist checking"
        ),
        version="2.0.0",
        service_port=ServicePorts.IP_INTELLIGENCE,
        tags=[
            {"name": "Intelligence", "description": "IP intelligence queries"},
            {"name": "Reputation", "description": "IP reputation scoring"},
            {"name": "Geolocation", "description": "IP geolocation data"},
            {"name": "Health", "description": "Service health check"},
        ],
    )


def get_malware_analysis_config() -> Dict[str, Any]:
    """Get OpenAPI config for Malware Analysis Service."""
    return create_openapi_config(
        service_name="Malware Analysis Service",
        service_description=(
            "**Static and Dynamic Malware Analysis** service.\n\n"
            "Capabilities:\n"
            "- Static analysis (PE headers, strings, signatures)\n"
            "- Dynamic analysis (sandbox execution)\n"
            "- YARA rule scanning\n"
            "- Behavioral analysis\n"
            "- IOC extraction\n"
            "- Family classification"
        ),
        version="1.5.0",
        service_port=ServicePorts.MALWARE_ANALYSIS,
        tags=[
            {"name": "Analysis", "description": "Malware analysis operations"},
            {"name": "Scan", "description": "File and hash scanning"},
            {"name": "YARA", "description": "YARA rule management"},
            {"name": "IOC", "description": "Indicator extraction"},
            {"name": "Health", "description": "Service health check"},
        ],
    )


# ============================================================================
# RESPONSE EXAMPLES
# ============================================================================

RESPONSE_EXAMPLES = {
    "success": {
        "summary": "Successful response",
        "value": {
            "status": "success",
            "data": {"example_field": "example_value"},
            "timestamp": "2025-10-05T12:00:00Z",
        },
    },
    "error": {
        "summary": "Error response",
        "value": {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input parameters",
                "status_code": 400,
                "details": {"field": "ip_address", "issue": "Invalid format"},
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-10-05T12:00:00Z",
            }
        },
    },
}


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "create_openapi_config",
    "get_maximus_core_config",
    "get_ip_intelligence_config",
    "get_malware_analysis_config",
    "CONTACT_INFO",
    "LICENSE_INFO",
    "SECURITY_SCHEMES",
    "COMMON_TAGS",
    "RESPONSE_EXAMPLES",
]
