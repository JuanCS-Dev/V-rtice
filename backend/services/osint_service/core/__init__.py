"""Maximus OSINT Service - Core Infrastructure Module.

This package provides production-grade infrastructure for all OSINT tools:
- BaseTool: Abstract base class with retry, circuit breaker, caching, metrics
- RateLimiter: Token bucket rate limiting
- CircuitBreaker: Fail-fast pattern for external APIs
- CacheManager: Multi-tier caching (Redis + in-memory LRU)

All OSINT tools MUST inherit from BaseTool to ensure consistent production patterns.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

from core.base_tool import BaseTool, ToolException
from core.cache_manager import CacheManager
from core.circuit_breaker import CircuitBreaker, CircuitState
from core.rate_limiter import RateLimiter

__all__ = [
    "BaseTool",
    "ToolException",
    "RateLimiter",
    "CircuitBreaker",
    "CircuitState",
    "CacheManager",
]
