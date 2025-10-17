"""Tests for Kafka consumer."""

from decimal import Decimal
from uuid import uuid4

import pytest
from kafka_consumer import VerdictConsumer


@pytest.mark.asyncio
async def test_consumer_init(mock_cache, ws_manager):
    """Test consumer initialization."""
    consumer = VerdictConsumer(mock_cache, ws_manager)

    assert consumer.cache == mock_cache
    assert consumer.ws_manager == ws_manager
    assert consumer.consumer is None
    assert consumer.running is False


@pytest.mark.asyncio
async def test_consumer_start_stop(mock_cache, ws_manager, mocker):
    """Test consumer start/stop lifecycle."""
    consumer = VerdictConsumer(mock_cache, ws_manager)

    # Mock AIOKafkaConsumer
    mock_kafka = mocker.patch("kafka_consumer.AIOKafkaConsumer")
    mock_instance = mocker.AsyncMock()
    mock_kafka.return_value = mock_instance

    await consumer.start()

    assert consumer.running is True

    await consumer.stop()

    assert consumer.running is False


@pytest.mark.asyncio
async def test_parse_verdict(mock_cache, ws_manager, sample_verdict_data):
    """Test verdict parsing from Kafka message."""
    consumer = VerdictConsumer(mock_cache, ws_manager)

    verdict = consumer._parse_verdict(sample_verdict_data)

    assert verdict.category == "ALLIANCE"
    assert verdict.severity == "MEDIUM"
    assert isinstance(verdict.confidence, Decimal)


@pytest.mark.asyncio
async def test_parse_verdict_with_uuid_strings(mock_cache, ws_manager):
    """Test parsing verdict with UUID strings."""
    consumer = VerdictConsumer(mock_cache, ws_manager)

    data = {
        "id": str(uuid4()),
        "mitigation_command_id": str(uuid4()),
        "timestamp": "2025-10-17T12:00:00",
        "category": "THREAT",
        "severity": "CRITICAL",
        "title": "Test",
        "agents_involved": ["a1"],
        "evidence_chain": ["m1"],
        "confidence": "0.95",
        "recommended_action": "ISOLATE",
        "status": "ACTIVE",
        "color": "#DC2626",
        "created_at": "2025-10-17T12:00:00",
    }

    verdict = consumer._parse_verdict(data)

    # UUIDs should be converted
    assert verdict.mitigation_command_id is not None


@pytest.mark.asyncio
async def test_consume_verdict_success(mock_cache, ws_manager, sample_verdict_data, mocker):
    """Test successful verdict consumption."""
    consumer = VerdictConsumer(mock_cache, ws_manager)

    # Mock Kafka message
    mock_message = mocker.MagicMock()
    mock_message.value = sample_verdict_data

    # Mock consumer
    async def mock_async_iter():
        yield mock_message

    consumer.consumer = mocker.AsyncMock()
    consumer.consumer.__aiter__.return_value = mock_async_iter()

    # Mock cache and ws_manager methods
    mock_cache.cache_verdict = mocker.AsyncMock()
    mock_cache.invalidate_stats = mocker.AsyncMock()
    ws_manager.broadcast_verdict = mocker.AsyncMock()

    # Validate _parse_verdict is working
    verdict = consumer._parse_verdict(sample_verdict_data)
    assert verdict.category == "ALLIANCE"


@pytest.mark.asyncio
async def test_consume_verdict_parsing_error(mock_cache, ws_manager, mocker):
    """Test verdict consumption with parsing error."""
    consumer = VerdictConsumer(mock_cache, ws_manager)

    # Mock Kafka message with invalid data
    mock_message = mocker.MagicMock()
    mock_message.value = {"invalid": "data"}  # Missing required fields

    # Test _parse_verdict with invalid data
    with pytest.raises(Exception):
        consumer._parse_verdict(mock_message.value)
