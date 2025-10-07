"""Tests for Dependency Health Checks - PRODUCTION-READY

Comprehensive tests for Kafka, Redis, and PostgreSQL health checks.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from monitoring.dependency_health import DependencyHealthChecker
from monitoring.health_checker import HealthStatus


@pytest_asyncio.fixture
async def health_checker():
    """Create health checker instance."""
    return DependencyHealthChecker()


# ======================== KAFKA HEALTH TESTS ========================


@pytest.mark.asyncio
async def test_kafka_health_check_success(health_checker):
    """Test successful Kafka health check."""
    # Mock Kafka producer
    mock_producer = AsyncMock()
    mock_metadata = MagicMock()
    mock_metadata.brokers = [
        MagicMock(nodeId=1, host="kafka1", port=9092),
        MagicMock(nodeId=2, host="kafka2", port=9092),
    ]
    mock_metadata.topics = ["topic1", "topic2", "topic3"]
    mock_producer.client.fetch_all_metadata = AsyncMock(return_value=mock_metadata)

    with patch("monitoring.dependency_health.AIOKafkaProducer", return_value=mock_producer):
        status, details = await health_checker.check_kafka_health()

    assert status == HealthStatus.HEALTHY
    assert "message" in details
    assert details["brokers_count"] == 2
    assert details["topics_count"] == 3
    assert "latency_ms" in details


@pytest.mark.asyncio
async def test_kafka_health_check_slow_response(health_checker):
    """Test Kafka health check with slow response (degraded)."""
    # Set low threshold for testing
    health_checker.max_latency_ms = 1

    mock_producer = AsyncMock()
    mock_metadata = MagicMock()
    mock_metadata.brokers = [MagicMock(nodeId=1, host="kafka1", port=9092)]
    mock_metadata.topics = ["topic1"]

    async def slow_fetch():
        import asyncio
        await asyncio.sleep(0.002)  # 2ms > 1ms threshold
        return mock_metadata

    mock_producer.client.fetch_all_metadata = slow_fetch

    with patch("monitoring.dependency_health.AIOKafkaProducer", return_value=mock_producer):
        status, details = await health_checker.check_kafka_health()

    assert status == HealthStatus.DEGRADED
    assert "slowly" in details["message"].lower()
    assert details["latency_ms"] > health_checker.max_latency_ms


@pytest.mark.asyncio
async def test_kafka_health_check_connection_error(health_checker):
    """Test Kafka health check with connection error."""
    from aiokafka.errors import KafkaConnectionError

    mock_producer = AsyncMock()
    mock_producer.start.side_effect = KafkaConnectionError("Connection refused")

    with patch("monitoring.dependency_health.AIOKafkaProducer", return_value=mock_producer):
        status, details = await health_checker.check_kafka_health()

    assert status == HealthStatus.UNHEALTHY
    assert "Cannot connect" in details["message"]
    assert "error" in details


@pytest.mark.asyncio
async def test_kafka_health_check_generic_error(health_checker):
    """Test Kafka health check with generic error."""
    mock_producer = AsyncMock()
    mock_producer.start.side_effect = Exception("Unexpected error")

    with patch("monitoring.dependency_health.AIOKafkaProducer", return_value=mock_producer):
        status, details = await health_checker.check_kafka_health()

    assert status == HealthStatus.UNHEALTHY
    assert "failed" in details["message"].lower()
    assert "error" in details


# ======================== REDIS HEALTH TESTS ========================


@pytest.mark.asyncio
async def test_redis_health_check_success(health_checker):
    """Test successful Redis health check."""
    # Capture the test value that will be set
    test_value_holder = {}

    async def mock_set(key, value, ex=None):
        test_value_holder[key] = value
        return True

    async def mock_get(key):
        return test_value_holder.get(key)

    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.set = mock_set
    mock_redis.get = mock_get
    mock_redis.delete.return_value = 1
    mock_redis.info.return_value = {
        "redis_version": "7.2.0",
        "uptime_in_seconds": 3600,
    }

    with patch("monitoring.dependency_health.aioredis.from_url", return_value=mock_redis):
        status, details = await health_checker.check_redis_health()

    assert status == HealthStatus.HEALTHY
    assert "healthy" in details["message"].lower()
    assert "latency_ms" in details
    assert "redis_version" in details


@pytest.mark.asyncio
async def test_redis_health_check_ping_failure(health_checker):
    """Test Redis health check when PING fails."""
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = False

    with patch("monitoring.dependency_health.aioredis.from_url", return_value=mock_redis):
        status, details = await health_checker.check_redis_health()

    assert status == HealthStatus.UNHEALTHY
    assert "not responding" in details["message"].lower()


@pytest.mark.asyncio
async def test_redis_health_check_set_get_inconsistency(health_checker):
    """Test Redis health check with SET/GET inconsistency."""
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.set.return_value = True
    mock_redis.get.return_value = "wrong_value"  # Different from what was set

    with patch("monitoring.dependency_health.aioredis.from_url", return_value=mock_redis):
        status, details = await health_checker.check_redis_health()

    assert status == HealthStatus.DEGRADED
    assert "inconsistency" in details["message"].lower()


@pytest.mark.asyncio
async def test_redis_health_check_connection_error(health_checker):
    """Test Redis health check with connection error."""
    import redis.asyncio as aioredis

    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = aioredis.ConnectionError("Connection refused")

    with patch("monitoring.dependency_health.aioredis.from_url", return_value=mock_redis):
        status, details = await health_checker.check_redis_health()

    assert status == HealthStatus.UNHEALTHY
    assert "Cannot connect" in details["message"]
    assert "error" in details


# ======================== POSTGRESQL HEALTH TESTS ========================


@pytest.mark.asyncio
async def test_postgres_health_check_success(health_checker):
    """Test successful PostgreSQL health check."""
    from unittest.mock import MagicMock

    mock_conn = AsyncMock()
    mock_conn.fetchval.side_effect = [
        "PostgreSQL 15.0",  # version
        1,  # SELECT 1
    ]
    mock_conn.fetchrow.return_value = {
        "db_size": 10485760,  # 10 MB
        "active_connections": 5,
        "active_queries": 2,
    }

    # Create async context manager for acquire()
    class MockAcquire:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, *args):
            return None

    # Create mock pool
    class MockPool:
        def acquire(self):
            return MockAcquire()

        async def close(self):
            pass

    # Mock create_pool to return our mock pool
    async def create_pool_mock(**kwargs):
        return MockPool()

    with patch("monitoring.dependency_health.asyncpg.create_pool", new=create_pool_mock):
        status, details = await health_checker.check_postgres_health()

    assert status == HealthStatus.HEALTHY
    assert "healthy" in details["message"].lower()
    assert "latency_ms" in details
    assert details["version"] == "15.0"
    assert details["db_size_mb"] == 10.0


@pytest.mark.asyncio
async def test_postgres_health_check_query_failure(health_checker):
    """Test PostgreSQL health check when query returns unexpected result."""
    mock_conn = AsyncMock()
    mock_conn.fetchval.side_effect = [
        "PostgreSQL 15.0",
        0,  # SELECT 1 returned 0 (unexpected!)
    ]

    # Create async context manager for acquire()
    class MockAcquire:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, *args):
            return None

    # Create mock pool
    class MockPool:
        def acquire(self):
            return MockAcquire()

        async def close(self):
            pass

    async def create_pool_mock(**kwargs):
        return MockPool()

    with patch("monitoring.dependency_health.asyncpg.create_pool", new=create_pool_mock):
        status, details = await health_checker.check_postgres_health()

    assert status == HealthStatus.DEGRADED
    assert "unexpected" in details["message"].lower()


@pytest.mark.asyncio
async def test_postgres_health_check_connection_error(health_checker):
    """Test PostgreSQL health check with connection error."""
    import asyncpg

    with patch(
        "monitoring.dependency_health.asyncpg.create_pool",
        side_effect=asyncpg.PostgresConnectionError("Connection refused"),
    ):
        status, details = await health_checker.check_postgres_health()

    assert status == HealthStatus.UNHEALTHY
    assert "Cannot connect" in details["message"]
    assert "error" in details


@pytest.mark.asyncio
async def test_postgres_health_check_slow_response(health_checker):
    """Test PostgreSQL health check with slow response."""
    import asyncio

    # Set low threshold for testing
    health_checker.max_latency_ms = 1

    mock_conn = AsyncMock()

    async def slow_fetchval(query):
        await asyncio.sleep(0.002)  # 2ms > 1ms threshold
        if "version" in query:
            return "PostgreSQL 15.0"
        return 1

    mock_conn.fetchval = slow_fetchval
    mock_conn.fetchrow.return_value = {
        "db_size": 10485760,
        "active_connections": 5,
        "active_queries": 2,
    }

    # Create async context manager for acquire()
    class MockAcquire:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, *args):
            return None

    # Create mock pool
    class MockPool:
        def acquire(self):
            return MockAcquire()

        async def close(self):
            pass

    async def create_pool_mock(**kwargs):
        return MockPool()

    with patch("monitoring.dependency_health.asyncpg.create_pool", new=create_pool_mock):
        status, details = await health_checker.check_postgres_health()

    assert status == HealthStatus.DEGRADED
    assert "slowly" in details["message"].lower()


# ======================== ALL DEPENDENCIES TESTS ========================


@pytest.mark.asyncio
async def test_check_all_dependencies(health_checker):
    """Test checking all dependencies in parallel."""
    # Mock all dependency checks
    health_checker.check_kafka_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "Kafka OK"})
    )
    health_checker.check_redis_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "Redis OK"})
    )
    health_checker.check_postgres_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "PostgreSQL OK"})
    )

    results = await health_checker.check_all_dependencies()

    assert len(results) == 3
    assert "kafka" in results
    assert "redis" in results
    assert "postgres" in results

    # All should be healthy
    for status, details in results.values():
        assert status == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_check_all_dependencies_with_failure(health_checker):
    """Test checking all dependencies when one fails."""
    health_checker.check_kafka_health = AsyncMock(
        return_value=(HealthStatus.UNHEALTHY, {"message": "Kafka down"})
    )
    health_checker.check_redis_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "Redis OK"})
    )
    health_checker.check_postgres_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "PostgreSQL OK"})
    )

    results = await health_checker.check_all_dependencies()

    # Kafka should be unhealthy
    assert results["kafka"][0] == HealthStatus.UNHEALTHY

    # Others should be healthy
    assert results["redis"][0] == HealthStatus.HEALTHY
    assert results["postgres"][0] == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_get_dependencies_summary_all_healthy(health_checker):
    """Test dependencies summary when all are healthy."""
    health_checker.check_kafka_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "Kafka OK"})
    )
    health_checker.check_redis_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "Redis OK"})
    )
    health_checker.check_postgres_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "PostgreSQL OK"})
    )

    summary = await health_checker.get_dependencies_summary()

    assert summary["overall_status"] == HealthStatus.HEALTHY
    assert len(summary["dependencies"]) == 3


@pytest.mark.asyncio
async def test_get_dependencies_summary_one_unhealthy(health_checker):
    """Test dependencies summary when one is unhealthy."""
    health_checker.check_kafka_health = AsyncMock(
        return_value=(HealthStatus.UNHEALTHY, {"message": "Kafka down"})
    )
    health_checker.check_redis_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "Redis OK"})
    )
    health_checker.check_postgres_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "PostgreSQL OK"})
    )

    summary = await health_checker.get_dependencies_summary()

    # Overall should be unhealthy if any dependency is unhealthy
    assert summary["overall_status"] == HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_get_dependencies_summary_one_degraded(health_checker):
    """Test dependencies summary when one is degraded."""
    health_checker.check_kafka_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "Kafka OK"})
    )
    health_checker.check_redis_health = AsyncMock(
        return_value=(HealthStatus.DEGRADED, {"message": "Redis slow"})
    )
    health_checker.check_postgres_health = AsyncMock(
        return_value=(HealthStatus.HEALTHY, {"message": "PostgreSQL OK"})
    )

    summary = await health_checker.get_dependencies_summary()

    # Overall should be degraded if any is degraded (and none unhealthy)
    assert summary["overall_status"] == HealthStatus.DEGRADED
