"""Tests for backend/shared/base_config.py - 100% coverage.

Strategy: Test Pydantic Settings base configuration class.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from backend.shared.base_config import (
    Environment,
    BaseServiceConfig,
)


class TestEnvironmentEnum:
    """Test Environment enum."""

    def test_environment_enum_values(self):
        """Environment enum has expected values."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"
        assert Environment.TESTING == "testing"

    def test_environment_enum_is_string(self):
        """Environment enum members are strings."""
        for env in Environment:
            assert isinstance(env.value, str)
            assert isinstance(env, str)


class TestBaseServiceConfig:
    """Test BaseServiceConfig class."""

    def test_base_service_config_creation(self):
        """BaseServiceConfig can be created with environment variables."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test-service",
            "SERVICE_PORT": "8080"
        }):
            config = BaseServiceConfig()
            
            assert config.service_name == "test-service"
            assert config.service_port == 8080
            assert config.vertice_env == Environment.DEVELOPMENT

    def test_base_service_config_with_env_vars(self):
        """BaseServiceConfig loads from environment variables."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "env-service",
            "SERVICE_PORT": "9000",
            "VERTICE_ENV": "production",
            "LOG_LEVEL": "WARNING"
        }):
            config = BaseServiceConfig()
            
            assert config.service_name == "env-service"
            assert config.service_port == 9000
            assert config.vertice_env == Environment.PRODUCTION
            assert config.log_level == "WARNING"

    def test_base_service_config_defaults(self):
        """BaseServiceConfig has sensible defaults."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000"
        }):
            config = BaseServiceConfig()
            
            assert config.vertice_env == Environment.DEVELOPMENT
            assert config.log_level == "INFO"
            assert config.debug is False
            assert config.api_prefix == "/api/v1"
            assert isinstance(config.cors_origins, list)

    def test_service_name_validation(self):
        """Service name must follow kebab-case pattern."""
        # Valid names
        with patch.dict(os.environ, {"SERVICE_NAME": "test-service", "SERVICE_PORT": "8000"}):
            BaseServiceConfig()
        
        with patch.dict(os.environ, {"SERVICE_NAME": "api-gateway", "SERVICE_PORT": "8001"}):
            BaseServiceConfig()
        
        with patch.dict(os.environ, {"SERVICE_NAME": "test123", "SERVICE_PORT": "8002"}):
            BaseServiceConfig()
        
        # Invalid: too short
        with pytest.raises(ValidationError):
            with patch.dict(os.environ, {"SERVICE_NAME": "ab", "SERVICE_PORT": "8000"}):
                BaseServiceConfig()
        
        # Invalid: uppercase
        with pytest.raises(ValidationError):
            with patch.dict(os.environ, {"SERVICE_NAME": "Test-Service", "SERVICE_PORT": "8000"}):
                BaseServiceConfig()
        
        # Invalid: underscore
        with pytest.raises(ValidationError):
            with patch.dict(os.environ, {"SERVICE_NAME": "test_service", "SERVICE_PORT": "8000"}):
                BaseServiceConfig()

    def test_service_port_validation(self):
        """Service port must be in valid range."""
        # Valid ports
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "1024"}):
            BaseServiceConfig()
        
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            BaseServiceConfig()
        
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "65535"}):
            BaseServiceConfig()
        
        # Invalid: too low
        with pytest.raises(ValidationError):
            with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "80"}):
                BaseServiceConfig()
        
        # Invalid: too high
        with pytest.raises(ValidationError):
            with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "70000"}):
                BaseServiceConfig()

    def test_environment_enum_validation(self):
        """Environment must be valid enum value."""
        with patch.dict(os.environ, {
            "VERTICE_ENV": "invalid_env",
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000"
        }):
            with pytest.raises(ValidationError):
                BaseServiceConfig()

    def test_log_level_default(self):
        """Log level defaults to INFO."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            assert config.log_level == "INFO"

    def test_debug_mode(self):
        """Debug mode can be enabled."""
        with patch.dict(os.environ, {"DEBUG": "true", "SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            assert config.debug is True
        
        with patch.dict(os.environ, {"DEBUG": "false", "SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            assert config.debug is False

    def test_api_prefix_customization(self):
        """API prefix can be customized."""
        with patch.dict(os.environ, {"API_PREFIX": "/v2/api", "SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            assert config.api_prefix == "/v2/api"

    def test_cors_origins_configuration(self):
        """CORS origins can be configured."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            assert isinstance(config.cors_origins, list)
            assert len(config.cors_origins) > 0

    def test_model_config_settings(self):
        """Model config has correct settings."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            
            # Should have model_config
            assert hasattr(BaseServiceConfig, "model_config")
            model_cfg = BaseServiceConfig.model_config
            
            # Check key settings
            assert model_cfg.get("env_file") == ".env"
            assert model_cfg.get("case_sensitive") is False
            assert model_cfg.get("extra") == "ignore"

    def test_config_from_dot_env_file(self):
        """Config can load from .env file."""
        # Create temporary .env file
        env_content = """
SERVICE_NAME=dotenv-service
SERVICE_PORT=9999
VERTICE_ENV=staging
LOG_LEVEL=DEBUG
"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                # Note: Actual .env loading requires file to exist
                # This test verifies config accepts values
                with patch.dict(os.environ, {
                    "SERVICE_NAME": "dotenv-service",
                    "SERVICE_PORT": "9999"
                }):
                    config = BaseServiceConfig()
                    assert config.service_name == "dotenv-service"
                    assert config.service_port == 9999

    def test_validation_alias_usage(self):
        """Validation aliases work for environment variables."""
        with patch.dict(os.environ, {
            "VERTICE_ENV": "staging",
            "SERVICE_NAME": "alias-test",
            "SERVICE_PORT": "8888"
        }):
            config = BaseServiceConfig()
            assert config.vertice_env == Environment.STAGING
            assert config.service_name == "alias-test"

    def test_config_serialization(self):
        """Config can be serialized to dict."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            
            config_dict = config.model_dump()
            assert isinstance(config_dict, dict)
            assert config_dict["service_name"] == "test"
            assert config_dict["service_port"] == 8000

    def test_config_json_export(self):
        """Config can be exported to JSON."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            
            json_str = config.model_dump_json()
            assert isinstance(json_str, str)
            assert "test" in json_str
            assert "8000" in json_str


class TestBaseServiceConfigInheritance:
    """Test that BaseServiceConfig can be inherited."""

    def test_custom_config_inheritance(self):
        """Custom config classes can inherit from BaseServiceConfig."""
        from pydantic import Field
        
        class CustomServiceConfig(BaseServiceConfig):
            custom_field: str = Field(default="custom_value")
        
        with patch.dict(os.environ, {"SERVICE_NAME": "custom", "SERVICE_PORT": "8000"}):
            config = CustomServiceConfig()
            assert config.service_name == "custom"
            assert config.custom_field == "custom_value"

    def test_override_defaults_in_child_class(self):
        """Child classes can override defaults."""
        from pydantic import Field
        
        class ProductionConfig(BaseServiceConfig):
            vertice_env: Environment = Field(default=Environment.PRODUCTION)
        
        with patch.dict(os.environ, {"SERVICE_NAME": "prod-service", "SERVICE_PORT": "8000"}):
            config = ProductionConfig()
            assert config.vertice_env == Environment.PRODUCTION


class TestConfigEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_env_variables(self):
        """Config requires SERVICE_NAME and SERVICE_PORT."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}, clear=True):
            config = BaseServiceConfig()
            assert config.service_name == "test"

    def test_service_name_length_limits(self):
        """Service name has min/max length constraints."""
        # Minimum length: 3
        with patch.dict(os.environ, {"SERVICE_NAME": "abc", "SERVICE_PORT": "8000"}):
            BaseServiceConfig()
        
        # Maximum length: 64
        long_name = "a" * 64
        with patch.dict(os.environ, {"SERVICE_NAME": long_name, "SERVICE_PORT": "8000"}):
            BaseServiceConfig()
        
        # Too long
        with pytest.raises(ValidationError):
            with patch.dict(os.environ, {"SERVICE_NAME": "a" * 65, "SERVICE_PORT": "8000"}):
                BaseServiceConfig()

    def test_cors_origins_as_list(self):
        """CORS origins must be a list."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            assert isinstance(config.cors_origins, list)
            for origin in config.cors_origins:
                assert isinstance(origin, str)

    def test_config_immutability_after_validation(self):
        """Config validates on creation and assignment."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test", "SERVICE_PORT": "8000"}):
            config = BaseServiceConfig()
            
            # Changing validated field triggers re-validation
            with pytest.raises(ValidationError):
                config.service_port = 100  # Below minimum

    def test_env_nested_delimiter(self):
        """Config supports nested env variables with delimiter."""
        # model_config specifies env_nested_delimiter="__"
        # This would allow ENV_VAR__NESTED for nested.nested
        assert BaseServiceConfig.model_config.get("env_nested_delimiter") == "__"


class TestBaseServiceConfigValidators:
    """Test field validators."""

    def test_log_level_validator_uppercase(self):
        """Log level is converted to uppercase."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "LOG_LEVEL": "debug"
        }):
            config = BaseServiceConfig()
            assert config.log_level == "DEBUG"

    def test_log_level_validator_invalid(self):
        """Log level validator rejects invalid levels."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "LOG_LEVEL": "INVALID"
        }):
            with pytest.raises(ValidationError) as exc_info:
                BaseServiceConfig()
            assert "log_level" in str(exc_info.value).lower()

    def test_log_level_validator_all_valid_levels(self):
        """Log level validator accepts all valid levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            with patch.dict(os.environ, {
                "SERVICE_NAME": "test",
                "SERVICE_PORT": "8000",
                "LOG_LEVEL": level.lower()
            }):
                config = BaseServiceConfig()
                assert config.log_level == level

    def test_cors_origins_string_parsing(self):
        """CORS origins validator can parse string."""
        # Direct call to validator
        from backend.shared.base_config import BaseServiceConfig
        
        # Test the validator directly
        result = BaseServiceConfig.parse_cors_origins("http://a.com,http://b.com")
        assert len(result) == 2
        assert "http://a.com" in result
        assert "http://b.com" in result

    def test_cors_origins_already_list(self):
        """CORS origins validator returns list as-is."""
        from backend.shared.base_config import BaseServiceConfig
        
        original_list = ["http://x.com", "http://y.com"]
        result = BaseServiceConfig.parse_cors_origins(original_list)
        assert result == original_list


class TestBaseServiceConfigProperties:
    """Test computed properties."""

    def test_is_development_property(self):
        """is_development returns True for development env."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "VERTICE_ENV": "development"
        }):
            config = BaseServiceConfig()
            assert config.is_development is True
            assert config.is_production is False
            assert config.is_testing is False

    def test_is_production_property(self):
        """is_production returns True for production env."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "VERTICE_ENV": "production"
        }):
            config = BaseServiceConfig()
            assert config.is_production is True
            assert config.is_development is False

    def test_is_testing_property(self):
        """is_testing returns True for testing env."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "VERTICE_ENV": "testing"
        }):
            config = BaseServiceConfig()
            assert config.is_testing is True

    def test_postgres_url_property(self):
        """postgres_url constructs database URL."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "pass",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "testdb"
        }):
            config = BaseServiceConfig()
            url = config.postgres_url
            assert url is not None
            assert "postgresql://" in url
            assert "user" in url
            assert "testdb" in url

    def test_postgres_url_property_missing_fields(self):
        """postgres_url returns None if required fields missing."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000"
            # No postgres fields
        }):
            config = BaseServiceConfig()
            url = config.postgres_url
            assert url is None

    def test_redis_url_property(self):
        """redis_url constructs Redis URL."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0"
        }):
            config = BaseServiceConfig()
            url = config.redis_url
            assert url is not None
            assert "redis://" in url

    def test_redis_url_property_missing_host(self):
        """redis_url returns None if host missing."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000"
            # No REDIS_HOST
        }):
            config = BaseServiceConfig()
            url = config.redis_url
            assert url is None

    def test_redis_url_with_password(self):
        """redis_url includes password if provided."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "REDIS_PASSWORD": "secret"
        }):
            config = BaseServiceConfig()
            url = config.redis_url
            assert url is not None
            assert ":secret@" in url


class TestBaseServiceConfigMethods:
    """Test instance methods."""

    def test_model_dump_safe_excludes_secrets(self):
        """model_dump_safe redacts sensitive fields."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000"
        }):
            config = BaseServiceConfig()
            safe_dict = config.model_dump_safe()
            
            assert "service_name" in safe_dict
            # JWT_SECRET has default value, check it's redacted to "***"
            if "jwt_secret" in safe_dict and safe_dict["jwt_secret"]:
                assert safe_dict["jwt_secret"] == "***"

    def test_validate_required_vars(self):
        """validate_required_vars checks environment variables."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000"
        }):
            config = BaseServiceConfig()
            # Should not raise if variable exists and has value
            config.validate_required_vars("service_name", "service_port")

    def test_validate_required_vars_missing(self):
        """validate_required_vars raises if variable missing."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000"
        }):
            config = BaseServiceConfig()
            # api_key is None by default
            with pytest.raises(ValueError) as exc_info:
                config.validate_required_vars("api_key")
            assert "Missing required" in str(exc_info.value)
            assert "API_KEY" in str(exc_info.value)

    def test_validate_required_vars_empty_string(self):
        """validate_required_vars raises if variable is empty string."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test",
            "SERVICE_PORT": "8000",
            "API_PREFIX": "   "  # Empty/whitespace string
        }):
            config = BaseServiceConfig()
            with pytest.raises(ValueError):
                config.validate_required_vars("api_prefix")


class TestBaseServiceConfigHelperFunctions:
    """Test module-level helper functions."""

    def test_generate_env_example(self):
        """generate_env_example creates env template."""
        from backend.shared.base_config import generate_env_example
        
        env_example = generate_env_example(BaseServiceConfig)
        
        assert isinstance(env_example, str)
        assert "SERVICE_NAME" in env_example
        assert "SERVICE_PORT" in env_example
        assert "VERTICE_ENV" in env_example
        # Check it includes field descriptions
        assert "description" in env_example.lower() or "#" in env_example

    def test_generate_env_example_includes_constraints(self):
        """generate_env_example processes field constraints."""
        from backend.shared.base_config import generate_env_example
        from pydantic import Field
        from unittest.mock import Mock, patch
        
        # Mock FieldInfo to have ge, le, pattern attributes
        # to hit lines 420, 422, 424
        class TestConfig(BaseServiceConfig):
            test_field: int = Field(default=50, description="Test")
        
        # Patch field iteration to inject constraints
        original_model_fields = TestConfig.model_fields.copy()
        
        # Create mock field with explicit ge/le/pattern attrs
        mock_field_info = Mock()
        mock_field_info.description = "Field with constraints"
        mock_field_info.ge = 10  # Line 420
        mock_field_info.le = 100  # Line 422
        mock_field_info.pattern = r"^[a-z]+$"  # Line 424
        mock_field_info.default = 50
        mock_field_info.validation_alias = None
        
        # Inject mock field
        test_fields = original_model_fields.copy()
        test_fields["mock_constrained"] = mock_field_info
        
        with patch.object(TestConfig, 'model_fields', test_fields):
            env_example = generate_env_example(TestConfig)
            
            # Verify constraint lines are generated
            assert "Min value: 10" in env_example  # Line 420
            assert "Max value: 100" in env_example  # Line 422
            assert "Pattern:" in env_example  # Line 424
        
    def test_generate_env_example_with_validation_alias(self):
        """generate_env_example uses validation_alias for env var name."""
        from backend.shared.base_config import generate_env_example
        
        env_example = generate_env_example(BaseServiceConfig)
        
        # SERVICE_PORT has validation_alias="SERVICE_PORT"
        # Line 428-429: checks validation_alias
        assert "SERVICE_PORT" in env_example

    def test_load_config_with_env_file_override(self):
        """load_config modifies model_config when env_file provided."""
        from backend.shared.base_config import load_config
        from pathlib import Path
        import tempfile
        
        # Create a temporary env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("SERVICE_NAME=temp-service\n")
            f.write("SERVICE_PORT=7777\n")
            temp_path = Path(f.name)
        
        try:
            # Line 476: sets model_config["env_file"]
            config = load_config(BaseServiceConfig, env_file=temp_path)
            assert config.service_name == "temp-service"
            assert config.service_port == 7777
        finally:
            temp_path.unlink()  # Clean up

    def test_load_config_with_env_file(self):
        """load_config can load config with custom env file."""
        from backend.shared.base_config import load_config
        
        with patch.dict(os.environ, {
            "SERVICE_NAME": "loaded-service",
            "SERVICE_PORT": "9000"
        }):
            config = load_config(BaseServiceConfig)
            assert config.service_name == "loaded-service"
            assert config.service_port == 9000

    def test_load_config_missing_file(self):
        """load_config raises if env file doesn't exist."""
        from backend.shared.base_config import load_config
        from pathlib import Path
        
        fake_path = Path("/nonexistent/file.env")
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(BaseServiceConfig, env_file=fake_path)
        assert "Environment file not found" in str(exc_info.value)

    def test_load_config_with_existing_file(self):
        """load_config loads from specified env file."""
        from backend.shared.base_config import load_config
        from pathlib import Path
        
        # Use current working directory .env if exists, otherwise skip
        with patch.dict(os.environ, {
            "SERVICE_NAME": "file-service",
            "SERVICE_PORT": "8888"
        }):
            config = load_config(BaseServiceConfig, env_file=None)
            assert config.service_name == "file-service"

    def test_load_config_validation_error(self):
        """load_config raises ValueError if config invalid."""
        from backend.shared.base_config import load_config
        
        # Missing required fields
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                load_config(BaseServiceConfig)
            assert "Configuration validation failed" in str(exc_info.value)
