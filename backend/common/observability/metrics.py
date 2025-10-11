"""Common Observability Module - Prometheus Metrics.

Reusable Prometheus instrumentation for all Vértice services.
Provides standardized metrics following RED method (Rate, Errors, Duration).

Usage:
    from backend.common.observability.metrics import ServiceMetrics
    
    metrics = ServiceMetrics(service_name="bas_service")
    
    # Instrument endpoint
    @app.get("/health")
    async def health():
        with metrics.track_request("health"):
            return {"status": "healthy"}
"""

import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for graceful degradation
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def time(self): return _MockTimer()
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    class _MockTimer:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    def generate_latest() -> bytes:
        return b"# Prometheus not available"
    
    CONTENT_TYPE_LATEST = "text/plain"


class ServiceMetrics:
    """Standardized metrics collection for Vértice services.
    
    Implements RED method:
    - Rate: requests per second
    - Errors: error rate
    - Duration: request latency
    
    Additional metrics:
    - Resource usage (CPU, memory, connections)
    - Business metrics (custom per service)
    """
    
    def __init__(
        self,
        service_name: str,
        namespace: str = "vertice",
        enable_business_metrics: bool = True
    ):
        """Initialize service metrics.
        
        Args:
            service_name: Name of the service (e.g., "bas_service")
            namespace: Metrics namespace (default: "vertice")
            enable_business_metrics: Enable custom business metrics
        """
        self.service_name = service_name
        self.namespace = namespace
        self.enabled = PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            return
        
        # RED Method Metrics
        self.requests_total = Counter(
            f"{namespace}_{service_name}_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )
        
        self.requests_duration = Histogram(
            f"{namespace}_{service_name}_requests_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.errors_total = Counter(
            f"{namespace}_{service_name}_errors_total",
            "Total errors",
            ["error_type", "endpoint"]
        )
        
        # Resource Metrics
        self.active_connections = Gauge(
            f"{namespace}_{service_name}_active_connections",
            "Number of active connections"
        )
        
        self.memory_usage_bytes = Gauge(
            f"{namespace}_{service_name}_memory_usage_bytes",
            "Memory usage in bytes"
        )
        
        # Service Info
        self.service_info = Info(
            f"{namespace}_{service_name}_info",
            "Service information"
        )
        
        # Business Metrics (customizable per service)
        if enable_business_metrics:
            self.business_operations = Counter(
                f"{namespace}_{service_name}_operations_total",
                "Total business operations",
                ["operation_type", "status"]
            )
            
            self.operation_duration = Histogram(
                f"{namespace}_{service_name}_operation_duration_seconds",
                "Business operation duration",
                ["operation_type"],
                buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
            )
    
    @contextmanager
    def track_request(
        self,
        endpoint: str,
        method: str = "GET"
    ):
        """Context manager to track HTTP request metrics.
        
        Usage:
            with metrics.track_request("health"):
                # Your endpoint code
                return {"status": "ok"}
        """
        if not self.enabled:
            yield
            return
        
        start_time = time.time()
        status = "200"
        
        try:
            yield
        except Exception as e:
            status = "500"
            self.errors_total.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            self.requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            self.requests_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    def track_business_operation(
        self,
        operation_type: str,
        status: str = "success",
        duration: Optional[float] = None
    ):
        """Track business-specific operation.
        
        Args:
            operation_type: Type of operation (e.g., "simulation", "scan")
            status: Operation status (success/failure/timeout)
            duration: Operation duration in seconds
        """
        if not self.enabled:
            return
        
        self.business_operations.labels(
            operation_type=operation_type,
            status=status
        ).inc()
        
        if duration is not None:
            self.operation_duration.labels(
                operation_type=operation_type
            ).observe(duration)
    
    def set_memory_usage(self, bytes_used: int):
        """Update memory usage metric."""
        if self.enabled:
            self.memory_usage_bytes.set(bytes_used)
    
    def set_active_connections(self, count: int):
        """Update active connections metric."""
        if self.enabled:
            self.active_connections.set(count)
    
    def set_service_info(self, version: str, **kwargs):
        """Set service information.
        
        Args:
            version: Service version
            **kwargs: Additional info (e.g., environment, git_commit)
        """
        if self.enabled:
            info = {"version": version, **kwargs}
            self.service_info.info(info)
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format.
        
        Returns:
            Metrics in Prometheus text format
        """
        if not self.enabled:
            return b"# Prometheus not available"
        
        return generate_latest()
    
    @property
    def content_type(self) -> str:
        """Content type for metrics endpoint."""
        return CONTENT_TYPE_LATEST


# Convenience function for FastAPI integration
def create_metrics_endpoint(metrics: ServiceMetrics):
    """Create FastAPI metrics endpoint.
    
    Usage:
        from fastapi import FastAPI, Response
        from backend.common.observability.metrics import (
            ServiceMetrics, 
            create_metrics_endpoint
        )
        
        app = FastAPI()
        metrics = ServiceMetrics("my_service")
        
        @app.get("/metrics")
        async def metrics_endpoint():
            return create_metrics_endpoint(metrics)
    
    Returns:
        FastAPI Response with Prometheus metrics
    """
    from fastapi import Response
    
    async def metrics_handler():
        return Response(
            content=metrics.get_metrics(),
            media_type=metrics.content_type
        )
    
    return metrics_handler


__all__ = [
    "ServiceMetrics",
    "create_metrics_endpoint",
    "PROMETHEUS_AVAILABLE",
]
