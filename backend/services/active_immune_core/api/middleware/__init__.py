"""API Middleware - PRODUCTION-READY

Middleware components for authentication, rate limiting, and request processing.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from .auth import AuthMiddleware, get_current_user, require_role
from .rate_limit import RateLimitMiddleware, rate_limit

__all__ = [
    "AuthMiddleware",
    "get_current_user",
    "require_role",
    "RateLimitMiddleware",
    "rate_limit",
]
