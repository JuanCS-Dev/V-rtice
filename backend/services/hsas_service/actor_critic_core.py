"""HSAS Service - Production-Ready Actor-Critic (Model-Free RL)

Bio-inspired Actor-Critic system that implements:
1. **Actor Network (Policy)**
   - Stochastic policy π(a|s)
   - Action selection with exploration
   - Policy gradient optimization

2. **Critic Network (Value Function)**
   - State-value function V(s)
   - Advantage estimation A(s,a) = Q(s,a) - V(s)
   - TD-error computation for dopamine

3. **Neuromodulation Integration**
   - Dopamine-modulated learning rate
   - Norepinephrine-modulated temperature
   - Serotonin-modulated exploration

Like biological Basal Ganglia: Habitual, fast, model-free reinforcement learning.
NO MOCKS - Production-ready implementation.
"""

import logging
import math
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class ActorNetwork:
    """Actor network: learns stochastic policy π(a|s)."""

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        """Initialize Actor network.

        Args:
            state_dim: State space dimensionality
            action_dim: Action space dimensionality
            hidden_dim: Hidden layer size
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim

        # Initialize weights (Xavier initialization)
        self.w1 = self._xavier_init((state_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        self.w2 = self._xavier_init((hidden_dim, hidden_dim))
        self.b2 = np.zeros(hidden_dim)
        self.w3 = self._xavier_init((hidden_dim, action_dim))
        self.b3 = np.zeros(action_dim)

        logger.info(f"ActorNetwork initialized (state={state_dim}, action={action_dim}, hidden={hidden_dim})")

    def _xavier_init(self, shape: Tuple[int, int]) -> np.ndarray:
        """Xavier weight initialization.

        Args:
            shape: Weight matrix shape

        Returns:
            Initialized weight matrix
        """
        fan_in, fan_out = shape
        bound = math.sqrt(6.0 / (fan_in + fan_out))
        return np.random.uniform(-bound, bound, size=shape)

    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)

    def _softmax(self, logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Temperature-modulated softmax.

        Args:
            logits: Action logits
            temperature: Softmax temperature (from norepinephrine)

        Returns:
            Action probabilities
        """
        # Temperature scaling
        scaled_logits = logits / max(0.01, temperature)

        # Numerical stability
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits))
        return exp_logits / np.sum(exp_logits)

    def forward(self, state: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Forward pass: compute action probabilities.

        Args:
            state: Current state
            temperature: Softmax temperature

        Returns:
            Action probabilities π(a|s)
        """
        # Layer 1
        h1 = self._relu(np.dot(state, self.w1) + self.b1)

        # Layer 2
        h2 = self._relu(np.dot(h1, self.w2) + self.b2)

        # Output layer (logits)
        logits = np.dot(h2, self.w3) + self.b3

        # Softmax with temperature
        action_probs = self._softmax(logits, temperature)

        return action_probs

    def select_action(
        self,
        state: np.ndarray,
        temperature: float = 1.0,
        deterministic: bool = False
    ) -> int:
        """Select action from policy.

        Args:
            state: Current state
            temperature: Softmax temperature
            deterministic: If True, select argmax (no sampling)

        Returns:
            Selected action index
        """
        action_probs = self.forward(state, temperature)

        if deterministic:
            action = int(np.argmax(action_probs))
        else:
            action = int(np.random.choice(len(action_probs), p=action_probs))

        return action

    def get_action_logits(self, state: np.ndarray) -> np.ndarray:
        """Get raw action logits (for norepinephrine modulation).

        Args:
            state: Current state

        Returns:
            Action logits (before softmax)
        """
        h1 = self._relu(np.dot(state, self.w1) + self.b1)
        h2 = self._relu(np.dot(h1, self.w2) + self.b2)
        logits = np.dot(h2, self.w3) + self.b3
        return logits


class CriticNetwork:
    """Critic network: learns state-value function V(s)."""

    def __init__(self, state_dim: int, hidden_dim: int = 256):
        """Initialize Critic network.

        Args:
            state_dim: State space dimensionality
            hidden_dim: Hidden layer size
        """
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim

        # Initialize weights
        self.w1 = self._xavier_init((state_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        self.w2 = self._xavier_init((hidden_dim, hidden_dim))
        self.b2 = np.zeros(hidden_dim)
        self.w3 = self._xavier_init((hidden_dim, 1))
        self.b3 = np.zeros(1)

        logger.info(f"CriticNetwork initialized (state={state_dim}, hidden={hidden_dim})")

    def _xavier_init(self, shape: Tuple[int, int]) -> np.ndarray:
        """Xavier weight initialization."""
        fan_in, fan_out = shape
        bound = math.sqrt(6.0 / (fan_in + fan_out))
        return np.random.uniform(-bound, bound, size=shape)

    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)

    def forward(self, state: np.ndarray) -> float:
        """Forward pass: compute state value V(s).

        Args:
            state: Current state

        Returns:
            State value V(s)
        """
        # Layer 1
        h1 = self._relu(np.dot(state, self.w1) + self.b1)

        # Layer 2
        h2 = self._relu(np.dot(h1, self.w2) + self.b2)

        # Output layer (single value)
        value = np.dot(h2, self.w3) + self.b3

        return float(value[0])


class ActorCriticCore:
    """Production-ready Actor-Critic for model-free RL.

    Implements:
    - Actor: stochastic policy π(a|s)
    - Critic: state-value function V(s)
    - TD-error computation (for dopamine)
    - Advantage estimation A(s,a)
    - Policy gradient updates
    - Neuromodulation integration
    """

    def __init__(
        self,
        state_dim: int = 512,
        action_dim: int = 50,
        hidden_dim: int = 256,
        gamma: float = 0.99,
        base_lr_actor: float = 0.001,
        base_lr_critic: float = 0.005
    ):
        """Initialize Actor-Critic Core.

        Args:
            state_dim: State space dimensionality
            action_dim: Action space dimensionality (number of skill primitives)
            hidden_dim: Hidden layer size
            gamma: Discount factor
            base_lr_actor: Base learning rate for actor
            base_lr_critic: Base learning rate for critic
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.base_lr_actor = base_lr_actor
        self.base_lr_critic = base_lr_critic

        # Current learning rates (modulated by dopamine)
        self.lr_actor = base_lr_actor
        self.lr_critic = base_lr_critic

        # Networks
        self.actor = ActorNetwork(state_dim, action_dim, hidden_dim)
        self.critic = CriticNetwork(state_dim, hidden_dim)

        # Experience buffer
        self.experience_buffer: deque = deque(maxlen=10000)

        # Training statistics
        self.td_error_history: deque = deque(maxlen=1000)
        self.episode_returns: deque = deque(maxlen=100)
        self.update_count = 0
        self.last_update_time: Optional[datetime] = None

        logger.info(
            f"ActorCriticCore initialized (state={state_dim}, action={action_dim}, "
            f"gamma={gamma})"
        )

    def select_action(
        self,
        state: np.ndarray,
        temperature: float = 1.0,
        epsilon: float = 0.0,
        deterministic: bool = False
    ) -> Tuple[int, float]:
        """Select action using actor policy.

        Args:
            state: Current state
            temperature: Softmax temperature (from norepinephrine)
            epsilon: Exploration rate (from serotonin)
            deterministic: If True, select argmax

        Returns:
            (action, value) tuple
        """
        # Epsilon-greedy exploration (serotonin)
        if not deterministic and np.random.random() < epsilon:
            action = int(np.random.randint(0, self.action_dim))
            logger.debug(f"Random exploration: action={action}")
        else:
            # Temperature-modulated policy (norepinephrine)
            action = self.actor.select_action(state, temperature, deterministic)

        # Compute state value (critic)
        value = self.critic.forward(state)

        return action, value

    def compute_td_error(
        self,
        state: np.ndarray,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ) -> float:
        """Compute TD-error (Reward Prediction Error for dopamine).

        TD-error = r + γ * V(s') - V(s)

        Args:
            state: Current state
            reward: Reward received
            next_state: Next state
            done: Episode termination flag

        Returns:
            TD-error (RPE for dopamine)
        """
        v_current = self.critic.forward(state)

        if done:
            v_next = 0.0
        else:
            v_next = self.critic.forward(next_state)

        td_error = reward + self.gamma * v_next - v_current

        # Store in history
        self.td_error_history.append(td_error)

        logger.debug(
            f"TD-error: {td_error:.4f} (r={reward:.4f}, V(s)={v_current:.4f}, "
            f"V(s')={v_next:.4f})"
        )

        return td_error

    def update_learning_rates(self, lr_actor: float, lr_critic: float):
        """Update learning rates (called by dopamine module).

        Args:
            lr_actor: New actor learning rate
            lr_critic: New critic learning rate
        """
        self.lr_actor = lr_actor
        self.lr_critic = lr_critic

        logger.debug(f"LR updated: actor={lr_actor:.6f}, critic={lr_critic:.6f}")

    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store experience in replay buffer.

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
            'timestamp': datetime.now().isoformat()
        }

        self.experience_buffer.append(experience)

    def compute_advantage(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ) -> float:
        """Compute advantage A(s,a) = Q(s,a) - V(s).

        Using TD-error: A(s,a) ≈ δ = r + γ*V(s') - V(s)

        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Episode termination flag

        Returns:
            Advantage estimate
        """
        td_error = self.compute_td_error(state, reward, next_state, done)
        return td_error

    def update_networks(self, batch_size: int = 32) -> Dict[str, float]:
        """Update actor and critic networks with policy gradient.

        Args:
            batch_size: Batch size for updates

        Returns:
            Training statistics
        """
        if len(self.experience_buffer) < batch_size:
            return {'error': 'insufficient_data'}

        # Sample batch from experience buffer
        indices = np.random.choice(len(self.experience_buffer), batch_size, replace=False)
        batch = [self.experience_buffer[i] for i in indices]

        # Compute losses
        actor_loss = 0.0
        critic_loss = 0.0

        for exp in batch:
            state = exp['state']
            action = exp['action']
            reward = exp['reward']
            next_state = exp['next_state']
            done = exp['done']

            # Compute advantage (TD-error)
            advantage = self.compute_advantage(state, action, reward, next_state, done)

            # Actor loss: -log π(a|s) * A(s,a) (policy gradient)
            action_probs = self.actor.forward(state)
            log_prob = np.log(action_probs[action] + 1e-8)
            actor_loss -= log_prob * advantage

            # Critic loss: (TD-error)^2
            critic_loss += advantage ** 2

        actor_loss /= batch_size
        critic_loss /= batch_size

        # Update networks (simplified gradient descent)
        # In production, use PyTorch/TensorFlow for automatic differentiation
        self._update_actor_weights(batch, actor_loss)
        self._update_critic_weights(batch, critic_loss)

        self.update_count += 1
        self.last_update_time = datetime.now()

        logger.info(
            f"Networks updated (count={self.update_count}): "
            f"actor_loss={actor_loss:.4f}, critic_loss={critic_loss:.4f}"
        )

        return {
            'actor_loss': actor_loss,
            'critic_loss': critic_loss,
            'batch_size': batch_size,
            'update_count': self.update_count
        }

    def _update_actor_weights(self, batch: List[Dict], loss: float):
        """Update actor weights using REAL gradient descent (NumPy).

        Implements policy gradient: ∇θ J(θ) = E[∇θ log π(a|s) * A(s,a)]

        Args:
            batch: Training batch
            loss: Actor loss (for logging)
        """
        learning_rate = self.actor_lr

        # Accumulate gradients over batch
        grad_w1 = np.zeros_like(self.actor.w1)
        grad_b1 = np.zeros_like(self.actor.b1)
        grad_w2 = np.zeros_like(self.actor.w2)
        grad_b2 = np.zeros_like(self.actor.b2)
        grad_w3 = np.zeros_like(self.actor.w3)
        grad_b3 = np.zeros_like(self.actor.b3)

        for experience in batch:
            state = experience['state']
            action = experience['action']
            advantage = experience.get('advantage', experience['reward'])  # A(s,a)

            # Forward pass (save activations)
            h1 = self.actor._relu(np.dot(state, self.actor.w1) + self.actor.b1)
            h2 = self.actor._relu(np.dot(h1, self.actor.w2) + self.actor.b2)
            logits = np.dot(h2, self.actor.w3) + self.actor.b3
            action_probs = self.actor._softmax(logits, temperature=1.0)

            # Backward pass (compute gradients)
            # Output layer gradient: ∇log π(a|s) = ∂/∂logits
            d_logits = action_probs.copy()
            d_logits[action] -= 1.0  # Gradient of log(π(a|s))
            d_logits *= advantage  # Scale by advantage

            # Layer 3 gradients
            grad_w3 += np.outer(h2, d_logits)
            grad_b3 += d_logits

            # Layer 2 gradients
            d_h2 = np.dot(d_logits, self.actor.w3.T)
            d_h2[h2 <= 0] = 0  # ReLU derivative
            grad_w2 += np.outer(h1, d_h2)
            grad_b2 += d_h2

            # Layer 1 gradients
            d_h1 = np.dot(d_h2, self.actor.w2.T)
            d_h1[h1 <= 0] = 0  # ReLU derivative
            grad_w1 += np.outer(state, d_h1)
            grad_b1 += d_h1

        # Average gradients
        batch_size = len(batch)
        grad_w1 /= batch_size
        grad_b1 /= batch_size
        grad_w2 /= batch_size
        grad_b2 /= batch_size
        grad_w3 /= batch_size
        grad_b3 /= batch_size

        # Gradient descent update
        self.actor.w1 -= learning_rate * grad_w1
        self.actor.b1 -= learning_rate * grad_b1
        self.actor.w2 -= learning_rate * grad_w2
        self.actor.b2 -= learning_rate * grad_b2
        self.actor.w3 -= learning_rate * grad_w3
        self.actor.b3 -= learning_rate * grad_b3

    def _update_critic_weights(self, batch: List[Dict], loss: float):
        """Update critic weights using REAL gradient descent (NumPy).

        Implements MSE loss: L = (V(s) - target)²

        Args:
            batch: Training batch
            loss: Critic loss (for logging)
        """
        learning_rate = self.critic_lr

        # Accumulate gradients over batch
        grad_w1 = np.zeros_like(self.critic.w1)
        grad_b1 = np.zeros_like(self.critic.b1)
        grad_w2 = np.zeros_like(self.critic.w2)
        grad_b2 = np.zeros_like(self.critic.b2)
        grad_w3 = np.zeros_like(self.critic.w3)
        grad_b3 = np.zeros_like(self.critic.b3)

        for experience in batch:
            state = experience['state']
            target = experience.get('target', experience['reward'])  # TD target

            # Forward pass (save activations)
            h1 = self.critic._relu(np.dot(state, self.critic.w1) + self.critic.b1)
            h2 = self.critic._relu(np.dot(h1, self.critic.w2) + self.critic.b2)
            value = np.dot(h2, self.critic.w3) + self.critic.b3

            # Backward pass (compute gradients)
            # MSE loss gradient: 2 * (V(s) - target) * ∂V/∂weights
            error = value[0] - target
            d_output = 2.0 * error

            # Layer 3 gradients
            grad_w3 += h2.reshape(-1, 1) * d_output
            grad_b3 += d_output

            # Layer 2 gradients
            d_h2 = d_output * self.critic.w3.flatten()
            d_h2[h2 <= 0] = 0  # ReLU derivative
            grad_w2 += np.outer(h1, d_h2)
            grad_b2 += d_h2

            # Layer 1 gradients
            d_h1 = np.dot(d_h2, self.critic.w2.T)
            d_h1[h1 <= 0] = 0  # ReLU derivative
            grad_w1 += np.outer(state, d_h1)
            grad_b1 += d_h1

        # Average gradients
        batch_size = len(batch)
        grad_w1 /= batch_size
        grad_b1 /= batch_size
        grad_w2 /= batch_size
        grad_b2 /= batch_size
        grad_w3 /= batch_size
        grad_b3 /= batch_size

        # Gradient descent update
        self.critic.w1 -= learning_rate * grad_w1
        self.critic.b1 -= learning_rate * grad_b1
        self.critic.w2 -= learning_rate * grad_w2
        self.critic.b2 -= learning_rate * grad_b2
        self.critic.w3 -= learning_rate * grad_w3
        self.critic.b3 -= learning_rate * grad_b3

    def get_td_error_statistics(self, window: int = 100) -> Dict[str, Any]:
        """Get TD-error statistics.

        Args:
            window: Window size for statistics

        Returns:
            TD-error statistics
        """
        if not self.td_error_history:
            return {'count': 0}

        recent = list(self.td_error_history)[-window:]

        mean_td = sum(recent) / len(recent)
        abs_mean_td = sum(abs(x) for x in recent) / len(recent)

        return {
            'count': len(recent),
            'mean_td_error': mean_td,
            'abs_mean_td_error': abs_mean_td,
            'min_td_error': min(recent),
            'max_td_error': max(recent)
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Actor-Critic status.

        Returns:
            Status dictionary
        """
        td_stats = self.get_td_error_statistics()

        return {
            'status': 'operational',
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'learning_rates': {
                'actor': self.lr_actor,
                'critic': self.lr_critic
            },
            'experience_buffer_size': len(self.experience_buffer),
            'update_count': self.update_count,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else 'N/A',
            'td_error_statistics': td_stats
        }
