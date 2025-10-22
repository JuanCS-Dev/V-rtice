"""
Shared pytest fixtures for MAXIMUS AI 3.0 tests

REGRA DE OURO: Zero mocks, production-ready fixtures
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Updated: 2025-10-20 - Added Testcontainers support
"""

import sys
import time
import os
from pathlib import Path
from typing import Generator

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Testcontainers imports (optional dependency)
try:
    from testcontainers.kafka import KafkaContainer
    from testcontainers.redis import RedisContainer
    from testcontainers.postgres import PostgresContainer
    from testcontainers.core.container import DockerContainer
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.admin import KafkaAdminClient, NewTopic
    import redis as redis_client
    import psycopg2

    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False

try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@pytest.fixture(scope="session")
def torch_available():
    """Check if PyTorch is available."""
    return TORCH_AVAILABLE


@pytest.fixture
def simple_torch_model():
    """Create simple PyTorch model for testing."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    class SimpleModel(nn.Module):
        def __init__(self, input_size=128, hidden_size=64, output_size=32):
            super().__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(hidden_size, output_size)

        def forward(self, x):
            x = self.fc1(x)
            x = self.relu(x)
            x = self.fc2(x)
            return x

    return SimpleModel()


@pytest.fixture
def sample_threat_data():
    """Sample cybersecurity threat data for testing."""
    return {
        "threat_id": "T001",
        "timestamp": "2025-10-06T12:00:00Z",
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.50",
        "port": 443,
        "protocol": "TCP",
        "payload_size": 1024,
        "threat_score": 0.85,
        "threat_type": "malware",
        "indicators": {"suspicious_patterns": 3, "known_malware_signatures": 1, "anomaly_score": 0.72},
    }


@pytest.fixture
def sample_decision_request():
    """Sample decision request for governance/HITL testing."""
    return {
        "decision_id": "DEC001",
        "action": "block_ip",
        "target": "192.168.1.100",
        "risk_level": "HIGH",
        "confidence": 0.89,
        "context": {"threat_score": 0.85, "false_positive_rate": 0.05},
        "ethical_constraints": {"privacy_concern": False, "transparency_required": True},
    }


@pytest.fixture
def sample_model_explanation():
    """Sample XAI explanation for testing."""
    return {
        "prediction": "malicious",
        "confidence": 0.92,
        "feature_importance": {"payload_size": 0.35, "port": 0.28, "suspicious_patterns": 0.22, "anomaly_score": 0.15},
        "counterfactuals": [
            {"feature": "payload_size", "original_value": 1024, "suggested_value": 512, "new_prediction": "benign"}
        ],
    }


@pytest.fixture
def temp_model_path(tmp_path):
    """Temporary path for saving models in tests."""
    return tmp_path / "models"


@pytest.fixture
def temp_data_path(tmp_path):
    """Temporary path for test data."""
    return tmp_path / "data"


# ========== TESTCONTAINERS FIXTURES ==========
# Real service fixtures for integration/e2e tests
# DOUTRINA VÉRTICE: No mocks, production-ready

@pytest.fixture(scope="session")
def testcontainers_available():
    """Check if Testcontainers is available."""
    return TESTCONTAINERS_AVAILABLE


@pytest.fixture(scope="session")
def kafka_container() -> Generator[KafkaContainer, None, None]:
    """
    Kafka container for consciousness messaging tests.
    Scope: session (shared across all tests for performance)

    Returns:
        KafkaContainer with bootstrap server accessible
    """
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("Testcontainers not available")

    container = KafkaContainer()
    container.start()

    # Wait for Kafka to be ready
    bootstrap_server = container.get_bootstrap_server()
    max_retries = 30
    for i in range(max_retries):
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_server,
                client_id='test_admin',
                request_timeout_ms=5000
            )
            admin_client.close()
            break
        except Exception as e:
            if i == max_retries - 1:
                container.stop()
                pytest.fail(f"Kafka container failed to start: {e}")
            time.sleep(1)

    yield container
    container.stop()


@pytest.fixture
def kafka_producer(kafka_container):
    """
    Kafka producer connected to test container.
    Scope: function (new producer per test)
    """
    bootstrap_server = kafka_container.get_bootstrap_server()
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_server,
        value_serializer=lambda v: str(v).encode('utf-8')
    )

    yield producer
    producer.close()


@pytest.fixture
def kafka_admin(kafka_container):
    """Kafka admin client for topic management."""
    bootstrap_server = kafka_container.get_bootstrap_server()
    admin_client = KafkaAdminClient(
        bootstrap_servers=bootstrap_server,
        client_id='test_admin'
    )

    yield admin_client
    admin_client.close()


@pytest.fixture
def consciousness_topics(kafka_admin):
    """
    Create consciousness-related topics for FASE 3 tests.
    Topics: global_workspace, visual_cortex, thalamus, prefrontal, neuromodulation
    """
    topics = [
        NewTopic(name="consciousness.global_workspace", num_partitions=3, replication_factor=1),
        NewTopic(name="consciousness.visual_cortex", num_partitions=1, replication_factor=1),
        NewTopic(name="consciousness.thalamus", num_partitions=1, replication_factor=1),
        NewTopic(name="consciousness.prefrontal", num_partitions=1, replication_factor=1),
        NewTopic(name="consciousness.neuromodulation", num_partitions=1, replication_factor=1),
    ]

    kafka_admin.create_topics(new_topics=topics, validate_only=False)
    time.sleep(2)  # Wait for topics to be created

    return [topic.name for topic in topics]


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    """
    Redis container for consciousness hot-path state.
    Scope: session (shared for performance)
    """
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("Testcontainers not available")

    container = RedisContainer()
    container.start()

    # Health check
    max_retries = 10
    for i in range(max_retries):
        try:
            client = redis_client.Redis(
                host=container.get_container_host_ip(),
                port=int(container.get_exposed_port(6379))
            )
            client.ping()
            client.close()
            break
        except Exception as e:
            if i == max_retries - 1:
                container.stop()
                pytest.fail(f"Redis container failed to start: {e}")
            time.sleep(1)

    yield container
    container.stop()


@pytest.fixture
def redis_client_fixture(redis_container):
    """Redis client connected to test container."""
    client = redis_client.Redis(
        host=redis_container.get_container_host_ip(),
        port=int(redis_container.get_exposed_port(6379)),
        decode_responses=True
    )

    yield client

    # Cleanup
    client.flushdb()
    client.close()


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """
    PostgreSQL container for governance, audit trails, precedents.
    Scope: session
    """
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("Testcontainers not available")

    container = PostgresContainer(
        image="postgres:15-alpine",
        user="maximus_test",
        password="test_password",
        dbname="maximus_test"
    )
    container.start()

    # Health check
    max_retries = 10
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(container.get_connection_url())
            conn.close()
            break
        except Exception as e:
            if i == max_retries - 1:
                container.stop()
                pytest.fail(f"Postgres container failed to start: {e}")
            time.sleep(1)

    yield container
    container.stop()


@pytest.fixture
def postgres_connection(postgres_container):
    """PostgreSQL connection for tests."""
    conn = psycopg2.connect(postgres_container.get_connection_url())
    conn.autocommit = True

    yield conn

    # Cleanup
    cursor = conn.cursor()
    cursor.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    cursor.close()
    conn.close()


@pytest.fixture
def minio_container() -> Generator[DockerContainer, None, None]:
    """
    MinIO container for ML model storage (S3-compatible).
    Scope: function (isolated per test)
    """
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("Testcontainers not available")

    container = DockerContainer("minio/minio:latest")
    container.with_exposed_ports(9000)
    container.with_env("MINIO_ROOT_USER", "minioadmin")
    container.with_env("MINIO_ROOT_PASSWORD", "minioadmin")
    container.with_command("server /data")
    container.start()

    # Wait for MinIO to be ready
    time.sleep(3)

    yield container
    container.stop()


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (medium speed, component interaction)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow, full workflow)")
    config.addinivalue_line("markers", "slow: Slow tests (skip with -m 'not slow')")
    config.addinivalue_line("markers", "requires_torch: Tests requiring PyTorch")
    config.addinivalue_line("markers", "requires_gpu: Tests requiring GPU")
