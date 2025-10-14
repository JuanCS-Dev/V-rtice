"""
Test Suite for ContradictionDetector
=====================================

FASE 2: Contradiction detection between belief updates
Target: False positive rate ≤ 15%, coverage ≥ 95%

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

import pytest
from typing import Dict, Any, List


# ===========================================================================
# CONTRADICTION DETECTION TESTS
# ===========================================================================

@pytest.mark.asyncio
async def test_contradiction_detector_initialization():
    """Test ContradictionDetector initializes correctly."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)

    assert detector.threshold == 0.5
    assert len(detector._history) == 0


@pytest.mark.asyncio
async def test_no_contradiction_similar_values():
    """Test no contradiction detected for similar values."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)
    agent_id = "user_001"
    belief_key = "confusion_history"

    # Record two similar values (0.6 → 0.7)
    await detector.record_update(agent_id, belief_key, old_value=0.6, new_value=0.7)

    # No contradiction (change is small)
    contradictions = detector.get_contradictions(agent_id)
    assert len(contradictions) == 0


@pytest.mark.asyncio
async def test_contradiction_detected_large_flip():
    """Test contradiction detected for large value flip."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)
    agent_id = "user_002"
    belief_key = "engagement"

    # Record large flip (0.2 → 0.9, delta = 0.7 > threshold)
    await detector.record_update(agent_id, belief_key, old_value=0.2, new_value=0.9)

    # Contradiction detected
    contradictions = detector.get_contradictions(agent_id)
    assert len(contradictions) == 1
    assert contradictions[0]["belief_key"] == belief_key
    assert contradictions[0]["delta"] >= 0.5


@pytest.mark.asyncio
async def test_contradiction_symmetric():
    """Test contradiction detection is symmetric (increase or decrease)."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)

    # Test decrease (0.9 → 0.2)
    await detector.record_update("user_A", "belief_1", old_value=0.9, new_value=0.2)

    # Test increase (0.1 → 0.8)
    await detector.record_update("user_B", "belief_2", old_value=0.1, new_value=0.8)

    # Both should be detected
    assert len(detector.get_contradictions("user_A")) == 1
    assert len(detector.get_contradictions("user_B")) == 1


@pytest.mark.asyncio
async def test_contradiction_threshold_boundary():
    """Test contradiction threshold boundary behavior."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)
    agent_id = "user_003"

    # Exactly at threshold (0.0 → 0.5, delta = 0.5)
    await detector.record_update(agent_id, "at_threshold", old_value=0.0, new_value=0.5)

    # Just below threshold (0.0 → 0.49, delta = 0.49)
    await detector.record_update(agent_id, "below_threshold", old_value=0.0, new_value=0.49)

    # Just above threshold (0.0 → 0.51, delta = 0.51)
    await detector.record_update(agent_id, "above_threshold", old_value=0.0, new_value=0.51)

    contradictions = detector.get_contradictions(agent_id)

    # Should detect: at_threshold + above_threshold
    assert len(contradictions) == 2
    detected_keys = {c["belief_key"] for c in contradictions}
    assert "at_threshold" in detected_keys
    assert "above_threshold" in detected_keys
    assert "below_threshold" not in detected_keys


@pytest.mark.asyncio
async def test_multiple_contradictions_per_agent():
    """Test tracking multiple contradictions for same agent."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)
    agent_id = "user_004"

    # Record multiple contradictions
    await detector.record_update(agent_id, "belief_A", old_value=0.1, new_value=0.9)
    await detector.record_update(agent_id, "belief_B", old_value=0.8, new_value=0.1)
    await detector.record_update(agent_id, "belief_C", old_value=0.3, new_value=0.4)  # No contradiction

    contradictions = detector.get_contradictions(agent_id)
    assert len(contradictions) == 2


@pytest.mark.asyncio
async def test_get_contradictions_nonexistent_agent():
    """Test get_contradictions for never-seen agent returns empty list."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector()

    contradictions = detector.get_contradictions("unknown_agent")
    assert contradictions == []


@pytest.mark.asyncio
async def test_contradiction_includes_metadata():
    """Test contradiction record includes all metadata."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)
    agent_id = "user_005"

    await detector.record_update(agent_id, "test_belief", old_value=0.2, new_value=0.9)

    contradictions = detector.get_contradictions(agent_id)
    assert len(contradictions) == 1

    contradiction = contradictions[0]
    assert "belief_key" in contradiction
    assert "old_value" in contradiction
    assert "new_value" in contradiction
    assert "delta" in contradiction
    assert "timestamp" in contradiction

    assert contradiction["belief_key"] == "test_belief"
    assert contradiction["old_value"] == 0.2
    assert contradiction["new_value"] == 0.9
    assert abs(contradiction["delta"] - 0.7) < 0.01


@pytest.mark.asyncio
async def test_clear_contradictions():
    """Test clearing contradictions for specific agent."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)

    # Record contradictions for two agents
    await detector.record_update("user_A", "belief", old_value=0.1, new_value=0.9)
    await detector.record_update("user_B", "belief", old_value=0.1, new_value=0.9)

    # Clear user_A only
    detector.clear_contradictions("user_A")

    assert len(detector.get_contradictions("user_A")) == 0
    assert len(detector.get_contradictions("user_B")) == 1


