"""
OpenTelemetry distributed tracing for HITL API.

Provides:
- Tracer initialization
- Span management
- Context propagation
- Trace decorators
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def setup_tracing(
    service_name: str = "hitl-api",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    enable_console_export: bool = False,
) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing with Jaeger exporter.

    Args:
        service_name: Name of the service for tracing
        jaeger_host: Jaeger agent host
        jaeger_port: Jaeger agent port
        enable_console_export: Also export to console (for debugging)

    Returns:
        Configured tracer instance

    Example:
        >>> from hitl.monitoring import setup_tracing
        >>> tracer = setup_tracing(
        ...     service_name="hitl-api",
        ...     jaeger_host="jaeger",
        ...     jaeger_port=6831
        ... )
    """
    global _tracer

    # Create resource with service name
    resource = Resource.create({SERVICE_NAME: service_name})

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure Jaeger exporter
    try:
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        logger.info(f"✅ Jaeger tracing initialized: {jaeger_host}:{jaeger_port}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Jaeger exporter: {e}")

    # Optionally add console exporter (for debugging)
    if enable_console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer
    _tracer = trace.get_tracer(__name__)

    # Auto-instrument common libraries
    _auto_instrument()

    return _tracer


def _auto_instrument():
    """Auto-instrument common libraries."""
    try:
        # FastAPI auto-instrumentation (if available)
        FastAPIInstrumentor().instrument()
        logger.info("✅ FastAPI auto-instrumented")
    except Exception as e:
        logger.debug(f"FastAPI auto-instrumentation failed: {e}")

    try:
        # HTTP client auto-instrumentation
        HTTPXClientInstrumentor().instrument()
        logger.info("✅ HTTPX client auto-instrumented")
    except Exception as e:
        logger.debug(f"HTTPX auto-instrumentation failed: {e}")

    try:
        # SQLAlchemy auto-instrumentation
        SQLAlchemyInstrumentor().instrument()
        logger.info("✅ SQLAlchemy auto-instrumented")
    except Exception as e:
        logger.debug(f"SQLAlchemy auto-instrumentation failed: {e}")

    try:
        # Redis auto-instrumentation
        RedisInstrumentor().instrument()
        logger.info("✅ Redis auto-instrumented")
    except Exception as e:
        logger.debug(f"Redis auto-instrumentation failed: {e}")


def get_tracer() -> trace.Tracer:
    """
    Get global tracer instance.

    Returns:
        Tracer instance (or no-op tracer if not initialized)
    """
    global _tracer
    if _tracer is None:
        logger.warning("⚠️ Tracer not initialized, using no-op tracer")
        return trace.get_tracer(__name__)
    return _tracer


@contextmanager
def trace_operation(
    name: str,
    kind: str = "internal",
    attributes: Optional[dict[str, Any]] = None,
):
    """
    Context manager for tracing an operation.

    Args:
        name: Name of the operation
        kind: Span kind (internal, server, client, producer, consumer)
        attributes: Additional span attributes

    Example:
        >>> with trace_operation("process_review", attributes={"review_id": 123}):
        ...     # Do work
        ...     pass
    """
    tracer = get_tracer()

    # Map kind string to SpanKind enum
    span_kind_map = {
        "internal": trace.SpanKind.INTERNAL,
        "server": trace.SpanKind.SERVER,
        "client": trace.SpanKind.CLIENT,
        "producer": trace.SpanKind.PRODUCER,
        "consumer": trace.SpanKind.CONSUMER,
    }
    span_kind = span_kind_map.get(kind, trace.SpanKind.INTERNAL)

    with tracer.start_as_current_span(name, kind=span_kind) as span:
        # Add custom attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        try:
            yield span
        except Exception as exc:
            # Record exception in span
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(exc).__name__)
            span.set_attribute("error.message", str(exc))
            span.record_exception(exc)
            raise


def trace_function(name: Optional[str] = None, kind: str = "internal"):
    """
    Decorator for tracing a function.

    Args:
        name: Name of the span (defaults to function name)
        kind: Span kind (internal, server, client, producer, consumer)

    Example:
        >>> @trace_function(name="validate_review")
        ... def validate_review(review_id: int):
        ...     # Validation logic
        ...     pass
    """

    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_operation(span_name, kind=kind):
                return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_operation(span_name, kind=kind):
                return await func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attribute(key: str, value: Any):
    """
    Add attribute to current span.

    Args:
        key: Attribute key
        value: Attribute value

    Example:
        >>> add_span_attribute("user_id", 123)
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[dict[str, Any]] = None):
    """
    Add event to current span.

    Args:
        name: Event name
        attributes: Event attributes

    Example:
        >>> add_span_event("review_validated", {"result": "approved"})
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes=attributes or {})


def record_exception_in_span(exc: Exception):
    """
    Record exception in current span.

    Args:
        exc: Exception to record

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     record_exception_in_span(e)
        ...     raise
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("error", True)
        span.set_attribute("error.type", type(exc).__name__)
        span.set_attribute("error.message", str(exc))
        span.record_exception(exc)
