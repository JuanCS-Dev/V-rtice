"""
Test Suite for ConfidenceTracker (Temporal Decay)
==================================================

FASE 2: Confidence decay implementation
Target: Temporal decay λ = 0.01/hour, coverage ≥ 95%

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

import pytest
from datetime import datetime, timedelta
import math


# ===========================================================================
# CONFIDENCE DECAY TESTS
# ===========================================================================

@pytest.mark.asyncio
async def test_confidence_tracker_initialization():
    """Test ConfidenceTracker initializes with correct defaults."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(decay_lambda=0.01)

    assert tracker.decay_lambda == 0.01
    assert tracker.min_confidence == 0.1
    assert len(tracker._timestamps) == 0


@pytest.mark.asyncio
async def test_record_belief_stores_timestamp():
    """Test recording a belief stores timestamp correctly."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker()
    agent_id = "user_001"
    belief_key = "confusion_history"

    await tracker.record_belief(agent_id, belief_key, 0.7)

    # Verify timestamp was recorded
    timestamps = tracker.get_timestamps(agent_id, belief_key)
    assert len(timestamps) == 1
    assert isinstance(timestamps[0], datetime)


@pytest.mark.asyncio
async def test_calculate_confidence_no_decay_immediate():
    """Test confidence is 1.0 for freshly recorded belief."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(decay_lambda=0.01)
    agent_id = "user_002"
    belief_key = "engagement"

    await tracker.record_belief(agent_id, belief_key, 0.8)

    # Immediate confidence should be ~1.0
    confidence = tracker.calculate_confidence(agent_id, belief_key)
    assert confidence >= 0.99


@pytest.mark.asyncio
async def test_calculate_confidence_decays_over_time():
    """Test confidence decays exponentially over time."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(decay_lambda=0.01)  # λ = 0.01/hour
    agent_id = "user_003"
    belief_key = "frustration_history"

    # Record belief with artificial old timestamp
    old_timestamp = datetime.utcnow() - timedelta(hours=100)
    tracker._timestamps[(agent_id, belief_key)] = [old_timestamp]

    # Calculate confidence (should decay significantly)
    confidence = tracker.calculate_confidence(agent_id, belief_key)

    # Formula: e^(-λ * hours) = e^(-0.01 * 100) = e^(-1.0) ≈ 0.368
    expected = math.exp(-0.01 * 100)
    assert abs(confidence - expected) < 0.01


@pytest.mark.asyncio
async def test_calculate_confidence_respects_min_threshold():
    """Test confidence never goes below min_confidence threshold."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(decay_lambda=0.01, min_confidence=0.1)
    agent_id = "user_004"
    belief_key = "isolation_history"

    # Record belief with extremely old timestamp (1000 hours ago)
    very_old = datetime.utcnow() - timedelta(hours=1000)
    tracker._timestamps[(agent_id, belief_key)] = [very_old]

    # Confidence should be clamped to min_confidence
    confidence = tracker.calculate_confidence(agent_id, belief_key)
    assert confidence == 0.1


@pytest.mark.asyncio
async def test_calculate_confidence_nonexistent_belief():
    """Test confidence is min_confidence for non-existent belief."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(min_confidence=0.1)

    # Never recorded this belief
    confidence = tracker.calculate_confidence("unknown_user", "unknown_belief")
    assert confidence == 0.1


@pytest.mark.asyncio
async def test_multiple_updates_use_latest_timestamp():
    """Test multiple updates use the latest timestamp for decay."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(decay_lambda=0.01)
    agent_id = "user_005"
    belief_key = "confusion_history"

    # Record belief twice (second update refreshes timestamp)
    await tracker.record_belief(agent_id, belief_key, 0.5)
    await tracker.record_belief(agent_id, belief_key, 0.6)

    # Confidence should still be ~1.0 (latest timestamp is recent)
    confidence = tracker.calculate_confidence(agent_id, belief_key)
    assert confidence >= 0.99


