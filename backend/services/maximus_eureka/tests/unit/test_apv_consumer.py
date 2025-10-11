"""
Unit Tests - APV Kafka Consumer.

Tests for APVConsumer class covering:
- APV deserialization
- Idempotency (deduplication)
- Error handling
- DLQ behavior
- Statistics tracking

Author: MAXIMUS Team
Date: 2025-01-10
Compliance: Doutrina MAXIMUS | ≥85% coverage | Production-Ready
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest
from pydantic import ValidationError

# Add Oráculo to path for APV import
import sys

sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / "maximus_oraculo"),
)
from models.apv import APV, PriorityLevel, AffectedPackage

from consumers.apv_consumer import APVConsumer, APVConsumerConfig


# ===================== FIXTURES =====================


@pytest.fixture
def valid_apv_dict() -> dict[str, Any]:
    """Valid APV dictionary for testing."""
    return {
        "cve_id": "CVE-2024-99999",
        "aliases": ["GHSA-test-1234"],
        "published": "2024-01-01T00:00:00Z",
        "modified": "2024-01-02T00:00:00Z",
        "summary": "Test vulnerability summary for consumer testing",
        "details": "Detailed description of test vulnerability with sufficient length for validation requirements",
        "source_feed": "OSV.dev",  # Required field
        "priority": "critical",
        "affected_packages": [
            {
                "ecosystem": "PyPI",
                "name": "test-package",
                "affected_versions": [">=1.0.0,<2.0.0"],
                "fixed_versions": ["2.0.0"],
            }
        ],
    }


@pytest.fixture
def consumer_config() -> APVConsumerConfig:
    """Consumer configuration for testing."""
    return APVConsumerConfig(
        kafka_bootstrap_servers="localhost:9092",
        kafka_topic="test.apv",
        kafka_group_id="test-group",
        enable_auto_commit=False,
        redis_cache_url="redis://localhost:6379/0",
    )


@pytest.fixture
def mock_apv_handler() -> AsyncMock:
    """Mock APV handler function."""
    return AsyncMock()


# ===================== DESERIALIZATION TESTS =====================


@pytest.mark.asyncio
async def test_deserialize_valid_apv(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
    valid_apv_dict: dict[str, Any],
) -> None:
    """Test deserialization of valid APV."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    message = json.dumps(valid_apv_dict).encode("utf-8")
    apv = await consumer._deserialize_apv(message)

    assert isinstance(apv, APV)
    assert apv.cve_id == "CVE-2024-99999"
    assert apv.priority == PriorityLevel.CRITICAL
    assert len(apv.affected_packages) == 1


