"""Coordination Service Tests - PRODUCTION-READY

Tests for CoordinationService using REAL Lymphnode.

NO MOCKS - All tests use real Core components with graceful degradation.

Authors: Juan & Claude
Version: 1.0.0
"""

import pytest
from datetime import datetime

from .core_manager import CoreManager
from .coordination_service import (
    CoordinationService,
    LymphnodeNotAvailableError,
    AgentNotFoundForCloneError,
)
from .agent_service import AgentService
from ..models.coordination import (
    CloneResponse,
    LymphnodeMetrics,
    HomeostaticStateResponse,
)


# ==================== FIXTURES ====================


# Cleanup fixture is in conftest.py


# ==================== HELPER FUNCTIONS ====================


async def setup_coordination_service() -> CoordinationService:
    """
    Setup CoordinationService with initialized Core.

    Returns:
        CoordinationService instance
    """
    core = CoreManager.get_instance()

    # Initialize Core with test config (services unavailable)
    await core.initialize(
        kafka_bootstrap="localhost:9999",  # Not running
        redis_url="redis://localhost:9999",  # Not running
        lymphnode_id="test_lymphnode",
        enable_degraded_mode=True,  # Allow graceful degradation
    )

    # Start Core
    await core.start()

    # Create service
    service = CoordinationService()

    return service


# ==================== TESTS ====================


@pytest.mark.asyncio
async def test_initialization():
    """Test CoordinationService initialization"""
    service = await setup_coordination_service()

    assert service is not None
    assert isinstance(service, CoordinationService)
    assert "CoordinationService" in repr(service)


@pytest.mark.asyncio
async def test_lymphnode_not_available_error():
    """Test error when lymphnode not available"""
    # Don't initialize Core
    service = CoordinationService()

    with pytest.raises(LymphnodeNotAvailableError, match="Core System not initialized"):
        await service.get_lymphnode_metrics()


@pytest.mark.asyncio
async def test_clone_agent_success():
    """Test cloning an agent successfully"""
    service = await setup_coordination_service()

    # First, create an agent to clone
    agent_service = AgentService()
    original = await agent_service.create_agent(
        "macrofago",
        {"area_patrulha": "test_area"}
    )

    # Clone the agent
    clone_response = await service.clone_agent(
        agent_id=original.agent_id,
        especializacao="test_threat",
        num_clones=3,
        mutate=True,
        mutation_rate=0.1,
    )

    assert isinstance(clone_response, CloneResponse)
    assert clone_response.parent_id == original.agent_id
    assert clone_response.num_clones == 3
    assert len(clone_response.clone_ids) == 3
    assert clone_response.especializacao == "test_threat"
    assert clone_response.created_at is not None

    # Verify all clone IDs are different
    assert len(set(clone_response.clone_ids)) == 3

    # Verify clones are different from parent
    for clone_id in clone_response.clone_ids:
        assert clone_id != original.agent_id


@pytest.mark.asyncio
async def test_clone_agent_not_found():
    """Test cloning a non-existent agent"""
    service = await setup_coordination_service()

    with pytest.raises(AgentNotFoundForCloneError, match="Agent not found"):
        await service.clone_agent(
            agent_id="non_existent_agent",
            num_clones=1,
        )


@pytest.mark.asyncio
async def test_clone_agent_single():
    """Test cloning with default num_clones=1"""
    service = await setup_coordination_service()

    # Create an agent to clone
    agent_service = AgentService()
    original = await agent_service.create_agent(
        "nk_cell",
        {"area_patrulha": "test_area"}
    )

    # Clone with default num_clones
    clone_response = await service.clone_agent(
        agent_id=original.agent_id,
    )

    assert clone_response.num_clones == 1
    assert len(clone_response.clone_ids) == 1


@pytest.mark.asyncio
async def test_get_lymphnode_metrics():
    """Test getting lymphnode metrics"""
    service = await setup_coordination_service()

    metrics = await service.get_lymphnode_metrics()

    assert isinstance(metrics, LymphnodeMetrics)
    assert metrics.lymphnode_id == "test_lymphnode"
    assert metrics.nivel in ["local", "regional", "global"]
    assert metrics.homeostatic_state in [
        "REPOUSO",
        "VIGILÂNCIA",
        "ATENÇÃO",
        "ATIVAÇÃO",
        "INFLAMAÇÃO",
    ]
    assert 30.0 <= metrics.temperatura_regional <= 45.0
    assert metrics.agentes_ativos >= 0
    assert metrics.agentes_dormindo >= 0
    assert metrics.total_ameacas_detectadas >= 0
    assert metrics.total_neutralizacoes >= 0
    assert metrics.total_clones_criados >= 0
    assert metrics.total_clones_destruidos >= 0


@pytest.mark.asyncio
async def test_lymphnode_metrics_after_clone():
    """Test lymphnode metrics update after cloning"""
    service = await setup_coordination_service()

    # Get initial metrics
    metrics_before = await service.get_lymphnode_metrics()
    clones_before = metrics_before.total_clones_criados

    # Create and clone an agent
    agent_service = AgentService()
    original = await agent_service.create_agent(
        "neutrofilo",
        {"area_patrulha": "test_area"}
    )

    await service.clone_agent(
        agent_id=original.agent_id,
        num_clones=2,
    )

    # Get updated metrics
    metrics_after = await service.get_lymphnode_metrics()

    # Verify clone count increased
    assert metrics_after.total_clones_criados == clones_before + 2


