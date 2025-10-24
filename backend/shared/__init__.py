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
    "auto_register_service"
]

# Import registry client for convenience
try:
    from .vertice_registry_client import RegistryClient, auto_register_service
except ImportError:
    # Optional import - service registry may not be deployed yet
    RegistryClient = None
    auto_register_service = None
