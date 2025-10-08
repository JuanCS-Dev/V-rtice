"""
Smoke Test - Neuromodulation Integration (FASE 1 Validation)

Quick validation that all components work together:
1. Create coordinator with all 4 modulators
2. Apply various modulation patterns
3. Verify bounds [0, 1] maintained
4. Verify conflict resolution works
5. Verify interactions work
6. Verify circuit breakers protect system
7. Verify emergency stop works

This is a REAL integration test - no mocks.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import pytest
from consciousness.neuromodulation.coordinator_hardened import (
    NeuromodulationCoordinator,
    CoordinatorConfig,
    ModulationRequest,
)


def test_smoke_create_coordinator():
    """Smoke test: Create coordinator successfully."""
    coordinator = NeuromodulationCoordinator()

    # All 4 modulators initialized
    assert coordinator.dopamine is not None
    assert coordinator.serotonin is not None
    assert coordinator.acetylcholine is not None
    assert coordinator.norepinephrine is not None

    # All at baseline
    levels = coordinator.get_levels()
    assert levels["dopamine"] == pytest.approx(0.5, abs=1e-6)
    assert levels["serotonin"] == pytest.approx(0.6, abs=1e-6)
    assert levels["acetylcholine"] == pytest.approx(0.4, abs=1e-6)
    assert levels["norepinephrine"] == pytest.approx(0.3, abs=1e-6)


def test_smoke_modulate_all_four():
    """Smoke test: Modulate all 4 modulators."""
    config = CoordinatorConfig(max_simultaneous_modulations=4)
    coordinator = NeuromodulationCoordinator(config)

    requests = [
        ModulationRequest("dopamine", delta=0.2, source="smoke_test"),
        ModulationRequest("serotonin", delta=0.1, source="smoke_test"),
        ModulationRequest("acetylcholine", delta=0.3, source="smoke_test"),
        ModulationRequest("norepinephrine", delta=0.4, source="smoke_test"),
    ]

    results = coordinator.coordinate_modulation(requests)

    # All modulations executed
    assert len(results) == 4
    assert all(name in results for name in ["dopamine", "serotonin", "acetylcholine", "norepinephrine"])

    # All levels still bounded [0, 1]
    levels = coordinator.get_levels()
    for name, level in levels.items():
        assert 0.0 <= level <= 1.0, f"{name} level {level} out of bounds"


def test_smoke_bounds_under_stress():
    """Smoke test: Bounds maintained under heavy stress."""
    config = CoordinatorConfig(max_simultaneous_modulations=4)
    coordinator = NeuromodulationCoordinator(config)

    # Apply 50 random modulations
    for i in range(50):
        requests = [
            ModulationRequest("dopamine", delta=0.5 if i % 2 == 0 else -0.3, source="stress"),
            ModulationRequest("serotonin", delta=0.4 if i % 3 == 0 else -0.2, source="stress"),
            ModulationRequest("acetylcholine", delta=0.6 if i % 5 == 0 else -0.4, source="stress"),
            ModulationRequest("norepinephrine", delta=0.7 if i % 7 == 0 else -0.5, source="stress"),
        ]

        try:
            coordinator.coordinate_modulation(requests)
        except RuntimeError:
            # Circuit breaker may open - this is expected and safe
            break

    # All levels STILL bounded [0, 1]
    levels = coordinator.get_levels()
    for name, level in levels.items():
        assert 0.0 <= level <= 1.0, f"{name} level {level} out of bounds after stress"


def test_smoke_conflict_resolution():
    """Smoke test: Conflict resolution prevents runaway."""
    # Lower conflict threshold so conflicts are detected
    config = CoordinatorConfig(conflict_threshold=0.3)
    coordinator = NeuromodulationCoordinator(config)

    # Repeatedly try to increase both DA and 5HT (conflict)
    for _ in range(20):
        requests = [
            ModulationRequest("dopamine", delta=0.8, source="conflict_test"),
            ModulationRequest("serotonin", delta=0.8, source="conflict_test"),
        ]

        try:
            coordinator.coordinate_modulation(requests)
        except RuntimeError:
            break

    # Conflicts should have been detected and resolved
    assert coordinator.conflicts_detected > 0
    assert coordinator.conflicts_resolved > 0

    # Levels still bounded
    assert 0.0 <= coordinator.dopamine.level <= 1.0
    assert 0.0 <= coordinator.serotonin.level <= 1.0


def test_smoke_interactions():
    """Smoke test: Non-linear interactions apply correctly."""
    config = CoordinatorConfig(max_simultaneous_modulations=4)
    coordinator = NeuromodulationCoordinator(config)

    # ACh + NE synergy
    requests = [
        ModulationRequest("acetylcholine", delta=0.3, source="synergy"),
        ModulationRequest("norepinephrine", delta=0.3, source="synergy"),
    ]

    initial_ach = coordinator.acetylcholine.level
    initial_ne = coordinator.norepinephrine.level

    results = coordinator.coordinate_modulation(requests)

    final_ach = coordinator.acetylcholine.level
    final_ne = coordinator.norepinephrine.level

    # Both increased (synergy)
    assert final_ach > initial_ach
    assert final_ne > initial_ne

    # Still bounded
    assert 0.0 <= final_ach <= 1.0
    assert 0.0 <= final_ne <= 1.0


def test_smoke_circuit_breaker_protection():
    """Smoke test: Circuit breaker protects against runaway."""
    config = CoordinatorConfig(max_simultaneous_modulations=1)
    coordinator = NeuromodulationCoordinator(config)

    # Try to push dopamine way above 1.0 (should trigger circuit breaker)
    for i in range(20):
        try:
            requests = [ModulationRequest("dopamine", delta=0.8, source="runaway")]
            coordinator.coordinate_modulation(requests)
        except RuntimeError as e:
            # Circuit breaker opened (expected)
            assert "circuit breaker" in str(e).lower()
            break

    # Dopamine never exceeded 1.0
    assert coordinator.dopamine.level <= 1.0


def test_smoke_emergency_stop():
    """Smoke test: Emergency stop shuts down all modulators."""
    config = CoordinatorConfig(max_simultaneous_modulations=4)
    coordinator = NeuromodulationCoordinator(config)

    # Modulate all
    requests = [
        ModulationRequest("dopamine", delta=0.3, source="test"),
        ModulationRequest("serotonin", delta=0.2, source="test"),
        ModulationRequest("acetylcholine", delta=0.3, source="test"),
        ModulationRequest("norepinephrine", delta=0.4, source="test"),
    ]
    coordinator.coordinate_modulation(requests)

    # Emergency stop
    coordinator.emergency_stop()

    # All circuit breakers open
    assert coordinator.dopamine._circuit_breaker_open is True
    assert coordinator.serotonin._circuit_breaker_open is True
    assert coordinator.acetylcholine._circuit_breaker_open is True
    assert coordinator.norepinephrine._circuit_breaker_open is True

    # All returned to baseline
    assert coordinator.dopamine._level == coordinator.dopamine.config.baseline
    assert coordinator.serotonin._level == coordinator.serotonin.config.baseline
    assert coordinator.acetylcholine._level == coordinator.acetylcholine.config.baseline
    assert coordinator.norepinephrine._level == coordinator.norepinephrine.config.baseline


def test_smoke_metrics_export():
    """Smoke test: Health metrics export works."""
    coordinator = NeuromodulationCoordinator()

    metrics = coordinator.get_health_metrics()

    # Has all 4 modulators' metrics
    assert "dopamine_level" in metrics
    assert "serotonin_level" in metrics
    assert "acetylcholine_level" in metrics
    assert "norepinephrine_level" in metrics

    # Has coordination metrics
    assert "neuromod_total_coordinations" in metrics
    assert "neuromod_conflicts_detected" in metrics
    assert "neuromod_conflict_rate" in metrics
    assert "neuromod_aggregate_circuit_breaker_open" in metrics

    # All numeric values
    for key, value in metrics.items():
        assert isinstance(value, (int, float, bool)), f"{key} has non-numeric value: {value}"


def test_smoke_aggregate_breaker():
    """Smoke test: Aggregate circuit breaker triggers when ≥3 modulators fail."""
    coordinator = NeuromodulationCoordinator()

    # Manually open 3 modulators (simulate failures)
    coordinator.dopamine._circuit_breaker_open = True
    coordinator.serotonin._circuit_breaker_open = True
    coordinator.acetylcholine._circuit_breaker_open = True

    # Aggregate breaker should be open
    assert coordinator._is_aggregate_circuit_breaker_open() is True

    # Modulation should be rejected
    requests = [ModulationRequest("norepinephrine", delta=0.1, source="test")]

    with pytest.raises(RuntimeError, match="Aggregate circuit breaker OPEN"):
        coordinator.coordinate_modulation(requests)


def test_smoke_full_lifecycle():
    """Smoke test: Full lifecycle - create, modulate, monitor, shutdown."""
    config = CoordinatorConfig(max_simultaneous_modulations=4)
    coordinator = NeuromodulationCoordinator(config)

    # 1. Initial state
    initial_levels = coordinator.get_levels()
    assert all(0.0 <= v <= 1.0 for v in initial_levels.values())

    # 2. Apply modulations (reward scenario: DA↑, ACh↑, NE↑)
    for _ in range(10):
        requests = [
            ModulationRequest("dopamine", delta=0.1, source="reward"),
            ModulationRequest("acetylcholine", delta=0.05, source="attention"),
            ModulationRequest("norepinephrine", delta=0.08, source="arousal"),
        ]
        coordinator.coordinate_modulation(requests)

    # 3. Check metrics
    metrics = coordinator.get_health_metrics()
    assert metrics["neuromod_total_coordinations"] == 10
    assert metrics["dopamine_total_modulations"] >= 10

    # 4. Verify bounds maintained
    final_levels = coordinator.get_levels()
    assert all(0.0 <= v <= 1.0 for v in final_levels.values())

    # 5. Emergency shutdown
    coordinator.emergency_stop()
    assert all(mod._circuit_breaker_open for mod in coordinator._modulators.values())


if __name__ == "__main__":
    # Run smoke tests standalone
    pytest.main([__file__, "-v"])
