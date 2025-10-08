"""API Dependencies - PRODUCTION-READY

FastAPI dependency injection functions.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Optional

from fastapi import HTTPException, status

from monitoring import HealthChecker, MetricsCollector, PrometheusExporter


def get_prometheus_exporter() -> PrometheusExporter:
    """
    Get Prometheus exporter instance.

    Returns:
        PrometheusExporter instance

    Raises:
        HTTPException: If exporter not initialized
    """
    from api.main import prometheus_exporter

    if prometheus_exporter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus exporter not initialized",
        )

    return prometheus_exporter


def get_health_checker() -> HealthChecker:
    """
    Get health checker instance.

    Returns:
        HealthChecker instance

    Raises:
        HTTPException: If health checker not initialized
    """
    from api.main import health_checker

    if health_checker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health checker not initialized",
        )

    return health_checker


def get_metrics_collector() -> MetricsCollector:
    """
    Get metrics collector instance.

    Returns:
        MetricsCollector instance

    Raises:
        HTTPException: If metrics collector not initialized
    """
    from api.main import metrics_collector

    if metrics_collector is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics collector not initialized",
        )

    return metrics_collector


def get_prometheus_exporter_optional() -> Optional[PrometheusExporter]:
    """
    Get Prometheus exporter instance (optional).

    Returns:
        PrometheusExporter instance or None
    """
    from api.main import prometheus_exporter

    return prometheus_exporter


def get_health_checker_optional() -> Optional[HealthChecker]:
    """
    Get health checker instance (optional).

    Returns:
        HealthChecker instance or None
    """
    from api.main import health_checker

    return health_checker


def get_metrics_collector_optional() -> Optional[MetricsCollector]:
    """
    Get metrics collector instance (optional).

    Returns:
        MetricsCollector instance or None
    """
    from api.main import metrics_collector

    return metrics_collector
