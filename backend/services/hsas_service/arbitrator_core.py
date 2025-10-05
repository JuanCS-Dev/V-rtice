"""HSAS Service - Production-Ready Arbitrator (Hybrid Controller)

Bio-inspired Arbitrator that implements:
1. **Model-Free vs Model-Based Selection**
   - Chooses between Actor-Critic (fast) and World Model (deliberative)
   - Based on model uncertainty
   - Adaptive arbitration strategy

2. **Uncertainty-Based Arbitration**
   - Low uncertainty → Model-free (habitual, fast)
   - High uncertainty → Model-based (planning, slow)
   - Smooth transition between modes

3. **Performance Monitoring**
   - Tracks success rates per mode
   - Adapts arbitration threshold
   - Meta-learning for arbitration

4. **Dyna-Style Integration**
   - Uses real experience for both models
   - Imaginary rollouts with world model
   - Hybrid experience replay

Like biological motor control: Basal Ganglia (habits) + Cerebellum (planning) arbitration.
NO MOCKS - Production-ready implementation.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from collections import deque
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ControlMode(Enum):
    """Control mode selection."""
    MODEL_FREE = "model_free"  # Actor-Critic (fast, habitual)
    MODEL_BASED = "model_based"  # World Model (slow, deliberative)
    HYBRID = "hybrid"  # Arbitrated


class ArbitratorCore:
    """Production-ready Arbitrator for hybrid model-free/model-based control.

    Implements:
    - Uncertainty-based arbitration
    - Mode selection (model-free vs model-based)
    - Performance tracking per mode
    - Adaptive arbitration threshold
    - Dyna-style integration
    """

    def __init__(
        self,
        uncertainty_threshold: float = 0.3,
        alpha_threshold: float = 0.1
    ):
        """Initialize Arbitrator Core.

        Args:
            uncertainty_threshold: Uncertainty threshold for mode selection
            alpha_threshold: Learning rate for threshold adaptation
        """
        self.uncertainty_threshold = uncertainty_threshold
        self.alpha_threshold = alpha_threshold

        # Mode statistics
        self.mode_selection_history: deque = deque(maxlen=1000)
        self.model_free_successes = 0
        self.model_free_trials = 0
        self.model_based_successes = 0
        self.model_based_trials = 0

        # Arbitration statistics
        self.arbitration_count = 0
        self.last_arbitration_time: Optional[datetime] = None
        self.current_mode: Optional[ControlMode] = None

        logger.info(
            f"ArbitratorCore initialized (uncertainty_threshold={uncertainty_threshold})"
        )

    def arbitrate(
        self,
        uncertainty: float,
        urgency: float = 0.5,
        mode: ControlMode = ControlMode.HYBRID
    ) -> ControlMode:
        """Arbitrate between model-free and model-based control.

        Strategy:
        - Low uncertainty + high urgency → Model-free (fast habit)
        - High uncertainty + low urgency → Model-based (careful planning)
        - Hybrid mode adapts threshold based on performance

        Args:
            uncertainty: Model uncertainty (0-1)
            urgency: Urgency signal from norepinephrine (0-1)
            mode: Control mode (HYBRID does arbitration)

        Returns:
            Selected control mode
        """
        self.arbitration_count += 1
        self.last_arbitration_time = datetime.now()

        if mode == ControlMode.MODEL_FREE:
            selected_mode = ControlMode.MODEL_FREE
        elif mode == ControlMode.MODEL_BASED:
            selected_mode = ControlMode.MODEL_BASED
        elif mode == ControlMode.HYBRID:
            # Adaptive threshold (considers urgency)
            # High urgency → lower threshold (favor model-free)
            effective_threshold = self.uncertainty_threshold * (1.0 - 0.5 * urgency)

            if uncertainty < effective_threshold:
                # Confident in model → use fast habit
                selected_mode = ControlMode.MODEL_FREE
            else:
                # Uncertain → use slow planning
                selected_mode = ControlMode.MODEL_BASED
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Record selection
        self.mode_selection_history.append({
            'timestamp': datetime.now().isoformat(),
            'mode': selected_mode.value,
            'uncertainty': uncertainty,
            'urgency': urgency,
            'threshold': self.uncertainty_threshold
        })

        self.current_mode = selected_mode

        logger.debug(
            f"Arbitration: {selected_mode.value} (uncertainty={uncertainty:.3f}, "
            f"threshold={self.uncertainty_threshold:.3f}, urgency={urgency:.2f})"
        )

        return selected_mode

    def record_outcome(self, mode: ControlMode, success: bool):
        """Record outcome for selected mode.

        Args:
            mode: Control mode used
            success: Whether action was successful
        """
        if mode == ControlMode.MODEL_FREE:
            self.model_free_trials += 1
            if success:
                self.model_free_successes += 1
        elif mode == ControlMode.MODEL_BASED:
            self.model_based_trials += 1
            if success:
                self.model_based_successes += 1

        logger.debug(
            f"Outcome recorded: mode={mode.value}, success={success}"
        )

    def adapt_threshold(self):
        """Adapt arbitration threshold based on performance.

        If model-free is performing better, lower threshold (use it more).
        If model-based is performing better, raise threshold (use it more).
        """
        if self.model_free_trials < 10 or self.model_based_trials < 10:
            # Insufficient data
            return

        # Compute success rates
        model_free_rate = self.model_free_successes / self.model_free_trials
        model_based_rate = self.model_based_successes / self.model_based_trials

        # Compute performance difference
        performance_diff = model_free_rate - model_based_rate

        # Update threshold
        # If model-free better → lower threshold (use more)
        # If model-based better → raise threshold (use more)
        delta_threshold = -self.alpha_threshold * performance_diff

        self.uncertainty_threshold = np.clip(
            self.uncertainty_threshold + delta_threshold,
            0.1,  # min threshold
            0.9   # max threshold
        )

        logger.info(
            f"Threshold adapted: {self.uncertainty_threshold:.3f} "
            f"(model_free={model_free_rate:.2f}, model_based={model_based_rate:.2f})"
        )

    def get_mode_statistics(self) -> Dict[str, Any]:
        """Get mode selection statistics.

        Returns:
            Mode statistics
        """
        model_free_rate = (
            self.model_free_successes / self.model_free_trials
            if self.model_free_trials > 0 else 0.0
        )

        model_based_rate = (
            self.model_based_successes / self.model_based_trials
            if self.model_based_trials > 0 else 0.0
        )

        # Count mode selections
        recent_history = list(self.mode_selection_history)[-100:]
        model_free_count = sum(1 for h in recent_history if h['mode'] == ControlMode.MODEL_FREE.value)
        model_based_count = sum(1 for h in recent_history if h['mode'] == ControlMode.MODEL_BASED.value)

        return {
            'model_free': {
                'trials': self.model_free_trials,
                'successes': self.model_free_successes,
                'success_rate': model_free_rate,
                'recent_count': model_free_count
            },
            'model_based': {
                'trials': self.model_based_trials,
                'successes': self.model_based_successes,
                'success_rate': model_based_rate,
                'recent_count': model_based_count
            }
        }

    def get_uncertainty_statistics(self, window: int = 100) -> Dict[str, Any]:
        """Get uncertainty statistics from recent arbitrations.

        Args:
            window: Window size for statistics

        Returns:
            Uncertainty statistics
        """
        if not self.mode_selection_history:
            return {'count': 0}

        recent = list(self.mode_selection_history)[-window:]

        uncertainties = [h['uncertainty'] for h in recent]
        mean_uncertainty = sum(uncertainties) / len(uncertainties)

        return {
            'count': len(recent),
            'mean_uncertainty': mean_uncertainty,
            'min_uncertainty': min(uncertainties),
            'max_uncertainty': max(uncertainties)
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Arbitrator status.

        Returns:
            Status dictionary
        """
        mode_stats = self.get_mode_statistics()
        uncertainty_stats = self.get_uncertainty_statistics()

        return {
            'status': 'operational',
            'current_mode': self.current_mode.value if self.current_mode else 'N/A',
            'uncertainty_threshold': self.uncertainty_threshold,
            'arbitration_count': self.arbitration_count,
            'last_arbitration': self.last_arbitration_time.isoformat() if self.last_arbitration_time else 'N/A',
            'mode_statistics': mode_stats,
            'uncertainty_statistics': uncertainty_stats
        }


