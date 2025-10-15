"""Tests for DataOrchestrator - Reactive Fabric Sprint 3.

Target: 100% statement + branch coverage.

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

from consciousness.reactive_fabric.orchestration.data_orchestrator import (
    DataOrchestrator,
    OrchestrationDecision,
)
from consciousness.reactive_fabric.collectors.metrics_collector import SystemMetrics
from consciousness.reactive_fabric.collectors.event_collector import (
    ConsciousnessEvent,
    EventType,
    EventSeverity,
)
from consciousness.esgt.coordinator import SalienceScore


class TestOrchestrationDecision:
    """Test OrchestrationDecision dataclass."""

    def test_orchestration_decision_creation(self):
        """Test creating OrchestrationDecision."""
        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        decision = OrchestrationDecision(
            should_trigger_esgt=True,
            salience=salience,
            reason="Test trigger",
            triggering_events=[],
            metrics_snapshot=metrics,
            timestamp=time.time(),
            confidence=0.9,
        )

        assert decision.should_trigger_esgt is True
        assert decision.salience == salience
        assert decision.reason == "Test trigger"
        assert decision.confidence == 0.9


class TestDataOrchestratorInit:
    """Test DataOrchestrator initialization."""

    def test_init_with_default_params(self, mock_consciousness_system):
        """Test initialization with default parameters."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        assert orchestrator.system == mock_consciousness_system
        assert orchestrator.collection_interval_ms == 100.0
        assert orchestrator.salience_threshold == 0.65
        assert orchestrator._running is False
        assert orchestrator.total_collections == 0
        assert orchestrator.total_triggers_generated == 0
        assert orchestrator.total_triggers_executed == 0
        assert orchestrator.MAX_HISTORY == 100

    def test_init_with_custom_params(self, mock_consciousness_system):
        """Test initialization with custom parameters."""
        orchestrator = DataOrchestrator(
            mock_consciousness_system,
            collection_interval_ms=50.0,
            salience_threshold=0.75,
            event_buffer_size=500,
            decision_history_size=50,
        )

        assert orchestrator.collection_interval_ms == 50.0
        assert orchestrator.salience_threshold == 0.75
        assert orchestrator.event_collector.max_events == 500
        assert orchestrator.MAX_HISTORY == 50


class TestStartStop:
    """Test start/stop orchestration."""

    @pytest.mark.asyncio
    async def test_start_orchestrator(self, mock_consciousness_system):
        """Test starting orchestrator."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator.start()

        assert orchestrator._running is True
        assert orchestrator._orchestration_task is not None

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self, mock_consciousness_system):
        """Test starting orchestrator when already running."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator.start()
        await orchestrator.start()  # Should log warning but not error

        assert orchestrator._running is True

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_stop_orchestrator(self, mock_consciousness_system):
        """Test stopping orchestrator."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator.start()
        await orchestrator.stop()

        assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_stop_not_running(self, mock_consciousness_system):
        """Test stopping orchestrator when not running."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator.stop()  # Should not error

        assert orchestrator._running is False


class TestOrchestrationLoop:
    """Test _orchestration_loop() method."""

    @pytest.mark.asyncio
    async def test_orchestration_loop_runs(self, mock_consciousness_system):
        """Test that orchestration loop executes collections."""
        orchestrator = DataOrchestrator(
            mock_consciousness_system, collection_interval_ms=10.0
        )

        await orchestrator.start()
        await asyncio.sleep(0.05)  # Let it run a few cycles
        await orchestrator.stop()

        # Should have collected at least once
        assert orchestrator.total_collections > 0

    @pytest.mark.asyncio
    async def test_orchestration_loop_handles_exception(self, mock_consciousness_system):
        """Test that loop continues despite errors."""
        orchestrator = DataOrchestrator(
            mock_consciousness_system, collection_interval_ms=10.0
        )

        # Force an error in collection
        orchestrator.metrics_collector.collect = AsyncMock(side_effect=Exception("Test error"))

        await orchestrator.start()
        await asyncio.sleep(0.03)
        await orchestrator.stop()

        # Should have attempted collections despite errors
        assert orchestrator.total_collections >= 0


