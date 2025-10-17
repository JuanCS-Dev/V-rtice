"""Tests for config."""

from config import settings


def test_config_settings() -> None:
    """Test configuration settings."""
    assert settings.service_name == "command-bus-service"
    assert settings.port == 9202
    assert settings.nats_url == "nats://localhost:4222"
    assert settings.rate_limit_terminate == 3
    assert settings.command_timeout_terminate == 30


def test_postgres_dsn() -> None:
    """Test PostgreSQL DSN construction."""
    dsn = settings.postgres_dsn
    assert "postgresql+asyncpg://" in dsn
    assert "vertice_db" in dsn
    assert settings.postgres_host in dsn
