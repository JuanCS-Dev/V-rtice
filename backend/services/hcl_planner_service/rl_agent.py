"""
HCL Planner - Reinforcement Learning Agent
===========================================
Soft Actor-Critic (SAC) agent for resource allocation.
Learns optimal policies through interaction.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import gymnasium as gym
from gymnasium import spaces

# Stable-Baselines3
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv

logger = logging.getLogger(__name__)


class KubernetesEnvironment(gym.Env):
    """
    Gymnasium environment simulating Kubernetes cluster.

    State space:
    - Current CPU usage (0-100%)
    - Current memory usage (0-100%)
    - Current GPU usage (0-100%)
    - Request queue depth (0-1000)
    - Error rate (0-100 errors/min)
    - Latency p99 (0-1000ms)
    - Current replicas per service (0-20)

    Action space:
    - Service scaling decisions:
      - action[0]: maximus_core replicas delta (-3 to +3)
      - action[1]: threat_intel replicas delta (-2 to +2)
      - action[2]: malware_analysis replicas delta (-2 to +2)
      - action[3]: resource limits multiplier (0.5 to 2.0)

    Reward:
    - +10 for SLA compliance (latency < 200ms, error_rate < 5)
    - -5 * cost_per_request
    - -10 * downtime_minutes
    - +3 * user_satisfaction_score (latency-based)
    """

    metadata = {'render_modes': []}

    def __init__(self):
        super().__init__()

        # State space (9 dimensions)
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0, 0, 1, 1, 1], dtype=np.float32),
            high=np.array([100, 100, 100, 1000, 100, 1000, 20, 20, 20], dtype=np.float32),
            dtype=np.float32
        )

        # Action space (4 dimensions)
        self.action_space = spaces.Box(
            low=np.array([-3, -2, -2, 0.5], dtype=np.float32),
            high=np.array([3, 2, 2, 2.0], dtype=np.float32),
            dtype=np.float32
        )

        # Internal state
        self.cpu_usage = 50.0
        self.memory_usage = 50.0
        self.gpu_usage = 30.0
        self.queue_depth = 100
        self.error_rate = 5.0
        self.latency = 150.0
        self.replicas = {"maximus_core": 3, "threat_intel": 2, "malware": 2}

        # Simulation parameters
        self.step_count = 0
        self.max_steps = 1000
        self.base_load = 50.0  # Base traffic load

        logger.info("Kubernetes environment initialized")

    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)

        # Random initial state
        self.cpu_usage = np.random.uniform(30, 70)
        self.memory_usage = np.random.uniform(30, 70)
        self.gpu_usage = np.random.uniform(20, 50)
        self.queue_depth = np.random.uniform(50, 200)
        self.error_rate = np.random.uniform(2, 10)
        self.latency = np.random.uniform(100, 300)

        self.replicas = {
            "maximus_core": np.random.randint(2, 6),
            "threat_intel": np.random.randint(1, 4),
            "malware": np.random.randint(1, 4)
        }

        self.step_count = 0

        return self._get_obs(), {}

    def _get_obs(self) -> np.ndarray:
        """Get current observation"""
        return np.array([
            self.cpu_usage,
            self.memory_usage,
            self.gpu_usage,
            self.queue_depth,
            self.error_rate,
            self.latency,
            self.replicas["maximus_core"],
            self.replicas["threat_intel"],
            self.replicas["malware"]
        ], dtype=np.float32)

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute action and update environment.

        Args:
            action: [maximus_delta, threat_intel_delta, malware_delta, resource_mult]

        Returns:
            (observation, reward, terminated, truncated, info)
        """
        self.step_count += 1

        # Parse action
        maximus_delta = int(np.round(action[0]))
        threat_intel_delta = int(np.round(action[1]))
        malware_delta = int(np.round(action[2]))
        resource_mult = float(action[3])

        # Apply actions (with constraints)
        self.replicas["maximus_core"] = np.clip(
            self.replicas["maximus_core"] + maximus_delta, 1, 20
        )
        self.replicas["threat_intel"] = np.clip(
            self.replicas["threat_intel"] + threat_intel_delta, 1, 20
        )
        self.replicas["malware"] = np.clip(
            self.replicas["malware"] + malware_delta, 1, 20
        )

        # Simulate system dynamics (simplified physics)
        total_replicas = sum(self.replicas.values())

        # Traffic load varies (simulate daily patterns + randomness)
        hour_of_day = (self.step_count % 24)
        traffic_multiplier = 0.5 + 0.5 * np.sin(2 * np.pi * hour_of_day / 24)
        traffic_multiplier += np.random.normal(0, 0.1)
        current_load = self.base_load * (1 + traffic_multiplier)

        # CPU usage depends on load and available replicas
        capacity = total_replicas * 10  # Each replica handles 10 units
        utilization = current_load / capacity
        self.cpu_usage = np.clip(utilization * 100, 0, 100)

        # Memory usage (slower dynamics)
        self.memory_usage = 0.9 * self.memory_usage + 0.1 * (30 + 0.5 * self.cpu_usage)
        self.memory_usage = np.clip(self.memory_usage, 0, 100)

        # GPU usage (depends on malware analysis)
        gpu_load = self.replicas["malware"] * 15
        self.gpu_usage = np.clip(gpu_load + np.random.normal(0, 5), 0, 100)

        # Queue depth (inversely related to capacity)
        if utilization > 1.0:
            self.queue_depth = self.queue_depth * 1.2 + 50  # Queue builds up
        else:
            self.queue_depth = self.queue_depth * 0.8  # Queue drains
        self.queue_depth = np.clip(self.queue_depth, 0, 1000)

        # Error rate (increases with overload)
        if self.cpu_usage > 90:
            self.error_rate = self.error_rate * 1.5
        elif self.cpu_usage < 50:
            self.error_rate = self.error_rate * 0.8
        self.error_rate = np.clip(self.error_rate, 0, 100)

        # Latency (increases with queue + CPU)
        base_latency = 50
        queue_latency = self.queue_depth * 0.5
        cpu_latency = max(0, (self.cpu_usage - 70) * 5)
        self.latency = base_latency + queue_latency + cpu_latency
        self.latency = np.clip(self.latency, 0, 1000)

        # Compute reward
        reward = self._compute_reward(resource_mult)

        # Episode termination
        terminated = False
        truncated = self.step_count >= self.max_steps

        info = {
            "cpu": self.cpu_usage,
            "memory": self.memory_usage,
            "latency": self.latency,
            "error_rate": self.error_rate,
            "replicas": dict(self.replicas),
            "cost": self._compute_cost(),
            "sla_compliant": self.latency < 200 and self.error_rate < 5
        }

        return self._get_obs(), reward, terminated, truncated, info

    def _compute_reward(self, resource_mult: float) -> float:
        """Compute reward signal"""
        reward = 0.0

        # SLA compliance reward
        if self.latency < 200 and self.error_rate < 5:
            reward += 10.0
        else:
            # Penalty proportional to violation
            latency_violation = max(0, self.latency - 200) / 200
            error_violation = max(0, self.error_rate - 5) / 20
            reward -= 10.0 * (latency_violation + error_violation)

        # Cost penalty (more replicas = higher cost)
        cost = self._compute_cost() * resource_mult
        reward -= cost * 0.1

        # User satisfaction (latency-based)
        if self.latency < 100:
            user_satisfaction = 10
        elif self.latency < 200:
            user_satisfaction = 5
        elif self.latency < 500:
            user_satisfaction = 0
        else:
            user_satisfaction = -5
        reward += user_satisfaction * 0.3

        # Resource efficiency bonus (low usage at low load)
        if self.cpu_usage < 40 and self.latency < 150:
            reward += 2.0  # Efficient operation

        return reward

    def _compute_cost(self) -> float:
        """Compute infrastructure cost"""
        # Cost per replica per hour (arbitrary units)
        costs = {
            "maximus_core": 2.0,
            "threat_intel": 1.5,
            "malware": 3.0  # GPU-intensive
        }
        total_cost = sum(costs[svc] * count for svc, count in self.replicas.items())
        return total_cost


