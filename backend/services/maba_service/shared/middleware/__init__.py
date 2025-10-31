"""
Shared Middleware for Vértice Platform
=======================================

FastAPI middleware components for:
- Rate limiting
- Authentication (future)
- Logging (future)
- CORS (future)
"""

from .rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    TokenBucket,
    get_rate_limit_status,
    rate_limit,
)

__all__ = [
    "RateLimiter",
    "RateLimitConfig",
    "TokenBucket",
    "rate_limit",
    "get_rate_limit_status",
]
