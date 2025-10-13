"""
Configuration management for Adaptive Immune System - HITL API.

Uses Pydantic Settings for type-safe configuration loading from environment variables.

Usage:
    from hitl.config import settings

    print(settings.app_name)
    print(settings.database_url)
"""

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    All settings can be overridden via environment variables.
    Boolean values: "true", "1", "yes" = True | "false", "0", "no" = False
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # --- Application ---
    app_name: str = Field(
        default="Adaptive Immune System - HITL API",
        description="Application name displayed in logs and docs",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (more verbose logging, auto-reload)",
    )

    # --- Server ---
    host: str = Field(
        default="0.0.0.0",
        description="Server host to bind to",
    )
    port: int = Field(
        default=8003,
        ge=1,
        le=65535,
        description="Server port to bind to",
    )

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/adaptive_immune",
        description="PostgreSQL database URL (asyncpg driver for async support)",
    )

    # --- RabbitMQ ---
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="RabbitMQ connection URL",
    )

    # --- GitHub ---
    github_token: str = Field(
        default="",
        description="GitHub Personal Access Token for API access",
    )
    github_repo_owner: str = Field(
        default="vertice-ai",
        description="GitHub repository owner/organization",
    )
    github_repo_name: str = Field(
        default="adaptive-immune",
        description="GitHub repository name",
    )

    # --- Redis ---
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching",
    )

    # --- CORS ---
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Vue dev server
        ],
        description="Allowed CORS origins for frontend access",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- Observability ---
    log_level: str = Field(
        default="info",
        description="Logging level (debug, info, warning, error, critical)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate and normalize log level."""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        level = v.lower()
        if level not in valid_levels:
            raise ValueError(f"log_level must be one of: {', '.join(valid_levels)}")
        return level

    prometheus_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics collection",
    )

    # --- Feature Flags ---
    websocket_enabled: bool = Field(
        default=True,
        description="Enable WebSocket real-time updates",
    )

    wargaming_enabled: bool = Field(
        default=True,
        description="Enable wargaming engine integration",
    )

    # --- Computed Properties ---

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug

    @property
    def github_configured(self) -> bool:
        """Check if GitHub integration is configured."""
        return bool(self.github_token)

    @property
    def base_url(self) -> str:
        """Get base URL for this service."""
        protocol = "https" if self.is_production else "http"
        return f"{protocol}://{self.host}:{self.port}"

    def model_dump_safe(self) -> dict:
        """
        Dump settings with sensitive fields masked.

        Use this for logging configuration without exposing secrets.

        Returns:
            Dictionary with sensitive fields masked
        """
        data = self.model_dump()

        # Mask sensitive fields
        sensitive_fields = ["github_token", "database_url", "rabbitmq_url", "redis_url"]
        for field in sensitive_fields:
            if field in data and data[field]:
                # Show first 4 and last 4 characters only
                value = data[field]
                if len(value) > 12:
                    data[field] = f"{value[:4]}...{value[-4:]}"
                else:
                    data[field] = "***"

        return data


# Global settings instance
settings = Settings()


# Validation on import
if __name__ == "__main__":
    """Test settings loading and display current configuration."""
    import json

    print("=" * 60)
    print("ADAPTIVE IMMUNE SYSTEM - HITL API CONFIGURATION")
    print("=" * 60)
    print()
    print("Configuration loaded successfully!")
    print()
    print("Settings (safe dump):")
    print(json.dumps(settings.model_dump_safe(), indent=2))
    print()
    print("Computed properties:")
    print(f"  is_production: {settings.is_production}")
    print(f"  is_development: {settings.is_development}")
    print(f"  github_configured: {settings.github_configured}")
    print(f"  base_url: {settings.base_url}")
    print()
    print("=" * 60)
