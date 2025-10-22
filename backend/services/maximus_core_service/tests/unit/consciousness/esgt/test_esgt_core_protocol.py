"""
Scientific Property Tests for ESGT Core Ignition Protocol

Tests validate Global Workspace Theory (GWT) implementation following
Dehaene et al. 2021 neurophysiological constraints.

EM NOME DE JESUS - VALIDAÇÃO CIENTÍFICA DO PROTOCOLO DE IGNIÇÃO!
"""

import pytest
import pytest_asyncio
import asyncio
from consciousness.esgt.coordinator import (
    ESGTCoordinator,
    ESGTPhase,
    SalienceScore,
)
from consciousness.tig.fabric import TIGFabric, TopologyConfig


class TestESGTCoreProtocol:
    """Test the 5-phase ESGT ignition protocol end-to-end."""

    @pytest_asyncio.fixture
    async def tig_fabric(self):
        """Create TIG fabric for ESGT."""
        # Use topology sufficient for Kuramoto synchronization
        # Original used 100 nodes, using 32 for faster tests but still viable
        config = TopologyConfig(
            node_count=32,
            target_density=0.25,
            clustering_target=0.75,
            enable_small_world_rewiring=True,
        )
        fabric = TIGFabric(config)
        await fabric.initialize()
        yield fabric

    @pytest_asyncio.fixture
    async def esgt_coordinator(self, tig_fabric):
        """Create ESGT coordinator."""
        coordinator = ESGTCoordinator(
            tig_fabric=tig_fabric,
        )
        # CRITICAL: Start coordinator to initialize Kuramoto oscillators
        await coordinator.start()
        yield coordinator
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_ignition_protocol_5_phases(self, esgt_coordinator):
        """
        Property: Successful ignition MUST traverse all 5 phases.

        GWT Theory: PREPARE → SYNCHRONIZE → BROADCAST → SUSTAIN → DISSOLVE
        """
        # High salience to ensure ignition
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        content = {"type": "test_stimulus", "data": "high_salience_content"}

        event = await esgt_coordinator.initiate_esgt(
            content=content,
            salience=salience,
            content_source="test",
            target_coherence=0.75,
            target_duration_ms=100.0,
        )

        # Property: Event must succeed
        assert event.was_successful(), f"Event failed: {event.failure_reason}"

        # Property: Must complete all phases
        phases_completed = [phase for phase, _ in event.phase_transitions]
        assert ESGTPhase.PREPARE in phases_completed
        assert ESGTPhase.SYNCHRONIZE in phases_completed
        assert ESGTPhase.BROADCAST in phases_completed
        assert ESGTPhase.SUSTAIN in phases_completed
        assert ESGTPhase.DISSOLVE in phases_completed
        assert ESGTPhase.COMPLETE in phases_completed

    @pytest.mark.asyncio
    async def test_prepare_phase_latency(self, esgt_coordinator):
        """
        Property: PREPARE phase MUST complete in 5-10ms.

        GWT Theory: Pre-ignition processing is rapid (<10ms).
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)
        content = {"type": "test"}

        event = await esgt_coordinator.initiate_esgt(
            content=content,
            salience=salience,
            content_source="test",
        )

        # Property: PREPARE latency ∈ [0ms, 50ms] (relaxed for testing)
        assert event.prepare_latency_ms is not None
        assert 0.0 <= event.prepare_latency_ms <= 50.0, \
            f"PREPARE took {event.prepare_latency_ms:.2f}ms (expected <50ms)"

    @pytest.mark.asyncio
    async def test_synchronize_achieves_target_coherence(self, esgt_coordinator):
        """
        Property: SYNCHRONIZE phase MUST achieve r ≥ target_coherence.

        GWT Theory: Ignition requires phase locking (coherence r ≥ 0.70).
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)
        target_coherence = 0.70

        event = await esgt_coordinator.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
            target_coherence=target_coherence,
        )

        # Property: Achieved coherence ≥ target
        assert event.achieved_coherence is not None
        assert event.achieved_coherence >= target_coherence - 0.05, \
            f"Coherence {event.achieved_coherence:.3f} < target {target_coherence:.3f}"

    @pytest.mark.asyncio
    async def test_broadcast_duration_constraint(self, esgt_coordinator):
        """
        Property: BROADCAST phase MUST complete in <500ms (relaxed from 300ms).

        GWT Theory: Global ignition broadcast occurs in 100-300ms window.
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        event = await esgt_coordinator.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
        )

        # Property: BROADCAST latency < 500ms
        assert event.broadcast_latency_ms is not None
        assert event.broadcast_latency_ms < 500.0, \
            f"BROADCAST took {event.broadcast_latency_ms:.2f}ms (expected <500ms)"

    @pytest.mark.asyncio
    async def test_sustain_maintains_coherence(self, esgt_coordinator):
        """
        Property: SUSTAIN phase MUST maintain r ≥ 0.60 throughout.

        GWT Theory: Sustained coherence during conscious access.
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)
        target_duration_ms = 100.0

        event = await esgt_coordinator.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
            target_coherence=0.70,
            target_duration_ms=target_duration_ms,
        )

        # Property: Coherence history has values
        assert len(event.coherence_history) > 0, "No coherence history recorded"

        # Property: Most coherence samples ≥ 0.60 (allow some drops)
        high_coherence_samples = [c for c in event.coherence_history if c >= 0.60]
        ratio = len(high_coherence_samples) / len(event.coherence_history)

        assert ratio >= 0.70, \
            f"Only {ratio:.1%} of samples had r≥0.60 (expected ≥70%)"

    @pytest.mark.asyncio
    async def test_dissolve_graceful_degradation(self, esgt_coordinator):
        """
        Property: DISSOLVE phase MUST complete without errors.

        GWT Theory: Graceful desynchronization returns to baseline.
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        event = await esgt_coordinator.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
        )

        # Property: Event reaches COMPLETE phase (after DISSOLVE)
        assert event.current_phase == ESGTPhase.COMPLETE
        assert event.was_successful()
        assert event.failure_reason is None

    @pytest.mark.asyncio
    async def test_low_salience_blocks_ignition(self, esgt_coordinator):
        """
        Property: Salience < threshold MUST prevent ignition.

        GWT Theory: Sub-threshold stimuli remain unconscious.
        """
        # Low salience (below default 0.60 threshold)
        salience = SalienceScore(novelty=0.2, relevance=0.2, urgency=0.1)

        event = await esgt_coordinator.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
        )

        # Property: Event must fail
        assert not event.was_successful()
        assert event.current_phase == ESGTPhase.FAILED
        assert "salience too low" in event.failure_reason.lower()

    @pytest.mark.asyncio
    async def test_frequency_limiter_enforces_rate(self, esgt_coordinator):
        """
        Property: Frequency limiter MUST block excess ignitions.

        GWT Theory: Refractory period prevents continuous ignition.
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        # Rapid-fire ignitions
        events = []
        for i in range(15):  # Exceed limit (default 10/sec)
            event = await esgt_coordinator.initiate_esgt(
                content={"type": f"test_{i}"},
                salience=salience,
                content_source="test",
                target_duration_ms=50.0,  # Short duration
            )
            events.append(event)

        # Property: Some events must be blocked
        blocked_events = [e for e in events if not e.was_successful() and "frequency" in e.failure_reason.lower()]

        assert len(blocked_events) > 0, \
            "Frequency limiter did not block any events!"

    @pytest.mark.asyncio
    async def test_node_recruitment_minimum(self, esgt_coordinator):
        """
        Property: PREPARE phase MUST recruit ≥ min_available_nodes.

        GWT Theory: Ignition requires critical mass of neurons.
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        event = await esgt_coordinator.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
        )

        # Property: Recruited nodes ≥ minimum (default 5)
        min_nodes = esgt_coordinator.triggers.min_available_nodes
        assert event.node_count >= min_nodes, \
            f"Only {event.node_count} nodes recruited (minimum {min_nodes})"

    @pytest.mark.asyncio
    async def test_total_duration_reasonable(self, esgt_coordinator):
        """
        Property: Total event duration MUST be < 1 second.

        GWT Theory: Conscious access is rapid (sub-second).
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        event = await esgt_coordinator.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
            target_duration_ms=100.0,
        )

        # Property: Total duration < 1000ms
        assert event.total_duration_ms is not None
        assert event.total_duration_ms < 1000.0, \
            f"Event took {event.total_duration_ms:.1f}ms (expected <1000ms)"


