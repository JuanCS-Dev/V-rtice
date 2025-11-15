"""
Sentry Error Tracking Integration

DOUTRINA VÉRTICE - GAP #8 (P2)
Production error tracking and monitoring with Sentry

Following Boris Cherny's principle: "Errors should be observable"
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from fastapi import Request
from typing import Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

class SentryConfig:
    """Sentry configuration."""

    # Environment variables
    DSN = os.getenv("SENTRY_DSN")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    RELEASE = os.getenv("RELEASE_VERSION", "unknown")

    # Sampling rates
    TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
    PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "1.0"))

    # Feature flags
    ENABLE_TRACING = os.getenv("SENTRY_ENABLE_TRACING", "true").lower() == "true"
    ENABLE_PROFILING = os.getenv("SENTRY_ENABLE_PROFILING", "true").lower() == "true"

    # PII (Personally Identifiable Information)
    SEND_DEFAULT_PII = os.getenv("SENTRY_SEND_PII", "false").lower() == "true"


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_sentry():
    """
    Initialize Sentry SDK with FastAPI integration.

    Call this at application startup:
        from middleware.sentry_integration import init_sentry
        init_sentry()

    Environment Variables:
        SENTRY_DSN: Your Sentry DSN (required)
        ENVIRONMENT: Environment name (development, staging, production)
        RELEASE_VERSION: Release version (e.g., git commit hash)
        SENTRY_TRACES_SAMPLE_RATE: Fraction of transactions to trace (0.0-1.0)
        SENTRY_PROFILES_SAMPLE_RATE: Fraction of profiles to sample (0.0-1.0)
        SENTRY_SEND_PII: Whether to send PII (emails, IPs, etc.)
    """
    if not SentryConfig.DSN:
        print("[Sentry] DSN not configured. Error tracking disabled.")
        return

    try:
        sentry_sdk.init(
            dsn=SentryConfig.DSN,
            environment=SentryConfig.ENVIRONMENT,
            release=SentryConfig.RELEASE,

            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",  # Group by endpoint, not URL
                ),
                StarletteIntegration(
                    transaction_style="endpoint",
                ),
                RedisIntegration(),
                HttpxIntegration(),
            ],

            # Performance monitoring
            traces_sample_rate=SentryConfig.TRACES_SAMPLE_RATE if SentryConfig.ENABLE_TRACING else 0.0,
            profiles_sample_rate=SentryConfig.PROFILES_SAMPLE_RATE if SentryConfig.ENABLE_PROFILING else 0.0,

            # Privacy
            send_default_pii=SentryConfig.SEND_DEFAULT_PII,

            # Filtering
            before_send=before_send_filter,
            before_send_transaction=before_send_transaction_filter,

            # SDK options
            attach_stacktrace=True,
            max_breadcrumbs=50,
        )

        print(f"[Sentry] Initialized for environment: {SentryConfig.ENVIRONMENT}")
        print(f"[Sentry] Release: {SentryConfig.RELEASE}")
        print(f"[Sentry] Tracing enabled: {SentryConfig.ENABLE_TRACING}")

    except Exception as e:
        print(f"[Sentry] Failed to initialize: {e}")


# ============================================================================
# FILTERING & PRIVACY
# ============================================================================

def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry.

    Use this to:
    - Remove sensitive data
    - Filter out noisy errors
    - Add custom context
    """
    # Ignore health check errors
    if event.get("transaction") == "/api/v1/health":
        return None

    # Ignore specific error types
    if "exception" in event:
        exceptions = event.get("exception", {}).get("values", [])
        for exc in exceptions:
            # Ignore 404 errors
            if exc.get("type") == "HTTPException" and "404" in str(exc.get("value", "")):
                return None

    # Remove sensitive data from request
    if "request" in event:
        # Remove cookies
        if "cookies" in event["request"]:
            event["request"]["cookies"] = "[Filtered]"

        # Remove auth headers
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            if "Authorization" in headers:
                headers["Authorization"] = "[Filtered]"
            if "X-API-Key" in headers:
                headers["X-API-Key"] = "[Filtered]"

    return event


def before_send_transaction_filter(event, hint):
    """
    Filter performance transactions before sending.

    Use this to reduce noise from low-value transactions.
    """
    # Ignore health checks
    if event.get("transaction") == "/api/v1/health":
        return None

    # Ignore metrics endpoint (too frequent)
    if event.get("transaction") == "/metrics":
        return None

    return event


# ============================================================================
# CONTEXT MANAGEMENT
# ============================================================================