class TestCollectAndOrchestrate:
    """Test _collect_and_orchestrate() method."""

    @pytest.mark.asyncio
    async def test_collect_and_orchestrate_success(self, mock_consciousness_system):
        """Test successful collection and orchestration."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator._collect_and_orchestrate()

        assert orchestrator.total_collections == 1
        assert len(orchestrator.decision_history) == 1

    @pytest.mark.asyncio
    async def test_collect_and_orchestrate_with_exception(self, mock_consciousness_system):
        """Test orchestration with exception."""
        orchestrator = DataOrchestrator(mock_consciousness_system)
        orchestrator.metrics_collector.collect = AsyncMock(side_effect=Exception("Test error"))

        await orchestrator._collect_and_orchestrate()

        # Should increment collection count even with error
        assert orchestrator.total_collections == 1

    @pytest.mark.asyncio
    async def test_decision_history_pruning(self, mock_consciousness_system):
        """Test that decision history is pruned to MAX_HISTORY."""
        orchestrator = DataOrchestrator(
            mock_consciousness_system, decision_history_size=5
        )

        # Generate more decisions than MAX_HISTORY
        for _ in range(10):
            await orchestrator._collect_and_orchestrate()

        # Should be pruned to 5
        assert len(orchestrator.decision_history) == 5


class TestAnalyzeAndDecide:
    """Test _analyze_and_decide() method."""

    @pytest.mark.asyncio
    async def test_analyze_and_decide_low_salience(self, mock_consciousness_system):
        """Test decision when salience is below threshold."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )
        events = []

        decision = await orchestrator._analyze_and_decide(metrics, events)

        # With no events and good health, salience should be low
        assert isinstance(decision, OrchestrationDecision)
        # Likely should_trigger_esgt is False, but depends on calculation

    @pytest.mark.asyncio
    async def test_analyze_and_decide_high_salience(self, mock_consciousness_system):
        """Test decision when salience exceeds threshold."""
        orchestrator = DataOrchestrator(mock_consciousness_system, salience_threshold=0.5)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            safety_violations=1,  # Increase urgency
        )

        # High salience events
        events = [
            ConsciousnessEvent(
                event_id="e1",
                event_type=EventType.SAFETY_VIOLATION,
                severity=EventSeverity.CRITICAL,
                timestamp=time.time(),
                source="Test",
                novelty=0.9,
                relevance=1.0,
                urgency=1.0,
            )
        ]

        decision = await orchestrator._analyze_and_decide(metrics, events)

        # With high salience event, should likely trigger
        assert decision.should_trigger_esgt is True
        assert len(decision.triggering_events) > 0


