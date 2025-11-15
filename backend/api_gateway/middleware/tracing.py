"""Request Tracing Middleware for Distributed Correlation.

This module implements X-Request-ID based distributed tracing for the Vértice platform.
All requests are tracked with a unique correlation ID that propagates across services,
enabling comprehensive debugging and monitoring in distributed systems.

Key Features:
- Automatic request ID generation (UUID v4)
- Request ID propagation from client headers
- Structlog context binding for correlated logging
- Response header injection for client tracking
- Exception tracking with request IDs

Following Boris Cherny's principle: "If you can't trace it, you can't debug it"

Author: Vértice Development Team
DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard (Zero Mocks, Real Code Only)
"""

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Get structured logger
logger = structlog.get_logger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed request tracing via X-Request-ID headers.

    This middleware implements comprehensive request tracking by:
    1. Extracting or generating unique request IDs (UUID v4)
    2. Storing request ID in request.state for handler access
    3. Binding request ID to structlog context for correlated logs
    4. Adding X-Request-ID header to all responses
    5. Logging request lifecycle events (start, complete, error)

    The X-Request-ID header follows industry standards:
    - Amazon API Gateway uses X-Request-ID
    - Nginx uses $request_id
    - HAProxy uses unique-id
    - HTTP/2 uses header propagation

    Attributes:
        None (stateless middleware)

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(RequestTracingMiddleware)
        >>> # All requests now have X-Request-ID tracking

    Performance:
        - UUID generation: ~1μs
        - Context binding: ~5μs
        - Total overhead: <10μs per request

    Thread Safety:
        Uses contextvars for thread-safe context isolation.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with distributed tracing.

        Args:
            request: The incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with X-Request-ID header added

        Side Effects:
            - Binds request_id to structlog context
            - Logs request_started and request_completed events
            - Logs request_failed on exceptions

        Example:
            # Client sends request with ID
            GET /api/v1/health
            X-Request-ID: 550e8400-e29b-41d4-a716-446655440000

            # Server response includes same ID
            HTTP/1.1 200 OK
            X-Request-ID: 550e8400-e29b-41d4-a716-446655440000

            # Logs show correlated events
            {
                "event": "request_started",
                "request_id": "550e8400-...",
                "method": "GET",
                "path": "/api/v1/health"
            }
        """
        # Step 1: Extract or generate request ID
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            # Generate UUID v4 (random, cryptographically strong)
            request_id = str(uuid.uuid4())

        # Step 2: Store in request state for handler access
        # Handlers can access via: request.state.request_id
        request.state.request_id = request_id

        # Step 3: Bind to structlog context
        # This ensures ALL logs in this request have request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )

        # Step 4: Log request start
        start_time = time.perf_counter()

        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent", "unknown"),
        )

        # Step 5: Process request with error handling
        try:
            response = await call_next(request)

            # Calculate request duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log successful completion
            logger.info(
                "request_completed",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

        except Exception as exc:
            # Calculate error duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log error with full context
            logger.error(
                "request_failed",
                request_id=request_id,
                error_type=type(exc).__name__,
                error_message=str(exc),
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )

            # Re-raise to let exception handlers process it
            raise

        # Step 6: Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


# ============================================================================
# Utility Functions
# ============================================================================


def get_request_id(request: Request) -> str:
    """Extract request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID string (UUID format)

    Example:
        >>> @app.get("/endpoint")
        >>> async def endpoint(request: Request):
        >>>     request_id = get_request_id(request)
        >>>     logger.info("processing", request_id=request_id)
    """
    return getattr(request.state, "request_id", "unknown")
