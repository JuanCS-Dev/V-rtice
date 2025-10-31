"""Uvicorn entrypoint for Tegumentar Service."""

from __future__ import annotations

import uvicorn

from app import app, service_settings

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck



def run() -> None:
    uvicorn.run(
        app,
        host=service_settings.host,
        port=service_settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    run()
