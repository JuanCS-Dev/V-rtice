"""Middleware package for API Gateway.

This package contains all middleware components for the Vértice API Gateway.
Following Boris Cherny's principle: "Explicit is better than implicit"
"""

from .tracing import RequestTracingMiddleware

__all__ = ["RequestTracingMiddleware"]
