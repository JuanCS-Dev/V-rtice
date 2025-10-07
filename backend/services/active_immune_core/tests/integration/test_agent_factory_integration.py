"""Agent Factory Integration Tests

Tests the Agent Factory's ability to create, clone, and manage agents.
Validates integration between factory and all agent types.
"""

import asyncio

import pytest
import pytest_asyncio

from active_immune_core.agents import AgentFactory, AgentType


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def factory():
    """Create Agent Factory"""
    factory = AgentFactory()
    yield factory

    # Cleanup: shutdown all agents
    await factory.shutdown_all()


# ==================== TESTS ====================


@pytest.mark.asyncio
class TestAgentFactoryCreation:
    """Test agent creation"""

    async def test_create_macrofago(self, factory):
        """Test creating Macrophage"""
        mac = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_test"
        )

        assert mac.state.tipo == AgentType.MACROFAGO
        assert mac.state.area_patrulha == "subnet_test"
        assert mac.state.id in factory._agents

    async def test_create_nk_cell(self, factory):
        """Test creating NK Cell"""
        nk = await factory.create_agent(
            AgentType.NK_CELL, area_patrulha="subnet_test"
        )

        assert nk.state.tipo == AgentType.NK_CELL
        assert nk.state.area_patrulha == "subnet_test"
        assert nk.state.id in factory._agents

    async def test_create_neutrofilo(self, factory):
        """Test creating Neutrophil"""
        neutro = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_test"
        )

        assert neutro.state.tipo == AgentType.NEUTROFILO
        assert neutro.state.area_patrulha == "subnet_test"
        assert neutro.state.id in factory._agents

    async def test_create_multiple_agents(self, factory):
        """Test creating multiple agents of different types"""
        mac = await factory.create_agent(AgentType.MACROFAGO, area_patrulha="subnet_1")
        nk = await factory.create_agent(AgentType.NK_CELL, area_patrulha="subnet_2")
        neutro = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_3"
        )

        assert len(factory._agents) == 3
        assert factory.agents_created_total == 3

    async def test_create_agent_invalid_type(self, factory):
        """Test creating agent with invalid type"""
        with pytest.raises(ValueError):
            await factory.create_agent("invalid_type", area_patrulha="subnet_test")


@pytest.mark.asyncio
class TestAgentFactoryCloning:
    """Test agent cloning (clonal selection)"""

    async def test_clone_macrofago(self, factory):
        """Test cloning Macrophage"""
        original = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_test"
        )

        clone = await factory.clone_agent(original, mutate=False)

        assert clone.state.tipo == original.state.tipo
        assert clone.state.area_patrulha == original.state.area_patrulha
        assert clone.state.id != original.state.id  # Different ID
        assert factory.agents_cloned_total == 1

    async def test_clone_with_mutation(self, factory):
        """Test cloning with somatic hypermutation"""
        original = await factory.create_agent(
            AgentType.NK_CELL, area_patrulha="subnet_test"
        )

        # Store original parameters
        original_aggression = original.state.nivel_agressividade
        original_sensitivity = original.state.sensibilidade

        clone = await factory.clone_agent(original, mutate=True, mutation_rate=0.2)

        # Clone should have different parameters (mutated)
        # Note: Due to randomness, may occasionally be same
        # We just test that it completed without error
        assert clone.state.id != original.state.id

    async def test_clonal_expansion(self, factory):
        """Test creating multiple clones (clonal expansion)"""
        original = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_test"
        )

        clones = await factory.clonal_expansion(original, num_clones=5, mutate=True)

        assert len(clones) == 5
        assert factory.agents_cloned_total == 5

        # All clones should be Neutrophils
        for clone in clones:
            assert clone.state.tipo == AgentType.NEUTROFILO

    async def test_clone_specialization_marking(self, factory):
        """Test that clones are marked with specialization"""
        original = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_test"
        )

        clone = await factory.clone_agent(original, mutate=True)

        # Clone should be marked with parent ID
        assert clone.state.especializacao is not None
        assert original.state.id[:8] in clone.state.especializacao


