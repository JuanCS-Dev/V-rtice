"""
SalienceSPM - Salience Detection for ESGT Trigger Control
==========================================================

This module implements the critical salience detection mechanism that determines
what information becomes conscious via ESGT ignition.

Theoretical Foundation:
-----------------------
Global Workspace Dynamics (Dehaene et al., 2021) proposes that consciousness
emerges when information exceeds a salience threshold, triggering global broadcast.

**Salience Dimensions** (weighted combination):

1. **Novelty** (0.4 weight):
   - How unexpected/surprising is the information?
   - Computed via prediction error or change detection
   - High novelty → attention capture

2. **Relevance** (0.4 weight):
   - How important is this for current goals/context?
   - Computed via goal alignment or semantic similarity
   - High relevance → prioritized processing

3. **Urgency** (0.2 weight):
   - How time-critical is this information?
   - Computed via threat detection or deadline proximity
   - High urgency → immediate conscious access

**Biological Correspondence**:
Salience network in humans (anterior insula + dorsal ACC) performs similar
function: gating what enters consciousness based on these dimensions.

Implementation:
---------------
SalienceSPM continuously monitors:
- Internal metrics (MMEI needs)
- External events (user commands, alerts)
- Processing outputs (other SPMs)

It computes salience scores and triggers ESGT when threshold exceeded.

Historical Context:
-------------------
First artificial salience network for consciousness gating.
This SPM is the "attention controller" - it decides what MAXIMUS becomes aware of.

"Salience is the gatekeeper of consciousness."
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from consciousness.esgt.coordinator import SalienceScore
from consciousness.esgt.spm.base import (
    SpecializedProcessingModule,
    SPMOutput,
    SPMType,
)


class SalienceMode(Enum):
    """Operating mode for salience detection."""

    PASSIVE = "passive"  # Only compute when asked
    ACTIVE = "active"  # Continuously monitor and alert


@dataclass
class SalienceThresholds:
    """Thresholds for salience classification."""

    low_threshold: float = 0.30  # Below: unconscious processing
    medium_threshold: float = 0.50  # Peripheral awareness
    high_threshold: float = 0.70  # Conscious access (ESGT trigger)
    critical_threshold: float = 0.90  # Immediate priority


@dataclass
class SalienceDetectorConfig:
    """Configuration for salience detection."""

    # Mode
    mode: SalienceMode = SalienceMode.ACTIVE
    update_interval_ms: float = 50.0  # 20 Hz monitoring

    # Weights (must sum to 1.0)
    novelty_weight: float = 0.4
    relevance_weight: float = 0.4
    urgency_weight: float = 0.2

    # Thresholds
    thresholds: SalienceThresholds = field(default_factory=SalienceThresholds)

    # Novelty detection
    novelty_baseline_window: int = 50  # Samples for baseline
    novelty_change_threshold: float = 0.15  # Change detection

    # Relevance computation
    default_relevance: float = 0.5  # When context unavailable

    # Urgency computation
    urgency_decay_rate: float = 0.1  # Per second
    urgency_boost_on_error: float = 0.3

    # History
    max_history_size: int = 100


@dataclass
class SalienceEvent:
    """Record of a high-salience detection."""

    timestamp: float
    salience: SalienceScore
    source: str
    content: dict[str, Any]
    threshold_exceeded: float


class SalienceSPM(SpecializedProcessingModule):
    """
    Specialized Processing Module for salience detection.

    SalienceSPM is the "attention controller" of MAXIMUS consciousness.
    It continuously monitors internal and external information streams,
    computing salience scores to determine what should trigger ESGT ignition.

    This SPM doesn't process domain-specific content - it meta-processes
    outputs from other SPMs and internal metrics to decide conscious access.

    Architecture:
    -------------
    ```
    Internal Metrics (MMEI) ─┐
    External Events         ─┼→ Salience Computation → Threshold Check
    Other SPM Outputs       ─┘                              ↓
                                                    High Salience?
                                                           ↓
                                                    Trigger ESGT
    ```

    Example:
    --------
    ```python
    detector = SalienceSPM("salience-01")
    await detector.start()

    # Register for high-salience alerts
    detector.register_high_salience_callback(on_high_salience)

    # Monitor continuous stream
    for event in stream:
        detector.evaluate_event(event)
        # If salience > threshold, callback fires
    ```
    """

    def __init__(
        self,
        spm_id: str,
        config: SalienceDetectorConfig | None = None,
    ):
        """
        Initialize SalienceSPM.

        Args:
            spm_id: Unique identifier
            config: Detection configuration
        """
        super().__init__(spm_id, SPMType.METACOGNITIVE)

        self.config = config or SalienceDetectorConfig()

        # Validate weights
        total_weight = self.config.novelty_weight + self.config.relevance_weight + self.config.urgency_weight
        if not (0.99 < total_weight < 1.01):  # Allow floating point tolerance
            raise ValueError(f"Salience weights must sum to 1.0, got {total_weight}")

        # State
        self._running: bool = False
        self._monitoring_task: asyncio.Task | None = None

        # Novelty tracking (for change detection)
        self._metric_history: dict[str, list[float]] = {}
        self._baseline_values: dict[str, float] = {}

        # Urgency tracking (decays over time)
        self._urgency_sources: dict[str, tuple[float, float]] = {}  # source: (urgency, timestamp)

        # Event history
        self._high_salience_events: list[SalienceEvent] = []

        # Callbacks
        self._high_salience_callbacks: list[Callable[[SalienceEvent], None]] = []

        # Metrics
        self.total_evaluations: int = 0
        self.high_salience_count: int = 0

    async def start(self) -> None:
        """Start salience monitoring."""
        if self._running:
            return

        self._running = True

        if self.config.mode == SalienceMode.ACTIVE:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self) -> None:
        """Stop salience monitoring."""
        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        self._monitoring_task = None

    async def _monitoring_loop(self) -> None:
        """
        Active monitoring loop.

        Periodically decays urgency and checks for timeout conditions.
        """
        interval_s = self.config.update_interval_ms / 1000.0

        while self._running:
            try:
                # Decay urgencies
                self._decay_urgencies()

                await asyncio.sleep(interval_s)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[SalienceSPM {self.spm_id}] Monitoring error: {e}")
                await asyncio.sleep(interval_s)

    def evaluate_event(
        self,
        source: str,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> SalienceScore:
        """
        Evaluate salience of an event.

        This is the core salience computation. Call this for any event
        that might need to become conscious.

        Args:
            source: Identifier of event source
            content: Event content
            context: Optional context for relevance computation

        Returns:
            SalienceScore with novelty, relevance, urgency
        """
        self.total_evaluations += 1

        # Compute dimensions
        novelty = self._compute_novelty(source, content)
        relevance = self._compute_relevance(content, context)
        urgency = self._get_current_urgency(source)

        # Calculate delta (confidence weight) to ensure weights sum to 1.0
        delta_weight = 1.0 - (self.config.novelty_weight + self.config.relevance_weight + self.config.urgency_weight)

        salience = SalienceScore(
            novelty=novelty,
            relevance=relevance,
            urgency=urgency,
            alpha=self.config.novelty_weight,
            beta=self.config.relevance_weight,
            gamma=self.config.urgency_weight,
            delta=max(0.0, delta_weight),  # Confidence weight
        )

        # Check if high salience
        total_salience = salience.compute_total()

        # DEBUG: Print salience computation
        # print(f"[SalienceSPM] {source}: novelty={novelty:.3f}, relevance={relevance:.3f}, urgency={urgency:.3f}, total={total_salience:.3f}, threshold={self.config.thresholds.high_threshold:.3f}")

        if total_salience >= self.config.thresholds.high_threshold:
            self._handle_high_salience(source, content, salience)

        return salience

    def _compute_novelty(self, source: str, content: dict[str, Any]) -> float:
        """
        Compute novelty via change detection.

        Novelty = how much this deviates from recent baseline.
        """
        # Extract numeric value to track (if available)
        value = self._extract_tracking_value(content)

        if value is None:
            # No trackable value, use default moderate novelty
            return 0.55  # Slightly above baseline to allow critical priorities to trigger

        # Update history
        if source not in self._metric_history:
            self._metric_history[source] = []

        self._metric_history[source].append(value)

        # Keep only recent window
        window = self.config.novelty_baseline_window
        if len(self._metric_history[source]) > window:
            self._metric_history[source].pop(0)

        # Compute baseline (mean of recent values)
        history = self._metric_history[source]
        if len(history) < 3:
            # Not enough data for baseline
            return 0.55  # Slightly above baseline to allow critical priorities to trigger

        baseline = np.mean(history[:-1])  # All but current
        self._baseline_values[source] = baseline

        # Compute deviation
        if baseline == 0:
            deviation = 1.0 if value > 0 else 0.0
        else:
            deviation = abs(value - baseline) / max(abs(baseline), 1.0)

        # Normalize to [0, 1]
        novelty = min(1.0, deviation / self.config.novelty_change_threshold)

        return novelty

    def _extract_tracking_value(self, content: dict[str, Any]) -> float | None:
        """Extract a numeric value to track for novelty detection."""
        # Try common keys
        for key in ["value", "metric", "score", "level", "magnitude"]:
            if key in content:
                val = content[key]
                if isinstance(val, (int, float)):
                    return float(val)

        # Try any numeric value
        for val in content.values():
            if isinstance(val, (int, float)):
                return float(val)

        return None

    def _compute_relevance(
        self,
        content: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> float:
        """
        Compute relevance to current goals/context.

        In full implementation, would use semantic similarity or goal alignment.
        For now, uses heuristics.
        """
        # Collect relevance from multiple sources
        relevance_scores = []

        # Check for explicit relevance score
        if "relevance" in content:
            relevance_scores.append(float(content["relevance"]))

        # Check for priority mapping
        if "priority" in content:
            priority = content["priority"]
            priority_map = {
                "low": 0.3,
                "medium": 0.5,
                "high": 0.7,
                "critical": 0.95,
            }
            if isinstance(priority, str) and priority.lower() in priority_map:
                relevance_scores.append(priority_map[priority.lower()])

        # Check for goal alignment
        if context and "goal_id" in content and "active_goals" in context:
            active_goals = context["active_goals"]
            if content["goal_id"] in active_goals:
                relevance_scores.append(0.8)

        # Check for need alignment
        if context and "need" in content and "current_needs" in context:
            need = content["need"]
            current_needs = context["current_needs"]
            if need in current_needs:
                relevance_scores.append(min(1.0, current_needs[need] * 1.2))

        # Return max of all sources, or default
        return max(relevance_scores) if relevance_scores else self.config.default_relevance

    def _get_current_urgency(self, source: str) -> float:
        """Get current urgency level (with decay)."""
        if source not in self._urgency_sources:
            return 0.0

        urgency, timestamp = self._urgency_sources[source]

        # Apply decay
        elapsed = time.time() - timestamp
        decayed = urgency * np.exp(-self.config.urgency_decay_rate * elapsed)

        # Update stored value
        self._urgency_sources[source] = (decayed, time.time())

        return max(0.0, decayed)

    def set_urgency(self, source: str, urgency: float) -> None:
        """
        Explicitly set urgency for a source.

        Call this when detecting time-critical conditions (errors, threats, deadlines).
        """
        urgency = max(0.0, min(1.0, urgency))
        self._urgency_sources[source] = (urgency, time.time())

    def boost_urgency_on_error(self, source: str) -> None:
        """Boost urgency when errors detected."""
        current = self._get_current_urgency(source)
        boosted = min(1.0, current + self.config.urgency_boost_on_error)
        self.set_urgency(source, boosted)

    def _decay_urgencies(self) -> None:
        """Decay all urgency sources."""
        for source in list(self._urgency_sources.keys()):
            self._get_current_urgency(source)  # Triggers decay

            # Remove if fully decayed
            if self._urgency_sources[source][0] < 0.01:
                del self._urgency_sources[source]

    def _handle_high_salience(
        self,
        source: str,
        content: dict[str, Any],
        salience: SalienceScore,
    ) -> None:
        """Handle high-salience detection."""
        self.high_salience_count += 1

        # Create event
        event = SalienceEvent(
            timestamp=time.time(),
            salience=salience,
            source=source,
            content=content,
            threshold_exceeded=self.config.thresholds.high_threshold,
        )

        # Add to history
        self._high_salience_events.append(event)
        if len(self._high_salience_events) > self.config.max_history_size:
            self._high_salience_events.pop(0)

        # Notify callbacks
        for callback in self._high_salience_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"[SalienceSPM {self.spm_id}] Callback error: {e}")

    # =========================================================================
    # Abstract Method Implementations
    # =========================================================================

    async def process(self) -> SPMOutput | None:
        """
        Process and generate output (required by base class).

        SalienceSPM operates via evaluate_event() calls rather than
        autonomous processing, so this returns None.
        """
        return None

    def compute_salience(self, data: dict[str, Any]) -> SalienceScore:
        """
        Compute salience for given data (required by base class).

        This delegates to evaluate_event() with default source.
        """
        return self.evaluate_event(
            source="compute_salience",
            content=data,
            context=None,
        )

    # =========================================================================
    # SalienceSPM-Specific Methods
    # =========================================================================

    def register_high_salience_callback(self, callback: Callable[[SalienceEvent], None]) -> None:
        """Register callback for high-salience events."""
        if callback not in self._high_salience_callbacks:
            self._high_salience_callbacks.append(callback)

    def get_recent_high_salience_events(self, count: int = 10) -> list[SalienceEvent]:
        """Get recent high-salience events."""
        return self._high_salience_events[-count:]

    def get_salience_rate(self) -> float:
        """Get percentage of evaluations that were high-salience."""
        if self.total_evaluations == 0:
            return 0.0
        return self.high_salience_count / self.total_evaluations

    def get_metrics(self) -> dict[str, Any]:
        """Get detector performance metrics."""
        return {
            "spm_id": self.spm_id,
            "running": self._running,
            "total_evaluations": self.total_evaluations,
            "high_salience_count": self.high_salience_count,
            "salience_rate": self.get_salience_rate(),
            "tracked_sources": len(self._metric_history),
            "active_urgencies": len(self._urgency_sources),
        }

    def __repr__(self) -> str:
        return (
            f"SalienceSPM(id={self.spm_id}, "
            f"evals={self.total_evaluations}, "
            f"high_salience={self.high_salience_count}, "
            f"rate={self.get_salience_rate():.1%})"
        )
