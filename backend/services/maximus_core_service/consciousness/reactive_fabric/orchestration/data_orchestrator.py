"""Data Orchestrator - ESGT Trigger Generation

Orchestrates data from MetricsCollector and EventCollector to generate
intelligent ESGT ignition triggers with proper salience scoring.

Architecture:
    MetricsCollector + EventCollector → DataOrchestrator → ESGT

The orchestrator:
1. Collects metrics and events
2. Analyzes salience (novelty, relevance, urgency)
3. Generates ESGT triggers when threshold met
4. Tracks orchestration performance

This is the **Reactive Fabric** - the system that makes consciousness
reactive to multi-modal system state.

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Sprint: Reactive Fabric Sprint 3
Governance: Constituição Vértice v2.5 - Article IV (Autonomous Operation)
"""

import time
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging

from consciousness.reactive_fabric.collectors.metrics_collector import (
    MetricsCollector,
    SystemMetrics,
)
from consciousness.reactive_fabric.collectors.event_collector import (
    EventCollector,
    ConsciousnessEvent,
    EventSeverity,
)
from consciousness.esgt.coordinator import SalienceScore

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationDecision:
    """Decision made by orchestrator."""

    should_trigger_esgt: bool
    salience: SalienceScore
    reason: str
    triggering_events: List[ConsciousnessEvent]
    metrics_snapshot: SystemMetrics
    timestamp: float
    confidence: float  # 0-1


