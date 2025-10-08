"""
Neuromodulation Coordinator - Production-Hardened with Conflict Resolution

Biological Inspiration:
- Multiple neuromodulators interact NON-LINEARLY in biological brains
- Antagonistic interactions: Dopamine ↔ Serotonin (reward vs. impulse control)
- Synergistic interactions: Acetylcholine + Norepinephrine (attention + arousal)
- Homeostatic balance: System prevents dominance by single modulator

Functional Role in MAXIMUS:
- Coordinate modulations across 4 neuromodulators (DA, 5HT, ACh, NE)
- Detect and resolve conflicting modulation requests
- Apply non-linear interaction weights (antagonism, synergy)
- Aggregate metrics for Safety Core monitoring
- Emergency shutdown coordination

Safety Features (CRITICAL):
- Conflict detection: Detects antagonistic modulation patterns
- Conflict resolution: Reduces magnitude of conflicting requests
- Max simultaneous modulations: 3 (prevents overload)
- Aggregate circuit breaker: If ≥3 modulators fail → kill switch
- Bounded output: All final levels guaranteed [0, 1]
- Full observability: Aggregates all modulator metrics

NO MOCK, NO PLACEHOLDER, NO TODO.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from consciousness.neuromodulation.acetylcholine_hardened import AcetylcholineModulator
from consciousness.neuromodulation.dopamine_hardened import DopamineModulator
from consciousness.neuromodulation.modulator_base import NeuromodulatorBase
from consciousness.neuromodulation.norepinephrine_hardened import NorepinephrineModulator
from consciousness.neuromodulation.serotonin_hardened import SerotoninModulator

logger = logging.getLogger(__name__)


@dataclass
class CoordinatorConfig:
    """Configuration for neuromodulation coordination.

    Defines interaction weights and conflict resolution parameters.
    """

    # Antagonistic interactions (negative weight = opposition)
    # DA-5HT: Dopamine (reward-seeking) antagonizes Serotonin (impulse control)
    da_5ht_antagonism: float = -0.3  # DA↑ suppresses 5HT effect, vice versa

    # Synergistic interactions (positive weight = enhancement)
    # ACh-NE: Acetylcholine (attention) + Norepinephrine (arousal) = focused alertness
    ach_ne_synergy: float = 0.2  # ACh↑ + NE↑ = enhanced effect

    # Conflict resolution
    conflict_threshold: float = 0.7  # Conflict score above this triggers resolution
    conflict_reduction_factor: float = 0.5  # Reduce conflicting deltas by this factor

    # Safety limits
    max_simultaneous_modulations: int = 3  # Max modulators modified per coordinate() call


@dataclass
class ModulationRequest:
    """Request to modulate a specific neuromodulator."""

    modulator: str  # "dopamine", "serotonin", "acetylcholine", "norepinephrine"
    delta: float  # Requested change
    source: str  # Source of request (for logging)


class NeuromodulationCoordinator:
    """
    Coordinates modulations across 4 neuromodulators with conflict resolution.

    This coordinator ensures:
    1. **Conflict Detection**: Detects antagonistic modulation patterns (DA↑ + 5HT↑)
    2. **Conflict Resolution**: Reduces magnitude of conflicting requests
    3. **Non-linear Interactions**: Applies DA-5HT antagonism, ACh-NE synergy
    4. **Bounded Behavior**: All modulators guaranteed [0, 1]
    5. **Aggregate Circuit Breaker**: If ≥3 modulators fail → system kill switch
    6. **Full Observability**: Aggregates metrics from all 4 modulators

    Usage:
        coordinator = NeuromodulationCoordinator(kill_switch_callback=safety.kill_switch.trigger)

        # Request modulations
        requests = [
            ModulationRequest("dopamine", delta=0.3, source="reward_signal"),
            ModulationRequest("serotonin", delta=0.1, source="mood_regulation"),
        ]

        # Coordinate (applies conflict resolution + interactions)
        results = coordinator.coordinate_modulation(requests)

        # Get aggregate metrics
        metrics = coordinator.get_health_metrics()

        # Emergency shutdown
        coordinator.emergency_stop()

    Thread Safety: NOT thread-safe. Use external locking if called from multiple threads.
    """

    def __init__(
        self, config: CoordinatorConfig | None = None, kill_switch_callback: Callable[[str], None] | None = None
    ):
        """Initialize neuromodulation coordinator.

        Args:
            config: Coordinator configuration (uses defaults if None)
            kill_switch_callback: Callback for emergency shutdown
        """
        self.config = config or CoordinatorConfig()
        self._kill_switch = kill_switch_callback

        # Initialize all 4 modulators
        self.dopamine = DopamineModulator(kill_switch_callback=kill_switch_callback)
        self.serotonin = SerotoninModulator(kill_switch_callback=kill_switch_callback)
        self.acetylcholine = AcetylcholineModulator(kill_switch_callback=kill_switch_callback)
        self.norepinephrine = NorepinephrineModulator(kill_switch_callback=kill_switch_callback)

        # Modulator lookup
        self._modulators: dict[str, NeuromodulatorBase] = {
            "dopamine": self.dopamine,
            "serotonin": self.serotonin,
            "acetylcholine": self.acetylcholine,
            "norepinephrine": self.norepinephrine,
        }

        # Coordination metrics
        self.total_coordinations = 0
        self.conflicts_detected = 0
        self.conflicts_resolved = 0

        logger.info(
            "NeuromodulationCoordinator initialized with 4 modulators: "
            f"DA (baseline={self.dopamine.config.baseline}), "
            f"5HT (baseline={self.serotonin.config.baseline}), "
            f"ACh (baseline={self.acetylcholine.config.baseline}), "
            f"NE (baseline={self.norepinephrine.config.baseline})"
        )

    def coordinate_modulation(self, requests: list[ModulationRequest]) -> dict[str, float]:
        """
        Coordinate modulations across multiple neuromodulators.

        Applies conflict resolution and non-linear interactions before
        executing modulations.

        Args:
            requests: List of modulation requests

        Returns:
            Dict mapping modulator name → actual change applied

        Raises:
            ValueError: If too many simultaneous modulations requested
            RuntimeError: If aggregate circuit breaker is open
        """
        self.total_coordinations += 1

        # Validate request count
        if len(requests) > self.config.max_simultaneous_modulations:
            error_msg = (
                f"Too many simultaneous modulations: {len(requests)} > max {self.config.max_simultaneous_modulations}"
            )
            logger.error(f"🔴 {error_msg}")
            raise ValueError(error_msg)

        # Check aggregate circuit breaker
        if self._is_aggregate_circuit_breaker_open():
            error_msg = "Aggregate circuit breaker OPEN - ≥3 modulators failed"
            logger.error(f"🔴 {error_msg}")

            if self._kill_switch:
                self._kill_switch("Neuromodulation aggregate circuit breaker open")

            raise RuntimeError(error_msg)

        # Detect conflicts
        conflict_score = self._compute_conflict_score(requests)

        if conflict_score > self.config.conflict_threshold:
            self.conflicts_detected += 1
            logger.warning(
                f"⚠️ Conflict detected (score={conflict_score:.2f} > threshold={self.config.conflict_threshold})"
            )

            # Resolve conflicts
            requests = self._resolve_conflicts(requests)
            self.conflicts_resolved += 1

        # Apply non-linear interactions
        requests = self._apply_interactions(requests)

        # Execute modulations
        results = {}
        for req in requests:
            modulator = self._modulators.get(req.modulator)
            if not modulator:
                logger.error(f"Unknown modulator: {req.modulator}")
                continue

            try:
                actual_change = modulator.modulate(delta=req.delta, source=req.source)
                results[req.modulator] = actual_change

                logger.debug(
                    f"Coordinated modulation: {req.modulator} delta={req.delta:.3f} → actual={actual_change:.3f}"
                )

            except RuntimeError as e:
                # Individual modulator circuit breaker open
                logger.error(f"Modulator {req.modulator} rejected modulation: {e}")
                results[req.modulator] = 0.0

        return results

    def _compute_conflict_score(self, requests: list[ModulationRequest]) -> float:
        """
        Compute conflict score for modulation requests.

        Conflicts occur when antagonistic modulators are both increased:
        - DA↑ + 5HT↑ = conflict (reward-seeking vs. impulse control)

        Returns:
            Conflict score [0, 1] - higher = more conflict
        """
        # Build delta map
        deltas = {req.modulator: req.delta for req in requests}

        da_delta = deltas.get("dopamine", 0.0)
        sht_delta = deltas.get("serotonin", 0.0)

        # Conflict: Both DA and 5HT increase (or both decrease)
        # Score = min(|da_delta|, |5ht_delta|) if same sign
        if da_delta * sht_delta > 0:  # Same sign (both + or both -)
            conflict = min(abs(da_delta), abs(sht_delta))
            return conflict
        return 0.0

    def _resolve_conflicts(self, requests: list[ModulationRequest]) -> list[ModulationRequest]:
        """
        Resolve conflicts by reducing magnitude of conflicting requests.

        Applies conflict_reduction_factor to DA and 5HT deltas.

        Args:
            requests: Original requests

        Returns:
            Modified requests with reduced conflict
        """
        resolved = []

        for req in requests:
            if req.modulator in ("dopamine", "serotonin"):
                # Reduce magnitude
                new_delta = req.delta * self.config.conflict_reduction_factor

                logger.info(f"Conflict resolution: {req.modulator} delta {req.delta:.3f} → {new_delta:.3f}")

                resolved.append(
                    ModulationRequest(
                        modulator=req.modulator, delta=new_delta, source=f"{req.source}_conflict_resolved"
                    )
                )
            else:
                resolved.append(req)

        return resolved

    def _apply_interactions(self, requests: list[ModulationRequest]) -> list[ModulationRequest]:
        """
        Apply non-linear interactions between neuromodulators.

        Interactions:
        1. DA-5HT Antagonism: DA↑ suppresses 5HT effect (and vice versa)
        2. ACh-NE Synergy: ACh↑ + NE↑ = enhanced effect

        Args:
            requests: Requests after conflict resolution

        Returns:
            Requests with interaction weights applied
        """
        # Build delta map
        deltas = {req.modulator: req.delta for req in requests}

        da_delta = deltas.get("dopamine", 0.0)
        sht_delta = deltas.get("serotonin", 0.0)
        ach_delta = deltas.get("acetylcholine", 0.0)
        ne_delta = deltas.get("norepinephrine", 0.0)

        # Apply DA-5HT antagonism (only if opposite directions)
        if da_delta * sht_delta < 0:  # Opposite signs
            # DA increase suppresses 5HT decrease (and vice versa)
            da_suppression = abs(sht_delta) * self.config.da_5ht_antagonism
            sht_suppression = abs(da_delta) * self.config.da_5ht_antagonism

            deltas["dopamine"] = da_delta + da_suppression
            deltas["serotonin"] = sht_delta + sht_suppression

            logger.debug(
                f"DA-5HT antagonism applied: DA {da_delta:.3f}→{deltas['dopamine']:.3f}, "
                f"5HT {sht_delta:.3f}→{deltas['serotonin']:.3f}"
            )

        # Apply ACh-NE synergy (only if both increase)
        if ach_delta > 0 and ne_delta > 0:
            # Synergy: both effects enhanced
            ach_boost = ne_delta * self.config.ach_ne_synergy
            ne_boost = ach_delta * self.config.ach_ne_synergy

            deltas["acetylcholine"] = ach_delta + ach_boost
            deltas["norepinephrine"] = ne_delta + ne_boost

            logger.debug(
                f"ACh-NE synergy applied: ACh {ach_delta:.3f}→{deltas['acetylcholine']:.3f}, "
                f"NE {ne_delta:.3f}→{deltas['norepinephrine']:.3f}"
            )

        # Rebuild requests with updated deltas
        modified = []
        for req in requests:
            modified.append(
                ModulationRequest(
                    modulator=req.modulator, delta=deltas[req.modulator], source=f"{req.source}_interacted"
                )
            )

        return modified

    def _is_aggregate_circuit_breaker_open(self) -> bool:
        """
        Check if aggregate circuit breaker should be open.

        Opens if ≥3 modulators have circuit breakers open.

        Returns:
            True if aggregate breaker should be open
        """
        open_count = sum(1 for mod in self._modulators.values() if mod._circuit_breaker_open)

        return open_count >= 3

    def get_levels(self) -> dict[str, float]:
        """
        Get current levels of all 4 neuromodulators.

        Returns:
            Dict mapping modulator name → current level [0, 1]
        """
        return {
            "dopamine": self.dopamine.level,
            "serotonin": self.serotonin.level,
            "acetylcholine": self.acetylcholine.level,
            "norepinephrine": self.norepinephrine.level,
        }

    def get_health_metrics(self) -> dict:
        """
        Export aggregate health metrics for Safety Core monitoring.

        Aggregates metrics from all 4 modulators + coordination metrics.

        Returns:
            Dictionary with all metrics
        """
        # Aggregate individual modulator metrics
        metrics = {}

        for name, modulator in self._modulators.items():
            metrics.update(modulator.get_health_metrics())

        # Add coordination-specific metrics
        metrics.update(
            {
                "neuromod_total_coordinations": self.total_coordinations,
                "neuromod_conflicts_detected": self.conflicts_detected,
                "neuromod_conflicts_resolved": self.conflicts_resolved,
                "neuromod_conflict_rate": (self.conflicts_detected / max(1, self.total_coordinations)),
                "neuromod_aggregate_circuit_breaker_open": self._is_aggregate_circuit_breaker_open(),
            }
        )

        return metrics

    def emergency_stop(self):
        """
        Emergency stop - shutdown all modulators immediately.

        Called by Safety Core during system-wide shutdown.
        """
        logger.critical("🔴 NeuromodulationCoordinator emergency stop triggered")

        for name, modulator in self._modulators.items():
            modulator.emergency_stop()
            logger.info(f"  ✓ {name.capitalize()} modulator stopped")

    def __repr__(self) -> str:
        """String representation for debugging."""
        levels = self.get_levels()
        breaker_open = self._is_aggregate_circuit_breaker_open()

        return (
            f"NeuromodulationCoordinator("
            f"DA={levels['dopamine']:.3f}, "
            f"5HT={levels['serotonin']:.3f}, "
            f"ACh={levels['acetylcholine']:.3f}, "
            f"NE={levels['norepinephrine']:.3f}, "
            f"aggregate_breaker={'OPEN' if breaker_open else 'CLOSED'})"
        )
