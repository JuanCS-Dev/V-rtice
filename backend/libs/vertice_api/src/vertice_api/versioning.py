"""API versioning utilities for Vértice services.

This module provides middleware and decorators for managing API versions
using header-based versioning strategy.

Example:
-------
    Basic setup::

        from fastapi import FastAPI
        from vertice_api.versioning import APIVersionMiddleware, version

        app = FastAPI()
        app.add_middleware(APIVersionMiddleware, default_version="v1")

        @app.get("/users")
        @version("v1")
        async def list_users_v1():
            return {"version": "v1", "users": []}

        @app.get("/users")
        @version("v2")
        async def list_users_v2():
            return {"version": "v2", "users": [], "pagination": {}}

    Version negotiation::

        # Client sends:
        # GET /users
        # Accept-Version: v2
        #
        # Server responds with v2 endpoint

    Deprecation::

        @app.get("/old-endpoint")
        @version("v1", deprecated=True, sunset_date="2025-12-31")
        async def old_endpoint():
            return {"message": "This endpoint is deprecated"}
            # Response includes: Sunset: Sat, 31 Dec 2025 23:59:59 GMT

Note:
----
    - Version format: "v{major}" (e.g., v1, v2, v3)
    - Versioning via Accept-Version header (fallback to query param)
    - Automatic deprecation warnings via Sunset header

"""

import asyncio
import re
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

if TYPE_CHECKING:
    pass

P = ParamSpec("P")
R = TypeVar("R")


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware for API version negotiation.

    Extracts version from Accept-Version header or ?version query param,
    validates it, and stores in request.state for route handlers.

    Args:
    ----
        app: ASGI application.
        default_version: Default version to use if client doesn't specify (default: "v1").
        supported_versions: List of supported versions (default: ["v1"]).
        strict: If True, reject requests with unsupported versions (default: False).

    Attributes:
    ----------
        default_version: The fallback version.
        supported_versions: Set of valid version strings.
        strict: Whether to enforce version validation.

    Example:
    -------
        >>> app = FastAPI()
        >>> app.add_middleware(
        >>>     APIVersionMiddleware,
        >>>     default_version="v1",
        >>>     supported_versions=["v1", "v2", "v3"],
        >>>     strict=True,
        >>> )
    """

    def __init__(
        self,
        app: ASGIApp,
        default_version: str = "v1",
        supported_versions: list[str] | None = None,
        strict: bool = False,
    ) -> None:
        super().__init__(app)
        self.default_version = default_version
        self.supported_versions = set(supported_versions or [default_version])
        self.strict = strict

        # Validate default version is in supported versions
        if default_version not in self.supported_versions:
            raise ValueError(
                f"default_version '{default_version}' must be in supported_versions",
            )

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Process request and add version information.

        Args:
        ----
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
        -------
            HTTP response with version headers.

        Raises:
        ------
            HTTPException: 400 if version format is invalid or unsupported (strict mode).
        """
        # Extract version from header or query param
        version = (
            request.headers.get("Accept-Version")
            or request.query_params.get("version")
            or self.default_version
        )

        # Validate version format (v{number})
        if not re.match(r"^v\d+$", version):
            if self.strict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid version format: '{version}'. Must be v1, v2, etc.",
                )
            version = self.default_version

        # Check if version is supported
        if version not in self.supported_versions:
            if self.strict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported version: '{version}'. "
                    f"Supported: {', '.join(sorted(self.supported_versions))}",
                )
            version = self.default_version

        # Store version in request state
        request.state.api_version = version

        # Call next middleware/handler
        response = await call_next(request)

        # Add version to response headers
        response.headers["X-API-Version"] = version

        return response  # type: ignore[no-any-return]


