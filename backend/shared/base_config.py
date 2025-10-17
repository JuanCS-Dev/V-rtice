"""
Vértice Platform - Base Configuration Management
=================================================

Standardized environment variable management using Pydantic Settings.
All services should inherit from BaseServiceConfig to ensure consistent
configuration handling, validation, and documentation.

Features:
    - Type-safe configuration with Pydantic
    - Automatic .env file loading
    - Environment variable validation at startup
    - Consistent naming conventions
    - Secret management integration
    - Development/staging/production profiles

Usage:
    ```python
    from shared.base_config import BaseServiceConfig
    from pydantic import Field
    
    class MyServiceConfig(BaseServiceConfig):
        # Service-specific settings
        api_key: str = Field(..., description="External API key")
        max_workers: int = Field(default=4, ge=1, le=32)
        
    config = MyServiceConfig()
    ```

Environment Variable Naming Convention:
    - All uppercase with underscores
    - Prefix with service name: SERVICE_NAME_VAR_NAME
    - Common prefixes: VERTICE_, MAXIMUS_, SERVICE_
    - Examples:
        - VERTICE_ENV=production
        - MAXIMUS_CORE_PORT=8001
        - SERVICE_LOG_LEVEL=INFO

Author: Vértice Platform Team
License: Proprietary
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================================
# ENVIRONMENT ENUM
# ============================================================================


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


# ============================================================================
# BASE SERVICE CONFIGURATION
# ============================================================================


class BaseServiceConfig(BaseSettings):
    """
    Base configuration class for all Vértice microservices.

    All service-specific configs should inherit from this class to ensure
    consistent environment variable handling, validation, and documentation.

    Common Environment Variables:
        VERTICE_ENV: Environment name (development/staging/production)
        SERVICE_NAME: Name of the microservice
        SERVICE_PORT: Port number for the service
        LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        DEBUG: Enable debug mode (true/false)
    """

    model_config = SettingsConfigDict(
        # Environment file configuration
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        # Case sensitivity
        case_sensitive=False,
        # Extra fields handling
        extra="ignore",
        # Validation
        validate_default=True,
        validate_assignment=True,
    )

    # ========================================================================
    # CORE SETTINGS - Required for all services
    # ========================================================================

    vertice_env: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment",
        validation_alias="VERTICE_ENV",
    )

    service_name: str = Field(
        ...,
        description="Service name (kebab-case)",
        min_length=3,
        max_length=64,
        pattern=r"^[a-z0-9-]+$",
        validation_alias="SERVICE_NAME",
    )

    service_port: int = Field(
        ...,
        description="Service HTTP port",
        ge=1024,
        le=65535,
        validation_alias="SERVICE_PORT",
    )

    # ========================================================================
    # LOGGING CONFIGURATION
    # ========================================================================

    log_level: str = Field(
        default="INFO",
        description="Logging level",
        validation_alias="LOG_LEVEL",
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        validation_alias="DEBUG",
    )

    # ========================================================================
    # API CONFIGURATION
    # ========================================================================

    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix",
        validation_alias="API_PREFIX",
    )

    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
        validation_alias="CORS_ORIGINS",
    )

    # ========================================================================
    # DATABASE CONFIGURATION (Optional - services override if needed)
    # ========================================================================

    postgres_host: Optional[str] = Field(
        default=None,
        description="PostgreSQL host",
        validation_alias="POSTGRES_HOST",
    )

    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port",
        validation_alias="POSTGRES_PORT",
    )

    postgres_db: Optional[str] = Field(
        default=None,
        description="PostgreSQL database name",
        validation_alias="POSTGRES_DB",
    )

    postgres_user: Optional[str] = Field(
        default=None,
        description="PostgreSQL username",
        validation_alias="POSTGRES_USER",
    )

    postgres_password: Optional[str] = Field(
        default=None,
        description="PostgreSQL password",
        validation_alias="POSTGRES_PASSWORD",
    )

    # ========================================================================
    # REDIS CONFIGURATION (Optional)
    # ========================================================================

    redis_host: Optional[str] = Field(
        default=None,
        description="Redis host",
        validation_alias="REDIS_HOST",
    )

    redis_port: int = Field(
        default=6379,
        description="Redis port",
        validation_alias="REDIS_PORT",
    )

    redis_db: int = Field(
        default=0,
        description="Redis database number",
        ge=0,
        le=15,
        validation_alias="REDIS_DB",
    )

    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password",
        validation_alias="REDIS_PASSWORD",
    )

    # ========================================================================
    # SECURITY CONFIGURATION
    # ========================================================================

    jwt_secret: Optional[str] = Field(
        default=None,
        description="JWT signing secret",
        min_length=32,
        validation_alias="JWT_SECRET",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
        validation_alias="JWT_ALGORITHM",
    )

    jwt_expiration_minutes: int = Field(
        default=30,
        description="JWT token expiration in minutes",
        ge=5,
        le=1440,
        validation_alias="JWT_EXPIRATION_MINUTES",
    )

    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication",
        validation_alias="API_KEY",
    )

    # ========================================================================
    # OBSERVABILITY
    # ========================================================================

    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
        validation_alias="ENABLE_METRICS",
    )

    enable_tracing: bool = Field(
        default=False,
        description="Enable distributed tracing",
        validation_alias="ENABLE_TRACING",
    )

    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking",
        validation_alias="SENTRY_DSN",
    )

    # ========================================================================
    # VALIDATORS
    # ========================================================================

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard Python logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.vertice_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.vertice_env == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.vertice_env == Environment.TESTING

    @property
    def postgres_url(self) -> Optional[str]:
        """Build PostgreSQL connection URL."""
        if not all(
            [
                self.postgres_host,
                self.postgres_db,
                self.postgres_user,
                self.postgres_password,
            ]
        ):
            return None
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> Optional[str]:
        """Build Redis connection URL."""
        if not self.redis_host:
            return None
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def model_dump_safe(self) -> Dict[str, Any]:
        """
        Dump config as dict with secrets masked.

        Returns:
            Dict with sensitive fields replaced with '***'
        """
        data = self.model_dump()
        sensitive_keys = [
            "password",
            "secret",
            "token",
            "key",
            "dsn",
            "api_key",
            "jwt_secret",
        ]

        for key in data:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                data[key] = "***" if data[key] else None

        return data

    def validate_required_vars(self, *var_names: str) -> None:
        """
        Validate that required environment variables are set.

        Args:
            *var_names: Names of required configuration attributes

        Raises:
            ValueError: If any required variable is None or empty
        """
        missing = []
        for var_name in var_names:
            value = getattr(self, var_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(var_name.upper())

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


# ============================================================================
# ENV EXAMPLE GENERATOR
# ============================================================================


def generate_env_example(config_class: type[BaseServiceConfig]) -> str:
    """
    Generate .env.example content from a config class.

    Args:
        config_class: Configuration class extending BaseServiceConfig

    Returns:
        String content for .env.example file with all fields documented
    """
    lines = [
        "# =============================================================================",
        f"# {config_class.__name__} - Environment Variables",
        "# =============================================================================",
        "",
        "# This file lists all environment variables used by the service.",
        "# Copy to .env and fill in appropriate values.",
        "",
    ]

    for field_name, field_info in config_class.model_fields.items():
        # Field description
        description = field_info.description or "No description"
        lines.append(f"# {description}")

        # Field constraints
        if hasattr(field_info, "ge") and field_info.ge is not None:
            lines.append(f"#   Min value: {field_info.ge}")
        if hasattr(field_info, "le") and field_info.le is not None:
            lines.append(f"#   Max value: {field_info.le}")
        if hasattr(field_info, "pattern") and field_info.pattern:
            lines.append(f"#   Pattern: {field_info.pattern}")

        # Environment variable name
        env_name = field_name.upper()
        if hasattr(field_info, "validation_alias") and field_info.validation_alias:
            env_name = field_info.validation_alias

        # Default value or placeholder
        default = field_info.default
        if default is None or (hasattr(default, "__name__") and default.__name__ == "_missing"):
            value = ""  # Required field
        elif isinstance(default, list):
            value = ",".join(str(v) for v in default)
        elif isinstance(default, Enum):
            value = default.value
        else:
            value = str(default)

        lines.append(f"{env_name}={value}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def load_config(
    config_class: type[BaseServiceConfig],
    env_file: Optional[Path] = None,
) -> BaseServiceConfig:
    """
    Load and validate service configuration.

    Args:
        config_class: Configuration class to instantiate
        env_file: Optional path to .env file (default: .env in current dir)

    Returns:
        Validated configuration instance

    Raises:
        ValidationError: If configuration is invalid
        FileNotFoundError: If specified env_file doesn't exist
    """
    if env_file and not env_file.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file}")

    # Temporarily override env_file if provided
    if env_file:
        config_class.model_config["env_file"] = str(env_file)

    try:
        config = config_class()
        return config
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}") from e


__all__ = [
    "BaseServiceConfig",
    "Environment",
    "generate_env_example",
    "load_config",
]
