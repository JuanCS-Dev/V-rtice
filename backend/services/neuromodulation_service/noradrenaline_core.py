"""Neuromodulation Service - Production-Ready Norepinephrine Module

Bio-inspired norepinephrine modulator that implements:
1. **Urgency Computation**
   - Combines threat severity and time pressure
   - Models fight-or-flight response
   - Drives rapid decision-making

2. **Temperature Modulation**
   - Adjusts policy softmax temperature
   - High urgency → Low temperature (decisive)
   - Low urgency → High temperature (exploratory)

3. **Policy Softmax Adjustment**
   - Real-time policy distribution shaping
   - Integration with RL policies
   - Adaptive decision boldness

Like biological norepinephrine: Modulates arousal and urgency-driven behavior.
NO MOCKS - Production-ready implementation.
"""

import logging
import math
from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class NoradrenalineCore:
    """Production-ready Noradrenaline module for urgency and temperature control.

    Modulates policy temperature based on urgency:
    - High urgency → Low temperature (focused, decisive)
    - Low urgency → High temperature (broad, exploratory)
    """

    def __init__(
        self,
        base_temperature: float = 1.0,
        min_temperature: float = 0.1,
        max_temperature: float = 2.0,
        urgency_window_size: int = 50,
    ):
        """Initialize Noradrenaline Core.

        Args:
            base_temperature: Base softmax temperature
            min_temperature: Minimum temperature
            max_temperature: Maximum temperature
            urgency_window_size: Window size for urgency history
        """
        self.base_temperature = base_temperature
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature

        self.current_temperature = base_temperature
        self.current_urgency = 0.0
        self.urgency_history: deque = deque(maxlen=urgency_window_size)

        self.last_modulation_time: Optional[datetime] = None
        self.modulation_count = 0

        logger.info(
            f"NoradrenalineCore initialized (base_temp={base_temperature}, "
            f"range=[{min_temperature}, {max_temperature}])"
        )

    def compute_urgency(self, threat_severity: float, time_pressure: float, stakes: float = 0.5) -> float:
        """Compute urgency signal from threat and time pressure.

        Urgency = f(severity, time_pressure, stakes)

        Args:
            threat_severity: Threat severity (0-1)
            time_pressure: Time pressure (0=relaxed, 1=immediate)
            stakes: Outcome importance (0-1)

        Returns:
            Urgency level (0-1)
        """
        # Combine factors (weighted average)
        urgency = 0.4 * threat_severity + 0.4 * time_pressure + 0.2 * stakes

        urgency = max(0.0, min(1.0, urgency))

        # Store in history
        self.urgency_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "urgency": urgency,
                "threat_severity": threat_severity,
                "time_pressure": time_pressure,
                "stakes": stakes,
            }
        )

        self.current_urgency = urgency

        logger.debug(
            f"Urgency computed: {urgency:.3f} (severity={threat_severity:.2f}, "
            f"time={time_pressure:.2f}, stakes={stakes:.2f})"
        )

        return urgency

    def modulate_temperature(self, urgency: Optional[float] = None, confidence: float = 0.5) -> float:
        """Modulate policy temperature based on urgency.

        Strategy:
        - High urgency → Low temperature (exploit best action)
        - Low urgency → High temperature (explore options)
        - High confidence amplifies effect

        Args:
            urgency: Urgency level (uses current_urgency if None)
            confidence: Decision confidence (0-1)

        Returns:
            New temperature value
        """
        if urgency is None:
            urgency = self.current_urgency

        # Inverse relationship: high urgency → low temperature
        temperature_factor = 1.0 - urgency

        # Confidence amplifies (confident + urgent = very low temp)
        confidence_modulation = 1.0 - 0.5 * confidence

        # Compute temperature (logarithmic scale)
        log_min = math.log(self.min_temperature)
        log_max = math.log(self.max_temperature)
        log_base = math.log(self.base_temperature)

        log_temp = log_base + (log_max - log_base) * temperature_factor * confidence_modulation

        temperature = math.exp(log_temp)
        temperature = max(self.min_temperature, min(self.max_temperature, temperature))

        self.current_temperature = temperature
        self.last_modulation_time = datetime.now()
        self.modulation_count += 1

        logger.info(f"Temperature modulated: {temperature:.3f} (urgency={urgency:.2f}, confidence={confidence:.2f})")

        return temperature

    def apply_softmax_temperature(self, logits: np.ndarray, temperature: Optional[float] = None) -> np.ndarray:
        """Apply temperature-modulated softmax to policy logits.

        Args:
            logits: Policy logits (unnormalized scores)
            temperature: Temperature value (uses current_temperature if None)

        Returns:
            Temperature-modulated probabilities
        """
        if temperature is None:
            temperature = self.current_temperature

        # Avoid division by zero or negative temperature
        temperature = max(0.01, temperature)

        # Temperature-scaled logits
        scaled_logits = logits / temperature

        # Softmax with numerical stability
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits))
        probabilities = exp_logits / np.sum(exp_logits)

        logger.debug(f"Softmax applied with temp={temperature:.3f}: entropy={self._compute_entropy(probabilities):.3f}")

        return probabilities

    def _compute_entropy(self, probabilities: np.ndarray) -> float:
        """Compute Shannon entropy of probability distribution.

        Args:
            probabilities: Probability distribution

        Returns:
            Entropy in nats
        """
        # Avoid log(0)
        probs = np.clip(probabilities, 1e-10, 1.0)
        return -np.sum(probs * np.log(probs))

    def modulate_policy_boldness(self, action_values: np.ndarray, urgency: Optional[float] = None) -> int:
        """Select action with urgency-modulated policy.

        High urgency = greedy (argmax)
        Low urgency = stochastic (softmax sampling)

        Args:
            action_values: Q-values or policy logits
            urgency: Urgency level (uses current_urgency if None)

        Returns:
            Selected action index
        """
        if urgency is None:
            urgency = self.current_urgency

        # Modulate temperature based on urgency
        temperature = self.modulate_temperature(urgency)

        # Apply softmax
        action_probs = self.apply_softmax_temperature(action_values, temperature)

        # Sample action
        action = np.random.choice(len(action_probs), p=action_probs)

        logger.debug(
            f"Action selected: {action} (urgency={urgency:.2f}, "
            f"temp={temperature:.3f}, prob={action_probs[action]:.3f})"
        )

        return int(action)

    def get_urgency_statistics(self, window: int = 50) -> Dict[str, Any]:
        """Get urgency statistics.

        Args:
            window: Window size for statistics

        Returns:
            Urgency statistics
        """
        if not self.urgency_history:
            return {"count": 0}

        recent = list(self.urgency_history)[-window:]

        urgencies = [entry["urgency"] for entry in recent]
        mean_urgency = sum(urgencies) / len(urgencies)

        return {
            "count": len(recent),
            "current_urgency": self.current_urgency,
            "mean_urgency": mean_urgency,
            "min_urgency": min(urgencies),
            "max_urgency": max(urgencies),
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Norepinephrine module status.

        Returns:
            Status dictionary
        """
        stats = self.get_urgency_statistics()

        return {
            "status": "operational",
            "current_temperature": self.current_temperature,
            "base_temperature": self.base_temperature,
            "temperature_range": [self.min_temperature, self.max_temperature],
            "current_urgency": self.current_urgency,
            "modulation_count": self.modulation_count,
            "last_modulation": (self.last_modulation_time.isoformat() if self.last_modulation_time else "N/A"),
            "urgency_statistics": stats,
        }