@pytest.mark.asyncio
async def test_deserialize_invalid_json(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test deserialization with invalid JSON."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    message = b"{ invalid json }"

    with pytest.raises(json.JSONDecodeError):
        await consumer._deserialize_apv(message)


@pytest.mark.asyncio
async def test_deserialize_invalid_schema(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test deserialization with invalid APV schema."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    invalid_data = {"cve_id": "CVE-2024-99999"}  # Missing required fields
    message = json.dumps(invalid_data).encode("utf-8")

    with pytest.raises(ValidationError):
        await consumer._deserialize_apv(message)


# ===================== IDEMPOTENCY TESTS =====================


@pytest.mark.asyncio
async def test_deduplication_marks_processed(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test that processed APVs are marked in Redis."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock Redis client
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()
    consumer._redis_client = mock_redis

    await consumer._mark_processed("CVE-2024-99999")

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert "apv:processed:CVE-2024-99999" in call_args[0]
    assert call_args[0][1] == consumer_config.redis_ttl_seconds


@pytest.mark.asyncio
async def test_deduplication_detects_duplicate(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test duplicate detection via Redis."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock Redis client returning existing entry
    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)
    consumer._redis_client = mock_redis

    is_duplicate = await consumer._is_duplicate("CVE-2024-99999")

    assert is_duplicate is True
    mock_redis.exists.assert_called_once()


@pytest.mark.asyncio
async def test_deduplication_allows_new(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test new APV is not detected as duplicate."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock Redis client returning no entry
    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)
    consumer._redis_client = mock_redis

    is_duplicate = await consumer._is_duplicate("CVE-2024-99999")

    assert is_duplicate is False


@pytest.mark.asyncio
async def test_deduplication_redis_failure_allows_processing(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test that Redis failures don't block processing (fail open)."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock Redis client raising exception
    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(side_effect=Exception("Redis down"))
    consumer._redis_client = mock_redis

    is_duplicate = await consumer._is_duplicate("CVE-2024-99999")

    assert is_duplicate is False  # Fail open


# ===================== DLQ TESTS =====================


@pytest.mark.asyncio
async def test_dlq_publish_on_validation_error(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test DLQ publish on validation error."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock Kafka producer
    with patch("aiokafka.AIOKafkaProducer") as MockProducer:
        mock_producer = AsyncMock()
        MockProducer.return_value = mock_producer

        invalid_message = b'{"invalid": "data"}'
        await consumer._publish_to_dlq(
            invalid_message, "Validation failed"
        )

        # Verify producer started, sent to DLQ, stopped
        mock_producer.start.assert_called_once()
        mock_producer.send_and_wait.assert_called_once()
        mock_producer.stop.assert_called_once()

        # Verify DLQ topic
        call_args = mock_producer.send_and_wait.call_args
        assert call_args[0][0] == consumer_config.kafka_dlq_topic


@pytest.mark.asyncio
async def test_dlq_message_contains_metadata(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test DLQ message includes error metadata."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    with patch("aiokafka.AIOKafkaProducer") as MockProducer:
        mock_producer = AsyncMock()
        MockProducer.return_value = mock_producer

        await consumer._publish_to_dlq(
            b'{"test": "data"}', "Test error"
        )

        # Extract DLQ message
        call_args = mock_producer.send_and_wait.call_args
        dlq_message_bytes = call_args[0][1]
        dlq_message = json.loads(dlq_message_bytes.decode("utf-8"))

        # Verify metadata
        assert "original_message" in dlq_message
        assert "error" in dlq_message
        assert "timestamp" in dlq_message
        assert "consumer_group" in dlq_message
        assert dlq_message["error"] == "Test error"


# ===================== ERROR HANDLING TESTS =====================


@pytest.mark.asyncio
async def test_process_message_handles_validation_error(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test processing handles validation errors gracefully."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock message with invalid APV
    mock_message = MagicMock()
    mock_message.value = b'{"cve_id": "CVE-2024-99999"}'  # Missing required fields

    # Mock DLQ
    consumer._publish_to_dlq = AsyncMock()

    await consumer._process_message(mock_message)

    # Verify DLQ called
    consumer._publish_to_dlq.assert_called_once()

    # Verify handler NOT called
    mock_apv_handler.assert_not_called()

    # Verify failed count incremented
    assert consumer._failed_count == 1


@pytest.mark.asyncio
async def test_process_message_handles_handler_exception(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
    valid_apv_dict: dict[str, Any],
) -> None:
    """Test processing handles handler exceptions."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock handler raising exception
    mock_apv_handler.side_effect = Exception("Handler failed")

    # Mock message
    mock_message = MagicMock()
    mock_message.value = json.dumps(valid_apv_dict).encode("utf-8")

    # Mock dependencies
    consumer._is_duplicate = AsyncMock(return_value=False)
    consumer._publish_to_dlq = AsyncMock()
    consumer._mark_processed = AsyncMock()

    await consumer._process_message(mock_message)

    # Verify DLQ called
    consumer._publish_to_dlq.assert_called_once()

    # Verify NOT marked processed
    consumer._mark_processed.assert_not_called()

    # Verify failed count incremented
    assert consumer._failed_count == 1

@pytest.mark.asyncio
async def test_process_message_success_path(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
    valid_apv_dict: dict[str, Any],
) -> None:
    """Test successful message processing path."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock message with valid APV
    mock_message = MagicMock()
    mock_message.value = json.dumps(valid_apv_dict).encode("utf-8")

    # Mock only external dependencies
    consumer._is_duplicate = AsyncMock(return_value=False)
    consumer._mark_processed = AsyncMock()
    consumer._publish_to_dlq = AsyncMock()

    await consumer._process_message(mock_message)

    # Verify handler was called
    assert mock_apv_handler.call_count == 1
    
    # Verify called with APV object
    call_args = mock_apv_handler.call_args
    if call_args and call_args[0]:
        apv = call_args[0][0]
        assert isinstance(apv, APV)
        assert apv.cve_id == "CVE-2024-99999"

    # Verify marked processed
    consumer._mark_processed.assert_called_once_with("CVE-2024-99999")

    # Verify NOT sent to DLQ
    consumer._publish_to_dlq.assert_not_called()

    # Verify counts
    assert consumer._processed_count == 1

@pytest.mark.asyncio
async def test_process_message_skips_duplicate(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
    valid_apv_dict: dict[str, Any],
) -> None:
    """Test duplicate APVs are skipped."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock message
    mock_message = MagicMock()
    mock_message.value = json.dumps(valid_apv_dict).encode("utf-8")

    # Mock as duplicate (let deserialize run naturally)
    consumer._is_duplicate = AsyncMock(return_value=True)
    consumer._mark_processed = AsyncMock()
    consumer._publish_to_dlq = AsyncMock()

    await consumer._process_message(mock_message)

    # Verify handler NOT called (skipped)
    mock_apv_handler.assert_not_called()

    # Verify NOT marked processed (already was)
    consumer._mark_processed.assert_not_called()

    # Verify counts - duplicate detected early, no processing
    assert consumer._processed_count == 0
    assert consumer._failed_count == 0


# ===================== STATISTICS TESTS =====================


def test_stats_initial_state(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test statistics in initial state."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    stats = consumer.stats

    assert stats["running"] is False
    assert stats["processed_count"] == 0
    assert stats["failed_count"] == 0
    assert stats["success_rate"] == 0.0
    assert stats["uptime_seconds"] == 0
    assert stats["throughput_per_min"] == 0
    assert stats["started_at"] is None


def test_stats_after_processing(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test statistics after processing messages."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    consumer._processed_count = 10
    consumer._failed_count = 2
    consumer._started_at = datetime.utcnow()

    stats = consumer.stats

    assert stats["processed_count"] == 10
    assert stats["failed_count"] == 2
    assert stats["success_rate"] == pytest.approx(10 / 12, rel=0.01)


def test_is_running_property(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test is_running property."""
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    assert consumer.is_running is False

    consumer._running = True
    assert consumer.is_running is True


# ===================== INTEGRATION-STYLE TESTS =====================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_kafka
async def test_consumer_lifecycle(
    consumer_config: APVConsumerConfig,
    mock_apv_handler: AsyncMock,
) -> None:
    """Test consumer start/stop lifecycle.
    
    Requires: Kafka broker running on localhost:9092
    """
    consumer = APVConsumer(consumer_config, mock_apv_handler)

    # Mock Kafka consumer
    with patch("consumers.apv_consumer.AIOKafkaConsumer") as MockConsumer:
        mock_kafka = AsyncMock()
        MockConsumer.return_value = mock_kafka

        # Mock async iteration (no messages)
        async def mock_iteration():
            await asyncio.sleep(0.1)
            consumer._running = False
            return
            yield  # pragma: no cover

        mock_kafka.__aiter__ = lambda self: mock_iteration()

        # Mock Redis
        consumer._init_redis = AsyncMock()
        consumer._redis_client = AsyncMock()

        # Start consumer
        await consumer.start()

        # Verify Kafka consumer lifecycle
        mock_kafka.start.assert_called_once()
        mock_kafka.stop.assert_called_once()

        # Verify stats
        assert consumer._processed_count >= 0
        assert consumer._started_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=consumers", "--cov-report=term-missing"])
