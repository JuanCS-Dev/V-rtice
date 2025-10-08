"""
Federated Learning Client (On-Premise)

The FL client runs on each organization's infrastructure and:
- Downloads global model from coordinator
- Trains on local private data
- Computes model update (gradients/weights)
- Sends update to coordinator
- Optionally applies differential privacy

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import copy
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

from .base import (
    ClientInfo,
    FLConfig,
    ModelUpdate,
)

logger = logging.getLogger(__name__)


@dataclass
class ClientConfig:
    """
    Configuration for FL client.

    Attributes:
        client_id: Unique identifier for this client
        organization: Organization name
        coordinator_url: URL of the FL coordinator server
        local_data_path: Path to local training data
        use_gpu: Whether to use GPU for training
        max_memory_mb: Maximum memory usage (MB)
        apply_dp_locally: Whether to apply DP before sending update
        dp_epsilon: Privacy budget for local DP
        dp_delta: Failure probability for local DP
        dp_clip_norm: Gradient clipping norm
    """

    client_id: str
    organization: str
    coordinator_url: str
    local_data_path: str = "/data/threats"
    use_gpu: bool = False
    max_memory_mb: int = 4096
    apply_dp_locally: bool = False
    dp_epsilon: float = 8.0
    dp_delta: float = 1e-5
    dp_clip_norm: float = 1.0


class FLClient:
    """
    Federated learning client for on-premise training.

    The client:
    1. Fetches global model from coordinator
    2. Trains model on local data (data never leaves premises)
    3. Computes update (gradients or weight difference)
    4. Optionally applies differential privacy
    5. Sends update to coordinator
    """

    def __init__(self, config: ClientConfig, model_adapter: Any):
        """
        Initialize FL client.

        Args:
            config: Client configuration
            model_adapter: Model adapter for training
        """
        self.config = config
        self.model_adapter = model_adapter

        # Client state
        self.client_info = ClientInfo(
            client_id=config.client_id,
            organization=config.organization,
            client_version="1.0.0",
            capabilities={
                "gpu": config.use_gpu,
                "max_memory_mb": config.max_memory_mb,
            },
        )

        self.current_round_id: int | None = None
        self.global_model_weights: dict[str, np.ndarray] | None = None
        self.initial_weights: dict[str, np.ndarray] | None = None

        logger.info(f"FL Client initialized: {config.client_id} ({config.organization})")

    def fetch_global_model(self, round_id: int, global_weights: dict[str, np.ndarray]) -> bool:
        """
        Fetch global model from coordinator.

        In a real implementation, this would make an HTTP request to the
        coordinator. Here we simulate by directly accepting the weights.

        Args:
            round_id: Current round ID
            global_weights: Global model weights

        Returns:
            True if fetch successful
        """
        self.current_round_id = round_id
        self.global_model_weights = global_weights
        self.initial_weights = copy.deepcopy(global_weights)

        # Set weights in model adapter
        self.model_adapter.set_weights(global_weights)

        logger.info(
            f"Fetched global model for round {round_id} ({sum(w.size for w in global_weights.values())} parameters)"
        )

        return True

    def train_local_model(
        self,
        train_data: Any,
        train_labels: Any,
        fl_config: FLConfig,
        validation_split: float = 0.1,
    ) -> dict[str, float]:
        """
        Train model on local private data.

        Args:
            train_data: Local training data
            train_labels: Local training labels
            fl_config: FL configuration (epochs, batch size, etc.)
            validation_split: Fraction of data for validation

        Returns:
            Training metrics (loss, accuracy, etc.)
        """
        if self.global_model_weights is None:
            raise RuntimeError("Global model not fetched")

        logger.info(
            f"Training local model for {fl_config.local_epochs} epochs "
            f"(batch_size={fl_config.local_batch_size}, "
            f"lr={fl_config.learning_rate})"
        )

        start_time = datetime.utcnow()

        # Train using model adapter
        training_metrics = self.model_adapter.train_epochs(
            train_data=train_data,
            train_labels=train_labels,
            epochs=fl_config.local_epochs,
            batch_size=fl_config.local_batch_size,
            learning_rate=fl_config.learning_rate,
            validation_split=validation_split,
        )

        training_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"Local training completed in {training_time:.1f}s - "
            f"loss: {training_metrics.get('loss', 0.0):.4f}, "
            f"accuracy: {training_metrics.get('accuracy', 0.0):.4f}"
        )

        training_metrics["training_time"] = training_time

        return training_metrics

    def compute_update(
        self,
        num_samples: int,
        training_metrics: dict[str, float],
    ) -> ModelUpdate:
        """
        Compute model update to send to coordinator.

        The update is the difference between trained weights and initial
        global weights.

        Args:
            num_samples: Number of samples used for training
            training_metrics: Metrics from training

        Returns:
            ModelUpdate object
        """
        if self.current_round_id is None:
            raise RuntimeError("No round in progress")
        if self.initial_weights is None:
            raise RuntimeError("Initial weights not saved")

        # Get current weights after training
        current_weights = self.model_adapter.get_weights()

        # Compute weight update (difference)
        # In FedAvg, clients send full weights, not deltas
        # But we could also send deltas: Δw = w_new - w_old
        update_weights = current_weights

        # Apply local differential privacy if configured
        if self.config.apply_dp_locally:
            update_weights = self._apply_local_dp(update_weights)

        # Create model update
        update = ModelUpdate(
            client_id=self.config.client_id,
            round_id=self.current_round_id,
            weights=update_weights,
            num_samples=num_samples,
            metrics=training_metrics,
            differential_privacy_applied=self.config.apply_dp_locally,
            epsilon_used=self.config.dp_epsilon if self.config.apply_dp_locally else 0.0,
            computation_time=training_metrics.get("training_time", 0.0),
        )

        logger.info(
            f"Computed update for round {self.current_round_id}: "
            f"{num_samples} samples, {update.get_update_size_mb():.1f} MB"
        )

        return update

    def _apply_local_dp(self, weights: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """
        Apply differential privacy to model update.

        Uses Gaussian mechanism:
        1. Clip gradient to bounded L2 norm
        2. Add Gaussian noise calibrated to (ε, δ)

        Args:
            weights: Model weights

        Returns:
            DP-protected weights
        """
        logger.info(
            f"Applying local DP (ε={self.config.dp_epsilon}, δ={self.config.dp_delta}, clip={self.config.dp_clip_norm})"
        )

        # Calculate current L2 norm
        l2_norm = np.sqrt(sum(np.sum(w**2) for w in weights.values()))

        # Clip to bounded norm
        if l2_norm > self.config.dp_clip_norm:
            scaling_factor = self.config.dp_clip_norm / l2_norm
            clipped_weights = {layer: w * scaling_factor for layer, w in weights.items()}
            logger.debug(f"Clipped weights: {l2_norm:.4f} -> {self.config.dp_clip_norm:.4f}")
        else:
            clipped_weights = weights

        # Add Gaussian noise
        sensitivity = self.config.dp_clip_norm
        noise_scale = (sensitivity * np.sqrt(2 * np.log(1.25 / self.config.dp_delta))) / self.config.dp_epsilon

        noisy_weights = {}
        for layer, w in clipped_weights.items():
            noise = np.random.normal(0, noise_scale, size=w.shape)
            noisy_weights[layer] = w + noise

        logger.debug(f"Added Gaussian noise with scale σ={noise_scale:.4f}")

        return noisy_weights

    def send_update(self, update: ModelUpdate, coordinator: Any = None) -> bool:
        """
        Send model update to coordinator.

        In a real implementation, this would make an HTTP POST request.
        For testing, we can directly call coordinator.receive_update().

        Args:
            update: Model update to send
            coordinator: Coordinator object (for testing)

        Returns:
            True if send successful
        """
        logger.info(f"Sending update to coordinator: {update.get_update_size_mb():.1f} MB")

        # In real implementation:
        # response = requests.post(
        #     f"{self.config.coordinator_url}/submit-update",
        #     json=update.to_dict(include_weights=True)
        # )

        # For testing, directly call coordinator
        if coordinator:
            try:
                coordinator.receive_update(update)
                logger.info("Update sent successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to send update: {e}")
                return False
        else:
            logger.warning("No coordinator provided, update not sent")
            return False

    def participate_in_round(
        self,
        round_id: int,
        global_weights: dict[str, np.ndarray],
        train_data: Any,
        train_labels: Any,
        fl_config: FLConfig,
        coordinator: Any = None,
    ) -> tuple[bool, ModelUpdate | None]:
        """
        Participate in a federated learning round.

        Complete workflow:
        1. Fetch global model
        2. Train on local data
        3. Compute update
        4. Send to coordinator

        Args:
            round_id: Round ID
            global_weights: Global model weights
            train_data: Local training data
            train_labels: Local training labels
            fl_config: FL configuration
            coordinator: Coordinator object (optional)

        Returns:
            Tuple of (success, update)
        """
        try:
            # Step 1: Fetch global model
            self.fetch_global_model(round_id, global_weights)

            # Step 2: Train local model
            training_metrics = self.train_local_model(train_data, train_labels, fl_config)

            # Step 3: Compute update
            num_samples = len(train_data) if hasattr(train_data, "__len__") else train_data.shape[0]
            update = self.compute_update(num_samples, training_metrics)

            # Step 4: Send update
            if coordinator:
                success = self.send_update(update, coordinator)
            else:
                success = True  # Simulated success

            if success:
                logger.info(f"Successfully participated in round {round_id}")
            else:
                logger.error(f"Failed to participate in round {round_id}")

            return success, update

        except Exception as e:
            logger.error(f"Error participating in round {round_id}: {e}")
            return False, None

    def get_client_info(self) -> ClientInfo:
        """Get client information."""
        return self.client_info

    def update_client_info(self, total_samples: int) -> None:
        """
        Update client information.

        Args:
            total_samples: Total number of samples available locally
        """
        self.client_info.total_samples = total_samples
        self.client_info.last_seen = datetime.utcnow()
        logger.info(f"Updated client info: {total_samples} samples available")
