

def test_postgres_dsn_construction() -> None:
    """Test PostgreSQL DSN property."""
    from narrative_filter_service.config import settings

    dsn = settings.postgres_dsn
    assert "postgresql+asyncpg://" in dsn
    assert settings.postgres_db in dsn
    assert settings.postgres_host in dsn
    assert str(settings.postgres_port) in dsn


def test_kafka_settings() -> None:
    """Test Kafka configuration."""
    from narrative_filter_service.config import settings

    assert settings.kafka_bootstrap_servers == "localhost:9092"
    assert settings.kafka_topic_input == "agent-communications"
    assert settings.kafka_topic_semantic == "semantic-events"


def test_threshold_settings() -> None:
    """Test ML threshold settings."""
    from narrative_filter_service.config import settings

    assert 0 < settings.alliance_threshold <= 1
    assert 0 < settings.inconsistency_threshold <= 1
    assert 0 < settings.deception_threshold <= 1
