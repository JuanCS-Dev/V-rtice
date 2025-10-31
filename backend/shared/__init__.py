"""
Vértice Platform - Shared Modules

This package contains shared utilities, constants, validators, and common code
used across all 107+ microservices in the Vértice cybersecurity platform.

Modules:
    constants: Service ports, API endpoints, system-wide constants
    enums: Enumerated types for status codes, threat levels, etc.
    exceptions: Custom exception hierarchy
    error_handlers: FastAPI error handlers
    validators: Input validation using Pydantic
    sanitizers: Input sanitization and escaping
    vertice_registry_client: Service Registry client for auto-registration
    subordinate_service: Base interface for MAXIMUS subordinate services
    maximus_integration: MAXIMUS integration helper mixin
    tool_protocol: Standard tool interface for MAXIMUS

Author: Vértice Platform Team
License: Proprietary
"""

__version__ = "1.0.0"
__all__ = [
    "constants",
    "enums",
    "exceptions",
    "validators",
    "sanitizers",
    "vertice_registry_client",
    "RegistryClient",
    "auto_register_service",
    "subordinate_service",
    "maximus_integration",
    "tool_protocol",
    "SubordinateServiceBase",
    "MaximusIntegrationMixin",
    "ToolBase",
    "ToolParameter",
    "ToolInvocationRequest",
    "ToolInvocationResponse",
]

# Import registry client for convenience
try:
    from .vertice_registry_client import RegistryClient, auto_register_service
except ImportError:
    # Optional import - service registry may not be deployed yet
    RegistryClient = None
    auto_register_service = None

# Import MAXIMUS subordinate service utilities
try:
    from .maximus_integration import MaximusIntegrationMixin
    from .subordinate_service import SubordinateServiceBase
    from .tool_protocol import (
        ToolBase,
        ToolInvocationRequest,
        ToolInvocationResponse,
        ToolParameter,
    )
except ImportError:
    # Optional import - may not be available in all services
    SubordinateServiceBase = None
    MaximusIntegrationMixin = None
    ToolBase = None
    ToolParameter = None
    ToolInvocationRequest = None
    ToolInvocationResponse = None