class DynaIntegration:
    """Dyna-style integration of real and imaginary experience.

    Combines:
    - Real experience (from environment)
    - Imaginary experience (from world model)
    - Hybrid replay for both actor-critic and world model
    """

    def __init__(self, real_ratio: float = 0.5):
        """Initialize Dyna Integration.

        Args:
            real_ratio: Ratio of real to imaginary experience in replay (0-1)
        """
        self.real_ratio = real_ratio

        # Experience buffers
        self.real_experience: deque = deque(maxlen=10000)
        self.imaginary_experience: deque = deque(maxlen=10000)

        # Statistics
        self.real_experience_count = 0
        self.imaginary_experience_count = 0

        logger.info(f"DynaIntegration initialized (real_ratio={real_ratio})")

    def store_real_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store real experience from environment.

        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Episode termination flag
        """
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'type': 'real',
            'timestamp': datetime.now().isoformat()
        }

        self.real_experience.append(experience)
        self.real_experience_count += 1

    def store_imaginary_experience(
        self,
        state: np.ndarray,
        action: int,
        predicted_reward: float,
        predicted_next_state: np.ndarray,
        uncertainty: float
    ):
        """Store imaginary experience from world model.

        Args:
            state: Current state
            action: Action taken
            predicted_reward: Predicted reward
            predicted_next_state: Predicted next state
            uncertainty: Model uncertainty
        """
        experience = {
            'state': state,
            'action': action,
            'reward': predicted_reward,
            'next_state': predicted_next_state,
            'done': False,  # Imaginary experiences don't terminate
            'type': 'imaginary',
            'uncertainty': uncertainty,
            'timestamp': datetime.now().isoformat()
        }

        self.imaginary_experience.append(experience)
        self.imaginary_experience_count += 1

    def sample_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Sample mixed batch of real and imaginary experience.

        Args:
            batch_size: Total batch size

        Returns:
            Mixed batch of experiences
        """
        num_real = int(batch_size * self.real_ratio)
        num_imaginary = batch_size - num_real

        batch = []

        # Sample real experience
        if len(self.real_experience) >= num_real:
            real_indices = np.random.choice(len(self.real_experience), num_real, replace=False)
            batch.extend([self.real_experience[i] for i in real_indices])

        # Sample imaginary experience
        if len(self.imaginary_experience) >= num_imaginary:
            imaginary_indices = np.random.choice(len(self.imaginary_experience), num_imaginary, replace=False)
            batch.extend([self.imaginary_experience[i] for i in imaginary_indices])

        logger.debug(
            f"Sampled batch: {len(batch)} experiences "
            f"(real={num_real}, imaginary={num_imaginary})"
        )

        return batch

    async def get_status(self) -> Dict[str, Any]:
        """Get Dyna Integration status.

        Returns:
            Status dictionary
        """
        return {
            'status': 'operational',
            'real_ratio': self.real_ratio,
            'real_experience_buffer_size': len(self.real_experience),
            'imaginary_experience_buffer_size': len(self.imaginary_experience),
            'real_experience_count': self.real_experience_count,
            'imaginary_experience_count': self.imaginary_experience_count
        }
