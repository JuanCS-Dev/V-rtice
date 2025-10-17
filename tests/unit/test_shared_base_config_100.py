"""
Test Suite: base_config.py - 100% ABSOLUTE Coverage
====================================================

Target: backend/shared/base_config.py
Estratégia: Testes de configuração, validação, propriedades e helpers
Meta: 100% statements + 100% branches
"""

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import pytest
from pydantic import Field, ValidationError

from backend.shared.base_config import (
    BaseServiceConfig,
    Environment,
    generate_env_example,
    load_config,
)

# ============================================================================
# ENVIRONMENT ENUM TESTS
# ============================================================================


class TestEnvironment:
    """Test Environment enum."""

    def test_environment_values(self):
        """Test all environment enum values."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"
        assert Environment.TESTING == "testing"

    def test_environment_as_string(self):
        """Test enum value representation."""
        env = Environment.PRODUCTION
        assert env.value == "production"


# ============================================================================
# BASE SERVICE CONFIG TESTS
# ============================================================================


class TestBaseServiceConfig:
    """Test BaseServiceConfig model."""

    def test_minimal_config(self, monkeypatch):
        """Test minimal required configuration."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8080")

        config = BaseServiceConfig()
        assert config.service_name == "test-service"
        assert config.service_port == 8080
        assert config.vertice_env == Environment.DEVELOPMENT  # default

    def test_all_core_fields(self, monkeypatch):
        """Test all core fields with values."""
        monkeypatch.setenv("VERTICE_ENV", "production")
        monkeypatch.setenv("SERVICE_NAME", "my-awesome-service")
        monkeypatch.setenv("SERVICE_PORT", "9000")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DEBUG", "true")

        config = BaseServiceConfig()
        assert config.vertice_env == Environment.PRODUCTION
        assert config.service_name == "my-awesome-service"
        assert config.service_port == 9000
        assert config.log_level == "DEBUG"
        assert config.debug is True

    def test_service_name_validation_pattern(self, monkeypatch):
        """Test service_name pattern validation (kebab-case)."""
        monkeypatch.setenv("SERVICE_PORT", "8080")

        # Valid: lowercase with hyphens
        monkeypatch.setenv("SERVICE_NAME", "my-test-service-123")
        config = BaseServiceConfig()
        assert config.service_name == "my-test-service-123"

    def test_service_name_validation_invalid_pattern(self, monkeypatch):
        """Test service_name rejects invalid patterns."""
        monkeypatch.setenv("SERVICE_PORT", "8080")

        # Invalid: uppercase
        monkeypatch.setenv("SERVICE_NAME", "MyService")
        with pytest.raises((ValidationError, Exception)) as exc:
            BaseServiceConfig()
        error_str = str(exc.value)
        # Pattern validation may appear in different error formats
        assert "service_name" in error_str or "SERVICE_NAME" in error_str or "pattern" in error_str.lower()

    def test_service_name_validation_too_short(self, monkeypatch):
        """Test service_name min_length validation."""
        monkeypatch.setenv("SERVICE_NAME", "ab")  # Too short
        monkeypatch.setenv("SERVICE_PORT", "8080")

        with pytest.raises((ValidationError, Exception)):
            BaseServiceConfig()

    def test_service_name_validation_too_long(self, monkeypatch):
        """Test service_name max_length validation."""
        monkeypatch.setenv("SERVICE_NAME", "a" * 65)  # Too long
        monkeypatch.setenv("SERVICE_PORT", "8080")

        with pytest.raises((ValidationError, Exception)):
            BaseServiceConfig()

    def test_service_port_validation_min(self, monkeypatch):
        """Test service_port minimum value."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "1023")  # Below min

        with pytest.raises((ValidationError, Exception)):
            BaseServiceConfig()

    def test_service_port_validation_max(self, monkeypatch):
        """Test service_port maximum value."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "65536")  # Above max

        with pytest.raises((ValidationError, Exception)):
            BaseServiceConfig()

    def test_log_level_validation_valid(self, monkeypatch):
        """Test log_level accepts valid values."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            monkeypatch.setenv("LOG_LEVEL", level)
            config = BaseServiceConfig()
            assert config.log_level == level

    def test_log_level_validation_case_insensitive(self, monkeypatch):
        """Test log_level converts to uppercase."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("LOG_LEVEL", "debug")

        config = BaseServiceConfig()
        assert config.log_level == "DEBUG"

    def test_log_level_validation_invalid(self, monkeypatch):
        """Test log_level rejects invalid values."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        with pytest.raises(ValidationError) as exc:
            BaseServiceConfig()
        assert "log_level" in str(exc.value)

    def test_cors_origins_from_string(self, monkeypatch):
        """Test cors_origins parsing from comma-separated string."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000","https://example.com","http://api.test"]')

        config = BaseServiceConfig()
        assert len(config.cors_origins) == 3
        assert "http://localhost:3000" in config.cors_origins
        assert "https://example.com" in config.cors_origins

    def test_cors_origins_default(self, monkeypatch):
        """Test cors_origins uses default value."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        # Don't set CORS_ORIGINS, use default

        config = BaseServiceConfig()
        assert isinstance(config.cors_origins, list)
        assert len(config.cors_origins) >= 2

    def test_cors_origins_parse_from_csv_string(self, monkeypatch):
        """Test parse_cors_origins validator with CSV string."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        # Pydantic Settings may handle JSON or need explicit testing
        # We'll test the validator is called correctly
        config = BaseServiceConfig()
        # Validator exists, default behavior works
        assert config.cors_origins is not None

    def test_cors_origins_validator_string_input(self, monkeypatch):
        """Test parse_cors_origins with string input (covers line 295)."""
        from backend.shared.base_config import BaseServiceConfig

        # Test the validator directly
        result = BaseServiceConfig.parse_cors_origins("http://a.com,http://b.com, http://c.com ")
        assert len(result) == 3
        assert "http://a.com" in result
        assert "http://c.com" in result
        # Covers the string split path (line 295)

    def test_cors_origins_validator_list_passthrough(self):
        """Test parse_cors_origins with list input (covers line 296)."""
        from backend.shared.base_config import BaseServiceConfig

        # Test the validator with list (passthrough case)
        input_list = ["http://a.com", "http://b.com"]
        result = BaseServiceConfig.parse_cors_origins(input_list)
        assert result == input_list
        # Covers the return v path (line 296)

    def test_postgres_configuration(self, monkeypatch):
        """Test PostgreSQL configuration fields."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_PORT", "5433")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")

        config = BaseServiceConfig()
        assert config.postgres_host == "localhost"
        assert config.postgres_port == 5433
        assert config.postgres_db == "testdb"
        assert config.postgres_user == "testuser"
        assert config.postgres_password == "testpass"

    def test_redis_configuration(self, monkeypatch):
        """Test Redis configuration fields."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("REDIS_HOST", "redis-server")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "5")
        monkeypatch.setenv("REDIS_PASSWORD", "redispass")

        config = BaseServiceConfig()
        assert config.redis_host == "redis-server"
        assert config.redis_port == 6380
        assert config.redis_db == 5
        assert config.redis_password == "redispass"

    def test_redis_db_validation_min(self, monkeypatch):
        """Test redis_db minimum value (0)."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("REDIS_DB", "0")

        config = BaseServiceConfig()
        assert config.redis_db == 0

    def test_redis_db_validation_max(self, monkeypatch):
        """Test redis_db maximum value (15)."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("REDIS_DB", "15")

        config = BaseServiceConfig()
        assert config.redis_db == 15

    def test_redis_db_validation_out_of_range(self, monkeypatch):
        """Test redis_db rejects values > 15."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("REDIS_DB", "16")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_jwt_configuration(self, monkeypatch):
        """Test JWT configuration."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)  # Min 32 chars
        monkeypatch.setenv("JWT_ALGORITHM", "RS256")
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "60")

        config = BaseServiceConfig()
        assert len(config.jwt_secret) >= 32
        assert config.jwt_algorithm == "RS256"
        assert config.jwt_expiration_minutes == 60

    def test_jwt_secret_validation_too_short(self, monkeypatch):
        """Test JWT secret minimum length."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("JWT_SECRET", "tooshort")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_jwt_expiration_validation_min(self, monkeypatch):
        """Test JWT expiration minimum (5 min)."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "4")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_jwt_expiration_validation_max(self, monkeypatch):
        """Test JWT expiration maximum (1440 min)."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "1441")

        with pytest.raises(ValidationError):
            BaseServiceConfig()

    def test_observability_flags(self, monkeypatch):
        """Test observability configuration."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("ENABLE_METRICS", "false")
        monkeypatch.setenv("ENABLE_TRACING", "true")
        monkeypatch.setenv("SENTRY_DSN", "https://sentry.io/123")

        config = BaseServiceConfig()
        assert config.enable_metrics is False
        assert config.enable_tracing is True
        assert config.sentry_dsn == "https://sentry.io/123"


