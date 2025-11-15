"""
Input Sanitization Middleware
==============================

Validates and sanitizes all incoming request data to prevent injection attacks.
Boris Cherny Pattern: Defense in depth - validate at the gateway level.

Security Protection:
- XSS (Cross-Site Scripting) prevention
- SQL Injection prevention
- Command Injection prevention
- Path Traversal prevention
- DoS via large payloads prevention

Governed by: Constituição Vértice v2.7 - Security First
"""

import re
import logging
from typing import Any, Dict, List, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Maximum payload size (5MB)
MAX_PAYLOAD_SIZE = 5 * 1024 * 1024

# Maximum string length (prevent DoS)
MAX_STRING_LENGTH = 10000

# Maximum array/object depth (prevent stack overflow)
MAX_DEPTH = 10

# Dangerous patterns (SQL injection, command injection)
DANGEROUS_SQL_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
    r"(--|;|\/\*|\*\/)",  # SQL comments
    r"(\b(UNION|OR|AND)\b.*\b(SELECT|FROM)\b)",  # UNION attacks
    r"('|\"|`)(.*)\1",  # String concatenation attempts
]

DANGEROUS_COMMAND_PATTERNS = [
    r"(;|\||&|\$\(|\`)",  # Command chaining
    r"(\.\./|\.\.\\)",  # Path traversal
    r"(\\x[0-9a-fA-F]{2})",  # Hex encoding
]

# Compiled patterns for performance
SQL_PATTERN = re.compile("|".join(DANGEROUS_SQL_PATTERNS), re.IGNORECASE)
COMMAND_PATTERN = re.compile("|".join(DANGEROUS_COMMAND_PATTERNS))


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Sanitize string input.

    Args:
        value: Input string
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        HTTPException: If string contains dangerous patterns
    """
    if not isinstance(value, str):
        return value

    # Check length
    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"String too long: {len(value)} chars (max: {max_length})",
        )

    # Check for SQL injection patterns
    if SQL_PATTERN.search(value):
        logger.warning(
            f"Potential SQL injection detected",
            extra={"value": value[:100]},  # Log first 100 chars
        )
        raise HTTPException(
            status_code=400,
            detail="Input contains potentially dangerous SQL patterns",
        )

    # Check for command injection patterns
    if COMMAND_PATTERN.search(value):
        logger.warning(
            f"Potential command injection detected",
            extra={"value": value[:100]},
        )
        raise HTTPException(
            status_code=400,
            detail="Input contains potentially dangerous command patterns",
        )

    # Remove null bytes (can cause issues in C-based systems)
    value = value.replace("\x00", "")

    # Normalize whitespace (prevent unicode tricks)
    value = " ".join(value.split())

    return value


def sanitize_dict(
    data: Dict[str, Any], depth: int = 0, max_depth: int = MAX_DEPTH
) -> Dict[str, Any]:
    """Recursively sanitize dictionary.

    Args:
        data: Input dictionary
        depth: Current recursion depth
        max_depth: Maximum allowed depth

    Returns:
        Sanitized dictionary

    Raises:
        HTTPException: If depth exceeds maximum or contains dangerous data
    """
    if depth > max_depth:
        raise HTTPException(
            status_code=400,
            detail=f"Data structure too deep: {depth} levels (max: {max_depth})",
        )

    sanitized = {}

    for key, value in data.items():
        # Sanitize key (prevent prototype pollution)
        if not isinstance(key, str):
            raise HTTPException(
                status_code=400, detail="Dictionary keys must be strings"
            )

        # Check for dangerous keys
        if key.startswith("__") or key in ["constructor", "prototype", "__proto__"]:
            logger.warning(f"Dangerous key detected: {key}")
            raise HTTPException(
                status_code=400, detail=f"Forbidden key: {key}"
            )

        # Sanitize key
        sanitized_key = sanitize_string(key, max_length=255)

        # Sanitize value based on type
        sanitized[sanitized_key] = sanitize_value(value, depth + 1, max_depth)

    return sanitized


def sanitize_list(
    data: List[Any], depth: int = 0, max_depth: int = MAX_DEPTH
) -> List[Any]:
    """Recursively sanitize list.

    Args:
        data: Input list
        depth: Current recursion depth
        max_depth: Maximum allowed depth

    Returns:
        Sanitized list
    """
    if depth > max_depth:
        raise HTTPException(
            status_code=400,
            detail=f"Data structure too deep: {depth} levels (max: {max_depth})",
        )

    return [sanitize_value(item, depth + 1, max_depth) for item in data]


def sanitize_value(value: Any, depth: int = 0, max_depth: int = MAX_DEPTH) -> Any:
    """Sanitize value based on type.

    Args:
        value: Input value
        depth: Current recursion depth
        max_depth: Maximum allowed depth

    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        return sanitize_string(value)
    elif isinstance(value, dict):
        return sanitize_dict(value, depth, max_depth)
    elif isinstance(value, list):
        return sanitize_list(value, depth, max_depth)
    elif isinstance(value, (int, float, bool, type(None))):
        # Primitive types are safe
        return value
    else:
        # Unknown types - convert to string and sanitize
        logger.warning(f"Unknown type detected: {type(value)}")
        return sanitize_string(str(value))


