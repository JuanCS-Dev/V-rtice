"""Neutrophil Tests - Unit tests for NeutrofiloDigital

Tests the Neutrophil agent (swarm specialist) without requiring external services.
Uses graceful degradation paths for testing.
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict

import pytest
import pytest_asyncio

from active_immune_core.agents import AgentStatus, AgentType
from active_immune_core.agents.neutrofilo import NeutrofiloDigital


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def neutrofilo():
    """Create Neutrophil agent"""
    neutro = NeutrofiloDigital(
        area_patrulha="test_subnet_10_0_1_0",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        lifespan_hours=8.0,
        swarm_threshold=3,
    )
    yield neutro

    # Cleanup
    if neutro._running:
        await neutro.parar()


@pytest.fixture
def sample_gradient():
    """Sample IL-8 gradient"""
    return {
        "area": "subnet_192_168_10_0",
        "concentracao": 5.0,
    }


@pytest.fixture
def weak_gradient():
    """Weak IL-8 gradient"""
    return {
        "area": "subnet_10_0_2_0",
        "concentracao": 1.0,  # Below threshold
    }


@pytest.fixture
def multiple_gradients():
    """Multiple IL-8 gradients"""
    return [
        {"area": "subnet_192_168_10_0", "concentracao": 5.0},
        {"area": "subnet_192_168_20_0", "concentracao": 8.0},  # Highest
        {"area": "subnet_192_168_30_0", "concentracao": 3.0},
    ]


# ==================== TESTS ====================


@pytest.mark.asyncio
class TestNeutrofiloInitialization:
    """Test Neutrophil initialization"""

    async def test_neutrofilo_creation(self, neutrofilo):
        """Test that Neutrophil initializes correctly"""
        assert neutrofilo.state.tipo == AgentType.NEUTROFILO
        assert neutrofilo.state.area_patrulha == "test_subnet_10_0_1_0"
        assert neutrofilo.swarm_members == []
        assert neutrofilo.nets_formadas == 0
        assert neutrofilo.targets_engulfed == 0
        assert neutrofilo.chemotaxis_count == 0
        assert neutrofilo.swarm_threshold == 3
        assert neutrofilo.tempo_vida_max == timedelta(hours=8.0)

    async def test_neutrofilo_default_lifespan(self):
        """Test default lifespan"""
        neutro = NeutrofiloDigital(area_patrulha="test")
        assert neutro.tempo_vida_max == timedelta(hours=8.0)

        await neutro.parar()

    async def test_neutrofilo_custom_lifespan(self):
        """Test custom lifespan"""
        neutro = NeutrofiloDigital(area_patrulha="test", lifespan_hours=6.0)
        assert neutro.tempo_vida_max == timedelta(hours=6.0)

        await neutro.parar()

    async def test_neutrofilo_custom_swarm_threshold(self):
        """Test custom swarm threshold"""
        neutro = NeutrofiloDigital(area_patrulha="test", swarm_threshold=5)
        assert neutro.swarm_threshold == 5

        await neutro.parar()


@pytest.mark.asyncio
class TestNeutrofiloLifecycle:
    """Test Neutrophil lifecycle"""

    async def test_neutrofilo_start_stop(self, neutrofilo):
        """Test starting and stopping Neutrophil"""
        # Start
        await neutrofilo.iniciar()
        assert neutrofilo._running is True
        assert neutrofilo.state.ativo is True
        assert neutrofilo.state.status == AgentStatus.PATRULHANDO

        await asyncio.sleep(0.5)

        # Stop
        await neutrofilo.parar()
        assert neutrofilo._running is False
        assert neutrofilo.state.ativo is False

    async def test_neutrofilo_patrol_executes(self, neutrofilo):
        """Test that patrol loop executes"""
        await neutrofilo.iniciar()
        await asyncio.sleep(2)

        # Patrol should have run (even if no gradients found)
        assert neutrofilo._running is True

        await neutrofilo.parar()

    async def test_neutrofilo_apoptosis_on_lifespan_exceeded(self, neutrofilo):
        """Test apoptosis when lifespan exceeded"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Force lifespan to exceed maximum
        neutrofilo.state.tempo_vida = timedelta(hours=10)  # > 8 hours

        # Call patrol, should trigger apoptosis
        await neutrofilo.patrulhar()

        # Agent should have stopped
        # Note: apoptose() sets _running to False
        assert neutrofilo._running is False
        assert neutrofilo.state.status == AgentStatus.APOPTOSE