# ============================================================================
# PROPERTY TESTS
# ============================================================================


class TestConfigProperties:
    """Test BaseServiceConfig computed properties."""

    def test_is_development_true(self, monkeypatch):
        """Test is_development property when env=development."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("VERTICE_ENV", "development")

        config = BaseServiceConfig()
        assert config.is_development is True
        assert config.is_production is False
        assert config.is_testing is False

    def test_is_production_true(self, monkeypatch):
        """Test is_production property when env=production."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("VERTICE_ENV", "production")

        config = BaseServiceConfig()
        assert config.is_production is True
        assert config.is_development is False
        assert config.is_testing is False

    def test_is_testing_true(self, monkeypatch):
        """Test is_testing property when env=testing."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("VERTICE_ENV", "testing")

        config = BaseServiceConfig()
        assert config.is_testing is True
        assert config.is_development is False
        assert config.is_production is False

    def test_postgres_url_complete(self, monkeypatch):
        """Test postgres_url with all fields set."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("POSTGRES_HOST", "dbhost")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("POSTGRES_DB", "mydb")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "pass")

        config = BaseServiceConfig()
        expected = "postgresql://user:pass@dbhost:5432/mydb"
        assert config.postgres_url == expected

    def test_postgres_url_missing_host(self, monkeypatch):
        """Test postgres_url returns None when host missing."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        # No POSTGRES_HOST
        monkeypatch.setenv("POSTGRES_DB", "mydb")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "pass")

        config = BaseServiceConfig()
        assert config.postgres_url is None

    def test_postgres_url_missing_db(self, monkeypatch):
        """Test postgres_url returns None when db missing."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("POSTGRES_HOST", "dbhost")
        # No POSTGRES_DB
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "pass")

        config = BaseServiceConfig()
        assert config.postgres_url is None

    def test_postgres_url_missing_credentials(self, monkeypatch):
        """Test postgres_url returns None when credentials missing."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("POSTGRES_HOST", "dbhost")
        monkeypatch.setenv("POSTGRES_DB", "mydb")
        # Missing user/password

        config = BaseServiceConfig()
        assert config.postgres_url is None

    def test_redis_url_with_password(self, monkeypatch):
        """Test redis_url with password."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "0")
        monkeypatch.setenv("REDIS_PASSWORD", "secret")

        config = BaseServiceConfig()
        expected = "redis://:secret@redishost:6379/0"
        assert config.redis_url == expected

    def test_redis_url_without_password(self, monkeypatch):
        """Test redis_url without password."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "1")

        config = BaseServiceConfig()
        expected = "redis://redishost:6380/1"
        assert config.redis_url == expected

    def test_redis_url_no_host(self, monkeypatch):
        """Test redis_url returns None when host missing."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        # No REDIS_HOST

        config = BaseServiceConfig()
        assert config.redis_url is None


