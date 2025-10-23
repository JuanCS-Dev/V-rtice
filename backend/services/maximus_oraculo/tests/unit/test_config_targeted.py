"""
Config Module - Targeted Coverage Tests

Objetivo: Cobrir config.py (29 lines, 0% → 80%+)

Testa OraculoConfig: initialization, feature flags, capabilities, health status

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import os
from config import OraculoConfig, config


# ===== INITIALIZATION TESTS =====

def test_oraculo_config_initialization_default(monkeypatch):
    """
    SCENARIO: OraculoConfig created with defaults
    EXPECTED: Default values set from env (or defaults)
    """
    # Clear env vars to test defaults
    monkeypatch.delenv("ENABLE_KAFKA", raising=False)
    monkeypatch.delenv("ENABLE_WEBSOCKET", raising=False)

    cfg = OraculoConfig()

    assert cfg.enable_kafka is True
    assert cfg.enable_websocket is True
    assert cfg.service_name == "maximus_oraculo"
    assert cfg.service_version == "2.0.0"


def test_oraculo_config_initialization_from_env(monkeypatch):
    """
    SCENARIO: OraculoConfig created with env vars
    EXPECTED: Values loaded from environment
    """
    monkeypatch.setenv("ENABLE_KAFKA", "false")
    monkeypatch.setenv("KAFKA_BROKERS", "kafka1:9092,kafka2:9092")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4")

    cfg = OraculoConfig()

    assert cfg.enable_kafka is False
    assert cfg.kafka_brokers == "kafka1:9092,kafka2:9092"
    assert cfg.openai_model == "gpt-4"


def test_oraculo_config_kafka_settings(monkeypatch):
    """
    SCENARIO: OraculoConfig Kafka settings
    EXPECTED: Kafka topic and brokers configured
    """
    monkeypatch.setenv("KAFKA_TOPIC", "custom.topic")

    cfg = OraculoConfig()

    assert cfg.kafka_topic == "custom.topic"
    assert cfg.kafka_brokers is not None


def test_oraculo_config_openai_settings(monkeypatch):
    """
    SCENARIO: OraculoConfig OpenAI settings
    EXPECTED: API key, model, and max_tokens configured
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_MAX_TOKENS", "8192")

    cfg = OraculoConfig()

    assert cfg.openai_api_key == "sk-test-key"
    assert cfg.openai_max_tokens == 8192


def test_oraculo_config_degradations_list():
    """
    SCENARIO: OraculoConfig degradations list
    EXPECTED: Starts as empty list
    """
    cfg = OraculoConfig()

    assert cfg.degradations == []
    assert isinstance(cfg.degradations, list)


# ===== METHOD TESTS =====

def test_check_kafka_availability_enabled(monkeypatch):
    """
    SCENARIO: check_kafka_availability() with ENABLE_KAFKA=true
    EXPECTED: Returns True
    """
    monkeypatch.setenv("ENABLE_KAFKA", "true")
    cfg = OraculoConfig()

    assert cfg.check_kafka_availability() is True


def test_check_kafka_availability_disabled(monkeypatch):
    """
    SCENARIO: check_kafka_availability() with ENABLE_KAFKA=false
    EXPECTED: Returns False
    """
    monkeypatch.setenv("ENABLE_KAFKA", "false")
    cfg = OraculoConfig()

    assert cfg.check_kafka_availability() is False


def test_check_llm_availability_with_api_key(monkeypatch):
    """
    SCENARIO: check_llm_availability() with API key set
    EXPECTED: Returns True
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "true")
    cfg = OraculoConfig()

    assert cfg.check_llm_availability() is True


def test_check_llm_availability_without_api_key(monkeypatch):
    """
    SCENARIO: check_llm_availability() without API key
    EXPECTED: Returns False
    """
    monkeypatch.setenv("OPENAI_API_KEY", "")
    cfg = OraculoConfig()

    assert cfg.check_llm_availability() is False


def test_check_llm_availability_disabled(monkeypatch):
    """
    SCENARIO: check_llm_availability() with ENABLE_LLM_CODEGEN=false
    EXPECTED: Returns False even with API key
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    cfg = OraculoConfig()

    assert cfg.check_llm_availability() is False


