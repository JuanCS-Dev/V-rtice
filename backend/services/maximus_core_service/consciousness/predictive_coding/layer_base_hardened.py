"""
Predictive Coding Layer Base - Production-Hardened with Bounded Behavior

Biological Inspiration:
- Cortical hierarchy processes predictions bottom-up and top-down
- Each layer predicts input from layer below, computes prediction error
- Errors propagate up, predictions propagate down
- Bounded prediction errors prevent runaway feedback loops
- Attention gates limit computational load

Free Energy Principle:
- Minimize prediction error (surprise) across hierarchy
- Bounded errors ensure stable learning
- Timeout protection prevents infinite computation
- Circuit breakers isolate failing layers

Safety Features (CRITICAL):
- HARD CLIP prediction errors to max threshold (prevents explosion)
- Timeout protection (max computation time per prediction)
- Attention gating (max predictions per cycle)
- Circuit breaker (consecutive errors/timeouts → layer isolation)
- Layer isolation (exceptions don't propagate)
- Kill switch integration
- Full observability for Safety Core

This is the BASE CLASS for all 5 predictive coding layers.
Each layer inherits safety features and implements specific prediction logic.

NO MOCK, NO PLACEHOLDER, NO TODO.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import asyncio
import time
import logging
from dataclasses import dataclass
from typing import Optional, Callable, Any, Dict
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LayerConfig:
    """Configuration for predictive coding layer."""

    layer_id: int  # Layer number (1-5)
    input_dim: int  # Input dimensionality
    hidden_dim: int  # Hidden/latent dimensionality

    # Safety limits
    max_prediction_error: float = 10.0  # HARD CLIP for prediction errors
    max_computation_time_ms: float = 100.0  # Timeout per prediction (milliseconds)
    max_predictions_per_cycle: int = 100  # Attention gating

    # Circuit breaker
    max_consecutive_errors: int = 5  # Errors before circuit breaker opens
    max_consecutive_timeouts: int = 3  # Timeouts before circuit breaker opens

    def __post_init__(self):
        """Validate configuration."""
        assert 1 <= self.layer_id <= 5, f"Layer ID {self.layer_id} must be 1-5"
        assert self.input_dim > 0, f"Input dim {self.input_dim} must be > 0"
        assert self.hidden_dim > 0, f"Hidden dim {self.hidden_dim} must be > 0"
        assert self.max_prediction_error > 0, "Max prediction error must be > 0"
        assert self.max_computation_time_ms > 0, "Max computation time must be > 0"
        assert self.max_predictions_per_cycle > 0, "Max predictions per cycle must be > 0"


@dataclass
class LayerState:
    """Observable state of predictive coding layer."""

    layer_id: int
    is_active: bool  # False if circuit breaker open
    total_predictions: int
    total_errors: int
    total_timeouts: int
    bounded_errors: int  # How many times we clipped prediction error
    consecutive_errors: int
    consecutive_timeouts: int
    circuit_breaker_open: bool
    average_prediction_error: float
    average_computation_time_ms: float


class PredictiveCodingLayerBase(ABC):
    """
    Base class for all predictive coding layers with BOUNDED, ISOLATED, OBSERVABLE behavior.

    This class provides:
    1. **Bounded Prediction Errors**: Hard clip to max_prediction_error
    2. **Timeout Protection**: Max computation time per prediction
    3. **Attention Gating**: Max predictions per cycle
    4. **Circuit Breaker**: Isolate layer after consecutive failures
    5. **Layer Isolation**: Exceptions don't propagate up/down
    6. **Kill Switch Integration**: Emergency shutdown
    7. **Full Observability**: Metrics for Safety Core

    Subclasses MUST implement:
    - _predict_impl(input_data): Core prediction logic
    - _compute_error_impl(predicted, actual): Core error computation
    - get_layer_name(): Layer name for logging

    Thread Safety: NOT thread-safe. Use external locking for async/parallel calls.
    """

    def __init__(
        self,
        config: LayerConfig,
        kill_switch_callback: Optional[Callable[[str], None]] = None
    ):
        """Initialize predictive coding layer.

        Args:
            config: Layer configuration
            kill_switch_callback: Optional callback for emergency shutdown
        """
        self.config = config
        self._kill_switch = kill_switch_callback

        # State
        self._is_active = True
        self._total_predictions = 0
        self._total_errors = 0
        self._total_timeouts = 0
        self._bounded_errors = 0  # Track how many times we clipped
        self._consecutive_errors = 0
        self._consecutive_timeouts = 0

        # Circuit breaker
        self._circuit_breaker_open = False

        # Performance tracking
        self._prediction_errors: list = []  # Recent errors for averaging
        self._computation_times: list = []  # Recent times for averaging

        # Prediction cycle counter (for attention gating)
        self._predictions_this_cycle = 0

        layer_name = self.get_layer_name()
        logger.info(
            f"{layer_name} initialized: "
            f"input_dim={config.input_dim}, hidden_dim={config.hidden_dim}, "
            f"max_error={config.max_prediction_error}, "
            f"timeout={config.max_computation_time_ms}ms"
        )

    @abstractmethod
    def get_layer_name(self) -> str:
        """Return layer name for logging (e.g., 'Layer1_Sensory')."""
        pass

    @abstractmethod
    async def _predict_impl(self, input_data: Any) -> Any:
        """
        Core prediction logic (implemented by subclass).

        Args:
            input_data: Input from layer below (or raw input for Layer 1)

        Returns:
            Prediction output
        """
        pass

    @abstractmethod
    def _compute_error_impl(self, predicted: Any, actual: Any) -> float:
        """
        Core error computation logic (implemented by subclass).

        Args:
            predicted: Predicted output
            actual: Actual input

        Returns:
            Prediction error (scalar)
        """
        pass

    async def predict(self, input_data: Any) -> Optional[Any]:
        """
        Make prediction with SAFETY BOUNDS and timeout protection.

        Args:
            input_data: Input from layer below

        Returns:
            Prediction output, or None if layer is inactive/timed out

        Raises:
            RuntimeError: If circuit breaker is open
        """
        layer_name = self.get_layer_name()

        # Circuit breaker check
        if self._circuit_breaker_open:
            error_msg = f"{layer_name} circuit breaker OPEN - prediction rejected"
            logger.error(f"🔴 {error_msg}")

            if self._kill_switch:
                self._kill_switch(f"{layer_name} circuit breaker open")

            raise RuntimeError(f"{layer_name} circuit breaker is open")

        # Attention gating check
        if self._predictions_this_cycle >= self.config.max_predictions_per_cycle:
            logger.warning(
                f"{layer_name} attention gate BLOCKED - "
                f"{self._predictions_this_cycle} predictions this cycle"
            )
            return None

        try:
            # Prediction with timeout protection
            start_time = time.time()

            async with asyncio.timeout(self.config.max_computation_time_ms / 1000.0):
                prediction = await self._predict_impl(input_data)

            computation_time_ms = (time.time() - start_time) * 1000.0

            # Track performance
            self._computation_times.append(computation_time_ms)
            if len(self._computation_times) > 100:
                self._computation_times.pop(0)

            # Update counters
            self._total_predictions += 1
            self._predictions_this_cycle += 1

            # Reset error counters on success
            self._consecutive_errors = 0
            self._consecutive_timeouts = 0

            logger.debug(
                f"{layer_name} prediction: {computation_time_ms:.2f}ms, "
                f"cycle_count={self._predictions_this_cycle}"
            )

            return prediction

        except asyncio.TimeoutError:
            # Timeout - track and potentially open circuit breaker
            self._total_timeouts += 1
            self._consecutive_timeouts += 1

            logger.error(
                f"⚠️ {layer_name} TIMEOUT ({self.config.max_computation_time_ms}ms exceeded) - "
                f"consecutive={self._consecutive_timeouts}"
            )

            if self._consecutive_timeouts >= self.config.max_consecutive_timeouts:
                self._open_circuit_breaker(reason="consecutive_timeouts")

            return None

        except Exception as e:
            # Error - track and potentially open circuit breaker
            self._total_errors += 1
            self._consecutive_errors += 1

            logger.error(
                f"⚠️ {layer_name} ERROR: {e} - consecutive={self._consecutive_errors}"
            )

            if self._consecutive_errors >= self.config.max_consecutive_errors:
                self._open_circuit_breaker(reason="consecutive_errors")

            return None

    def compute_error(self, predicted: Any, actual: Any) -> float:
        """
        Compute prediction error with HARD CLIP to bounds.

        Args:
            predicted: Predicted output
            actual: Actual input

        Returns:
            Clipped prediction error [0, max_prediction_error]
        """
        layer_name = self.get_layer_name()

        try:
            # Compute raw error
            raw_error = self._compute_error_impl(predicted, actual)

            # HARD CLIP to max_prediction_error
            clipped_error = min(self.config.max_prediction_error, abs(raw_error))

            # Track if we clipped
            if abs(raw_error) > self.config.max_prediction_error:
                self._bounded_errors += 1
                logger.warning(
                    f"⚠️ {layer_name} ERROR CLIPPED: {raw_error:.3f} → {clipped_error:.3f}"
                )

            # Track for averaging
            self._prediction_errors.append(clipped_error)
            if len(self._prediction_errors) > 100:
                self._prediction_errors.pop(0)

            return clipped_error

        except Exception as e:
            logger.error(f"⚠️ {layer_name} error computation failed: {e}")
            return self.config.max_prediction_error  # Return max on error

    def reset_cycle(self):
        """Reset attention gate counter (call at start of each hierarchy cycle)."""
        self._predictions_this_cycle = 0

    def _open_circuit_breaker(self, reason: str):
        """Open circuit breaker and trigger kill switch."""
        layer_name = self.get_layer_name()

        self._circuit_breaker_open = True
        self._is_active = False

        logger.critical(f"🔴 {layer_name} CIRCUIT BREAKER OPENED - reason: {reason}")

        if self._kill_switch:
            self._kill_switch(f"{layer_name} circuit breaker: {reason}")

    def emergency_stop(self):
        """Emergency shutdown - open circuit breaker and deactivate layer."""
        layer_name = self.get_layer_name()

        logger.critical(f"🔴 {layer_name} emergency stop triggered")

        self._circuit_breaker_open = True
        self._is_active = False

    def get_state(self) -> LayerState:
        """Get observable layer state."""
        avg_error = (
            sum(self._prediction_errors) / len(self._prediction_errors)
            if self._prediction_errors else 0.0
        )
        avg_time = (
            sum(self._computation_times) / len(self._computation_times)
            if self._computation_times else 0.0
        )

        return LayerState(
            layer_id=self.config.layer_id,
            is_active=self._is_active,
            total_predictions=self._total_predictions,
            total_errors=self._total_errors,
            total_timeouts=self._total_timeouts,
            bounded_errors=self._bounded_errors,
            consecutive_errors=self._consecutive_errors,
            consecutive_timeouts=self._consecutive_timeouts,
            circuit_breaker_open=self._circuit_breaker_open,
            average_prediction_error=avg_error,
            average_computation_time_ms=avg_time
        )

    def get_health_metrics(self) -> Dict[str, Any]:
        """Export health metrics for Safety Core monitoring."""
        layer_name = self.get_layer_name().lower().replace(" ", "_")
        state = self.get_state()

        return {
            f"{layer_name}_is_active": state.is_active,
            f"{layer_name}_circuit_breaker_open": state.circuit_breaker_open,
            f"{layer_name}_total_predictions": state.total_predictions,
            f"{layer_name}_total_errors": state.total_errors,
            f"{layer_name}_total_timeouts": state.total_timeouts,
            f"{layer_name}_bounded_errors": state.bounded_errors,
            f"{layer_name}_error_rate": (
                state.total_errors / max(1, state.total_predictions)
            ),
            f"{layer_name}_timeout_rate": (
                state.total_timeouts / max(1, state.total_predictions)
            ),
            f"{layer_name}_avg_prediction_error": state.average_prediction_error,
            f"{layer_name}_avg_computation_time_ms": state.average_computation_time_ms,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        layer_name = self.get_layer_name()
        state = self.get_state()

        return (
            f"{layer_name}("
            f"active={state.is_active}, "
            f"predictions={state.total_predictions}, "
            f"errors={state.total_errors}, "
            f"avg_error={state.average_prediction_error:.3f}, "
            f"circuit_breaker={'OPEN' if state.circuit_breaker_open else 'CLOSED'})"
        )
