"""
Rate limiting middleware using token bucket algorithm.

Implements adaptive rate limiting for Wargaming Service endpoints to prevent abuse
and ensure fair resource allocation. Inspired by biological immune system's
ability to regulate response intensity.

Limits:
- /wargaming/ml-first: 100 req/min per IP
- /wargaming/validate: 50 req/min per IP  
- /wargaming/ml/accuracy: 10 req/min per IP

Biological Analogy:
Token bucket = Cytokine production limits (prevent cytokine storm)
Refill rate = Immune response regulation
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
import time
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket rate limiter implementation.
    
    Allows bursts up to capacity, then enforces steady-state rate.
    Similar to immune system's ability to mount strong initial response
    then regulate to prevent autoimmune reactions.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens (burst allowance)
            refill_rate: Tokens added per second (steady-state rate)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens. Returns True if allowed.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if request allowed, False if rate limited
        """
        now = time.time()
        
        # Refill tokens based on elapsed time
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
        
        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_status(self) -> Dict[str, float]:
        """Get current bucket status for monitoring."""
        return {
            "tokens": self.tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "fill_percentage": (self.tokens / self.capacity) * 100
        }


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI.
    
    Applies per-IP rate limits based on endpoint patterns.
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # IP -> (endpoint -> TokenBucket)
        self.buckets: Dict[str, Dict[str, TokenBucket]] = {}
        
        # Rate limits by endpoint pattern
        # (capacity, refill_rate_per_second)
        self.limits = {
            "/wargaming/ml-first": (100, 100/60),      # 100 req/min
            "/wargaming/validate": (50, 50/60),         # 50 req/min
            "/wargaming/ml/accuracy": (10, 10/60),      # 10 req/min
            "/wargaming/ab-testing": (20, 20/60),       # 20 req/min
            "/wargaming/cache": (30, 30/60),            # 30 req/min
        }
    
    def get_bucket(self, ip: str, endpoint: str) -> TokenBucket:
        """Get or create token bucket for IP + endpoint combination."""
        if ip not in self.buckets:
            self.buckets[ip] = {}
        
        if endpoint not in self.buckets[ip]:
            capacity, rate = self.limits.get(endpoint, (1000, 1000/60))
            self.buckets[ip][endpoint] = TokenBucket(capacity, rate)
        
        return self.buckets[ip][endpoint]
    
    async def dispatch(self, request: Request, call_next):
        """Middleware handler - check rate limits before processing request."""
        # Get client IP (handle proxy headers)
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        endpoint = request.url.path
        
        # Find matching rate limit
        limit_key = None
        for pattern in self.limits:
            if endpoint.startswith(pattern):
                limit_key = pattern
                break
        
        # Apply rate limit if endpoint matches
        if limit_key:
            bucket = self.get_bucket(client_ip, limit_key)
            
            if not bucket.consume():
                capacity, rate = self.limits[limit_key]
                logger.warning(
                    f"Rate limit exceeded: {client_ip} → {endpoint} "
                    f"(limit: {capacity} req/min)"
                )
                
                # Return JSONResponse instead of raising (for middleware compatibility)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": {
                            "error": "Rate limit exceeded",
                            "endpoint": endpoint,
                            "limit": f"{capacity} requests per minute",
                            "retry_after": 60,  # seconds
                            "message": "Too many requests. Please slow down."
                        }
                    },
                    headers={
                        "X-RateLimit-Limit": str(capacity),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": "60"
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        if limit_key:
            bucket = self.get_bucket(client_ip, limit_key)
            status = bucket.get_status()
            response.headers["X-RateLimit-Limit"] = str(self.limits[limit_key][0])
            response.headers["X-RateLimit-Remaining"] = str(int(status["tokens"]))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response


# Global instance
rate_limiter = RateLimiterMiddleware
