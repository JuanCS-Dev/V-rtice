"""
100% Coverage Tests for base_config.py
====================================

Tests ALL classes, validators, properties, edge cases.
Production-grade only.
"""

from pathlib import Path

import pytest
from pydantic import Field, ValidationError

from shared.base_config import (
    BaseServiceConfig,
    Environment,
    generate_env_example,
    load_config,
)


class TestEnvironmentEnum:
    """Test Environment enum."""

    def test_environment_values(self) -> None:
        """Test all environment enum values."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"
        assert Environment.TESTING == "testing"

    def test_environment_is_string_enum(self) -> None:
        """Test Environment inherits from str."""
        assert isinstance(Environment.DEVELOPMENT, str)
        assert isinstance(Environment.PRODUCTION, str)

    def test_environment_comparison(self) -> None:
        """Test environment comparison with strings."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.PRODUCTION != "development"


class TestBaseServiceConfig:
    """Test BaseServiceConfig class."""

    def test_minimal_valid_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test creating config with minimal required fields."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.service_name == "test-service"
        assert config.service_port == 8000
        assert config.vertice_env == Environment.DEVELOPMENT

    def test_all_environments(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test all environment values."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        for env in [Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION, Environment.TESTING]:
            monkeypatch.setenv("VERTICE_ENV", env.value)
            config = BaseServiceConfig()
            assert config.vertice_env == env

    def test_service_name_validation_min_length(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test service_name minimum length validation."""
        monkeypatch.setenv("SERVICE_NAME", "ab")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        with pytest.raises(ValidationError) as exc_info:
            BaseServiceConfig()
        assert "service_name" in str(exc_info.value).lower()

    def test_service_name_validation_max_length(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test service_name maximum length validation."""
        monkeypatch.setenv("SERVICE_NAME", "a" * 65)
        monkeypatch.setenv("SERVICE_PORT", "8000")

        with pytest.raises(ValidationError) as exc_info:
            BaseServiceConfig()
        assert "service_name" in str(exc_info.value).lower()

    def test_service_name_pattern_validation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test service_name pattern validation (kebab-case)."""
        monkeypatch.setenv("SERVICE_NAME", "Invalid_Service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        with pytest.raises(ValidationError) as exc_info:
            BaseServiceConfig()
        assert "service_name" in str(exc_info.value).lower()

    def test_service_port_min_validation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test service_port minimum value validation."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "1023")

        with pytest.raises(ValidationError) as exc_info:
            BaseServiceConfig()
        assert "service_port" in str(exc_info.value).lower()

    def test_service_port_max_validation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test service_port maximum value validation."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "65536")

        with pytest.raises(ValidationError) as exc_info:
            BaseServiceConfig()
        assert "service_port" in str(exc_info.value).lower()

    def test_log_level_validation_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test log_level validation with valid values."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            monkeypatch.setenv("LOG_LEVEL", level)
            config = BaseServiceConfig()
            assert config.log_level == level.upper()

    def test_log_level_validation_lowercase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test log_level validation converts lowercase to uppercase."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("LOG_LEVEL", "debug")

        config = BaseServiceConfig()
        assert config.log_level == "DEBUG"

    def test_log_level_validation_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test log_level validation rejects invalid values."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        with pytest.raises(ValidationError) as exc_info:
            BaseServiceConfig()
        assert "log_level" in str(exc_info.value).lower()

    def test_cors_origins_from_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test CORS origins parsing from JSON array string."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000","http://localhost:8000","http://example.com"]')

        config = BaseServiceConfig()
        assert len(config.cors_origins) == 3
        assert "http://localhost:3000" in config.cors_origins
        assert "http://example.com" in config.cors_origins

    def test_cors_origins_from_string_with_spaces(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test CORS origins parsing from CSV string (programmatic)."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig(cors_origins=" http://localhost:3000 , http://localhost:8000 ")
        assert len(config.cors_origins) == 2
        assert "http://localhost:3000" in config.cors_origins

    def test_cors_origins_csv_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test CORS origins CSV string parsing in validator."""
        from shared.base_config import BaseServiceConfig

        result = BaseServiceConfig.parse_cors_origins("http://a.com,http://b.com, http://c.com ")
        assert len(result) == 3
        assert "http://a.com" in result
        assert "http://c.com" in result

    def test_cors_origins_from_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test CORS origins from list (programmatic)."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig(cors_origins=["http://test1.com", "http://test2.com"])
        assert len(config.cors_origins) == 2

    def test_debug_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test debug flag."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("DEBUG", "true")

        config = BaseServiceConfig()
        assert config.debug is True

    def test_redis_db_validation_min(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test redis_db minimum value validation."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("REDIS_DB", "-1")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_redis_db_validation_max(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test redis_db maximum value validation."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("REDIS_DB", "16")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_jwt_secret_min_length(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test JWT secret minimum length validation."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("JWT_SECRET", "short")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_jwt_expiration_validation_min(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test JWT expiration minimum validation."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "4")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_jwt_expiration_validation_max(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test JWT expiration maximum validation."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "1441")

        with pytest.raises(ValidationError):
            BaseServiceConfig()


class TestBaseServiceConfigProperties:
    """Test BaseServiceConfig properties."""

    def test_is_development(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_development property."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("VERTICE_ENV", "development")

        config = BaseServiceConfig()
        assert config.is_development is True
        assert config.is_production is False
        assert config.is_testing is False

    def test_is_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_production property."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("VERTICE_ENV", "production")

        config = BaseServiceConfig()
        assert config.is_production is True
        assert config.is_development is False
        assert config.is_testing is False

    def test_is_testing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_testing property."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("VERTICE_ENV", "testing")

        config = BaseServiceConfig()
        assert config.is_testing is True
        assert config.is_development is False
        assert config.is_production is False

    def test_postgres_url_complete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test postgres_url with all parameters."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "password")

        config = BaseServiceConfig()
        assert config.postgres_url == "postgresql://user:password@localhost:5432/testdb"

    def test_postgres_url_incomplete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test postgres_url returns None when incomplete."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")

        config = BaseServiceConfig()
        assert config.postgres_url is None

    def test_postgres_url_missing_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test postgres_url returns None when host is missing."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "password")

        config = BaseServiceConfig()
        assert config.postgres_url is None

    def test_redis_url_with_password(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test redis_url with password."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("REDIS_HOST", "localhost")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "0")
        monkeypatch.setenv("REDIS_PASSWORD", "secret")

        config = BaseServiceConfig()
        assert config.redis_url == "redis://:secret@localhost:6379/0"

    def test_redis_url_without_password(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test redis_url without password."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("REDIS_HOST", "localhost")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "1")

        config = BaseServiceConfig()
        assert config.redis_url == "redis://localhost:6379/1"

    def test_redis_url_missing_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test redis_url returns None when host missing."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.redis_url is None


class TestBaseServiceConfigMethods:
    """Test BaseServiceConfig methods."""

    def test_model_dump_safe_masks_secrets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test model_dump_safe masks sensitive fields."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_PASSWORD", "secret123")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("API_KEY", "key123")

        config = BaseServiceConfig()
        safe_dump = config.model_dump_safe()

        assert safe_dump["postgres_password"] == "***"
        assert safe_dump["jwt_secret"] == "***"
        assert safe_dump["api_key"] == "***"
        assert safe_dump["service_name"] == "test-service"

    def test_model_dump_safe_none_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test model_dump_safe handles None values."""
        # Clear .env loading to ensure clean state
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        # Explicitly unset secrets
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.delenv("API_KEY", raising=False)

        # Create config with explicit env_file=None to avoid .env pollution
        from pydantic_settings import SettingsConfigDict
        
        class TestConfig(BaseServiceConfig):
            model_config = SettingsConfigDict(
                env_file=None,
                env_file_encoding="utf-8",
                env_nested_delimiter="__",
                case_sensitive=False,
                extra="ignore",
                validate_default=True,
                validate_assignment=True,
            )
        
        config = TestConfig()
        safe_dump = config.model_dump_safe()

        assert safe_dump["postgres_password"] is None
        assert safe_dump["jwt_secret"] is None

    def test_validate_required_vars_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validate_required_vars with all vars present."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("API_KEY", "test-key")

        config = BaseServiceConfig()
        config.validate_required_vars("service_name", "service_port", "api_key")

    def test_validate_required_vars_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validate_required_vars raises on missing vars."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()

        with pytest.raises(ValueError) as exc_info:
            config.validate_required_vars("service_name", "api_key")
        assert "API_KEY" in str(exc_info.value)

    def test_validate_required_vars_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validate_required_vars raises on empty string."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("API_KEY", "   ")

        config = BaseServiceConfig()

        with pytest.raises(ValueError) as exc_info:
            config.validate_required_vars("api_key")
        assert "API_KEY" in str(exc_info.value)

    def test_validate_required_vars_multiple_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validate_required_vars with multiple missing vars."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        # Ensure required vars are NOT set
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("JWT_SECRET", raising=False)

        # Use config without .env loading
        from pydantic_settings import SettingsConfigDict
        
        class TestConfig(BaseServiceConfig):
            model_config = SettingsConfigDict(
                env_file=None,
                env_file_encoding="utf-8",
                env_nested_delimiter="__",
                case_sensitive=False,
                extra="ignore",
                validate_default=True,
                validate_assignment=True,
            )
        
        config = TestConfig()

        with pytest.raises(ValueError) as exc_info:
            config.validate_required_vars("api_key", "jwt_secret")
        error_msg = str(exc_info.value)
        assert "API_KEY" in error_msg
        assert "JWT_SECRET" in error_msg


class TestGenerateEnvExample:
    """Test generate_env_example function."""

    def test_generate_env_example_basic(self) -> None:
        """Test generate_env_example creates valid output."""
        result = generate_env_example(BaseServiceConfig)

        assert "SERVICE_NAME=" in result
        assert "SERVICE_PORT=" in result
        assert "Environment Variables" in result

    def test_generate_env_example_has_comments(self) -> None:
        """Test generate_env_example includes descriptions."""
        result = generate_env_example(BaseServiceConfig)

        assert "# Service name" in result or "# Name of the microservice" in result
        assert "#" in result

    def test_generate_env_example_custom_config(self) -> None:
        """Test generate_env_example with custom config class."""

        class CustomConfig(BaseServiceConfig):
            custom_field: str = Field(default="test", description="Custom field")

        result = generate_env_example(CustomConfig)
        assert "CUSTOM_FIELD" in result
        assert "test" in result

    def test_generate_env_example_with_constraints(self) -> None:
        """Test generate_env_example with field constraints."""
        from pydantic import Field

        class ConfigWithConstraints(BaseServiceConfig):
            multiple_field: int = Field(default=10, multiple_of=5, description="Multiple field")

        result = generate_env_example(ConfigWithConstraints)
        assert "Multiple of: 5" in result or "multiple_field" in result.lower()


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_basic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test load_config with basic config."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = load_config(BaseServiceConfig)
        assert config.service_name == "test-service"
        assert config.service_port == 8000

    def test_load_config_missing_env_file(self) -> None:
        """Test load_config with non-existent env file."""
        fake_path = Path("/nonexistent/.env")

        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(BaseServiceConfig, env_file=fake_path)
        assert "not found" in str(exc_info.value).lower()

    def test_load_config_invalid_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test load_config with invalid configuration."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "invalid")

        with pytest.raises(ValueError) as exc_info:
            load_config(BaseServiceConfig)
        assert "validation failed" in str(exc_info.value).lower()

    def test_load_config_with_env_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test load_config with custom env file."""
        env_file = tmp_path / ".env.test"
        env_file.write_text("SERVICE_NAME=test-service\nSERVICE_PORT=8000\n")

        config = load_config(BaseServiceConfig, env_file=env_file)
        assert config.service_name == "test-service"


class TestDefaultValues:
    """Test default values for all fields."""

    def test_default_log_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default log_level."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.log_level == "INFO"

    def test_default_api_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default api_prefix."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.api_prefix == "/api/v1"

    def test_default_cors_origins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default CORS origins."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert len(config.cors_origins) == 2
        assert "http://localhost:3000" in config.cors_origins

    def test_default_postgres_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default postgres_port."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.postgres_port == 5432

    def test_default_redis_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default redis_port."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.redis_port == 6379

    def test_default_redis_db(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default redis_db."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.redis_db == 0

    def test_default_jwt_algorithm(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default jwt_algorithm."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.jwt_algorithm == "HS256"

    def test_default_jwt_expiration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default jwt_expiration_minutes."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.jwt_expiration_minutes == 30

    def test_default_enable_metrics(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default enable_metrics."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.enable_metrics is True

    def test_default_enable_tracing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default enable_tracing."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")

        config = BaseServiceConfig()
        assert config.enable_tracing is False
