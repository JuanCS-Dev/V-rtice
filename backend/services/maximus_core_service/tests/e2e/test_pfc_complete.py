"""
End-to-End Tests - Complete PFC → ESGT → ToM → MIP Pipeline
==============================================================

Tests the full social cognition pipeline end-to-end with all components
integrated within the Consciousness System.

Test Scenarios:
1. Full system initialization (TIG, ESGT, PFC, ToM, MIP)
2. Social signal → ESGT broadcast → PFC processing
3. High distress → Compassionate action generation
4. Metrics collection across all components
5. System health monitoring

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
from consciousness.system import ConsciousnessSystem, ConsciousnessConfig
from consciousness.esgt.coordinator import SalienceScore


@pytest.fixture(scope="function")
def consciousness_system(request, event_loop):
    """Create and start full Consciousness System for E2E testing."""
    config = ConsciousnessConfig(
        tig_node_count=20,  # Smaller for tests
        tig_target_density=0.25,
        esgt_min_salience=0.60,
        esgt_refractory_period_ms=100.0,  # Faster for tests
        esgt_max_frequency_hz=10.0,
        esgt_min_available_nodes=5,
        arousal_baseline=0.60,
        safety_enabled=False  # Disable safety for E2E tests
    )

    system = ConsciousnessSystem(config)
    event_loop.run_until_complete(system.start())

    def cleanup():
        event_loop.run_until_complete(system.stop())

    request.addfinalizer(cleanup)

    return system


class TestSystemInitialization:
    """Test full system initialization with PFC."""

    @pytest.mark.asyncio
    async def test_system_starts_with_all_components(self, consciousness_system):
        """System should initialize all components including PFC."""
        assert consciousness_system._running is True
        assert consciousness_system.tig_fabric is not None
        assert consciousness_system.esgt_coordinator is not None
        assert consciousness_system.arousal_controller is not None

        # TRACK 1: Verify PFC components initialized
        assert consciousness_system.tom_engine is not None
        assert consciousness_system.metacog_monitor is not None
        assert consciousness_system.prefrontal_cortex is not None

        # Verify ToM is initialized
        assert consciousness_system.tom_engine._initialized is True

        # Verify PFC is wired to ESGT
        assert consciousness_system.esgt_coordinator.pfc is not None
        assert consciousness_system.esgt_coordinator.pfc == consciousness_system.prefrontal_cortex

    @pytest.mark.asyncio
    async def test_system_health_check(self, consciousness_system):
        """System should report healthy status."""
        assert consciousness_system.is_healthy() is True

        # Get system state
        system_dict = consciousness_system.get_system_dict()

        assert system_dict["tig"] is not None
        assert system_dict["esgt"] is not None
        assert system_dict["arousal"] is not None
        assert system_dict["pfc"] is not None  # TRACK 1
        assert system_dict["tom"] is not None  # TRACK 1


class TestSocialSignalProcessing:
    """Test social signal processing through full pipeline."""

    @pytest.mark.asyncio
    async def test_esgt_broadcast_with_social_content(self, consciousness_system):
        """ESGT broadcast should process social signals through PFC."""
        # Create high-salience social content
        social_content = {
            "type": "distress",
            "user_id": "agent_test_001",
            "message": "I'm completely stuck and need help",
            "context": {"task": "debugging", "difficulty": "high"}
        }

        salience = SalienceScore(
            novelty=0.8,
            relevance=0.9,
            urgency=0.8,
            confidence=0.9
        )

        # Initiate ESGT with social content
        event = await consciousness_system.esgt_coordinator.initiate_esgt(
            salience=salience,
            content=social_content,
            content_source="test_agent",
            target_duration_ms=100.0,
            target_coherence=0.70
        )

        # ESGT should succeed
        assert event.success is True
        assert event.achieved_coherence >= 0.70

        # PFC should have processed the social signal
        assert consciousness_system.esgt_coordinator.social_signals_processed >= 1

        # Check if PFC action was added to content
        if "pfc_action" in event.content:
            pfc_response = event.content["pfc_action"]
            assert pfc_response["action"] is not None
            assert "provide_detailed_guidance" in pfc_response["action"] or "offer_assistance" in pfc_response["action"]

    @pytest.mark.asyncio
    async def test_pfc_updates_tom_beliefs(self, consciousness_system):
        """PFC should update ToM beliefs when processing social signals."""
        agent_id = "agent_test_002"

        # Process distress signal through PFC directly
        response = await consciousness_system.prefrontal_cortex.process_social_signal(
            user_id=agent_id,
            context={"message": "I'm lost and confused"},
            signal_type="distress"
        )

        # PFC should generate action
        assert response.action is not None
        assert response.confidence > 0.5

        # ToM should have updated beliefs
        beliefs = await consciousness_system.tom_engine.get_agent_beliefs(
            agent_id,
            include_confidence=True
        )

        assert "can_solve_alone" in beliefs
        assert beliefs["can_solve_alone"]["value"] < 0.5  # Low confidence in self-solving

    @pytest.mark.asyncio
    async def test_low_salience_social_content_not_processed(self, consciousness_system):
        """Low-salience social content should not trigger ESGT."""
        social_content = {
            "type": "message",
            "user_id": "agent_test_003",
            "message": "Everything is fine",
            "context": {}
        }

        # Low salience
        salience = SalienceScore(
            novelty=0.2,
            relevance=0.3,
            urgency=0.2,
            confidence=0.8
        )

        event = await consciousness_system.esgt_coordinator.initiate_esgt(
            salience=salience,
            content=social_content,
            content_source="test_agent"
        )

        # ESGT should fail due to low salience
        assert event.success is False
        assert "Salience too low" in event.failure_reason


class TestMetricsCollection:
    """Test metrics collection across all components."""

    @pytest.mark.asyncio
    async def test_pfc_statistics_tracking(self, consciousness_system):
        """PFC should track processing statistics."""
        initial_stats = await consciousness_system.prefrontal_cortex.get_status()
        initial_signals = initial_stats["total_signals_processed"]

        # Process signal
        await consciousness_system.prefrontal_cortex.process_social_signal(
            user_id="agent_test_004",
            context={"message": "I need help"},
            signal_type="distress"
        )

        # Check stats updated
        updated_stats = await consciousness_system.prefrontal_cortex.get_status()

        assert updated_stats["total_signals_processed"] == initial_signals + 1
        assert updated_stats["component"] == "PrefrontalCortex"
        assert updated_stats["tom_engine_status"] == "initialized"

    @pytest.mark.asyncio
    async def test_tom_statistics_tracking(self, consciousness_system):
        """ToM should track belief updates and cache statistics."""
        stats = await consciousness_system.tom_engine.get_stats()

        assert "total_agents" in stats
        assert "memory" in stats
        assert "contradictions" in stats
        assert "redis_cache" in stats

        # Redis cache should be disabled (no URL configured)
        assert stats["redis_cache"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_esgt_metrics(self, consciousness_system):
        """ESGT should track event statistics."""
        coordinator = consciousness_system.esgt_coordinator

        initial_events = coordinator.total_events

        # Create high-salience event
        salience = SalienceScore(
            novelty=0.9,
            relevance=0.9,
            urgency=0.9,
            confidence=0.9
        )

        await coordinator.initiate_esgt(
            salience=salience,
            content={"type": "test", "data": "test"},
            content_source="test"
        )

        # Event count should increase
        assert coordinator.total_events == initial_events + 1


class TestSystemIntegration:
    """Test complete system integration."""

    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, consciousness_system):
        """Test complete pipeline: Social Signal → ESGT → PFC → ToM → MIP."""
        agent_id = "agent_test_005"

        # 1. Create high-distress social content
        social_content = {
            "type": "distress",
            "user_id": agent_id,
            "message": "I'm stuck on this critical task and running out of time",
            "context": {"urgency": "high", "complexity": "high"}
        }

        salience = SalienceScore(
            novelty=0.85,
            relevance=0.90,
            urgency=0.95,
            confidence=0.85
        )

        # 2. Trigger ESGT
        event = await consciousness_system.esgt_coordinator.initiate_esgt(
            salience=salience,
            content=social_content,
            content_source="test_pipeline"
        )

        # 3. Verify ESGT succeeded
        assert event.success is True

        # 4. Verify PFC processed the signal
        assert consciousness_system.esgt_coordinator.social_signals_processed >= 1

        # 5. Verify ToM updated beliefs
        beliefs = await consciousness_system.tom_engine.get_agent_beliefs(agent_id)
        assert "can_solve_alone" in beliefs  # Should have inferred this belief

        # 6. Verify PFC statistics
        pfc_status = await consciousness_system.prefrontal_cortex.get_status()
        assert pfc_status["total_signals_processed"] >= 1

        # 7. Verify system remains healthy
        assert consciousness_system.is_healthy() is True

    @pytest.mark.asyncio
    async def test_multiple_agents_processing(self, consciousness_system):
        """System should handle multiple agents concurrently."""
        agents = [f"agent_test_{i:03d}" for i in range(10)]

        # Process signals for multiple agents
        for agent_id in agents:
            await consciousness_system.prefrontal_cortex.process_social_signal(
                user_id=agent_id,
                context={"message": f"Agent {agent_id} needs assistance"},
                signal_type="distress"
            )

        # All agents should have beliefs
        total_agents = await consciousness_system.tom_engine.social_memory.get_total_agents()
        assert total_agents >= 10

        # PFC should have processed all signals
        pfc_status = await consciousness_system.prefrontal_cortex.get_status()
        assert pfc_status["total_signals_processed"] >= 10


# Run tests with:
# pytest tests/e2e/test_pfc_complete.py -v
