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
from sqlalchemy.orm import Session

from database import User, get_db, init_db

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


# Configuration for JWT
SECRET_KEY = "your-super-secret-key"  # In production, use a strong, environment-variable-based key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Maximus Authentication Service", version="1.0.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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


async def get_user(username: str, db: Session) -> Optional[UserInDB]:
    """Retrieves a user from the database by username.

    Args:
        username (str): The username to retrieve.
        db (Session): Database session.

    Returns:
        Optional[UserInDB]: The UserInDB object if found, None otherwise.
    """
    user = db.query(User).filter(User.username == username).first()
    if user:
        return UserInDB(
            username=user.username,
            hashed_password=user.hashed_password,
            roles=user.roles
        )
    return None


async def authenticate_user(username: str, password: str, db: Session) -> Optional[UserInDB]:
    """Authenticates a user against the database.

    Args:
        username (str): The username.
        password (str): The plain-text password.
        db (Session): Database session.

    Returns:
        Optional[UserInDB]: The authenticated UserInDB object if successful, None otherwise.
    """
    user = await get_user(username, db)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
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
        user = await get_user(username, db)
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

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="auth_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="auth_service",
            version=service_version
        )
        auto_update_sabbath_status("auth_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="auth_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="auth_service")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {e}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()

    print("🔑 Starting Maximus Authentication Service...")
    init_db()
    print("✅ Database initialized with default users")
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
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticates a user and returns an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data containing username and password.
        db (Session): Database session.

    Returns:
        Token: The JWT access token.

    Raises:
        HTTPException: If authentication fails.
    """
    user = await authenticate_user(form_data.username, form_data.password, db)
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
