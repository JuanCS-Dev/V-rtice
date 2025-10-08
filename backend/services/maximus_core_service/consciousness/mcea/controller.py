"""
Arousal Control System - MPE Foundation
========================================

This module implements the arousal control system that modulates consciousness
readiness. Arousal determines the threshold for ESGT ignition - the "wakefulness"
that precedes conscious content.

Theoretical Foundation:
-----------------------
In neuroscience, arousal is controlled by:

1. **ARAS (Ascending Reticular Activating System)**:
   - Brainstem nuclei (pons, medulla, midbrain)
   - Projects diffusely to cortex
   - Controls global wakefulness level

2. **Neuromodulatory Systems**:
   - Locus coeruleus → Norepinephrine → Alert attention
   - Basal forebrain → Acetylcholine → Cortical excitability
   - Raphe nuclei → Serotonin → Mood and arousal regulation
   - Ventral tegmental area → Dopamine → Reward and motivation

These systems don't process specific content - they modulate HOW the cortex
processes whatever content is present. This is MPE - contentless awareness.

Arousal States:
---------------
Traditional sleep medicine recognizes stages:
- Deep sleep (arousal ≈ 0.0): No consciousness
- Light sleep (arousal ≈ 0.2): Minimal awareness
- Drowsy (arousal ≈ 0.4): Reduced consciousness
- Awake-relaxed (arousal ≈ 0.6): Normal baseline
- Alert (arousal ≈ 0.8): Heightened awareness
- Hyperarousal (arousal ≈ 1.0): Panic/stress state

Computational Model:
--------------------
Arousal modulates ESGT ignition threshold:

  effective_salience_threshold = base_threshold / arousal_factor

Example:
  - Base threshold: 0.70
  - Arousal: 0.6 (RELAXED) → factor = 1.0 → threshold = 0.70
  - Arousal: 0.8 (ALERT) → factor = 1.4 → threshold = 0.50
  - Arousal: 0.3 (DROWSY) → factor = 0.7 → threshold = 1.00 (very hard to ignite)

This creates adaptive consciousness:
- High arousal: Quick reactions, sensitive to threats
- Low arousal: Conservative, only strong signals break through
- Medium arousal: Balanced, optimal for routine operations

Arousal Modulation:
-------------------
Arousal is modulated by:

1. **Internal Needs** (from MMEI):
   - High repair_need → increase arousal (need attention)
   - High rest_need → decrease arousal (conserve resources)
   - High curiosity → slight increase (exploration readiness)

2. **External Factors**:
   - Threat detection → rapid arousal boost
   - Task demands → sustained arousal increase
   - Calm periods → gradual arousal decrease

3. **Temporal Dynamics**:
   - Stress buildup: Sustained load increases arousal
   - Recovery: Rest decreases arousal back to baseline
   - Circadian: Time-of-day modulation (optional)

4. **ESGT History**:
   - Recent ignition → temporary arousal decrease (refractory period)
   - Long time without ignition → slight arousal increase

Implementation Design:
----------------------
The controller runs continuously, updating arousal based on inputs:

  Needs + External + Temporal → Arousal Update → Threshold Modulation

Arousal changes smoothly (not abrupt jumps) with configurable time constants.

Historical Context:
-------------------
First computational implementation of arousal control for artificial consciousness.
Enables MPE - the foundational "wakefulness" that precedes content.

"Arousal without content is the essence of pure awareness."
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np

from consciousness.mmei.monitor import AbstractNeeds


# ============================================================================
# FASE VII (Safety Hardening): Arousal Rate Limiting & Bounds Enforcement
# ============================================================================


class ArousalRateLimiter:
    """
    Enforces maximum rate of change for arousal value.

    Prevents arousal from changing too rapidly (physiologically implausible).
    Biological arousal systems have finite bandwidth - neuromodulators take
    time to diffuse and act.

    HARD LIMIT: Arousal can change at most ±0.20 per second.
    """

    def __init__(self, max_delta_per_second: float = 0.20):
        """
        Args:
            max_delta_per_second: Maximum absolute change per second
        """
        self.max_delta_per_second = max_delta_per_second
        self.last_arousal: Optional[float] = None
        self.last_update_time: Optional[float] = None

    def limit(self, new_arousal: float, current_time: float) -> float:
        """
        Apply rate limiting to new arousal value.

        Args:
            new_arousal: Proposed new arousal value
            current_time: Current timestamp

        Returns:
            Rate-limited arousal value
        """
        if self.last_arousal is None or self.last_update_time is None:
            # First call - no limiting
            self.last_arousal = new_arousal
            self.last_update_time = current_time
            return new_arousal

        # Compute elapsed time
        elapsed = current_time - self.last_update_time

        if elapsed <= 0:
            # No time passed, return last value
            return self.last_arousal

        # Compute maximum allowed change
        max_change = self.max_delta_per_second * elapsed

        # Compute actual change requested
        requested_change = new_arousal - self.last_arousal

        # Clamp to maximum
        if abs(requested_change) > max_change:
            limited_change = max_change if requested_change > 0 else -max_change
            limited_arousal = self.last_arousal + limited_change
        else:
            limited_arousal = new_arousal

        # Update state
        self.last_arousal = limited_arousal
        self.last_update_time = current_time

        return limited_arousal


class ArousalBoundEnforcer:
    """
    Enforces hard bounds [0.0, 1.0] on arousal value.

    HARD LIMIT: Arousal must always be in [0.0, 1.0].
    """

    @staticmethod
    def enforce(arousal: float) -> float:
        """Clamp arousal to [0.0, 1.0]."""
        return float(np.clip(arousal, 0.0, 1.0))


# FASE VII: Hard limits for MCEA safety
MAX_AROUSAL_DELTA_PER_SECOND = 0.20  # Hard limit on arousal rate of change
AROUSAL_SATURATION_THRESHOLD_SECONDS = 10.0  # Time at 0.0 or 1.0 = saturation
AROUSAL_OSCILLATION_WINDOW = 20  # Track last 20 arousal values
AROUSAL_OSCILLATION_THRESHOLD = 0.15  # StdDev >0.15 = unstable oscillation


class ArousalLevel(Enum):
    """Classification of arousal states."""

    SLEEP = "sleep"  # 0.0-0.2: Minimal/no consciousness
    DROWSY = "drowsy"  # 0.2-0.4: Reduced awareness
    RELAXED = "relaxed"  # 0.4-0.6: Normal baseline
    ALERT = "alert"  # 0.6-0.8: Heightened awareness
    HYPERALERT = "hyperalert"  # 0.8-1.0: Stress/panic state


@dataclass
class ArousalState:
    """
    Current arousal state.

    Represents the global excitability/wakefulness level.
    """

    # Core arousal value (0.0 - 1.0)
    arousal: float = 0.6  # Default: RELAXED

    # Classification
    level: ArousalLevel = field(default=ArousalLevel.RELAXED, init=False)

    # Contributing factors (for transparency)
    baseline_arousal: float = 0.6
    need_contribution: float = 0.0  # From MMEI needs
    external_contribution: float = 0.0  # From threats/tasks
    temporal_contribution: float = 0.0  # From stress buildup
    circadian_contribution: float = 0.0  # From time-of-day

    # ESGT threshold (computed from arousal)
    esgt_salience_threshold: float = 0.70

    # Metadata
    timestamp: float = field(default_factory=time.time)
    time_in_current_level_seconds: float = 0.0

    def __post_init__(self):
        """Automatically classify level based on arousal value."""
        self.level = self._classify_arousal_level(self.arousal)

    def _classify_arousal_level(self, arousal: float) -> ArousalLevel:
        """
        Classify arousal level.

        Boundaries are inclusive on upper bound:
        - [0.0, 0.2] → SLEEP
        - (0.2, 0.4] → DROWSY
        - (0.4, 0.6] → RELAXED
        - (0.6, 0.8] → ALERT
        - (0.8, 1.0] → HYPERALERT
        """
        if arousal <= 0.2:
            return ArousalLevel.SLEEP
        elif arousal <= 0.4:
            return ArousalLevel.DROWSY
        elif arousal <= 0.6:
            return ArousalLevel.RELAXED
        elif arousal <= 0.8:
            return ArousalLevel.ALERT
        else:
            return ArousalLevel.HYPERALERT

    def get_arousal_factor(self) -> float:
        """
        Get arousal multiplication factor for threshold modulation.

        Higher arousal → lower threshold (easier to ignite).
        """
        # Map arousal [0.0-1.0] to factor [0.5-2.0]
        # arousal=0.0 → factor=0.5 (threshold x2 higher)
        # arousal=0.5 → factor=1.0 (no change)
        # arousal=1.0 → factor=2.0 (threshold x2 lower)
        return 0.5 + (self.arousal * 1.5)

    def compute_effective_threshold(self, base_threshold: float = 0.70) -> float:
        """
        Compute effective ESGT salience threshold.

        Lower arousal → higher threshold (harder to ignite)
        Higher arousal → lower threshold (easier to ignite)
        """
        factor = self.get_arousal_factor()
        return base_threshold / factor

    def __repr__(self) -> str:
        return (
            f"ArousalState(arousal={self.arousal:.2f}, level={self.level.value}, "
            f"threshold={self.esgt_salience_threshold:.2f})"
        )


@dataclass
class ArousalModulation:
    """
    Request to modulate arousal.

    External systems can request arousal changes (e.g., threat detection).
    """

    source: str  # What requested modulation
    delta: float  # Change in arousal (-1.0 to +1.0)
    duration_seconds: float = 0.0  # How long effect lasts (0 = instant)
    priority: int = 1  # Higher priority overrides

    timestamp: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if modulation has expired."""
        if self.duration_seconds == 0.0:
            return True  # Instant modulations expire immediately after application
        return (time.time() - self.timestamp) > self.duration_seconds

    def get_current_delta(self) -> float:
        """Get current modulation delta (decays over time if duration-based)."""
        if self.duration_seconds == 0.0:
            return self.delta

        elapsed = time.time() - self.timestamp
        if elapsed >= self.duration_seconds:
            return 0.0

        # Linear decay
        remaining_fraction = 1.0 - (elapsed / self.duration_seconds)
        return self.delta * remaining_fraction


