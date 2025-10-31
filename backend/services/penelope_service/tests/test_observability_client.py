"""Tests for Observability Client.

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime

import pytest
from core.observability_client import ObservabilityClient


class TestObservabilityClient:
    """Test suite for ObservabilityClient."""

    def test_initialization_with_defaults(self):
        """Test client initialization with default URLs."""
        client = ObservabilityClient()

        assert client.prometheus_url == "http://prometheus:9090"
        assert client.loki_url == "http://loki:3100"

    def test_initialization_with_custom_urls(self):
        """Test client initialization with custom URLs."""
        client = ObservabilityClient(
            prometheus_url="http://custom-prometheus:9090",
            loki_url="http://custom-loki:3100",
        )

        assert client.prometheus_url == "http://custom-prometheus:9090"
        assert client.loki_url == "http://custom-loki:3100"

    @pytest.mark.asyncio
    async def test_query_similar_anomalies(self):
        """Test querying similar anomalies returns empty list in FASE 1."""
        client = ObservabilityClient()

        anomalies = await client.query_similar_anomalies(
            anomaly_type="high_latency",
            service="vertice-api",
            since=datetime(2025, 10, 1),
        )

        assert isinstance(anomalies, list)
        assert len(anomalies) == 0

    @pytest.mark.asyncio
    async def test_get_service_metrics(self):
        """Test getting service metrics returns default values in FASE 1."""
        client = ObservabilityClient()

        metrics = await client.get_service_metrics(
            service="vertice-api",
            metric_names=["cpu_usage", "memory_usage", "request_rate"],
        )

        assert isinstance(metrics, dict)
        assert len(metrics) == 3
        assert metrics["cpu_usage"] == 0.0
        assert metrics["memory_usage"] == 0.0
        assert metrics["request_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_recent_logs(self):
        """Test getting recent logs returns empty list in FASE 1."""
        client = ObservabilityClient()

        logs = await client.get_recent_logs(
            service="vertice-api", level="ERROR", limit=100
        )

        assert isinstance(logs, list)
        assert len(logs) == 0

    @pytest.mark.asyncio
    async def test_get_recent_logs_with_warn_level(self):
        """Test getting WARN level logs."""
        client = ObservabilityClient()

        logs = await client.get_recent_logs(
            service="vertice-api", level="WARN", limit=50
        )

        assert isinstance(logs, list)
        assert len(logs) == 0
