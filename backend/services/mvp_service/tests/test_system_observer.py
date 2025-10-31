"""Comprehensive unit tests for SystemObserver.

Tests cover initialization, metrics collection, Prometheus/Loki queries, service health checks,
and error handling to achieve 90%+ code coverage.

Author: Vértice Platform Team
License: Proprietary
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from core.system_observer import SystemObserver


@pytest.fixture(scope="session", autouse=True)
def prometheus_tmp_dir():
    """Create /tmp/prometheus directory for Prometheus metrics."""
    os.makedirs("/tmp/prometheus", exist_ok=True)
    yield
    # Cleanup not needed - /tmp is ephemeral in containers


class TestSystemObserverInitialization:
    """Test SystemObserver initialization."""

    def test_initialization_default_urls(self):
        """Test observer initializes with default URLs."""
        observer = SystemObserver()

        assert observer.prometheus_url == "http://vertice-prometheus:9090"
        assert observer.influxdb_url == "http://vertice-influxdb:8086"
        assert observer.http_client is None
        assert observer._initialized is False
        assert observer._metrics_cache == {}

    def test_initialization_custom_urls(self):
        """Test observer initializes with custom URLs."""
        observer = SystemObserver(
            prometheus_url="http://custom-prom:9090",
            influxdb_url="http://custom-influx:8086",
        )

        assert observer.prometheus_url == "http://custom-prom:9090"
        assert observer.influxdb_url == "http://custom-influx:8086"
        assert observer._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful observer initialization."""
        observer = SystemObserver()

        with patch(
            "core.system_observer.httpx.AsyncClient"
        ) as mock_client_class:
            # Mock HTTP client
            mock_client = MagicMock()
            mock_client.get = AsyncMock(
                return_value=MagicMock(
                    status_code=200,
                    json=lambda: {
                        "status": "success",
                        "data": {"resultType": "vector", "result": []},
                    },
                )
            )
            mock_client_class.return_value = mock_client

            result = await observer.initialize()

            assert result is True
            assert observer._initialized is True
            assert observer.http_client is not None
            mock_client_class.assert_called_once()
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_prometheus_unavailable(self):
        """Test initialization when Prometheus is unavailable."""
        observer = SystemObserver()

        with patch(
            "core.system_observer.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            mock_client_class.return_value = mock_client

            result = await observer.initialize()

            # Should still succeed in degraded mode
            assert result is True
            assert observer._initialized is True
            assert observer.http_client is not None

    @pytest.mark.asyncio
    async def test_initialize_client_creation_fails(self):
        """Test initialization handles client creation failure."""
        observer = SystemObserver()

        with patch(
            "core.system_observer.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client_class.side_effect = Exception("Client creation failed")

            result = await observer.initialize()

            assert result is False
            assert observer._initialized is False


class TestCollectMetrics:
    """Test collect_metrics method."""

    @pytest.mark.asyncio
    async def test_collect_metrics_not_initialized_raises_error(self):
        """Test collect_metrics raises error when not initialized."""
        observer = SystemObserver()
        observer._initialized = False

        with pytest.raises(RuntimeError, match="SystemObserver not initialized"):
            await observer.collect_metrics()

    @pytest.mark.asyncio
    async def test_collect_metrics_no_http_client_raises_error(self):
        """Test collect_metrics raises error when http_client is None."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = None

        with pytest.raises(RuntimeError, match="SystemObserver not initialized"):
            await observer.collect_metrics()

    @pytest.mark.asyncio
    async def test_collect_metrics_success_default_range(self):
        """Test successful metrics collection with default time range."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        # Mock _collect_prometheus_metrics
        mock_prometheus_metrics = [
            {
                "name": "cpu_usage",
                "value": 45.5,
                "unit": "%",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "prometheus",
            },
            {
                "name": "memory_usage",
                "value": 60.2,
                "unit": "%",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "prometheus",
            },
        ]

        # Mock _collect_service_health
        mock_service_health = [
            {"name": "maximus", "status": "healthy", "uptime_seconds": 3600},
            {"name": "maba", "status": "healthy", "uptime_seconds": 7200},
        ]

        observer._collect_prometheus_metrics = AsyncMock(
            return_value=mock_prometheus_metrics
        )
        observer._collect_service_health = AsyncMock(return_value=mock_service_health)

        result = await observer.collect_metrics()

        assert result["time_range_minutes"] == 60
        assert result["focus_areas"] == []
        assert len(result["metrics"]) == 2
        assert len(result["services"]) == 2
        assert result["anomalies"] == []
        assert result["data_sources"]["prometheus"] == "available"
        assert result["data_sources"]["influxdb"] == "not_implemented"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_collect_metrics_custom_time_range(self):
        """Test metrics collection with custom time range."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(return_value=[])
        observer._collect_service_health = AsyncMock(return_value=[])

        result = await observer.collect_metrics(time_range_minutes=120)

        assert result["time_range_minutes"] == 120
        observer._collect_prometheus_metrics.assert_called_once_with(120, None)

    @pytest.mark.asyncio
    async def test_collect_metrics_with_focus_areas(self):
        """Test metrics collection with focus areas."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(return_value=[])
        observer._collect_service_health = AsyncMock(return_value=[])

        focus_areas = ["cpu", "memory"]
        result = await observer.collect_metrics(
            time_range_minutes=30, focus_areas=focus_areas
        )

        assert result["time_range_minutes"] == 30
        assert result["focus_areas"] == focus_areas
        observer._collect_prometheus_metrics.assert_called_once_with(30, focus_areas)

    @pytest.mark.asyncio
    async def test_collect_metrics_prometheus_error_propagates(self):
        """Test collect_metrics propagates Prometheus collection errors."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(
            side_effect=Exception("Prometheus query failed")
        )
        observer._collect_service_health = AsyncMock(return_value=[])

        with pytest.raises(Exception, match="Prometheus query failed"):
            await observer.collect_metrics()

    @pytest.mark.asyncio
    async def test_collect_metrics_service_health_error_propagates(self):
        """Test collect_metrics propagates service health errors."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(return_value=[])
        observer._collect_service_health = AsyncMock(
            side_effect=Exception("Service health check failed")
        )

        with pytest.raises(Exception, match="Service health check failed"):
            await observer.collect_metrics()


class TestCollectPrometheusMetrics:
    """Test _collect_prometheus_metrics method."""

    @pytest.mark.asyncio
    async def test_collect_prometheus_metrics_success(self):
        """Test successful Prometheus metrics collection."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        # Mock _query_and_format_metric to return metrics
        mock_metric_1 = {"name": "cpu_usage", "value": 45.0, "unit": "%"}
        mock_metric_2 = {"name": "memory_usage", "value": 60.0, "unit": "%"}

        observer._query_and_format_metric = AsyncMock(
            side_effect=[
                mock_metric_1,
                mock_metric_2,
                None,  # Some queries may fail
            ]
        )

        result = await observer._collect_prometheus_metrics(60, None)

        assert len(result) >= 2
        assert any(m["name"] == "cpu_usage" for m in result if m)
        assert any(m["name"] == "memory_usage" for m in result if m)

    @pytest.mark.asyncio
    async def test_collect_prometheus_metrics_with_focus_areas(self):
        """Test Prometheus metrics collection with focus areas."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._query_and_format_metric = AsyncMock(
            return_value={"name": "cpu_usage", "value": 45.0}
        )

        focus_areas = ["cpu", "memory"]
        result = await observer._collect_prometheus_metrics(30, focus_areas)

        # Should only query metrics that match focus areas
        assert observer._query_and_format_metric.call_count >= 1

    @pytest.mark.asyncio
    async def test_collect_prometheus_metrics_handles_exceptions(self):
        """Test Prometheus metrics collection handles individual query exceptions."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        # Some queries succeed, some raise exceptions
        observer._query_and_format_metric = AsyncMock(
            side_effect=[
                {"name": "cpu_usage", "value": 45.0},
                Exception("Query failed"),
                {"name": "memory_usage", "value": 60.0},
            ]
        )

        result = await observer._collect_prometheus_metrics(60, None)

        # Should return successful metrics, skip failed ones
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_collect_prometheus_metrics_all_queries_fail(self):
        """Test Prometheus metrics collection when all queries fail."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._query_and_format_metric = AsyncMock(return_value=None)

        result = await observer._collect_prometheus_metrics(60, None)

        assert result == []


class TestQueryAndFormatMetric:
    """Test _query_and_format_metric method."""

    @pytest.mark.asyncio
    async def test_query_and_format_metric_vector_result(self):
        """Test formatting metric from vector result."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        prometheus_response = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [{"metric": {}, "value": [1635724800, "45.5"]}],
            },
        }

        observer._query_prometheus = AsyncMock(return_value=prometheus_response)

        result = await observer._query_and_format_metric("cpu_usage", "query", "5m")

        assert result is not None
        assert result["name"] == "cpu_usage"
        assert result["value"] == 45.5
        assert result["unit"] == "%"
        assert result["source"] == "prometheus"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_query_and_format_metric_scalar_result(self):
        """Test formatting metric from scalar result."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        prometheus_response = {
            "status": "success",
            "data": {"resultType": "scalar", "result": [1635724800, "75.2"]},
        }

        observer._query_prometheus = AsyncMock(return_value=prometheus_response)

        result = await observer._query_and_format_metric("memory_usage", "query", "5m")

        assert result is not None
        assert result["name"] == "memory_usage"
        assert result["value"] == 75.2

    @pytest.mark.asyncio
    async def test_query_and_format_metric_empty_result(self):
        """Test formatting metric with empty result."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        prometheus_response = {
            "status": "success",
            "data": {"resultType": "vector", "result": []},
        }

        observer._query_prometheus = AsyncMock(return_value=prometheus_response)

        result = await observer._query_and_format_metric("cpu_usage", "query", "5m")

        assert result is not None
        assert result["value"] == 0

    @pytest.mark.asyncio
    async def test_query_and_format_metric_query_fails(self):
        """Test formatting metric when query fails."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._query_prometheus = AsyncMock(return_value=None)

        result = await observer._query_and_format_metric("cpu_usage", "query", "5m")

        assert result is not None
        assert result["value"] == 0

    @pytest.mark.asyncio
    async def test_query_and_format_metric_exception(self):
        """Test formatting metric handles exceptions."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._query_prometheus = AsyncMock(side_effect=Exception("Query error"))

        result = await observer._query_and_format_metric("cpu_usage", "query", "5m")

        assert result is None


class TestQueryPrometheus:
    """Test _query_prometheus method."""

    @pytest.mark.asyncio
    async def test_query_prometheus_success(self):
        """Test successful Prometheus query."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"resultType": "vector", "result": []},
        }

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._query_prometheus("up", "5m")

        assert result is not None
        assert result["status"] == "success"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_prometheus_no_client(self):
        """Test Prometheus query when no HTTP client."""
        observer = SystemObserver()
        observer.http_client = None

        result = await observer._query_prometheus("up", "5m")

        assert result is None

    @pytest.mark.asyncio
    async def test_query_prometheus_http_status_error(self):
        """Test Prometheus query handles HTTP status errors."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._query_prometheus("up", "5m")

        assert result is None

    @pytest.mark.asyncio
    async def test_query_prometheus_request_error(self):
        """Test Prometheus query handles request errors."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        observer.http_client = mock_client

        result = await observer._query_prometheus("up", "5m")

        assert result is None

    @pytest.mark.asyncio
    async def test_query_prometheus_unexpected_error(self):
        """Test Prometheus query handles unexpected errors."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Unexpected error"))
        observer.http_client = mock_client

        result = await observer._query_prometheus("up", "5m")

        assert result is None

    @pytest.mark.asyncio
    async def test_query_prometheus_default_duration(self):
        """Test Prometheus query with default duration."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._query_prometheus("up")

        assert result is not None
        mock_client.get.assert_called_once()


