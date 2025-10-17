"""
Testes para shared.base_config
Coverage target: 100% ABSOLUTO
"""
import os
import pytest
from pathlib import Path
from typing import Optional
from pydantic import Field, ValidationError

from backend.shared.base_config import (
    BaseServiceConfig,
    Environment,
    generate_env_example,
    load_config,
)


class TestEnvironmentEnum:
    """Test Environment enum"""
    
    def test_environment_values(self):
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"
    
    def test_environment_is_string_enum(self):
        """Test that Environment extends str"""
        assert isinstance(Environment.PRODUCTION, str)
        assert Environment.PRODUCTION == "production"


class TestBaseServiceConfig:
    """Test BaseServiceConfig class"""
    
    def test_minimal_config(self, monkeypatch):
        """Test config with minimal required fields"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        assert config.service_name == "test-service"
        assert config.service_port == 8000
        assert config.vertice_env == Environment.DEVELOPMENT  # Default
    
    def test_full_config(self, monkeypatch):
        """Test config with all fields populated"""
        monkeypatch.setenv("VERTICE_ENV", "production")
        monkeypatch.setenv("SERVICE_NAME", "my-service")
        monkeypatch.setenv("SERVICE_PORT", "9000")
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("API_PREFIX", "/api/v2")
        # Use JSON format for list
        monkeypatch.setenv("CORS_ORIGINS", '["https://example.com","https://other.com"]')
        
        config = BaseServiceConfig()
        assert config.vertice_env == Environment.PRODUCTION
        assert config.log_level == "ERROR"
        assert config.debug is True
        assert config.api_prefix == "/api/v2"
        assert len(config.cors_origins) == 2
    
    def test_database_config(self, monkeypatch):
        """Test PostgreSQL configuration"""
        monkeypatch.setenv("SERVICE_NAME", "db-service")
        monkeypatch.setenv("SERVICE_PORT", "8001")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_PORT", "5433")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "pass")
        
        config = BaseServiceConfig()
        assert config.postgres_host == "localhost"
        assert config.postgres_port == 5433
        assert config.postgres_db == "testdb"
    
    def test_redis_config(self, monkeypatch):
        """Test Redis configuration"""
        monkeypatch.setenv("SERVICE_NAME", "redis-service")
        monkeypatch.setenv("SERVICE_PORT", "8002")
        monkeypatch.setenv("REDIS_HOST", "redis.local")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "5")
        monkeypatch.setenv("REDIS_PASSWORD", "redispass")
        
        config = BaseServiceConfig()
        assert config.redis_host == "redis.local"
        assert config.redis_port == 6380
        assert config.redis_db == 5
        assert config.redis_password == "redispass"
    
    def test_security_config(self, monkeypatch):
        """Test security configuration"""
        monkeypatch.setenv("SERVICE_NAME", "secure-service")
        monkeypatch.setenv("SERVICE_PORT", "8003")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)  # Min 32 chars
        monkeypatch.setenv("JWT_ALGORITHM", "RS256")
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "60")
        monkeypatch.setenv("API_KEY", "secret-api-key")
        
        config = BaseServiceConfig()
        assert len(config.jwt_secret) >= 32
        assert config.jwt_algorithm == "RS256"
        assert config.jwt_expiration_minutes == 60
        assert config.api_key == "secret-api-key"
    
    def test_observability_config(self, monkeypatch):
        """Test observability configuration"""
        monkeypatch.setenv("SERVICE_NAME", "obs-service")
        monkeypatch.setenv("SERVICE_PORT", "8004")
        monkeypatch.setenv("ENABLE_METRICS", "false")
        monkeypatch.setenv("ENABLE_TRACING", "true")
        monkeypatch.setenv("SENTRY_DSN", "https://sentry.io/123")
        
        config = BaseServiceConfig()
        assert config.enable_metrics is False
        assert config.enable_tracing is True
        assert config.sentry_dsn == "https://sentry.io/123"


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_service_name_valid_pattern(self, monkeypatch):
        """Test valid service_name patterns"""
        monkeypatch.setenv("SERVICE_NAME", "valid-service-123")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        assert config.service_name == "valid-service-123"
    
    def test_port_valid_range(self, monkeypatch):
        """Test valid port range"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8080")
        
        config = BaseServiceConfig()
        assert config.service_port == 8080
    
    def test_redis_db_valid_range(self, monkeypatch):
        """Test valid redis_db range"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("REDIS_DB", "10")
        
        config = BaseServiceConfig()
        assert config.redis_db == 10
    
    def test_jwt_secret_valid_length(self, monkeypatch):
        """Test valid jwt_secret length"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        
        config = BaseServiceConfig()
        assert len(config.jwt_secret) == 32
    
    def test_jwt_expiration_valid_range(self, monkeypatch):
        """Test valid jwt_expiration_minutes range"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "120")
        
        config = BaseServiceConfig()
        assert config.jwt_expiration_minutes == 120


class TestLogLevelValidator:
    """Test log_level validator"""
    
    @pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    def test_valid_log_levels(self, level, monkeypatch):
        """Test all valid log levels"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("LOG_LEVEL", level)
        
        config = BaseServiceConfig()
        assert config.log_level == level.upper()
    
    def test_log_level_case_insensitive(self, monkeypatch):
        """Test log_level is converted to uppercase"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("LOG_LEVEL", "info")
        
        config = BaseServiceConfig()
        assert config.log_level == "INFO"
    
    def test_log_level_invalid_raises_error(self, monkeypatch):
        """Test invalid log level raises error"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        
        with pytest.raises(ValidationError):
            BaseServiceConfig()


