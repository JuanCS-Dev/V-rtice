"""Centralized Authentication Service for the Vertice project.

This service handles user authentication via Google OAuth, creates and verifies
JWT tokens for session management, and manages user permissions based on predefined
rules. It uses Redis for session storage to allow for stateless API services.

- Authenticates users with a Google OAuth token.
- Creates a JWT containing user info and permissions.
- Verifies JWTs for other services.
- Provides permission-based access control dependencies.
- Manages sessions via Redis.
"""

import os
import jwt
import json
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis

# ============================================================================
# Configuration and Initialization
# ============================================================================

app = FastAPI(
    title="Authentication Service",
    description="Centralized authentication service with Google OAuth for Vertice.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration from Environment Variables ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "default-secret-key")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
AUTHORIZED_DOMAINS = os.getenv("AUTHORIZED_DOMAINS", "").split(",")
AUTHORIZED_EMAILS = os.getenv("AUTHORIZED_EMAILS", "").split(",")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")
SUPER_ADMIN_EMAIL = "juan.brainfarma@gmail.com"

# --- Redis Connection ---
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except redis.exceptions.ConnectionError:
    redis_client = None

# --- Security Scheme ---
security = HTTPBearer()

# --- Permission Levels ---
PERMISSION_LEVELS = {
    "admin": ["read", "write", "delete", "offensive", "admin"],
    "analyst": ["read", "write", "offensive"],
    "viewer": ["read"],
}

# ============================================================================
# Pydantic Models
# ============================================================================

class GoogleTokenRequest(BaseModel):
    """Request model for authenticating with a Google OAuth token."""
    token: str

class UserInfo(BaseModel):
    """Pydantic model representing public user information."""
    id: str
    email: str
    name: str
    picture: str

class AuthStatus(BaseModel):
    """Response model for the /auth/me endpoint."""
    authenticated: bool
    user: Optional[UserInfo] = None
    permissions: List[str] = []

# ============================================================================
# Core Authentication Logic
# ============================================================================

async def verify_google_token(token: str) -> Dict[str, Any]:
    """Verifies a Google OAuth token and retrieves user information.

    Args:
        token (str): The Google OAuth access token.

    Returns:
        Dict[str, Any]: The user information dictionary from Google.

    Raises:
        HTTPException: If the token is invalid or the user is not authorized.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={token}")
            response.raise_for_status()
            user_info = response.json()
            if not is_authorized_user(user_info):
                raise HTTPException(status_code=403, detail="User not authorized.")
            return user_info
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e.response.text}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Failed to connect to Google services.")

def is_authorized_user(user_info: Dict[str, Any]) -> bool:
    """Checks if a user is authorized to access the system based on their email."""
    email = user_info.get("email", "").lower()
    domain = email.split("@")[-1] if "@" in email else ""
    if email == SUPER_ADMIN_EMAIL.lower(): return True
    if email in [e.lower() for e in AUTHORIZED_EMAILS if e]: return True
    if domain in [d.lower() for d in AUTHORIZED_DOMAINS if d]: return True
    return False

def get_user_permissions(user_info: Dict[str, Any]) -> List[str]:
    """Determines a user's permission level based on their email."""
    email = user_info.get("email", "").lower()
    if email == SUPER_ADMIN_EMAIL.lower() or email in [e.lower() for e in ADMIN_EMAILS if e]:
        return PERMISSION_LEVELS["admin"]
    return PERMISSION_LEVELS["analyst"] # Default for other authorized users

def create_jwt_token(user_info: Dict[str, Any]) -> str:
    """Creates a JWT for an authenticated user and stores it in Redis."""
    permissions = get_user_permissions(user_info)
    payload = {
        "sub": user_info["id"],
        "email": user_info["email"],
        "name": user_info["name"],
        "picture": user_info["picture"],
        "permissions": permissions,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    if redis_client:
        redis_client.setex(f"session:{user_info['id']}", TOKEN_EXPIRE_HOURS * 3600, json.dumps(payload, default=str))
    return token

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verifies a JWT and checks for a valid session in Redis."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if redis_client and not redis_client.get(f"session:{payload['sub']}"):
            raise HTTPException(status_code=401, detail="Session not found or expired.")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """A dependency to get the current authenticated user from a JWT."""
    return verify_jwt_token(credentials.credentials)

def require_permission(permission: str):
    """A dependency factory to protect endpoints based on user permissions."""
    def dependency(user: Dict[str, Any] = Depends(get_current_user)):
        if permission not in user.get("permissions", []):
            raise HTTPException(status_code=403, detail=f"Permission '{permission}' required.")
        return user
    return dependency

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", tags=["Management"])
async def health_check():
    """Provides a health check of the service and its dependencies."""
    return {"status": "healthy", "redis_connected": redis_client is not None}

@app.post("/auth/google", tags=["Authentication"])
async def authenticate_with_google(request: GoogleTokenRequest):
    """Authenticates a user via a Google OAuth token and returns a JWT."""
    user_info = await verify_google_token(request.token)
    jwt_token = create_jwt_token(user_info)
    return {"access_token": jwt_token, "token_type": "Bearer"}

@app.get("/auth/me", response_model=AuthStatus, tags=["Authentication"])
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns information and permissions for the currently authenticated user."""
    return AuthStatus(
        authenticated=True,
        user=UserInfo(**user),
        permissions=user.get("permissions", [])
    )

@app.post("/auth/logout", tags=["Authentication"])
async def logout(user: Dict[str, Any] = Depends(get_current_user)):
    """Logs out the user by deleting their session from Redis."""
    if redis_client:
        redis_client.delete(f"session:{user['sub']}")
    return {"message": "Successfully logged out."}

@app.get("/protected/admin", tags=["Protected"])
async def admin_only_endpoint(user: Dict[str, Any] = Depends(require_permission("admin"))):
    """An example endpoint protected by the 'admin' permission."""
    return {"message": f"Welcome, admin {user['email']}!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
