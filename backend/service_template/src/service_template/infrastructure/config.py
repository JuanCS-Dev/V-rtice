"""
Infrastructure Layer - Configuration

Application configuration using pydantic-settings.
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

    # Service
    service_name: str = "service-template"
    service_version: str = "1.0.0"
    port: int = 8000
    host: str = "0.0.0.0"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # Database
    database_url: str = "postgresql+asyncpg://vertice:vertice_dev@localhost:5432/vertice_template"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = True
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831

    # Security
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    api_key_header: str = "X-API-Key"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