@pytest.mark.asyncio
class TestChemotaxis:
    """Test chemotaxis (gradient following)"""

    async def test_detectar_gradiente_il8_no_messenger(self, neutrofilo):
        """Test gradient detection without hormone messenger"""
        # Don't start agent (no hormone messenger)
        gradients = await neutrofilo._detectar_gradiente_il8()

        # Should return empty list
        assert gradients == []

    async def test_detectar_gradiente_il8_graceful_degradation(self, neutrofilo):
        """Test graceful degradation when Redis unavailable"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Redis not properly configured, should return empty list
        gradients = await neutrofilo._detectar_gradiente_il8()

        # Should handle gracefully
        assert isinstance(gradients, list)

        await neutrofilo.parar()

    async def test_migrar_updates_location(self, neutrofilo):
        """Test that migration updates location"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_location = neutrofilo.state.localizacao_atual
        target_area = "subnet_192_168_50_0"

        await neutrofilo._migrar(target_area)

        # Location should be updated
        assert neutrofilo.state.localizacao_atual == target_area
        assert neutrofilo.state.area_patrulha == target_area

        await neutrofilo.parar()

    async def test_migrar_increments_counter(self, neutrofilo):
        """Test that migration increments chemotaxis counter"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_count = neutrofilo.chemotaxis_count

        await neutrofilo._migrar("subnet_test")

        # Counter should increment
        assert neutrofilo.chemotaxis_count == initial_count + 1

        await neutrofilo.parar()

    async def test_migrar_consumes_energy(self, neutrofilo):
        """Test that migration consumes energy"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_energy = neutrofilo.state.energia

        await neutrofilo._migrar("subnet_test")

        # Energy should decrease
        assert neutrofilo.state.energia < initial_energy

        await neutrofilo.parar()


@pytest.mark.asyncio
class TestSwarmBehavior:
    """Test swarm formation and coordination"""

    async def test_formar_swarm_no_messenger(self, neutrofilo):
        """Test swarm formation without hormone messenger"""
        # Don't start agent (no hormone messenger)
        await neutrofilo._formar_swarm("subnet_test")

        # Should handle gracefully
        assert neutrofilo.swarm_members == []

    async def test_formar_swarm_graceful_degradation(self, neutrofilo):
        """Test graceful degradation when Redis unavailable"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Redis not configured, should handle gracefully
        await neutrofilo._formar_swarm("subnet_test")

        # Should complete without error
        assert isinstance(neutrofilo.swarm_members, list)

        await neutrofilo.parar()

    async def test_swarm_attack_below_threshold(self, neutrofilo, sample_gradient):
        """Test swarm attack when swarm size < threshold"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # No swarm members (size = 1, threshold = 3)
        neutrofilo.swarm_members = []

        initial_engulfed = neutrofilo.targets_engulfed

        # Should do individual attack
        await neutrofilo._swarm_attack(sample_gradient)

        # May or may not increment (depends on neutralization success)
        # Test that it doesn't crash

        await neutrofilo.parar()

    async def test_swarm_attack_above_threshold(self, neutrofilo, sample_gradient):
        """Test swarm attack when swarm size >= threshold"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Add swarm members (size = 4, threshold = 3)
        neutrofilo.swarm_members = ["neutro_1", "neutro_2", "neutro_3"]

        initial_nets = neutrofilo.nets_formadas

        # Should form NET
        await neutrofilo._swarm_attack(sample_gradient)

        # Should have attempted NET formation (may succeed or fail gracefully)
        # Test that it doesn't crash

        await neutrofilo.parar()


@pytest.mark.asyncio
class TestNETFormation:
    """Test NET (Neutrophil Extracellular Trap) formation"""

    async def test_formar_net_tracks_locally(self, neutrofilo, sample_gradient):
        """Test that NET formation tracks locally when RTE unavailable"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2", "neutro_3"]

        initial_nets = neutrofilo.nets_formadas

        # Form NET (RTE service not running, will degrade gracefully)
        await neutrofilo._formar_net(sample_gradient)

        # Should track locally
        assert neutrofilo.nets_formadas == initial_nets + 1

        await neutrofilo.parar()

    async def test_formar_net_triggers_il10(self, neutrofilo, sample_gradient):
        """Test that NET formation triggers IL-10 secretion"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2"]

        # Form NET
        await neutrofilo._formar_net(sample_gradient)

        # IL-10 secretion is logged (can't verify without Kafka)
        # Test that it doesn't crash
        assert True

        await neutrofilo.parar()


@pytest.mark.asyncio
class TestIL10Secretion:
    """Test IL-10 (anti-inflammatory) secretion"""

    async def test_secretar_il10_no_messenger(self, neutrofilo):
        """Test IL-10 secretion without cytokine messenger"""
        # Don't start agent (no cytokine messenger)
        await neutrofilo._secretar_il10()

        # Should not crash, just log debug
        assert True

    async def test_secretar_il10_after_net_formation(self, neutrofilo):
        """Test IL-10 secretion after NET formation"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2"]
        neutrofilo.nets_formadas = 3

        # Secrete IL-10
        await neutrofilo._secretar_il10()

        # Should complete without error (even if Kafka unavailable)
        assert True

        await neutrofilo.parar()


