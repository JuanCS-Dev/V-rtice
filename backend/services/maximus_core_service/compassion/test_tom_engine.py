"""
Test Suite for ToMEngine (Integration)
=======================================

Tests complete Theory of Mind engine with all integrated components.

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

import pytest


# ===========================================================================
# TOM ENGINE INITIALIZATION & LIFECYCLE
# ===========================================================================

@pytest.mark.asyncio
async def test_tom_engine_initialization():
    """Test ToM Engine initializes all components."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()

    assert engine.social_memory is not None
    assert engine.confidence_tracker is not None
    assert engine.contradiction_detector is not None
    assert engine._initialized is False

    await engine.initialize()
    assert engine._initialized is True

    await engine.close()


@pytest.mark.asyncio
async def test_tom_engine_double_initialize_idempotent():
    """Test double initialization is safe (idempotent)."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()
    await engine.initialize()  # Should not raise

    await engine.close()


@pytest.mark.asyncio
async def test_operations_before_initialize_raise_error():
    """Test operations before initialize raise RuntimeError."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()

    with pytest.raises(RuntimeError, match="not initialized"):
        await engine.infer_belief("user_001", "test", 0.5)


@pytest.mark.asyncio
async def test_tom_engine_close_idempotent():
    """Test close() is idempotent."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()
    await engine.close()
    await engine.close()  # Should not raise


# ===========================================================================
# BELIEF INFERENCE
# ===========================================================================

@pytest.mark.asyncio
async def test_infer_belief_new_agent():
    """Test inferring belief for new agent (no prior)."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        result = await engine.infer_belief("user_001", "confusion_history", 0.7)

        assert result["agent_id"] == "user_001"
        assert result["belief_key"] == "confusion_history"
        assert result["observed_value"] == 0.7
        assert result["contradiction"] is False  # No prior to contradict
        assert result["confidence"] >= 0.99  # Fresh belief
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_infer_belief_updates_with_ema():
    """Test belief updates use EMA smoothing."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        # First observation
        await engine.infer_belief("user_002", "engagement", 0.5)

        # Second observation (should apply EMA: 0.8*0.5 + 0.2*0.9)
        result = await engine.infer_belief("user_002", "engagement", 0.9)

        expected = 0.8 * 0.5 + 0.2 * 0.9  # = 0.58
        assert abs(result["updated_value"] - expected) < 0.01
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_infer_belief_detects_contradiction():
    """Test contradiction detection on large belief flip."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine(contradiction_threshold=0.5)
    await engine.initialize()

    try:
        # Initial belief
        await engine.infer_belief("user_003", "trust", 0.2)

        # Large flip (0.2 → 0.9, delta=0.7 > 0.5)
        result = await engine.infer_belief("user_003", "trust", 0.9)

        assert result["contradiction"] is True
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_infer_belief_tracks_confidence_decay():
    """Test confidence decays over time."""
    from compassion.tom_engine import ToMEngine
    from datetime import datetime, timedelta

    engine = ToMEngine(decay_lambda=0.01)
    await engine.initialize()

    try:
        # Record belief with artificial old timestamp
        agent_id = "user_004"
        belief_key = "knowledge"

        await engine.infer_belief(agent_id, belief_key, 0.8)

        # Manually inject old timestamp (100 hours ago)
        old_timestamp = datetime.utcnow() - timedelta(hours=100)
        engine.confidence_tracker._timestamps[(agent_id, belief_key)] = [
            old_timestamp
        ]

        # Check confidence (should be decayed)
        confidence = engine.confidence_tracker.calculate_confidence(
            agent_id, belief_key
        )

        import math

        expected = math.exp(-0.01 * 100)  # ≈ 0.368
        assert abs(confidence - expected) < 0.01
    finally:
        await engine.close()


# ===========================================================================
# AGENT BELIEFS RETRIEVAL
# ===========================================================================

