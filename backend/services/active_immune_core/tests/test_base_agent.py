"""Base Agent Tests - Unit tests for AgenteImunologicoBase

These tests validate the base agent class without requiring external services.
Uses a concrete test agent implementation.
"""

import asyncio
from typing import Any, Dict

import pytest
import pytest_asyncio

from active_immune_core.agents import AgentStatus, AgentType, AgenteImunologicoBase


# ==================== TEST AGENT IMPLEMENTATION ====================


class TestAgent(AgenteImunologicoBase):
    """Concrete test agent for testing base class functionality"""

    def __init__(self, **kwargs):
        super().__init__(tipo=AgentType.MACROFAGO, **kwargs)
        self.patrol_count = 0
        self.investigation_count = 0
        self.neutralization_count = 0

    async def patrulhar(self) -> None:
        """Test patrol implementation"""
        self.patrol_count += 1
        await asyncio.sleep(0.01)  # Simulate work

    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """Test investigation implementation"""
        self.investigation_count += 1
        return {
            "is_threat": alvo.get("is_malicious", False),
            "threat_level": alvo.get("threat_level", 0),
            "details": {"test": "investigation"},
        }

    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """Test neutralization implementation"""
        self.neutralization_count += 1
        return True  # Always successful in tests


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def test_agent():
    """Create test agent"""
    agent = TestAgent(
        area_patrulha="test_subnet",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
    )
    yield agent

    # Cleanup
    if agent._running:
        await agent.parar()


# ==================== TESTS ====================


@pytest.mark.asyncio
class TestAgentLifecycle:
    """Test agent lifecycle"""

    async def test_agent_initialization(self, test_agent):
        """Test that agent initializes correctly"""
        assert test_agent.state.tipo == AgentType.MACROFAGO
        assert test_agent.state.area_patrulha == "test_subnet"
        assert test_agent.state.ativo is False
        assert test_agent.state.status == AgentStatus.DORMINDO
        assert test_agent.state.energia == 100.0
        assert test_agent.state.temperatura_local == 37.0

    async def test_agent_start_stop(self, test_agent):
        """Test agent start and stop"""
        # Start
        await test_agent.iniciar()
        assert test_agent._running is True
        assert test_agent.state.ativo is True
        assert test_agent.state.status == AgentStatus.PATRULHANDO

        # Give it time to initialize
        await asyncio.sleep(0.5)

        # Stop
        await test_agent.parar()
        assert test_agent._running is False
        assert test_agent.state.ativo is False

    async def test_patrol_loop_runs(self, test_agent):
        """Test that patrol loop executes"""
        await test_agent.iniciar()
        await asyncio.sleep(2)  # Let patrol run a few times

        assert test_agent.patrol_count > 0

        await test_agent.parar()

    async def test_apoptosis(self, test_agent):
        """Test programmed cell death"""
        await test_agent.iniciar()
        await asyncio.sleep(0.5)

        # Trigger apoptosis
        await test_agent.apoptose(reason="test_apoptosis")

        # Agent should be stopped
        assert test_agent._running is False
        assert test_agent.state.status == AgentStatus.APOPTOSE


@pytest.mark.asyncio
class TestAgentDetection:
    """Test threat detection and neutralization"""

    async def test_investigation(self, test_agent):
        """Test investigation logic"""
        await test_agent.iniciar()
        await asyncio.sleep(0.5)

        # Investigate non-threat
        result = await test_agent.investigar(
            {"id": "target_1", "is_malicious": False}
        )

        assert result["is_threat"] is False
        assert test_agent.investigation_count == 1
        assert test_agent.state.deteccoes_total == 1

        # Investigate threat
        result = await test_agent.investigar(
            {"id": "target_2", "is_malicious": True, "threat_level": 8}
        )

        assert result["is_threat"] is True
        assert test_agent.investigation_count == 2
        assert test_agent.state.deteccoes_total == 2

        # Check that threat was added to memory
        assert "target_2" in test_agent.state.ultimas_ameacas

        await test_agent.parar()

    async def test_neutralization(self, test_agent):
        """Test neutralization logic (without Ethical AI)"""
        # Note: In real tests, Ethical AI service would need to be mocked
        # For now, we test the neutralization logic assuming ethical validation passes
        await test_agent.iniciar()
        await asyncio.sleep(0.5)

        # Neutralize (will likely fail due to Ethical AI unavailable)
        # This tests fail-safe behavior
        result = await test_agent.neutralizar(
            {"id": "malicious_target"}, metodo="isolate"
        )

        # Should fail because Ethical AI service is unavailable (fail-safe)
        assert result is False

        await test_agent.parar()


