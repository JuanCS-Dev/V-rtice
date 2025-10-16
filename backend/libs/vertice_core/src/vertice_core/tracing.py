"""OpenTelemetry distributed tracing setup."""

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(
    service_name: str,
    service_version: str,
    endpoint: str = "http://jaeger:4318/v1/traces",
    enabled: bool = True,
) -> trace.Tracer:
    """Setup OpenTelemetry tracing for the service."""
    if not enabled:
        return trace.get_tracer(service_name)

    resource = Resource.create({  # pragma: no cover
        "service.name": service_name,
        "service.version": service_version,
    })

    provider = TracerProvider(resource=resource)  # pragma: no cover
    processor = BatchSpanProcessor(  # pragma: no cover
        OTLPSpanExporter(endpoint=endpoint)
    )
    provider.add_span_processor(processor)  # pragma: no cover
    trace.set_tracer_provider(provider)  # pragma: no cover

    return trace.get_tracer(service_name, service_version)  # pragma: no cover


def instrument_fastapi(app: Any) -> None:  # pragma: no cover
    """Instrument a FastAPI application with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass
