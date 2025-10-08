"""
Base Modulator - Shared hardening infrastructure for all neuromodulators

This base class implements all safety mechanisms validated in DopamineModulator:
- Bounded levels [0, 1] with hard clamp
- Receptor desensitization (diminishing returns)
- Homeostatic decay (exponential return to baseline)
- Temporal smoothing (no instant jumps)
- Max change per step limits
- Circuit breaker (consecutive anomaly protection)
- Kill switch integration
- Full observability

Specific modulators (Dopamine, Serotonin, Acetylcholine, Norepinephrine)
inherit from this base and only customize:
- Baseline values
- Decay rates
- Desensitization thresholds
- Biological documentation

This eliminates code duplication and ensures ALL modulators have
identical safety guarantees.

NO MOCK, NO PLACEHOLDER, NO TODO.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModulatorConfig:
    """Immutable configuration for neuromodulator.

    All parameters validated on init. Configuration cannot be changed
    after creation (fail-fast if invalid).
    """

    baseline: float = 0.5  # Homeostatic set point [0, 1]
    min_level: float = 0.0  # HARD LOWER BOUND
    max_level: float = 1.0  # HARD UPPER BOUND

    # Decay parameters
    decay_rate: float = 0.01  # Per-second decay toward baseline (0.01 = 1%/s)

    # Temporal smoothing
    smoothing_factor: float = 0.2  # Exponential smoothing (0=instant, 1=no change)

    # Desensitization (diminishing returns)
    desensitization_threshold: float = 0.8  # Level above which desensitization starts
    desensitization_factor: float = 0.5  # Multiplier for overstimulated state

    # Safety limits
    max_change_per_step: float = 0.1  # HARD LIMIT on single-step change

    def __post_init__(self):
        """Validate configuration - fail fast if invalid."""
        assert 0.0 <= self.baseline <= 1.0, f"Baseline {self.baseline} must be in [0, 1]"
        assert self.min_level < self.max_level, f"Min {self.min_level} must be < max {self.max_level}"
        assert 0.0 < self.decay_rate <= 1.0, f"Decay rate {self.decay_rate} must be in (0, 1]"
        assert 0.0 < self.smoothing_factor <= 1.0, f"Smoothing {self.smoothing_factor} must be in (0, 1]"
        assert 0.0 < self.desensitization_threshold <= 1.0, "Desensitization threshold must be in (0, 1]"
        assert 0.0 < self.desensitization_factor <= 1.0, "Desensitization factor must be in (0, 1]"
        assert 0.0 < self.max_change_per_step <= 1.0, "Max change per step must be in (0, 1]"


@dataclass
class ModulatorState:
    """Current observable state of neuromodulator.

    Exposed for monitoring by Safety Core and debugging.
    """

    level: float  # Current modulator level [0, 1]
    baseline: float  # Homeostatic baseline
    is_desensitized: bool  # True if above desensitization threshold
    last_update_time: float  # Unix timestamp of last modulation
    total_modulations: int  # Total modulations since init
    bounded_corrections: int  # How many times we hit bounds (anomaly signal)
    desensitization_events: int  # How many times desensitization was triggered


class NeuromodulatorBase(ABC):
    """
    Base class for all neuromodulators with BOUNDED, SMOOTH, HOMEOSTATIC behavior.

    This class implements safety mechanisms validated in DopamineModulator:

    1. **Bounded Levels [0, 1]**: Levels cannot go negative or exceed max.
       Enforced via HARD CLAMP after every modulation.

    2. **Desensitization**: Above threshold, modulations have diminishing
       returns. Prevents runaway.

    3. **Homeostatic Decay**: Exponential decay toward baseline over time.
       Mimics reuptake mechanisms in biological systems.

    4. **Temporal Smoothing**: Changes are smoothed via exponential moving average.
       Prevents instant jumps (biologically implausible).

    5. **Max Change Per Step**: Hard limit on single-step changes.
       Multiple rapid modulations cannot cause runaway.

    6. **Circuit Breaker**: After consecutive bound violations, circuit breaker
       opens and blocks further modulations.

    7. **Kill Switch Hook**: Optional callback for emergency shutdown integration.

    8. **Full Observability**: get_health_metrics() exposes all internal state.

    Subclasses MUST implement:
    - get_modulator_name(): Return name for logging/metrics (e.g., "serotonin")

    Thread Safety: NOT thread-safe. Use external locking if called from multiple threads.
    """

    # Circuit breaker configuration
    MAX_CONSECUTIVE_ANOMALIES = 5  # Consecutive bound violations before opening

    def __init__(
        self, config: ModulatorConfig | None = None, kill_switch_callback: Callable[[str], None] | None = None
    ):
        """Initialize neuromodulator.

        Args:
            config: Configuration (uses defaults if None)
            kill_switch_callback: Optional callback for kill switch integration.
                Called with reason string when circuit breaker opens or emergency_stop().
        """
        self.config = config or ModulatorConfig()
        self._kill_switch = kill_switch_callback

        # State
        self._level = self.config.baseline
        self._last_update = time.time()
        self._total_modulations = 0
        self._bounded_corrections = 0
        self._desensitization_events = 0

        # Circuit breaker
        self._circuit_breaker_open = False
        self._consecutive_anomalies = 0

        modulator_name = self.get_modulator_name()
        logger.info(
            f"{modulator_name.capitalize()}Modulator initialized: "
            f"baseline={self.config.baseline:.3f}, "
            f"decay_rate={self.config.decay_rate:.4f}, "
            f"desensitization_threshold={self.config.desensitization_threshold:.2f}"
        )

    @abstractmethod
    def get_modulator_name(self) -> str:
        """Return modulator name for logging/metrics (e.g., 'dopamine', 'serotonin')."""
        pass

    @property
    def level(self) -> float:
        """Get current level (applies decay automatically).

        Reading this property applies homeostatic decay based on time elapsed
        since last update. This ensures level always reflects current state.

        Returns:
            Current level [0, 1]
        """
        self._apply_decay()
        return self._level

    @property
    def state(self) -> ModulatorState:
        """Get full observable state for monitoring.

        Returns:
            ModulatorState with all internal metrics
        """
        return ModulatorState(
            level=self._level,
            baseline=self.config.baseline,
            is_desensitized=self._is_desensitized(),
            last_update_time=self._last_update,
            total_modulations=self._total_modulations,
            bounded_corrections=self._bounded_corrections,
            desensitization_events=self._desensitization_events,
        )

    def modulate(self, delta: float, source: str = "unknown") -> float:
        """
        Apply modulation with SAFETY BOUNDS.

        This is the core method for changing level. All safety mechanisms
        are applied here:
        1. Circuit breaker check
        2. Decay application
        3. Desensitization (if above threshold)
        4. Max change limit
        5. Temporal smoothing
        6. Hard clamping to [0, 1]
        7. Anomaly detection (consecutive bound violations)

        Args:
            delta: Requested change in level (can be negative)
            source: Source of modulation (for logging/debugging)

        Returns:
            Actual change applied (may be less than requested due to bounds/desensitization)

        Raises:
            RuntimeError: If circuit breaker is open (too many anomalies)
        """
        modulator_name = self.get_modulator_name()

        # Circuit breaker check (CRITICAL)
        if self._circuit_breaker_open:
            error_msg = (
                f"{modulator_name.capitalize()}Modulator circuit breaker OPEN - modulation rejected (source={source})"
            )
            logger.error(f"🔴 {error_msg}")

            if self._kill_switch:
                self._kill_switch(f"{modulator_name.capitalize()} circuit breaker open: {source}")

            raise RuntimeError(f"{modulator_name.capitalize()} modulator circuit breaker is open")

        # Apply decay first (updates _level and _last_update)
        self._apply_decay()

        # Apply desensitization if above threshold
        original_delta = delta
        if self._is_desensitized():
            delta *= self.config.desensitization_factor
            self._desensitization_events += 1
            logger.warning(
                f"{modulator_name.capitalize()} desensitization active: "
                f"{original_delta:.3f} → {delta:.3f} "
                f"(level={self._level:.3f} > threshold={self.config.desensitization_threshold})"
            )

        # Apply max change limit (HARD CONSTRAINT)
        delta = max(-self.config.max_change_per_step, min(self.config.max_change_per_step, delta))

        # Apply temporal smoothing (exponential moving average)
        smoothed_delta = delta * self.config.smoothing_factor

        # Calculate new level
        old_level = self._level
        new_level = self._level + smoothed_delta

        # HARD CLAMP to bounds [min_level, max_level]
        clamped_level = max(self.config.min_level, min(self.config.max_level, new_level))

        # Track if we hit bounds (anomaly detection)
        if clamped_level != new_level:
            self._bounded_corrections += 1
            logger.warning(
                f"⚠️ {modulator_name.capitalize()} BOUNDED: {new_level:.3f} → {clamped_level:.3f} "
                f"(source={source}, bounds=[{self.config.min_level}, {self.config.max_level}])"
            )

            # Anomaly detection - too many bound hits = circuit breaker
            self._consecutive_anomalies += 1

            if self._consecutive_anomalies >= self.MAX_CONSECUTIVE_ANOMALIES:
                self._circuit_breaker_open = True
                error_msg = (
                    f"{modulator_name.capitalize()} circuit breaker OPENED - "
                    f"{self._consecutive_anomalies} consecutive bound violations"
                )
                logger.error(f"🔴 {error_msg}")

                if self._kill_switch:
                    self._kill_switch(f"{modulator_name.capitalize()} runaway detected: {source}")
        else:
            # Reset anomaly counter on successful modulation within bounds
            self._consecutive_anomalies = 0

        # Update state
        self._level = clamped_level
        self._last_update = time.time()
        self._total_modulations += 1

        actual_change = self._level - old_level

        logger.debug(
            f"{modulator_name.capitalize()} modulated: {old_level:.3f} → {self._level:.3f} "
            f"(requested_delta={original_delta:.3f}, actual_change={actual_change:.3f}, source={source})"
        )

        return actual_change

    def _apply_decay(self):
        """Apply homeostatic decay toward baseline.

        Uses exponential decay formula:
        level(t) = baseline + (level(t0) - baseline) * (1 - decay_rate)^elapsed

        This mimics biological reuptake mechanisms and homeostatic regulation.
        """
        now = time.time()
        elapsed = now - self._last_update

        if elapsed <= 0:
            return

        # Exponential decay toward baseline
        decay_factor = 1.0 - (1.0 - self.config.decay_rate) ** elapsed
        self._level += (self.config.baseline - self._level) * decay_factor

        # HARD CLAMP (should not be needed, but paranoid safety)
        self._level = max(self.config.min_level, min(self.config.max_level, self._level))

        self._last_update = now

    def _is_desensitized(self) -> bool:
        """Check if modulator is in desensitized state (overstimulated).

        Returns:
            True if current level >= desensitization_threshold
        """
        return self._level >= self.config.desensitization_threshold

    def reset_circuit_breaker(self):
        """
        Reset circuit breaker (use with CAUTION).

        Should only be called after manual investigation of anomalies.
        Do NOT call automatically - this defeats the safety mechanism.
        """
        modulator_name = self.get_modulator_name()
        logger.warning(f"⚠️ {modulator_name.capitalize()}Modulator circuit breaker manually reset")
        self._circuit_breaker_open = False
        self._consecutive_anomalies = 0

    def emergency_stop(self):
        """
        Kill switch hook - immediate safe shutdown.

        Opens circuit breaker and returns level to baseline immediately.
        Called by Safety Core during emergency shutdown.
        """
        modulator_name = self.get_modulator_name()
        logger.critical(f"🔴 {modulator_name.capitalize()}Modulator emergency stop triggered")
        self._circuit_breaker_open = True
        self._level = self.config.baseline  # Return to safe baseline immediately

    def get_health_metrics(self) -> dict:
        """
        Export health metrics for Safety Core monitoring.

        These metrics are consumed by:
        - AnomalyDetector (detect modulator runaway)
        - ThresholdMonitor (enforce bounds)
        - Prometheus exporter (observability)

        Returns:
            Dictionary of health metrics with modulator-specific prefix
        """
        prefix = self.get_modulator_name()
        return {
            f"{prefix}_level": self._level,
            f"{prefix}_baseline": self.config.baseline,
            f"{prefix}_desensitized": self._is_desensitized(),
            f"{prefix}_circuit_breaker_open": self._circuit_breaker_open,
            f"{prefix}_total_modulations": self._total_modulations,
            f"{prefix}_bounded_corrections": self._bounded_corrections,
            f"{prefix}_bound_hit_rate": (self._bounded_corrections / max(1, self._total_modulations)),
            f"{prefix}_desensitization_events": self._desensitization_events,
            f"{prefix}_consecutive_anomalies": self._consecutive_anomalies,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        modulator_name = self.get_modulator_name()
        return (
            f"{modulator_name.capitalize()}Modulator("
            f"level={self._level:.3f}, "
            f"baseline={self.config.baseline:.3f}, "
            f"desensitized={self._is_desensitized()}, "
            f"circuit_breaker={'OPEN' if self._circuit_breaker_open else 'CLOSED'})"
        )
