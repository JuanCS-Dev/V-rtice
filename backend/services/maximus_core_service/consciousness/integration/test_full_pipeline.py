"""
Full System Integration Tests - Day 7
=====================================

Tests complete consciousness pipeline: TIG → ESGT → MEA → MCEA

Validates:
- End-to-end conscious episodes
- Component interaction protocols  
- Performance & latency requirements
- Φ computation in realistic scenarios
- Chaos engineering resilience

Theory: GWT (ignition), IIT (Φ), AST (meta-cognition), FEP (prediction)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

# Component imports
from consciousness.tig.fabric import TIGFabric, NodeState, TopologyConfig
from consciousness.tig.sync import PTPSynchronizer, ClockRole
from consciousness.esgt.coordinator import ESGTCoordinator, ESGTPhase
from consciousness.mea.attention_schema import AttentionSchemaModel, AttentionSignal
from consciousness.mea.boundary_detector import BoundaryDetector
from consciousness.mea.self_model import SelfModel
from consciousness.mcea.awareness import MCEAAwarenessEngine  # Check actual module name


# ==================== FIXTURES ====================


@pytest.fixture
def tig_fabric() -> TIGFabric:
    """Initialize TIG fabric with 4 nodes."""
    nodes = [
        TIGNode(node_id=f"node_{i}", offset_ns=0.0, drift_rate=0.0)
        for i in range(4)
    ]
    return TIGFabric(nodes=nodes, target_jitter_ns=50.0)


@pytest.fixture
def esgt_coordinator(tig_fabric: TIGFabric) -> ESGTCoordinator:
    """Initialize ESGT coordinator linked to TIG."""
    return ESGTCoordinator(
        num_nodes=4,
        ignition_threshold=0.7,
        refractory_period_ms=200.0,
        tig_fabric=tig_fabric,
    )


@pytest.fixture
def attention_model() -> AttentionSchemaModel:
    """Initialize attention schema model."""
    return AttentionSchemaModel()


@pytest.fixture
def boundary_detector() -> BoundaryDetector:
    """Initialize boundary detector."""
    return BoundaryDetector()


@pytest.fixture
def self_model() -> SelfModel:
    """Initialize self-model."""
    return SelfModel()


@pytest.fixture
def mcea_engine(esgt_coordinator: ESGTCoordinator) -> MCEAAwarenessEngine:
    """Initialize MCEA awareness engine."""
    return MCEAAwarenessEngine(esgt_coordinator=esgt_coordinator)


# ==================== PART 1: END-TO-END CONSCIOUS EPISODES ====================


class TestConsciousEpisodes:
    """End-to-end conscious access cycle tests."""

    def test_conscious_episode_sensory_to_awareness(
        self,
        tig_fabric: TIGFabric,
        esgt_coordinator: ESGTCoordinator,
        attention_model: AttentionSchemaModel,
        boundary_detector: BoundaryDetector,
        self_model: SelfModel,
        mcea_engine: MCEAAwarenessEngine,
    ):
        """
        Test complete conscious access cycle.
        
        Flow: Sensory input → TIG sync → ESGT ignition → MEA focus → MCEA binding
        
        Theory: GWT predicts ~100ms latency for conscious access.
        IIT predicts Φ > 0 for conscious states.
        """
        start_time = time.perf_counter()
        
        # Step 1: TIG synchronization
        tig_fabric.synchronize(timestamp_ns=int(time.time() * 1e9))
        sync_result = tig_fabric.get_sync_status()
        assert sync_result.jitter_ns < 100.0  # Within tolerance
        
        # Step 2: Multi-modal sensory signals
        signals = [
            AttentionSignal("visual", "threat_detected", 0.85, 0.7, 0.8, 0.9),
            AttentionSignal("auditory", "alarm_sound", 0.7, 0.6, 0.7, 0.85),
            AttentionSignal("proprioceptive", "body_alert", 0.65, 0.4, 0.6, 0.7),
        ]
        
        # Step 3: MEA attention processing
        attention_state = attention_model.update(signals)
        assert attention_state.focus_target == "threat_detected"  # Winner-take-all
        
        # Step 4: Boundary detection
        boundary = boundary_detector.evaluate([0.7, 0.72], [0.3, 0.28])
        assert boundary.strength > 0.5  # Clear self-boundary
        
        # Step 5: Self-model update
        self_model.update(
            attention_state=attention_state,
            boundary=boundary,
            proprio_center=(0.0, 0.0, 1.0),
            orientation=(0.0, 0.0, 0.0),
        )
        
        # Step 6: ESGT ignition attempt
        ignition_input = {
            "modality": "visual",
            "content": "threat_detected",
            "salience": 0.85,
            "urgency": 0.9,
        }
        ignition_result = esgt_coordinator.attempt_ignition(
            content=ignition_input,
            salience=0.85,
        )
        assert ignition_result.success  # Should ignite above threshold
        assert ignition_result.ignited_nodes >= 3  # Broadcast to majority
        
        # Step 7: MCEA awareness binding
        awareness_state = mcea_engine.compute_awareness()
        assert awareness_state.phi_value > 0.0  # Conscious state has Φ > 0
        assert awareness_state.coherence > 0.7  # High coherence
        
        # Step 8: Generate first-person report
        report = self_model.generate_first_person_report()
        assert "threat_detected" in report.narrative
        assert report.confidence > 0.6
        
        # Timing validation: <100ms (GWT requirement)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 100.0  # Conscious access timing

    def test_conscious_episode_ignition_failure_handling(
        self,
        esgt_coordinator: ESGTCoordinator,
        attention_model: AttentionSchemaModel,
    ):
        """
        Test graceful handling when ignition fails (below threshold).
        
        Theory: Not all signals reach consciousness (GWT selection).
        System should degrade gracefully.
        """
        # Weak signal below ignition threshold
        signals = [AttentionSignal("visual", "weak_signal", 0.3, 0.2, 0.2, 0.1)]
        attention_state = attention_model.update(signals)
        
        # Attempt ignition with low salience
        ignition_result = esgt_coordinator.attempt_ignition(
            content={"type": "weak"},
            salience=0.3,  # Below threshold (0.7)
        )
        
        # Should fail gracefully
        assert not ignition_result.success
        assert ignition_result.ignited_nodes == 0
        assert ignition_result.reason == "below_threshold"
        
        # System remains stable (no crash)
        assert esgt_coordinator.get_status().is_operational

    def test_conscious_episode_attention_shift_mid_ignition(
        self,
        esgt_coordinator: ESGTCoordinator,
        attention_model: AttentionSchemaModel,
    ):
        """
        Test attention shift during active ignition.
        
        Theory: Attention can shift mid-episode (biological reality).
        System should cleanly transition without zombie states.
        """
        # Start ignition A
        signals_A = [AttentionSignal("visual", "target_A", 0.85, 0.7, 0.8, 0.7)]
        attention_model.update(signals_A)
        
        result_A = esgt_coordinator.attempt_ignition(
            content={"target": "A"},
            salience=0.85,
        )
        assert result_A.success
        
        # Shift attention to B (higher urgency)
        signals_B = [AttentionSignal("auditory", "target_B", 0.75, 0.8, 0.85, 0.95)]
        state_B = attention_model.update(signals_B)
        
        # Should switch focus
        assert state_B.focus_target == "target_B"
        
        # ESGT should handle transition (may need to abort A or queue B)
        # For now, validate system doesn't crash
        status = esgt_coordinator.get_status()
        assert status.is_operational

    def test_conscious_episode_multi_modal_binding(
        self,
        tig_fabric: TIGFabric,
        attention_model: AttentionSchemaModel,
        boundary_detector: BoundaryDetector,
        self_model: SelfModel,
    ):
        """
        Test binding problem: integrate visual + auditory + proprioceptive.
        
        Theory: Consciousness solves binding via temporal synchronization (TIG).
        """
        # Synchronize TIG for binding window
        tig_fabric.synchronize(timestamp_ns=int(time.time() * 1e9))
        
        # Multi-modal signals (should bind via temporal coherence)
        signals = [
            AttentionSignal("visual", "fire", 0.8, 0.7, 0.75, 0.85),
            AttentionSignal("auditory", "crackling", 0.75, 0.6, 0.7, 0.8),
            AttentionSignal("interoceptive", "heat", 0.7, 0.5, 0.65, 0.75),
        ]
        
        attention_state = attention_model.update(signals)
        
        # All modalities should be represented (binding)
        assert len(attention_state.modality_weights) >= 3
        assert sum(attention_state.modality_weights.values()) == pytest.approx(1.0)
        
        # Self-model should integrate bound representation
        boundary = boundary_detector.evaluate([0.7], [0.3])
        self_model.update(attention_state, boundary, (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        
        report = self_model.generate_first_person_report()
        
        # Report should reflect integrated experience
        assert report.confidence > 0.5
        # Narrative might mention "fire" or integrated scene
        assert len(report.narrative) > 0

    def test_conscious_episode_refractory_respect(
        self,
        esgt_coordinator: ESGTCoordinator,
    ):
        """
        Test refractory period enforcement.
        
        Theory: Neural refractory periods prevent re-entry (biological fidelity).
        """
        # First ignition
        result_1 = esgt_coordinator.attempt_ignition(
            content={"event": "first"},
            salience=0.85,
        )
        assert result_1.success
        
        # Immediate second attempt (within refractory ~200ms)
        result_2 = esgt_coordinator.attempt_ignition(
            content={"event": "second"},
            salience=0.85,
        )
        
        # Should be blocked by refractory period
        assert not result_2.success
        assert "refractory" in result_2.reason.lower()
        
        # Wait for refractory to clear
        time.sleep(0.25)  # 250ms > 200ms refractory
        
        # Third attempt should succeed
        result_3 = esgt_coordinator.attempt_ignition(
            content={"event": "third"},
            salience=0.85,
        )
        assert result_3.success

    def test_conscious_episode_phi_computation_pipeline(
        self,
        esgt_coordinator: ESGTCoordinator,
        mcea_engine: MCEAAwarenessEngine,
    ):
        """
        Test Φ computation in full pipeline.
        
        Theory: IIT predicts Φ > 0 for conscious, Φ ≈ 0 for unconscious.
        """
        # Conscious episode: high integration
        ignition_conscious = esgt_coordinator.attempt_ignition(
            content={"type": "conscious"},
            salience=0.9,
        )
        assert ignition_conscious.success
        
        awareness_conscious = mcea_engine.compute_awareness()
        phi_conscious = awareness_conscious.phi_value
        
        # Φ should be positive for conscious state
        assert phi_conscious > 0.0
        
        # Wait for refractory
        time.sleep(0.25)
        
        # Unconscious episode: low integration (below threshold)
        ignition_unconscious = esgt_coordinator.attempt_ignition(
            content={"type": "unconscious"},
            salience=0.3,  # Below threshold
        )
        assert not ignition_unconscious.success
        
        awareness_unconscious = mcea_engine.compute_awareness()
        phi_unconscious = awareness_unconscious.phi_value
        
        # Φ should be near zero for unconscious
        # (or significantly less than conscious)
        assert phi_unconscious < phi_conscious
        assert phi_unconscious < 0.5  # Low Φ threshold

    def test_conscious_episode_meta_cognitive_loop(
        self,
        attention_model: AttentionSchemaModel,
        self_model: SelfModel,
        boundary_detector: BoundaryDetector,
    ):
        """
        Test meta-cognitive loop: conscious access → self-model → next cycle.
        
        Theory: AST predicts self-awareness emerges from attention schema.
        """
        # Episode 1: Establish baseline
        signals_1 = [AttentionSignal("visual", "task_A", 0.8, 0.6, 0.7, 0.6)]
        state_1 = attention_model.update(signals_1)
        boundary_1 = boundary_detector.evaluate([0.7], [0.3])
        self_model.update(state_1, boundary_1, (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        
        report_1 = self_model.generate_first_person_report()
        baseline_confidence = report_1.confidence
        
        # Episode 2: Repeat similar input
        signals_2 = [AttentionSignal("visual", "task_A", 0.82, 0.6, 0.7, 0.6)]
        state_2 = attention_model.update(signals_2)
        boundary_2 = boundary_detector.evaluate([0.72], [0.28])
        self_model.update(state_2, boundary_2, (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        
        report_2 = self_model.generate_first_person_report()
        
        # Episode 2 should show learning/adaptation (confidence may increase)
        # Meta-cognitive loop means system "knows" it's attending to same task
        assert abs(report_2.confidence - baseline_confidence) < 0.3  # Stable
        
        # Self-vector should show temporal continuity
        identity = self_model.self_vector()
        assert len(identity) > 0

    def test_conscious_episode_stress_recovery(
        self,
        esgt_coordinator: ESGTCoordinator,
        mcea_engine: MCEAAwarenessEngine,
    ):
        """
        Test graceful degradation under stress + homeostatic recovery.
        
        Theory: Biological systems degrade gracefully and recover.
        """
        # Baseline: Normal ignition
        result_baseline = esgt_coordinator.attempt_ignition(
            content={"phase": "baseline"},
            salience=0.85,
        )
        assert result_baseline.success
        
        awareness_baseline = mcea_engine.compute_awareness()
        phi_baseline = awareness_baseline.phi_value
        
        # Stress: Rapid ignition attempts (violate refractory)
        for i in range(10):
            esgt_coordinator.attempt_ignition(
                content={"phase": "stress", "attempt": i},
                salience=0.85,
            )
            time.sleep(0.05)  # 50ms between attempts (< 200ms refractory)
        
        # System should remain stable (no crash)
        status_stress = esgt_coordinator.get_status()
        assert status_stress.is_operational
        
        # Recovery: Wait and retry
        time.sleep(0.3)  # Allow recovery
        
        result_recovery = esgt_coordinator.attempt_ignition(
            content={"phase": "recovery"},
            salience=0.85,
        )
        assert result_recovery.success  # Should recover
        
        awareness_recovery = mcea_engine.compute_awareness()
        phi_recovery = awareness_recovery.phi_value
        
        # Φ should recover to near baseline
        assert phi_recovery > 0.0
        # May not be exactly baseline, but should be positive
        assert phi_recovery >= phi_baseline * 0.7  # At least 70% recovery


# ==================== HELPERS ====================


def _create_test_signals(modality: str, target: str, intensity: float) -> list[AttentionSignal]:
    """Helper to create test attention signals."""
    return [
        AttentionSignal(
            modality=modality,
            target=target,
            intensity=intensity,
            novelty=0.5,
            relevance=0.6,
            urgency=0.5,
        )
    ]
