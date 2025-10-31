"""
Mock Service for Sidecar Testing

This is a minimal FastAPI service used exclusively for testing the
Vértice Registry Sidecar Agent.
"""

from fastapi import FastAPI
import time

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


app = FastAPI(title="Test Service", version="1.0.0")

start_time = time.time()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "uptime": time.time() - start_time,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Test Service for Sidecar - Running!"}