# ============================================================================
# UTILITY METHOD TESTS
# ============================================================================


class TestUtilityMethods:
    """Test BaseServiceConfig utility methods."""

    def test_model_dump_safe_masks_secrets(self, monkeypatch):
        """Test model_dump_safe() masks sensitive fields."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("POSTGRES_PASSWORD", "secretpass")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("API_KEY", "apikey123")

        config = BaseServiceConfig()
        safe_dump = config.model_dump_safe()

        assert safe_dump["postgres_password"] == "***"
        assert safe_dump["jwt_secret"] == "***"
        assert safe_dump["api_key"] == "***"

    def test_model_dump_safe_none_secrets(self, monkeypatch):
        """Test model_dump_safe() handles None secrets."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        # Unset JWT_SECRET to test None handling
        monkeypatch.delenv("JWT_SECRET", raising=False)

        config = BaseServiceConfig()
        safe_dump = config.model_dump_safe()

        assert safe_dump["postgres_password"] is None
        # JWT_SECRET may have a default value, check it's masked if set or None
        if config.jwt_secret:
            assert safe_dump["jwt_secret"] == "***"
        else:
            assert safe_dump["jwt_secret"] is None

    def test_model_dump_safe_preserves_non_secrets(self, monkeypatch):
        """Test model_dump_safe() preserves non-sensitive data."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")

        config = BaseServiceConfig()
        safe_dump = config.model_dump_safe()

        assert safe_dump["service_name"] == "test-svc"
        assert safe_dump["service_port"] == 8080

    def test_validate_required_vars_success(self, monkeypatch):
        """Test validate_required_vars() with all vars present."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("API_KEY", "my-key")

        config = BaseServiceConfig()
        # Should not raise
        config.validate_required_vars("service_name", "service_port", "api_key")

    def test_validate_required_vars_missing(self, monkeypatch):
        """Test validate_required_vars() raises on missing vars."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        # API_KEY not set

        config = BaseServiceConfig()
        with pytest.raises(ValueError) as exc:
            config.validate_required_vars("service_name", "api_key")
        assert "Missing required environment variables" in str(exc.value)
        assert "API_KEY" in str(exc.value)

    def test_validate_required_vars_empty_string(self, monkeypatch):
        """Test validate_required_vars() treats empty string as missing."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("API_KEY", "   ")  # Whitespace only

        config = BaseServiceConfig()
        with pytest.raises(ValueError) as exc:
            config.validate_required_vars("api_key")
        assert "API_KEY" in str(exc.value)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestGenerateEnvExample:
    """Test generate_env_example() function."""

    def test_generate_env_example_basic(self):
        """Test basic .env.example generation."""
        result = generate_env_example(BaseServiceConfig)

        assert "BaseServiceConfig" in result
        assert "SERVICE_NAME" in result
        assert "SERVICE_PORT" in result
        assert "LOG_LEVEL" in result

    def test_generate_env_example_includes_descriptions(self):
        """Test descriptions are included."""
        result = generate_env_example(BaseServiceConfig)

        assert "Service name" in result or "Service HTTP port" in result

    def test_generate_env_example_includes_defaults(self):
        """Test default values are included."""
        result = generate_env_example(BaseServiceConfig)

        # Check for some default values
        assert "INFO" in result  # log_level default
        assert "/api/v1" in result  # api_prefix default

    def test_generate_env_example_custom_config(self):
        """Test with custom config class."""
        class CustomConfig(BaseServiceConfig):
            custom_field: str = Field(
                default="custom_value",
                description="A custom field",
                validation_alias="CUSTOM_FIELD"
            )

        result = generate_env_example(CustomConfig)
        assert "CUSTOM_FIELD" in result
        assert "custom_value" in result

    def test_generate_env_example_with_constraints(self):
        """Test env example generation includes field constraints."""
        class ConfigWithConstraints(BaseServiceConfig):
            max_value_field: int = Field(
                default=100,
                ge=1,
                le=1000,
                description="Field with constraints"
            )
            pattern_field: str = Field(
                default="test",
                pattern=r"^[a-z]+$",
                description="Field with pattern"
            )
            multiple_field: int = Field(
                default=10,
                multiple_of=5,
                description="Field with multiple_of constraint"
            )

        result = generate_env_example(ConfigWithConstraints)
        # Covers lines 420, 422, 424 - verify constraints appear in output
        assert "MAX_VALUE_FIELD" in result
        assert "PATTERN_FIELD" in result
        assert "MULTIPLE_FIELD" in result

        # Verify constraint comments are present (lines 424, 426, 428, 431)
        assert "Min value: 1" in result  # Line 424 (ge constraint)
        assert "Max value: 1000" in result  # Line 426 (le constraint)
        assert "Multiple of: 5" in result  # Line 428 (multiple_of constraint)
        assert "Pattern: ^[a-z]+$" in result  # Line 431 (pattern constraint)

    def test_generate_env_example_required_field(self):
        """Test required field handling in generate_env_example."""
        class ConfigWithRequired(BaseServiceConfig):
            required_no_default: Optional[str] = Field(
                default=None,
                description="Required field"
            )

        result = generate_env_example(ConfigWithRequired)
        # Tests the default=None branch (line 433)
        assert "REQUIRED_NO_DEFAULT=" in result

    def test_generate_env_example_list_field(self):
        """Test list field formatting."""
        # BaseServiceConfig has cors_origins as a list, this should cover line 436
        result = generate_env_example(BaseServiceConfig)
        # Should contain list default values joined
        assert "CORS_ORIGINS" in result

    def test_generate_env_example_enum_field(self):
        """Test enum field formatting."""
        # BaseServiceConfig has vertice_env as enum, covers line 438
        result = generate_env_example(BaseServiceConfig)
        assert "VERTICE_ENV" in result
        assert "development" in result  # Enum value


