"""100% Coverage for backend/modules/tegumentar/config.py.

Testa todas as configurações do Tegumentar System sem mocks.
"""

import os
from unittest.mock import patch

import pytest

from backend.modules.tegumentar.config import TegumentarSettings, get_settings


class TestTegumentarSettings:
    """Testa criação e validação de TegumentarSettings."""

    def test_default_values(self):
        """Verifica valores padrão."""
        settings = TegumentarSettings()

        assert settings.environment == "production"
        assert settings.nft_binary == "/usr/sbin/nft"
        assert settings.nft_table_name == "tegumentar_epiderme"
        assert settings.nft_chain_name == "edge_filter"
        assert settings.reputation_refresh_interval == 900
        assert settings.rate_limit_capacity == 10000
        assert settings.rate_limit_refill_per_second == 500
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.kafka_bootstrap_servers == "localhost:9092"
        assert settings.reflex_topic == "tegumentar.reflex"
        assert settings.langerhans_topic == "tegumentar.langerhans"
        assert settings.prometheus_metrics_port == 9815

    def test_ip_reputation_sources_default(self):
        """Verifica fontes de reputação padrão."""
        settings = TegumentarSettings()

        assert len(settings.ip_reputation_sources) == 2
        assert "blocklist.de" in str(settings.ip_reputation_sources[0])
        assert "abuse.ch" in str(settings.ip_reputation_sources[1])

    def test_paths_are_strings(self):
        """Verifica que paths são strings válidas."""
        settings = TegumentarSettings()

        assert isinstance(settings.reputation_cache_path, str)
        assert isinstance(settings.anomaly_model_path, str)
        assert isinstance(settings.signature_directory, str)
        assert isinstance(settings.soar_playbooks_path, str)

    def test_postgres_dsn_default(self):
        """Verifica DSN PostgreSQL padrão."""
        settings = TegumentarSettings()

        assert "postgresql+asyncpg://" in settings.postgres_dsn
        assert "tegumentar" in settings.postgres_dsn

    def test_endpoints_default(self):
        """Verifica endpoints padrão."""
        settings = TegumentarSettings()

        assert str(settings.lymphnode_endpoint) == "http://localhost:8021/"
        assert str(settings.mmei_endpoint) == "http://localhost:8600/api/mmei/v1"
        assert str(settings.sdnc_endpoint) == "http://localhost:8181/restconf"

    def test_environment_validation_valid(self):
        """Testa validação de environment válido."""
        for env in ["development", "staging", "production"]:
            settings = TegumentarSettings(environment=env)
            assert settings.environment == env

    def test_environment_validation_invalid(self):
        """Testa validação de environment inválido."""
        with pytest.raises(ValueError, match="String should match pattern"):
            TegumentarSettings(environment="invalid_env")

    def test_nft_table_name_min_length(self):
        """Testa validação de comprimento mínimo nft_table_name."""
        with pytest.raises(ValueError):
            TegumentarSettings(nft_table_name="")

    def test_nft_table_name_max_length(self):
        """Testa validação de comprimento máximo nft_table_name."""
        long_name = "a" * 65
        with pytest.raises(ValueError):
            TegumentarSettings(nft_table_name=long_name)

    def test_nft_table_name_valid(self):
        """Testa nft_table_name válido."""
        settings = TegumentarSettings(nft_table_name="my_table")
        assert settings.nft_table_name == "my_table"

    def test_nft_chain_name_min_length(self):
        """Testa validação de comprimento mínimo nft_chain_name."""
        with pytest.raises(ValueError):
            TegumentarSettings(nft_chain_name="")

    def test_nft_chain_name_max_length(self):
        """Testa validação de comprimento máximo nft_chain_name."""
        long_name = "b" * 65
        with pytest.raises(ValueError):
            TegumentarSettings(nft_chain_name=long_name)

    def test_nft_chain_name_valid(self):
        """Testa nft_chain_name válido."""
        settings = TegumentarSettings(nft_chain_name="my_chain")
        assert settings.nft_chain_name == "my_chain"

    def test_positive_int_fields(self):
        """Testa campos PositiveInt."""
        settings = TegumentarSettings(
            reputation_refresh_interval=300,
            rate_limit_capacity=5000,
            rate_limit_refill_per_second=100,
            prometheus_metrics_port=8080,
        )

        assert settings.reputation_refresh_interval == 300
        assert settings.rate_limit_capacity == 5000
        assert settings.rate_limit_refill_per_second == 100
        assert settings.prometheus_metrics_port == 8080

    def test_positive_int_zero_invalid(self):
        """Testa que PositiveInt rejeita zero."""
        with pytest.raises(ValueError):
            TegumentarSettings(rate_limit_capacity=0)

    def test_positive_int_negative_invalid(self):
        """Testa que PositiveInt rejeita negativos."""
        with pytest.raises(ValueError):
            TegumentarSettings(reputation_refresh_interval=-100)

    def test_lymphnode_api_key_optional(self):
        """Testa que lymphnode_api_key é opcional."""
        settings = TegumentarSettings()
        assert settings.lymphnode_api_key is None

        settings = TegumentarSettings(lymphnode_api_key="test_token_123")
        assert settings.lymphnode_api_key == "test_token_123"

    def test_sdnc_endpoint_optional(self):
        """Testa que sdnc_endpoint é opcional."""
        settings = TegumentarSettings()
        assert settings.sdnc_endpoint is not None  # Default value

        settings = TegumentarSettings(sdnc_endpoint=None)
        assert settings.sdnc_endpoint is None


