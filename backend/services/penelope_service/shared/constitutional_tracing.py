"""Constitutional Tracing for Vértice Constitution v3.0 Compliance.

This module implements OpenTelemetry distributed tracing with custom
span attributes for tracking biblical principles and constitutional compliance.

Biblical Foundation:
- Aletheia (Truth): Transparent operation tracking
- Sophia (Wisdom): Decision tracing for accountability
- Stewardship: Responsible resource usage tracking
"""

import os
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class ConstitutionalTracer:
    """OpenTelemetry tracer with constitutional compliance tracking."""

    def __init__(
        self,
        service_name: str,
        version: str = "1.0.0",
        jaeger_endpoint: Optional[str] = None,
        otlp_endpoint: Optional[str] = None,
    ):
        """
        Initialize constitutional tracer.

        Args:
            service_name: Name of the service (e.g., "penelope", "maba", "mvp")
            version: Service version
            jaeger_endpoint: Jaeger collector endpoint (optional)
            otlp_endpoint: OTLP collector endpoint (optional)
        """
        self.service_name = service_name
        self.version = version

        # Create resource with service metadata
        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                "service.version": version,
                "constitution.version": "3.0",
                "framework": "DETER-AGENT",
                "governance": "7_biblical_articles",
            }
        )

        # Set up tracer provider
        provider = TracerProvider(resource=resource)

        # Add Jaeger exporter if configured
        if jaeger_endpoint or os.getenv("JAEGER_ENDPOINT"):
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_endpoint
                or os.getenv("JAEGER_AGENT_HOST", "localhost"),
                agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
            )
            provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # Add OTLP exporter if configured
        if otlp_endpoint or os.getenv("OTLP_ENDPOINT"):
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint or os.getenv("OTLP_ENDPOINT"),
                insecure=os.getenv("OTLP_INSECURE", "true").lower() == "true",
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer for this service (use provider directly to avoid API mismatch)
        self.tracer = provider.get_tracer(
            instrumenting_module_name=f"vertice.{service_name}",
            instrumenting_library_version=version,
        )

    def instrument_fastapi(self, app: Any) -> None:
        """
        Instrument FastAPI application with OpenTelemetry.

        Args:
            app: FastAPI application instance
        """
        FastAPIInstrumentor.instrument_app(app)

    def instrument_all(self) -> None:
        """Instrument all supported libraries."""
        # Instrument HTTP client
        try:
            HTTPXClientInstrumentor().instrument()
        except Exception as e:
            print(f"⚠️  Failed to instrument HTTPX: {e}")

        # Instrument database (skip if API incompatible)
        try:
            AsyncPGInstrumentor().instrument()
        except (TypeError, AttributeError) as e:
            print(f"⚠️  Failed to instrument AsyncPG (API mismatch): {e}")

        # Instrument Redis
        try:
            RedisInstrumentor().instrument()
        except Exception as e:
            print(f"⚠️  Failed to instrument Redis: {e}")

    def add_constitutional_attributes(
        self, span: trace.Span, attributes: Dict[str, Any]
    ) -> None:
        """
        Add constitutional compliance attributes to a span.

        Args:
            span: OpenTelemetry span
            attributes: Dictionary of attributes to add
        """
        for key, value in attributes.items():
            span.set_attribute(key, value)

    def trace_biblical_article(
        self,
        article: str,
        operation: str,
        compliance_score: Optional[float] = None,
    ):
        """
        Create a span for tracking biblical article compliance.

        Args:
            article: Name of the article (e.g., "sophia", "praotes")
            operation: Operation being performed
            compliance_score: Compliance score (0.0-1.0)

        Returns:
            Context manager for the span
        """
        span = self.tracer.start_span(f"biblical_article.{article}.{operation}")

        # Add constitutional attributes
        span.set_attribute("constitution.article", article)
        span.set_attribute("constitution.operation", operation)
        if compliance_score is not None:
            span.set_attribute("constitution.compliance_score", compliance_score)

        return span

    def trace_wisdom_decision(
        self,
        decision_type: str,
        confidence: float,
        wisdom_base_consulted: bool = False,
    ):
        """
        Trace a Sophia (Wisdom) decision.

        Args:
            decision_type: Type of decision being made
            confidence: Confidence level (0.0-1.0)
            wisdom_base_consulted: Whether Wisdom Base was consulted

        Returns:
            Context manager for the span
        """
        span = self.tracer.start_span(f"sophia.decision.{decision_type}")

        span.set_attribute("sophia.decision_type", decision_type)
        span.set_attribute("sophia.confidence", confidence)
        span.set_attribute("sophia.wisdom_base_consulted", wisdom_base_consulted)
        span.set_attribute("constitution.article", "sophia")

        return span

    def trace_gentleness_check(
        self, operation: str, code_lines: int, reversibility_score: float
    ):
        """
        Trace a Praótes (Gentleness) check.

        Args:
            operation: Operation being performed
            code_lines: Number of code lines generated
            reversibility_score: Reversibility score (0.0-1.0)

        Returns:
            Context manager for the span
        """
        span = self.tracer.start_span(f"praotes.check.{operation}")

        span.set_attribute("praotes.operation", operation)
        span.set_attribute("praotes.code_lines", code_lines)
        span.set_attribute("praotes.reversibility_score", reversibility_score)
        span.set_attribute("praotes.compliant", code_lines <= 25 and reversibility_score >= 0.9)
        span.set_attribute("constitution.article", "praotes")

        # Warning if exceeding limits
        if code_lines > 25:
            span.add_event(
                "praotes_violation",
                {"reason": f"Code lines ({code_lines}) exceeds 25 line limit"},
            )

        return span

    def trace_humility_check(
        self, operation: str, confidence: float, escalated: bool = False
    ):
        """
        Trace a Tapeinophrosynē (Humility) check.

        Args:
            operation: Operation being performed
            confidence: Confidence level (0.0-1.0)
            escalated: Whether operation was escalated to Maximus

        Returns:
            Context manager for the span
        """
        span = self.tracer.start_span(f"tapeinophrosyne.check.{operation}")

        span.set_attribute("tapeinophrosyne.operation", operation)
        span.set_attribute("tapeinophrosyne.confidence", confidence)
        span.set_attribute("tapeinophrosyne.escalated", escalated)
        span.set_attribute("tapeinophrosyne.compliant", confidence >= 0.85)
        span.set_attribute("constitution.article", "tapeinophrosyne")

        # Event if below confidence threshold
        if confidence < 0.85:
            span.add_event(
                "low_confidence_detected",
                {
                    "confidence": confidence,
                    "threshold": 0.85,
                    "escalated": escalated,
                },
            )

        return span

    def trace_sabbath_check(self, is_sabbath: bool, operation: str, is_p0: bool = False):
        """
        Trace a Sabbath observance check.

        Args:
            is_sabbath: Whether it's currently Sabbath (Sunday)
            operation: Operation being attempted
            is_p0: Whether operation is P0 critical

        Returns:
            Context manager for the span
        """
        span = self.tracer.start_span(f"sabbath.check.{operation}")

        span.set_attribute("sabbath.is_sabbath", is_sabbath)
        span.set_attribute("sabbath.operation", operation)
        span.set_attribute("sabbath.is_p0", is_p0)
        span.set_attribute("sabbath.allowed", not is_sabbath or is_p0)
        span.set_attribute("constitution.article", "sabbath")

        # Event if non-P0 operation attempted on Sabbath
        if is_sabbath and not is_p0:
            span.add_event(
                "sabbath_violation",
                {"reason": "Non-P0 operation attempted on Sabbath"},
            )

        return span

    def trace_truth_check(
        self,
        operation: str,
        uncertainty_declared: bool = False,
        hallucination_detected: bool = False,
    ):
        """
        Trace an Aletheia (Truth) check.

        Args:
            operation: Operation being performed
            uncertainty_declared: Whether uncertainty was declared
            hallucination_detected: Whether hallucination was detected

        Returns:
            Context manager for the span
        """
        span = self.tracer.start_span(f"aletheia.check.{operation}")

        span.set_attribute("aletheia.operation", operation)
        span.set_attribute("aletheia.uncertainty_declared", uncertainty_declared)
        span.set_attribute("aletheia.hallucination_detected", hallucination_detected)
        span.set_attribute("constitution.article", "aletheia")

        # CRITICAL: Hallucination detected
        if hallucination_detected:
            span.add_event(
                "CRITICAL_hallucination_detected",
                {
                    "severity": "CRITICAL",
                    "constitutional_violation": "aletheia",
                    "action_required": "IMMEDIATE",
                },
            )

        return span

    def trace_deter_agent_layer(
        self, layer: int, layer_name: str, operation: str, metadata: Optional[Dict] = None
    ):
        """
        Trace a DETER-AGENT framework layer operation.

        Args:
            layer: Layer number (1-5)
            layer_name: Name of the layer
            operation: Operation being performed
            metadata: Optional metadata

        Returns:
            Context manager for the span
        """
        span = self.tracer.start_span(f"deter_agent.layer{layer}.{operation}")

        span.set_attribute("deter_agent.layer", layer)
        span.set_attribute("deter_agent.layer_name", layer_name)
        span.set_attribute("deter_agent.operation", operation)

        if metadata:
            for key, value in metadata.items():
                span.set_attribute(f"deter_agent.{key}", value)

        return span


def create_constitutional_tracer(
    service_name: str, version: str = "1.0.0"
) -> ConstitutionalTracer:
    """
    Factory function to create a constitutional tracer.

    Args:
        service_name: Name of the service
        version: Service version

    Returns:
        Configured ConstitutionalTracer instance
    """
    tracer = ConstitutionalTracer(
        service_name=service_name,
        version=version,
        jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
    )

    # Auto-instrument all supported libraries
    tracer.instrument_all()

    return tracer


# 🤖 Generated with [Claude Code](https://claude.com/claude-code)
#
# Co-Authored-By: Claude <noreply@anthropic.com>