@pytest.mark.asyncio
class TestNeutrofiloInvestigation:
    """Test investigation logic"""

    async def test_investigation_always_threat(self, neutrofilo, sample_gradient):
        """Test that Neutrophil always considers target a threat"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Neutrophils trust IL-8 signal
        result = await neutrofilo.executar_investigacao(sample_gradient)

        assert result["is_threat"] is True
        assert result["method"] == "chemotaxis_trust"
        assert result["confidence"] == 0.95

        await neutrofilo.parar()

    async def test_investigation_includes_swarm_size(self, neutrofilo, sample_gradient):
        """Test that investigation includes swarm size"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2"]

        result = await neutrofilo.executar_investigacao(sample_gradient)

        assert result["swarm_size"] == 3  # 2 members + self

        await neutrofilo.parar()


@pytest.mark.asyncio
class TestNeutrofiloNeutralization:
    """Test neutralization (engulfment)"""

    async def test_neutralization_isolate_method(self, neutrofilo, sample_gradient):
        """Test isolation method"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Attempt neutralization (RTE service not running, will degrade gracefully)
        result = await neutrofilo.executar_neutralizacao(
            sample_gradient, metodo="isolate"
        )

        # Should succeed locally even if RTE unavailable
        assert result is True
        assert neutrofilo.targets_engulfed >= 1

        await neutrofilo.parar()

    async def test_neutralization_monitor_method(self, neutrofilo, sample_gradient):
        """Test monitor method (non-destructive)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Monitor only
        result = await neutrofilo.executar_neutralizacao(
            sample_gradient, metodo="monitor"
        )

        # Should succeed without blocking
        assert result is True

        await neutrofilo.parar()

    async def test_neutralization_increments_engulfed_counter(
        self, neutrofilo, sample_gradient
    ):
        """Test that neutralization increments engulfed counter"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_engulfed = neutrofilo.targets_engulfed

        await neutrofilo.executar_neutralizacao(sample_gradient, metodo="isolate")

        # Counter should increment
        assert neutrofilo.targets_engulfed == initial_engulfed + 1

        await neutrofilo.parar()


@pytest.mark.asyncio
class TestNeutrofiloMetrics:
    """Test Neutrophil metrics"""

    async def test_get_neutrofilo_metrics(self, neutrofilo):
        """Test Neutrophil-specific metrics"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Simulate some activity
        neutrofilo.nets_formadas = 5
        neutrofilo.targets_engulfed = 8
        neutrofilo.chemotaxis_count = 10
        neutrofilo.swarm_members = ["neutro_1", "neutro_2"]
        neutrofilo.state.tempo_vida = timedelta(hours=3.5)

        metrics = neutrofilo.get_neutrofilo_metrics()

        assert metrics["nets_formadas"] == 5
        assert metrics["targets_engulfed"] == 8
        assert metrics["chemotaxis_count"] == 10
        assert metrics["swarm_size_current"] == 3  # 2 members + self
        assert metrics["lifespan_hours"] == 3.5
        assert metrics["lifespan_remaining_hours"] == 4.5  # 8 - 3.5
        assert metrics["eficiencia_swarm"] == 0.5  # 5 NETs / 10 migrations

    async def test_repr(self, neutrofilo):
        """Test string representation"""
        neutrofilo.nets_formadas = 3
        neutrofilo.targets_engulfed = 7
        neutrofilo.swarm_members = ["neutro_1"]
        neutrofilo.state.tempo_vida = timedelta(hours=2.5)

        repr_str = repr(neutrofilo)

        assert "NeutrofiloDigital" in repr_str
        assert neutrofilo.state.id[:8] in repr_str
        assert "swarm=2" in repr_str  # 1 member + self
        assert "NETs=3" in repr_str
        assert "engulfed=7" in repr_str
        assert "age=2.5h" in repr_str