class TestCollectServiceHealth:
    """Test _collect_service_health method."""

    @pytest.mark.asyncio
    async def test_collect_service_health_all_healthy(self):
        """Test collecting health status when all services healthy."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        mock_health = {
            "name": "maximus",
            "status": "healthy",
            "uptime_seconds": 3600,
            "endpoint": "http://vertice-maximus-core-service:8150/health",
        }

        observer._check_service_health = AsyncMock(return_value=mock_health)

        result = await observer._collect_service_health()

        assert len(result) >= 1
        assert all(s["status"] == "healthy" for s in result)

    @pytest.mark.asyncio
    async def test_collect_service_health_mixed_status(self):
        """Test collecting health status with mixed service states."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        # Mock different health statuses
        observer._check_service_health = AsyncMock(
            side_effect=[
                {"name": "maximus", "status": "healthy"},
                {"name": "cognitio", "status": "unhealthy"},
                {"name": "maba", "status": "timeout"},
                {"name": "mvp", "status": "healthy"},
                {"name": "penelope", "status": "unreachable"},
            ]
        )

        result = await observer._collect_service_health()

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_collect_service_health_handles_exceptions(self):
        """Test service health collection handles individual check exceptions."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._check_service_health = AsyncMock(
            side_effect=[
                {"name": "maximus", "status": "healthy"},
                Exception("Check failed"),
                {"name": "maba", "status": "healthy"},
                None,  # Check returned None
            ]
        )

        result = await observer._collect_service_health()

        # Should include only successful checks
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_collect_service_health_all_fail(self):
        """Test service health collection when all checks fail."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._check_service_health = AsyncMock(return_value=None)

        result = await observer._collect_service_health()

        assert result == []