class TestCorsOriginsParser:
    """Test CORS origins parser"""
    
    def test_cors_origins_as_json_string(self, monkeypatch):
        """Test parsing JSON array string"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("CORS_ORIGINS", '["http://a.com","http://b.com"]')
        
        config = BaseServiceConfig()
        assert len(config.cors_origins) == 2
        assert "http://a.com" in config.cors_origins
    
    def test_cors_origins_default(self, monkeypatch):
        """Test default CORS origins"""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        # Should have default values
        assert len(config.cors_origins) >= 2
        assert "http://localhost:3000" in config.cors_origins
    
    def test_parse_cors_origins_validator_with_string(self):
        """Test parse_cors_origins validator directly with comma-separated string"""
        result = BaseServiceConfig.parse_cors_origins("http://a.com,http://b.com,http://c.com")
        assert len(result) == 3
        assert "http://a.com" in result
    
    def test_parse_cors_origins_validator_with_spaces(self):
        """Test parse_cors_origins validator with whitespace"""
        result = BaseServiceConfig.parse_cors_origins("http://a.com , http://b.com , http://c.com")
        assert len(result) == 3
        assert "http://a.com" in result
    
    def test_parse_cors_origins_validator_empty_values(self):
        """Test parse_cors_origins validator filters empty values"""
        result = BaseServiceConfig.parse_cors_origins("http://a.com,,http://b.com")
        # Empty strings should be filtered out
        assert len(result) == 2
    
    def test_parse_cors_origins_validator_with_list(self):
        """Test parse_cors_origins validator with list input"""
        input_list = ["http://a.com", "http://b.com"]
        result = BaseServiceConfig.parse_cors_origins(input_list)
        assert result == input_list


class TestPropertyMethods:
    """Test property methods"""
    
    def test_is_development(self, monkeypatch):
        """Test is_development property"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("VERTICE_ENV", "development")
        
        config = BaseServiceConfig()
        assert config.is_development is True
        assert config.is_production is False
        assert config.is_testing is False
    
    def test_is_production(self, monkeypatch):
        """Test is_production property"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("VERTICE_ENV", "production")
        
        config = BaseServiceConfig()
        assert config.is_production is True
        assert config.is_development is False
        assert config.is_testing is False
    
    def test_is_testing(self, monkeypatch):
        """Test is_testing property"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("VERTICE_ENV", "testing")
        
        config = BaseServiceConfig()
        assert config.is_testing is True
        assert config.is_development is False
        assert config.is_production is False
    
    def test_postgres_url_complete(self, monkeypatch):
        """Test postgres_url with all fields set"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_HOST", "dbhost")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("POSTGRES_DB", "mydb")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "pass")
        
        config = BaseServiceConfig()
        assert config.postgres_url == "postgresql://user:pass@dbhost:5432/mydb"
    
    def test_postgres_url_incomplete(self, monkeypatch):
        """Test postgres_url returns None when fields missing"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_HOST", "dbhost")
        # Missing other fields
        
        config = BaseServiceConfig()
        assert config.postgres_url is None
    
    def test_redis_url_with_password(self, monkeypatch):
        """Test redis_url with password"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "2")
        monkeypatch.setenv("REDIS_PASSWORD", "secret")
        
        config = BaseServiceConfig()
        assert config.redis_url == "redis://:secret@redishost:6379/2"
    
    def test_redis_url_without_password(self, monkeypatch):
        """Test redis_url without password"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "0")
        
        config = BaseServiceConfig()
        assert config.redis_url == "redis://redishost:6379/0"
    
    def test_redis_url_no_host(self, monkeypatch):
        """Test redis_url returns None when host missing"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        assert config.redis_url is None


class TestModelDumpSafe:
    """Test model_dump_safe method"""
    
    def test_model_dump_safe_masks_secrets(self, monkeypatch):
        """Test that sensitive fields are masked"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_PASSWORD", "dbpassword")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("API_KEY", "secret-key")
        monkeypatch.setenv("REDIS_PASSWORD", "redispass")
        
        config = BaseServiceConfig()
        safe_data = config.model_dump_safe()
        
        # Sensitive fields should be masked
        assert safe_data["postgres_password"] == "***"
        assert safe_data["jwt_secret"] == "***"
        assert safe_data["api_key"] == "***"
        assert safe_data["redis_password"] == "***"
    
    def test_model_dump_safe_preserves_non_secrets(self, monkeypatch):
        """Test that non-sensitive fields are preserved"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        safe_data = config.model_dump_safe()
        
        assert safe_data["service_name"] == "test"
        assert safe_data["service_port"] == 8000
    
    def test_model_dump_safe_none_values(self, monkeypatch):
        """Test that None sensitive fields stay None"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        safe_data = config.model_dump_safe()
        
        # Fields not set should be None
        assert safe_data["postgres_password"] is None
        assert safe_data["api_key"] is None