@pytest.mark.asyncio
async def test_get_confidence_scores_all_beliefs():
    """Test get_confidence_scores returns all tracked beliefs."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker()
    agent_id = "user_006"

    # Record multiple beliefs
    await tracker.record_belief(agent_id, "confusion_history", 0.5)
    await tracker.record_belief(agent_id, "engagement", 0.8)
    await tracker.record_belief(agent_id, "frustration_history", 0.3)

    # Get all confidence scores
    scores = tracker.get_confidence_scores(agent_id)

    assert len(scores) == 3
    assert "confusion_history" in scores
    assert "engagement" in scores
    assert "frustration_history" in scores
    assert all(0.0 <= v <= 1.0 for v in scores.values())


@pytest.mark.asyncio
async def test_decay_lambda_zero_no_decay():
    """Test λ=0 means no decay (confidence always 1.0)."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(decay_lambda=0.0)  # No decay
    agent_id = "user_007"
    belief_key = "test"

    # Record with old timestamp
    old = datetime.utcnow() - timedelta(hours=1000)
    tracker._timestamps[(agent_id, belief_key)] = [old]

    # Confidence should still be 1.0 (no decay)
    confidence = tracker.calculate_confidence(agent_id, belief_key)
    assert confidence == 1.0


@pytest.mark.asyncio
async def test_clear_old_beliefs():
    """Test clearing beliefs older than threshold."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker()
    agent_id = "user_008"

    # Record old belief
    old = datetime.utcnow() - timedelta(hours=500)
    tracker._timestamps[(agent_id, "old_belief")] = [old]

    # Record recent belief
    await tracker.record_belief(agent_id, "recent_belief", 0.5)

    # Clear beliefs older than 200 hours
    tracker.clear_old_beliefs(max_age_hours=200)

    # Old belief should be removed
    assert (agent_id, "old_belief") not in tracker._timestamps
    # Recent belief should remain
    assert (agent_id, "recent_belief") in tracker._timestamps


# ===========================================================================
# PERFORMANCE & EDGE CASES
# ===========================================================================

@pytest.mark.asyncio
async def test_high_volume_tracking():
    """Test tracker handles 1000+ beliefs efficiently."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker()

    # Record 1000 beliefs across 10 agents
    for agent_i in range(10):
        for belief_i in range(100):
            agent_id = f"user_{agent_i:03d}"
            belief_key = f"belief_{belief_i:03d}"
            await tracker.record_belief(agent_id, belief_key, 0.5)

    # Verify all recorded
    total_beliefs = sum(len(tracker.get_confidence_scores(f"user_{i:03d}")) for i in range(10))
    assert total_beliefs == 1000


@pytest.mark.asyncio
async def test_repr_method():
    """Test __repr__ returns useful debug info."""
    from compassion.confidence_tracker import ConfidenceTracker

    tracker = ConfidenceTracker(decay_lambda=0.02, min_confidence=0.15)

    repr_str = repr(tracker)
    assert "ConfidenceTracker" in repr_str
    assert "0.02" in repr_str
    assert "0.15" in repr_str


@pytest.mark.asyncio
async def test_invalid_decay_lambda_raises_error():
    """Test negative decay_lambda raises ValueError."""
    from compassion.confidence_tracker import ConfidenceTracker

    with pytest.raises(ValueError, match="decay_lambda must be >= 0"):
        ConfidenceTracker(decay_lambda=-0.01)


@pytest.mark.asyncio
async def test_invalid_min_confidence_raises_error():
    """Test out-of-range min_confidence raises ValueError."""
    from compassion.confidence_tracker import ConfidenceTracker

    # Too high
    with pytest.raises(ValueError, match="min_confidence must be in"):
        ConfidenceTracker(min_confidence=1.5)

    # Negative
    with pytest.raises(ValueError, match="min_confidence must be in"):
        ConfidenceTracker(min_confidence=-0.1)