def test_get_capabilities_all_enabled(monkeypatch):
    """
    SCENARIO: get_capabilities() with all features enabled
    EXPECTED: Returns dict with all capabilities True
    """
    monkeypatch.setenv("ENABLE_KAFKA", "true")
    monkeypatch.setenv("ENABLE_WEBSOCKET", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    cfg = OraculoConfig()

    caps = cfg.get_capabilities()

    assert caps["code_generation"] is True
    assert caps["llm_generation"] is True
    assert caps["kafka_integration"] is True
    assert caps["websocket_streaming"] is True


def test_get_capabilities_with_degradation(monkeypatch):
    """
    SCENARIO: get_capabilities() with kafka_unavailable degradation
    EXPECTED: Kafka and WebSocket capabilities disabled
    """
    monkeypatch.setenv("ENABLE_KAFKA", "true")
    monkeypatch.setenv("ENABLE_WEBSOCKET", "true")
    cfg = OraculoConfig()
    cfg.add_degradation("kafka_unavailable")

    caps = cfg.get_capabilities()

    assert caps["kafka_integration"] is False
    assert caps["websocket_streaming"] is False


def test_add_degradation_unique():
    """
    SCENARIO: add_degradation() called twice with same degradation
    EXPECTED: Only added once (no duplicates)
    """
    cfg = OraculoConfig()
    cfg.add_degradation("test_degradation")
    cfg.add_degradation("test_degradation")

    assert cfg.degradations == ["test_degradation"]


def test_add_degradation_multiple():
    """
    SCENARIO: add_degradation() called with different degradations
    EXPECTED: All degradations tracked
    """
    cfg = OraculoConfig()
    cfg.add_degradation("kafka_unavailable")
    cfg.add_degradation("openai_timeout")

    assert "kafka_unavailable" in cfg.degradations
    assert "openai_timeout" in cfg.degradations
    assert len(cfg.degradations) == 2


def test_get_health_status_healthy():
    """
    SCENARIO: get_health_status() with no degradations
    EXPECTED: status=healthy, degradations=None
    """
    cfg = OraculoConfig()

    health = cfg.get_health_status()

    assert health["status"] == "healthy"
    assert health["service"] == "maximus_oraculo"
    assert health["version"] == "2.0.0"
    assert "features" in health
    assert health["degradations"] is None


def test_get_health_status_degraded():
    """
    SCENARIO: get_health_status() with degradations
    EXPECTED: status=degraded, degradations list present
    """
    cfg = OraculoConfig()
    cfg.add_degradation("kafka_unavailable")

    health = cfg.get_health_status()

    assert health["status"] == "degraded"
    assert health["degradations"] == ["kafka_unavailable"]
    assert "features" in health


# ===== GLOBAL INSTANCE TESTS =====

def test_global_config_instance():
    """
    SCENARIO: Global config instance
    EXPECTED: Is OraculoConfig instance
    """
    assert isinstance(config, OraculoConfig)


def test_global_config_has_attributes():
    """
    SCENARIO: Global config instance attributes
    EXPECTED: Has all expected attributes
    """
    assert hasattr(config, "enable_kafka")
    assert hasattr(config, "kafka_brokers")
    assert hasattr(config, "service_name")
    assert hasattr(config, "degradations")


# ===== EDGE CASE TESTS =====

def test_openai_max_tokens_invalid(monkeypatch):
    """
    SCENARIO: OPENAI_MAX_TOKENS with invalid value
    EXPECTED: Raises ValueError
    """
    monkeypatch.setenv("OPENAI_MAX_TOKENS", "not_a_number")

    with pytest.raises(ValueError):
        OraculoConfig()


def test_enable_kafka_case_insensitive(monkeypatch):
    """
    SCENARIO: ENABLE_KAFKA with uppercase TRUE
    EXPECTED: Parsed correctly as True
    """
    monkeypatch.setenv("ENABLE_KAFKA", "TRUE")
    cfg = OraculoConfig()

    assert cfg.enable_kafka is True


def test_enable_kafka_any_value_false(monkeypatch):
    """
    SCENARIO: ENABLE_KAFKA with value other than 'true'
    EXPECTED: Parsed as False
    """
    monkeypatch.setenv("ENABLE_KAFKA", "yes")
    cfg = OraculoConfig()

    assert cfg.enable_kafka is False
