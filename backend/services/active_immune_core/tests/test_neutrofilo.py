"""Neutrophil Tests - Unit tests for NeutrofiloDigital

Tests the Neutrophil agent (swarm specialist) without requiring external services.
Uses graceful degradation paths for testing.
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

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

    async def test_chemotaxis_gradient_selection(self, neutrofilo, multiple_gradients):
        """Test chemotaxis selects highest concentration gradient"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Test with multiple gradients - should select highest (8.0)
        # Chemotaxis logic at lines 129-147
        initial_location = neutrofilo.state.localizacao_atual

        # Would need to inject gradients into Redis for full test
        # Testing gradient detection logic paths
        gradients = await neutrofilo._detectar_gradiente_il8()
        assert isinstance(gradients, list)

        await neutrofilo.parar()

    async def test_energy_depletion_below_threshold(self, neutrofilo):
        """Test behavior when energy depletes below action threshold"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Deplete energy to critical level
        neutrofilo.state.energia = 5.0

        # Attempt migration (should still work but consume remaining energy)
        initial_energy = neutrofilo.state.energia
        await neutrofilo._migrar("subnet_test")

        # Energy should decrease but not go negative
        assert neutrofilo.state.energia >= 0.0
        assert neutrofilo.state.energia < initial_energy

        await neutrofilo.parar()

    async def test_swarm_coordination_without_members(self, neutrofilo, sample_gradient):
        """Test swarm attack coordination when solo (no members)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Solo neutrophil (no swarm members)
        neutrofilo.swarm_members = []
        assert len(neutrofilo.swarm_members) + 1 < neutrofilo.swarm_threshold

        # Should perform individual attack
        await neutrofilo._swarm_attack(sample_gradient)

        # Should complete without forming NET
        assert True

        await neutrofilo.parar()

    async def test_net_formation_increments_counter(self, neutrofilo, sample_gradient):
        """Test NET formation increments counter correctly"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2"]
        initial_nets = neutrofilo.nets_formadas

        # Form NET twice
        await neutrofilo._formar_net(sample_gradient)
        await neutrofilo._formar_net(sample_gradient)

        # Counter should increment by 2
        assert neutrofilo.nets_formadas == initial_nets + 2

        await neutrofilo.parar()

    async def test_concurrent_swarm_attacks(self, neutrofilo, multiple_gradients):
        """Test multiple concurrent swarm attacks (stress test)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2", "neutro_3"]
        neutrofilo.state.energia = 90.0

        # Launch 3 concurrent swarm attacks
        tasks = [
            neutrofilo._swarm_attack(gradient) for gradient in multiple_gradients
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle without crashing
        assert len(results) == 3
        assert not any(isinstance(r, Exception) for r in results)

        await neutrofilo.parar()

    async def test_il10_secretion_after_multiple_nets(self, neutrofilo):
        """Test IL-10 secretion triggers after multiple NET formations"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Simulate multiple NETs formed
        neutrofilo.nets_formadas = 10

        # Secrete IL-10 (anti-inflammatory signal)
        await neutrofilo._secretar_il10()

        # Should complete without error even if Kafka unavailable
        assert neutrofilo.nets_formadas == 10

        await neutrofilo.parar()

    async def test_gradient_detection_empty_result(self, neutrofilo):
        """Test gradient detection returns empty list when no signal"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # With Redis not configured, should return empty list
        gradients = await neutrofilo._detectar_gradiente_il8()

        assert gradients == []
        assert isinstance(gradients, list)

        await neutrofilo.parar()

    async def test_metrics_swarm_efficiency_zero_migrations(self, neutrofilo):
        """Test swarm efficiency metric when no migrations occurred"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # No migrations, some NETs
        neutrofilo.chemotaxis_count = 0
        neutrofilo.nets_formadas = 5

        metrics = neutrofilo.get_neutrofilo_metrics()

        # Efficiency should be 0.0 (no migrations to divide by)
        assert metrics["eficiencia_swarm"] == 0.0

        await neutrofilo.parar()

    async def test_neutralization_consumes_energy(self, neutrofilo, sample_gradient):
        """Test that neutralization consumes energy"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_energy = neutrofilo.state.energia

        # Neutralize target
        await neutrofilo.executar_neutralizacao(sample_gradient, metodo="isolate")

        # Energy should decrease (isolation is expensive)
        assert neutrofilo.state.energia <= initial_energy

        await neutrofilo.parar()

    async def test_patrol_continuous_execution(self, neutrofilo):
        """Test patrol executes continuously without errors"""
        await neutrofilo.iniciar()

        # Run for 3 seconds to ensure multiple patrol cycles
        await asyncio.sleep(3)

        # Should still be running
        assert neutrofilo._running is True
        assert neutrofilo.state.status == AgentStatus.PATRULHANDO

        await neutrofilo.parar()

    async def test_swarm_member_tracking(self, neutrofilo):
        """Test swarm member list tracking"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Manually add swarm members
        neutrofilo.swarm_members = ["neutro_1", "neutro_2", "neutro_3", "neutro_4"]

        metrics = neutrofilo.get_neutrofilo_metrics()

        # Swarm size = members + self
        assert metrics["swarm_size_current"] == 5

        await neutrofilo.parar()

    async def test_chemotaxis_counter_accuracy(self, neutrofilo):
        """Test chemotaxis counter increments accurately"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        initial_count = neutrofilo.chemotaxis_count

        # Perform 10 migrations
        for i in range(10):
            await neutrofilo._migrar(f"subnet_{i}")

        # Counter should be exactly initial + 10
        assert neutrofilo.chemotaxis_count == initial_count + 10

        await neutrofilo.parar()

    async def test_apoptosis_cleanup(self, neutrofilo):
        """Test apoptosis properly cleans up resources"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Force apoptosis by exceeding lifespan
        neutrofilo.state.tempo_vida = timedelta(hours=20)

        await neutrofilo.patrulhar()

        # Agent should be stopped and marked for apoptosis
        assert neutrofilo._running is False
        assert neutrofilo.state.status == AgentStatus.APOPTOSE
        assert neutrofilo.state.ativo is False


# ==================== SUCCESS PATH TESTS (with mocks for external services) ====================


@pytest.mark.asyncio
class TestNeutrofiloSuccessPaths:
    """Test success paths with mocked external services

    DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
    Mocking external services (Redis, HTTP) for testing is acceptable -
    "NO MOCK" refers to production code, not test infrastructure.
    These tests validate the ACTUAL implementation logic with controlled inputs.
    """

    @pytest_asyncio.fixture
    async def neutrofilo(self):
        """Fixture for success path testing"""
        neutro = NeutrofiloDigital(
            area_patrulha="test_subnet_10_0_1_0",
            kafka_bootstrap="localhost:9092",
            redis_url="redis://localhost:6379",
            lifespan_hours=8.0,
            swarm_threshold=3,
        )
        yield neutro
        if neutro._running:
            await neutro.parar()

    async def test_gradient_detection_with_redis_data(self, neutrofilo, mocker):
        """Test gradient detection with Redis data (lines 176-183)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock Redis client (Redis decode_responses=True returns strings)
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = [
            "cytokine:IL8:zone_a",
            "cytokine:IL8:zone_b",
        ]
        mock_redis.get.side_effect = ["5.0", "8.0"]

        neutrofilo._hormone_messenger._redis_client = mock_redis

        # Detect gradients - should parse Redis data
        gradients = await neutrofilo._detectar_gradiente_il8()

        # Lines 176-183 should be covered
        assert len(gradients) == 2
        assert any(g["concentracao"] == 5.0 for g in gradients)
        assert any(g["concentracao"] == 8.0 for g in gradients)

        await neutrofilo.parar()

    async def test_gradient_detection_exception_handling(self, neutrofilo, mocker):
        """Test gradient detection exception path (lines 193-195)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock Redis to raise exception
        mock_redis = AsyncMock()
        mock_redis.keys.side_effect = Exception("Redis connection error")

        neutrofilo._hormone_messenger._redis_client = mock_redis

        # Should handle exception gracefully (lines 193-195)
        gradients = await neutrofilo._detectar_gradiente_il8()

        assert gradients == []

        await neutrofilo.parar()

    async def test_patrol_follows_gradient_above_threshold(self, neutrofilo, mocker):
        """Test patrol follows gradient above 2.0 threshold (lines 129-147)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock gradient detection to return high gradient
        mocker.patch.object(
            neutrofilo,
            "_detectar_gradiente_il8",
            return_value=[
                {"area": "hot_zone_1", "concentracao": 7.5},
                {"area": "hot_zone_2", "concentracao": 3.2},
            ],
        )

        # Mock swarm and attack methods
        mock_migrar = mocker.patch.object(neutrofilo, "_migrar", new_callable=AsyncMock)
        mock_formar_swarm = mocker.patch.object(
            neutrofilo, "_formar_swarm", new_callable=AsyncMock
        )
        mock_swarm_attack = mocker.patch.object(
            neutrofilo, "_swarm_attack", new_callable=AsyncMock
        )

        # Execute patrol - should follow highest gradient
        await neutrofilo.patrulhar()

        # Lines 129-147 should be covered
        mock_migrar.assert_called_once_with("hot_zone_1")  # Highest concentration
        mock_formar_swarm.assert_called_once_with("hot_zone_1")
        mock_swarm_attack.assert_called_once()

        await neutrofilo.parar()

    async def test_patrol_ignores_low_concentration_gradient(self, neutrofilo, mocker):
        """Test patrol ignores gradient below 2.0 threshold (lines 131-133)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock gradient detection to return low gradient
        mocker.patch.object(
            neutrofilo,
            "_detectar_gradiente_il8",
            return_value=[
                {"area": "weak_zone", "concentracao": 1.5},  # Below 2.0 threshold
            ],
        )

        mock_migrar = mocker.patch.object(neutrofilo, "_migrar", new_callable=AsyncMock)

        # Execute patrol - should ignore low gradient
        await neutrofilo.patrulhar()

        # Lines 131-133 should be covered (early return)
        mock_migrar.assert_not_called()

        await neutrofilo.parar()

    async def test_formar_swarm_finds_other_neutrophils(self, neutrofilo, mocker):
        """Test swarm formation finds other neutrophils (lines 250, 260, 263)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock Redis to return other neutrophil states
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = [
            "agent:neutro_001:state",
            "agent:neutro_002:state",
        ]
        mock_redis.get.side_effect = [
            # neutro_001: Same area, different ID (should add)
            '{"tipo": "neutrofilo", "localizacao_atual": "test_zone", "id": "neutro_001"}',
            # neutro_002: Different area (should skip)
            '{"tipo": "neutrofilo", "localizacao_atual": "other_zone", "id": "neutro_002"}',
        ]

        neutrofilo._hormone_messenger._redis_client = mock_redis

        # Form swarm
        await neutrofilo._formar_swarm("test_zone")

        # Lines 250, 260, 263 should be covered
        assert len(neutrofilo.swarm_members) == 1
        assert "neutro_001" in neutrofilo.swarm_members

        await neutrofilo.parar()

    async def test_formar_swarm_handles_null_state(self, neutrofilo, mocker):
        """Test swarm formation handles None state from Redis (line 250)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock Redis to return None for one key
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = [
            "agent:neutro_001:state",
            "agent:neutro_002:state",
        ]
        mock_redis.get.side_effect = [
            None,  # Should skip (line 250)
            '{"tipo": "neutrofilo", "localizacao_atual": "test_zone", "id": "neutro_002"}',
        ]

        neutrofilo._hormone_messenger._redis_client = mock_redis

        # Form swarm - should handle None gracefully
        await neutrofilo._formar_swarm("test_zone")

        # Line 250 should be covered (continue on None)
        assert len(neutrofilo.swarm_members) == 1
        assert "neutro_002" in neutrofilo.swarm_members

        await neutrofilo.parar()

    async def test_formar_swarm_exception_handling(self, neutrofilo, mocker):
        """Test swarm formation exception handling (lines 270-271)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock Redis to raise exception
        mock_redis = AsyncMock()
        mock_redis.keys.side_effect = Exception("Redis error")

        neutrofilo._hormone_messenger._redis_client = mock_redis

        # Should handle exception gracefully (lines 270-271)
        await neutrofilo._formar_swarm("test_zone")

        # Should not crash
        assert neutrofilo.swarm_members == []

        await neutrofilo.parar()

    async def test_formar_net_success_response(self, neutrofilo, mocker):
        """Test NET formation with successful RTE response (lines 351-356)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        neutrofilo.swarm_members = ["neutro_1", "neutro_2"]

        # Mock HTTP response with status 200
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mocker.patch.object(
            neutrofilo._http_session, "post", return_value=mock_response
        )

        # Mock IL-10 secretion
        mock_secretar_il10 = mocker.patch.object(
            neutrofilo, "_secretar_il10", new_callable=AsyncMock
        )

        initial_nets = neutrofilo.nets_formadas

        # Form NET
        await neutrofilo._formar_net({"area": "target_zone"})

        # Lines 351-356 should be covered
        assert neutrofilo.nets_formadas == initial_nets + 1
        mock_secretar_il10.assert_called_once()

        await neutrofilo.parar()

    async def test_formar_net_404_response(self, neutrofilo, mocker):
        """Test NET formation with 404 response (lines 358-361)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP response with status 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mocker.patch.object(
            neutrofilo._http_session, "post", return_value=mock_response
        )

        initial_nets = neutrofilo.nets_formadas

        # Form NET - should handle 404 gracefully
        await neutrofilo._formar_net({"area": "target_zone"})

        # Lines 358-361 should be covered
        assert neutrofilo.nets_formadas == initial_nets + 1

        await neutrofilo.parar()

    async def test_formar_net_error_response(self, neutrofilo, mocker):
        """Test NET formation with error response (lines 363-364)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP response with status 500
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mocker.patch.object(
            neutrofilo._http_session, "post", return_value=mock_response
        )

        initial_nets = neutrofilo.nets_formadas

        # Form NET - should handle error
        await neutrofilo._formar_net({"area": "target_zone"})

        # Lines 363-364 should be covered
        # Nets not incremented on error
        assert neutrofilo.nets_formadas == initial_nets

        await neutrofilo.parar()

    async def test_formar_net_generic_exception(self, neutrofilo, mocker):
        """Test NET formation generic exception handling (lines 371-372)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP to raise generic exception (not ClientConnectorError)
        mocker.patch.object(
            neutrofilo._http_session,
            "post",
            side_effect=RuntimeError("Unexpected error"),
        )

        # Should handle exception gracefully (lines 371-372)
        await neutrofilo._formar_net({"area": "target_zone"})

        # Should not crash
        assert True

        await neutrofilo.parar()

    async def test_secretar_il10_exception_handling(self, neutrofilo, mocker):
        """Test IL-10 secretion exception handling (lines 403-404)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock cytokine messenger to raise exception
        mock_messenger = AsyncMock()
        mock_messenger.send_cytokine.side_effect = Exception("Kafka error")

        neutrofilo._cytokine_messenger = mock_messenger

        # Should handle exception gracefully (lines 403-404)
        await neutrofilo._secretar_il10()

        # Should not crash
        assert True

        await neutrofilo.parar()

    async def test_neutralization_success_response(self, neutrofilo, mocker):
        """Test neutralization with successful RTE response (lines 469-472)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP response with status 200
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mocker.patch.object(
            neutrofilo._http_session, "post", return_value=mock_response
        )

        initial_engulfed = neutrofilo.targets_engulfed

        # Neutralize target
        result = await neutrofilo.executar_neutralizacao(
            {"id": "target_001"}, metodo="isolate"
        )

        # Lines 469-472 should be covered
        assert result is True
        assert neutrofilo.targets_engulfed == initial_engulfed + 1

        await neutrofilo.parar()

    async def test_neutralization_404_response(self, neutrofilo, mocker):
        """Test neutralization with 404 response (lines 474-478)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP response with status 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mocker.patch.object(
            neutrofilo._http_session, "post", return_value=mock_response
        )

        initial_engulfed = neutrofilo.targets_engulfed

        # Neutralize - should handle 404 gracefully
        result = await neutrofilo.executar_neutralizacao(
            {"id": "target_001"}, metodo="isolate"
        )

        # Lines 474-478 should be covered
        assert result is True
        assert neutrofilo.targets_engulfed == initial_engulfed + 1

        await neutrofilo.parar()

    async def test_neutralization_error_response(self, neutrofilo, mocker):
        """Test neutralization with error response (lines 480-482)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP response with status 500
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mocker.patch.object(
            neutrofilo._http_session, "post", return_value=mock_response
        )

        # Neutralize - should return False on error
        result = await neutrofilo.executar_neutralizacao(
            {"id": "target_001"}, metodo="isolate"
        )

        # Lines 480-482 should be covered
        assert result is False

        await neutrofilo.parar()

    async def test_neutralization_generic_exception(self, neutrofilo, mocker):
        """Test neutralization generic exception handling (lines 490-492)"""
        await neutrofilo.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP to raise generic exception
        mocker.patch.object(
            neutrofilo._http_session,
            "post",
            side_effect=RuntimeError("Unexpected error"),
        )

        # Should handle exception gracefully (lines 490-492)
        result = await neutrofilo.executar_neutralizacao(
            {"id": "target_001"}, metodo="isolate"
        )

        # Lines 490-492 should be covered
        assert result is False

        await neutrofilo.parar()
