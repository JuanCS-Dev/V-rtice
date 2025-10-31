"""
Prometheus Metrics Exporter for Vértice Services.

Exposes constitutional metrics, biblical article compliance,
and service-specific business metrics via HTTP endpoint.

Biblical Foundation:
- Aletheia (Truth): Transparent metrics exposure
- Stewardship: Responsible monitoring of system resources
"""

import time

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Gauge,
    Info,
    generate_latest,
)

from .constitutional_metrics import (
    record_constitutional_compliance,
    record_fpc_score,
    record_fruit_compliance,
    record_lei_score,
    record_sabbath_status,
)

# Service metadata
service_info = Info("vertice_service", "Vértice service metadata")

# System metrics
service_uptime_seconds = Gauge(
    "vertice_service_uptime_seconds", "Service uptime in seconds", ["service"]
)

service_health_status = Gauge(
    "vertice_service_health_status",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service", "check_type"],
)


class MetricsExporter:
    """Prometheus metrics exporter for Vértice services."""

    def __init__(self, service_name: str, version: str = "1.0.0"):
        """
        Initialize metrics exporter.

        Args:
            service_name: Name of the service (e.g., "penelope", "maba", "mvp")
            version: Service version
        """
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()

        # Set service metadata
        service_info.info(
            {
                "service": service_name,
                "version": version,
                "constitution_version": "3.0",
                "deter_agent_enabled": "true",
            }
        )

        # Initialize baseline metrics
        self._initialize_baseline_metrics()

    def _initialize_baseline_metrics(self) -> None:
        """Initialize baseline constitutional metrics."""
        # Set initial CRS scores for all 7 articles (target: >= 95%)
        articles = [
            "sophia",
            "praotes",
            "tapeinophrosyne",
            "stewardship",
            "agape",
            "sabbath",
            "aletheia",
        ]
        for article in articles:
            record_constitutional_compliance(
                service=self.service_name,
                article=article,
                score=95.0,  # Initial baseline
            )

        # Set initial quality metrics (Constitution requirements)
        record_lei_score(self.service_name, 0.8)  # Must be < 1.0
        record_fpc_score(self.service_name, 85.0)  # Must be >= 80%

        # Set initial Sabbath status (default: not Sabbath)
        record_sabbath_status(self.service_name, False)

        # Set initial Fruits of the Spirit compliance
        fruits = [
            "agape",  # Love
            "chara",  # Joy
            "eirene",  # Peace
            "makrothymia",  # Patience
            "chrestotes",  # Kindness
            "agathosyne",  # Goodness
            "pistis",  # Faithfulness
            "praotes",  # Gentleness
            "enkrateia",  # Self-control
        ]
        for fruit in fruits:
            record_fruit_compliance(
                service=self.service_name, fruit=fruit, score=0.90  # Initial baseline
            )

    def update_uptime(self) -> None:
        """Update service uptime metric."""
        uptime = time.time() - self.start_time
        service_uptime_seconds.labels(service=self.service_name).set(uptime)

    def update_health_status(self, check_type: str, is_healthy: bool) -> None:
        """
        Update service health status.

        Args:
            check_type: Type of health check (e.g., "database", "redis", "api")
            is_healthy: Whether the check passed
        """
        service_health_status.labels(
            service=self.service_name, check_type=check_type
        ).set(1.0 if is_healthy else 0.0)

    def create_router(self) -> APIRouter:
        """
        Create FastAPI router with metrics endpoint.

        Returns:
            APIRouter with /metrics endpoint
        """
        router = APIRouter(tags=["Observability"])

        @router.get(
            "/metrics",
            response_class=Response,
            summary="Prometheus Metrics",
            description=(
                "Exposes Prometheus metrics including:\n"
                "- Constitutional compliance (7 Biblical Articles)\n"
                "- DETER-AGENT framework metrics (5 layers)\n"
                "- Quality metrics (LEI, FPC, CRS)\n"
                "- Fruits of the Spirit compliance\n"
                "- Service-specific business metrics"
            ),
        )
        async def metrics() -> Response:
            """Export Prometheus metrics."""
            # Update uptime before exposing metrics
            self.update_uptime()

            # Generate metrics in Prometheus format
            metrics_output = generate_latest(REGISTRY)

            return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)

        @router.get(
            "/metrics/constitutional",
            summary="Constitutional Metrics Summary",
            description="Human-readable summary of constitutional compliance",
        )
        async def constitutional_summary() -> dict:
            """Return constitutional compliance summary."""
            return {
                "service": self.service_name,
                "constitution_version": "3.0",
                "framework": "DETER-AGENT",
                "articles": {
                    "sophia": "Wisdom - Enabled",
                    "praotes": "Gentleness - Max 25 lines, Reversibility >= 0.90",
                    "tapeinophrosyne": "Humility - Confidence >= 85%",
                    "stewardship": "Developer intent preservation",
                    "agape": "User impact prioritization",
                    "sabbath": "Sunday rest with P0 exceptions",
                    "aletheia": "Truth - Zero hallucinations",
                },
                "quality_requirements": {
                    "lei": "< 1.0 (Lazy Execution Index)",
                    "fpc": ">= 80% (First-Pass Correctness)",
                    "crs": ">= 95% (Constitutional Rule Satisfaction)",
                    "test_coverage": ">= 90%",
                    "hallucinations": "= 0",
                },
                "deter_agent_layers": [
                    "Layer 1: Constitutional Control (Strategic)",
                    "Layer 2: Deliberation Control (Cognitive)",
                    "Layer 3: State Management Control (Memory)",
                    "Layer 4: Execution Control (Operational)",
                    "Layer 5: Incentive Control (Behavioral)",
                ],
            }

        return router


# Helper function to check if today is Sabbath (Sunday)
def is_sabbath() -> bool:
    """
    Check if today is Sabbath (Sunday).

    Returns:
        True if today is Sunday, False otherwise
    """
    import datetime

    return datetime.datetime.now().weekday() == 6  # Sunday = 6


# Helper function to update Sabbath status automatically
def auto_update_sabbath_status(service_name: str) -> None:
    """Automatically update Sabbath status based on current day."""
    record_sabbath_status(service_name, is_sabbath())


# 🤖 Generated with [Claude Code](https://claude.com/claude-code)
#
# Co-Authored-By: Claude <noreply@anthropic.com>