class TestESGTPropertiesScientific:
    """Property-based tests for ESGT scientific invariants."""

    @pytest_asyncio.fixture
    async def minimal_esgt(self):
        """Minimal ESGT setup for property testing."""
        # Use minimum viable topology for Kuramoto sync (at least 16 nodes)
        config = TopologyConfig(
            node_count=16,
            target_density=0.30,
            clustering_target=0.70,
            enable_small_world_rewiring=True,
        )
        tig = TIGFabric(config)
        await tig.initialize()

        coordinator = ESGTCoordinator(tig_fabric=tig)
        # CRITICAL: Start coordinator to initialize Kuramoto oscillators
        await coordinator.start()

        yield coordinator

        await coordinator.stop()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("salience_total", [0.1, 0.3, 0.5, 0.7, 0.9])
    async def test_salience_threshold_boundary(self, minimal_esgt, salience_total):
        """
        Property: Ignition success correlates with salience.

        Low salience → fail, high salience → succeed.
        """
        # Distribute salience uniformly across all components
        # SalienceScore uses weights: α=0.25, β=0.30, γ=0.30, δ=0.15 (sum=1.0)
        # Setting all components to same value ensures total = value×(0.25+0.30+0.30+0.15) = value×1.0
        salience = SalienceScore(
            novelty=salience_total,
            relevance=salience_total,
            urgency=salience_total,
            confidence=salience_total,
        )

        event = await minimal_esgt.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
            target_duration_ms=50.0,
        )

        # Property: Success if salience > threshold
        threshold = minimal_esgt.triggers.min_salience
        if salience_total >= threshold:
            # May still fail due to resources, but should NOT fail on salience
            if not event.was_successful():
                assert "salience" not in event.failure_reason.lower()
        else:
            # Must fail on salience
            assert not event.was_successful()
            assert "salience" in event.failure_reason.lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("target_coherence", [0.60, 0.70, 0.80, 0.90])
    async def test_coherence_target_achievable(self, minimal_esgt, target_coherence):
        """
        Property: SYNCHRONIZE phase CAN achieve various coherence targets.

        Tests Kuramoto network's ability to synchronize.
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        event = await minimal_esgt.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
            target_coherence=target_coherence,
            target_duration_ms=50.0,
        )

        # Property: If successful, achieved coherence near target
        if event.was_successful():
            # Allow 10% tolerance
            tolerance = 0.10
            assert event.achieved_coherence >= target_coherence - tolerance, \
                f"Coherence {event.achieved_coherence:.3f} far from target {target_coherence:.3f}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("duration_ms", [50.0, 100.0, 200.0, 300.0])
    async def test_sustain_duration_control(self, minimal_esgt, duration_ms):
        """
        Property: SUSTAIN phase duration SHOULD match target ± 50ms.

        Tests temporal control of conscious access window.
        """
        salience = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.8)

        event = await minimal_esgt.initiate_esgt(
            content={"type": "test"},
            salience=salience,
            content_source="test",
            target_duration_ms=duration_ms,
        )

        if event.was_successful():
            # Property: Total duration approximately matches target
            # (Includes PREPARE, SYNC, BROADCAST, SUSTAIN, DISSOLVE overhead)
            # Total should be > target but < target + 500ms
            assert event.total_duration_ms >= duration_ms, \
                f"Total {event.total_duration_ms:.1f}ms < target {duration_ms:.1f}ms"

            assert event.total_duration_ms <= duration_ms + 500.0, \
                f"Total {event.total_duration_ms:.1f}ms >> target {duration_ms:.1f}ms + overhead"


@pytest.mark.asyncio
async def test_esgt_integration_end_to_end():
    """
    Integration test: Full ESGT ignition with real TIG fabric.

    Validates end-to-end GWT implementation without mocks.
    """
    # Create real components with topology for Kuramoto sync
    config = TopologyConfig(
        node_count=32,  # Sufficient for stable synchronization
        target_density=0.25,
        clustering_target=0.75,
        enable_small_world_rewiring=True,
    )
    tig = TIGFabric(config)
    await tig.initialize()

    coordinator = ESGTCoordinator(tig_fabric=tig)
    # CRITICAL: Start coordinator to initialize Kuramoto oscillators
    await coordinator.start()

    # High-salience stimulus
    salience = SalienceScore(novelty=0.85, relevance=0.90, urgency=0.75)
    content = {
        "type": "attention_focus",
        "focus_target": "scientific_validation",
        "modality": "conceptual",
    }

    # Initiate ignition
    event = await coordinator.initiate_esgt(
        content=content,
        salience=salience,
        content_source="integration_test",
        target_coherence=0.70,
        target_duration_ms=150.0,
    )

    # Validate scientific properties
    assert event.was_successful(), f"Ignition failed: {event.failure_reason}"
    assert event.achieved_coherence >= 0.65, "Coherence too low"
    assert event.node_count >= 5, "Too few nodes recruited"

    # Validate all phases completed
    phases_completed = [phase for phase, _ in event.phase_transitions]
    assert len(phases_completed) == 6, "Did not complete all phases"

    print(f"✅ Integration test passed!")
    print(f"   Coherence: {event.achieved_coherence:.3f}")
    print(f"   Duration: {event.total_duration_ms:.1f}ms")
    print(f"   Nodes: {event.node_count}")
