"""Main entry point - imports app from api.py."""
from api import app  # api.py in the same directory

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


__all__ = ["app"]