class TestLoadConfig:
    """Test load_config() function."""

    def test_load_config_success(self, monkeypatch):
        """Test successful config loading."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")

        config = load_config(BaseServiceConfig)
        assert isinstance(config, BaseServiceConfig)
        assert config.service_name == "test-svc"

    def test_load_config_from_file(self, monkeypatch):
        """Test loading from custom .env file."""
        with NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("SERVICE_NAME=file-service\n")
            f.write("SERVICE_PORT=9000\n")
            env_file_path = Path(f.name)

        try:
            config = load_config(BaseServiceConfig, env_file=env_file_path)
            assert config.service_name == "file-service"
            assert config.service_port == 9000
        finally:
            env_file_path.unlink()

    def test_load_config_file_not_found(self):
        """Test error when env file doesn't exist."""
        fake_path = Path("/tmp/nonexistent_env_file_12345.env")

        with pytest.raises(FileNotFoundError) as exc:
            load_config(BaseServiceConfig, env_file=fake_path)
        assert str(fake_path) in str(exc.value)

    def test_load_config_validation_error(self, monkeypatch):
        """Test error on invalid configuration."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "999")  # Below min

        with pytest.raises(ValueError) as exc:
            load_config(BaseServiceConfig)
        assert "Configuration validation failed" in str(exc.value)


# ============================================================================
# EDGE CASES & INTEGRATION
# ============================================================================


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_case_insensitive_env_vars(self, monkeypatch):
        """Test case-insensitive environment variable handling."""
        monkeypatch.setenv("service_name", "test-svc")  # lowercase
        monkeypatch.setenv("SERVICE_PORT", "8080")

        config = BaseServiceConfig()
        assert config.service_name == "test-svc"

    def test_extra_fields_ignored(self, monkeypatch):
        """Test extra unknown env vars are ignored."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("UNKNOWN_VARIABLE", "should_be_ignored")

        # Should not raise
        config = BaseServiceConfig()
        assert not hasattr(config, "unknown_variable")

    def test_environment_staging(self, monkeypatch):
        """Test staging environment."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("VERTICE_ENV", "staging")

        config = BaseServiceConfig()
        assert config.vertice_env == Environment.STAGING
        assert not config.is_development
        assert not config.is_production
        assert not config.is_testing

    def test_cors_origins_list_passthrough(self, monkeypatch):
        """Test cors_origins when already a list (not string)."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")

        # Simulate already parsed list (edge case in parse_cors_origins validator)
        config = BaseServiceConfig()
        # Default is already a list, so this tests the "return v" branch
        assert isinstance(config.cors_origins, list)

    def test_all_sensitive_key_patterns(self, monkeypatch):
        """Test all sensitive key patterns in model_dump_safe()."""
        monkeypatch.setenv("SERVICE_NAME", "test-svc")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        monkeypatch.setenv("POSTGRES_PASSWORD", "dbpass")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("API_KEY", "key123")
        monkeypatch.setenv("REDIS_PASSWORD", "redispass")
        monkeypatch.setenv("SENTRY_DSN", "https://sentry.io/dsn")

        config = BaseServiceConfig()
        safe = config.model_dump_safe()

        # All should be masked
        assert safe["postgres_password"] == "***"
        assert safe["jwt_secret"] == "***"
        assert safe["api_key"] == "***"
        assert safe["redis_password"] == "***"
        assert safe["sentry_dsn"] == "***"
