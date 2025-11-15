"""API Versioning Strategy for Vértice Platform.

This module implements comprehensive API versioning following industry best practices:
- Explicit version prefixes (/api/v1/, /api/v2/)
- Legacy route support with redirects
- Deprecation headers (Sunset, Deprecation)
- Version negotiation via headers
- Clear migration paths

Following Boris Cherny's principle: "Breaking changes must be explicit"
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_308_PERMANENT_REDIRECT


class APIVersion(str, Enum):
    """Supported API versions.

    Each version represents a major API contract change.
    Backward compatibility is NOT guaranteed between versions.
    """

    V1 = "v1"
    V2 = "v2"  # Future: For breaking changes


class VersionInfo:
    """Metadata about API version lifecycle.

    Tracks deprecation status, sunset dates, and migration guidance
    for each API version.

    Attributes:
        version: The API version (v1, v2, etc.)
        deprecated: Whether this version is deprecated
        sunset_date: When this version will be removed (if deprecated)
        migration_guide: URL to migration documentation

    Example:
        >>> v1_info = VersionInfo(
        ...     version=APIVersion.V1,
        ...     deprecated=False
        ... )
    """

    def __init__(
        self,
        version: APIVersion,
        deprecated: bool = False,
        sunset_date: Optional[datetime] = None,
        migration_guide: Optional[str] = None,
    ):
        self.version = version
        self.deprecated = deprecated
        self.sunset_date = sunset_date
        self.migration_guide = migration_guide


# ============================================================================
# Version Registry
# ============================================================================
# Define lifecycle for each API version
VERSION_REGISTRY = {
    APIVersion.V1: VersionInfo(
        version=APIVersion.V1,
        deprecated=False,
        sunset_date=None,
        migration_guide=None,
    ),
    # When V2 is released:
    # APIVersion.V2: VersionInfo(
    #     version=APIVersion.V2,
    #     deprecated=False,
    # ),
}

# Current stable version (recommended for new integrations)
CURRENT_VERSION = APIVersion.V1


# ============================================================================
# Version Headers Middleware
# ============================================================================
async def add_version_headers_middleware(request: Request, call_next):
    """Add API version headers to all responses.

    This middleware adds the following headers:
    - X-API-Version: Current API version (e.g., "v1")
    - Deprecation: "true" if endpoint is deprecated
    - Sunset: ISO 8601 date when endpoint will be removed
    - Link: URL to successor version documentation

    Args:
        request: The incoming request
        call_next: Next middleware in chain

    Returns:
        Response with version headers added

    Example Response Headers:
        X-API-Version: v1
        Deprecation: true
        Sunset: Wed, 01 Jan 2026 00:00:00 GMT
        Link: </api/v2/docs>; rel="successor-version"
    """
    response = await call_next(request)

    # Determine version from request path
    path = request.url.path
    version = None

    if "/api/v1/" in path:
        version = APIVersion.V1
    elif "/api/v2/" in path:
        version = APIVersion.V2
    else:
        # Legacy endpoint (no version in path)
        version = None

    # Add version header
    if version:
        response.headers["X-API-Version"] = version.value

        # Add deprecation headers if applicable
        version_info = VERSION_REGISTRY.get(version)
        if version_info and version_info.deprecated:
            response.headers["Deprecation"] = "true"

            if version_info.sunset_date:
                # Format as HTTP date
                sunset_http = version_info.sunset_date.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
                response.headers["Sunset"] = sunset_http

            if version_info.migration_guide:
                response.headers["Link"] = (
                    f'<{version_info.migration_guide}>; rel="successor-version"'
                )

    return response


# ============================================================================
# Legacy Route Redirector
# ============================================================================
def create_legacy_redirect(
    legacy_path: str,
    new_path: str,
    deprecation_message: Optional[str] = None
) -> RedirectResponse:
    """Create a permanent redirect from legacy route to versioned route.

    This helper creates 308 Permanent Redirects for legacy routes,
    ensuring backward compatibility while encouraging migration.

    Args:
        legacy_path: Old path without version (e.g., "/health")
        new_path: New versioned path (e.g., "/api/v1/health")
        deprecation_message: Custom deprecation warning

    Returns:
        RedirectResponse with 308 status code

    Example:
        @app.get("/health")
        async def health_legacy():
            return create_legacy_redirect("/health", "/api/v1/health")
    """
    response = RedirectResponse(
        url=new_path,
        status_code=HTTP_308_PERMANENT_REDIRECT
    )

    # Add deprecation headers
    response.headers["Deprecation"] = "true"
    response.headers["X-Deprecated-Endpoint"] = legacy_path
    response.headers["X-New-Endpoint"] = new_path

    if deprecation_message:
        response.headers["X-Deprecation-Message"] = deprecation_message
    else:
        response.headers["X-Deprecation-Message"] = (
            f"This endpoint is deprecated. Use {new_path} instead."
        )

    return response


# ============================================================================
# Version Negotiation
# ============================================================================
def negotiate_version(request: Request) -> APIVersion:
    """Negotiate API version from request.

    Version can be specified via:
    1. URL path (/api/v1/...)  ← Preferred
    2. Accept header (Accept: application/vnd.vertice.v1+json)
    3. Custom header (X-API-Version: v1)

    Args:
        request: The incoming request

    Returns:
        Negotiated API version (defaults to CURRENT_VERSION)

    Example:
        version = negotiate_version(request)
        if version == APIVersion.V2:
            # Use V2 logic
    """
    # 1. Check URL path (highest priority)
    path = request.url.path
    if "/api/v2/" in path:
        return APIVersion.V2
    elif "/api/v1/" in path:
        return APIVersion.V1

    # 2. Check custom header
    version_header = request.headers.get("X-API-Version", "").lower()
    if version_header == "v2":
        return APIVersion.V2
    elif version_header == "v1":
        return APIVersion.V1

    # 3. Check Accept header
    accept = request.headers.get("Accept", "")
    if "vnd.vertice.v2" in accept:
        return APIVersion.V2
    elif "vnd.vertice.v1" in accept:
        return APIVersion.V1

    # Default to current stable version
    return CURRENT_VERSION


# ============================================================================
# Version Compatibility Helpers
# ============================================================================
def is_version_compatible(
    requested: APIVersion,
    required: APIVersion
) -> bool:
    """Check if requested version satisfies required version.

    Args:
        requested: The API version being used
        required: The minimum version required

    Returns:
        True if compatible, False otherwise

    Example:
        if not is_version_compatible(request_version, APIVersion.V2):
            raise HTTPException(
                status_code=426,
                detail="This endpoint requires API v2 or higher"
            )
    """
    version_order = {
        APIVersion.V1: 1,
        APIVersion.V2: 2,
    }

    return version_order.get(requested, 0) >= version_order.get(required, 0)


def get_version_info(version: APIVersion) -> Optional[VersionInfo]:
    """Get metadata for a specific API version.

    Args:
        version: The API version to query

    Returns:
        VersionInfo object or None if version doesn't exist

    Example:
        info = get_version_info(APIVersion.V1)
        if info.deprecated:
            print(f"Warning: v1 will sunset on {info.sunset_date}")
    """
    return VERSION_REGISTRY.get(version)
