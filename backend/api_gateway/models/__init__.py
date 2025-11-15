"""Models package for API Gateway.

This package contains all Pydantic models for requests, responses, and errors.
Following Boris Cherny's principle: "If it doesn't have types, it's not production"
"""

from .errors import ErrorResponse, ValidationErrorResponse

__all__ = ["ErrorResponse", "ValidationErrorResponse"]
