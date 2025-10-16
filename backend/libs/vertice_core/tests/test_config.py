"""Tests for vertice_core.config module."""

import pytest

from vertice_core.config import BaseServiceSettings


class TestBaseServiceSettings:
    """Tests for BaseServiceSettings."""

    def test_creates_with_required_fields(self) -> None:
        """Test creating settings with required fields."""
        settings = BaseServiceSettings(
            service_name="test_service",
            port=8000,
        )

        assert settings.service_name == "test_service"
        assert settings.port == 8000

    def test_uses_default_values(self) -> None:
        """Test that default values are set."""
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
        assert settings.metrics_enabled is True

    def test_get_db_url_when_configured(self) -> None:
        """Test get_db_url() returns URL when configured."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            database_url="postgresql://localhost/test",
        )

        assert settings.get_db_url() == "postgresql://localhost/test"

    def test_get_db_url_raises_when_not_configured(self) -> None:
        """Test get_db_url() raises when not configured."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
        )

        with pytest.raises(ValueError, match="database_url not configured"):
            settings.get_db_url()

    def test_accepts_custom_cors_origins(self) -> None:
        """Test that CORS origins can be customized."""
        settings = BaseServiceSettings(
            service_name="test",
            port=8000,
            cors_origins=["http://example.com", "https://app.com"],
        )

        assert len(settings.cors_origins) == 2
        assert "http://example.com" in settings.cors_origins
