#!/usr/bin/env python3

import os
import jwt
import json
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

app = FastAPI(
    title="Authentication Service",
    description="Serviço de autenticação centralizado com Google OAuth - Vértice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://*.vertice.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
JWT_SECRET = os.getenv("JWT_SECRET", "vertice-super-secret-key-2024")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Redis connection
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except:
    redis_client = None

# Security
security = HTTPBearer()

# Models
class GoogleTokenRequest(BaseModel):
    token: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]

class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    verified_email: bool
    hd: Optional[str] = None  # Hosted domain for G Suite

class AuthStatus(BaseModel):
    authenticated: bool
    user: Optional[UserInfo] = None
    permissions: list = []

# Authorized domains/emails
AUTHORIZED_DOMAINS = os.getenv("AUTHORIZED_DOMAINS", "").split(",")
AUTHORIZED_EMAILS = os.getenv("AUTHORIZED_EMAILS", "").split(",")

# Permission levels
PERMISSION_LEVELS = {
    "admin": ["read", "write", "delete", "offensive", "admin"],
    "analyst": ["read", "write", "offensive"],
    "viewer": ["read"],
    "guest": []
}

# Admin emails (can access offensive tools) - Juan é o admin principal
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "juan.brainfarma@gmail.com").split(",")

# Juan sempre tem acesso completo, independente das configurações
SUPER_ADMIN_EMAIL = "juan.brainfarma@gmail.com"

async def verify_google_token(token: str) -> Dict[str, Any]:
    """Verify Google OAuth token and get user info"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={token}"
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")

            user_info = response.json()

            # Verify user is authorized
            if not is_authorized_user(user_info):
                raise HTTPException(status_code=403, detail="User not authorized")

            return user_info
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to verify Google token")

def is_authorized_user(user_info: Dict[str, Any]) -> bool:
    """Check if user is authorized to access the system"""
    email = user_info.get("email", "").lower()
    domain = email.split("@")[-1] if "@" in email else ""

    # Juan sempre tem acesso completo - super admin
    if email == SUPER_ADMIN_EMAIL.lower():
        return True

    # Check authorized emails
    if email in [e.lower() for e in AUTHORIZED_EMAILS if e]:
        return True

    # Check authorized domains
    if domain in [d.lower() for d in AUTHORIZED_DOMAINS if d]:
        return True

    # Check if it's a verified email
    if not user_info.get("verified_email", False):
        return False

    # For development, allow any Gmail if no restrictions set
    if not AUTHORIZED_EMAILS[0] and not AUTHORIZED_DOMAINS[0]:
        return True

    return False

def get_user_permissions(user_info: Dict[str, Any]) -> list:
    """Get user permissions based on email and role"""
    email = user_info.get("email", "").lower()

    # Juan sempre tem permissões de super admin
    if email == SUPER_ADMIN_EMAIL.lower():
        return PERMISSION_LEVELS["admin"]

    # Outros admins também têm permissões completas
    if email in [e.lower() for e in ADMIN_EMAILS if e]:
        return PERMISSION_LEVELS["admin"]

    # Check domain for role assignment
    domain = email.split("@")[-1] if "@" in email else ""

    # Default permissions for authorized users
    if domain in [d.lower() for d in AUTHORIZED_DOMAINS if d]:
        return PERMISSION_LEVELS["analyst"]

    return PERMISSION_LEVELS["viewer"]

def create_jwt_token(user_info: Dict[str, Any]) -> str:
    """Create JWT token for authenticated user"""
    permissions = get_user_permissions(user_info)

    payload = {
        "sub": user_info["id"],
        "email": user_info["email"],
        "name": user_info["name"],
        "picture": user_info["picture"],
        "permissions": permissions,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
        "iss": "vertice-auth-service"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Store token in Redis for session management
    if redis_client:
        try:
            redis_client.setex(
                f"session:{user_info['id']}",
                TOKEN_EXPIRE_HOURS * 3600,
                json.dumps(payload, default=str)
            )
        except:
            pass

    return token

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Check if session exists in Redis
        if redis_client:
            try:
                session_data = redis_client.get(f"session:{payload['sub']}")
                if not session_data:
                    raise HTTPException(status_code=401, detail="Session expired")
            except:
                pass

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    return verify_jwt_token(credentials.credentials)

def require_permission(permission: str):
    """Dependency factory to require specific permission"""
    def permission_dependency(user: Dict[str, Any] = Depends(get_current_user)):
        if permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )
        return user
    return permission_dependency

# Routes

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "redis_connected": redis_client is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/auth/google", response_model=LoginResponse)
async def authenticate_with_google(request: GoogleTokenRequest):
    """Authenticate user with Google OAuth token"""
    try:
        user_info = await verify_google_token(request.token)
        jwt_token = create_jwt_token(user_info)

        return LoginResponse(
            access_token=jwt_token,
            token_type="Bearer",
            expires_in=TOKEN_EXPIRE_HOURS * 3600,
            user_info=user_info
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/auth/me", response_model=AuthStatus)
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return AuthStatus(
        authenticated=True,
        user=UserInfo(
            id=user["sub"],
            email=user["email"],
            name=user["name"],
            picture=user["picture"],
            verified_email=True
        ),
        permissions=user.get("permissions", [])
    )

@app.post("/auth/logout")
async def logout(user: Dict[str, Any] = Depends(get_current_user)):
    """Logout user and invalidate session"""
    if redis_client:
        try:
            redis_client.delete(f"session:{user['sub']}")
        except:
            pass

    return {"message": "Successfully logged out"}

@app.get("/auth/verify-token")
async def verify_token(user: Dict[str, Any] = Depends(get_current_user)):
    """Verify token validity"""
    return {
        "valid": True,
        "user_id": user["sub"],
        "permissions": user.get("permissions", [])
    }

@app.get("/auth/permissions")
async def get_permissions(user: Dict[str, Any] = Depends(get_current_user)):
    """Get user permissions"""
    return {
        "permissions": user.get("permissions", []),
        "can_access_offensive": "offensive" in user.get("permissions", [])
    }

# Protected endpoint examples
@app.get("/protected/admin")
async def admin_only(user: Dict[str, Any] = Depends(require_permission("admin"))):
    """Admin only endpoint"""
    return {"message": "Admin access granted", "user": user["email"]}

@app.get("/protected/offensive")
async def offensive_tools(user: Dict[str, Any] = Depends(require_permission("offensive"))):
    """Offensive tools access"""
    return {"message": "Offensive tools access granted", "user": user["email"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)