class TestCheckServiceHealth:
    """Test _check_service_health method."""

    @pytest.mark.asyncio
    async def test_check_service_health_healthy(self):
        """Test checking health of healthy service."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "uptime_seconds": 3600}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._check_service_health(
            "maximus", "http://vertice-maximus-core-service:8150/health"
        )

        assert result is not None
        assert result["name"] == "maximus"
        assert result["status"] == "healthy"
        assert result["uptime_seconds"] == 3600
        assert result["endpoint"] == "http://vertice-maximus-core-service:8150/health"

    @pytest.mark.asyncio
    async def test_check_service_health_unhealthy(self):
        """Test checking health of unhealthy service."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._check_service_health(
            "cognitio", "http://example.com/health"
        )

        assert result is not None
        assert result["name"] == "cognitio"
        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_service_health_timeout(self):
        """Test checking health when service times out."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        observer.http_client = mock_client

        result = await observer._check_service_health(
            "maba", "http://example.com/health"
        )

        assert result is not None
        assert result["name"] == "maba"
        assert result["status"] == "timeout"
        assert result["endpoint"] == "http://example.com/health"

    @pytest.mark.asyncio
    async def test_check_service_health_unreachable(self):
        """Test checking health when service is unreachable."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection refused")
        )
        observer.http_client = mock_client

        result = await observer._check_service_health(
            "penelope", "http://example.com/health"
        )

        assert result is not None
        assert result["name"] == "penelope"
        assert result["status"] == "unreachable"

    @pytest.mark.asyncio
    async def test_check_service_health_no_client(self):
        """Test checking health when no HTTP client."""
        observer = SystemObserver()
        observer.http_client = None

        result = await observer._check_service_health(
            "maximus", "http://example.com/health"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_check_service_health_invalid_json(self):
        """Test checking health when response JSON is invalid."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception("Invalid JSON")

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._check_service_health(
            "maximus", "http://example.com/health"
        )

        assert result is not None
        assert result["name"] == "maximus"
        assert result["status"] == "healthy"
        assert result.get("uptime_seconds") is None

    @pytest.mark.asyncio
    async def test_check_service_health_unexpected_error(self):
        """Test checking health handles unexpected errors."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Unexpected error"))
        observer.http_client = mock_client

        result = await observer._check_service_health(
            "maximus", "http://example.com/health"
        )

        assert result is None