@pytest.mark.asyncio
async def test_get_homeostatic_state():
    """Test getting homeostatic state"""
    service = await setup_coordination_service()

    state = await service.get_homeostatic_state()

    assert isinstance(state, HomeostaticStateResponse)
    assert state.homeostatic_state in [
        "REPOUSO",
        "VIGILÂNCIA",
        "ATENÇÃO",
        "ATIVAÇÃO",
        "INFLAMAÇÃO",
    ]
    assert 30.0 <= state.temperatura_regional <= 45.0
    assert state.description is not None
    assert len(state.description) > 0
    assert state.recommended_action is not None
    assert len(state.recommended_action) > 0


@pytest.mark.asyncio
async def test_homeostatic_state_recommendations():
    """Test homeostatic state recommendations are appropriate"""
    service = await setup_coordination_service()

    state = await service.get_homeostatic_state()

    # Verify recommendations match state
    if state.homeostatic_state == "REPOUSO":
        assert "normal" in state.description.lower()
        assert "maintain" in state.recommended_action.lower()

    elif state.homeostatic_state == "INFLAMAÇÃO":
        assert "critical" in state.description.lower() or "inflamed" in state.description.lower()
        assert "maximum" in state.recommended_action.lower() or "emergency" in state.recommended_action.lower()


@pytest.mark.asyncio
async def test_destroy_clones():
    """Test destroying clones by specialization"""
    service = await setup_coordination_service()

    # Create and clone an agent
    agent_service = AgentService()
    original = await agent_service.create_agent(
        "macrofago",
        {"area_patrulha": "test_area"}
    )

    # Clone with specific specialization
    await service.clone_agent(
        agent_id=original.agent_id,
        especializacao="threat_to_destroy",
        num_clones=3,
    )

    # Destroy clones
    num_destroyed = await service.destroy_clones("threat_to_destroy")

    # Verify destruction
    assert num_destroyed == 3

    # Verify metrics updated
    metrics = await service.get_lymphnode_metrics()
    assert metrics.total_clones_destruidos >= 3


@pytest.mark.asyncio
async def test_destroy_clones_not_found():
    """Test destroying non-existent clones returns 0"""
    service = await setup_coordination_service()

    # Try to destroy non-existent specialization
    num_destroyed = await service.destroy_clones("non_existent_specialization")

    assert num_destroyed == 0


@pytest.mark.asyncio
async def test_multiple_clones_different_specializations():
    """Test cloning with different specializations"""
    service = await setup_coordination_service()

    # Create an agent
    agent_service = AgentService()
    original = await agent_service.create_agent(
        "macrofago",
        {"area_patrulha": "test_area"}
    )

    # Create clones with different specializations
    clone_response1 = await service.clone_agent(
        agent_id=original.agent_id,
        especializacao="threat_A",
        num_clones=2,
    )

    clone_response2 = await service.clone_agent(
        agent_id=original.agent_id,
        especializacao="threat_B",
        num_clones=3,
    )

    # Verify different clones created
    assert clone_response1.especializacao == "threat_A"
    assert clone_response2.especializacao == "threat_B"
    assert len(clone_response1.clone_ids) == 2
    assert len(clone_response2.clone_ids) == 3

    # Destroy only threat_A clones
    num_destroyed = await service.destroy_clones("threat_A")
    assert num_destroyed == 2

    # Verify metrics
    metrics = await service.get_lymphnode_metrics()
    assert metrics.total_clones_criados >= 5
    assert metrics.total_clones_destruidos >= 2


@pytest.mark.asyncio
async def test_concurrent_cloning():
    """Test concurrent cloning operations"""
    import asyncio

    service = await setup_coordination_service()

    # Create multiple agents
    agent_service = AgentService()
    agents = []
    for i in range(3):
        agent = await agent_service.create_agent(
            "macrofago",
            {"area_patrulha": f"area_{i}"}
        )
        agents.append(agent)

    # Clone all concurrently
    clone_tasks = [
        service.clone_agent(
            agent_id=agent.agent_id,
            especializacao=f"concurrent_{i}",
            num_clones=2,
        )
        for i, agent in enumerate(agents)
    ]

    clone_responses = await asyncio.gather(*clone_tasks)

    # Verify all cloning succeeded
    assert len(clone_responses) == 3
    for response in clone_responses:
        assert isinstance(response, CloneResponse)
        assert response.num_clones == 2

    # Verify total clones
    metrics = await service.get_lymphnode_metrics()
    assert metrics.total_clones_criados >= 6


@pytest.mark.asyncio
async def test_repr():
    """Test CoordinationService string representation"""
    service = await setup_coordination_service()

    repr_str = repr(service)

    assert "CoordinationService" in repr_str
    assert "lymphnode_available" in repr_str