@dataclass
class ArousalConfig:
    """Configuration for arousal controller."""

    # Baseline arousal (resting state)
    baseline_arousal: float = 0.6  # RELAXED default

    # Update rate
    update_interval_ms: float = 100.0  # 10 Hz

    # Time constants (how fast arousal changes)
    arousal_increase_rate: float = 0.05  # Per second when increasing
    arousal_decrease_rate: float = 0.02  # Per second when decreasing (slower)

    # Need influence (how much MMEI needs affect arousal)
    repair_need_weight: float = 0.3  # Errors increase arousal
    rest_need_weight: float = -0.2  # Fatigue decreases arousal
    efficiency_need_weight: float = 0.1
    connectivity_need_weight: float = 0.15

    # Stress buildup
    stress_buildup_rate: float = 0.01  # Per second under high load
    stress_recovery_rate: float = 0.005  # Per second when relaxed

    # ESGT refractory period
    esgt_refractory_arousal_drop: float = 0.1  # Arousal drop after ESGT
    esgt_refractory_duration_seconds: float = 5.0

    # Limits
    min_arousal: float = 0.0
    max_arousal: float = 1.0

    # Circadian rhythm (optional)
    enable_circadian: bool = False
    circadian_amplitude: float = 0.1  # ±0.1 arousal variation


