"""Base configuration using Pydantic Settings."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base settings for all Vértice services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str
    service_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"

    host: str = "0.0.0.0"
    port: int
    workers: int = 1

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    otel_enabled: bool = True
    otel_endpoint: str = "http://jaeger:4318"
    metrics_enabled: bool = True

    api_gateway_url: str = "http://api-gateway:8000"
    api_key: str = Field(default="", description="API key for gateway auth")

    database_url: str | None = None
    database_pool_size: int = 10
    database_max_overflow: int = 20

    redis_url: str | None = None
    redis_db: int = 0

    cors_origins: list[str] = ["http://localhost:3000"]
    jwt_secret: str = Field(default="", description="JWT signing secret")

    def get_db_url(self) -> str:
        """Get database URL or raise if not configured."""
        if not self.database_url:
            raise ValueError(f"{self.service_name}: database_url not configured")
        return self.database_url
