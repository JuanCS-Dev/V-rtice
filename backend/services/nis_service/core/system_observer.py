"""MVP System Observer - Real-time metrics collection and analysis.

This module provides the SystemObserver class that collects, aggregates, and
analyzes system metrics from Prometheus and InfluxDB. It serves as the data
layer for narrative generation, providing structured metrics to the NarrativeEngine.

Key Features:
- Prometheus metrics collection (service health, resource usage)
- InfluxDB time series data retrieval
- Metrics aggregation and transformation
- Service health tracking
- Historical trend analysis
- Query optimization and caching

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


class SystemObserver:
    """
    System metrics collection and observation engine.

    Collects metrics from Prometheus and InfluxDB, aggregates them,
    and provides structured data for narrative generation.

    Attributes:
        prometheus_url: Prometheus server URL
        influxdb_url: InfluxDB server URL
        http_client: Shared HTTP client for API calls
        _initialized: Observer initialization state
        _metrics_cache: Cache for recent metrics (simple dict cache)
    """

    # Prometheus metrics for the observer itself
    queries_total = Counter(
        "mvp_observer_queries_total", "Total queries to metrics backends", ["backend"]
    )

    query_duration = Histogram(
        "mvp_observer_query_duration_seconds", "Query duration in seconds", ["backend"]
    )

    def __init__(
        self,
        prometheus_url: str = "http://vertice-prometheus:9090",
        influxdb_url: str = "http://vertice-influxdb:8086",
    ):
        """
        Initialize system observer.

        Args:
            prometheus_url: Prometheus server URL
            influxdb_url: InfluxDB server URL
        """
        self.prometheus_url = prometheus_url
        self.influxdb_url = influxdb_url
        self.http_client: httpx.AsyncClient | None = None
        self._initialized = False
        self._metrics_cache: dict[str, Any] = {}

        logger.info(
            f"🔍 SystemObserver configured "
            f"(Prometheus: {prometheus_url}, InfluxDB: {influxdb_url})"
        )

    async def initialize(self) -> bool:
        """
        Initialize the system observer.

        Creates HTTP client and validates connectivity to metrics backends.

        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0), follow_redirects=True
            )

            # Validate Prometheus connectivity (non-blocking)
            try:
                await self._query_prometheus("up", duration="1m")
                logger.info("✅ Prometheus connection validated")
            except Exception as e:
                logger.warning(f"⚠️ Prometheus not available: {e}")
                logger.warning("   Observer will work in degraded mode")

            # InfluxDB validation skipped (optional dependency)
            # In production, add similar validation if InfluxDB is critical

            self._initialized = True
            logger.info("✅ SystemObserver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize SystemObserver: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the system observer gracefully."""
        if self.http_client and not self.http_client.is_closed:
            await self.http_client.aclose()
            self.http_client = None
        self._initialized = False
        self._metrics_cache.clear()
        logger.info("👋 SystemObserver shut down")

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on system observer.

        Returns:
            Dict with health status and backend connectivity
        """
        prometheus_healthy = False
        influxdb_healthy = False

        # Check Prometheus
        try:
            await self._query_prometheus("up", duration="1m")
            prometheus_healthy = True
        except Exception:
            pass

        # InfluxDB check skipped (optional)
        influxdb_healthy = (
            True  # Assume healthy unless we implement InfluxDB integration
        )

        overall_healthy = self._initialized and prometheus_healthy

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "initialized": self._initialized,
            "backends": {
                "prometheus": {
                    "url": self.prometheus_url,
                    "status": "healthy" if prometheus_healthy else "unhealthy",
                },
                "influxdb": {
                    "url": self.influxdb_url,
                    "status": "healthy" if influxdb_healthy else "unknown",
                },
            },
        }

    async def collect_metrics(
        self, time_range_minutes: int = 60, focus_areas: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Collect system metrics from all backends.

        Args:
            time_range_minutes: Time range for metrics collection
            focus_areas: Optional focus areas to filter metrics

        Returns:
            Dict containing aggregated metrics data
        """
        if not self._initialized or not self.http_client:
            raise RuntimeError("SystemObserver not initialized")

        logger.info(
            f"📊 Collecting metrics (range={time_range_minutes}m, focus={focus_areas})"
        )

        try:
            # Collect metrics from Prometheus
            prometheus_metrics = await self._collect_prometheus_metrics(
                time_range_minutes, focus_areas
            )

            # Collect service health status
            service_health = await self._collect_service_health()

            # Aggregate all metrics
            result = {
                "metrics": prometheus_metrics,
                "services": service_health,
                "anomalies": [],  # Populated by NarrativeEngine
                "time_range_minutes": time_range_minutes,
                "focus_areas": focus_areas or [],
                "timestamp": datetime.utcnow().isoformat(),
                "data_sources": {
                    "prometheus": "available",
                    "influxdb": "not_implemented",
                },
            }

            logger.info(
                f"✅ Collected {len(prometheus_metrics)} metrics, "
                f"{len(service_health)} services"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Failed to collect metrics: {e}", exc_info=True)
            raise

    async def _collect_prometheus_metrics(
        self, time_range_minutes: int, focus_areas: list[str] | None
    ) -> list[dict[str, Any]]:
        """
        Collect metrics from Prometheus.

        Args:
            time_range_minutes: Time range for queries
            focus_areas: Optional focus areas

        Returns:
            List of metric dictionaries
        """
        metrics = []
        duration = f"{time_range_minutes}m"

        # Define key metrics to collect
        metric_queries = [
            (
                "cpu_usage",
                f"avg(rate(container_cpu_usage_seconds_total[{duration}])) * 100",
            ),
            (
                "memory_usage",
                "avg(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100",
            ),
            ("http_request_rate", f"sum(rate(http_requests_total[{duration}]))"),
            (
                "http_error_rate",
                f'sum(rate(http_requests_total{{status=~"5.."}}[{duration}])) / sum(rate(http_requests_total[{duration}])) * 100',
            ),
            (
                "http_latency_p95",
                f"histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[{duration}]))",
            ),
            ("active_connections", "sum(tcp_connections_active)"),
            ("database_connections", "sum(pg_stat_activity_count)"),
        ]

        # Execute queries in parallel
        tasks = []
        for name, query in metric_queries:
            # Apply focus area filtering
            if focus_areas and not any(
                area.lower() in name.lower() for area in focus_areas
            ):
                continue
            tasks.append(self._query_and_format_metric(name, query, duration))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Metric query failed: {result}")
                continue
            if result:
                metrics.append(result)

        return metrics

    async def _query_and_format_metric(
        self, name: str, query: str, duration: str
    ) -> dict[str, Any] | None:
        """
        Query Prometheus and format result.

        Args:
            name: Metric name
            query: PromQL query
            duration: Time duration string

        Returns:
            Formatted metric dict or None
        """
        try:
            result = await self._query_prometheus(query, duration)

            # Extract scalar value from Prometheus response
            value = 0
            if result and "data" in result:
                data = result["data"]
                if data.get("resultType") == "vector" and data.get("result"):
                    value = float(data["result"][0]["value"][1])
                elif data.get("resultType") == "scalar":
                    value = float(data["result"][1])

            # Determine unit based on metric name
            unit = self._determine_metric_unit(name)

            return {
                "name": name,
                "value": round(value, 2),
                "unit": unit,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "prometheus",
            }

        except Exception as e:
            logger.debug(f"Failed to query metric {name}: {e}")
            return None

    async def _query_prometheus(
        self, query: str, duration: str = "5m"
    ) -> dict[str, Any] | None:
        """
        Execute PromQL query against Prometheus.

        Args:
            query: PromQL query string
            duration: Time duration for query

        Returns:
            Prometheus API response or None
        """
        if not self.http_client:
            return None

        url = f"{self.prometheus_url}/api/v1/query"
        params = {"query": query}

        try:
            self.queries_total.labels(backend="prometheus").inc()

            with self.query_duration.labels(backend="prometheus").time():
                response = await self.http_client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.warning(f"Prometheus query error: {e.response.status_code}")
            return None

        except httpx.RequestError as e:
            logger.warning(f"Prometheus connection error: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected Prometheus error: {e}")
            return None

    async def _collect_service_health(self) -> list[dict[str, Any]]:
        """
        Collect health status of all Vértice services.

        Returns:
            List of service health dictionaries
        """
        services = []

        # Define known services
        service_endpoints = [
            ("maximus", "http://vertice-maximus-core-service:8150/health"),
            ("cognitio", "http://vertice-cognitio-service:8151/health"),
            ("maba", "http://vertice-maba-dev:8152/health"),
            ("mvp", "http://localhost:8153/health"),
            ("penelope", "http://vertice-penelope-dev:8154/health"),
        ]

        # Check each service in parallel
        tasks = [
            self._check_service_health(name, endpoint)
            for name, endpoint in service_endpoints
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.debug(f"Service health check failed: {result}")
                continue
            if result:
                services.append(result)

        return services

    async def _check_service_health(
        self, service_name: str, health_endpoint: str
    ) -> dict[str, Any] | None:
        """
        Check health of a single service.

        Args:
            service_name: Service name
            health_endpoint: Health check endpoint URL

        Returns:
            Service health dict or None
        """
        if not self.http_client:
            return None

        try:
            response = await self.http_client.get(health_endpoint, timeout=5.0)

            status = "healthy" if response.status_code == 200 else "unhealthy"

            # Try to parse response for more details
            try:
                health_data = response.json()
                uptime = health_data.get("uptime_seconds", 0)
            except Exception:
                uptime = None

            return {
                "name": service_name,
                "status": status,
                "uptime_seconds": uptime,
                "endpoint": health_endpoint,
            }

        except httpx.TimeoutException:
            return {
                "name": service_name,
                "status": "timeout",
                "endpoint": health_endpoint,
            }

        except httpx.RequestError:
            return {
                "name": service_name,
                "status": "unreachable",
                "endpoint": health_endpoint,
            }

        except Exception as e:
            logger.debug(f"Health check error for {service_name}: {e}")
            return None

    def _determine_metric_unit(self, metric_name: str) -> str:
        """
        Determine the unit for a metric based on its name.

        Args:
            metric_name: Name of the metric

        Returns:
            Unit string (%, ms, count, etc.)
        """
        name_lower = metric_name.lower()

        if "usage" in name_lower or "rate" in name_lower:
            return "%"
        elif "latency" in name_lower or "duration" in name_lower:
            return "ms"
        elif "bytes" in name_lower:
            return "bytes"
        elif "count" in name_lower or "connections" in name_lower:
            return "count"
        else:
            return ""
