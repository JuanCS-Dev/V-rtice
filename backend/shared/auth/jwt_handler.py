"""
JWT Authentication Handler
===========================

Production-ready JWT authentication with multi-tenant support.
Boris Cherny Pattern: Type-safe authentication with explicit scopes.

Features:
- JWT token generation and validation
- Multi-tenant support (tenant_id in token)
- Scope-based authorization
- Token expiry validation
- Refresh token support
- Blacklist support (for logout)

Governed by: Constituição Vértice v2.7 - Security First

Research Reference:
- FastAPI JWT Best Practices 2025
- https://testdriven.io/blog/fastapi-jwt-auth/
"""

import os
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# =============================================================================
# CONFIGURATION
# =============================================================================

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days

security = HTTPBearer()

# Blacklist for revoked tokens (in production, use Redis)
token_blacklist: Dict[str, float] = {}

# =============================================================================
# JWT TOKEN GENERATION
# =============================================================================

def create_access_token(
    user_id: str,
    email: str,
    tenant_id: str,
    scopes: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token.
    
    Example:
        token = create_access_token(
            user_id="123",
            email="user@example.com",
            tenant_id="tenant-abc",
            scopes=["read:data", "write:data"],
        )
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email,
        "tenant_id": tenant_id,
        "scopes": scopes,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": f"{user_id}-{int(time.time())}",
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "scopes": ["refresh"],
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": f"refresh-{user_id}-{int(time.time())}",
        "type": "refresh",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# =============================================================================
# JWT TOKEN VALIDATION
# =============================================================================

def decode_token(token: str) -> Dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        jti = payload.get("jti")
        if jti and jti in token_blacklist:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        exp = payload.get("exp")
        if exp and exp < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """Get current user from JWT token.
    
    Example:
        @app.get("/api/profile")
        async def get_profile(user: Dict = Depends(get_current_user)):
            return {"user_id": user["sub"]}
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh tokens cannot be used for API access",
        )

    return payload


def require_scope(required_scope: str):
    """Require specific scope for endpoint access.
    
    Example:
        @app.post("/api/offensive/scan")
        async def run_scan(user: Dict = Depends(require_scope("offensive:execute"))):
            return {"status": "scanning"}
    """
    async def dependency(user: Dict = Depends(get_current_user)):
        scopes = user.get("scopes", [])

        if "*" in scopes:
            return user

        if required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {required_scope}",
            )

        return user

    return dependency


def require_tenant(tenant_id: str):
    """Require specific tenant for endpoint access."""
    async def dependency(user: Dict = Depends(get_current_user)):
        user_tenant_id = user.get("tenant_id")

        if user_tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: user belongs to tenant {user_tenant_id}",
            )

        return user

    return dependency


# =============================================================================
# TOKEN BLACKLIST
# =============================================================================

def revoke_token(token: str):
    """Revoke a token (add to blacklist)."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")

        if jti and exp:
            token_blacklist[jti] = exp
    except jwt.InvalidTokenError:
        pass


def cleanup_blacklist():
    """Remove expired tokens from blacklist."""
    current_time = time.time()
    expired_tokens = [
        jti for jti, exp in token_blacklist.items() if exp < current_time
    ]

    for jti in expired_tokens:
        del token_blacklist[jti]

    return len(expired_tokens)