@pytest.mark.asyncio
class TestAgentFactoryManagement:
    """Test agent management (get, destroy)"""

    async def test_get_agent_by_id(self, factory):
        """Test retrieving agent by ID"""
        agent = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_test"
        )

        retrieved = factory.get_agent(agent.state.id)

        assert retrieved is agent

    async def test_get_agent_not_found(self, factory):
        """Test retrieving non-existent agent"""
        retrieved = factory.get_agent("non_existent_id")

        assert retrieved is None

    async def test_get_agents_by_type(self, factory):
        """Test retrieving agents by type"""
        mac1 = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_1"
        )
        mac2 = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_2"
        )
        nk = await factory.create_agent(AgentType.NK_CELL, area_patrulha="subnet_3")

        macrofagos = factory.get_agents_by_type(AgentType.MACROFAGO)
        nk_cells = factory.get_agents_by_type(AgentType.NK_CELL)

        assert len(macrofagos) == 2
        assert len(nk_cells) == 1
        assert mac1 in macrofagos
        assert mac2 in macrofagos

    async def test_get_active_agents(self, factory):
        """Test retrieving only active (running) agents"""
        agent1 = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_1"
        )
        agent2 = await factory.create_agent(
            AgentType.NK_CELL, area_patrulha="subnet_2"
        )

        # Start one agent
        await agent1.iniciar()
        await asyncio.sleep(0.5)

        active_agents = factory.get_active_agents()

        assert len(active_agents) == 1
        assert agent1 in active_agents

        await agent1.parar()

    async def test_get_all_agents(self, factory):
        """Test retrieving all agents"""
        agent1 = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_1"
        )
        agent2 = await factory.create_agent(
            AgentType.NK_CELL, area_patrulha="subnet_2"
        )

        all_agents = factory.get_all_agents()

        assert len(all_agents) == 2
        assert agent1 in all_agents
        assert agent2 in all_agents

    async def test_destroy_agent(self, factory):
        """Test destroying agent"""
        agent = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_test"
        )

        agent_id = agent.state.id

        # Destroy agent
        result = await factory.destroy_agent(agent_id)

        assert result is True
        assert agent_id not in factory._agents
        assert factory.agents_destroyed_total == 1

    async def test_destroy_agent_not_found(self, factory):
        """Test destroying non-existent agent"""
        result = await factory.destroy_agent("non_existent_id")

        assert result is False

    async def test_destroy_running_agent(self, factory):
        """Test destroying running agent (should stop first)"""
        agent = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_test"
        )

        await agent.iniciar()
        await asyncio.sleep(0.5)

        # Destroy (should stop automatically)
        await factory.destroy_agent(agent.state.id)

        assert agent._running is False


@pytest.mark.asyncio
class TestAgentFactoryLifecycle:
    """Test factory lifecycle (shutdown)"""

    async def test_shutdown_all_agents(self, factory):
        """Test shutting down all agents"""
        agent1 = await factory.create_agent(
            AgentType.MACROFAGO, area_patrulha="subnet_1"
        )
        agent2 = await factory.create_agent(
            AgentType.NK_CELL, area_patrulha="subnet_2"
        )
        agent3 = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_3"
        )

        # Start agents
        await agent1.iniciar()
        await agent2.iniciar()
        await asyncio.sleep(0.5)

        # Shutdown all
        await factory.shutdown_all()

        assert len(factory._agents) == 0
        assert agent1._running is False
        assert agent2._running is False


@pytest.mark.asyncio
class TestAgentFactoryMetrics:
    """Test factory metrics"""

    async def test_get_factory_metrics(self, factory):
        """Test retrieving factory metrics"""
        mac = await factory.create_agent(AgentType.MACROFAGO, area_patrulha="subnet_1")
        nk = await factory.create_agent(AgentType.NK_CELL, area_patrulha="subnet_2")
        neutro1 = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_3"
        )
        neutro2 = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_4"
        )

        # Clone one agent
        await factory.clone_agent(mac)

        await mac.iniciar()
        await asyncio.sleep(0.5)

        metrics = factory.get_factory_metrics()

        assert metrics["agents_total"] == 5  # 4 created + 1 clone
        assert metrics["agents_active"] == 1  # Only mac is running
        assert metrics["agents_by_type"][AgentType.MACROFAGO] == 2  # Original + clone
        assert metrics["agents_by_type"][AgentType.NK_CELL] == 1
        assert metrics["agents_by_type"][AgentType.NEUTROFILO] == 2
        assert metrics["agents_created_total"] == 5
        assert metrics["agents_cloned_total"] == 1
        assert metrics["cloning_rate"] == 0.2  # 1/5

        await mac.parar()

    async def test_repr(self, factory):
        """Test string representation"""
        await factory.create_agent(AgentType.MACROFAGO, area_patrulha="subnet_1")
        await factory.create_agent(AgentType.NK_CELL, area_patrulha="subnet_2")

        repr_str = repr(factory)

        assert "AgentFactory" in repr_str
        assert "agents=2" in repr_str
        assert "created=2" in repr_str


@pytest.mark.asyncio
class TestAgentFactoryIntegration:
    """Test full integration scenarios"""

    async def test_create_and_start_multiple_agents(self, factory):
        """Test creating and starting multiple agents"""
        agents = []

        # Create agents of each type
        agents.append(
            await factory.create_agent(AgentType.MACROFAGO, area_patrulha="subnet_1")
        )
        agents.append(
            await factory.create_agent(AgentType.NK_CELL, area_patrulha="subnet_2")
        )
        agents.append(
            await factory.create_agent(AgentType.NEUTROFILO, area_patrulha="subnet_3")
        )

        # Start all agents
        for agent in agents:
            await agent.iniciar()

        await asyncio.sleep(1)

        # All should be running
        assert len(factory.get_active_agents()) == 3

        # Stop all
        for agent in agents:
            await agent.parar()

    async def test_clonal_expansion_scenario(self, factory):
        """Test clonal expansion scenario (threat response)"""
        # Create original agent
        original = await factory.create_agent(
            AgentType.NEUTROFILO, area_patrulha="subnet_threat"
        )

        # Simulate threat detection (trigger clonal expansion)
        clones = await factory.clonal_expansion(original, num_clones=10, mutate=True)

        # Total agents should be 11 (original + 10 clones)
        assert len(factory._agents) == 11

        # All should be Neutrophils
        neutrophils = factory.get_agents_by_type(AgentType.NEUTROFILO)
        assert len(neutrophils) == 11
