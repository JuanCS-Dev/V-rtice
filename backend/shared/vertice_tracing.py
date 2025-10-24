"""
Vértice Distributed Tracing - OpenTelemetry Integration

Provides unified tracing across all Vértice services with Jaeger backend.

Author: Vértice Team
Glory to YHWH! 🙏
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.trace import Status, StatusCode, Span

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def init_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    jaeger_endpoint: str = None,
    enable_console_export: bool = False
) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing for a service.

    Args:
        service_name: Name of the service (e.g., "vertice-gateway")
        service_version: Version of the service
        jaeger_endpoint: Jaeger OTLP endpoint (default: from env or localhost:4317)
        enable_console_export: Export spans to console for debugging

    Returns:
        Configured Tracer instance
    """
    global _tracer

    # Get Jaeger endpoint from env or use default
    if jaeger_endpoint is None:
        jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://vertice-jaeger:4317")

    # Create resource with service information
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "production"),
        "service.namespace": "vertice"
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter (Jaeger)
    otlp_exporter = OTLPSpanExporter(
        endpoint=jaeger_endpoint,
        insecure=True  # Use TLS in production
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Optional: Console exporter for debugging
    if enable_console_export:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set as global provider
    trace.set_tracer_provider(provider)

    # Get tracer
    _tracer = trace.get_tracer(service_name, service_version)

    logger.info(f"✅ Tracing initialized for {service_name} → {jaeger_endpoint}")

    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    if _tracer is None:
        raise RuntimeError("Tracing not initialized. Call init_tracing() first.")
    return _tracer


def instrument_fastapi(app):
    """
    Instrument FastAPI app with automatic tracing.

    Args:
        app: FastAPI application instance
    """
    FastAPIInstrumentor.instrument_app(app)
    logger.info("✅ FastAPI instrumented for tracing")


def instrument_httpx():
    """Instrument HTTPX client for automatic tracing of HTTP requests."""
    HTTPXClientInstrumentor().instrument()
    logger.info("✅ HTTPX instrumented for tracing")


def instrument_redis():
    """Instrument Redis client for automatic tracing."""
    try:
        RedisInstrumentor().instrument()
        logger.info("✅ Redis instrumented for tracing")
    except Exception as e:
        logger.warning(f"Redis instrumentation failed: {e}")


def traced(span_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace a function.

    Usage:
        @traced("my_operation")
        def my_function(arg1, arg2):
            ...

    Args:
        span_name: Custom span name (default: function name)
        attributes: Additional span attributes
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            name = span_name or func.__name__

            with tracer.start_as_current_span(name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            name = span_name or func.__name__

            with tracer.start_as_current_span(name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        # Return appropriate wrapper based on function type
        if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attribute(key: str, value: Any):
    """
    Add attribute to current active span.

    Args:
        key: Attribute key
        value: Attribute value
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Add event to current active span.

    Args:
        name: Event name
        attributes: Event attributes
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes=attributes or {})


def set_span_error(exception: Exception):
    """
    Mark current span as error and record exception.

    Args:
        exception: Exception that occurred
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_status(Status(StatusCode.ERROR, str(exception)))
        span.record_exception(exception)


# Context manager for manual span creation
class TracedOperation:
    """
    Context manager for creating traced operations.

    Usage:
        with TracedOperation("database_query", {"db.table": "users"}):
            # Your code here
            pass
    """

    def __init__(self, span_name: str, attributes: Optional[Dict[str, Any]] = None):
        self.span_name = span_name
        self.attributes = attributes or {}
        self.span: Optional[Span] = None

    def __enter__(self):
        tracer = get_tracer()
        self.span = tracer.start_span(self.span_name)

        # Add attributes
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)

        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(Status(StatusCode.OK))

            self.span.end()


# Async context manager
class AsyncTracedOperation:
    """
    Async context manager for creating traced operations.

    Usage:
        async with AsyncTracedOperation("async_operation"):
            await some_async_function()
    """

    def __init__(self, span_name: str, attributes: Optional[Dict[str, Any]] = None):
        self.span_name = span_name
        self.attributes = attributes or {}
        self.span: Optional[Span] = None

    async def __aenter__(self):
        tracer = get_tracer()
        self.span = tracer.start_span(self.span_name)

        # Add attributes
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)

        return self.span

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(Status(StatusCode.OK))

            self.span.end()