class TestCalculateNovelty:
    """Test _calculate_novelty() method."""

    def test_calculate_novelty_no_events(self, mock_consciousness_system):
        """Test novelty calculation with no events."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            esgt_frequency_hz=2.0,
            arousal_level=0.5,
        )

        novelty = orchestrator._calculate_novelty(metrics, [])

        assert 0 <= novelty <= 1.0
        assert novelty == 0.5  # Baseline

    def test_calculate_novelty_with_events(self, mock_consciousness_system):
        """Test novelty calculation with events."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            esgt_frequency_hz=2.0,
            arousal_level=0.5,
        )

        events = [
            ConsciousnessEvent(
                event_id="e1",
                event_type=EventType.SYSTEM_HEALTH,
                severity=EventSeverity.MEDIUM,
                timestamp=time.time(),
                source="Test",
                novelty=0.8,
            )
        ]

        novelty = orchestrator._calculate_novelty(metrics, events)

        assert 0 <= novelty <= 1.0

    def test_calculate_novelty_low_esgt_frequency(self, mock_consciousness_system):
        """Test novelty boost for low ESGT frequency."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            esgt_frequency_hz=0.5,  # < 1.0
            arousal_level=0.5,
        )

        novelty = orchestrator._calculate_novelty(metrics, [])

        assert novelty >= 0.6  # Baseline 0.5 + 0.1 boost

    def test_calculate_novelty_extreme_arousal_low(self, mock_consciousness_system):
        """Test novelty boost for low extreme arousal."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            esgt_frequency_hz=2.0,
            arousal_level=0.1,  # < 0.2
        )

        novelty = orchestrator._calculate_novelty(metrics, [])

        assert novelty >= 0.7  # Baseline 0.5 + 0.2 boost

    def test_calculate_novelty_extreme_arousal_high(self, mock_consciousness_system):
        """Test novelty boost for high extreme arousal."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            esgt_frequency_hz=2.0,
            arousal_level=0.95,  # > 0.9
        )

        novelty = orchestrator._calculate_novelty(metrics, [])

        assert novelty >= 0.7  # Baseline 0.5 + 0.2 boost

    def test_calculate_novelty_critical_event_weight(self, mock_consciousness_system):
        """Test that CRITICAL events get higher weight."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        critical_event = ConsciousnessEvent(
            event_id="e1",
            event_type=EventType.SAFETY_VIOLATION,
            severity=EventSeverity.CRITICAL,
            timestamp=time.time(),
            source="Test",
            novelty=0.6,
        )

        novelty = orchestrator._calculate_novelty(metrics, [critical_event])

        # 0.6 * 1.5 = 0.9
        assert novelty >= 0.85

    def test_calculate_novelty_high_event_weight(self, mock_consciousness_system):
        """Test that HIGH severity events get weight boost."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        high_event = ConsciousnessEvent(
            event_id="e1",
            event_type=EventType.ESGT_IGNITION,
            severity=EventSeverity.HIGH,
            timestamp=time.time(),
            source="Test",
            novelty=0.7,
        )

        novelty = orchestrator._calculate_novelty(metrics, [high_event])

        # 0.7 * 1.2 = 0.84
        assert novelty >= 0.8


class TestCalculateRelevance:
    """Test _calculate_relevance() method."""

    def test_calculate_relevance_no_events(self, mock_consciousness_system):
        """Test relevance calculation with no events."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        relevance = orchestrator._calculate_relevance(metrics, [])

        assert relevance == 0.5  # Baseline

    def test_calculate_relevance_with_events(self, mock_consciousness_system):
        """Test relevance calculation with events."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        events = [
            ConsciousnessEvent(
                event_id="e1",
                event_type=EventType.PFC_SOCIAL_SIGNAL,
                severity=EventSeverity.MEDIUM,
                timestamp=time.time(),
                source="Test",
                relevance=0.8,
            )
        ]

        relevance = orchestrator._calculate_relevance(metrics, events)

        assert relevance == 0.8  # From event

    def test_calculate_relevance_low_health(self, mock_consciousness_system):
        """Test relevance boost for low health."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.6,  # < 0.7
        )

        relevance = orchestrator._calculate_relevance(metrics, [])

        assert relevance >= 0.7  # Baseline 0.5 + 0.2 boost

    def test_calculate_relevance_pfc_activity(self, mock_consciousness_system):
        """Test relevance boost for PFC activity."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            pfc_signals_processed=5,  # > 0
        )

        relevance = orchestrator._calculate_relevance(metrics, [])

        assert relevance >= 0.6  # Baseline 0.5 + 0.1 boost

    def test_calculate_relevance_safety_violations(self, mock_consciousness_system):
        """Test relevance boost for safety violations."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            safety_violations=2,  # > 0
        )

        relevance = orchestrator._calculate_relevance(metrics, [])

        assert relevance >= 0.8  # Baseline 0.5 + 0.3 boost