class SACAgent:
    """
    Soft Actor-Critic agent for HCL planning.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize SAC agent.

        Args:
            model_path: Path to saved model (if loading)
        """
        # Create environment
        self.env = DummyVecEnv([lambda: KubernetesEnvironment()])

        if model_path and Path(model_path).exists():
            # Load existing model
            self.model = SAC.load(model_path, env=self.env)
            logger.info(f"Loaded SAC model from {model_path}")
        else:
            # Create new model
            self.model = SAC(
                "MlpPolicy",
                self.env,
                verbose=1,
                learning_rate=3e-4,
                buffer_size=100000,
                learning_starts=1000,
                batch_size=256,
                tau=0.005,
                gamma=0.99,
                train_freq=1,
                gradient_steps=1,
                ent_coef='auto',
                tensorboard_log="./tensorboard_logs/",
                policy_kwargs=dict(net_arch=[256, 256])
            )
            logger.info("Created new SAC model")

        self.training_steps = 0

    def predict(self, state: np.ndarray, deterministic: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Predict action for given state.

        Args:
            state: Current system state
            deterministic: Use deterministic policy (True for inference)

        Returns:
            (action, info)
        """
        action, _ = self.model.predict(state, deterministic=deterministic)
        return action, {}

    def train(self, total_timesteps: int = 50000):
        """
        Train the agent.

        Args:
            total_timesteps: Number of environment steps
        """
        logger.info(f"Training SAC agent for {total_timesteps} timesteps")

        self.model.learn(
            total_timesteps=total_timesteps,
            callback=TrainingCallback(),
            log_interval=10
        )

        self.training_steps += total_timesteps
        logger.info(f"Training complete. Total steps: {self.training_steps}")

    def save(self, path: str):
        """Save model to disk"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from disk"""
        self.model = SAC.load(path, env=self.env)
        logger.info(f"Model loaded from {path}")


class TrainingCallback(BaseCallback):
    """Callback for logging during training"""

    def __init__(self):
        super().__init__()
        self.episode_rewards = []
        self.episode_lengths = []

    def _on_step(self) -> bool:
        # Log rewards
        if len(self.locals['infos']) > 0:
            for info in self.locals['infos']:
                if 'episode' in info:
                    self.episode_rewards.append(info['episode']['r'])
                    self.episode_lengths.append(info['episode']['l'])

                    if len(self.episode_rewards) % 10 == 0:
                        avg_reward = np.mean(self.episode_rewards[-10:])
                        avg_length = np.mean(self.episode_lengths[-10:])
                        logger.info(f"Episode {len(self.episode_rewards)}: "
                                  f"avg_reward={avg_reward:.2f}, avg_length={avg_length:.0f}")

        return True


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create environment
    env = KubernetesEnvironment()

    # Test random actions
    print("\n" + "="*80)
    print("KUBERNETES ENVIRONMENT TEST")
    print("="*80 + "\n")

    obs, _ = env.reset()
    print(f"Initial state: {obs}")

    for step in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        print(f"\nStep {step + 1}:")
        print(f"  Action: {action}")
        print(f"  Reward: {reward:.2f}")
        print(f"  CPU: {info['cpu']:.1f}%")
        print(f"  Latency: {info['latency']:.1f}ms")
        print(f"  Replicas: {info['replicas']}")
        print(f"  SLA compliant: {info['sla_compliant']}")

        if terminated or truncated:
            break

    print("\n" + "="*80)
    print("SAC AGENT TEST")
    print("="*80 + "\n")

    # Create agent
    agent = SACAgent()

    # Train for a few steps (quick test)
    print("Training agent (10000 steps)...")
    agent.train(total_timesteps=10000)

    # Test trained agent
    print("\nTesting trained agent...")
    env = KubernetesEnvironment()
    obs, _ = env.reset()

    total_reward = 0
    for step in range(10):
        action, _ = agent.predict(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        print(f"Step {step + 1}: reward={reward:.2f}, latency={info['latency']:.1f}ms")

        if terminated or truncated:
            break

    print(f"\nTotal reward: {total_reward:.2f}")
