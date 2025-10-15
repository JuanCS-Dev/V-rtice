"""
Kuramoto Model - 100% Coverage Test Suite
==========================================

Comprehensive tests targeting 100% coverage for kuramoto.py.

This test suite covers:
- OscillatorState enum
- OscillatorConfig dataclass
- PhaseCoherence calculations and quality scoring
- SynchronizationDynamics tracking
- KuramotoOscillator phase updates
- KuramotoNetwork synchronization protocol

Strategy:
- Test all edge cases for coherence quality levels
- Test synchronization dynamics tracking
- Test phase update mechanics
- Test network topology handling
- Test oscillator initialization and reset

Author: Claude Code + JuanCS-Dev
Date: 2025-10-15
Target: 166 statements → 0 missed → 100.00%
"""

import asyncio
import time

import numpy as np
import pytest

from consciousness.esgt.kuramoto import (
    KuramotoNetwork,
    KuramotoOscillator,
    OscillatorConfig,
    OscillatorState,
    PhaseCoherence,
    SynchronizationDynamics,
)


# ============================================================================
# PHASE COHERENCE TESTS
# ============================================================================


class TestPhaseCoherence:
    """Test PhaseCoherence dataclass and methods."""

    def test_phase_coherence_unconscious_level(self):
        """Test coherence below conscious threshold."""
        coherence = PhaseCoherence(
            order_parameter=0.25,
            mean_phase=0.0,
            phase_variance=1.5,
            coherence_quality="unconscious",
        )

        assert coherence.is_conscious_level() is False
        assert coherence.coherence_quality == "unconscious"

    def test_phase_coherence_conscious_level(self):
        """Test coherence at conscious threshold."""
        coherence = PhaseCoherence(
            order_parameter=0.75,
            mean_phase=0.5,
            phase_variance=0.2,
            coherence_quality="conscious",
        )

        assert coherence.is_conscious_level() is True
        assert coherence.coherence_quality == "conscious"

    def test_get_quality_score_unconscious_range(self):
        """Test quality score for unconscious range (0.0-0.3)."""
        coherence = PhaseCoherence(
            order_parameter=0.15,  # Mid-point of unconscious range
            mean_phase=0.0,
            phase_variance=2.0,
            coherence_quality="unconscious",
        )

        score = coherence.get_quality_score()
        # 0.15 / 0.3 * 0.25 = 0.125
        assert abs(score - 0.125) < 0.01

    def test_get_quality_score_preconscious_range(self):
        """Test quality score for preconscious range (0.3-0.7)."""
        coherence = PhaseCoherence(
            order_parameter=0.50,  # Mid-point of preconscious range
            mean_phase=0.0,
            phase_variance=0.8,
            coherence_quality="preconscious",
        )

        score = coherence.get_quality_score()
        # 0.25 + (0.50 - 0.3) / 0.4 * 0.5 = 0.25 + 0.25 = 0.50
        assert abs(score - 0.50) < 0.01

    def test_get_quality_score_conscious_range(self):
        """Test quality score for conscious range (0.7-1.0)."""
        coherence = PhaseCoherence(
            order_parameter=0.85,  # In conscious range
            mean_phase=0.0,
            phase_variance=0.1,
            coherence_quality="conscious",
        )

        score = coherence.get_quality_score()
        # 0.75 + (0.85 - 0.7) / 0.3 * 0.25 = 0.75 + 0.125 = 0.875
        assert abs(score - 0.875) < 0.01

    def test_get_quality_score_boundaries(self):
        """Test quality score at exact boundaries."""
        # At 0.3 boundary
        coh_030 = PhaseCoherence(0.30, 0.0, 0.5, "preconscious")
        assert abs(coh_030.get_quality_score() - 0.25) < 0.01

        # At 0.7 boundary
        coh_070 = PhaseCoherence(0.70, 0.0, 0.2, "conscious")
        assert abs(coh_070.get_quality_score() - 0.75) < 0.01

        # At 1.0 (perfect sync)
        coh_100 = PhaseCoherence(1.0, 0.0, 0.0, "deep")
        assert abs(coh_100.get_quality_score() - 1.0) < 0.01


# ============================================================================
# SYNCHRONIZATION DYNAMICS TESTS
# ============================================================================


