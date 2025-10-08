"""Maximus Authentication Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Authentication
Service. It initializes and configures the FastAPI application, sets up event
handlers for startup and shutdown, and defines the API endpoints for user
authentication, authorization, and token management.

It handles user registration, login, token issuance and validation, and ensures
secure access to all Maximus AI services. This service is critical for maintaining
the security and integrity of the entire Maximus AI ecosystem.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt  # bcrypt
import jwt  # PyJWT
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# Configuration for JWT
SECRET_KEY = "your-super-secret-key"  # In production, use a strong, environment-variable-based key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Maximus Authentication Service", version="1.0.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock User Database (In a real app, this would be a proper database)
users_db = {
    "maximus_admin": {
        "username": "maximus_admin",
        "hashed_password": bcrypt.hashpw("adminpass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        "roles": ["admin", "user"],
    },
    "maximus_user": {
        "username": "maximus_user",
        "hashed_password": bcrypt.hashpw("userpass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        "roles": ["user"],
    },
}


class Token(BaseModel):
    """Response model for JWT token.

    Attributes:
        access_token (str): The JWT access token.
        token_type (str): The type of token (e.g., 'bearer').
    """

    access_token: str
    token_type: str


class User(BaseModel):
    """User model for registration and profile.

    Attributes:
        username (str): The username of the user.
        roles (List[str]): List of roles assigned to the user.
    """

    username: str
    roles: List[str]


class UserInDB(User):
    """User model including hashed password for database storage.

    Attributes:
        hashed_password (str): The hashed password of the user.
    """

    hashed_password: str


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """Creates a JWT access token.

    Args:
        data (Dict[str, Any]): The data to encode into the token.
        expires_delta (Optional[timedelta]): Optional timedelta for token expiration.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user(username: str) -> Optional[UserInDB]:
    """Retrieves a user from the mock database by username.

    Args:
        username (str): The username to retrieve.

    Returns:
        Optional[UserInDB]: The UserInDB object if found, None otherwise.
    """
    user_data = users_db.get(username)
    if user_data:
        return UserInDB(**user_data)
    return None


async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticates a user against the mock database.

    Args:
        username (str): The username.
        password (str): The plain-text password.

    Returns:
        Optional[UserInDB]: The authenticated UserInDB object if successful, None otherwise.
    """
    user = await get_user(username)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Retrieves the current authenticated user from the JWT token.

    Args:
        token (str): The JWT token from the request header.

    Returns:
        User: The authenticated User object.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = await get_user(username)
        if user is None:
            raise credentials_exception
        return User(username=user.username, roles=user.roles)
    except jwt.PyJWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Retrieves the current active authenticated user.

    Args:
        current_user (User): The authenticated user object.

    Returns:
        User: The active User object.

    Raises:
        HTTPException: If the user is inactive (not applicable in this mock).
    """
    # In a real app, you might check if the user is active/enabled
    return current_user


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Authentication Service."""
    print("🔑 Starting Maximus Authentication Service...")
    print("✅ Maximus Authentication Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Authentication Service."""
    print("👋 Shutting down Maximus Authentication Service...")
    print("🛑 Maximus Authentication Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Authentication Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Authentication Service is operational."}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticates a user and returns an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data containing username and password.

    Returns:
        Token: The JWT access token.

    Raises:
        HTTPException: If authentication fails.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retrieves the current authenticated user's information.

    Args:
        current_user (User): The authenticated user object.

    Returns:
        User: The current user's information.
    """
    return current_user


@app.get("/admin_resource")
async def read_admin_resource(current_user: User = Depends(get_current_active_user)):
    """Accesses a resource that requires 'admin' role.

    Args:
        current_user (User): The authenticated user object.

    Returns:
        Dict[str, str]: A message indicating successful access.

    Raises:
        HTTPException: If the user does not have the 'admin' role.
    """
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return {"message": "Welcome, admin! This is a highly sensitive resource."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