def version(
    api_version: str,
    deprecated: bool = False,
    sunset_date: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark endpoint as specific API version.

    Args:
    ----
        api_version: Version string (e.g., "v1", "v2").
        deprecated: Whether this version is deprecated.
        sunset_date: ISO date when version will be removed (e.g., "2025-12-31").

    Returns:
    -------
        Decorator function.

    Raises:
    ------
        HTTPException: 410 Gone if accessing endpoint after sunset date.

    Example:
    -------
        >>> @app.get("/users")
        >>> @version("v1", deprecated=True, sunset_date="2025-12-31")
        >>> async def list_users_v1():
        >>>     return []

        >>> @app.get("/users")
        >>> @version("v2")
        >>> async def list_users_v2():
        >>>     return {"users": [], "pagination": {}}

    Note:
    ----
        - Endpoints with different versions can share the same path
        - Middleware selects correct handler based on Accept-Version header
        - Deprecated endpoints include Sunset header in response
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            # Extract request from kwargs (FastAPI injects it)
            request = kwargs.get("request")
            if not request:
                # Try to find Request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            # Check if request version matches endpoint version
            if (
                request
                and hasattr(request, "state")
                and hasattr(request.state, "api_version")
                and request.state.api_version != api_version
            ):
                # Version mismatch - skip this endpoint
                # FastAPI will try other endpoints with same path
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Endpoint not available for version {request.state.api_version}",
                )

            # Check sunset date
            if sunset_date:
                sunset_datetime = datetime.fromisoformat(sunset_date)
                if datetime.now() > sunset_datetime:
                    raise HTTPException(
                        status_code=status.HTTP_410_GONE,
                        detail=f"API version {api_version} was sunset on {sunset_date}",
                    )

            # Call original function
            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

            # Add deprecation headers if needed
            if request and deprecated:
                response = kwargs.get("response")
                if response and isinstance(response, Response):
                    response.headers["Deprecation"] = "true"
                    if sunset_date:
                        # RFC 8594 format
                        sunset_dt = datetime.fromisoformat(sunset_date)
                        response.headers["Sunset"] = sunset_dt.strftime(
                            "%a, %d %b %Y %H:%M:%S GMT",
                        )
                    response.headers["Link"] = (
                        f'<https://docs.vertice.ai/migration/{api_version}>; rel="deprecation"'
                    )

            return result

        # Store version metadata (type ignore for dynamic attributes)
        wrapper.__api_version__ = api_version  # type: ignore[attr-defined]
        wrapper.__deprecated__ = deprecated  # type: ignore[attr-defined]
        wrapper.__sunset_date__ = sunset_date  # type: ignore[attr-defined]

        return wrapper  # type: ignore[return-value]

    return decorator


def get_request_version(request: Request) -> str:
    """Extract API version from request state.

    Args:
    ----
        request: FastAPI request object.

    Returns:
    -------
        Version string (e.g., "v1", "v2").

    Raises:
    ------
        ValueError: If version not set in request state.

    Example:
    -------
        >>> from vertice_api.versioning import get_request_version
        >>>
        >>> @app.get("/info")
        >>> async def get_info(request: Request):
        >>>     version = get_request_version(request)
        >>>     return {"version": version, "features": get_features(version)}
    """
    if not hasattr(request.state, "api_version"):
        raise ValueError(
            "API version not set. Ensure APIVersionMiddleware is installed.",
        )
    return request.state.api_version  # type: ignore[no-any-return]


def version_range(min_version: str, max_version: str | None = None) -> Callable[..., Any]:
    """Decorator to mark endpoint as available in a range of versions.

    Args:
    ----
        min_version: Minimum version (inclusive), e.g., "v1".
        max_version: Maximum version (inclusive), e.g., "v3". None = no max.

    Returns:
    -------
        Decorator function.

    Example:
    -------
        >>> @app.get("/legacy")
        >>> @version_range("v1", "v2")
        >>> async def legacy_endpoint():
        >>>     # Available in v1 and v2 only
        >>>     return {"message": "Legacy"}

        >>> @app.get("/new")
        >>> @version_range("v3")
        >>> async def new_endpoint():
        >>>     # Available in v3 and above
        >>>     return {"message": "New"}
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request) or (
                        hasattr(arg, "state") and hasattr(arg, "method")
                    ):
                        request = arg
                        break

            if (
                request
                and hasattr(request, "state")
                and hasattr(request.state, "api_version")
            ):
                current_version = request.state.api_version
                current_major = int(current_version[1:])  # Extract number from v1, v2, etc.
                min_major = int(min_version[1:])

                if current_major < min_major:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Endpoint requires version >= {min_version}",
                    )

                if max_version:
                    max_major = int(max_version[1:])
                    if current_major > max_major:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Endpoint removed in version > {max_version}",
                        )

            return (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

        return wrapper  # type: ignore[return-value]

    return decorator
