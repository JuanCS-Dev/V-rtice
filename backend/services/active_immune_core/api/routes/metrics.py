"""Metrics Routes - PRODUCTION-READY

Metrics endpoints for Prometheus and custom metrics.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Dict, Any
from fastapi import APIRouter
from fastapi.responses import Response, JSONResponse

router = APIRouter()


@router.get("/", response_class=Response)
async def prometheus_metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.

    Returns:
        Prometheus-formatted metrics
    """
    from api.main import prometheus_exporter

    if not prometheus_exporter:
        return Response(
            content="# Prometheus exporter not initialized\n",
            media_type="text/plain",
        )

    # Export metrics in Prometheus format
    metrics = prometheus_exporter.export_metrics()

    return Response(
        content=metrics,
        media_type="text/plain; version=0.0.4",
    )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics(window: int = 60) -> Dict[str, Any]:
    """
    Get comprehensive statistics.

    Args:
        window: Time window in seconds for aggregations (default: 60)

    Returns:
        Statistics including counters, gauges, and time-series aggregations
    """
    from api.main import metrics_collector

    if not metrics_collector:
        return {
            "error": "Metrics collector not initialized",
            "counters": {},
            "gauges": {},
        }

    # Get statistics
    stats = metrics_collector.get_statistics(window=window)

    return stats


@router.get("/rates", response_model=Dict[str, float])
async def get_rates(window: int = 60) -> Dict[str, float]:
    """
    Get metric rates (per second).

    Args:
        window: Time window in seconds (default: 60)

    Returns:
        Rates for all counters
    """
    from api.main import metrics_collector

    if not metrics_collector:
        return {}

    # Get rates
    rates = metrics_collector.get_rates(window=window)

    return rates


@router.get("/trends/{metric_name}", response_model=Dict[str, Any])
async def get_metric_trend(metric_name: str, window: int = 300) -> JSONResponse:
    """
    Get trend analysis for specific metric.

    Args:
        metric_name: Name of the metric
        window: Time window in seconds (default: 300)

    Returns:
        Trend analysis (direction, slope, confidence)
    """
    from api.main import metrics_collector

    if not metrics_collector:
        return JSONResponse(
            status_code=503,
            content={"error": "Metrics collector not initialized"},
        )

    # Get trends
    trends = metrics_collector.get_trends(metric_name, window=window)

    if not trends:
        return JSONResponse(
            status_code=404,
            content={"error": f"No data available for metric '{metric_name}'"},
        )

    return JSONResponse(
        status_code=200,
        content=trends,
    )


@router.get("/aggregation/{metric_name}", response_model=Dict[str, Any])
async def get_metric_aggregation(metric_name: str, window: int = 60) -> JSONResponse:
    """
    Get time-series aggregation for specific metric.

    Args:
        metric_name: Name of the metric
        window: Time window in seconds (default: 60)

    Returns:
        Aggregated statistics (min, max, avg, p50, p95, p99)
    """
    from api.main import metrics_collector

    if not metrics_collector:
        return JSONResponse(
            status_code=503,
            content={"error": "Metrics collector not initialized"},
        )

    # Get aggregation
    aggregation = metrics_collector.aggregate_time_series(metric_name, window=window)

    if not aggregation:
        return JSONResponse(
            status_code=404,
            content={"error": f"No data available for metric '{metric_name}'"},
        )

    return JSONResponse(
        status_code=200,
        content=aggregation,
    )


@router.get("/list", response_model=Dict[str, Any])
async def list_metrics() -> Dict[str, Any]:
    """
    List all available metrics.

    Returns:
        List of all metric names and their types
    """
    from api.main import metrics_collector

    if not metrics_collector:
        return {
            "error": "Metrics collector not initialized",
            "metrics": [],
        }

    # Get metric names
    metric_names = metrics_collector.get_metric_names()

    return {
        "total_metrics": len(metric_names),
        "metrics": metric_names,
    }


@router.post("/reset-counters")
async def reset_counters() -> Dict[str, str]:
    """
    Reset all counters to zero.

    WARNING: This will reset all counter metrics!

    Returns:
        Success message
    """
    from api.main import metrics_collector

    if not metrics_collector:
        return {"error": "Metrics collector not initialized"}

    # Reset counters
    metrics_collector.reset_counters()

    return {"message": "All counters have been reset"}


@router.post("/clear-history")
async def clear_history() -> Dict[str, str]:
    """
    Clear all time-series history.

    WARNING: This will delete all historical data!

    Returns:
        Success message
    """
    from api.main import metrics_collector

    if not metrics_collector:
        return {"error": "Metrics collector not initialized"}

    # Clear history
    metrics_collector.clear_history()

    return {"message": "All time-series history has been cleared"}