class TestIpReputationSourcesValidator:
    """Testa validator para ip_reputation_sources."""

    def test_validator_splits_string_with_commas(self):
        """Testa que validator separa string por vírgulas."""
        sources_str = "https://example.com/list1.txt,https://example.com/list2.txt"
        settings = TegumentarSettings(ip_reputation_sources=sources_str)

        assert len(settings.ip_reputation_sources) == 2
        assert str(settings.ip_reputation_sources[0]) == "https://example.com/list1.txt"
        assert str(settings.ip_reputation_sources[1]) == "https://example.com/list2.txt"

    def test_validator_strips_whitespace(self):
        """Testa que validator remove espaços."""
        sources_str = "  https://example.com/a.txt  ,  https://example.com/b.txt  "
        settings = TegumentarSettings(ip_reputation_sources=sources_str)

        assert len(settings.ip_reputation_sources) == 2
        assert str(settings.ip_reputation_sources[0]) == "https://example.com/a.txt"
        assert str(settings.ip_reputation_sources[1]) == "https://example.com/b.txt"

    def test_validator_ignores_empty_strings(self):
        """Testa que validator ignora strings vazias."""
        sources_str = "https://example.com/a.txt,,https://example.com/b.txt,"
        settings = TegumentarSettings(ip_reputation_sources=sources_str)

        assert len(settings.ip_reputation_sources) == 2

    def test_validator_accepts_list_directly(self):
        """Testa que validator aceita lista diretamente."""
        sources_list = [
            "https://example.com/x.txt",
            "https://example.com/y.txt",
        ]
        settings = TegumentarSettings(ip_reputation_sources=sources_list)

        assert len(settings.ip_reputation_sources) == 2
        assert str(settings.ip_reputation_sources[0]) == "https://example.com/x.txt"
        assert str(settings.ip_reputation_sources[1]) == "https://example.com/y.txt"


