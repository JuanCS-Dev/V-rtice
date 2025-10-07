"""Authentication and authorization for Ethical Audit Service.

Implements JWT-based authentication and RBAC (Role-Based Access Control).
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
import os
from typing import List, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_VIA_ENV_VAR")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# Warn if using default secret
if SECRET_KEY == "CHANGE_THIS_IN_PRODUCTION_VIA_ENV_VAR":
    logger.warning("⚠️  Using default JWT secret - CHANGE THIS IN PRODUCTION!")

security = HTTPBearer()


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    SOC_OPERATOR = "soc_operator"
    SECURITY_ENGINEER = "security_engineer"
    AUDITOR = "auditor"
    READONLY = "readonly"


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    user_id: str
    username: str
    roles: List[str]


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token.

    Args:
        data: Data to encode in token (must include 'sub' for user_id)
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData object with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username", "unknown")
        roles: List[str] = payload.get("roles", [])

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug(
            f"Token decoded successfully for user: {username} (roles: {roles})"
        )
        return TokenData(user_id=user_id, username=username, roles=roles)

    except jwt.ExpiredSignatureError:
        logger.warning("Expired token rejected")
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        logger.warning(f"Invalid token rejected: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> TokenData:
    """Dependency to get current authenticated user from JWT.

    Args:
        credentials: HTTP authorization credentials (Bearer token)

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return decode_token(token)


def require_role(required_roles: List[UserRole]):
    """Dependency factory to require specific roles.

    Args:
        required_roles: List of roles required to access the endpoint

    Returns:
        Dependency function that checks user roles
    """

    async def role_checker(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        """Check if user has required role.

        Args:
            current_user: Current authenticated user

        Returns:
            TokenData if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        user_roles = set(current_user.roles)
        required_role_names = set(role.value for role in required_roles)

        # Admin has access to everything
        if UserRole.ADMIN.value in user_roles:
            return current_user

        # Check if user has any of the required roles
        if not user_roles.intersection(required_role_names):
            logger.warning(
                f"Access denied for user {current_user.username}: "
                f"required {required_role_names}, has {user_roles}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {required_role_names}",
            )

        logger.debug(f"Access granted for user {current_user.username}")
        return current_user

    return role_checker


# Convenience dependencies for common role requirements
require_admin = require_role([UserRole.ADMIN])
require_soc_or_admin = require_role([UserRole.SOC_OPERATOR, UserRole.ADMIN])
require_auditor_or_admin = require_role([UserRole.AUDITOR, UserRole.ADMIN])
require_any_role = get_current_user  # Just need to be authenticated