def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """
    Set user context for error reports.

    Call this after authentication:
        set_user_context(user.id, user.email, user.username)

    Args:
        user_id: Unique user identifier
        email: User email (optional, PII)
        username: Username (optional)
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email if SentryConfig.SEND_DEFAULT_PII else None,
        "username": username,
    })


def set_request_context(request: Request):
    """
    Set request context for error reports.

    Call this in middleware or dependency:
        set_request_context(request)

    Args:
        request: FastAPI Request object
    """
    sentry_sdk.set_context("request_details", {
        "url": str(request.url),
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "request_id": request.headers.get("X-Request-ID"),
    })


def add_breadcrumb(message: str, category: str = "custom", level: str = "info", data: Optional[dict] = None):
    """
    Add breadcrumb for debugging context.

    Breadcrumbs show the trail of events leading to an error.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "query", "auth", "cache")
        level: Severity (debug, info, warning, error, fatal)
        data: Additional data

    Example:
        add_breadcrumb("Database query executed", "query", "info", {
            "query": "SELECT * FROM scans",
            "duration_ms": 45
        })
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


# ============================================================================
# ERROR CAPTURING
# ============================================================================

def capture_exception(error: Exception, level: str = "error", extras: Optional[dict] = None):
    """
    Manually capture an exception.

    Use this for caught exceptions that you want to track:
        try:
            risky_operation()
        except Exception as e:
            capture_exception(e, level="warning", extras={"context": "..."})

    Args:
        error: Exception to capture
        level: Severity (debug, info, warning, error, fatal)
        extras: Additional context
    """
    if extras:
        sentry_sdk.set_context("extras", extras)

    sentry_sdk.capture_exception(error, level=level)


def capture_message(message: str, level: str = "info", extras: Optional[dict] = None):
    """
    Capture a message (not an exception).

    Use this for important events without exceptions:
        capture_message("Rate limit exceeded", level="warning", extras={
            "user_id": user.id,
            "endpoint": "/api/v1/scan"
        })

    Args:
        message: Message to capture
        level: Severity
        extras: Additional context
    """
    if extras:
        sentry_sdk.set_context("extras", extras)

    sentry_sdk.capture_message(message, level=level)


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

def start_transaction(name: str, op: str = "function"):
    """
    Start a performance transaction.

    Use this to measure performance of specific operations:
        with start_transaction("expensive_operation", "task"):
            expensive_operation()

    Args:
        name: Transaction name
        op: Operation type (http, task, db.query, etc.)

    Returns:
        Transaction context manager
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def start_span(operation: str, description: Optional[str] = None):
    """
    Start a performance span within a transaction.

    Use this to measure sub-operations:
        with start_span("db.query", "Fetch scans"):
            scans = db.query(Scan).all()

    Args:
        operation: Span operation (e.g., "db.query", "http.client")
        description: Span description

    Returns:
        Span context manager
    """
    return sentry_sdk.start_span(op=operation, description=description)


# ============================================================================
# MIDDLEWARE
# ============================================================================

class SentryContextMiddleware:
    """
    Middleware to automatically set request context for Sentry.

    Usage:
        from middleware.sentry_integration import SentryContextMiddleware
        app.add_middleware(SentryContextMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            set_request_context(request)

        await self.app(scope, receive, send)


# ============================================================================
# UTILITIES
# ============================================================================

def is_enabled() -> bool:
    """Check if Sentry is enabled."""
    return SentryConfig.DSN is not None


def flush(timeout: int = 2):
    """
    Flush pending events to Sentry.

    Call this before shutdown:
        sentry_integration.flush(timeout=5)

    Args:
        timeout: Max time to wait (seconds)
    """
    if is_enabled():
        sentry_sdk.flush(timeout=timeout)
        print("[Sentry] Flushed pending events")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
# In main.py:

from middleware.sentry_integration import init_sentry, SentryContextMiddleware

# Initialize Sentry
init_sentry()

# Add middleware
app.add_middleware(SentryContextMiddleware)

# In endpoints:

from middleware.sentry_integration import (
    set_user_context,
    add_breadcrumb,
    capture_exception,
    start_span,
)

@app.post("/api/v1/scan/start")
async def start_scan(scan_data: ScanRequest, user = Depends(get_current_user)):
    # Set user context
    set_user_context(user.id, user.email, user.username)

    # Add breadcrumb
    add_breadcrumb("Starting scan", "scan", "info", {
        "target": scan_data.target
    })

    try:
        # Measure performance
        with start_span("scanner.nmap", "Run Nmap scan"):
            result = await run_nmap_scan(scan_data.target)

        return result

    except Exception as e:
        # Capture exception with context
        capture_exception(e, level="error", extras={
            "target": scan_data.target,
            "user_id": user.id,
        })
        raise

# At shutdown:

from middleware.sentry_integration import flush

@app.on_event("shutdown")
async def shutdown():
    flush(timeout=5)
"""