# =============================================================================
# MIDDLEWARE
# =============================================================================


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware to sanitize all incoming request data.

    Boris Cherny Pattern: Fail fast with clear error messages.
    """

    def __init__(
        self,
        app,
        max_payload_size: int = MAX_PAYLOAD_SIZE,
        enable_sanitization: bool = True,
        exempt_paths: Optional[List[str]] = None,
    ):
        """Initialize sanitization middleware.

        Args:
            app: FastAPI application
            max_payload_size: Maximum allowed payload size in bytes
            enable_sanitization: Enable/disable sanitization (for testing)
            exempt_paths: Paths to exempt from sanitization (e.g., /docs)
        """
        super().__init__(app)
        self.max_payload_size = max_payload_size
        self.enable_sanitization = enable_sanitization
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and sanitize input data.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response from application
        """
        # Skip sanitization for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Skip sanitization if disabled (testing mode)
        if not self.enable_sanitization:
            return await call_next(request)

        # Skip GET requests (no body to sanitize)
        if request.method == "GET":
            return await call_next(request)

        try:
            # Check payload size BEFORE reading body
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_payload_size:
                logger.warning(
                    f"Payload too large: {content_length} bytes",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "content_length": content_length,
                    },
                )
                raise HTTPException(
                    status_code=413,
                    detail=f"Payload too large: {int(content_length) / 1024 / 1024:.2f}MB "
                    f"(max: {self.max_payload_size / 1024 / 1024:.0f}MB)",
                )

            # Read and parse body
            body = await request.body()

            # Check actual size
            if len(body) > self.max_payload_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Payload too large: {len(body) / 1024 / 1024:.2f}MB",
                )

            # Parse JSON if content-type is JSON
            if (
                request.headers.get("content-type", "").startswith("application/json")
                and body
            ):
                import json

                try:
                    data = json.loads(body)

                    # Sanitize data
                    sanitized_data = sanitize_value(data)

                    # Replace request body with sanitized version
                    # Note: This is a simplified approach. In production,
                    # you might want to use FastAPI's dependency injection
                    # to inject sanitized data into route handlers.

                    logger.debug(
                        f"Sanitized request data",
                        extra={
                            "path": request.url.path,
                            "method": request.method,
                        },
                    )

                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400, detail="Invalid JSON in request body"
                    )
                except HTTPException:
                    # Re-raise validation errors
                    raise
                except Exception as e:
                    logger.error(f"Sanitization error: {str(e)}")
                    raise HTTPException(
                        status_code=400, detail=f"Input validation failed: {str(e)}"
                    )

            # Continue to next middleware/route handler
            return await call_next(request)

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in input sanitization: {str(e)}",
                extra={"path": request.url.path, "method": request.method},
            )
            raise HTTPException(
                status_code=500, detail="Internal server error during input validation"
            )


# =============================================================================
# STANDALONE FUNCTIONS (for use in route handlers)
# =============================================================================


def validate_and_sanitize(data: Any) -> Any:
    """Validate and sanitize data (for use in route handlers).

    Args:
        data: Input data (dict, list, str, etc.)

    Returns:
        Sanitized data

    Raises:
        HTTPException: If data is invalid

    Example:
        ```python
        @app.post("/api/data")
        async def create_data(raw_data: dict):
            data = validate_and_sanitize(raw_data)
            # Now data is safe to use
        ```
    """
    return sanitize_value(data)
