"""
Monitoring middleware for automatic instrumentation.

Provides FastAPI middleware for:
- Prometheus metrics collection
- OpenTelemetry distributed tracing
- Request/response logging
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Callable
import logging

from .metrics import metrics

logger = logging.getLogger(__name__)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic Prometheus metrics collection.

    Automatically tracks:
    - Request count
    - Request duration
    - Request/response sizes
    - SLO compliance
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and record metrics."""
        # Start timer
        start_time = time.time()

        # Get request size
        request_size = None
        if "content-length" in request.headers:
            try:
                request_size = int(request.headers["content-length"])
            except (ValueError, TypeError):
                pass

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            # Record error
            status_code = 500
            metrics.record_exception(type(exc).__name__)
            logger.exception(f"Unhandled exception in request: {exc}")
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Get response size
        response_size = None
        if "content-length" in response.headers:
            try:
                response_size = int(response.headers["content-length"])
            except (ValueError, TypeError):
                pass

        # Normalize endpoint (remove IDs)
        endpoint = self._normalize_endpoint(request.url.path)

        # Record metrics
        metrics.record_request(
            method=request.method,
            endpoint=endpoint,
            status=status_code,
            duration=duration,
            request_size=request_size,
            response_size=response_size,
        )

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path by replacing IDs with placeholders.

        Examples:
            /hitl/reviews/123 -> /hitl/reviews/{id}
            /hitl/reviews/abc-def-123/decision -> /hitl/reviews/{id}/decision
        """
        parts = path.split("/")
        normalized = []

        for i, part in enumerate(parts):
            # Check if part looks like an ID (UUID, integer, etc.)
            if self._is_id_like(part):
                normalized.append("{id}")
            else:
                normalized.append(part)

        return "/".join(normalized)

    def _is_id_like(self, part: str) -> bool:
        """Check if path part looks like an ID."""
        if not part:
            return False

        # Integer ID
        if part.isdigit():
            return True

        # UUID pattern (simple check)
        if "-" in part and len(part) > 20:
            return True

        # Hexadecimal ID
        if len(part) > 10 and all(c in "0123456789abcdefABCDEF" for c in part):
            return True

        return False


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for OpenTelemetry distributed tracing.

    Automatically:
    - Creates spans for each request
    - Propagates trace context
    - Adds request/response attributes
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.tracer = None  # Will be set by setup_tracing()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with distributed tracing."""
        if not self.tracer:
            # Tracing not initialized, pass through
            return await call_next(request)

        # Extract trace context from headers
        # (OpenTelemetry auto-instrumentation handles this)

        # Create span for request
        with self.tracer.start_as_current_span(
            name=f"{request.method} {request.url.path}",
            kind="server",
        ) as span:
            # Add request attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.netloc)
            span.set_attribute("http.target", request.url.path)

            if "user-agent" in request.headers:
                span.set_attribute("http.user_agent", request.headers["user-agent"])

            # Process request
            try:
                response = await call_next(request)

                # Add response attributes
                span.set_attribute("http.status_code", response.status_code)

                # Mark span as error if 5xx
                if response.status_code >= 500:
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", f"HTTP_{response.status_code}")

                return response

            except Exception as exc:
                # Record exception in span
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(exc).__name__)
                span.set_attribute("error.message", str(exc))
                span.record_exception(exc)
                raise


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging.

    Logs:
    - Request details (method, path, headers)
    - Response details (status, duration)
    - Errors and exceptions
    """

    def __init__(self, app: ASGIApp, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        start_time = time.time()

        # Log request
        logger.info(
            f"→ {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "client": request.client.host if request.client else None,
            },
        )

        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            log_level = logging.INFO
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING

            logger.log(
                log_level,
                f"← {response.status_code} {request.method} {request.url.path} ({duration:.3f}s)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration": duration,
                },
            )

            return response

        except Exception as exc:
            duration = time.time() - start_time
            logger.exception(
                f"✗ {request.method} {request.url.path} ({duration:.3f}s) - {type(exc).__name__}: {exc}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "exception": type(exc).__name__,
                },
            )
            raise