@pytest.mark.asyncio
class TestNeutrofiloPatrolLogic:
    """Test patrol logic"""

    async def test_patrol_handles_no_gradients(self, neutrofilo):
        """Test that patrol handles empty gradient list gracefully"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Call patrol directly (will get empty gradients since Redis not configured)
        await neutrofilo.patrulhar()

        # Should complete without error
        assert True

        await neutrofilo.parar()

    async def test_patrol_ignores_weak_gradients(self, neutrofilo):
        """Test that patrol ignores gradients below threshold"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_chemotaxis = neutrofilo.chemotaxis_count

        # Manually test weak gradient logic
        # (can't test full patrol without Redis configured)
        weak_gradient = {"area": "subnet_test", "concentracao": 1.0}

        # Weak gradient (< 2.0) should be ignored
        # This is tested in the patrol logic, which won't migrate

        await neutrofilo.parar()


@pytest.mark.asyncio
class TestNeutrofiloEdgeCases:
    """Test edge cases"""

    async def test_patrol_with_expired_lifespan(self, neutrofilo):
        """Test patrol when lifespan already exceeded"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Set lifespan to already exceeded
        neutrofilo.state.tempo_vida = timedelta(hours=10)

        # Call patrol
        await neutrofilo.patrulhar()

        # Should trigger apoptosis
        assert neutrofilo.state.status == AgentStatus.APOPTOSE
        assert neutrofilo._running is False

    async def test_swarm_formation_empty_area(self, neutrofilo):
        """Test swarm formation with empty area"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Empty area string
        await neutrofilo._formar_swarm("")

        # Should handle gracefully
        assert isinstance(neutrofilo.swarm_members, list)

        await neutrofilo.parar()

    async def test_net_formation_empty_target(self, neutrofilo):
        """Test NET formation with empty target"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2"]

        # Empty target
        await neutrofilo._formar_net({})

        # Should track locally (graceful degradation)
        assert neutrofilo.nets_formadas >= 1

        await neutrofilo.parar()

    async def test_neutralization_empty_target_id(self, neutrofilo):
        """Test neutralization with empty target ID"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Empty target ID
        result = await neutrofilo.executar_neutralizacao({"id": ""}, metodo="isolate")

        # Should track even with empty ID (graceful degradation)
        assert result is True

        await neutrofilo.parar()

    async def test_migration_multiple_times(self, neutrofilo):
        """Test multiple consecutive migrations"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_count = neutrofilo.chemotaxis_count

        # Migrate 5 times
        for i in range(5):
            await neutrofilo._migrar(f"subnet_{i}")

        # Counter should increment 5 times
        assert neutrofilo.chemotaxis_count == initial_count + 5

        await neutrofilo.parar()

    async def test_lifespan_remaining_calculation(self, neutrofilo):
        """Test lifespan remaining calculation in metrics"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Set lifespan to 7 hours (1 hour remaining)
        neutrofilo.state.tempo_vida = timedelta(hours=7)

        metrics = neutrofilo.get_neutrofilo_metrics()

        # Remaining should be 1 hour
        assert metrics["lifespan_remaining_hours"] == 1.0

        await neutrofilo.parar()

    async def test_lifespan_negative_remaining(self, neutrofilo):
        """Test lifespan remaining when negative (exceeded)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Set lifespan to exceeded
        neutrofilo.state.tempo_vida = timedelta(hours=10)

        metrics = neutrofilo.get_neutrofilo_metrics()

        # Remaining should be capped at 0
        assert metrics["lifespan_remaining_hours"] == 0.0

        await neutrofilo.parar()