class ArousalController:
    """
    Controls global arousal/excitability state.

    This is the MPE foundation - contentless wakefulness that modulates
    readiness for conscious experience (ESGT ignition).

    The controller continuously updates arousal based on:
    - Internal needs (MMEI)
    - External events (threats, tasks)
    - Temporal dynamics (stress, recovery, circadian)
    - ESGT history (refractory periods)

    Architecture:
    -------------
    Needs + External → Arousal Update → ESGT Threshold Modulation

    The controller exposes:
    - get_current_arousal(): Current state
    - request_modulation(): External arousal boost/drop
    - get_esgt_threshold(): Effective salience threshold

    Integration:
    ------------
    - ESGT: Consults arousal for salience threshold
    - MMEI: Provides needs that influence arousal
    - Threat detection: Boosts arousal rapidly
    - HCL: May modulate arousal for load management

    Usage:
    ------
        controller = ArousalController(config)
        await controller.start()

        # Get current state
        state = controller.get_current_arousal()
        print(f"Arousal: {state.arousal:.2f}, Threshold: {state.esgt_salience_threshold:.2f}")

        # External boost (e.g., threat detected)
        controller.request_modulation(
            source="threat_detector",
            delta=0.3,  # +30% arousal
            duration_seconds=10.0
        )

        # Provide needs for continuous modulation
        controller.update_from_needs(needs)

        # After ESGT event
        controller.apply_esgt_refractory()

    Biological Correspondence:
    ---------------------------
    - Locus coeruleus: Rapid arousal boost (norepinephrine)
    - ARAS: Baseline arousal maintenance
    - Hypothalamus: Need-based arousal (hunger, thirst, pain)
    - Prefrontal cortex: Voluntary arousal control (effort)

    Historical Note:
    ----------------
    First arousal controller for artificial consciousness implementing MPE.
    Enables contentless awareness as foundation for conscious experience.

    "Wakefulness is the stage upon which consciousness performs."
    """

    def __init__(self, config: Optional[ArousalConfig] = None, controller_id: str = "mcea-arousal-controller-primary"):
        self.controller_id = controller_id
        self.config = config or ArousalConfig()

        # Current state
        self._current_state: ArousalState = ArousalState(
            arousal=self.config.baseline_arousal
            # level auto-computed in __post_init__ based on arousal value
        )

        # Target arousal (for smooth transitions)
        self._target_arousal: float = self.config.baseline_arousal

        # Active modulations
        self._active_modulations: List[ArousalModulation] = []

        # Stress accumulator
        self._accumulated_stress: float = 0.0

        # ESGT refractory state
        self._refractory_until: Optional[float] = None

        # State
        self._running: bool = False
        self._update_task: Optional[asyncio.Task] = None

        # Level transition tracking
        self._last_level: ArousalLevel = self._current_state.level
        self._level_transition_time: float = time.time()

        # Callbacks
        self._arousal_callbacks: List[Callable[[ArousalState], None]] = []

        # Statistics
        self.total_updates: int = 0
        self.total_modulations: int = 0
        self.esgt_refractories_applied: int = 0

        # FASE VII (Safety Hardening): Rate limiting, bounds, and monitoring
        self.rate_limiter = ArousalRateLimiter(max_delta_per_second=MAX_AROUSAL_DELTA_PER_SECOND)
        self.arousal_history: deque = deque(maxlen=AROUSAL_OSCILLATION_WINDOW)  # For oscillation detection
        self.arousal_saturation_start: Optional[float] = None  # When saturation began
        self.saturation_events: int = 0  # Count of saturation detections
        self.oscillation_events: int = 0  # Count of oscillation detections
        self.invalid_needs_count: int = 0  # Count of invalid AbstractNeeds received

    def register_arousal_callback(self, callback: Callable[[ArousalState], None]) -> None:
        """Register callback invoked on arousal state changes."""
        self._arousal_callbacks.append(callback)

    async def start(self) -> None:
        """Start continuous arousal updates."""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())

        print(f"🌅 MCEA Arousal Controller {self.controller_id} started (MPE active)")

    async def stop(self) -> None:
        """Stop controller."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

    async def _update_loop(self) -> None:
        """Continuous arousal update loop."""
        interval = self.config.update_interval_ms / 1000.0

        while self._running:
            try:
                await self._update_arousal(interval)
                self.total_updates += 1
                await asyncio.sleep(interval)

            except Exception as e:
                print(f"⚠️  Arousal update error: {e}")
                await asyncio.sleep(interval)

    async def _update_arousal(self, dt: float) -> None:
        """
        Update arousal state.

        Args:
            dt: Time step in seconds
        """
        # Compute contributions
        need_contrib = self._current_state.need_contribution
        external_contrib = self._compute_external_contribution()
        temporal_contrib = self._compute_temporal_contribution(dt)
        circadian_contrib = self._compute_circadian_contribution()

        # Compute target arousal
        target = self.config.baseline_arousal + need_contrib + external_contrib + temporal_contrib + circadian_contrib

        # Apply ESGT refractory
        if self._refractory_until and time.time() < self._refractory_until:
            target -= self.config.esgt_refractory_arousal_drop

        # Clamp to limits
        target = np.clip(target, self.config.min_arousal, self.config.max_arousal)

        # Smooth transition toward target
        current = self._current_state.arousal

        if target > current:
            # Increasing - use increase rate
            delta = self.config.arousal_increase_rate * dt
            new_arousal = min(current + delta, target)
        else:
            # Decreasing - use decrease rate (slower)
            delta = self.config.arousal_decrease_rate * dt
            new_arousal = max(current - delta, target)

        # FASE VII: Apply rate limiting (HARD LIMIT)
        new_arousal = self.rate_limiter.limit(new_arousal, time.time())

        # FASE VII: Enforce hard bounds [0.0, 1.0] (HARD LIMIT)
        new_arousal = ArousalBoundEnforcer.enforce(new_arousal)

        # FASE VII: Track arousal history for oscillation detection
        self.arousal_history.append(new_arousal)

        # FASE VII: Detect saturation (arousal stuck at 0.0 or 1.0)
        self._detect_saturation(new_arousal)

        # FASE VII: Detect oscillation (arousal variance too high)
        self._detect_oscillation()

        # Update state
        self._current_state.arousal = new_arousal
        self._current_state.level = self._classify_arousal(new_arousal)
        self._current_state.need_contribution = need_contrib
        self._current_state.external_contribution = external_contrib
        self._current_state.temporal_contribution = temporal_contrib
        self._current_state.circadian_contribution = circadian_contrib
        self._current_state.esgt_salience_threshold = self._current_state.compute_effective_threshold()
        self._current_state.timestamp = time.time()

        # Track level transitions
        if self._current_state.level != self._last_level:
            self._level_transition_time = time.time()
            self._last_level = self._current_state.level
        else:
            self._current_state.time_in_current_level_seconds = time.time() - self._level_transition_time

        # Invoke callbacks
        await self._invoke_callbacks()

    def _compute_external_contribution(self) -> float:
        """Compute arousal contribution from external modulations."""
        # Remove expired modulations
        self._active_modulations = [m for m in self._active_modulations if not m.is_expired()]

        if not self._active_modulations:
            return 0.0

        # Sum all active modulations (weighted by priority)
        total = 0.0
        total_priority = 0

        for mod in self._active_modulations:
            delta = mod.get_current_delta()
            total += delta * mod.priority
            total_priority += mod.priority

        if total_priority > 0:
            return total / total_priority
        else:
            return 0.0

    def _compute_temporal_contribution(self, dt: float) -> float:
        """Compute arousal contribution from stress buildup/recovery."""
        current_arousal = self._current_state.arousal

        # High arousal (>0.7) builds stress
        if current_arousal > 0.7:
            self._accumulated_stress += self.config.stress_buildup_rate * dt
        # Low arousal (<0.5) recovers stress
        elif current_arousal < 0.5:
            self._accumulated_stress -= self.config.stress_recovery_rate * dt

        # Clamp stress
        self._accumulated_stress = np.clip(self._accumulated_stress, 0.0, 1.0)

        # Stress contributes positively to arousal (stress → hyperarousal)
        return self._accumulated_stress * 0.2  # Up to +0.2 arousal from stress

    def _compute_circadian_contribution(self) -> float:
        """Compute circadian rhythm contribution (optional)."""
        if not self.config.enable_circadian:
            return 0.0

        # Simple sinusoidal circadian (peak at noon, trough at midnight)
        hour = time.localtime().tm_hour
        phase = (hour / 24.0) * 2 * np.pi  # 0 to 2π over 24 hours
        return self.config.circadian_amplitude * np.sin(phase - np.pi / 2)

    def _classify_arousal(self, arousal: float) -> ArousalLevel:
        """
        Classify arousal level.

        Boundaries are inclusive on upper bound:
        - [0.0, 0.2] → SLEEP
        - (0.2, 0.4] → DROWSY
        - (0.4, 0.6] → RELAXED
        - (0.6, 0.8] → ALERT
        - (0.8, 1.0] → HYPERALERT
        """
        if arousal <= 0.2:
            return ArousalLevel.SLEEP
        elif arousal <= 0.4:
            return ArousalLevel.DROWSY
        elif arousal <= 0.6:
            return ArousalLevel.RELAXED
        elif arousal <= 0.8:
            return ArousalLevel.ALERT
        else:
            return ArousalLevel.HYPERALERT

    async def _invoke_callbacks(self) -> None:
        """Invoke registered callbacks with current state."""
        for callback in self._arousal_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._current_state)
                else:
                    callback(self._current_state)
            except Exception as e:
                print(f"⚠️  Arousal callback error: {e}")

    # Public API

    def get_current_arousal(self) -> ArousalState:
        """Get current arousal state."""
        return self._current_state

    def get_esgt_threshold(self) -> float:
        """Get current effective ESGT salience threshold."""
        return self._current_state.esgt_salience_threshold

    def request_modulation(self, source: str, delta: float, duration_seconds: float = 0.0, priority: int = 1) -> None:
        """
        Request arousal modulation from external source.

        Args:
            source: Name of requesting system
            delta: Change in arousal (-1.0 to +1.0)
            duration_seconds: How long effect lasts (0 = instant)
            priority: Priority (higher overrides lower)
        """
        modulation = ArousalModulation(source=source, delta=delta, duration_seconds=duration_seconds, priority=priority)

        self._active_modulations.append(modulation)
        self.total_modulations += 1

    def update_from_needs(self, needs: AbstractNeeds) -> None:
        """
        Update arousal based on internal needs.

        Should be called regularly with current needs from MMEI.

        Args:
            needs: Current AbstractNeeds
        """
        # FASE VII: Validate AbstractNeeds input
        if not self._validate_needs(needs):
            self.invalid_needs_count += 1
            return  # Skip invalid needs

        contribution = (
            self.config.repair_need_weight * needs.repair_need
            + self.config.rest_need_weight * needs.rest_need
            + self.config.efficiency_need_weight * needs.efficiency_need
            + self.config.connectivity_need_weight * needs.connectivity_need
        )

        self._current_state.need_contribution = contribution

    def apply_esgt_refractory(self) -> None:
        """
        Apply refractory period after ESGT event.

        Temporarily reduces arousal to prevent rapid re-ignition.
        """
        self._refractory_until = time.time() + self.config.esgt_refractory_duration_seconds
        self.esgt_refractories_applied += 1

    def get_stress_level(self) -> float:
        """Get current accumulated stress (0.0 - 1.0)."""
        return self._accumulated_stress

    def reset_stress(self) -> None:
        """Manually reset accumulated stress."""
        self._accumulated_stress = 0.0

    def get_statistics(self) -> Dict[str, any]:
        """Get controller statistics."""
        return {
            "controller_id": self.controller_id,
            "running": self._running,
            "current_arousal": self._current_state.arousal,
            "current_level": self._current_state.level.value,
            "esgt_threshold": self._current_state.esgt_salience_threshold,
            "accumulated_stress": self._accumulated_stress,
            "active_modulations": len(self._active_modulations),
            "total_updates": self.total_updates,
            "total_modulations": self.total_modulations,
            "esgt_refractories": self.esgt_refractories_applied,
        }

    # ========================================================================
    # FASE VII (Safety Hardening): Validation & Anomaly Detection
    # ========================================================================

    def _validate_needs(self, needs: AbstractNeeds) -> bool:
        """
        Validate AbstractNeeds input.

        Checks that all need values are in valid range [0.0, 1.0].

        Args:
            needs: AbstractNeeds to validate

        Returns:
            True if valid, False otherwise
        """
        if needs is None:
            return False

        # Check all need values are in [0.0, 1.0]
        need_values = [
            needs.rest_need,
            needs.repair_need,
            needs.efficiency_need,
            needs.connectivity_need,
            needs.curiosity_drive,
            needs.learning_drive,
        ]

        for value in need_values:
            if not isinstance(value, (int, float)):
                return False
            if value < 0.0 or value > 1.0:
                return False

        return True

    def _detect_saturation(self, arousal: float) -> None:
        """
        Detect arousal saturation (stuck at 0.0 or 1.0).

        Saturation indicates loss of dynamic range - arousal can't adapt.
        This is a pathological state that should be monitored.

        Args:
            arousal: Current arousal value
        """
        # Check if at boundary
        at_boundary = arousal <= 0.01 or arousal >= 0.99

        if at_boundary:
            if self.arousal_saturation_start is None:
                # Start tracking saturation
                self.arousal_saturation_start = time.time()
            else:
                # Check duration
                duration = time.time() - self.arousal_saturation_start
                if duration >= AROUSAL_SATURATION_THRESHOLD_SECONDS:
                    # Saturation event
                    self.saturation_events += 1
                    print(f"⚠️  MCEA SATURATION: Arousal stuck at {arousal:.2f} for {duration:.1f}s")
                    # Reset to avoid repeated alerts
                    self.arousal_saturation_start = time.time()
        else:
            # Not at boundary, reset
            self.arousal_saturation_start = None

    def _detect_oscillation(self) -> None:
        """
        Detect arousal oscillation (high variance).

        Oscillation indicates instability - arousal is fluctuating rapidly
        instead of smoothly tracking needs. This suggests tuning issues
        or external interference.
        """
        if len(self.arousal_history) < AROUSAL_OSCILLATION_WINDOW:
            return  # Not enough data

        # Compute standard deviation
        stddev = float(np.std(self.arousal_history))

        # Check threshold
        if stddev > AROUSAL_OSCILLATION_THRESHOLD:
            self.oscillation_events += 1
            print(f"⚠️  MCEA OSCILLATION: Arousal variance = {stddev:.3f} (threshold={AROUSAL_OSCILLATION_THRESHOLD})")

    def get_health_metrics(self) -> Dict[str, any]:
        """
        Get MCEA health metrics for Safety Core integration.

        Returns metrics about arousal state, anomalies (saturation, oscillation),
        and input validation. Used by Safety Core for monitoring.

        Returns:
            Dict with health metrics
        """
        # Compute current arousal variance
        arousal_variance = float(np.std(self.arousal_history)) if len(self.arousal_history) >= 2 else 0.0

        # Check if currently saturated
        is_saturated = False
        if self.arousal_saturation_start:
            saturation_duration = time.time() - self.arousal_saturation_start
            is_saturated = saturation_duration >= AROUSAL_SATURATION_THRESHOLD_SECONDS

        return {
            "controller_id": self.controller_id,
            "running": self._running,
            # Current state
            "current_arousal": self._current_state.arousal,
            "current_level": self._current_state.level.value,
            "esgt_threshold": self._current_state.esgt_salience_threshold,
            "accumulated_stress": self._accumulated_stress,
            # Update metrics
            "total_updates": self.total_updates,
            "total_modulations": self.total_modulations,
            "esgt_refractories": self.esgt_refractories_applied,
            # Safety metrics
            "saturation_events": self.saturation_events,
            "oscillation_events": self.oscillation_events,
            "invalid_needs_count": self.invalid_needs_count,
            "is_saturated": is_saturated,
            "arousal_variance": arousal_variance,
            "arousal_history_size": len(self.arousal_history),
        }

    def __repr__(self) -> str:
        return (
            f"ArousalController({self.controller_id}, "
            f"arousal={self._current_state.arousal:.2f}, "
            f"level={self._current_state.level.value})"
        )
