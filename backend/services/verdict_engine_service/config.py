"""Configuration for Verdict Engine Service.

All settings are loaded from environment variables with sensible defaults.
100% type-safe using pydantic-settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Info
    service_name: str = "verdict_engine"
    version: str = "1.0.0"
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # Database (PostgreSQL via narrative_filter)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "cockpit_db"
    postgres_user: str = "cockpit_user"
    postgres_password: str = "cockpit_pass_dev_only"

    # Redis (cache)
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300  # 5 minutes

    # Kafka (consume verdicts-stream)
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "verdict_engine_group"
    kafka_verdicts_topic: str = "verdicts-stream"
    kafka_auto_offset_reset: str = "latest"

    # WebSocket
    websocket_ping_interval: int = 30
    websocket_max_connections: int = 100

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    api_workers: int = 1

    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL DSN."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