@pytest.mark.asyncio
async def test_get_agent_beliefs_with_confidence():
    """Test retrieving all beliefs with confidence scores."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        # Record multiple beliefs
        await engine.infer_belief("user_005", "confusion", 0.6)
        await engine.infer_belief("user_005", "engagement", 0.8)

        beliefs = await engine.get_agent_beliefs("user_005", include_confidence=True)

        assert "confusion" in beliefs
        assert "engagement" in beliefs
        assert "value" in beliefs["confusion"]
        assert "confidence" in beliefs["confusion"]
        assert beliefs["confusion"]["confidence"] >= 0.99  # Fresh
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_get_agent_beliefs_without_confidence():
    """Test retrieving beliefs without confidence scores."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        await engine.infer_belief("user_006", "frustration", 0.4)

        beliefs = await engine.get_agent_beliefs("user_006", include_confidence=False)

        assert "frustration" in beliefs
        assert isinstance(beliefs["frustration"], float)
        assert beliefs["frustration"] == 0.4
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_get_agent_beliefs_nonexistent_agent():
    """Test getting beliefs for non-existent agent returns empty dict."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        beliefs = await engine.get_agent_beliefs("unknown_agent")
        assert beliefs == {}
    finally:
        await engine.close()


# ===========================================================================
# ACTION PREDICTION (SALLY-ANNE SCENARIOS)
# ===========================================================================

@pytest.mark.asyncio
async def test_predict_action_classic_sally_anne():
    """Test action prediction for classic Sally-Anne scenario."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        # Sally believes marble is in basket (not updated)
        await engine.infer_belief("sally", "knows_marble_in_box", 0.0)

        # Scenarios: where will Sally look?
        scenarios = {
            "basket": 0.0,  # Sally doesn't know it's in box
            "box": 1.0,  # Sally knows it's in box
        }

        action = await engine.predict_action("sally", "knows_marble_in_box", scenarios)

        assert action == "basket"  # Sally has false belief
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_predict_action_updated_belief():
    """Test action prediction when Sally observes the move."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        # Sally observed the move (belief updated)
        await engine.infer_belief("sally", "knows_marble_in_box", 1.0)

        scenarios = {"basket": 0.0, "box": 1.0}

        action = await engine.predict_action("sally", "knows_marble_in_box", scenarios)

        assert action == "box"  # Sally updated her belief
    finally:
        await engine.close()


# ===========================================================================
# CONTRADICTION TRACKING
# ===========================================================================

@pytest.mark.asyncio
async def test_get_contradictions():
    """Test retrieving contradictions for an agent."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine(contradiction_threshold=0.5)
    await engine.initialize()

    try:
        # Create contradiction
        await engine.infer_belief("user_007", "belief_A", 0.1)
        await engine.infer_belief("user_007", "belief_A", 0.9)

        contradictions = engine.get_contradictions("user_007")

        assert len(contradictions) >= 1
        assert contradictions[0]["belief_key"] == "belief_A"
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_get_contradiction_rate():
    """Test calculating contradiction rate."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine(contradiction_threshold=0.5)
    await engine.initialize()

    try:
        # 3 total updates: 1 contradiction (initial belief doesn't count)
        await engine.infer_belief("user_008", "b1", 0.1)
        await engine.infer_belief("user_008", "b1", 0.9)  # Contradiction (delta=0.8)
        await engine.infer_belief("user_008", "b2", 0.5)  # Normal

        rate = engine.get_contradiction_rate("user_008")

        # Expected: 1 contradiction out of 3 updates = 33.3%
        assert abs(rate - 0.333) < 0.05  # Approximately 33%
    finally:
        await engine.close()


# ===========================================================================
# STATISTICS & MONITORING
# ===========================================================================

@pytest.mark.asyncio
async def test_get_stats():
    """Test comprehensive statistics retrieval."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()
    await engine.initialize()

    try:
        # Create some activity
        await engine.infer_belief("user_009", "test", 0.5)

        stats = await engine.get_stats()

        assert "total_agents" in stats
        assert "memory" in stats
        assert "contradictions" in stats
        assert stats["total_agents"] >= 1
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_repr_method():
    """Test __repr__ returns useful info."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine()

    repr_before = repr(engine)
    assert "ToMEngine" in repr_before
    assert "NOT_INITIALIZED" in repr_before

    await engine.initialize()

    repr_after = repr(engine)
    assert "INITIALIZED" in repr_after

    await engine.close()


# ===========================================================================
# INTEGRATION TEST (FULL SALLY-ANNE WORKFLOW)
# ===========================================================================

@pytest.mark.asyncio
async def test_full_sally_anne_workflow():
    """Integration test: complete Sally-Anne scenario."""
    from compassion.tom_engine import ToMEngine

    engine = ToMEngine(contradiction_threshold=0.6)  # Higher threshold to avoid false positives
    await engine.initialize()

    try:
        # 1. Initial state: Sally puts marble in basket
        await engine.infer_belief("sally", "marble_location", 0.0)  # 0.0 = basket

        # 2. Anne moves marble to box (Sally doesn't observe)
        # Sally's belief should NOT update (she wasn't present)

        # 3. Predict where Sally will look
        scenarios = {
            "basket": 0.0,  # Sally still thinks it's here
            "box": 1.0,  # Reality
        }

        action = await engine.predict_action("sally", "marble_location", scenarios)
        assert action == "basket"

        # 4. Check confidence is high (recent belief)
        beliefs = await engine.get_agent_beliefs("sally", include_confidence=True)
        assert beliefs["marble_location"]["confidence"] >= 0.99

        # 5. With threshold=0.6, initial belief (0.5→0.0) should not be contradiction
        contradictions = engine.get_contradictions("sally")
        assert len(contradictions) == 0

    finally:
        await engine.close()
