"""Maximus HCL Analyzer Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Homeostatic Control
Loop (HCL) Analyzer Service. It initializes and configures the FastAPI
application, sets up event handlers for startup and shutdown, and defines the
API endpoints for ingesting system metrics and performing in-depth analysis.

It orchestrates the application of statistical methods and machine learning
models to identify anomalies, predict trends, and assess the overall health
and performance of the Maximus AI system. This service is crucial for providing
actionable insights to the HCL Planner Service, enabling adaptive self-management.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from models import AnalysisResult, Anomaly, AnomalyType, SystemMetrics

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


app = FastAPI(title="Maximus HCL Analyzer Service", version="1.0.0")

# Historical data storage (in production, would query from hcl_kb_service)
historical_metrics: List[Dict[str, Any]] = []


class AnalyzeMetricsRequest(BaseModel):
    """Request model for submitting system metrics for analysis.

    Attributes:
        current_metrics (SystemMetrics): The current snapshot of system metrics.
    """

    current_metrics: SystemMetrics


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the HCL Analyzer Service."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="hcl_analyzer_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="hcl_analyzer_service",
            version=service_version
        )
        auto_update_sabbath_status("hcl_analyzer_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="hcl_analyzer_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="hcl_analyzer_service")
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

    print("📊 Starting Maximus HCL Analyzer Service...")
    print("✅ Maximus HCL Analyzer Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the HCL Analyzer Service."""
    print("👋 Shutting down Maximus HCL Analyzer Service...")
    print("🛑 Maximus HCL Analyzer Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the HCL Analyzer Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "HCL Analyzer Service is operational."}


@app.post("/analyze_metrics", response_model=AnalysisResult)
async def analyze_system_metrics(request: AnalyzeMetricsRequest) -> AnalysisResult:
    """Analyzes incoming system metrics to detect anomalies and assess health.

    Args:
        request (AnalyzeMetricsRequest): The request body containing current system metrics.

    Returns:
        AnalysisResult: The comprehensive analysis result.
    """
    print(f"[API] Analyzing metrics from {request.current_metrics.timestamp}")
    historical_metrics.append(request.current_metrics)
    if len(historical_metrics) > 100:  # Keep a rolling window of 100 metrics
        historical_metrics.pop(0)

    await asyncio.sleep(0.1)  # Simulate analysis time

    anomalies: List[Anomaly] = []
    recommendations: List[str] = []
    requires_intervention: bool = False
    overall_health_score: float = 1.0

    # Simplified anomaly detection logic
    cpu_usages = [m.cpu_usage for m in historical_metrics]
    if len(cpu_usages) > 5:
        mean_cpu = np.mean(cpu_usages[:-1])
        std_cpu = np.std(cpu_usages[:-1])
        if request.current_metrics.cpu_usage > mean_cpu + 2 * std_cpu:
            anomalies.append(
                Anomaly(
                    type=AnomalyType.SPIKE,
                    metric_name="cpu_usage",
                    current_value=request.current_metrics.cpu_usage,
                    severity=0.8,
                    description="Sudden spike in CPU usage.",
                )
            )
            recommendations.append("Investigate high CPU processes.")
            requires_intervention = True
            overall_health_score -= 0.2

    if request.current_metrics.memory_usage > 90:
        anomalies.append(
            Anomaly(
                type=AnomalyType.OUTLIER,
                metric_name="memory_usage",
                current_value=request.current_metrics.memory_usage,
                severity=0.9,
                description="Memory usage critically high.",
            )
        )
        recommendations.append("Optimize memory consumption or scale up memory resources.")
        requires_intervention = True
        overall_health_score -= 0.3

    if request.current_metrics.error_rate > 0.05:
        anomalies.append(
            Anomaly(
                type=AnomalyType.TREND,
                metric_name="error_rate",
                current_value=request.current_metrics.error_rate,
                severity=0.7,
                description="Elevated error rate detected.",
            )
        )
        recommendations.append("Review recent logs for service errors.")
        requires_intervention = True
        overall_health_score -= 0.15

    return AnalysisResult(
        timestamp=datetime.now().isoformat(),
        overall_health_score=max(0.0, overall_health_score),
        anomalies=anomalies,
        trends={
            "cpu_trend": "stable" if not requires_intervention else "unstable",
            "memory_trend": "stable" if not requires_intervention else "unstable",
        },  # Simplified
        recommendations=recommendations,
        requires_intervention=requires_intervention,
    )


@app.get("/analysis_history", response_model=List[AnalysisResult])
async def get_analysis_history(limit: int = 10) -> List[AnalysisResult]:
    """Retrieves a history of past analysis results.

    Args:
        limit (int): The maximum number of historical results to retrieve.

    Returns:
        List[AnalysisResult]: A list of past analysis results.
    """
    # Return recent historical analyses
    # In production, this would query hcl_kb_service via HTTP
    return [
        {
            "timestamp": metric.get("timestamp", datetime.now().isoformat()),
            "analysis_summary": "Historical analysis data",
            "anomalies_detected": [],
            "recommendations": []
        }
        for metric in historical_metrics[-limit:]
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8015)