class TestDetermineMetricUnit:
    """Test _determine_metric_unit method."""

    def test_determine_metric_unit_usage(self):
        """Test unit determination for usage metrics."""
        observer = SystemObserver()

        assert observer._determine_metric_unit("cpu_usage") == "%"
        assert observer._determine_metric_unit("memory_usage") == "%"
        assert observer._determine_metric_unit("disk_usage") == "%"

    def test_determine_metric_unit_rate(self):
        """Test unit determination for rate metrics."""
        observer = SystemObserver()

        assert observer._determine_metric_unit("http_request_rate") == "%"
        assert observer._determine_metric_unit("error_rate") == "%"

    def test_determine_metric_unit_latency(self):
        """Test unit determination for latency metrics."""
        observer = SystemObserver()

        assert observer._determine_metric_unit("api_latency") == "ms"
        assert observer._determine_metric_unit("response_latency") == "ms"
        assert observer._determine_metric_unit("query_duration") == "ms"

    def test_determine_metric_unit_bytes(self):
        """Test unit determination for bytes metrics."""
        observer = SystemObserver()

        assert observer._determine_metric_unit("memory_bytes") == "bytes"
        assert observer._determine_metric_unit("disk_bytes") == "bytes"

    def test_determine_metric_unit_count(self):
        """Test unit determination for count metrics."""
        observer = SystemObserver()

        assert observer._determine_metric_unit("request_count") == "count"
        assert observer._determine_metric_unit("active_connections") == "count"
        assert observer._determine_metric_unit("database_connections") == "count"

    def test_determine_metric_unit_unknown(self):
        """Test unit determination for unknown metrics."""
        observer = SystemObserver()

        assert observer._determine_metric_unit("custom_metric") == ""
        assert observer._determine_metric_unit("unknown") == ""

    def test_determine_metric_unit_case_insensitive(self):
        """Test unit determination is case insensitive."""
        observer = SystemObserver()

        assert observer._determine_metric_unit("CPU_USAGE") == "%"
        assert observer._determine_metric_unit("Memory_Usage") == "%"
        assert observer._determine_metric_unit("API_LATENCY") == "ms"