class DataOrchestrator:
    """
    Orchestrates metrics and events to generate ESGT triggers.

    The orchestrator continuously monitors system state and generates
    consciousness ignition events when salience thresholds are met.

    Usage:
        orchestrator = DataOrchestrator(consciousness_system)
        await orchestrator.start()

        # Orchestrator runs in background
        # ESGT triggers generated automatically

        await orchestrator.stop()
    """

    def __init__(
        self,
        consciousness_system: Any,
        collection_interval_ms: float = 100.0,
        salience_threshold: float = 0.65,
        event_buffer_size: int = 1000,
        decision_history_size: int = 100,
    ):
        """Initialize data orchestrator.

        Args:
            consciousness_system: ConsciousnessSystem instance
            collection_interval_ms: How often to collect data (default 100ms)
            salience_threshold: Minimum salience to trigger ESGT (default 0.65)
            event_buffer_size: Maximum events in ring buffer (default 1000)
            decision_history_size: Maximum decisions to retain (default 100)
        """
        self.system = consciousness_system
        self.collection_interval_ms = collection_interval_ms
        self.salience_threshold = salience_threshold

        # Collectors
        self.metrics_collector = MetricsCollector(consciousness_system)
        self.event_collector = EventCollector(consciousness_system, max_events=event_buffer_size)

        # Orchestration state
        self._running = False
        self._orchestration_task: Optional[asyncio.Task] = None

        # Statistics
        self.total_collections = 0
        self.total_triggers_generated = 0
        self.total_triggers_executed = 0

        # Decision history (configurable size)
        self.decision_history: List[OrchestrationDecision] = []
        self.MAX_HISTORY = decision_history_size

        logger.info(
            f"DataOrchestrator initialized: "
            f"interval={collection_interval_ms}ms, "
            f"threshold={salience_threshold}"
        )

    async def start(self) -> None:
        """Start orchestrator background loop."""
        if self._running:
            logger.warning("Orchestrator already running")
            return

        self._running = True
        self._orchestration_task = asyncio.create_task(self._orchestration_loop())
        logger.info("🎼 DataOrchestrator started - reactive fabric active")

    async def stop(self) -> None:
        """Stop orchestrator background loop."""
        if not self._running:
            return

        self._running = False

        if self._orchestration_task:
            self._orchestration_task.cancel()
            try:
                await self._orchestration_task
            except asyncio.CancelledError:
                pass

        logger.info("DataOrchestrator stopped")

    async def _orchestration_loop(self) -> None:
        """Main orchestration loop - runs continuously."""
        logger.info("Orchestration loop started")

        while self._running:
            try:
                # Collect data
                await self._collect_and_orchestrate()

                # Sleep until next collection
                await asyncio.sleep(self.collection_interval_ms / 1000.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                # Continue running despite errors
                await asyncio.sleep(1.0)

        logger.info("Orchestration loop stopped")

    async def _collect_and_orchestrate(self) -> None:
        """Collect data and generate ESGT triggers if needed."""
        self.total_collections += 1

        try:
            # 1. Collect metrics
            metrics = await self.metrics_collector.collect()

            # 2. Collect events
            events = await self.event_collector.collect_events()

            # 3. Analyze and decide
            decision = await self._analyze_and_decide(metrics, events)

            # 4. Record decision
            self.decision_history.append(decision)
            if len(self.decision_history) > self.MAX_HISTORY:
                self.decision_history.pop(0)

            # 5. Execute trigger if decision made
            if decision.should_trigger_esgt:
                await self._execute_esgt_trigger(decision)

        except Exception as e:
            logger.error(f"Error in collect_and_orchestrate: {e}")

    async def _analyze_and_decide(
        self, metrics: SystemMetrics, events: List[ConsciousnessEvent]
    ) -> OrchestrationDecision:
        """Analyze metrics and events to decide if ESGT should be triggered.

        Salience calculation:
        - Novelty: Based on event novelty and metric changes
        - Relevance: Based on event relevance and system health
        - Urgency: Based on event urgency and safety violations

        Args:
            metrics: Current system metrics
            events: Recent consciousness events

        Returns:
            OrchestrationDecision with trigger recommendation
        """
        now = time.time()

        # Calculate salience components
        novelty = self._calculate_novelty(metrics, events)
        relevance = self._calculate_relevance(metrics, events)
        urgency = self._calculate_urgency(metrics, events)

        # Create salience score
        salience = SalienceScore(
            novelty=novelty, relevance=relevance, urgency=urgency, confidence=0.9
        )

        # Calculate total salience
        total_salience = salience.compute_total()

        # Decide if trigger should fire
        should_trigger = total_salience >= self.salience_threshold

        # Find triggering events (high salience events)
        triggering_events = [
            e
            for e in events
            if e.novelty >= 0.7 or e.relevance >= 0.8 or e.urgency >= 0.8
        ]

        # Generate reason
        reason = self._generate_decision_reason(
            should_trigger, salience, metrics, triggering_events
        )

        # Calculate confidence
        confidence = self._calculate_confidence(metrics, events, salience)

        decision = OrchestrationDecision(
            should_trigger_esgt=should_trigger,
            salience=salience,
            reason=reason,
            triggering_events=triggering_events,
            metrics_snapshot=metrics,
            timestamp=now,
            confidence=confidence,
        )

        if should_trigger:
            logger.info(
                f"🎯 Orchestrator decision: TRIGGER ESGT "
                f"(salience={total_salience:.2f}, "
                f"novelty={novelty:.2f}, relevance={relevance:.2f}, urgency={urgency:.2f})"
            )
        else:
            logger.debug(
                f"Orchestrator decision: No trigger "
                f"(salience={total_salience:.2f} < threshold={self.salience_threshold})"
            )

        return decision

    def _calculate_novelty(
        self, metrics: SystemMetrics, events: List[ConsciousnessEvent]
    ) -> float:
        """Calculate novelty component of salience.

        Novelty is high when:
        - New high-severity events occur
        - Metrics show unexpected patterns
        - ESGT frequency is low (novel consciousness moments)

        Args:
            metrics: System metrics
            events: Recent events

        Returns:
            Novelty score (0-1)
        """
        novelty = 0.5  # Baseline

        # Factor 1: Event novelty (weighted by severity)
        if events:
            event_novelties = []
            for event in events:
                weight = 1.0
                if event.severity == EventSeverity.CRITICAL:
                    weight = 1.5
                elif event.severity == EventSeverity.HIGH:
                    weight = 1.2

                event_novelties.append(event.novelty * weight)

            # Calculate average novelty (guaranteed non-empty due to events check)
            novelty = sum(event_novelties) / len(event_novelties)

        # Factor 2: Low ESGT frequency = higher novelty for new events
        if metrics.esgt_frequency_hz < 1.0:
            novelty += 0.1

        # Factor 3: Extreme arousal is novel
        if metrics.arousal_level < 0.2 or metrics.arousal_level > 0.9:
            novelty += 0.2

        return min(1.0, novelty)

    def _calculate_relevance(
        self, metrics: SystemMetrics, events: List[ConsciousnessEvent]
    ) -> float:
        """Calculate relevance component of salience.

        Relevance is high when:
        - Events are relevant to system goals
        - System health is degraded (needs attention)
        - PFC/ToM showing social cognition activity

        Args:
            metrics: System metrics
            events: Recent events

        Returns:
            Relevance score (0-1)
        """
        relevance = 0.5  # Baseline

        # Factor 1: Event relevance (weighted average)
        if events:
            relevances = [e.relevance for e in events]
            relevance = sum(relevances) / len(relevances)

        # Factor 2: Low health = high relevance (system needs attention)
        if metrics.health_score < 0.7:
            relevance += 0.2

        # Factor 3: PFC activity (social cognition is relevant)
        if metrics.pfc_signals_processed > 0:
            relevance += 0.1

        # Factor 4: Safety violations are highly relevant
        if metrics.safety_violations > 0:
            relevance = min(1.0, relevance + 0.3)

        return min(1.0, relevance)

    def _calculate_urgency(
        self, metrics: SystemMetrics, events: List[ConsciousnessEvent]
    ) -> float:
        """Calculate urgency component of salience.

        Urgency is high when:
        - Critical events occur
        - Safety violations present
        - Kill switch triggered
        - Extreme arousal states

        Args:
            metrics: System metrics
            events: Recent events

        Returns:
            Urgency score (0-1)
        """
        urgency = 0.3  # Baseline (low default urgency)

        # Factor 1: Event urgency (max of all events)
        if events:
            urgency = max(e.urgency for e in events)

        # Factor 2: Safety violations = critical urgency
        if metrics.safety_violations > 0:
            urgency = max(urgency, 0.9)

        # Factor 3: Kill switch = maximum urgency
        if metrics.kill_switch_active:
            urgency = 1.0

        # Factor 4: Extreme arousal = moderate urgency
        if metrics.arousal_level < 0.2 or metrics.arousal_level > 0.9:
            urgency = max(urgency, 0.6)

        return min(1.0, urgency)

    def _generate_decision_reason(
        self,
        should_trigger: bool,
        salience: SalienceScore,
        metrics: SystemMetrics,
        triggering_events: List[ConsciousnessEvent],
    ) -> str:
        """Generate human-readable reason for decision.

        Args:
            should_trigger: Whether trigger was recommended
            salience: Salience score
            metrics: System metrics
            triggering_events: Events that contributed to trigger

        Returns:
            Reason string
        """
        if not should_trigger:
            return f"Salience below threshold ({salience.compute_total():.2f} < {self.salience_threshold})"

        reasons = []

        if triggering_events:
            event_types = set(e.event_type.value for e in triggering_events)
            reasons.append(f"{len(triggering_events)} high-salience events ({', '.join(event_types)})")

        if metrics.safety_violations > 0:
            reasons.append(f"{metrics.safety_violations} safety violations")

        if metrics.health_score < 0.7:
            reasons.append(f"low system health ({metrics.health_score:.2f})")

        if metrics.pfc_signals_processed > 0:
            reasons.append("PFC social cognition active")

        if not reasons:
            reasons.append("high computed salience")

        return "ESGT trigger: " + ", ".join(reasons)

    def _calculate_confidence(
        self,
        metrics: SystemMetrics,
        events: List[ConsciousnessEvent],
        salience: SalienceScore,
    ) -> float:
        """Calculate confidence in orchestration decision.

        Confidence is high when:
        - Metrics collection was error-free
        - Salience components are consistent
        - System health is good

        Args:
            metrics: System metrics
            events: Recent events
            salience: Computed salience

        Returns:
            Confidence score (0-1)
        """
        confidence = 1.0

        # Penalize for collection errors
        if metrics.errors:
            confidence -= 0.1 * len(metrics.errors)

        # Penalize for low health
        if metrics.health_score < 0.5:
            confidence -= 0.2

        # Penalize for inconsistent salience (large variance)
        salience_components = [salience.novelty, salience.relevance, salience.urgency]
        variance = max(salience_components) - min(salience_components)
        if variance > 0.5:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    async def _execute_esgt_trigger(self, decision: OrchestrationDecision) -> None:
        """Execute ESGT trigger based on orchestration decision.

        Args:
            decision: Orchestration decision with trigger details
        """
        self.total_triggers_generated += 1

        try:
            # Prepare content for ESGT
            content = {
                "type": "orchestrated_trigger",
                "reason": decision.reason,
                "triggering_events": [
                    {
                        "event_id": e.event_id,
                        "type": e.event_type.value,
                        "severity": e.severity.value,
                        "source": e.source,
                    }
                    for e in decision.triggering_events
                ],
                "metrics": {
                    "health_score": decision.metrics_snapshot.health_score,
                    "arousal": decision.metrics_snapshot.arousal_level,
                    "esgt_success_rate": decision.metrics_snapshot.esgt_success_rate,
                },
                "confidence": decision.confidence,
            }

            # Trigger ESGT
            event = await self.system.esgt_coordinator.initiate_esgt(
                salience=decision.salience,
                content=content,
                content_source="DataOrchestrator",
            )

            if event.success:
                self.total_triggers_executed += 1
                logger.info(
                    f"✅ ESGT trigger executed successfully: "
                    f"event_id={event.event_id}, "
                    f"coherence={event.achieved_coherence:.2f}"
                )
            else:
                logger.warning(
                    f"⚠️  ESGT trigger failed: {event.failure_reason}"
                )

            # Mark triggering events as processed
            for e in decision.triggering_events:
                self.event_collector.mark_processed(e.event_id)
                e.esgt_triggered = True

        except Exception as e:
            logger.error(f"Error executing ESGT trigger: {e}")

    def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics.

        Returns:
            Dict with collection, trigger, and performance stats
        """
        metrics_stats = self.metrics_collector.get_collection_stats()
        event_stats = self.event_collector.get_collection_stats()

        return {
            "total_collections": self.total_collections,
            "total_triggers_generated": self.total_triggers_generated,
            "total_triggers_executed": self.total_triggers_executed,
            "trigger_execution_rate": (
                self.total_triggers_executed / max(1, self.total_triggers_generated)
            ),
            "decision_history_size": len(self.decision_history),
            "metrics_collector": metrics_stats,
            "event_collector": event_stats,
            "collection_interval_ms": self.collection_interval_ms,
            "salience_threshold": self.salience_threshold,
        }

    def get_recent_decisions(self, limit: int = 10) -> List[OrchestrationDecision]:
        """Get recent orchestration decisions.

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of recent decisions (newest first)
        """
        recent = self.decision_history[-limit:]
        return sorted(recent, key=lambda d: d.timestamp, reverse=True)

    def __repr__(self) -> str:
        return (
            f"DataOrchestrator("
            f"running={self._running}, "
            f"collections={self.total_collections}, "
            f"triggers={self.total_triggers_executed}/{self.total_triggers_generated})"
        )
