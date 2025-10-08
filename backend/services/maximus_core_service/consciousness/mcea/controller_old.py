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
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np

from consciousness.mmei.monitor import AbstractNeeds


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

    def __repr__(self) -> str:
        return (
            f"ArousalController({self.controller_id}, "
            f"arousal={self._current_state.arousal:.2f}, "
            f"level={self._current_state.level.value})"
        )