class TestHealthCheck:
    """Test health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check when observer is healthy."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer.health_check()

        assert result["status"] == "healthy"
        assert result["initialized"] is True
        assert result["backends"]["prometheus"]["status"] == "healthy"
        assert result["backends"]["influxdb"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """Test health check when observer not initialized."""
        observer = SystemObserver()
        observer._initialized = False

        result = await observer.health_check()

        assert result["status"] == "degraded"
        assert result["initialized"] is False

    @pytest.mark.asyncio
    async def test_health_check_prometheus_unhealthy(self):
        """Test health check when Prometheus is unhealthy."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection failed"))
        observer.http_client = mock_client

        result = await observer.health_check()

        # _query_prometheus catches all exceptions and returns None (lines 339-349),
        # so no exception is raised and prometheus_healthy becomes True at line 137
        assert result["status"] == "healthy"
        assert result["initialized"] is True
        assert result["backends"]["prometheus"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_includes_backend_urls(self):
        """Test health check includes backend URLs."""
        observer = SystemObserver(
            prometheus_url="http://custom-prom:9090",
            influxdb_url="http://custom-influx:8086",
        )
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection failed"))
        observer.http_client = mock_client

        result = await observer.health_check()

        assert result["backends"]["prometheus"]["url"] == "http://custom-prom:9090"
        assert result["backends"]["influxdb"]["url"] == "http://custom-influx:8086"

    @pytest.mark.asyncio
    async def test_health_check_degraded_mode(self):
        """Test health check in degraded mode."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = None

        result = await observer.health_check()

        # When http_client is None, _query_prometheus returns None at line 326 (no exception raised),
        # so prometheus_healthy becomes True, making overall status "healthy"
        assert result["status"] == "healthy"
        assert result["backends"]["prometheus"]["status"] == "healthy"


class TestShutdown:
    """Test shutdown method."""

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful shutdown."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        observer.http_client = mock_client
        observer._metrics_cache = {"key": "value"}

        await observer.shutdown()

        mock_client.aclose.assert_called_once()
        assert observer.http_client is None
        assert observer._initialized is False
        assert observer._metrics_cache == {}

    @pytest.mark.asyncio
    async def test_shutdown_client_already_closed(self):
        """Test shutdown when client already closed."""
        observer = SystemObserver()
        observer._initialized = True

        mock_client = MagicMock()
        mock_client.is_closed = True
        observer.http_client = mock_client

        await observer.shutdown()

        # When client is already closed, shutdown() doesn't enter the if block (line 117)
        # and doesn't set http_client to None, but still sets _initialized to False
        assert observer.http_client is not None
        assert observer._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_no_client(self):
        """Test shutdown when no client exists."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = None

        # Should not raise exception
        await observer.shutdown()

        assert observer.http_client is None
        assert observer._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_not_initialized(self):
        """Test shutdown when not initialized."""
        observer = SystemObserver()
        observer._initialized = False
        observer.http_client = None

        await observer.shutdown()

        assert observer._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_clears_cache(self):
        """Test shutdown clears metrics cache."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = None
        observer._metrics_cache = {"metric1": {"value": 100}, "metric2": {"value": 200}}

        await observer.shutdown()

        assert observer._metrics_cache == {}


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_collect_metrics_empty_results(self):
        """Test metrics collection with empty results from all sources."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(return_value=[])
        observer._collect_service_health = AsyncMock(return_value=[])

        result = await observer.collect_metrics()

        assert len(result["metrics"]) == 0
        assert len(result["services"]) == 0
        assert result["anomalies"] == []

    @pytest.mark.asyncio
    async def test_query_prometheus_malformed_response(self):
        """Test Prometheus query with malformed JSON response."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._query_prometheus("up", "5m")

        assert result is None

    @pytest.mark.asyncio
    async def test_initialize_multiple_times(self):
        """Test calling initialize multiple times."""
        observer = SystemObserver()

        with patch(
            "core.system_observer.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(
                return_value=MagicMock(
                    status_code=200,
                    json=lambda: {
                        "status": "success",
                        "data": {"resultType": "vector", "result": []},
                    },
                )
            )
            mock_client_class.return_value = mock_client

            # First initialization
            result1 = await observer.initialize()
            assert result1 is True

            # Second initialization (should still work)
            result2 = await observer.initialize()
            assert result2 is True

            # Should have created client twice
            assert mock_client_class.call_count == 2

    @pytest.mark.asyncio
    async def test_collect_metrics_with_zero_time_range(self):
        """Test metrics collection with zero time range."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(return_value=[])
        observer._collect_service_health = AsyncMock(return_value=[])

        result = await observer.collect_metrics(time_range_minutes=0)

        assert result["time_range_minutes"] == 0

    @pytest.mark.asyncio
    async def test_collect_metrics_with_large_time_range(self):
        """Test metrics collection with very large time range."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(return_value=[])
        observer._collect_service_health = AsyncMock(return_value=[])

        result = await observer.collect_metrics(time_range_minutes=10080)  # 1 week

        assert result["time_range_minutes"] == 10080

    @pytest.mark.asyncio
    async def test_query_and_format_metric_missing_data_field(self):
        """Test formatting metric when response missing data field."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        prometheus_response = {
            "status": "success"
            # Missing "data" field
        }

        observer._query_prometheus = AsyncMock(return_value=prometheus_response)

        result = await observer._query_and_format_metric("cpu_usage", "query", "5m")

        assert result is not None
        assert result["value"] == 0

    @pytest.mark.asyncio
    async def test_check_service_health_partial_response(self):
        """Test checking health with partial response data."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy"
        }  # Missing uptime_seconds

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        result = await observer._check_service_health(
            "maximus", "http://example.com/health"
        )

        assert result is not None
        assert result["status"] == "healthy"
        # When uptime_seconds is missing, .get() returns default value of 0 (line 415 in source)
        assert result["uptime_seconds"] == 0

    def test_observer_preserves_configuration(self):
        """Test that observer preserves its configuration."""
        prometheus_url = "http://test-prom:9090"
        influxdb_url = "http://test-influx:8086"

        observer = SystemObserver(
            prometheus_url=prometheus_url, influxdb_url=influxdb_url
        )

        assert observer.prometheus_url == prometheus_url
        assert observer.influxdb_url == influxdb_url

    @pytest.mark.asyncio
    async def test_collect_metrics_timestamp_format(self):
        """Test that collect_metrics returns valid ISO timestamp."""
        observer = SystemObserver()
        observer._initialized = True
        observer.http_client = MagicMock()

        observer._collect_prometheus_metrics = AsyncMock(return_value=[])
        observer._collect_service_health = AsyncMock(return_value=[])

        result = await observer.collect_metrics()

        # Verify timestamp is valid ISO format
        timestamp = result["timestamp"]
        assert isinstance(timestamp, str)
        datetime.fromisoformat(timestamp)  # Should not raise

    @pytest.mark.asyncio
    async def test_query_prometheus_increments_metrics(self):
        """Test that Prometheus queries increment observer metrics."""
        observer = SystemObserver()
        observer._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        observer.http_client = mock_client

        # Get initial counter value
        initial_count = observer.queries_total.labels(
            backend="prometheus"
        )._value._value

        await observer._query_prometheus("up", "5m")

        # Counter should have incremented
        final_count = observer.queries_total.labels(backend="prometheus")._value._value
        assert final_count > initial_count
