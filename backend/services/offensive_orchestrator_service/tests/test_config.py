"""
Tests for configuration management.

Covers:
- Configuration loading
- Environment variable parsing
- Default values
- Configuration validation
- Singleton pattern
"""

import os
import pytest
from unittest.mock import patch

from config import (
    DatabaseConfig,
    VectorDBConfig,
    LLMConfig,
    HOTLConfig,
    ServiceConfig,
    get_config,
)


@pytest.mark.unit
class TestDatabaseConfig:
    """Test DatabaseConfig dataclass."""

    def test_create_database_config_defaults(self):
        """Test creating database config with environment defaults."""
        with patch.dict(os.environ, {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_pass",
            "POSTGRES_DB": "test_db",
        }):
            config = DatabaseConfig()

            assert config.host == "localhost"
            assert config.port == 5432
            assert config.user == "test_user"
            assert config.password == "test_pass"
            assert config.database == "test_db"
            assert config.pool_size == 10  # Default

    def test_database_config_connection_string(self):
        """Test connection string generation."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="admin",
            password="secret",
            database="mydb",
        )

        conn_str = config.connection_string
        assert "postgresql+psycopg2://" in conn_str
        assert "admin:secret" in conn_str
        assert "@localhost:5432/mydb" in conn_str

    def test_database_config_custom_pool_size(self):
        """Test custom pool size configuration."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="user",
            password="pass",
            database="db",
            pool_size=20,
        )

        assert config.pool_size == 20


@pytest.mark.unit
class TestVectorDBConfig:
    """Test VectorDBConfig dataclass."""

    def test_create_vector_db_config_defaults(self):
        """Test creating vector DB config with defaults."""
        with patch.dict(os.environ, {
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333",
        }):
            config = VectorDBConfig()

            assert config.host == "localhost"
            assert config.port == 6333
            assert config.collection_name == "attack_memory"  # Correct default
            assert config.api_key is None

    def test_vector_db_config_with_api_key(self):
        """Test vector DB config with API key."""
        config = VectorDBConfig(
            host="qdrant.cloud",
            port=6334,
            collection_name="prod_campaigns",
            api_key="secret_key_123",
        )

        assert config.host == "qdrant.cloud"
        assert config.api_key == "secret_key_123"

    def test_vector_db_config_grpc_url(self):
        """Test vector DB gRPC URL generation."""
        config = VectorDBConfig(
            host="qdrant.example.com",
            port=6334,
        )

        grpc_url = config.grpc_url
        assert grpc_url == "http://qdrant.example.com:6334"


