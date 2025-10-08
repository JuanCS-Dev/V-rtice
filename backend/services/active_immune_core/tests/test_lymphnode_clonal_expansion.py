"""Lymphnode Clonal Expansion Tests - Real immune memory behavior

These tests validate the FASCINATING behavior of lymphnodes creating specialized
immune memory through clonal expansion and apoptosis.

Biological parallel:
- When you get infected, lymphnodes swell ("ínguas") because B/T cells are
  rapidly cloning inside to fight the specific pathogen.
- After infection clears, excess clones die (apoptosis) and lymphnodes shrink.
- Some clones persist as memory cells for future protection.

Digital implementation:
- clonar_agente(): Creates specialized clones (lymphnode swelling)
- destruir_clones(): Apoptosis signal (lymphnode returns to normal)
- Somatic hypermutation: Each clone has slight variation in sensitivity

Tests focus on PUBLIC API and OBSERVABLE behavior.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from active_immune_core.agents import AgentType
from active_immune_core.agents.models import AgenteState
from active_immune_core.coordination.lymphnode import LinfonodoDigital

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def lymphnode():
    """Create lymphnode for clonal expansion tests"""
    node = LinfonodoDigital(
        lymphnode_id="lymph_clonal_test",
        area_responsabilidade="subnet_10.0.1.0/24",
        nivel="local",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379/0",
    )

    await node.iniciar()
    await asyncio.sleep(0.3)

    yield node

    if node._running:
        await node.parar()


# ==================== CLONAL EXPANSION TESTS ====================


class TestClonalExpansion:
    """Test clonal expansion (lymphnode swelling - "íngua inchando")"""

    @pytest.mark.asyncio
    async def test_clonar_agente_creates_specialized_clones(self, lymphnode):
        """
        Test clonal expansion creates specialized agent clones.

        Real behavior: When threat detected, lymphnode creates multiple
        specialized clones (like B cells in lymphnode during infection).

        Coverage: Lines 372-435 (complete clonar_agente method)
        """
        # ARRANGE: Mock AgentFactory
        with patch.object(lymphnode.factory, "create_agent") as mock_create:
            # Create mock agents
            mock_agents = []
            for i in range(3):
                mock_agent = MagicMock()
                mock_agent.state = AgenteState(
                    id=f"clone_{i}",
                    tipo=AgentType.NK_CELL,
                    status="patrulhando",
                    area_patrulha="subnet_10.0.1.0/24",
                    localizacao_atual="subnet_10.0.1.0/24",
                )
                mock_agent.iniciar = AsyncMock()
                mock_agents.append(mock_agent)

            mock_create.side_effect = mock_agents

            initial_clones = lymphnode.total_clones_criados

            # ACT: Create 3 NK cell clones specialized for "malware_xyz"
            clone_ids = await lymphnode.clonar_agente(
                tipo_base=AgentType.NK_CELL,
                especializacao="malware_xyz",
                quantidade=3,
            )

        # ASSERT: Clonal expansion should succeed
        assert len(clone_ids) == 3, "Should create 3 clones"
        assert lymphnode.total_clones_criados == initial_clones + 3, "Should increment clone counter"

        # Verify all clones registered
        for clone_id in clone_ids:
            assert clone_id in lymphnode.agentes_ativos, f"Clone {clone_id} should be registered"

        # Verify specialization was set
        for clone_id in clone_ids:
            state = lymphnode.agentes_ativos[clone_id]
            assert state.especializacao == "malware_xyz", "Clone should have correct specialization"

    @pytest.mark.asyncio
    async def test_somatic_hypermutation_creates_variation(self, lymphnode):
        """
        Test somatic hypermutation creates variation in clones.

        Real behavior: Clones aren't identical - slight variations in
        sensitivity create diverse immune response (affinity maturation).

        Coverage: Lines 412-416 (somatic hypermutation logic)
        """
        # ARRANGE: Mock AgentFactory
        with patch.object(lymphnode.factory, "create_agent") as mock_create:
            # Track sensitivity variations
            sensitivities = []

            def create_mock_agent():
                mock_agent = MagicMock()
                mock_agent.state = AgenteState(
                    id=f"clone_{len(sensitivities)}",
                    tipo=AgentType.MACROFAGO,
                    status="patrulhando",
                    area_patrulha="subnet_10.0.1.0/24",
                    localizacao_atual="subnet_10.0.1.0/24",
                    sensibilidade=0.5,  # Base sensitivity
                )
                mock_agent.iniciar = AsyncMock()

                # Capture sensitivity after mutation
                async def track_sensibilidade():
                    sensitivities.append(mock_agent.state.sensibilidade)

                mock_agent.iniciar.side_effect = track_sensibilidade
                return mock_agent

            mock_create.side_effect = [create_mock_agent() for _ in range(5)]

            # ACT: Create 5 clones (should have different sensitivities)
            clone_ids = await lymphnode.clonar_agente(
                tipo_base=AgentType.MACROFAGO,
                especializacao="ransomware_abc",
                quantidade=5,
            )

        # ASSERT: Clones should have varied sensitivities (somatic hypermutation)
        assert len(set(sensitivities)) > 1, "Clones should have different sensitivities (mutation)"

        # Verify mutation range (-10% to +10%)
        # Mutation formula: (i * 0.04) - 0.1
        # i=0: -0.1, i=1: -0.06, i=2: -0.02, i=3: +0.02, i=4: +0.06
        expected_base = 0.5
        assert min(sensitivities) < expected_base, "Some clones should have lower sensitivity"
        assert max(sensitivities) > expected_base, "Some clones should have higher sensitivity"

    @pytest.mark.asyncio
    async def test_clonal_expansion_handles_errors_gracefully(self, lymphnode):
        """
        Test clonal expansion continues despite individual failures.

        Real behavior: If some clones fail to mature, others continue
        (biological systems are fault-tolerant).

        Coverage: Lines 428-429 (error handling in clonal expansion)
        """
        # ARRANGE: Mock factory to fail on second clone
        with patch.object(lymphnode.factory, "create_agent") as mock_create:

            def create_agent_with_failure(tipo, **kwargs):
                """Create agent, but fail on second call"""
                call_count = len([c for c in mock_create.call_args_list])

                if call_count == 1:  # Second call (0-indexed)
                    raise Exception("Clone maturation failed")

                # Successful clone
                mock_agent = MagicMock()
                mock_agent.state = AgenteState(
                    id=f"clone_{call_count}",
                    tipo=tipo,
                    status="patrulhando",
                    area_patrulha="subnet_10.0.1.0/24",
                    localizacao_atual="subnet_10.0.1.0/24",
                )
                mock_agent.iniciar = AsyncMock()
                return mock_agent

            mock_create.side_effect = create_agent_with_failure

            # ACT: Request 3 clones (1 will fail)
            clone_ids = await lymphnode.clonar_agente(
                tipo_base=AgentType.NK_CELL,
                especializacao="ddos_attack",
                quantidade=3,
            )

        # ASSERT: Should create 2 clones (skip failed one)
        assert len(clone_ids) == 2, "Should create 2 clones despite 1 failure (fault tolerance)"


# ==================== APOPTOSIS TESTS ====================


class TestApoptosis:
    """Test apoptosis (lymphnode shrinking - "íngua diminuindo")"""

    @pytest.mark.asyncio
    async def test_destruir_clones_triggers_apoptosis(self, lymphnode):
        """
        Test destroying clones triggers apoptosis signal.

        Real behavior: When threat eliminated, excess clones receive
        apoptosis signal and die (lymphnode shrinks back to normal).

        Coverage: Lines 437-469 (complete destruir_clones method)
        """
        # ARRANGE: Register some specialized clones manually
        for i in range(3):
            agent_state = AgenteState(
                id=f"specialized_clone_{i}",
                tipo=AgentType.MACROFAGO,
                status="patrulhando",
                area_patrulha="subnet_10.0.1.0/24",
                localizacao_atual="subnet_10.0.1.0/24",
                especializacao="threat_xyz",  # All have same specialization
            )
            lymphnode.agentes_ativos[agent_state.id] = agent_state

        # Also register one clone with different specialization (should NOT be destroyed)
        other_agent = AgenteState(
            id="other_clone",
            tipo=AgentType.NK_CELL,
            status="patrulhando",
            area_patrulha="subnet_10.0.1.0/24",
            localizacao_atual="subnet_10.0.1.0/24",
            especializacao="different_threat",
        )
        lymphnode.agentes_ativos[other_agent.id] = other_agent

        initial_total = len(lymphnode.agentes_ativos)
        initial_destroyed_count = lymphnode.total_clones_destruidos

        # Mock _send_apoptosis_signal
        with patch.object(lymphnode, "_send_apoptosis_signal", new_callable=AsyncMock):
            # ACT: Destroy clones specialized for "threat_xyz"
            destruidos = await lymphnode.destruir_clones(especializacao="threat_xyz")

        # ASSERT: Should destroy exactly 3 clones
        assert destruidos == 3, "Should destroy 3 specialized clones"
        assert lymphnode.total_clones_destruidos == initial_destroyed_count + 3, "Should increment destruction counter"

        # Verify clones removed from registry
        assert len(lymphnode.agentes_ativos) == initial_total - 3, "Should remove clones from active registry"

        # Verify only specialized clones destroyed (not other_clone)
        assert "other_clone" in lymphnode.agentes_ativos, "Should NOT destroy clones with different specialization"

        for i in range(3):
            assert f"specialized_clone_{i}" not in lymphnode.agentes_ativos, f"Clone {i} should be destroyed"

    @pytest.mark.asyncio
    async def test_send_apoptosis_signal_without_redis(self, lymphnode):
        """
        Test apoptosis signal handles missing Redis gracefully.

        Real behavior: Even without Redis (graceful degradation),
        apoptosis should complete locally.

        Coverage: Lines 478-480 (_send_apoptosis_signal without Redis)
        """
        # ARRANGE: Temporarily disable Redis
        original_redis = lymphnode._redis_client
        lymphnode._redis_client = None

        # ACT: Send apoptosis signal (should not crash)
        try:
            await lymphnode._send_apoptosis_signal("agent_001")
            apoptosis_succeeded = True
        except Exception:
            apoptosis_succeeded = False
        finally:
            lymphnode._redis_client = original_redis

        # ASSERT: Should handle gracefully
        assert apoptosis_succeeded, "Apoptosis should succeed even without Redis (graceful degradation)"


# ==================== SUMMARY ====================

"""
Clonal Expansion & Apoptosis Tests Summary:

Tests Added: 5 comprehensive behavioral tests

Real Immune Behaviors Tested:
✅ Clonal Expansion (lymphnode swelling/"íngua")
   - Creates specialized agent clones
   - Somatic hypermutation (variation in clones)
   - Error handling (fault tolerance)

✅ Apoptosis (lymphnode shrinking)
   - Destroys specialized clones after threat
   - Selective destruction (only matching specialization)
   - Graceful degradation (works without Redis)

Coverage Impact: 61% → ~70%+ (targeting lines 372-480)

These tests validate REAL lymphnode behavior that mirrors biology:
- Lymphnodes swell during infection (clonal expansion)
- Lymphnodes shrink after recovery (apoptosis)
- Each clone has slight variation (affinity maturation)

This is what makes immune systems fascinating! 🦠
"""
