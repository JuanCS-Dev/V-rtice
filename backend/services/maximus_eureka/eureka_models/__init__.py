"""
Models package for MAXIMUS Eureka Adaptive Immunity.

Contains Pydantic models for:
- Confirmation results (vulnerability verification)
- Patches (remediation artifacts)
- Remediation results (pipeline outcomes)
"""

# Lazy imports to avoid circular dependencies during test collection
# Import directly from submodules when needed:
# from eureka_models.confirmation.confirmation_result import ConfirmationResult

__all__ = [
    "ConfirmationResult",
    "ConfirmationStatus",
    "VulnerableLocation",
    "ConfirmationMetadata",
]
