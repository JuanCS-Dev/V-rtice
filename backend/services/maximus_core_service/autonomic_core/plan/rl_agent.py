"""SAC RL Agent - Continuous Resource Optimization"""

import logging
import numpy as np
try:
    from stable_baselines3 import SAC
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    logging.warning("stable-baselines3 not available")

logger = logging.getLogger(__name__)


class SACAgent:
    """Soft Actor-Critic agent for resource allocation."""

    def __init__(self):
        self.model = None
        if not SB3_AVAILABLE:
            logger.warning("SAC agent disabled (install stable-baselines3)")

    def decide_actions(self, state: np.ndarray) -> dict:
        """
        Decide resource allocation actions.

        Args:
            state: 50+ metrics from Monitor Module

        Returns:
            Actions dict with cpu_%, mem_%, gpu_%, replicas
        """
        if not self.model or not SB3_AVAILABLE:
            # Fallback: conservative allocation
            return {
                'cpu_percent': 75.0,
                'memory_percent': 60.0,
                'gpu_percent': 50.0,
                'replicas': 3
            }

        action, _ = self.model.predict(state, deterministic=True)

        return self._apply_safety_constraints({
            'cpu_percent': float(action[0]),
            'memory_percent': float(action[1]),
            'gpu_percent': float(action[2]),
            'replicas': int(action[3])
        })

    def _apply_safety_constraints(self, action: dict) -> dict:
        """Apply hard limits: never <10% CPU, never >90% memory."""
        action['cpu_percent'] = np.clip(action['cpu_percent'], 10, 100)
        action['memory_percent'] = np.clip(action['memory_percent'], 10, 90)
        action['gpu_percent'] = np.clip(action['gpu_percent'], 0, 100)
        action['replicas'] = np.clip(action['replicas'], 1, 20)
        return action