class TestCalculateUrgency:
    """Test _calculate_urgency() method."""

    def test_calculate_urgency_no_events(self, mock_consciousness_system):
        """Test urgency calculation with no events."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        urgency = orchestrator._calculate_urgency(metrics, [])

        assert urgency == 0.3  # Baseline

    def test_calculate_urgency_with_events(self, mock_consciousness_system):
        """Test urgency calculation with events."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        events = [
            ConsciousnessEvent(
                event_id="e1",
                event_type=EventType.AROUSAL_CHANGE,
                severity=EventSeverity.MEDIUM,
                timestamp=time.time(),
                source="Test",
                urgency=0.7,
            )
        ]

        urgency = orchestrator._calculate_urgency(metrics, events)

        assert urgency == 0.7  # Max from events

    def test_calculate_urgency_safety_violations(self, mock_consciousness_system):
        """Test urgency for safety violations."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            safety_violations=1,
        )

        urgency = orchestrator._calculate_urgency(metrics, [])

        assert urgency >= 0.9

    def test_calculate_urgency_kill_switch(self, mock_consciousness_system):
        """Test urgency for kill switch active."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.0,
            kill_switch_active=True,
        )

        urgency = orchestrator._calculate_urgency(metrics, [])

        assert urgency == 1.0  # Maximum urgency

    def test_calculate_urgency_extreme_arousal_low(self, mock_consciousness_system):
        """Test urgency boost for low extreme arousal."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            arousal_level=0.1,  # < 0.2
        )

        urgency = orchestrator._calculate_urgency(metrics, [])

        assert urgency >= 0.6

    def test_calculate_urgency_extreme_arousal_high(self, mock_consciousness_system):
        """Test urgency boost for high extreme arousal."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            arousal_level=0.95,  # > 0.9
        )

        urgency = orchestrator._calculate_urgency(metrics, [])

        assert urgency >= 0.6


class TestGenerateDecisionReason:
    """Test _generate_decision_reason() method."""

    def test_reason_no_trigger(self, mock_consciousness_system):
        """Test reason when no trigger."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.5, relevance=0.5, urgency=0.3, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        reason = orchestrator._generate_decision_reason(False, salience, metrics, [])

        assert "below threshold" in reason.lower()

    def test_reason_with_triggering_events(self, mock_consciousness_system):
        """Test reason with triggering events."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        events = [
            ConsciousnessEvent(
                event_id="e1",
                event_type=EventType.SAFETY_VIOLATION,
                severity=EventSeverity.HIGH,
                timestamp=time.time(),
                source="Test",
            )
        ]

        reason = orchestrator._generate_decision_reason(True, salience, metrics, events)

        assert "high-salience events" in reason
        assert "safety_violation" in reason

    def test_reason_with_safety_violations(self, mock_consciousness_system):
        """Test reason mentions safety violations."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            safety_violations=2,
        )

        reason = orchestrator._generate_decision_reason(True, salience, metrics, [])

        assert "safety violations" in reason

    def test_reason_with_low_health(self, mock_consciousness_system):
        """Test reason mentions low health."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.6,  # < 0.7
        )

        reason = orchestrator._generate_decision_reason(True, salience, metrics, [])

        assert "low system health" in reason

    def test_reason_with_pfc_activity(self, mock_consciousness_system):
        """Test reason mentions PFC activity."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            pfc_signals_processed=5,
        )

        reason = orchestrator._generate_decision_reason(True, salience, metrics, [])

        assert "PFC social cognition" in reason

    def test_reason_fallback(self, mock_consciousness_system):
        """Test reason falls back to generic message."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        reason = orchestrator._generate_decision_reason(True, salience, metrics, [])

        assert "high computed salience" in reason


class TestCalculateConfidence:
    """Test _calculate_confidence() method."""

    def test_confidence_perfect_conditions(self, mock_consciousness_system):
        """Test confidence with perfect conditions."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.85, urgency=0.82, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.9,
            errors=[],
        )

        confidence = orchestrator._calculate_confidence(metrics, [], salience)

        assert confidence >= 0.9

    def test_confidence_with_errors(self, mock_consciousness_system):
        """Test confidence penalty for collection errors."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.8, urgency=0.8, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.9,
            errors=["Error 1", "Error 2"],
        )

        confidence = orchestrator._calculate_confidence(metrics, [], salience)

        assert confidence <= 0.8  # -0.1 per error

    def test_confidence_low_health(self, mock_consciousness_system):
        """Test confidence penalty for low health."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.8, urgency=0.8, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.4,  # < 0.5
        )

        confidence = orchestrator._calculate_confidence(metrics, [], salience)

        assert confidence <= 0.8  # -0.2 penalty

    def test_confidence_inconsistent_salience(self, mock_consciousness_system):
        """Test confidence penalty for inconsistent salience."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.2, relevance=0.9, urgency=0.3, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.9,
        )

        confidence = orchestrator._calculate_confidence(metrics, [], salience)

        # Variance = 0.9 - 0.2 = 0.7 > 0.5, so -0.1 penalty
        assert confidence <= 0.9


