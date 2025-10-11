"""Common Observability Module.

Unified observability for Vértice Platform services.
Provides metrics (Prometheus) and structured logging (JSON).

Quick Start:
    from backend.common.observability import setup_observability, get_logger
    
    # Setup once at startup
    metrics = setup_observability(
        service_name="bas_service",
        version="1.0.0",
        log_level="INFO"
    )
    
    # Use in endpoints
    logger = get_logger(__name__)
    
    @app.get("/health")
    async def health():
        with metrics.track_request("health"):
            logger.info("Health check called")
            return {"status": "healthy"}
"""

from typing import Optional

from .logging import (
    ContextAdapter,
    JSONFormatter,
    correlation_id_middleware,
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
)
from .metrics import (
    PROMETHEUS_AVAILABLE,
    ServiceMetrics,
    create_metrics_endpoint,
)


def setup_observability(
    service_name: str,
    version: str = "1.0.0",
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    enable_metrics: bool = True,
    enable_business_metrics: bool = True,
    **service_info
) -> ServiceMetrics:
    """Setup complete observability (logging + metrics) for service.
    
    Args:
        service_name: Name of the service
        version: Service version
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: "json" or "text"
        log_file: Optional log file path
        enable_metrics: Enable Prometheus metrics
        enable_business_metrics: Enable business-specific metrics
        **service_info: Additional service info (env, commit, etc.)
        
    Returns:
        ServiceMetrics instance
        
    Example:
        metrics = setup_observability(
            service_name="bas_service",
            version="1.0.0",
            environment="production",
            git_commit="abc123"
        )
    """
    # Setup structured logging
    setup_logging(
        service_name=service_name,
        level=log_level,
        format_type=log_format,
        log_file=log_file
    )
    
    logger = get_logger(__name__, service=service_name)
    logger.info(
        "Observability initialized",
        extra={
            "version": version,
            "metrics_enabled": enable_metrics,
            "prometheus_available": PROMETHEUS_AVAILABLE
        }
    )
    
    # Setup metrics
    if enable_metrics:
        metrics = ServiceMetrics(
            service_name=service_name,
            enable_business_metrics=enable_business_metrics
        )
        
        # Set service info
        metrics.set_service_info(version=version, **service_info)
        
        return metrics
    else:
        # Return disabled metrics instance
        return ServiceMetrics(service_name=service_name)


__version__ = "1.0.0"

__all__ = [
    # Main setup
    "setup_observability",
    
    # Logging
    "setup_logging",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "correlation_id_middleware",
    "JSONFormatter",
    "ContextAdapter",
    
    # Metrics
    "ServiceMetrics",
    "create_metrics_endpoint",
    "PROMETHEUS_AVAILABLE",
    
    # Version
    "__version__",
]