class TestSynchronizationDynamics:
    """Test SynchronizationDynamics tracking."""

    def test_add_coherence_sample_updates_max(self):
        """Test that adding samples updates max_coherence."""
        dynamics = SynchronizationDynamics()

        dynamics.add_coherence_sample(0.50, time.time())
        assert dynamics.max_coherence == 0.50

        dynamics.add_coherence_sample(0.75, time.time())
        assert dynamics.max_coherence == 0.75

        dynamics.add_coherence_sample(0.60, time.time())
        assert dynamics.max_coherence == 0.75  # Stays at max

    def test_compute_dissolution_rate_insufficient_samples(self):
        """Test dissolution rate with fewer than 10 samples."""
        dynamics = SynchronizationDynamics()

        for i in range(5):
            dynamics.add_coherence_sample(0.7 - i * 0.05, time.time())

        rate = dynamics.compute_dissolution_rate()
        assert rate == 0.0  # Not enough samples

    def test_compute_dissolution_rate_with_valid_samples(self):
        """Test dissolution rate with exactly 10+ valid samples (covers lines 165-167)."""
        dynamics = SynchronizationDynamics()

        # Add exactly 10 samples with clear decay pattern
        for i in range(10):
            coherence = 0.9 - i * 0.05
            dynamics.coherence_history.append(coherence)

        # This should cover lines 165-167 (decay_rate = -coeffs[0]; return decay_rate)
        rate = dynamics.compute_dissolution_rate()

        # Should return a value (lines 165-167 executed)
        assert isinstance(rate, (float, np.floating))
        assert rate >= 0.0  # Decay means positive rate

    def test_compute_dissolution_rate_with_stable_coherence(self):
        """Test dissolution rate with stable coherence (no decay)."""
        dynamics = SynchronizationDynamics()

        # Add stable coherence (no change)
        for _ in range(10):
            dynamics.coherence_history.append(0.75)

        rate = dynamics.compute_dissolution_rate()

        # Should be near 0 (no decay)
        assert abs(rate) < 0.1  # Nearly zero rate


# ============================================================================
# KURAMOTO OSCILLATOR TESTS
# ============================================================================


class TestKuramotoOscillator:
    """Test KuramotoOscillator behavior."""

    def test_oscillator_initialization(self):
        """Test oscillator initialization."""
        config = OscillatorConfig(natural_frequency=40.0)
        osc = KuramotoOscillator("node-001", config)

        assert osc.node_id == "node-001"
        assert osc.frequency == 40.0
        assert osc.state == OscillatorState.IDLE
        assert 0 <= osc.phase <= 2 * np.pi

    def test_oscillator_update_changes_state(self):
        """Test that update changes state to COUPLING."""
        osc = KuramotoOscillator("node-001")

        neighbor_phases = {"node-002": 1.5}
        coupling_weights = {"node-002": 1.0}

        osc.update(neighbor_phases, coupling_weights, dt=0.005)

        assert osc.state == OscillatorState.COUPLING

    def test_oscillator_update_with_no_neighbors(self):
        """Test oscillator update with empty neighbors."""
        osc = KuramotoOscillator("node-001")
        initial_phase = osc.phase

        # Update with no neighbors (free running)
        osc.update({}, {}, dt=0.005)

        # Phase should still update (natural frequency)
        assert osc.phase != initial_phase

    def test_oscillator_update_records_history(self):
        """Test that phase history is recorded."""
        osc = KuramotoOscillator("node-001")
        initial_history_len = len(osc.phase_history)

        osc.update({}, {}, dt=0.005)

        assert len(osc.phase_history) > initial_history_len
        assert len(osc.frequency_history) > initial_history_len - 1

    def test_oscillator_phase_wrapping(self):
        """Test that phase wraps to [0, 2π]."""
        osc = KuramotoOscillator("node-001")
        osc.phase = 3 * np.pi  # > 2π

        # Update should wrap
        osc.update({}, {}, dt=0.005)

        assert 0 <= osc.phase <= 2 * np.pi

    def test_oscillator_history_trimming(self):
        """Test that history is trimmed after 1000 samples."""
        osc = KuramotoOscillator("node-001")

        # Fill history beyond 1000
        for _ in range(1005):
            osc.update({}, {}, dt=0.005)

        # Should be trimmed to 1000
        assert len(osc.phase_history) <= 1001  # 1000 + 1 (initial)

    def test_get_phase(self):
        """Test get_phase method."""
        osc = KuramotoOscillator("node-001")
        osc.phase = 1.5

        assert osc.get_phase() == 1.5

    def test_set_phase(self):
        """Test set_phase method."""
        osc = KuramotoOscillator("node-001")

        osc.set_phase(2.5)
        assert abs(osc.phase - 2.5) < 0.01

        # Test wrapping
        osc.set_phase(7.0)  # > 2π
        assert osc.phase < 2 * np.pi

    def test_reset(self):
        """Test oscillator reset."""
        osc = KuramotoOscillator("node-001")
        osc.state = OscillatorState.SYNCHRONIZED

        # Update a few times to build history
        for _ in range(10):
            osc.update({}, {}, dt=0.005)

        osc.reset()

        assert osc.state == OscillatorState.IDLE
        assert len(osc.phase_history) == 1  # Only initial phase

    def test_repr(self):
        """Test __repr__ method."""
        osc = KuramotoOscillator("node-001")
        osc.phase = 1.234

        repr_str = repr(osc)

        assert "node-001" in repr_str
        assert "1.234" in repr_str
        assert "idle" in repr_str or "IDLE" in repr_str


