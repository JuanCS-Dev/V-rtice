"""
User-Based Rate Limiting Middleware

DOUTRINA VÉRTICE - GAP #13 (P2)
Rate limiting by user ID (not just IP address)

Following Boris Cherny's principle: "Security should scale with identity"
"""

import jwt
import os
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Get JWT secret from environment
JWT_SECRET = os.getenv("JWT_SECRET", "")


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.

    Priority:
    1. User ID from JWT token (if authenticated)
    2. IP address (fallback for anonymous users)

    This ensures:
    - Authenticated users have per-user limits
    - Anonymous users share IP-based limits
    - No user can bypass limits by switching IPs after login

    Examples:
        Authenticated: "user:550e8400-e29b-41d4-a716-446655440000"
        Anonymous: "ip:192.168.1.1"
    """
    # Try to extract user ID from Authorization header
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")

        try:
            # Decode JWT to get user ID
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_exp": False},  # Don't verify expiration for rate limiting
            )

            user_id = payload.get("sub")
            if user_id:
                # Rate limit by authenticated user ID
                return f"user:{user_id}"

        except (jwt.InvalidTokenError, jwt.DecodeError):
            # Invalid token - fall through to IP-based limiting
            pass

    # Fallback to IP address for anonymous/invalid users
    return f"ip:{get_remote_address(request)}"


# Create limiter with user-based identification
limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379"),
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
    default_limits=["100/minute"],  # Global default
)


# ============================================================================
# ENDPOINT-SPECIFIC LIMITS
# ============================================================================

# Scan endpoints (resource-intensive)
SCAN_START_LIMIT = "10/minute"  # Max 10 scans per minute per user
SCAN_RESULT_LIMIT = "60/minute"  # Max 60 result fetches per minute

# Authentication endpoints
AUTH_LOGIN_LIMIT = "5/minute"  # Max 5 login attempts per minute per IP
AUTH_REGISTER_LIMIT = "3/minute"  # Max 3 registrations per minute per IP
AUTH_RESET_LIMIT = "3/minute"  # Max 3 password resets per minute per IP

# Data modification endpoints
MUTATION_LIMIT = "30/minute"  # Max 30 mutations per minute per user

# Public/read-only endpoints
READ_LIMIT = "100/minute"  # Max 100 reads per minute per user

# Admin endpoints
ADMIN_LIMIT = "200/minute"  # Higher limit for admins


# ============================================================================
# RATE LIMIT DECORATOR
# ============================================================================

def user_rate_limit(limit: str):
    """
    Decorator for user-based rate limiting on specific endpoints.

    Usage:
        @app.post("/api/v1/scan/start")
        @user_rate_limit("10/minute")
        async def start_scan():
            ...

    The limit applies per authenticated user ID or per IP for anonymous users.

    Examples:
        @user_rate_limit("5/minute")   # 5 requests per minute
        @user_rate_limit("100/hour")   # 100 requests per hour
        @user_rate_limit("1000/day")   # 1000 requests per day
    """
    return limiter.limit(limit, key_func=get_user_identifier)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_rate_limit_key(request: Request) -> str:
    """
    Get the rate limit key for a request (for debugging).

    Returns:
        "user:USER_ID" or "ip:IP_ADDRESS"
    """
    return get_user_identifier(request)


def is_user_authenticated(request: Request) -> bool:
    """
    Check if request is from authenticated user.

    Returns:
        True if user is authenticated (rate limited by user ID)
        False if anonymous (rate limited by IP)
    """
    return get_user_identifier(request).startswith("user:")
