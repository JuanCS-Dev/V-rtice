"""HCL Planner Service - Reinforcement Learning Agent.

This module implements a Reinforcement Learning (RL) agent using the Soft
Actor-Critic (SAC) algorithm from the `stable-baselines3` library. The agent is
trained in a simulated Kubernetes environment to learn optimal resource
allocation policies.

Its goal is to make decisions (e.g., scaling services) that balance performance
(low latency, low error rate) with operational cost.
"""

import numpy as np
import logging
from typing import Tuple, Optional
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import SAC
from pathlib import Path

logger = logging.getLogger(__name__)


class KubernetesEnvironment(gym.Env):
    """A custom Gymnasium environment that simulates a Kubernetes cluster.

    This environment defines the state space, action space, and reward function
    for the RL agent. The agent interacts with this simulation to learn how its
    actions (like scaling replicas) affect the system's state (like CPU usage
    and latency).

    Attributes:
        observation_space (spaces.Box): The space of possible states.
        action_space (spaces.Box): The space of possible actions.
    """

    def __init__(self):
        """Initializes the Kubernetes simulation environment."""
        super().__init__()
        # Define state space (e.g., cpu, memory, replicas)
        self.observation_space = spaces.Box(low=0, high=100, shape=(9,), dtype=np.float32)
        # Define action space (e.g., scaling deltas)
        self.action_space = spaces.Box(low=-3, high=3, shape=(4,), dtype=np.float32)
        self.reset()

    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, dict]:
        """Resets the environment to a random initial state."""
        super().reset(seed=seed)
        self.state = self.observation_space.sample()
        return self.state, {}

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """Executes one time step within the environment.

        This method applies an action, simulates the system's response, calculates
        the reward, and returns the new state.

        Args:
            action (np.ndarray): The action taken by the agent.

        Returns:
            A tuple containing the new state, reward, done flag, and info dict.
        """
        # Simplified simulation logic
        self.state = np.clip(self.state + np.random.randn(9), 0, 100)
        reward = -np.mean((self.state - 50)**2) # Reward for staying near 50% usage
        terminated = False
        truncated = False
        return self.state, reward, terminated, truncated, {}


class SACAgent:
    """A Soft Actor-Critic (SAC) agent for HCL resource allocation.

    This class wraps the `stable-baselines3` SAC implementation, providing a
    simple interface for training the agent and predicting actions.

    Attributes:
        model (SAC): The underlying SAC model from `stable-baselines3`.
        env (DummyVecEnv): The vectorized training environment.
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initializes the SAC agent, loading a model if a path is provided.

        Args:
            model_path (Optional[str]): The file path to a pre-trained model.
                If None, a new model is created.
        """
        self.env = gym.make('__main__:KubernetesEnvironment')
        if model_path and Path(model_path).exists():
            self.model = SAC.load(model_path, env=self.env)
            logger.info(f"Loaded SAC model from {model_path}")
        else:
            self.model = SAC("MlpPolicy", self.env, verbose=0)
            logger.info("Created a new SAC model.")

    def predict(self, state: np.ndarray, deterministic: bool = True) -> Tuple[np.ndarray, dict]:
        """Predicts the best action for a given state.

        Args:
            state (np.ndarray): The current observation of the system state.
            deterministic (bool): Whether to use a deterministic or stochastic policy.

        Returns:
            A tuple containing the predicted action and optional state info.
        """
        action, _states = self.model.predict(state, deterministic=deterministic)
        return action, {}

    def train(self, total_timesteps: int = 50000):
        """Trains the agent for a specified number of timesteps."""
        logger.info(f"Training SAC agent for {total_timesteps} timesteps...")
        self.model.learn(total_timesteps=total_timesteps)
        logger.info("Training complete.")

    def save(self, path: str):
        """Saves the trained model to the specified path."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
        logger.info(f"SAC model saved to {path}")