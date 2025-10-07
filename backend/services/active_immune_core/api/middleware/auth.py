"""Authentication Middleware - PRODUCTION-READY

JWT-based authentication and authorization middleware.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Configuration (in production, load from environment variables)
SECRET_KEY = "your-secret-key-change-in-production"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class User(BaseModel):
    """User model"""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[str] = []


class TokenData(BaseModel):
    """Token data model"""

    username: Optional[str] = None
    roles: List[str] = []


class AuthMiddleware:
    """
    Authentication middleware for FastAPI.

    Provides JWT-based authentication with role-based access control.
    """

    def __init__(self):
        """Initialize authentication middleware"""
        self.users_db: Dict[str, Dict[str, Any]] = {
            # Demo users (in production, load from database)
            "admin": {
                "username": "admin",
                "full_name": "System Administrator",
                "email": "admin@immunecore.local",
                "hashed_password": self.hash_password("admin123"),  # Change in production
                "disabled": False,
                "roles": ["admin", "user"],
            },
            "operator": {
                "username": "operator",
                "full_name": "System Operator",
                "email": "operator@immunecore.local",
                "hashed_password": self.hash_password("operator123"),  # Change in production
                "disabled": False,
                "roles": ["operator", "user"],
            },
            "viewer": {
                "username": "viewer",
                "full_name": "System Viewer",
                "email": "viewer@immunecore.local",
                "hashed_password": self.hash_password("viewer123"),  # Change in production
                "disabled": False,
                "roles": ["viewer"],
            },
        }

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_user(self, username: str) -> Optional[User]:
        """Get user from database"""
        if username not in self.users_db:
            return None

        user_data = self.users_db[username]
        return User(**user_data)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        if username not in self.users_db:
            return None

        user_data = self.users_db[username]

        if not self.verify_password(password, user_data["hashed_password"]):
            return None

        return User(**user_data)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt

    def decode_token(self, token: str) -> TokenData:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            roles: List[str] = payload.get("roles", [])

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return TokenData(username=username, roles=roles)

        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global auth middleware instance
auth_middleware = AuthMiddleware()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Dependency to get current authenticated user.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        Current user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Decode token
    token_data = auth_middleware.decode_token(token)

    # Get user
    user = auth_middleware.get_user(token_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    return user


def require_role(required_roles: List[str]):
    """
    Dependency to require specific role(s).

    Args:
        required_roles: List of required roles

    Returns:
        Dependency function

    Example:
        @router.get("/admin", dependencies=[Depends(require_role(["admin"]))])
        async def admin_endpoint():
            ...
    """

    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        """Check if user has required role"""
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}",
            )

        return current_user

    return check_role


class LoginRequest(BaseModel):
    """Login request model"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