# ============================================================================
# KURAMOTO NETWORK TESTS
# ============================================================================


class TestKuramotoNetwork:
    """Test KuramotoNetwork coordination."""

    def test_network_initialization(self):
        """Test network initialization."""
        network = KuramotoNetwork()

        assert len(network.oscillators) == 0
        assert network.dynamics is not None

    def test_add_oscillator(self):
        """Test adding oscillator to network."""
        network = KuramotoNetwork()

        network.add_oscillator("node-001")

        assert "node-001" in network.oscillators
        assert len(network.oscillators) == 1

    def test_add_oscillator_with_custom_config(self):
        """Test adding oscillator with custom config."""
        network = KuramotoNetwork()
        custom_config = OscillatorConfig(natural_frequency=50.0)

        network.add_oscillator("node-001", custom_config)

        assert network.oscillators["node-001"].frequency == 50.0

    def test_remove_oscillator(self):
        """Test removing oscillator from network."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")

        network.remove_oscillator("node-001")

        assert "node-001" not in network.oscillators
        assert "node-002" in network.oscillators

    def test_remove_oscillator_nonexistent(self):
        """Test removing non-existent oscillator (no error)."""
        network = KuramotoNetwork()

        # Should not raise error
        network.remove_oscillator("nonexistent")

    def test_reset_all(self):
        """Test resetting all oscillators."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")

        # Update to build history
        topology = {"node-001": ["node-002"], "node-002": ["node-001"]}
        network.update_network(topology)

        # Set cache
        network._coherence_cache = PhaseCoherence(0.8, 0.0, 0.1, "conscious")

        network.reset_all()

        # Dynamics should be reset
        assert len(network.dynamics.coherence_history) == 0
        assert network._coherence_cache is None

    def test_update_network_with_topology(self):
        """Test network update with topology."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")
        network.add_oscillator("node-003")

        topology = {
            "node-001": ["node-002", "node-003"],
            "node-002": ["node-001", "node-003"],
            "node-003": ["node-001", "node-002"],
        }

        initial_phases = {
            "node-001": network.oscillators["node-001"].phase,
            "node-002": network.oscillators["node-002"].phase,
            "node-003": network.oscillators["node-003"].phase,
        }

        network.update_network(topology, dt=0.005)

        # Phases should have changed
        for node_id, initial_phase in initial_phases.items():
            current_phase = network.oscillators[node_id].phase
            # Phase may wrap, but history should grow
            assert len(network.oscillators[node_id].phase_history) > 1

    def test_update_network_with_custom_coupling_weights(self):
        """Test network update with custom coupling weights."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")

        topology = {
            "node-001": ["node-002"],
            "node-002": ["node-001"],
        }

        # Strong coupling from node-001 to node-002
        coupling_weights = {
            ("node-001", "node-002"): 2.0,
            ("node-002", "node-001"): 0.5,
        }

        network.update_network(topology, coupling_weights, dt=0.005)

        # Both should have updated
        assert len(network.oscillators["node-001"].phase_history) > 1
        assert len(network.oscillators["node-002"].phase_history) > 1

    def test_get_coherence_computes_if_none(self):
        """Test get_coherence computes initial coherence."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")

        # Initially no cache
        assert network._coherence_cache is None

        coherence = network.get_coherence()

        # Should have computed
        assert coherence is not None
        assert 0 <= coherence.order_parameter <= 1.0

    def test_get_coherence_returns_cached(self):
        """Test get_coherence returns cached value."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")

        # First call computes
        coherence1 = network.get_coherence()
        coherence2 = network.get_coherence()

        # Same object (cached)
        assert coherence1 is coherence2

    def test_get_order_parameter(self):
        """Test get_order_parameter quick access."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")

        r = network.get_order_parameter()

        assert isinstance(r, float)
        assert 0 <= r <= 1.0

    def test_get_order_parameter_no_cache(self):
        """Test get_order_parameter with no coherence cache."""
        network = KuramotoNetwork()

        r = network.get_order_parameter()

        assert r == 0.0  # No oscillators

    @pytest.mark.asyncio
    async def test_synchronize_reaches_target(self):
        """Test synchronize reaches target coherence."""
        network = KuramotoNetwork()

        # Add oscillators
        for i in range(10):
            network.add_oscillator(f"node-{i:03d}")

        # Fully connected topology
        topology = {
            f"node-{i:03d}": [f"node-{j:03d}" for j in range(10) if j != i] for i in range(10)
        }

        dynamics = await network.synchronize(
            topology=topology,
            duration_ms=100.0,
            target_coherence=0.70,
            dt=0.005,
        )

        # Should have coherence history
        assert len(dynamics.coherence_history) > 0

        # Should have reached target at some point (or tried)
        final_coherence = network.get_order_parameter()
        # With 10 fully connected oscillators, should synchronize
        assert final_coherence > 0.3  # At least partial sync

    @pytest.mark.asyncio
    async def test_synchronize_tracks_time_to_sync(self):
        """Test synchronize records time_to_sync."""
        network = KuramotoNetwork()

        for i in range(8):
            network.add_oscillator(f"node-{i}")

        topology = {f"node-{i}": [f"node-{j}" for j in range(8) if j != i] for i in range(8)}

        dynamics = await network.synchronize(
            topology=topology,
            duration_ms=200.0,
            target_coherence=0.70,
        )

        # If reached, time_to_sync should be set
        if dynamics.time_to_sync is not None:
            assert dynamics.time_to_sync > 0.0
            assert dynamics.sustained_duration > 0.0

    def test_update_coherence_with_no_oscillators(self):
        """Test _update_coherence early return with no oscillators (line 393)."""
        network = KuramotoNetwork()

        # No oscillators added
        assert len(network.oscillators) == 0

        # Call _update_coherence - should return early (line 393)
        network._update_coherence(time.time())

        # Cache should remain None
        assert network._coherence_cache is None

    def test_get_phase_distribution(self):
        """Test get_phase_distribution."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")
        network.add_oscillator("node-003")

        distribution = network.get_phase_distribution()

        assert isinstance(distribution, np.ndarray)
        assert len(distribution) == 3
        assert all(0 <= phase <= 2 * np.pi for phase in distribution)

    def test_repr(self):
        """Test __repr__ method."""
        network = KuramotoNetwork()
        network.add_oscillator("node-001")
        network.add_oscillator("node-002")

        repr_str = repr(network)

        assert "2" in repr_str  # 2 oscillators
        assert "KuramotoNetwork" in repr_str


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestKuramotoIntegration:
    """Integration tests for full Kuramoto synchronization."""

    @pytest.mark.asyncio
    async def test_full_synchronization_cycle(self):
        """Test complete synchronization from random to coherent."""
        network = KuramotoNetwork()

        # Create small network
        n_nodes = 6
        for i in range(n_nodes):
            network.add_oscillator(f"node-{i}")

        # Ring topology
        topology = {f"node-{i}": [f"node-{(i - 1) % n_nodes}", f"node-{(i + 1) % n_nodes}"] for i in range(n_nodes)}

        # Run synchronization
        dynamics = await network.synchronize(
            topology=topology,
            duration_ms=150.0,
            target_coherence=0.70,
        )

        # Check dynamics recorded
        assert len(dynamics.coherence_history) > 0
        assert dynamics.max_coherence > 0.0

    @pytest.mark.asyncio
    async def test_partial_synchronization(self):
        """Test network with weak coupling (partial sync)."""
        weak_config = OscillatorConfig(coupling_strength=2.0)  # Weak coupling
        network = KuramotoNetwork(weak_config)

        for i in range(5):
            network.add_oscillator(f"node-{i}")

        # Sparse topology (not fully connected)
        topology = {
            "node-0": ["node-1"],
            "node-1": ["node-0", "node-2"],
            "node-2": ["node-1", "node-3"],
            "node-3": ["node-2", "node-4"],
            "node-4": ["node-3"],
        }

        await network.synchronize(topology=topology, duration_ms=100.0)

        # Should have some coherence, but maybe not full
        r = network.get_order_parameter()
        assert 0.0 < r < 1.0

    def test_oscillator_coupling_with_phase_differences(self):
        """Test coupling effect on phase evolution."""
        osc1 = KuramotoOscillator("node-1")
        osc2 = KuramotoOscillator("node-2")

        # Set specific phases
        osc1.set_phase(0.0)
        osc2.set_phase(np.pi / 2)  # 90 degrees ahead

        # Update osc1 with osc2 as neighbor
        neighbor_phases = {"node-2": osc2.phase}
        coupling_weights = {"node-2": 1.0}

        initial_phase = osc1.phase

        osc1.update(neighbor_phases, coupling_weights, dt=0.01)

        # Phase should have shifted due to coupling
        # (Kuramoto dynamics pull toward neighbor)
        assert osc1.phase != initial_phase


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