class TestValidateRequiredVars:
    """Test validate_required_vars method"""
    
    def test_validate_required_vars_all_present(self, monkeypatch):
        """Test validation passes when all vars present"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        
        config = BaseServiceConfig()
        # Should not raise
        config.validate_required_vars("postgres_host")
    
    def test_validate_required_vars_missing(self, monkeypatch):
        """Test validation fails when var missing"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        with pytest.raises(ValueError) as exc_info:
            config.validate_required_vars("postgres_host")
        
        assert "POSTGRES_HOST" in str(exc_info.value)
    
    def test_validate_required_vars_empty_string(self, monkeypatch):
        """Test validation fails for empty strings"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        monkeypatch.setenv("POSTGRES_HOST", "   ")  # Whitespace only
        
        config = BaseServiceConfig()
        with pytest.raises(ValueError) as exc_info:
            config.validate_required_vars("postgres_host")
        
        assert "POSTGRES_HOST" in str(exc_info.value)
    
    def test_validate_required_vars_multiple(self, monkeypatch):
        """Test validation with multiple vars"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = BaseServiceConfig()
        with pytest.raises(ValueError) as exc_info:
            config.validate_required_vars("postgres_host", "redis_host")
        
        error_msg = str(exc_info.value)
        assert "POSTGRES_HOST" in error_msg
        assert "REDIS_HOST" in error_msg