class TestGetSettings:
    """Testa função cached get_settings()."""

    def test_get_settings_returns_instance(self):
        """Verifica que get_settings retorna instância."""
        settings = get_settings()
        assert isinstance(settings, TegumentarSettings)

    def test_get_settings_is_cached(self):
        """Verifica que get_settings usa cache."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Deve retornar mesmo objeto devido a lru_cache
        assert settings1 is settings2

    def test_get_settings_reads_from_cache_after_env_change(self):
        """Verifica que cache persiste mesmo após mudança de env var."""
        # Clear cache primeiro
        get_settings.cache_clear()

        # Primeira chamada
        settings1 = get_settings()
        original_port = settings1.prometheus_metrics_port

        # Mudar env var (não deveria afetar cache)
        with patch.dict(os.environ, {"TEGUMENTAR_PROMETHEUS_METRICS_PORT": "9999"}):
            settings2 = get_settings()
            # Cache deve retornar mesmo valor
            assert settings2.prometheus_metrics_port == original_port

    def test_get_settings_cache_can_be_cleared(self):
        """Verifica que cache pode ser limpo."""
        get_settings.cache_clear()

        settings1 = get_settings()

        get_settings.cache_clear()

        settings2 = get_settings()

        # Após clear, devem ser instâncias diferentes
        assert settings1 is not settings2


class TestSettingsConfig:
    """Testa Config class dentro de TegumentarSettings."""

    def test_env_prefix_applied(self):
        """Verifica que env_prefix funciona."""
        with patch.dict(os.environ, {"TEGUMENTAR_PROMETHEUS_METRICS_PORT": "7777"}):
            # Clear cache para forçar reload
            get_settings.cache_clear()
            settings = TegumentarSettings()
            assert settings.prometheus_metrics_port == 7777

    def test_case_insensitive_env_vars(self):
        """Verifica que env vars são case insensitive."""
        with patch.dict(os.environ, {"tegumentar_prometheus_metrics_port": "6666"}):
            get_settings.cache_clear()
            settings = TegumentarSettings()
            assert settings.prometheus_metrics_port == 6666


class TestEdgeCases:
    """Testa edge cases e boundary conditions."""

    def test_all_fields_can_be_set_via_kwargs(self):
        """Verifica que todos os campos podem ser configurados."""
        settings = TegumentarSettings(
            environment="development",
            nft_binary="/custom/path/nft",
            nft_table_name="custom_table",
            nft_chain_name="custom_chain",
            reputation_refresh_interval=600,
            ip_reputation_sources=["https://custom.com/feed.txt"],
            redis_url="redis://custom:6379/1",
            reputation_cache_path="/tmp/cache.txt",
            rate_limit_capacity=20000,
            rate_limit_refill_per_second=1000,
            postgres_dsn="postgresql://custom/db",
            kafka_bootstrap_servers="kafka:9092",
            reflex_topic="custom.reflex",
            langerhans_topic="custom.langerhans",
            lymphnode_endpoint="https://custom:8021",
            lymphnode_api_key="custom_key",
            anomaly_model_path="/tmp/model.joblib",
            signature_directory="/tmp/sigs",
            mmei_endpoint="https://custom:8600/api",
            sdnc_endpoint="https://custom:8181/api",
            soar_playbooks_path="/tmp/playbooks",
            prometheus_metrics_port=9999,
        )

        assert settings.environment == "development"
        assert settings.nft_binary == "/custom/path/nft"
        assert settings.prometheus_metrics_port == 9999

    def test_http_url_validation(self):
        """Testa validação de HttpUrl."""
        # URL válida
        settings = TegumentarSettings(mmei_endpoint="http://127.0.0.1:8000/v1")
        assert "127.0.0.1" in str(settings.mmei_endpoint)

        # URL inválida
        with pytest.raises(ValueError):
            TegumentarSettings(mmei_endpoint="not_a_valid_url")

    def test_validator_mode_before(self):
        """Verifica que validator usa mode='before'."""
        # Validator deve processar antes de Pydantic converter
        sources_str = "https://a.com,https://b.com"
        settings = TegumentarSettings(ip_reputation_sources=sources_str)

        assert isinstance(settings.ip_reputation_sources, list)
        assert len(settings.ip_reputation_sources) == 2
