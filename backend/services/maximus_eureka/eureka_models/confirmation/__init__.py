"""
Confirmation Models - MAXIMUS Eureka.

Pydantic models representing vulnerability confirmation results.
Structured data flowing from confirmation to remediation phase.
"""

# Lazy imports to avoid circular dependencies
# Import directly when needed:
# from eureka_models.confirmation.confirmation_result import ConfirmationResult

__all__ = [
    "ConfirmationResult",
    "ConfirmationStatus",
    "VulnerableLocation",
    "ConfirmationMetadata",
]
