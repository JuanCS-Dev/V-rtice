"""
Tests for MEA integration bridge.
"""

import pytest

from consciousness.esgt.coordinator import ESGTCoordinator, TriggerConditions
from consciousness.integration.mea_bridge import MEABridge
from consciousness.mea import AttentionSchemaModel, AttentionSignal, BoundaryDetector, SelfModel
from consciousness.tig.fabric import TIGFabric, TopologyConfig


@pytest.mark.asyncio
async def test_mea_bridge_builds_context():
    attention_model = AttentionSchemaModel()
    self_model = SelfModel()
    boundary_detector = BoundaryDetector()

    bridge = MEABridge(attention_model, self_model, boundary_detector)

    signals = [
        AttentionSignal("visual", "threat:alpha", 0.8, 0.5, 0.6, 0.5),
        AttentionSignal("proprioceptive", "body_state", 0.4, 0.2, 0.5, 0.1),
    ]

    snapshot = bridge.create_snapshot(signals, proprio_center=(0.0, 0.0, 1.0), orientation=(0.0, 0.1, 0.0))
    context = MEABridge.to_lrr_context(snapshot)

    assert "mea_attention_state" in context
    assert context["mea_attention_state"].focus_target == "threat:alpha"
    assert "mea_summary" in context
    assert context["mea_summary"].focus_target == "threat:alpha"
    assert context["episodic_episode"].focus_target == "threat:alpha"
    assert context["episodic_coherence"] >= 0.0
    assert snapshot.narrative_coherence >= 0.0


@pytest.mark.asyncio
async def test_mea_bridge_to_esgt_payload():
    attention_model = AttentionSchemaModel()
    self_model = SelfModel()
    boundary_detector = BoundaryDetector()
    bridge = MEABridge(attention_model, self_model, boundary_detector)

    signals = [
        AttentionSignal("visual", "threat:beta", 0.9, 0.6, 0.7, 0.6),
        AttentionSignal("proprioceptive", "body_state", 0.5, 0.3, 0.5, 0.1),
    ]
    snapshot = bridge.create_snapshot(signals, proprio_center=(0.0, 0.0, 1.0), orientation=(0.05, 0.0, 0.0))

    tig_config = TopologyConfig(node_count=8, target_density=0.25)
    tig_fabric = TIGFabric(tig_config)
    await tig_fabric.initialize()
    triggers = TriggerConditions(min_salience=0.5, min_available_nodes=4)
    coordinator = ESGTCoordinator(tig_fabric=tig_fabric, triggers=triggers, coordinator_id="bridge-test")

    salience, content = MEABridge.to_esgt_payload(coordinator, snapshot, arousal_level=0.7)

    assert salience.compute_total() >= 0.5
    assert content["focus_target"] == "threat:beta"
    assert "self_narrative" in content
