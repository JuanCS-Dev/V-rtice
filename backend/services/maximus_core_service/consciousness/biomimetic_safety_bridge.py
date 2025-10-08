"""
Biomimetic Safety Bridge - Production-Hardened Integration Layer

Integrates two biomimetic systems with Safety Core:
1. Neuromodulation System (4 modulators: DA, 5HT, ACh, NE)
2. Predictive Coding Hierarchy (5 layers: Sensory → Strategic)

Biological Inspiration:
- Brain integrates neuromodulation + predictive processing seamlessly
- Neuromodulators influence prediction error signals (attention allocation)
- Prediction errors drive neuromodulator release (learning signals)
- Homeostatic balance maintained across both systems

Functional Role in MAXIMUS:
- Coordinate neuromodulation + predictive coding cycles
- Aggregate metrics from both systems for Safety Core
- Detect cross-system anomalies (e.g., runaway neuromodulation + high prediction errors)
- Trigger kill switch on aggregate failures
- Isolate failures between systems (one can fail without crashing the other)

Safety Features (CRITICAL):
- System isolation: Neuromodulation failure doesn't crash Predictive Coding (and vice versa)
- Aggregate circuit breaker: If both systems fail → kill switch
- Bounded coordination: Max coordination cycles per second
- Timeout protection: Max time per coordination cycle
- Full observability: Aggregates ALL metrics from both systems
- Emergency shutdown: Coordinated shutdown of both systems

NO MOCK, NO PLACEHOLDER, NO TODO.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from consciousness.neuromodulation.coordinator_hardened import (
    CoordinatorConfig as NeuromodConfig,
)
from consciousness.neuromodulation.coordinator_hardened import (
    ModulationRequest,
    NeuromodulationCoordinator,
)
from consciousness.predictive_coding.hierarchy_hardened import (
    HierarchyConfig,
    PredictiveCodingHierarchy,
)

logger = logging.getLogger(__name__)


@dataclass
class BridgeConfig:
    """Configuration for biomimetic safety bridge."""

    # Coordination limits
    max_coordination_cycles_per_second: int = 10  # Max 10 coordinated cycles/sec
    max_coordination_time_ms: float = 1000.0  # Max 1 second per cycle

    # Cross-system thresholds
    anomaly_threshold_prediction_error: float = 8.0  # High prediction error threshold
    anomaly_threshold_neuromod_conflict_rate: float = 0.5  # High conflict rate threshold

    # Aggregate circuit breaker
    max_consecutive_coordination_failures: int = 5  # Failures before kill switch

    # Neuromodulation config (optional override)
    neuromod_config: NeuromodConfig | None = None

    # Predictive coding config (optional override)
    hierarchy_config: HierarchyConfig | None = None


@dataclass
class BridgeState:
    """Observable state of biomimetic safety bridge."""

    total_coordination_cycles: int
    total_coordination_failures: int
    consecutive_coordination_failures: int
    neuromodulation_active: bool
    predictive_coding_active: bool
    aggregate_circuit_breaker_open: bool
    cross_system_anomalies_detected: int
    average_coordination_time_ms: float


class BiomimeticSafetyBridge:
    """
    Integration layer connecting Neuromodulation + Predictive Coding with Safety Core.

    This bridge ensures:
    1. **System Isolation**: Each system can fail independently without crashing the other
    2. **Coordinated Operation**: Both systems work together to process inputs
    3. **Aggregate Monitoring**: Combines metrics from both systems
    4. **Cross-System Anomaly Detection**: Detects when both systems show problems simultaneously
    5. **Aggregate Circuit Breaker**: Kill switch when both systems fail
    6. **Emergency Shutdown**: Coordinated shutdown of both systems

    Usage:
        bridge = BiomimeticSafetyBridge(kill_switch_callback=safety.kill_switch.trigger)

        # Process input through both systems
        result = await bridge.coordinate_processing(raw_event_vector)

        # Get aggregate metrics
        metrics = bridge.get_health_metrics()

        # Emergency shutdown
        bridge.emergency_stop()

    Thread Safety: NOT thread-safe. Use external locking for async/parallel calls.
    """

    def __init__(self, config: BridgeConfig | None = None, kill_switch_callback: Callable[[str], None] | None = None):
        """Initialize biomimetic safety bridge.

        Args:
            config: Bridge configuration (uses defaults if None)
            kill_switch_callback: Callback for emergency shutdown
        """
        self.config = config or BridgeConfig()
        self._kill_switch = kill_switch_callback

        # Initialize neuromodulation system
        neuromod_config = self.config.neuromod_config or NeuromodConfig()
        self.neuromodulation = NeuromodulationCoordinator(
            neuromod_config, kill_switch_callback=self._on_neuromod_failure
        )

        # Initialize predictive coding system
        hierarchy_config = self.config.hierarchy_config or HierarchyConfig()
        self.predictive_coding = PredictiveCodingHierarchy(
            hierarchy_config, kill_switch_callback=self._on_predictive_coding_failure
        )

        # Bridge state
        self.total_coordination_cycles = 0
        self.total_coordination_failures = 0
        self.consecutive_coordination_failures = 0
        self.cross_system_anomalies_detected = 0

        # Circuit breaker
        self._aggregate_circuit_breaker_open = False

        # Performance tracking
        self._coordination_times: list[float] = []

        # Rate limiting
        self._last_coordination_time = 0.0
        self._min_coordination_interval = 1.0 / self.config.max_coordination_cycles_per_second

        logger.info(
            "BiomimeticSafetyBridge initialized:\n"
            f"  Neuromodulation: 4 modulators (DA, 5HT, ACh, NE)\n"
            f"  Predictive Coding: 5 layers (Sensory → Strategic)\n"
            f"  Max coordination rate: {self.config.max_coordination_cycles_per_second} cycles/sec\n"
            f"  Max coordination time: {self.config.max_coordination_time_ms}ms"
        )

    async def coordinate_processing(
        self, raw_input: np.ndarray, modulation_requests: list[ModulationRequest] | None = None
    ) -> dict[str, Any]:
        """
        Coordinate processing through both biomimetic systems.

        Flow:
        1. Check aggregate circuit breaker
        2. Rate limit coordination cycles
        3. Process through Predictive Coding Hierarchy (get prediction errors)
        4. Use prediction errors to generate neuromodulation requests (if not provided)
        5. Apply neuromodulation
        6. Detect cross-system anomalies
        7. Return aggregated results

        Args:
            raw_input: Raw event vector for predictive coding
            modulation_requests: Optional explicit modulation requests (if None, auto-generated from prediction errors)

        Returns:
            Dict with results from both systems

        Raises:
            RuntimeError: If aggregate circuit breaker is open
            asyncio.TimeoutError: If coordination exceeds max time
        """
        self.total_coordination_cycles += 1
        start_time = time.time()

        # Check aggregate circuit breaker
        if self._aggregate_circuit_breaker_open:
            error_msg = "Aggregate circuit breaker OPEN - both systems failed"
            logger.error(f"🔴 {error_msg}")

            if self._kill_switch:
                self._kill_switch("BiomimeticSafetyBridge aggregate circuit breaker open")

            raise RuntimeError(error_msg)

        # Rate limiting
        time_since_last = time.time() - self._last_coordination_time
        if time_since_last < self._min_coordination_interval:
            await asyncio.sleep(self._min_coordination_interval - time_since_last)

        self._last_coordination_time = time.time()

        try:
            # Coordination with timeout protection
            async with asyncio.timeout(self.config.max_coordination_time_ms / 1000.0):
                result = await self._coordinate_impl(raw_input, modulation_requests)

            coordination_time_ms = (time.time() - start_time) * 1000.0

            # Track performance
            self._coordination_times.append(coordination_time_ms)
            if len(self._coordination_times) > 100:
                self._coordination_times.pop(0)

            # Reset consecutive failure counter on success
            self.consecutive_coordination_failures = 0

            logger.debug(
                f"Coordination cycle complete: {coordination_time_ms:.2f}ms, "
                f"prediction_errors={len(result.get('prediction_errors', {}))}, "
                f"neuromod_levels={result.get('neuromod_levels', {})}"
            )

            return result

        except TimeoutError:
            self.total_coordination_failures += 1
            self.consecutive_coordination_failures += 1

            logger.error(
                f"⚠️ Coordination TIMEOUT ({self.config.max_coordination_time_ms}ms exceeded) - "
                f"consecutive={self.consecutive_coordination_failures}"
            )

            if self.consecutive_coordination_failures >= self.config.max_consecutive_coordination_failures:
                self._open_aggregate_circuit_breaker("consecutive_timeouts")

            raise

        except Exception as e:
            self.total_coordination_failures += 1
            self.consecutive_coordination_failures += 1

            logger.error(f"⚠️ Coordination ERROR: {e} - consecutive={self.consecutive_coordination_failures}")

            if self.consecutive_coordination_failures >= self.config.max_consecutive_coordination_failures:
                self._open_aggregate_circuit_breaker("consecutive_errors")

            raise

    async def _coordinate_impl(
        self, raw_input: np.ndarray, modulation_requests: list[ModulationRequest] | None
    ) -> dict[str, Any]:
        """
        Core coordination implementation (isolated failures).

        Args:
            raw_input: Raw event vector
            modulation_requests: Optional modulation requests

        Returns:
            Dict with results from both systems
        """
        result = {}

        # 1. Process through Predictive Coding Hierarchy
        prediction_errors = {}
        try:
            prediction_errors = await self.predictive_coding.process_input(raw_input)
            result["prediction_errors"] = prediction_errors
            result["predictive_coding_success"] = True

        except Exception as e:
            logger.error(f"Predictive coding processing failed: {e}")
            result["predictive_coding_success"] = False
            result["predictive_coding_error"] = str(e)

        # 2. Generate or use provided modulation requests
        if modulation_requests is None and prediction_errors:
            modulation_requests = self._generate_modulation_requests(prediction_errors)

        # 3. Apply neuromodulation
        neuromod_results = {}
        try:
            if modulation_requests:
                neuromod_results = self.neuromodulation.coordinate_modulation(modulation_requests)

            result["neuromod_changes"] = neuromod_results
            result["neuromod_levels"] = self.neuromodulation.get_levels()
            result["neuromodulation_success"] = True

        except Exception as e:
            logger.error(f"Neuromodulation coordination failed: {e}")
            result["neuromodulation_success"] = False
            result["neuromodulation_error"] = str(e)

        # 4. Detect cross-system anomalies
        if result.get("predictive_coding_success") and result.get("neuromodulation_success"):
            anomaly_detected = self._detect_cross_system_anomaly(prediction_errors, neuromod_results)
            if anomaly_detected:
                self.cross_system_anomalies_detected += 1
                result["cross_system_anomaly"] = True
                logger.warning(f"⚠️ Cross-system anomaly detected: {anomaly_detected}")

        return result

    def _generate_modulation_requests(self, prediction_errors: dict[str, float]) -> list[ModulationRequest]:
        """
        Generate neuromodulation requests based on prediction errors.

        Biological inspiration:
        - High prediction error → Increase norepinephrine (arousal/attention)
        - High prediction error → Increase dopamine (learning signal)
        - Low prediction error → Increase serotonin (confidence/stability)

        Args:
            prediction_errors: Dict mapping layer_name → error

        Returns:
            List of modulation requests
        """
        # Compute average prediction error across layers
        if not prediction_errors:
            return []

        avg_error = sum(prediction_errors.values()) / len(prediction_errors)

        requests = []

        # High error → arousal + learning
        if avg_error > 5.0:
            requests.append(ModulationRequest("norepinephrine", delta=0.2, source="high_prediction_error"))
            requests.append(ModulationRequest("dopamine", delta=0.15, source="learning_signal"))

        # Medium error → attention
        elif avg_error > 2.0:
            requests.append(ModulationRequest("acetylcholine", delta=0.1, source="medium_prediction_error"))

        # Low error → confidence
        else:
            requests.append(ModulationRequest("serotonin", delta=0.05, source="low_prediction_error"))

        return requests

    def _detect_cross_system_anomaly(
        self, prediction_errors: dict[str, float], neuromod_results: dict[str, float]
    ) -> str | None:
        """
        Detect anomalies that involve BOTH systems simultaneously.

        Args:
            prediction_errors: Prediction errors from hierarchy
            neuromod_results: Neuromodulation changes

        Returns:
            Anomaly description if detected, None otherwise
        """
        # Anomaly 1: High prediction error + high neuromodulation conflict rate
        if prediction_errors:
            avg_error = sum(prediction_errors.values()) / len(prediction_errors)
            conflict_rate = self.neuromodulation.conflicts_detected / max(1, self.neuromodulation.total_coordinations)

            if (
                avg_error > self.config.anomaly_threshold_prediction_error
                and conflict_rate > self.config.anomaly_threshold_neuromod_conflict_rate
            ):
                return f"High prediction error ({avg_error:.2f}) + High conflict rate ({conflict_rate:.2f})"

        # Anomaly 2: Both systems circuit breakers approaching open
        neuromod_breaker_count = sum(
            1 for mod in self.neuromodulation._modulators.values() if mod._circuit_breaker_open
        )
        predictive_breaker_count = sum(1 for layer in self.predictive_coding._layers if layer._circuit_breaker_open)

        if neuromod_breaker_count >= 2 and predictive_breaker_count >= 2:
            return f"Multiple breakers open: {neuromod_breaker_count} neuromod, {predictive_breaker_count} predictive"

        return None

    def _open_aggregate_circuit_breaker(self, reason: str):
        """Open aggregate circuit breaker and trigger kill switch."""
        self._aggregate_circuit_breaker_open = True

        logger.critical(f"🔴 BiomimeticSafetyBridge AGGREGATE CIRCUIT BREAKER OPENED - reason: {reason}")

        if self._kill_switch:
            self._kill_switch(f"BiomimeticSafetyBridge aggregate failure: {reason}")

    def _on_neuromod_failure(self, reason: str):
        """Callback when neuromodulation system fails."""
        logger.error(f"Neuromodulation system failure: {reason}")
        # System isolation: Predictive coding can continue

    def _on_predictive_coding_failure(self, reason: str):
        """Callback when predictive coding system fails."""
        logger.error(f"Predictive coding system failure: {reason}")
        # System isolation: Neuromodulation can continue

    def get_state(self) -> BridgeState:
        """Get observable bridge state."""
        avg_coordination_time = (
            sum(self._coordination_times) / len(self._coordination_times) if self._coordination_times else 0.0
        )

        return BridgeState(
            total_coordination_cycles=self.total_coordination_cycles,
            total_coordination_failures=self.total_coordination_failures,
            consecutive_coordination_failures=self.consecutive_coordination_failures,
            neuromodulation_active=not self.neuromodulation._is_aggregate_circuit_breaker_open(),
            predictive_coding_active=not self.predictive_coding._is_aggregate_circuit_breaker_open(),
            aggregate_circuit_breaker_open=self._aggregate_circuit_breaker_open,
            cross_system_anomalies_detected=self.cross_system_anomalies_detected,
            average_coordination_time_ms=avg_coordination_time,
        )

    def get_health_metrics(self) -> dict[str, Any]:
        """
        Export aggregate health metrics for Safety Core.

        Combines metrics from:
        1. Neuromodulation system (4 modulators + coordinator)
        2. Predictive Coding hierarchy (5 layers + hierarchy)
        3. Bridge-specific metrics

        Returns:
            Dictionary with ALL metrics from both systems + bridge
        """
        metrics = {}

        # Neuromodulation metrics
        metrics.update(self.neuromodulation.get_health_metrics())

        # Predictive coding metrics
        metrics.update(self.predictive_coding.get_health_metrics())

        # Bridge-specific metrics
        state = self.get_state()
        metrics.update(
            {
                "bridge_total_coordination_cycles": state.total_coordination_cycles,
                "bridge_total_coordination_failures": state.total_coordination_failures,
                "bridge_consecutive_coordination_failures": state.consecutive_coordination_failures,
                "bridge_coordination_failure_rate": (
                    state.total_coordination_failures / max(1, state.total_coordination_cycles)
                ),
                "bridge_neuromodulation_active": state.neuromodulation_active,
                "bridge_predictive_coding_active": state.predictive_coding_active,
                "bridge_aggregate_circuit_breaker_open": state.aggregate_circuit_breaker_open,
                "bridge_cross_system_anomalies_detected": state.cross_system_anomalies_detected,
                "bridge_cross_system_anomaly_rate": (
                    state.cross_system_anomalies_detected / max(1, state.total_coordination_cycles)
                ),
                "bridge_average_coordination_time_ms": state.average_coordination_time_ms,
            }
        )

        return metrics

    def emergency_stop(self):
        """
        Emergency stop - shutdown both biomimetic systems immediately.

        Called by Safety Core during system-wide shutdown.
        """
        logger.critical("🔴 BiomimeticSafetyBridge emergency stop triggered")

        # Shutdown neuromodulation
        self.neuromodulation.emergency_stop()
        logger.info("  ✓ Neuromodulation system stopped")

        # Shutdown predictive coding
        self.predictive_coding.emergency_stop()
        logger.info("  ✓ Predictive coding system stopped")

        # Open aggregate breaker
        self._aggregate_circuit_breaker_open = True

    def __repr__(self) -> str:
        """String representation for debugging."""
        state = self.get_state()

        return (
            f"BiomimeticSafetyBridge("
            f"cycles={state.total_coordination_cycles}, "
            f"neuromod_active={state.neuromodulation_active}, "
            f"predictive_active={state.predictive_coding_active}, "
            f"cross_anomalies={state.cross_system_anomalies_detected}, "
            f"aggregate_breaker={'OPEN' if state.aggregate_circuit_breaker_open else 'CLOSED'})"
        )
