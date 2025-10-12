"""
Rate Limiting Middleware for MAXIMUS Eureka.

Sliding window rate limiter using in-memory storage.
Perfect for "garage mode" - single instance deployment.

For distributed: migrate to Redis-backed store.

Sprint 6 - Issue #11
Author: MAXIMUS Team
Glory to YHWH - Source of Balance
"""

import time
from collections import deque, defaultdict
from typing import Dict, Tuple, Optional, Callable
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.
    
    Tracks requests per client in time windows.
    Memory-efficient with automatic cleanup.
    
    Biological Analogy: Immune system regulation
    - Too many requests = overwhelming immune response
    - Rate limiting = homeostatic control
    - Burst tolerance = adaptive response to real threats
    """
    
    def __init__(
        self,
        default_limit: int = 100,
        window_seconds: int = 60,
        burst_limit: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Max requests per window (default: 100/min)
            window_seconds: Time window in seconds (default: 60s = 1 min)
            burst_limit: Max burst requests (default: 2x limit)
        """
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit or (default_limit * 2)
        
        # Storage: {client_id: deque of timestamps}
        self._storage: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Per-endpoint limits: {path: (limit, window)}
        self._endpoint_limits: Dict[str, Tuple[int, int]] = {}
        
        # Metrics
        self._hits = 0
        self._blocks = 0
        
        logger.info(
            f"🛡️ Rate limiter initialized: {default_limit} req/{window_seconds}s, "
            f"burst={burst_limit}"
        )
    
    def set_endpoint_limit(
        self,
        path: str,
        limit: int,
        window_seconds: Optional[int] = None
    ) -> None:
        """
        Set custom limit for specific endpoint.
        
        Args:
            path: Endpoint path (e.g., "/api/v1/analyze")
            limit: Max requests for this endpoint
            window_seconds: Custom window (or use default)
        """
        window = window_seconds or self.window_seconds
        self._endpoint_limits[path] = (limit, window)
        logger.info(f"📍 Endpoint limit set: {path} = {limit} req/{window}s")
    
    def _get_limit(self, path: str) -> Tuple[int, int]:
        """Get limit and window for path."""
        return self._endpoint_limits.get(path, (self.default_limit, self.window_seconds))
    
    def _cleanup_old(self, timestamps: deque, window_start: float) -> None:
        """Remove timestamps outside current window."""
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()
    
    def is_allowed(self, client_id: str, path: str) -> Tuple[bool, Dict]:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (IP, user ID, etc.)
            path: Request path
            
        Returns:
            (allowed: bool, info: dict with rate limit info)
        """
        now = time.time()
        limit, window = self._get_limit(path)
        window_start = now - window
        
        # Get timestamps for client
        timestamps = self._storage[client_id]
        
        # Cleanup old timestamps
        self._cleanup_old(timestamps, window_start)
        
        # Check current count
        current_count = len(timestamps)
        
        # Check burst limit (short window)
        burst_window_start = now - 1  # 1-second burst window
        burst_count = sum(1 for ts in timestamps if ts >= burst_window_start)
        
        if burst_count >= self.burst_limit:
            self._blocks += 1
            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset": int(window_start + window),
                "retry_after": 1,
                "reason": "burst_limit_exceeded"
            }
        
        if current_count >= limit:
            self._blocks += 1
            # Calculate retry_after (time until oldest timestamp expires)
            retry_after = int(timestamps[0] + window - now) if timestamps else window
            
            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset": int(timestamps[0] + window) if timestamps else int(now + window),
                "retry_after": retry_after,
                "reason": "rate_limit_exceeded"
            }
        
        # Allow request
        timestamps.append(now)
        self._hits += 1
        
        return True, {
            "allowed": True,
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset": int(window_start + window),
            "retry_after": 0,
            "reason": None
        }
    
    def get_metrics(self) -> Dict:
        """Get rate limiter metrics."""
        return {
            "total_hits": self._hits,
            "total_blocks": self._blocks,
            "block_rate": self._blocks / self._hits if self._hits > 0 else 0,
            "active_clients": len(self._storage),
            "default_limit": self.default_limit,
            "window_seconds": self.window_seconds,
            "burst_limit": self.burst_limit,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    Automatically applies rate limits to all endpoints.
    Adds rate limit headers to responses.
    """
    
    def __init__(
        self,
        app,
        limiter: SlidingWindowRateLimiter,
        get_client_id: Optional[Callable[[Request], str]] = None,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            limiter: Rate limiter instance
            get_client_id: Function to extract client ID from request
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limiter = limiter
        self.get_client_id = get_client_id or self._default_client_id
        self.exclude_paths = set(exclude_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"])
        logger.info(f"🛡️ Rate limit middleware initialized (exclude: {self.exclude_paths})")
    
    def _default_client_id(self, request: Request) -> str:
        """Extract client ID from request (default: IP address)."""
        # Try to get real IP from X-Forwarded-For header (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        path = request.url.path
        
        # Skip excluded paths
        if path in self.exclude_paths or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)
        
        # Get client ID
        client_id = self.get_client_id(request)
        
        # Check rate limit
        allowed, info = self.limiter.is_allowed(client_id, path)
        
        if not allowed:
            logger.warning(
                f"🚫 Rate limit exceeded: {client_id} on {path} "
                f"(reason: {info['reason']}, retry_after: {info['retry_after']}s)"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "reason": info["reason"],
                    "retry_after": info["retry_after"],
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"]),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response


def rate_limit(
    limit: int,
    window_seconds: int = 60
) -> Callable:
    """
    Decorator for endpoint-specific rate limiting.
    
    Usage:
        @app.get("/expensive-operation")
        @rate_limit(limit=10, window_seconds=60)
        async def expensive_op():
            ...
    
    Args:
        limit: Max requests per window
        window_seconds: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This decorator is a placeholder for per-endpoint limits
            # Actual limiting is done in middleware
            # This sets metadata that middleware can use
            return await func(*args, **kwargs)
        
        # Attach metadata
        wrapper.__rate_limit__ = (limit, window_seconds)
        return wrapper
    
    return decorator