@pytest.mark.unit
class TestLLMConfig:
    """Test LLMConfig dataclass."""

    def test_create_llm_config_defaults(self):
        """Test creating LLM config with defaults."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "GEMINI_MODEL": "gemini-1.5-pro",
        }):
            config = LLMConfig()

            assert config.api_key == "test_key"
            assert config.model == "gemini-1.5-pro"
            assert config.temperature == 0.7  # Default
            assert config.max_tokens == 4096  # Correct default
            assert config.timeout_seconds == 60  # Correct field name and default

    def test_llm_config_custom_temperature(self):
        """Test LLM config with custom temperature."""
        config = LLMConfig(
            api_key="key",
            model="gemini-1.5-pro",
            temperature=0.3,
        )

        assert config.temperature == 0.3

    def test_llm_config_custom_max_tokens(self):
        """Test LLM config with custom max tokens."""
        config = LLMConfig(
            api_key="key",
            model="gemini-1.5-pro",
            max_tokens=16384,
        )

        assert config.max_tokens == 16384


@pytest.mark.unit
class TestHOTLConfig:
    """Test HOTLConfig dataclass."""

    def test_create_hotl_config_defaults(self):
        """Test creating HOTL config with defaults."""
        with patch.dict(os.environ, {
            "HOTL_ENABLED": "true",
            "HOTL_TIMEOUT": "300",
        }):
            config = HOTLConfig()

            assert config.enabled is True
            assert config.approval_timeout_seconds == 300
            assert config.auto_approve_low_risk is False  # Correct default (safe default)
            assert "/hotl" in config.audit_log_path or "audit.log" in config.audit_log_path

    def test_hotl_config_disabled(self):
        """Test HOTL config when disabled."""
        config = HOTLConfig(
            enabled=False,
            approval_timeout_seconds=180,
            auto_approve_low_risk=False,
        )

        assert config.enabled is False
        assert config.auto_approve_low_risk is False

    def test_hotl_config_custom_timeout(self):
        """Test HOTL config with custom timeout."""
        config = HOTLConfig(
            enabled=True,
            approval_timeout_seconds=600,
        )

        assert config.approval_timeout_seconds == 600


@pytest.mark.unit
class TestServiceConfig:
    """Test main ServiceConfig dataclass."""

    def test_create_service_config_with_all_components(
        self,
        test_database_config,
        test_vector_db_config,
        test_llm_config,
        test_hotl_config,
    ):
        """Test creating service config with all components."""
        config = ServiceConfig(
            host="localhost",
            port=8090,
            debug=True,
            log_level="DEBUG",
            database=test_database_config,
            vectordb=test_vector_db_config,
            llm=test_llm_config,
            hotl=test_hotl_config,
        )

        assert config.debug is True
        assert config.port == 8090
        assert config.database == test_database_config
        assert config.vectordb == test_vector_db_config
        assert config.llm == test_llm_config
        assert config.hotl == test_hotl_config

    def test_service_config_defaults(self):
        """Test service config with default values."""
        with patch.dict(os.environ, {
            "SERVICE_HOST": "0.0.0.0",
            "SERVICE_PORT": "8080",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
        }, clear=False):
            config = ServiceConfig()

            assert config.host == "0.0.0.0"
            assert config.port == 8080
            assert config.debug is False
            assert config.log_level == "INFO"


@pytest.mark.unit
class TestGetConfig:
    """Test get_config singleton function."""

    def test_get_config_returns_service_config(self):
        """Test get_config returns ServiceConfig instance."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "POSTGRES_PASSWORD": "test_pass",
        }, clear=False):
            config = get_config()

            assert isinstance(config, ServiceConfig)
            assert hasattr(config, "database")
            assert hasattr(config, "vectordb")
            assert hasattr(config, "llm")
            assert hasattr(config, "hotl")

    def test_get_config_is_singleton(self):
        """Test get_config returns same instance (singleton)."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "POSTGRES_PASSWORD": "test_pass",
        }, clear=False):
            config1 = get_config()
            config2 = get_config()

            assert config1 is config2

    def test_config_has_all_required_attributes(self):
        """Test config has all required attributes."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "POSTGRES_PASSWORD": "test_pass",
        }, clear=False):
            config = get_config()

        # Main config attributes (ServiceConfig fields)
        assert hasattr(config, "host")
        assert hasattr(config, "port")
        assert hasattr(config, "debug")
        assert hasattr(config, "log_level")

        # Database config
        assert hasattr(config.database, "host")
        assert hasattr(config.database, "port")
        assert hasattr(config.database, "connection_string")

        # Vector DB config (field name is 'vectordb' not 'vector_db')
        assert hasattr(config.vectordb, "host")
        assert hasattr(config.vectordb, "port")
        assert hasattr(config.vectordb, "collection_name")

        # LLM config
        assert hasattr(config.llm, "api_key")
        assert hasattr(config.llm, "model")
        assert hasattr(config.llm, "temperature")

        # HOTL config
        assert hasattr(config.hotl, "enabled")
        assert hasattr(config.hotl, "approval_timeout_seconds")


@pytest.mark.unit
class TestLoadConfig:
    """Test load_config validation function."""

    def test_load_config_missing_api_key(self):
        """Test load_config fails without API key."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "",  # Empty
            "POSTGRES_PASSWORD": "test_pass",
        }, clear=False):
            with pytest.raises(ValueError) as exc_info:
                from config import load_config
                load_config()

            assert "GEMINI_API_KEY" in str(exc_info.value)

    def test_load_config_missing_db_password(self):
        """Test load_config fails without database password."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "POSTGRES_PASSWORD": "",  # Empty
        }, clear=False):
            with pytest.raises(ValueError) as exc_info:
                from config import load_config
                load_config()

            assert "POSTGRES_PASSWORD" in str(exc_info.value)


@pytest.mark.unit
class TestConfigIntegration:
    """Test configuration integration scenarios."""

    def test_service_config_for_development(self):
        """Test configuration for development environment."""
        with patch.dict(os.environ, {
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
        }, clear=False):
            config = ServiceConfig()

            assert config.debug is True
            assert config.log_level == "DEBUG"

    def test_service_config_for_production(self):
        """Test configuration for production environment."""
        with patch.dict(os.environ, {
            "DEBUG": "false",
            "SERVICE_HOST": "0.0.0.0",
            "LOG_LEVEL": "INFO",
        }, clear=False):
            config = ServiceConfig()

            assert config.debug is False
            assert config.host == "0.0.0.0"
            assert config.log_level == "INFO"

    def test_service_config_port_range(self):
        """Test port configuration."""
        # Valid port
        with patch.dict(os.environ, {"SERVICE_PORT": "8080"}, clear=False):
            config = ServiceConfig()
            assert config.port == 8080

        # Edge cases
        with patch.dict(os.environ, {"SERVICE_PORT": "1"}, clear=False):
            config_low = ServiceConfig()
            assert config_low.port == 1

        with patch.dict(os.environ, {"SERVICE_PORT": "65535"}, clear=False):
            config_high = ServiceConfig()
            assert config_high.port == 65535
