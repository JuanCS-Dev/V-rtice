"""Maximus HCL Monitor Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Homeostatic Control
Loop (HCL) Monitor Service. It initializes and configures the FastAPI
application, sets up event handlers for startup and shutdown, and defines the
API endpoints for collecting and exposing system metrics.

It orchestrates the continuous collection of real-time operational data from
various Maximus AI services and the underlying infrastructure. This service is
crucial for providing accurate and up-to-date monitoring information to the
HCL Analyzer Service, enabling effective self-management and adaptive behavior.
"""

import asyncio
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI

from collectors import SystemMetricsCollector

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


app = FastAPI(title="Maximus HCL Monitor Service", version="1.0.0")

# Initialize metrics collector
system_metrics_collector = SystemMetricsCollector()


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the HCL Monitor Service."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="hcl_monitor_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="hcl_monitor_service",
            version=service_version
        )
        auto_update_sabbath_status("hcl_monitor_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="hcl_monitor_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="hcl_monitor_service")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {e}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()

    print("📈 Starting Maximus HCL Monitor Service...")
    # Start background task for continuous metric collection
    asyncio.create_task(system_metrics_collector.start_collection())
    print("✅ Maximus HCL Monitor Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the HCL Monitor Service."""
    print("👋 Shutting down Maximus HCL Monitor Service...")
    await system_metrics_collector.stop_collection()
    print("🛑 Maximus HCL Monitor Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the HCL Monitor Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "HCL Monitor Service is operational."}


@app.get("/metrics")
async def get_current_metrics() -> Dict[str, Any]:
    """Retrieves the latest collected system metrics.

    Returns:
        Dict[str, Any]: A dictionary containing the current system metrics.
    """
    return system_metrics_collector.get_latest_metrics()


@app.get("/metrics/history", response_model=List[Dict[str, Any]])
async def get_metrics_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves a history of collected system metrics.

    Args:
        limit (int): The maximum number of historical metrics to retrieve.

    Returns:
        List[Dict[str, Any]]: A list of historical system metrics.
    """
    return system_metrics_collector.get_metrics_history(limit)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8018)
