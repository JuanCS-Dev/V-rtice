"""
Testes unitários para backend.modules.tegumentar.config

Testa a configuração Pydantic do Tegumentar, incluindo:
- Validação de tipos
- Valores padrão
- Validadores customizados
- Parsing de variáveis de ambiente
- Cache de settings

Padrão Pagani: Zero mocks desnecessários, validação real de Pydantic.
"""
import os
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from backend.modules.tegumentar.config import get_settings, TegumentarSettings


class TestTegumentarSettingsDefaults:
    """Testa valores padrão da configuração."""

    def test_default_environment_is_production(self):
        """Ambiente padrão deve ser 'production'."""
        settings = TegumentarSettings()
        assert settings.environment == "production"

    def test_default_nft_binary_path(self):
        """Caminho padrão do nftables deve ser /usr/sbin/nft."""
        settings = TegumentarSettings()
        assert settings.nft_binary == "/usr/sbin/nft"

    def test_default_nft_table_name(self):
        """Nome padrão da tabela nftables."""
        settings = TegumentarSettings()
        assert settings.nft_table_name == "tegumentar_epiderme"

    def test_default_nft_chain_name(self):
        """Nome padrão da chain nftables."""
        settings = TegumentarSettings()
        assert settings.nft_chain_name == "edge_filter"

    def test_default_reputation_refresh_interval(self):
        """Intervalo padrão de sincronização de reputação (15 minutos)."""
        settings = TegumentarSettings()
        assert settings.reputation_refresh_interval == 900

    def test_default_ip_reputation_sources(self):
        """Sources padrão de reputação de IP."""
        settings = TegumentarSettings()
        assert len(settings.ip_reputation_sources) == 2
        assert "blocklist.de" in str(settings.ip_reputation_sources[0])
        assert "feodotracker" in str(settings.ip_reputation_sources[1])

    def test_default_redis_url(self):
        """URL padrão do Redis."""
        settings = TegumentarSettings()
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_default_rate_limit_capacity(self):
        """Capacidade padrão do token bucket."""
        settings = TegumentarSettings()
        assert settings.rate_limit_capacity == 10000

    def test_default_rate_limit_refill_per_second(self):
        """Taxa de refill padrão do token bucket."""
        settings = TegumentarSettings()
        assert settings.rate_limit_refill_per_second == 500

    def test_default_postgres_dsn(self):
        """DSN padrão do PostgreSQL/TimescaleDB."""
        settings = TegumentarSettings()
        assert settings.postgres_dsn.startswith("postgresql://")
        assert "tegumentar" in settings.postgres_dsn

    def test_default_kafka_bootstrap_servers(self):
        """Servidores Kafka padrão."""
        settings = TegumentarSettings()
        assert settings.kafka_bootstrap_servers == "localhost:9092"

    def test_default_kafka_topics(self):
        """Tópicos Kafka padrão."""
        settings = TegumentarSettings()
        assert settings.reflex_topic == "tegumentar.reflex"
        assert settings.langerhans_topic == "tegumentar.langerhans"

    def test_default_lymphnode_endpoint(self):
        """Endpoint padrão do Linfonodo Digital."""
        settings = TegumentarSettings()
        assert str(settings.lymphnode_endpoint) == "http://localhost:8021/"

    def test_default_mmei_endpoint(self):
        """Endpoint padrão do MMEI (MAXIMUS)."""
        settings = TegumentarSettings()
        # Pydantic HttpUrl não adiciona trailing slash para paths
        assert "localhost:8600" in str(settings.mmei_endpoint)
        assert "mmei" in str(settings.mmei_endpoint)

    def test_default_prometheus_metrics_port(self):
        """Porta padrão de métricas Prometheus."""
        settings = TegumentarSettings()
        assert settings.prometheus_metrics_port == 9815


