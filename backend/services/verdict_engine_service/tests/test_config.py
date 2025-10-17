"""Tests for configuration."""

import pytest
from pydantic import ValidationError

from verdict_engine_service.config import Settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()

    assert settings.service_name == "verdict_engine"
    assert settings.version == "1.0.0"
    assert settings.log_level == "INFO"
    assert settings.api_port == 8002


def test_settings_postgres_dsn():
    """Test PostgreSQL DSN construction."""
    settings = Settings(
        postgres_host="db.example.com",
        postgres_port=5433,
        postgres_db="cockpit",
        postgres_user="verdict_user",
        postgres_password="secret123",
    )

    expected = "postgresql://verdict_user:secret123@db.example.com:5433/cockpit"
    assert settings.postgres_dsn == expected


def test_settings_invalid_log_level():
    """Test invalid log level validation."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(log_level="INVALID")

    assert "log_level" in str(exc_info.value)


def test_settings_redis_url():
    """Test Redis URL configuration."""
    settings = Settings(redis_url="redis://cache.example.com:6380/1")

    assert settings.redis_url == "redis://cache.example.com:6380/1"


def test_settings_kafka_config():
    """Test Kafka configuration."""
    settings = Settings(
        kafka_bootstrap_servers="kafka1:9092,kafka2:9092",
        kafka_consumer_group="custom_group",
        kafka_verdicts_topic="custom-verdicts",
    )

    assert settings.kafka_bootstrap_servers == "kafka1:9092,kafka2:9092"
    assert settings.kafka_consumer_group == "custom_group"
    assert settings.kafka_verdicts_topic == "custom-verdicts"


def test_settings_websocket_config():
    """Test WebSocket configuration."""
    settings = Settings(
        websocket_ping_interval=60,
        websocket_max_connections=200,
    )

    assert settings.websocket_ping_interval == 60
    assert settings.websocket_max_connections == 200


def test_settings_from_env(monkeypatch):
    """Test settings loading from environment."""
    monkeypatch.setenv("POSTGRES_HOST", "env-db-host")
    monkeypatch.setenv("POSTGRES_PORT", "5555")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.postgres_host == "env-db-host"
    assert settings.postgres_port == 5555
    assert settings.log_level == "DEBUG"
