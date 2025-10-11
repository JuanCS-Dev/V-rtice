"""
Confirmation Models - MAXIMUS Eureka.

Pydantic models representing vulnerability confirmation results.
Structured data flowing from confirmation to remediation phase.
"""

from models.confirmation.confirmation_result import (
    ConfirmationResult,
    ConfirmationStatus,
    VulnerableLocation,
    ConfirmationMetadata,
)

__all__ = [
    "ConfirmationResult",
    "ConfirmationStatus",
    "VulnerableLocation",
    "ConfirmationMetadata",
]