class TestGenerateEnvExample:
    """Test generate_env_example function"""
    
    def test_generate_env_example_basic(self):
        """Test basic env example generation"""
        result = generate_env_example(BaseServiceConfig)
        
        # Should contain header
        assert "Environment Variables" in result
        
        # Should contain field descriptions
        assert "SERVICE_NAME" in result
        assert "SERVICE_PORT" in result
        
        # Should have comments
        assert "#" in result
    
    def test_generate_env_example_with_defaults(self):
        """Test that defaults are included"""
        result = generate_env_example(BaseServiceConfig)
        
        # Should show default values
        assert "LOG_LEVEL=INFO" in result
        assert "DEBUG=False" in result
    
    def test_generate_env_example_required_fields(self):
        """Test that required fields have empty values"""
        result = generate_env_example(BaseServiceConfig)
        
        # Required fields should be empty
        assert "SERVICE_NAME=" in result
        assert "SERVICE_PORT=" in result
    
    def test_generate_env_example_with_custom_config(self):
        """Test with custom config that has MultipleOf constraint"""
        from pydantic import Field
        from typing import Annotated
        
        class CustomConfig(BaseServiceConfig):
            batch_size: Annotated[int, Field(default=100, multiple_of=10)] = 100
        
        result = generate_env_example(CustomConfig)
        # Should generate without errors
        assert "BATCH_SIZE" in result or "batch_size" in result


class TestLoadConfig:
    """Test load_config helper function"""
    
    def test_load_config_success(self, tmp_path, monkeypatch):
        """Test successful config loading"""
        env_file = tmp_path / ".env"
        env_file.write_text("SERVICE_NAME=test\nSERVICE_PORT=8000\n")
        
        config = load_config(BaseServiceConfig, env_file)
        assert config.service_name == "test"
        assert config.service_port == 8000
    
    def test_load_config_file_not_found(self, tmp_path):
        """Test error when env file doesn't exist"""
        non_existent = tmp_path / "missing.env"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(BaseServiceConfig, non_existent)
        
        assert "missing.env" in str(exc_info.value)
    
    def test_load_config_validation_error(self, tmp_path):
        """Test error on invalid configuration"""
        env_file = tmp_path / ".env"
        env_file.write_text("SERVICE_NAME=ab\nSERVICE_PORT=8000\n")  # Too short
        
        with pytest.raises(ValueError) as exc_info:
            load_config(BaseServiceConfig, env_file)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_load_config_no_env_file(self, monkeypatch):
        """Test loading without specifying env file"""
        monkeypatch.setenv("SERVICE_NAME", "test")
        monkeypatch.setenv("SERVICE_PORT", "8000")
        
        config = load_config(BaseServiceConfig)
        assert config.service_name == "test"


class TestCustomServiceConfig:
    """Test custom service configs extending BaseServiceConfig"""
    
    def test_custom_config_inheritance(self, monkeypatch):
        """Test that custom configs can extend BaseServiceConfig"""
        
        class CustomConfig(BaseServiceConfig):
            custom_field: str = Field(default="custom_value")
        
        monkeypatch.setenv("SERVICE_NAME", "custom")
        monkeypatch.setenv("SERVICE_PORT", "9000")
        
        config = CustomConfig()
        assert config.service_name == "custom"
        assert config.custom_field == "custom_value"
    
    def test_custom_config_override(self, monkeypatch):
        """Test overriding base config fields"""
        
        class CustomConfig(BaseServiceConfig):
            log_level: str = Field(default="DEBUG")
        
        monkeypatch.setenv("SERVICE_NAME", "custom")
        monkeypatch.setenv("SERVICE_PORT", "9000")
        
        config = CustomConfig()
        assert config.log_level == "DEBUG"
