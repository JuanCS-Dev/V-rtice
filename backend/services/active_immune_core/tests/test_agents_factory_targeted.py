"""
Agent Factory - Targeted Coverage Tests

Objetivo: Cobrir agents/agent_factory.py (93 lines, 0% → 20%+)

Testa AgentFactory: initialization, agent registry, statistics

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from agents.agent_factory import AgentFactory
from agents.models import AgentType


# ===== INITIALIZATION TESTS =====

def test_agent_factory_initialization_default():
    """
    SCENARIO: AgentFactory created with defaults
    EXPECTED: Default service URLs set, empty registry
    """
    factory = AgentFactory()

    assert factory.kafka_bootstrap == "localhost:9092"
    assert factory.redis_url == "redis://localhost:6379"
    assert factory.rte_service_url == "http://localhost:8002"
    assert factory.ethical_ai_url == "http://localhost:8100"


def test_agent_factory_initialization_custom():
    """
    SCENARIO: AgentFactory created with custom URLs
    EXPECTED: Custom URLs stored
    """
    factory = AgentFactory(
        kafka_bootstrap="kafka:9093",
        redis_url="redis://redis:6380",
        rte_service_url="http://rte:8003",
        ethical_ai_url="http://ethical:8101",
    )

    assert factory.kafka_bootstrap == "kafka:9093"
    assert factory.redis_url == "redis://redis:6380"
    assert factory.rte_service_url == "http://rte:8003"
    assert factory.ethical_ai_url == "http://ethical:8101"


def test_agent_factory_attributes_exist():
    """
    SCENARIO: AgentFactory instance created
    EXPECTED: All required attributes exist
    """
    factory = AgentFactory()

    assert hasattr(factory, "kafka_bootstrap")
    assert hasattr(factory, "redis_url")
    assert hasattr(factory, "rte_service_url")
    assert hasattr(factory, "ethical_ai_url")
    assert hasattr(factory, "_agents")
    assert hasattr(factory, "_agent_classes")
    assert hasattr(factory, "agents_created_total")
    assert hasattr(factory, "agents_cloned_total")
    assert hasattr(factory, "agents_destroyed_total")


# ===== AGENT REGISTRY TESTS =====

def test_agent_factory_registry_initialized():
    """
    SCENARIO: AgentFactory created
    EXPECTED: _agents registry is empty dict
    """
    factory = AgentFactory()

    assert factory._agents == {}
    assert isinstance(factory._agents, dict)


def test_agent_factory_has_agent_classes_mapping():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: _agent_classes maps AgentType to class
    """
    factory = AgentFactory()

    assert isinstance(factory._agent_classes, dict)
    assert AgentType.MACROFAGO in factory._agent_classes
    assert AgentType.NK_CELL in factory._agent_classes
    assert AgentType.NEUTROFILO in factory._agent_classes


def test_agent_factory_agent_classes_count():
    """
    SCENARIO: AgentFactory._agent_classes
    EXPECTED: Contains 3 agent types
    """
    factory = AgentFactory()

    assert len(factory._agent_classes) == 3


# ===== STATISTICS TESTS =====

def test_agent_factory_statistics_initialized():
    """
    SCENARIO: AgentFactory created
    EXPECTED: All statistics start at 0
    """
    factory = AgentFactory()

    assert factory.agents_created_total == 0
    assert factory.agents_cloned_total == 0
    assert factory.agents_destroyed_total == 0


def test_agent_factory_has_create_agent_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has create_agent method
    """
    factory = AgentFactory()

    assert hasattr(factory, "create_agent")
    assert callable(factory.create_agent)


def test_agent_factory_has_clone_agent_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has clone_agent method
    """
    factory = AgentFactory()

    assert hasattr(factory, "clone_agent")
    assert callable(factory.clone_agent)


