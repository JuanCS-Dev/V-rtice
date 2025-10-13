"""
Structured logging configuration for HITL API.

Provides JSON-formatted logs in production and human-readable logs in development.

Usage:
    from hitl.monitoring import configure_logging, logger

    # Configure on startup
    configure_logging(log_level="info")

    # Use logger
    logger.info("request_received", method="GET", path="/hitl/reviews")
    logger.error("database_error", error=str(e), query="SELECT...")
"""

import structlog
import logging
import sys
from typing import Any


def configure_logging(log_level: str = "info", use_json: bool = False) -> None:
    """
    Configure structured logging.

    Args:
        log_level: Logging level (debug, info, warning, error, critical)
        use_json: If True, output JSON format. If False, use human-readable format.
                  Auto-detects: JSON if not a TTY (production), human-readable if TTY (dev)

    Effects:
        - Configures structlog with appropriate processors
        - Sets up Python standard logging
        - Adds context processors for request IDs, timestamps, etc.
    """

    # Auto-detect format based on TTY
    if use_json is None:
        use_json = not sys.stderr.isatty()

    # Configure Python's standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Disable noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Choose renderer based on format
    if use_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=sys.stderr.isatty(),
            pad_event=30,
        )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add context variables
            structlog.contextvars.merge_contextvars,
            # Add log level
            structlog.processors.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Add stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.processors.format_exc_info,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Render to JSON or Console
            renderer,
        ],
        # Context class
        context_class=dict,
        # Logger factory
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache logger on first use
        cache_logger_on_first_use=True,
    )


# Create logger instance
logger = structlog.get_logger("hitl_api")


# --- Context Managers for Adding Context ---

class log_context:
    """
    Context manager to add context to all logs within a block.

    Usage:
        with log_context(request_id="abc123", user_id="user456"):
            logger.info("processing_request")
            # All logs will include request_id and user_id
    """

    def __init__(self, **kwargs: Any):
        self.context = kwargs
        self.token = None

    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())


# --- Logging Helpers ---

def log_request(method: str, path: str, status: int, duration: float, **kwargs: Any) -> None:
    """
    Log an HTTP request.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status: HTTP status code
        duration: Request duration in seconds
        **kwargs: Additional context
    """
    logger.info(
        "http_request",
        method=method,
        path=path,
        status=status,
        duration_seconds=duration,
        **kwargs,
    )


def log_decision(apv_code: str, decision: str, reviewer: str, **kwargs: Any) -> None:
    """
    Log a HITL decision.

    Args:
        apv_code: APV code (e.g., APV-2025-001)
        decision: Decision type (approve, reject, modify, escalate)
        reviewer: Reviewer name
        **kwargs: Additional context
    """
    logger.info(
        "hitl_decision",
        apv_code=apv_code,
        decision=decision,
        reviewer=reviewer,
        **kwargs,
    )


def log_websocket_event(event: str, client_id: str = None, **kwargs: Any) -> None:
    """
    Log a WebSocket event.

    Args:
        event: Event name (connect, disconnect, message, broadcast)
        client_id: WebSocket client ID
        **kwargs: Additional context
    """
    logger.info(
        "websocket_event",
        event=event,
        client_id=client_id,
        **kwargs,
    )


def log_error(error_type: str, error_message: str, **kwargs: Any) -> None:
    """
    Log an error.

    Args:
        error_type: Error type/category
        error_message: Error message
        **kwargs: Additional context (exc_info, stack trace, etc.)
    """
    logger.error(
        "error_occurred",
        error_type=error_type,
        error_message=error_message,
        **kwargs,
    )


# --- Example Usage ---

if __name__ == "__main__":
    """Test structured logging configuration."""

    print("Testing Structured Logging")
    print("=" * 60)

    # Configure logging
    configure_logging(log_level="debug", use_json=False)

    # Test basic logging
    logger.info("application_started", version="1.0.0", environment="development")
    logger.debug("debug_message", details="This is a debug message")

    # Test with context
    with log_context(request_id="req-123", user_id="user-456"):
        logger.info("processing_request", action="get_reviews")
        logger.warning("slow_query", query_time=1.5, query="SELECT * FROM apv_reviews")

    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("exception_occurred", exc_info=True)

    # Test helper functions
    log_request("GET", "/hitl/reviews", 200, 0.123, count=42)
    log_decision("APV-2025-001", "approve", "Alice Johnson", confidence=0.95)
    log_websocket_event("connect", client_id="abc-123", channels=["apvs", "decisions"])

    print()
    print("=" * 60)
    print("Structured logging test complete!")