class TestTegumentarSettingsValidation:
    """Testa validação de campos."""

    def test_environment_accepts_valid_values(self):
        """Environment deve aceitar development, staging, production."""
        for env in ["development", "staging", "production"]:
            settings = TegumentarSettings(environment=env)
            assert settings.environment == env

    def test_environment_rejects_invalid_value(self):
        """Environment deve rejeitar valores inválidos."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(environment="invalid")

        assert "environment" in str(exc_info.value)

    def test_nft_table_name_min_length(self):
        """Nome de tabela nftables deve ter pelo menos 1 caractere."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(nft_table_name="")

        assert "nft_table_name" in str(exc_info.value)

    def test_nft_table_name_max_length(self):
        """Nome de tabela nftables deve ter no máximo 64 caracteres."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(nft_table_name="a" * 65)

        assert "nft_table_name" in str(exc_info.value)

    def test_reputation_refresh_interval_must_be_positive(self):
        """Intervalo de refresh deve ser positivo."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(reputation_refresh_interval=0)

        assert "reputation_refresh_interval" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(reputation_refresh_interval=-1)

        assert "reputation_refresh_interval" in str(exc_info.value)

    def test_rate_limit_capacity_must_be_positive(self):
        """Capacidade de rate limit deve ser positiva."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(rate_limit_capacity=0)

        assert "rate_limit_capacity" in str(exc_info.value)

    def test_rate_limit_refill_must_be_positive(self):
        """Taxa de refill deve ser positiva."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(rate_limit_refill_per_second=0)

        assert "rate_limit_refill_per_second" in str(exc_info.value)

    def test_prometheus_port_must_be_positive(self):
        """Porta Prometheus deve ser positiva."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(prometheus_metrics_port=0)

        assert "prometheus_metrics_port" in str(exc_info.value)

    def test_lymphnode_endpoint_validates_url(self):
        """Endpoint do Linfonodo deve ser URL válida."""
        settings = TegumentarSettings(
            lymphnode_endpoint="https://lymphnode.example.com"
        )
        assert str(settings.lymphnode_endpoint) == "https://lymphnode.example.com/"

        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(lymphnode_endpoint="not-a-url")

        assert "lymphnode_endpoint" in str(exc_info.value)

    def test_mmei_endpoint_validates_url(self):
        """Endpoint do MMEI deve ser URL válida."""
        settings = TegumentarSettings(mmei_endpoint="https://mmei.example.com/api")
        assert "mmei.example.com" in str(settings.mmei_endpoint)
        assert "api" in str(settings.mmei_endpoint)

        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(mmei_endpoint="invalid-url")

        assert "mmei_endpoint" in str(exc_info.value)


class TestIPReputationSourcesValidator:
    """Testa validador customizado de IP reputation sources."""

    def test_reputation_sources_accepts_list_of_urls(self):
        """Deve aceitar lista de URLs."""
        sources = ["https://example.com/list1.txt", "https://example.org/list2.txt"]
        settings = TegumentarSettings(ip_reputation_sources=sources)
        assert len(settings.ip_reputation_sources) == 2

    def test_reputation_sources_splits_comma_separated_string(self):
        """Deve aceitar string separada por vírgulas."""
        sources_str = "https://example.com/list1.txt,https://example.org/list2.txt"
        settings = TegumentarSettings(ip_reputation_sources=sources_str)
        assert len(settings.ip_reputation_sources) == 2
        assert "example.com" in str(settings.ip_reputation_sources[0])
        assert "example.org" in str(settings.ip_reputation_sources[1])

    def test_reputation_sources_handles_whitespace(self):
        """Deve remover whitespace de strings separadas por vírgula."""
        sources_str = " https://example.com/list1.txt , https://example.org/list2.txt "
        settings = TegumentarSettings(ip_reputation_sources=sources_str)
        assert len(settings.ip_reputation_sources) == 2

    def test_reputation_sources_filters_empty_strings(self):
        """Deve filtrar strings vazias."""
        sources_str = "https://example.com/list1.txt, , https://example.org/list2.txt"
        settings = TegumentarSettings(ip_reputation_sources=sources_str)
        assert len(settings.ip_reputation_sources) == 2

    def test_reputation_sources_rejects_invalid_urls(self):
        """Deve rejeitar URLs inválidas."""
        with pytest.raises(ValidationError) as exc_info:
            TegumentarSettings(ip_reputation_sources=["not-a-url"])

        assert "ip_reputation_sources" in str(exc_info.value)


class TestEnvironmentVariableParsing:
    """Testa parsing de variáveis de ambiente."""

    def test_parses_environment_from_env_var(self, monkeypatch):
        """Deve parsear TEGUMENTAR_ENVIRONMENT."""
        monkeypatch.setenv("TEGUMENTAR_ENVIRONMENT", "development")
        settings = TegumentarSettings()
        assert settings.environment == "development"

    def test_parses_nft_binary_from_env_var(self, monkeypatch):
        """Deve parsear TEGUMENTAR_NFT_BINARY."""
        monkeypatch.setenv("TEGUMENTAR_NFT_BINARY", "/custom/path/nft")
        settings = TegumentarSettings()
        assert settings.nft_binary == "/custom/path/nft"

    def test_parses_redis_url_from_env_var(self, monkeypatch):
        """Deve parsear TEGUMENTAR_REDIS_URL."""
        monkeypatch.setenv("TEGUMENTAR_REDIS_URL", "redis://custom:6380/5")
        settings = TegumentarSettings()
        assert settings.redis_url == "redis://custom:6380/5"

    def test_parses_postgres_dsn_from_env_var(self, monkeypatch):
        """Deve parsear TEGUMENTAR_POSTGRES_DSN."""
        dsn = "postgresql://user:pass@db.example.com:5432/mydb"
        monkeypatch.setenv("TEGUMENTAR_POSTGRES_DSN", dsn)
        settings = TegumentarSettings()
        assert settings.postgres_dsn == dsn

    def test_parses_kafka_servers_from_env_var(self, monkeypatch):
        """Deve parsear TEGUMENTAR_KAFKA_BOOTSTRAP_SERVERS."""
        monkeypatch.setenv(
            "TEGUMENTAR_KAFKA_BOOTSTRAP_SERVERS", "kafka1:9092,kafka2:9092"
        )
        settings = TegumentarSettings()
        assert settings.kafka_bootstrap_servers == "kafka1:9092,kafka2:9092"

    def test_parses_lymphnode_endpoint_from_env_var(self, monkeypatch):
        """Deve parsear TEGUMENTAR_LYMPHNODE_ENDPOINT."""
        monkeypatch.setenv(
            "TEGUMENTAR_LYMPHNODE_ENDPOINT", "https://lymphnode.prod.com"
        )
        settings = TegumentarSettings()
        assert "lymphnode.prod.com" in str(settings.lymphnode_endpoint)

    def test_parses_lymphnode_api_key_from_env_var(self, monkeypatch):
        """Deve parsear TEGUMENTAR_LYMPHNODE_API_KEY."""
        monkeypatch.setenv("TEGUMENTAR_LYMPHNODE_API_KEY", "secret-key-123")
        settings = TegumentarSettings()
        assert settings.lymphnode_api_key == "secret-key-123"

    def test_env_prefix_is_case_insensitive(self, monkeypatch):
        """Deve aceitar variáveis em maiúsculas ou minúsculas."""
        monkeypatch.setenv("tegumentar_environment", "staging")
        settings = TegumentarSettings()
        assert settings.environment == "staging"

    def test_ignores_extra_env_vars(self, monkeypatch):
        """Deve ignorar variáveis de ambiente não mapeadas."""
        monkeypatch.setenv("TEGUMENTAR_UNKNOWN_VAR", "value")
        settings = TegumentarSettings()  # Não deve lançar exceção
        assert not hasattr(settings, "unknown_var")


class TestGetSettingsCaching:
    """Testa o mecanismo de cache do get_settings()."""

    def test_get_settings_returns_same_instance(self):
        """get_settings() deve retornar a mesma instância (cached)."""
        # Clear cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2  # Same object reference

    def test_cache_clear_creates_new_instance(self):
        """Limpar cache deve criar nova instância."""
        get_settings.cache_clear()
        settings1 = get_settings()

        get_settings.cache_clear()
        settings2 = get_settings()

        assert settings1 is not settings2  # Different object references

    def test_cache_persists_across_calls(self):
        """Cache deve persistir entre múltiplas chamadas."""
        get_settings.cache_clear()

        instances = [get_settings() for _ in range(10)]
        unique_instances = set(id(inst) for inst in instances)

        assert len(unique_instances) == 1  # Only one unique instance


class TestPathResolution:
    """Testa resolução de paths em configurações."""

    def test_reputation_cache_path_uses_home_directory(self):
        """Cache de reputação deve usar diretório home."""
        settings = TegumentarSettings()
        cache_path = Path(settings.reputation_cache_path)

        assert cache_path.parts[0] == "/"
        assert ".cache" in cache_path.parts
        assert "tegumentar" in cache_path.parts
        assert cache_path.name == "blocked_ips.txt"

    def test_anomaly_model_path_uses_home_directory(self):
        """Modelo de anomalia deve usar diretório home."""
        settings = TegumentarSettings()
        model_path = Path(settings.anomaly_model_path)

        assert ".cache" in model_path.parts
        assert "tegumentar" in model_path.parts
        assert "models" in model_path.parts
        assert model_path.name == "anomaly_detector.joblib"

    def test_signature_directory_resolves_relative_to_module(self):
        """Diretório de assinaturas deve resolver relativo ao módulo."""
        settings = TegumentarSettings()
        sig_dir = Path(settings.signature_directory)

        assert sig_dir.parts[-2] == "resources"
        assert sig_dir.parts[-1] == "signatures"

    def test_soar_playbooks_path_resolves_relative_to_module(self):
        """Diretório de playbooks deve resolver relativo ao módulo."""
        settings = TegumentarSettings()
        playbooks_path = Path(settings.soar_playbooks_path)

        assert playbooks_path.parts[-2] == "resources"
        assert playbooks_path.parts[-1] == "playbooks"


class TestConfigurationIntegrity:
    """Testa integridade geral da configuração."""

    def test_can_instantiate_with_all_defaults(self):
        """Deve conseguir instanciar com todos os valores padrão."""
        settings = TegumentarSettings()
        assert settings is not None

    def test_config_class_settings(self):
        """Deve ter configurações corretas no Config."""
        assert TegumentarSettings.model_config["env_prefix"] == "TEGUMENTAR_"
        assert TegumentarSettings.model_config["case_sensitive"] is False
        assert TegumentarSettings.model_config["extra"] == "ignore"

    def test_all_required_fields_have_defaults(self):
        """Todos os campos devem ter valores padrão."""
        settings = TegumentarSettings()

        # Verificar campos críticos
        assert settings.environment is not None
        assert settings.nft_binary is not None
        assert settings.redis_url is not None
        assert settings.postgres_dsn is not None
        assert settings.kafka_bootstrap_servers is not None

    def test_optional_fields_can_be_none(self):
        """Campos opcionais devem aceitar None."""
        settings = TegumentarSettings(lymphnode_api_key=None, sdnc_endpoint=None)

        assert settings.lymphnode_api_key is None
        assert settings.sdnc_endpoint is None
