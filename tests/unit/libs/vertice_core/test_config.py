"""Tests for vertice_core.config - 100% coverage."""

import pytest
from pydantic import ValidationError
from vertice_core.config import BaseServiceSettings


class TestBaseServiceSettings:
    """Test BaseServiceSettings."""
    
    def test_minimal_config(self):
        """Test minimal configuration."""
        settings = BaseServiceSettings(
            service_name="test-service",
            port=8000,
        )
        assert settings.service_name == "test-service"
        assert settings.port == 8000
        assert settings.service_version == "1.0.0"
        assert settings.environment == "development"
        assert settings.host == "0.0.0.0"
        assert settings.workers == 1
        assert settings.log_level == "INFO"
    
    def test_full_config(self):
        """Test full configuration."""
        settings = BaseServiceSettings(
            service_name="maximus",
            service_version="2.0.0",
            environment="production",
            host="127.0.0.1",
            port=9000,
            workers=4,
            log_level="DEBUG",
            otel_enabled=True,
            otel_endpoint="http://jaeger:4318",
            metrics_enabled=True,
            api_gateway_url="http://gateway:8080",
            api_key="test-key",
            database_url="postgresql://user:pass@localhost/db",
            database_pool_size=20,
            database_max_overflow=30,
            redis_url="redis://localhost:6379",
            redis_db=1,
            cors_origins=["http://localhost:3000", "http://localhost:3001"],
            jwt_secret="secret-key",
        )
        assert settings.service_name == "maximus"
        assert settings.service_version == "2.0.0"
        assert settings.environment == "production"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.workers == 4
        assert settings.log_level == "DEBUG"
        assert settings.otel_enabled is True
        assert settings.otel_endpoint == "http://jaeger:4318"
        assert settings.metrics_enabled is True
        assert settings.api_gateway_url == "http://gateway:8080"
        assert settings.api_key == "test-key"
        assert settings.database_url == "postgresql://user:pass@localhost/db"
        assert settings.database_pool_size == 20
        assert settings.database_max_overflow == 30
        assert settings.redis_url == "redis://localhost:6379"
        assert settings.redis_db == 1
        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:3001"]
        assert settings.jwt_secret == "secret-key"
    
    def test_get_db_url_success(self):
        """Test get_db_url with configured URL."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            database_url="postgresql://localhost/test",
        )
        assert settings.get_db_url() == "postgresql://localhost/test"
    
    def test_get_db_url_not_configured(self):
        """Test get_db_url raises when not configured."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
        )
        with pytest.raises(ValueError, match="database_url not configured"):
            settings.get_db_url()
    
    def test_environment_validation(self):
        """Test environment field validation."""
        # Valid environments
        for env in ["development", "staging", "production"]:
            settings = BaseServiceSettings(
                service_name="test",
                port=8000,
                environment=env,
            )
            assert settings.environment == env
    
    def test_log_level_validation(self):
        """Test log_level field validation."""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = BaseServiceSettings(
                service_name="test",
                port=8000,
                log_level=level,
            )
            assert settings.log_level == level
    
    def test_defaults(self):
        """Test default values."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
        )
        assert settings.service_version == "1.0.0"
        assert settings.environment == "development"
        assert settings.host == "0.0.0.0"
        assert settings.workers == 1
        assert settings.log_level == "INFO"
        assert settings.otel_enabled is True
        assert settings.otel_endpoint == "http://jaeger:4318"
        assert settings.metrics_enabled is True
        assert settings.api_gateway_url == "http://api-gateway:8000"
        assert settings.api_key == ""
        assert settings.database_url is None
        assert settings.database_pool_size == 10
        assert settings.database_max_overflow == 20
        assert settings.redis_url is None
        assert settings.redis_db == 0
        assert settings.cors_origins == ["http://localhost:3000"]
        # JWT secret may come from environment or .env file
        assert isinstance(settings.jwt_secret, str)
    
    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            unknown_field="should be ignored",
        )
        assert settings.service_name == "test"
        assert not hasattr(settings, "unknown_field")