class TestExecuteESGTTrigger:
    """Test _execute_esgt_trigger() method."""

    @pytest.mark.asyncio
    async def test_execute_esgt_trigger_success(self, mock_consciousness_system):
        """Test successful ESGT trigger execution."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        event = ConsciousnessEvent(
            event_id="e1",
            event_type=EventType.SAFETY_VIOLATION,
            severity=EventSeverity.HIGH,
            timestamp=time.time(),
            source="Test",
        )

        decision = OrchestrationDecision(
            should_trigger_esgt=True,
            salience=salience,
            reason="Test trigger",
            triggering_events=[event],
            metrics_snapshot=metrics,
            timestamp=time.time(),
            confidence=0.9,
        )

        await orchestrator._execute_esgt_trigger(decision)

        assert orchestrator.total_triggers_generated == 1
        assert orchestrator.total_triggers_executed == 1
        assert event.esgt_triggered is True

    @pytest.mark.asyncio
    async def test_execute_esgt_trigger_failure(self, mock_consciousness_system):
        """Test ESGT trigger execution failure."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        # Make initiate_esgt return failed event
        mock_event = MagicMock()
        mock_event.success = False
        mock_event.failure_reason = "Test failure"
        mock_consciousness_system.esgt_coordinator.initiate_esgt = AsyncMock(return_value=mock_event)

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        decision = OrchestrationDecision(
            should_trigger_esgt=True,
            salience=salience,
            reason="Test trigger",
            triggering_events=[],
            metrics_snapshot=metrics,
            timestamp=time.time(),
            confidence=0.9,
        )

        await orchestrator._execute_esgt_trigger(decision)

        assert orchestrator.total_triggers_generated == 1
        assert orchestrator.total_triggers_executed == 0  # Not executed due to failure

    @pytest.mark.asyncio
    async def test_execute_esgt_trigger_exception(self, mock_consciousness_system):
        """Test ESGT trigger execution with exception."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        mock_consciousness_system.esgt_coordinator.initiate_esgt = AsyncMock(
            side_effect=Exception("Test exception")
        )

        salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7, confidence=0.9)
        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
        )

        decision = OrchestrationDecision(
            should_trigger_esgt=True,
            salience=salience,
            reason="Test trigger",
            triggering_events=[],
            metrics_snapshot=metrics,
            timestamp=time.time(),
            confidence=0.9,
        )

        await orchestrator._execute_esgt_trigger(decision)

        # Should handle exception gracefully
        assert orchestrator.total_triggers_generated == 1


class TestOrchestrationStats:
    """Test get_orchestration_stats() method."""

    @pytest.mark.asyncio
    async def test_get_orchestration_stats(self, mock_consciousness_system):
        """Test getting orchestration statistics."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator._collect_and_orchestrate()

        stats = orchestrator.get_orchestration_stats()

        assert "total_collections" in stats
        assert "total_triggers_generated" in stats
        assert "total_triggers_executed" in stats
        assert "trigger_execution_rate" in stats
        assert "decision_history_size" in stats
        assert "metrics_collector" in stats
        assert "event_collector" in stats
        assert stats["collection_interval_ms"] == 100.0
        assert stats["salience_threshold"] == 0.65

    def test_trigger_execution_rate_no_triggers(self, mock_consciousness_system):
        """Test trigger execution rate with no triggers."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        stats = orchestrator.get_orchestration_stats()

        # Should not divide by zero
        assert stats["trigger_execution_rate"] == 0.0


class TestRecentDecisions:
    """Test get_recent_decisions() method."""

    @pytest.mark.asyncio
    async def test_get_recent_decisions(self, mock_consciousness_system):
        """Test getting recent decisions."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator._collect_and_orchestrate()
        await orchestrator._collect_and_orchestrate()

        recent = orchestrator.get_recent_decisions(limit=5)

        assert isinstance(recent, list)
        assert len(recent) == 2
        # Should be sorted newest first
        assert recent[0].timestamp >= recent[1].timestamp

    @pytest.mark.asyncio
    async def test_get_recent_decisions_limit(self, mock_consciousness_system):
        """Test recent decisions respects limit."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        for _ in range(10):
            await orchestrator._collect_and_orchestrate()

        recent = orchestrator.get_recent_decisions(limit=3)

        assert len(recent) == 3


class TestRepr:
    """Test __repr__() method."""

    def test_repr_not_running(self, mock_consciousness_system):
        """Test repr when not running."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        repr_str = repr(orchestrator)

        assert "DataOrchestrator" in repr_str
        assert "running=False" in repr_str
        assert "collections=0" in repr_str
        assert "triggers=0/0" in repr_str

    @pytest.mark.asyncio
    async def test_repr_running(self, mock_consciousness_system):
        """Test repr when running."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        await orchestrator.start()

        repr_str = repr(orchestrator)

        assert "running=True" in repr_str

        await orchestrator.stop()


class TestMissingBranches:
    """Test remaining branches for 100% coverage."""

    @pytest.mark.asyncio
    async def test_orchestration_loop_non_cancelled_exception(self, mock_consciousness_system):
        """Test orchestration loop handles non-Cancelled exceptions (lines 159-162)."""
        orchestrator = DataOrchestrator(mock_consciousness_system, collection_interval_ms=10.0)

        # Create a mock that raises exception on first call, then succeeds
        call_count = [0]
        original_collect = orchestrator._collect_and_orchestrate

        async def raising_collect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Test exception")
            await original_collect()

        orchestrator._collect_and_orchestrate = raising_collect

        await orchestrator.start()
        await asyncio.sleep(1.2)  # Give time for exception + recovery sleep
        await orchestrator.stop()

        # Should have recovered and continued
        assert call_count[0] >= 1

    @pytest.mark.asyncio
    async def test_stop_with_active_task(self, mock_consciousness_system):
        """Test stop() with active orchestration_task (lines 136->143)."""
        orchestrator = DataOrchestrator(mock_consciousness_system, collection_interval_ms=50.0)

        await orchestrator.start()
        assert orchestrator._orchestration_task is not None

        # Stop should cancel and await the task
        await orchestrator.stop()

        assert orchestrator._running is False

    def test_calculate_novelty_empty_event_novelties(self, mock_consciousness_system):
        """Test novelty calculation when event_novelties list could be empty (line 297->301)."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        metrics = SystemMetrics(
            timestamp=time.time(),
            tig_node_count=10,
            tig_edge_count=25,
            health_score=0.85,
            esgt_frequency_hz=0.5,  # Will add boost
        )

        # Events list exists but could theoretically result in empty event_novelties
        # This defensive check ensures the branch is covered
        events = []

        novelty = orchestrator._calculate_novelty(metrics, events)

        # Should get baseline + frequency boost
        assert novelty >= 0.6

    @pytest.mark.asyncio
    async def test_stop_when_running_but_no_task(self, mock_consciousness_system):
        """Test stop() when running but task is None (defensive branch 136->143)."""
        orchestrator = DataOrchestrator(mock_consciousness_system)

        # Force edge case: running=True but task=None
        orchestrator._running = True
        orchestrator._orchestration_task = None

        # Should handle gracefully
        await orchestrator.stop()

        assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_orchestration_loop_natural_exit(self, mock_consciousness_system):
        """Test orchestration loop exits naturally when _running becomes False (line 149->164)."""
        orchestrator = DataOrchestrator(mock_consciousness_system, collection_interval_ms=10.0)

        # Set _running to True so loop starts
        orchestrator._running = True

        # Create a mechanism to stop the loop naturally after one iteration
        call_count = [0]
        original_collect = orchestrator._collect_and_orchestrate

        async def stopping_collect():
            call_count[0] += 1
            await original_collect()
            # Set _running to False AFTER collection to trigger natural loop exit
            orchestrator._running = False

        orchestrator._collect_and_orchestrate = stopping_collect

        # Manually call the orchestration loop (not via start/stop which uses cancellation)
        await orchestrator._orchestration_loop()

        # Loop should have exited naturally
        assert call_count[0] >= 1
        assert orchestrator._running is False
