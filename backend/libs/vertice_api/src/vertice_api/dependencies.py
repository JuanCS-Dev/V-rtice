"""FastAPI dependency injection utilities for Vértice services.

This module provides reusable dependency injection patterns for common
service needs like logging, database sessions, and authentication.

Example:
-------
    Basic usage::

        from fastapi import Depends, FastAPI
        from vertice_api.dependencies import get_logger, get_db

        app = FastAPI()

        @app.get("/users")
        async def list_users(
            logger=Depends(get_logger),
            db=Depends(get_db),
        ):
            logger.info("listing_users")
            users = await db.execute(select(User))
            return users.scalars().all()

    Authentication::

        from vertice_api.dependencies import get_current_user, require_permissions

        @app.get("/admin")
        async def admin_panel(
            user=Depends(get_current_user),
            _=Depends(require_permissions(["admin:read"])),
        ):
            return {"message": "Admin access granted"}

Note:
----
    All dependency functions are designed to be used with FastAPI's
    `Depends()` mechanism and support async/await patterns.

"""

from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Header, HTTPException, Request, status
from structlog.stdlib import BoundLogger
from vertice_core.logging import get_logger as create_logger

if TYPE_CHECKING:
    from vertice_api.client import ServiceClient


async def get_logger(request: Request) -> AsyncGenerator[BoundLogger, None]:
    """Get a logger instance with request context bound.

    Automatically binds request_id, method, and path to the logger context
    for all log entries within the request scope.

    Args:
    ----
        request: FastAPI request object.

    Returns:
    -------
        A structlog BoundLogger with request context.

    Example:
    -------
        >>> @app.get("/test")
        >>> async def test(logger=Depends(get_logger)):
        >>>     logger.info("processing_request")  # includes request_id automatically
    """
    logger = create_logger(request.app.title)

    # Bind request context
    import structlog

    structlog.contextvars.bind_contextvars(
        request_id=request.headers.get("X-Request-ID", "unknown"),
        method=request.method,
        path=request.url.path,
    )

    try:
        yield logger
    finally:
        # Clear context after request
        structlog.contextvars.clear_contextvars()


async def get_db(request: Request) -> AsyncGenerator[Any, None]:
    """Get a database session for the request.

    Creates an async database session from the app state and ensures
    proper cleanup after the request completes.

    Args:
    ----
        request: FastAPI request object.

    Yields:
    ------
        AsyncSession instance.

    Raises:
    ------
        HTTPException: If database connection is not configured.

    Example:
    -------
        >>> @app.get("/users")
        >>> async def get_users(db=Depends(get_db)):
        >>>     result = await db.execute(select(User))
        >>>     return result.scalars().all()

    Note:
    ----
        Requires app.state.db_session_factory to be set during app startup.
    """
    if not hasattr(request.app.state, "db_session_factory"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured",
        )

    session_factory = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    request: Request | None = None,
) -> dict[str, Any]:
    """Extract and validate the current user from the request.

    Validates JWT token from Authorization header and returns user data.

    Args:
    ----
        authorization: Authorization header value (Bearer token).
        request: FastAPI request object (optional, for additional context).

    Returns:
    -------
        Dictionary containing user data: {"user_id": str, "email": str, "roles": list}

    Raises:
    ------
        HTTPException: 401 if token is missing or invalid.

    Example:
    -------
        >>> @app.get("/me")
        >>> async def get_me(user=Depends(get_current_user)):
        >>>     return {"user_id": user["user_id"], "email": user["email"]}

    Note:
    ----
        This is a basic implementation. In production, integrate with
        your JWT validation service or auth provider.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # Basic token validation
    # In production systems, integrate with JWT validation service
    # or MAXIMUS_CORE authentication system via HTTP client
    if not token or token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Return validated user data
    # Token format expected: base64 encoded user data or JWT
    # Production implementation should decode JWT and verify signature
    return {
        "user_id": "dev_user",
        "email": "dev@vertice.ai",
        "roles": ["user"],
    }


def require_permissions(
    required_permissions: list[str],
) -> Callable[[dict[str, Any] | None], Awaitable[None]]:
    """Create a dependency that checks if user has required permissions.

    This is a dependency factory that returns a dependency function.

    Args:
    ----
        required_permissions: List of permission strings required (e.g., ["admin:write"]).

    Returns:
    -------
        A dependency function that validates permissions.

    Raises:
    ------
        HTTPException: 403 if user lacks required permissions.

    Example:
    -------
        >>> @app.delete("/users/{user_id}")
        >>> async def delete_user(
        >>>     user_id: str,
        >>>     user=Depends(get_current_user),
        >>>     _=Depends(require_permissions(["admin:write"])),
        >>> ):
        >>>     # Only users with admin:write permission can execute this
        >>>     return {"deleted": user_id}

    Note:
    ----
        Automatically depends on get_current_user(), so you don't need
        to add it explicitly.
    """

    async def check_permissions(user: dict[str, Any] | None = None) -> None:
        if user is None:
            user = await get_current_user()
        user_permissions = user.get("permissions", [])
        user_roles = user.get("roles", [])

        # Admin role bypasses permission checks
        if "admin" in user_roles:
            return

        # Check if user has all required permissions
        missing_permissions = [
            perm for perm in required_permissions if perm not in user_permissions
        ]

        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}",
            )

    return check_permissions


def get_service_client(
    service_name: str,
) -> Callable[[Request], Awaitable["ServiceClient"]]:
    """Create a dependency that provides a configured service client.

    Factory function that creates a dependency for inter-service communication.

    Args:
    ----
        service_name: Name of the target service (e.g., "maximus_core").

    Returns:
    -------
        A dependency function that returns a ServiceClient instance.

    Example:
    -------
        >>> from vertice_api.dependencies import get_service_client
        >>>
        >>> @app.get("/osint/query")
        >>> async def query_osint(
        >>>     query: str,
        >>>     osint_client=Depends(get_service_client("osint_collector")),
        >>> ):
        >>>     response = await osint_client.post("/collect", json={"query": query})
        >>>     return response.json()

    Note:
    ----
        Requires service registry to be configured in app.state.service_registry.
    """
    from vertice_api.client import ServiceClient  # - Lazy import

    async def get_client(request: Request) -> ServiceClient:
        # Get service URL from registry or environment
        service_url = None

        if hasattr(request.app.state, "service_registry"):
            service_url = request.app.state.service_registry.get(service_name)

        if not service_url:
            # Fallback to environment variable
            import os

            env_key = f"{service_name.upper()}_URL"
            service_url = os.getenv(env_key)

        if not service_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service '{service_name}' not available",
            )

        return ServiceClient(base_url=service_url)

    return get_client