@pytest.mark.asyncio
async def test_get_contradiction_rate():
    """Test calculating contradiction rate (contradictions / total updates)."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)
    agent_id = "user_006"

    # Record 10 updates: 3 contradictions, 7 normal
    for i in range(3):
        await detector.record_update(agent_id, f"contradiction_{i}", old_value=0.1, new_value=0.9)

    for i in range(7):
        await detector.record_update(agent_id, f"normal_{i}", old_value=0.4, new_value=0.5)

    # Contradiction rate = 3/10 = 0.3
    rate = detector.get_contradiction_rate(agent_id)
    assert abs(rate - 0.3) < 0.01


@pytest.mark.asyncio
async def test_contradiction_rate_no_updates():
    """Test contradiction rate is 0.0 for agent with no updates."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector()

    rate = detector.get_contradiction_rate("unknown_agent")
    assert rate == 0.0


# ===========================================================================
# FALSE POSITIVE VALIDATION
# ===========================================================================

@pytest.mark.asyncio
async def test_false_positive_rate_natural_drift():
    """Test false positive rate for natural belief drift (EMA)."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)
    agent_id = "user_007"

    # Simulate natural EMA drift (α=0.8): 0.5 → 0.58 → 0.624 → ...
    # None of these should trigger contradictions (small incremental changes)
    current = 0.5
    for i in range(10):
        new_value = 0.8 * current + 0.2 * 0.9  # EMA update towards 0.9
        await detector.record_update(agent_id, "natural_drift", old_value=current, new_value=new_value)
        current = new_value

    # No contradictions should be detected (all changes < 0.5)
    contradictions = detector.get_contradictions(agent_id)
    assert len(contradictions) == 0  # False positive rate = 0%


@pytest.mark.asyncio
async def test_false_positive_rate_threshold_tuning():
    """Test different thresholds for false positive rate."""
    from compassion.contradiction_detector import ContradictionDetector

    # Test multiple thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    results = {}

    for threshold in thresholds:
        detector = ContradictionDetector(threshold=threshold)

        # Simulate 100 updates with noise (±0.2 random jitter)
        import random
        random.seed(42)

        current = 0.5
        for i in range(100):
            noise = random.uniform(-0.2, 0.2)
            new_value = max(0.0, min(1.0, current + noise))
            await detector.record_update("test_agent", f"belief_{i}", old_value=current, new_value=new_value)
            current = new_value

        # Calculate false positive rate
        contradictions = len(detector.get_contradictions("test_agent"))
        false_positive_rate = contradictions / 100
        results[threshold] = false_positive_rate

    # With threshold=0.5, false positive rate should be ≤ 15%
    assert results[0.5] <= 0.15


# ===========================================================================
# PERFORMANCE & EDGE CASES
# ===========================================================================

@pytest.mark.asyncio
async def test_high_volume_contradiction_detection():
    """Test detector handles 1000+ updates efficiently."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector()

    # Record 1000 updates
    for i in range(1000):
        agent_id = f"user_{i % 10:03d}"
        await detector.record_update(agent_id, f"belief_{i}", old_value=0.5, new_value=0.6)

    # Verify all recorded (10 agents, ~100 updates each)
    total_updates = sum(len(detector._history.get(f"user_{i:03d}", [])) for i in range(10))
    assert total_updates == 1000


@pytest.mark.asyncio
async def test_repr_method():
    """Test __repr__ returns useful debug info."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.6)

    # Record some data
    await detector.record_update("user_A", "belief", old_value=0.1, new_value=0.9)

    repr_str = repr(detector)
    assert "ContradictionDetector" in repr_str
    assert "0.6" in repr_str
    assert "1" in repr_str  # 1 agent tracked


@pytest.mark.asyncio
async def test_invalid_threshold_raises_error():
    """Test out-of-range threshold raises ValueError."""
    from compassion.contradiction_detector import ContradictionDetector

    # Too high
    with pytest.raises(ValueError, match="threshold must be in"):
        ContradictionDetector(threshold=1.5)

    # Negative
    with pytest.raises(ValueError, match="threshold must be in"):
        ContradictionDetector(threshold=-0.1)


@pytest.mark.asyncio
async def test_get_all_agents():
    """Test get_all_agents returns list of tracked agents."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector()

    # Record updates for multiple agents
    await detector.record_update("user_A", "belief", old_value=0.1, new_value=0.9)
    await detector.record_update("user_B", "belief", old_value=0.2, new_value=0.8)
    await detector.record_update("user_C", "belief", old_value=0.3, new_value=0.7)

    agents = detector.get_all_agents()
    assert len(agents) == 3
    assert set(agents) == {"user_A", "user_B", "user_C"}


@pytest.mark.asyncio
async def test_get_stats_comprehensive():
    """Test get_stats returns global statistics."""
    from compassion.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector(threshold=0.5)

    # Record updates: 3 agents, 10 total updates, 3 contradictions
    await detector.record_update("user_A", "b1", old_value=0.1, new_value=0.9)  # Contradiction
    await detector.record_update("user_A", "b2", old_value=0.4, new_value=0.5)  # Normal
    await detector.record_update("user_B", "b3", old_value=0.2, new_value=0.8)  # Contradiction
    await detector.record_update("user_B", "b4", old_value=0.3, new_value=0.4)  # Normal
    await detector.record_update("user_C", "b5", old_value=0.1, new_value=0.7)  # Contradiction
    await detector.record_update("user_C", "b6", old_value=0.5, new_value=0.6)  # Normal

    stats = detector.get_stats()

    assert stats["total_agents"] == 3
    assert stats["total_updates"] == 6
    assert stats["total_contradictions"] == 3
    assert abs(stats["global_contradiction_rate"] - 0.5) < 0.01
    assert stats["threshold"] == 0.5