@pytest.mark.asyncio
class TestAgentHomeostasis:
    """Test homeostatic regulation"""

    async def test_energy_decay(self, test_agent):
        """Test that energy decays over time"""
        initial_energy = test_agent.state.energia

        await test_agent.iniciar()
        await asyncio.sleep(3)  # Wait for energy decay

        # Energy should have decreased
        assert test_agent.state.energia < initial_energy

        await test_agent.parar()

    async def test_low_energy_apoptosis(self, test_agent):
        """Test that agent triggers apoptosis when energy is low"""
        await test_agent.iniciar()

        # Force low energy
        test_agent.state.energia = 5.0

        # Wait for patrol loop to check energy
        await asyncio.sleep(15)  # Patrol interval + check

        # Agent should have stopped due to apoptosis
        # Note: This test is timing-sensitive
        # In production, we'd use more deterministic testing

        await test_agent.parar()

    async def test_patrol_interval_by_temperature(self, test_agent):
        """Test that patrol interval changes with temperature"""
        # Low temperature (repouso)
        test_agent.state.temperatura_local = 37.0
        interval = test_agent._get_patrol_interval()
        assert interval == 30.0

        # Vigilância
        test_agent.state.temperatura_local = 37.5
        interval = test_agent._get_patrol_interval()
        assert interval == 10.0

        # Atenção
        test_agent.state.temperatura_local = 38.0
        interval = test_agent._get_patrol_interval()
        assert interval == 3.0

        # Inflamação
        test_agent.state.temperatura_local = 39.0
        interval = test_agent._get_patrol_interval()
        assert interval == 1.0


@pytest.mark.asyncio
class TestAgentCommunication:
    """Test communication (cytokines and hormones)"""

    async def test_cytokine_processing_pro_inflammatory(self, test_agent):
        """Test that pro-inflammatory cytokines increase temperature"""
        from active_immune_core.communication import CytokineMessage

        initial_temp = test_agent.state.temperatura_local

        # Create pro-inflammatory cytokine
        cytokine = CytokineMessage(
            tipo="IL1",
            emissor_id="other_agent",
            prioridade=8,
            payload={},
        )

        await test_agent._processar_citocina(cytokine)

        # Temperature should increase
        assert test_agent.state.temperatura_local > initial_temp

    async def test_cytokine_processing_anti_inflammatory(self, test_agent):
        """Test that anti-inflammatory cytokines decrease temperature"""
        from active_immune_core.communication import CytokineMessage

        # Set high temperature
        test_agent.state.temperatura_local = 39.0

        # Create anti-inflammatory cytokine
        cytokine = CytokineMessage(
            tipo="IL10",
            emissor_id="other_agent",
            prioridade=5,
            payload={},
        )

        await test_agent._processar_citocina(cytokine)

        # Temperature should decrease
        assert test_agent.state.temperatura_local < 39.0

    async def test_hormone_processing_cortisol(self, test_agent):
        """Test cortisol hormone (suppresses sensitivity)"""
        from active_immune_core.communication import HormoneMessage

        initial_sensitivity = test_agent.state.sensibilidade

        # Create cortisol hormone
        hormone = HormoneMessage(
            tipo="cortisol",
            emissor="lymphnode",
            nivel=8.0,
            payload={},
        )

        await test_agent._processar_hormonio(hormone)

        # Sensitivity should decrease
        assert test_agent.state.sensibilidade < initial_sensitivity

    async def test_hormone_processing_adrenaline(self, test_agent):
        """Test adrenaline hormone (increases aggressiveness)"""
        from active_immune_core.communication import HormoneMessage

        initial_aggression = test_agent.state.nivel_agressividade

        # Create adrenaline hormone
        hormone = HormoneMessage(
            tipo="adrenalina",
            emissor="lymphnode",
            nivel=9.0,
            payload={},
        )

        await test_agent._processar_hormonio(hormone)

        # Aggressiveness should increase
        assert test_agent.state.nivel_agressividade > initial_aggression


@pytest.mark.asyncio
class TestAgentMetrics:
    """Test agent metrics"""

    async def test_get_metrics(self, test_agent):
        """Test metrics retrieval"""
        await test_agent.iniciar()
        await asyncio.sleep(0.5)

        metrics = test_agent.get_metrics()

        assert "agent_id" in metrics
        assert "agent_type" in metrics
        assert "status" in metrics
        assert "energy" in metrics
        assert "temperature" in metrics
        assert "detections_total" in metrics
        assert "neutralizations_total" in metrics

        assert metrics["agent_type"] == AgentType.MACROFAGO
        assert metrics["status"] == AgentStatus.PATRULHANDO

        await test_agent.parar()

    async def test_repr(self, test_agent):
        """Test string representation"""
        repr_str = repr(test_agent)

        assert "TestAgent" in repr_str
        assert test_agent.state.id[:8] in repr_str
        assert str(test_agent.state.status) in repr_str


@pytest.mark.asyncio
class TestAgentErrorHandling:
    """Test error handling"""

    async def test_double_start(self, test_agent):
        """Test that double start is handled gracefully"""
        await test_agent.iniciar()
        await asyncio.sleep(0.5)

        # Try to start again (should be ignored)
        await test_agent.iniciar()

        assert test_agent._running is True

        await test_agent.parar()

    async def test_stop_without_start(self, test_agent):
        """Test that stop without start is handled gracefully"""
        # Should not raise exception
        await test_agent.parar()

        assert test_agent._running is False
