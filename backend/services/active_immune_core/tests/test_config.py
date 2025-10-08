"""Configuration tests"""

import pytest
from pydantic import ValidationError

from active_immune_core.config import Settings


class TestSettings:
    """Test Settings configuration"""

    def test_settings_default_values(self):
        """Test that settings have sensible defaults"""
        settings = Settings()

        assert settings.service_port == 8200
        assert settings.log_level == "INFO"
        assert settings.baseline_active_percentage == 0.15
        assert settings.max_agent_lifespan_hours == 24

    def test_settings_postgres_url_generation(self):
        """Test PostgreSQL URL generation"""
        settings = Settings(
            postgres_host="testhost",
            postgres_port=5433,
            postgres_db="testdb",
            postgres_user="testuser",
            postgres_password="testpass",
        )

        expected_url = "postgresql+asyncpg://testuser:testpass@testhost:5433/testdb"
        assert settings.postgres_url == expected_url

    def test_settings_log_level_validation(self):
        """Test log level validation"""
        # Valid levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level

        # Invalid level
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")

    def test_settings_port_validation(self):
        """Test port number validation"""
        # Valid port
        settings = Settings(service_port=8200)
        assert settings.service_port == 8200

        # Invalid port (too low)
        with pytest.raises(ValidationError):
            Settings(service_port=80)  # < 1024

        # Invalid port (too high)
        with pytest.raises(ValidationError):
            Settings(service_port=70000)  # > 65535

    def test_settings_percentage_validation(self):
        """Test percentage validation (0-1)"""
        # Valid percentage
        settings = Settings(baseline_active_percentage=0.15)
        assert settings.baseline_active_percentage == 0.15

        # Invalid percentage (negative)
        with pytest.raises(ValidationError):
            Settings(baseline_active_percentage=-0.1)

        # Invalid percentage (> 1)
        with pytest.raises(ValidationError):
            Settings(baseline_active_percentage=1.5)

    def test_settings_kafka_acks_validation(self):
        """Test Kafka acks validation"""
        # Valid acks
        for acks in ["all", "1", "0"]:
            settings = Settings(kafka_acks=acks)
            assert settings.kafka_acks == acks

        # Invalid acks
        with pytest.raises(ValidationError):
            Settings(kafka_acks="invalid")
