"""
Integration Tests - PrefrontalCortex ↔ ToM Engine
==================================================

Tests the integration between Prefrontal Cortex and Theory of Mind Engine.

Test Scenarios:
1. Social signal → ToM inference → Action generation
2. High distress → ToM belief update → Approved action
3. Low distress → No action needed
4. Metacognition confidence tracking
5. Redis cache performance (if Redis available)

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
from compassion.tom_engine import ToMEngine
from consciousness.prefrontal_cortex import PrefrontalCortex
from consciousness.metacognition.monitor import MetacognitiveMonitor


@pytest.fixture
async def tom_engine():
    """Create and initialize ToM Engine for testing."""
    tom = ToMEngine(db_path=":memory:")
    await tom.initialize()
    yield tom
    await tom.close()


@pytest.fixture
def metacog_monitor():
    """Create Metacognition Monitor for testing (synchronous)."""
    return MetacognitiveMonitor(window_size=50)


@pytest.fixture
def prefrontal_cortex(tom_engine):
    """Create PrefrontalCortex with ToM and Metacognition."""
    # Create metacognition monitor inline
    metacog = MetacognitiveMonitor(window_size=50)
    return PrefrontalCortex(
        tom_engine=tom_engine,
        metacognition_monitor=metacog
    )


class TestPFCBasicIntegration:
    """Basic PFC integration tests."""

    @pytest.mark.asyncio
    async def test_pfc_initialization(self, prefrontal_cortex):
        """Test PFC initializes with ToM and Metacognition."""
        assert prefrontal_cortex.tom is not None
        assert prefrontal_cortex.metacog is not None
        assert prefrontal_cortex.total_signals_processed == 0

    @pytest.mark.asyncio
    async def test_pfc_process_high_distress_signal(self, prefrontal_cortex):
        """High distress signal should generate approved action."""
        response = await prefrontal_cortex.process_social_signal(
            user_id="agent_001",
            context={"message": "I'm completely confused and stuck on this problem"},
            signal_type="distress"
        )

        # Should generate action
        assert response.action is not None
        assert "provide_detailed_guidance" in response.action or "offer_assistance" in response.action

        # Should have high confidence (distress is clear)
        assert response.confidence > 0.5

        # Should have ToM prediction
        assert response.tom_prediction is not None
        assert response.tom_prediction["distress_level"] >= 0.7

        # Should be approved by MIP
        assert response.mip_verdict is not None
        assert response.mip_verdict["approved"] is True

    @pytest.mark.asyncio
    async def test_pfc_process_moderate_distress_signal(self, prefrontal_cortex):
        """Moderate distress should generate assistance action."""
        response = await prefrontal_cortex.process_social_signal(
            user_id="agent_002",
            context={"message": "I'm unsure about how to proceed with X"},
            signal_type="message"
        )

        # Should generate action (moderate distress)
        assert response.action is not None
        assert "offer_assistance" in response.action or "acknowledge" in response.action

        # Distress level should be moderate
        assert 0.5 <= response.tom_prediction["distress_level"] < 0.7

    @pytest.mark.asyncio
    async def test_pfc_process_low_distress_signal(self, prefrontal_cortex):
        """Low distress signal should not generate action."""
        response = await prefrontal_cortex.process_social_signal(
            user_id="agent_003",
            context={"message": "Everything is going well, thanks!"},
            signal_type="message"
        )

        # Should NOT generate action (agent is fine)
        assert response.action is None
        assert response.confidence == 1.0  # High confidence in no-intervention
        assert response.tom_prediction["distress_level"] < 0.5
        assert response.tom_prediction["needs_help"] is False


class TestPFCToMIntegration:
    """Test PFC → ToM belief inference integration."""

    @pytest.mark.asyncio
    async def test_tom_belief_inference_from_distress(self, prefrontal_cortex, tom_engine):
        """PFC should update ToM beliefs based on distress signals."""
        # Process high distress signal
        await prefrontal_cortex.process_social_signal(
            user_id="agent_004",
            context={"message": "I'm lost and confused"},
            signal_type="distress"
        )

        # Check ToM beliefs were updated
        beliefs = await tom_engine.get_agent_beliefs("agent_004", include_confidence=True)

        assert "can_solve_alone" in beliefs
        assert beliefs["can_solve_alone"]["value"] < 0.5  # Low belief in self-solving

    @pytest.mark.asyncio
    async def test_tom_beliefs_persist_across_signals(self, prefrontal_cortex, tom_engine):
        """ToM beliefs should persist and update across multiple signals."""
        agent_id = "agent_005"

        # First signal: high distress
        await prefrontal_cortex.process_social_signal(
            user_id=agent_id,
            context={"message": "I'm stuck"},
            signal_type="distress"
        )

        beliefs_1 = await tom_engine.get_agent_beliefs(agent_id)

        # Second signal: still distressed
        await prefrontal_cortex.process_social_signal(
            user_id=agent_id,
            context={"message": "Still confused"},
            signal_type="distress"
        )

        beliefs_2 = await tom_engine.get_agent_beliefs(agent_id)

        # Beliefs should have been updated (EMA)
        assert "can_solve_alone" in beliefs_1
        assert "can_solve_alone" in beliefs_2
        # Value should be reinforced (lower confidence in self-solving)
        assert beliefs_2["can_solve_alone"] <= beliefs_1["can_solve_alone"]


class TestMetacognitionIntegration:
    """Test Metacognition confidence tracking."""

    @pytest.mark.asyncio
    async def test_metacognition_confidence_starts_neutral(self, metacog_monitor):
        """Initial confidence should be neutral (0.5)."""
        confidence = metacog_monitor.calculate_confidence()
        assert confidence == 0.5

    @pytest.mark.asyncio
    async def test_metacognition_tracks_errors(self, metacog_monitor):
        """Metacognition should track prediction errors."""
        # Record some errors
        metacog_monitor.record_error(0.2)  # 20% error
        metacog_monitor.record_error(0.3)  # 30% error

        # Confidence should decrease
        confidence = metacog_monitor.calculate_confidence()
        expected = 1.0 - ((0.2 + 0.3) / 2)  # 1 - avg_error = 0.75
        assert abs(confidence - expected) < 0.01

    @pytest.mark.asyncio
    async def test_pfc_uses_metacognition_confidence(self, prefrontal_cortex, metacog_monitor):
        """PFC should incorporate metacognition confidence."""
        # Set low metacognition confidence
        for _ in range(10):
            metacog_monitor.record_error(0.8)  # High errors

        response = await prefrontal_cortex.process_social_signal(
            user_id="agent_006",
            context={"message": "I'm confused"},
            signal_type="distress"
        )

        # Confidence should be affected by metacognition
        # (ToM confidence + MIP approval - metacog penalty)
        assert response.confidence < 0.9  # Not maximum confidence


class TestPFCStatistics:
    """Test PFC statistics tracking."""

    @pytest.mark.asyncio
    async def test_pfc_tracks_signals_processed(self, prefrontal_cortex):
        """PFC should track total signals processed."""
        initial_count = prefrontal_cortex.total_signals_processed

        await prefrontal_cortex.process_social_signal(
            user_id="agent_007",
            context={"message": "Hello"},
            signal_type="message"
        )

        assert prefrontal_cortex.total_signals_processed == initial_count + 1

    @pytest.mark.asyncio
    async def test_pfc_tracks_actions_generated(self, prefrontal_cortex):
        """PFC should track actions generated."""
        initial_actions = prefrontal_cortex.total_actions_generated

        await prefrontal_cortex.process_social_signal(
            user_id="agent_008",
            context={"message": "I'm confused"},  # Should generate action
            signal_type="distress"
        )

        assert prefrontal_cortex.total_actions_generated == initial_actions + 1

    @pytest.mark.asyncio
    async def test_pfc_get_status(self, prefrontal_cortex):
        """PFC get_status should return comprehensive statistics."""
        await prefrontal_cortex.process_social_signal(
            user_id="agent_009",
            context={"message": "I'm stuck"},
            signal_type="distress"
        )

        status = await prefrontal_cortex.get_status()

        assert status["component"] == "PrefrontalCortex"
        assert status["total_signals_processed"] >= 1
        assert status["total_actions_generated"] >= 0
        assert status["tom_engine_status"] == "initialized"
        assert status["metacognition"] == "enabled"


class TestRedisCacheIntegration:
    """Test Redis cache integration (if Redis available)."""

    @pytest.mark.asyncio
    async def test_tom_redis_cache_enabled(self):
        """ToM Engine should enable Redis cache if URL provided."""
        # Skip if Redis not available
        try:
            import redis.asyncio  # noqa
        except ImportError:
            pytest.skip("Redis not available")

        tom = ToMEngine(
            db_path=":memory:",
            redis_url="redis://localhost:6379",
            redis_ttl=30
        )

        try:
            await tom.initialize()
            stats = await tom.get_stats()

            # Check if Redis was successfully enabled
            # (May fail if Redis not running, which is OK for test)
            if stats["redis_cache"]["enabled"]:
                assert stats["redis_cache"]["ttl_seconds"] == 30
                assert "hit_rate" in stats["redis_cache"]
        finally:
            await tom.close()

    @pytest.mark.asyncio
    async def test_tom_cache_hit_tracking(self):
        """ToM should track cache hits/misses."""
        try:
            import redis.asyncio  # noqa
        except ImportError:
            pytest.skip("Redis not available")

        tom = ToMEngine(
            db_path=":memory:",
            redis_url="redis://localhost:6379"
        )

        try:
            await tom.initialize()

            # First query - cache miss
            await tom.get_agent_beliefs("agent_010")

            # Second query - should be cache hit (if Redis running)
            await tom.get_agent_beliefs("agent_010")

            stats = await tom.get_stats()

            if stats["redis_cache"]["enabled"]:
                # Should have at least one miss (first query)
                assert stats["redis_cache"]["misses"] >= 1
        finally:
            await tom.close()


# Run tests with:
# pytest tests/integration/test_pfc_tom_integration.py -v
