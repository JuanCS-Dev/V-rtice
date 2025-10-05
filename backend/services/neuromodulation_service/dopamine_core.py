"""Neuromodulation Service - Production-Ready Dopamine Module

Bio-inspired dopamine modulator that implements:
1. **Reward Prediction Error (RPE) Computation**
   - TD-error from HSAS Critic
   - Temporal-difference learning
   - Reward expectation vs reality

2. **Learning Rate Modulation**
   - Adaptive LR based on RPE magnitude
   - High RPE = higher LR (novelty)
   - Low RPE = lower LR (exploitation)

3. **PyTorch Optimizer Integration**
   - Direct modification of optimizer LR
   - Adam, SGD, AdamW support
   - Real-time hyperparameter adjustment

Like biological dopamine: Signals reward prediction errors and modulates learning.
NO MOCKS - Production-ready implementation.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import deque

logger = logging.getLogger(__name__)


class DopamineCore:
    """Production-ready Dopamine module for learning rate modulation.

    Computes RPE and adjusts learning rates based on reward prediction errors:
    - High RPE → High LR (learn faster from surprises)
    - Low RPE → Low LR (stable in known situations)
    """

    def __init__(
        self,
        base_learning_rate: float = 0.001,
        min_lr: float = 0.0001,
        max_lr: float = 0.01,
        rpe_window_size: int = 100
    ):
        """Initialize Dopamine Core.

        Args:
            base_learning_rate: Base LR for modulation
            min_lr: Minimum learning rate
            max_lr: Maximum learning rate
            rpe_window_size: Window size for RPE history
        """
        self.base_lr = base_learning_rate
        self.min_lr = min_lr
        self.max_lr = max_lr

        self.current_lr = base_learning_rate
        self.rpe_history: deque = deque(maxlen=rpe_window_size)
        self.reward_history: deque = deque(maxlen=rpe_window_size)
        self.expected_reward_history: deque = deque(maxlen=rpe_window_size)

        self.last_modulation_time: Optional[datetime] = None
        self.modulation_count = 0

        logger.info(
            f"DopamineCore initialized (base_lr={base_learning_rate}, "
            f"range=[{min_lr}, {max_lr}])"
        )

    def compute_rpe(
        self,
        actual_reward: float,
        expected_reward: float,
        discount_factor: float = 0.99
    ) -> float:
        """Compute Reward Prediction Error (RPE).

        RPE = actual_reward - expected_reward

        In TD-learning:
        RPE = r_t + γ * V(s_{t+1}) - V(s_t)

        Args:
            actual_reward: Actual reward received
            expected_reward: Expected reward (from Critic)
            discount_factor: Discount factor (gamma)

        Returns:
            Reward prediction error
        """
        rpe = actual_reward - expected_reward

        # Store in history
        self.rpe_history.append(rpe)
        self.reward_history.append(actual_reward)
        self.expected_reward_history.append(expected_reward)

        logger.debug(
            f"RPE computed: {rpe:.4f} (actual={actual_reward:.4f}, "
            f"expected={expected_reward:.4f})"
        )

        return rpe

    def modulate_learning_rate(self, rpe: float, urgency: float = 0.5) -> float:
        """Modulate learning rate based on RPE magnitude.

        Strategy:
        - High |RPE| → High LR (novelty, need to learn fast)
        - Low |RPE| → Low LR (stable, exploitation)
        - Urgency amplifies modulation

        Args:
            rpe: Reward prediction error
            urgency: Urgency signal from norepinephrine (0-1)

        Returns:
            New learning rate
        """
        # Compute RPE magnitude (surprise level)
        rpe_magnitude = abs(rpe)

        # Normalize RPE by recent history (0-1 scale)
        if len(self.rpe_history) > 10:
            rpe_std = max(0.01, self._compute_rpe_std())
            normalized_rpe = min(1.0, rpe_magnitude / (3 * rpe_std))  # 3-sigma
        else:
            normalized_rpe = min(1.0, rpe_magnitude)

        # Modulate LR with urgency
        # High surprise + high urgency = very high LR
        modulation_factor = normalized_rpe * (0.5 + 0.5 * urgency)

        # Compute new LR (logarithmic scale)
        log_min = math.log(self.min_lr)
        log_max = math.log(self.max_lr)
        log_base = math.log(self.base_lr)

        log_new = log_base + (log_max - log_base) * modulation_factor

        new_lr = math.exp(log_new)
        new_lr = max(self.min_lr, min(self.max_lr, new_lr))

        self.current_lr = new_lr
        self.last_modulation_time = datetime.now()
        self.modulation_count += 1

        logger.info(
            f"LR modulated: {new_lr:.6f} (RPE={rpe:.4f}, "
            f"surprise={normalized_rpe:.2f}, urgency={urgency:.2f})"
        )

        return new_lr

    def _compute_rpe_std(self) -> float:
        """Compute standard deviation of recent RPE history.

        Returns:
            Standard deviation of RPE
        """
        if len(self.rpe_history) < 2:
            return 1.0

        rpe_list = list(self.rpe_history)
        mean_rpe = sum(rpe_list) / len(rpe_list)
        variance = sum((x - mean_rpe) ** 2 for x in rpe_list) / len(rpe_list)

        return math.sqrt(variance)

    def integrate_with_pytorch_optimizer(
        self,
        optimizer,
        rpe: float,
        urgency: float = 0.5
    ):
        """Integrate with PyTorch optimizer (modify LR in-place).

        Args:
            optimizer: PyTorch optimizer (Adam, SGD, etc.)
            rpe: Reward prediction error
            urgency: Urgency signal from norepinephrine
        """
        new_lr = self.modulate_learning_rate(rpe, urgency)

        # Update optimizer LR
        for param_group in optimizer.param_groups:
            param_group['lr'] = new_lr

        logger.info(f"PyTorch optimizer LR updated: {new_lr:.6f}")

    def get_rpe_statistics(self, window: int = 100) -> Dict[str, Any]:
        """Get RPE statistics for recent window.

        Args:
            window: Window size for statistics

        Returns:
            RPE statistics
        """
        if not self.rpe_history:
            return {'count': 0}

        recent_rpe = list(self.rpe_history)[-window:]

        mean_rpe = sum(recent_rpe) / len(recent_rpe)
        abs_mean_rpe = sum(abs(x) for x in recent_rpe) / len(recent_rpe)

        positive_rpe = [x for x in recent_rpe if x > 0]
        negative_rpe = [x for x in recent_rpe if x < 0]

        return {
            'count': len(recent_rpe),
            'mean_rpe': mean_rpe,
            'abs_mean_rpe': abs_mean_rpe,
            'std_rpe': self._compute_rpe_std(),
            'positive_count': len(positive_rpe),
            'negative_count': len(negative_rpe),
            'positive_ratio': len(positive_rpe) / len(recent_rpe) if recent_rpe else 0.0
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Dopamine module status.

        Returns:
            Status dictionary
        """
        stats = self.get_rpe_statistics()

        return {
            'status': 'operational',
            'current_lr': self.current_lr,
            'base_lr': self.base_lr,
            'lr_range': [self.min_lr, self.max_lr],
            'modulation_count': self.modulation_count,
            'last_modulation': self.last_modulation_time.isoformat() if self.last_modulation_time else 'N/A',
            'rpe_statistics': stats
        }
