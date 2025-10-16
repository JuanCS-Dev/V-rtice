"""FastAPI middleware components."""

import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from vertice_core import VerticeException


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and metadata."""

    def __init__(self, app: Any, logger: structlog.stdlib.BoundLogger) -> None:
        super().__init__(app)
        self.logger = logger

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:  # pragma: no cover
        """Process request and log details."""
        start_time = time.time()

        request_id = request.headers.get("X-Request-ID", "")
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            self.logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000

            self.logger.error(
                "request_failed",
                error=str(exc),
                error_type=exc.__class__.__name__,
                duration_ms=round(duration_ms, 2),
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Convert exceptions to proper JSON responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle exceptions and convert to JSON."""
        try:
            return await call_next(request)
        except VerticeException as exc:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict(),
            )
        except Exception:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "status_code": 500,
                    "details": {},
                },
            )