def test_agent_factory_has_get_agent_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has get_agent method
    """
    factory = AgentFactory()

    assert hasattr(factory, "get_agent")
    assert callable(factory.get_agent)


def test_agent_factory_has_get_all_agents_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has get_all_agents method
    """
    factory = AgentFactory()

    assert hasattr(factory, "get_all_agents")
    assert callable(factory.get_all_agents)


def test_agent_factory_has_destroy_agent_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has destroy_agent method
    """
    factory = AgentFactory()

    assert hasattr(factory, "destroy_agent")
    assert callable(factory.destroy_agent)


def test_agent_factory_has_shutdown_all_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has shutdown_all method
    """
    factory = AgentFactory()

    assert hasattr(factory, "shutdown_all")
    assert callable(factory.shutdown_all)


# ===== DOCSTRING TESTS =====

def test_agent_factory_docstring_clonal_selection():
    """
    SCENARIO: AgentFactory class docstring
    EXPECTED: Mentions clonal selection and cloning
    """
    doc = AgentFactory.__doc__

    assert "Clone agents" in doc or "clonal selection" in doc.lower()


def test_agent_factory_docstring_production_ready():
    """
    SCENARIO: Module docstring
    EXPECTED: Declares PRODUCTION-READY
    """
    import agents.agent_factory as module

    doc = module.__doc__

    assert "PRODUCTION-READY" in doc
    assert "No mocks" in doc


def test_agent_factory_docstring_biological_inspiration():
    """
    SCENARIO: Module docstring
    EXPECTED: Mentions biological clonal selection
    """
    import agents.agent_factory as module

    doc = module.__doc__

    assert "clonal selection" in doc
    assert "Antigen" in doc or "antigen" in doc
    assert "apoptosis" in doc


# ===== AGENT TYPE MAPPING TESTS =====

def test_agent_factory_macrofago_class_mapped():
    """
    SCENARIO: AgentFactory._agent_classes
    EXPECTED: MACROFAGO type mapped to class
    """
    factory = AgentFactory()

    assert AgentType.MACROFAGO in factory._agent_classes
    assert factory._agent_classes[AgentType.MACROFAGO] is not None


def test_agent_factory_nk_cell_class_mapped():
    """
    SCENARIO: AgentFactory._agent_classes
    EXPECTED: NK_CELL type mapped to class
    """
    factory = AgentFactory()

    assert AgentType.NK_CELL in factory._agent_classes
    assert factory._agent_classes[AgentType.NK_CELL] is not None


def test_agent_factory_neutrofilo_class_mapped():
    """
    SCENARIO: AgentFactory._agent_classes
    EXPECTED: NEUTROFILO type mapped to class
    """
    factory = AgentFactory()

    assert AgentType.NEUTROFILO in factory._agent_classes
    assert factory._agent_classes[AgentType.NEUTROFILO] is not None


# ===== GET AGENT TESTS (synchronous) =====

def test_agent_factory_get_agent_empty_registry():
    """
    SCENARIO: get_agent() called on empty registry
    EXPECTED: Returns None
    """
    factory = AgentFactory()

    result = factory.get_agent("nonexistent-agent-id")

    assert result is None


# ===== LIST AGENTS TESTS (synchronous) =====

def test_agent_factory_get_all_agents_empty():
    """
    SCENARIO: get_all_agents() called on empty registry
    EXPECTED: Returns empty list
    """
    factory = AgentFactory()

    result = factory.get_all_agents()

    assert result == []
    assert isinstance(result, list)


def test_agent_factory_has_get_agents_by_type_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has get_agents_by_type method
    """
    factory = AgentFactory()

    assert hasattr(factory, "get_agents_by_type")
    assert callable(factory.get_agents_by_type)


def test_agent_factory_has_get_active_agents_method():
    """
    SCENARIO: AgentFactory instance
    EXPECTED: Has get_active_agents method
    """
    factory = AgentFactory()

    assert hasattr(factory, "get_active_agents")
    assert callable(factory.get_active_agents)
