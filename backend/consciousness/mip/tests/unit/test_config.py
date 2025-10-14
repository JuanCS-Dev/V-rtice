"""
Unit Tests - MIP Configuration

Testes para configurações do Motor de Integridade Processual.
100% coverage de config.py.

Autor: Juan Carlos de Souza
"""

import os
import pytest
from unittest.mock import patch

from mip.config import Settings, get_settings


class TestSettings:
    """Testes para Settings model."""

    def test_settings_defaults(self):
        """Deve usar valores padrão quando env vars não setadas."""
        settings = Settings()

        # Service defaults
        assert settings.service_name == "mip"
        assert settings.service_version == "1.0.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8100
        assert settings.log_level == "INFO"

        # Neo4j defaults
        assert settings.neo4j_uri == "bolt://localhost:7687"
        assert settings.neo4j_user == "neo4j"
        assert settings.neo4j_password == "neo4j123"
        assert settings.neo4j_database == "neo4j"
        assert settings.neo4j_max_pool_size == 50

        # API defaults
        assert settings.api_title == "MIP - Motor de Integridade Processual"
        assert settings.api_description == "Sistema de supervisão ética para MAXIMUS"
        assert settings.api_prefix == "/api/v1"
        assert settings.cors_origins == ["*"]

        # Performance defaults
        assert settings.request_timeout == 30.0
        assert settings.evaluation_timeout == 10.0

        # Monitoring defaults
        assert settings.enable_metrics is True
        assert settings.metrics_port == 8101

    def test_settings_from_env_vars(self):
        """Deve ler valores de variáveis de ambiente."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "mip-test",
            "SERVICE_VERSION": "2.0.0",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "LOG_LEVEL": "DEBUG",
            "NEO4J_URI": "bolt://neo4j-test:7687",
            "NEO4J_USER": "test_user",
            "NEO4J_PASSWORD": "test_pass",
            "NEO4J_DATABASE": "test_db",
            "NEO4J_MAX_POOL_SIZE": "100",
            "API_TITLE": "Test API",
            "API_DESCRIPTION": "Test Description",
            "API_PREFIX": "/api/v2",
            "REQUEST_TIMEOUT": "60.0",
            "EVALUATION_TIMEOUT": "20.0",
            "ENABLE_METRICS": "false",
            "METRICS_PORT": "9091",
        }, clear=False):
            # Clear cache antes de criar settings
            get_settings.cache_clear()
            settings = Settings()

            # Verify all overrides
            assert settings.service_name == "mip-test"
            assert settings.service_version == "2.0.0"
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000
            assert settings.log_level == "DEBUG"
            assert settings.neo4j_uri == "bolt://neo4j-test:7687"
            assert settings.neo4j_user == "test_user"
            assert settings.neo4j_password == "test_pass"
            assert settings.neo4j_database == "test_db"
            assert settings.neo4j_max_pool_size == 100
            assert settings.api_title == "Test API"
            assert settings.api_description == "Test Description"
            assert settings.api_prefix == "/api/v2"
            assert settings.request_timeout == 60.0
            assert settings.evaluation_timeout == 20.0
            assert settings.enable_metrics is False
            assert settings.metrics_port == 9091

    def test_settings_case_insensitive(self):
        """Deve aceitar env vars case-insensitive."""
        with patch.dict(os.environ, {
            "service_name": "lowercase",  # lowercase
            "SERVICE_NAME": "uppercase",  # uppercase (should override)
        }, clear=False):
            get_settings.cache_clear()
            settings = Settings()

            # Should use either (case insensitive)
            assert settings.service_name in ["lowercase", "uppercase"]

    def test_settings_ignore_extra_fields(self):
        """Deve ignorar campos extras em env vars."""
        with patch.dict(os.environ, {
            "RANDOM_FIELD": "should_be_ignored",
            "ANOTHER_FIELD": "also_ignored",
        }, clear=False):
            get_settings.cache_clear()
            settings = Settings()

            # Should not raise error
            assert not hasattr(settings, "random_field")
            assert not hasattr(settings, "another_field")

    def test_settings_type_validation(self):
        """Deve validar tipos de campos."""
        with patch.dict(os.environ, {
            "PORT": "not_a_number",
        }, clear=False):
            get_settings.cache_clear()

            with pytest.raises(Exception):  # Pydantic validation error
                Settings()

    def test_cors_origins_list(self):
        """CORS origins deve ser lista."""
        settings = Settings()
        assert isinstance(settings.cors_origins, list)
        assert "*" in settings.cors_origins

    def test_cors_origins_from_env(self):
        """CORS origins pode ser customizado via env."""
        with patch.dict(os.environ, {
            "CORS_ORIGINS": '["http://localhost:3000", "https://app.example.com"]',
        }, clear=False):
            get_settings.cache_clear()
            settings = Settings()

            # Pydantic should parse JSON string
            assert isinstance(settings.cors_origins, list)


class TestGetSettings:
    """Testes para get_settings() singleton."""

    def test_get_settings_returns_settings(self):
        """Deve retornar instância de Settings."""
        get_settings.cache_clear()
        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_get_settings_singleton(self):
        """Deve retornar mesma instância (cached)."""
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # Same object (cached)
        assert settings1 is settings2

    def test_get_settings_cache_clear(self):
        """Deve permitir limpar cache."""
        get_settings.cache_clear()
        settings1 = get_settings()

        get_settings.cache_clear()
        settings2 = get_settings()

        # Different objects após cache clear
        assert settings1 is not settings2


class TestSettingsIntegration:
    """Testes de integração de Settings."""

    def test_complete_configuration_cycle(self):
        """Teste ciclo completo de configuração."""
        # 1. Limpar cache
        get_settings.cache_clear()

        # 2. Carregar com defaults
        settings_default = get_settings()
        assert settings_default.port == 8100

        # 3. Limpar e reconfigurar
        get_settings.cache_clear()

        with patch.dict(os.environ, {"PORT": "9999"}, clear=False):
            settings_custom = get_settings()
            assert settings_custom.port == 9999

        # 4. Limpar novamente
        get_settings.cache_clear()
        settings_final = get_settings()

        # Should be back to default (env var cleared)
        assert settings_final.port == 8100

    def test_all_timeouts_are_floats(self):
        """Timeouts devem ser float."""
        get_settings.cache_clear()
        settings = get_settings()

        assert isinstance(settings.request_timeout, float)
        assert isinstance(settings.evaluation_timeout, float)

    def test_all_ports_are_ints(self):
        """Portas devem ser int."""
        get_settings.cache_clear()
        settings = get_settings()

        assert isinstance(settings.port, int)
        assert isinstance(settings.metrics_port, int)

    def test_enable_metrics_is_bool(self):
        """enable_metrics deve ser bool."""
        get_settings.cache_clear()
        settings = get_settings()

        assert isinstance(settings.enable_metrics, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
