"""
Tests for Infrastructure Layer - Config

100% coverage required.
"""
from service_template.infrastructure.config import Settings, get_settings


class TestSettings:
    """Tests for Settings."""

    def test_defaults(self) -> None:
        """Test default settings."""
        settings = Settings()
        
        assert settings.service_name == "service-template"
        assert settings.service_version == "1.0.0"
        assert settings.port == 8000
        assert settings.environment == "development"
        assert settings.enable_metrics is True


    def test_get_settings(self) -> None:
        """Test get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)
