"""Custom Exceptions for Lymphnode Operations

Specific exceptions for better error handling and debugging.

Authors: Juan + Claude
Date: 2025-10-07
"""


class LymphnodeException(Exception):
    """Base exception for all lymphnode errors"""
    pass


class LymphnodeConfigurationError(LymphnodeException):
    """Raised when lymphnode configuration is invalid"""
    pass


class LymphnodeConnectionError(LymphnodeException):
    """Raised when connection to infrastructure fails (Redis/Kafka)"""
    pass


class LymphnodeValidationError(LymphnodeException):
    """Raised when input validation fails"""
    pass


class LymphnodeRateLimitError(LymphnodeException):
    """Raised when rate limit is exceeded"""
    pass


class LymphnodeResourceExhaustedError(LymphnodeException):
    """Raised when resources are exhausted (too many agents, etc.)"""
    pass


class CytokineProcessingError(LymphnodeException):
    """Raised when cytokine processing fails"""
    pass


class PatternDetectionError(LymphnodeException):
    """Raised when pattern detection fails"""
    pass


class AgentOrchestrationError(LymphnodeException):
    """Raised when agent orchestration fails (clone creation/destruction)"""
    pass


class HormonePublishError(LymphnodeException):
    """Raised when hormone publishing fails"""
    pass


class ESGTIntegrationError(LymphnodeException):
    """Raised when ESGT integration fails"""
    pass


class LymphnodeStateError(LymphnodeException):
    """Raised when lymphnode is in invalid state for operation"""
    pass
