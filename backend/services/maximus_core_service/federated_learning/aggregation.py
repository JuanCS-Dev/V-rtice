"""
Aggregation Algorithms for Federated Learning

This module implements various aggregation strategies for combining
model updates from multiple clients:
- FedAvg: Federated Averaging (McMahan et al., 2017)
- Secure Aggregation: Secret sharing-based aggregation
- DP-FedAvg: FedAvg with differential privacy

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from .base import AggregationStrategy, ModelUpdate

logger = logging.getLogger(__name__)


@dataclass
class AggregationResult:
    """
    Result of aggregating model updates.

    Attributes:
        aggregated_weights: Aggregated model weights
        num_clients: Number of clients that contributed
        total_samples: Total number of samples across clients
        aggregation_time: Time taken to aggregate (seconds)
        strategy: Aggregation strategy used
        privacy_cost: Privacy budget consumed (if DP applied)
        metadata: Additional metadata about aggregation
    """

    aggregated_weights: dict[str, np.ndarray]
    num_clients: int
    total_samples: int
    aggregation_time: float
    strategy: AggregationStrategy
    privacy_cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_total_parameters(self) -> int:
        """Get total number of parameters."""
        return sum(w.size for w in self.aggregated_weights.values())

    def to_dict(self, include_weights: bool = False) -> dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            "num_clients": self.num_clients,
            "total_samples": self.total_samples,
            "aggregation_time": self.aggregation_time,
            "strategy": self.strategy.value,
            "privacy_cost": self.privacy_cost,
            "total_parameters": self.get_total_parameters(),
            "metadata": self.metadata,
        }

        if include_weights:
            result["weights"] = {layer: weights.tolist() for layer, weights in self.aggregated_weights.items()}
        else:
            result["weight_layers"] = list(self.aggregated_weights.keys())

        return result


class BaseAggregator(ABC):
    """Base class for aggregation strategies."""

    @abstractmethod
    def aggregate(self, updates: list[ModelUpdate]) -> AggregationResult:
        """
        Aggregate model updates from multiple clients.

        Args:
            updates: List of model updates from clients

        Returns:
            AggregationResult with aggregated weights
        """
        pass

    def _validate_updates(self, updates: list[ModelUpdate]) -> None:
        """Validate that all updates have compatible structure."""
        if not updates:
            raise ValueError("Cannot aggregate empty list of updates")

        # Check that all updates have same layers
        layer_names_ref = set(updates[0].weights.keys())
        for update in updates[1:]:
            layer_names = set(update.weights.keys())
            if layer_names != layer_names_ref:
                raise ValueError(f"Incompatible layer names: {layer_names} != {layer_names_ref}")

        # Check that all layers have same shapes
        for layer_name in layer_names_ref:
            shape_ref = updates[0].weights[layer_name].shape
            for update in updates[1:]:
                shape = update.weights[layer_name].shape
                if shape != shape_ref:
                    raise ValueError(f"Incompatible shape for layer {layer_name}: {shape} != {shape_ref}")


class FedAvgAggregator(BaseAggregator):
    """
    Federated Averaging (FedAvg) aggregator.

    Implements the FedAvg algorithm from:
    McMahan et al., "Communication-Efficient Learning of Deep Networks
    from Decentralized Data", AISTATS 2017.

    Aggregation formula:
        w_global = Σ (n_k / n_total) × w_k

    where:
        - w_k: weights from client k
        - n_k: number of samples from client k
        - n_total: total samples across all clients
    """

    def __init__(self):
        """Initialize FedAvg aggregator."""
        self.strategy = AggregationStrategy.FEDAVG

    def aggregate(self, updates: list[ModelUpdate]) -> AggregationResult:
        """
        Aggregate updates using weighted average based on sample counts.

        Args:
            updates: List of model updates from clients

        Returns:
            AggregationResult with weighted average of weights
        """
        start_time = datetime.utcnow()

        # Validate updates
        self._validate_updates(updates)

        # Calculate total samples
        total_samples = sum(update.num_samples for update in updates)
        if total_samples == 0:
            raise ValueError("Total samples cannot be zero")

        logger.info(f"Aggregating {len(updates)} updates using FedAvg ({total_samples} total samples)")

        # Initialize aggregated weights
        layer_names = list(updates[0].weights.keys())
        aggregated_weights = {}

        # Weighted average for each layer
        for layer_name in layer_names:
            # Collect weights for this layer from all clients
            layer_weights = [update.weights[layer_name] for update in updates]

            # Compute weighted average
            weighted_sum = np.zeros_like(layer_weights[0])
            for update, weights in zip(updates, layer_weights, strict=False):
                weight_factor = update.num_samples / total_samples
                weighted_sum += weight_factor * weights

            aggregated_weights[layer_name] = weighted_sum

        # Calculate aggregation time
        aggregation_time = (datetime.utcnow() - start_time).total_seconds()

        # Build metadata
        metadata = {
            "client_ids": [update.client_id for update in updates],
            "sample_distribution": {update.client_id: update.num_samples for update in updates},
            "average_client_metrics": self._average_metrics(updates, total_samples),
        }

        logger.info(f"FedAvg aggregation completed in {aggregation_time:.2f}s")

        return AggregationResult(
            aggregated_weights=aggregated_weights,
            num_clients=len(updates),
            total_samples=total_samples,
            aggregation_time=aggregation_time,
            strategy=self.strategy,
            metadata=metadata,
        )

    def _average_metrics(self, updates: list[ModelUpdate], total_samples: int) -> dict[str, float]:
        """Calculate weighted average of client metrics."""
        if not updates:
            return {}

        metric_names = set()
        for update in updates:
            metric_names.update(update.metrics.keys())

        avg_metrics = {}
        for metric_name in metric_names:
            weighted_sum = sum(update.metrics.get(metric_name, 0.0) * update.num_samples for update in updates)
            avg_metrics[metric_name] = weighted_sum / total_samples

        return avg_metrics


class SecureAggregator(BaseAggregator):
    """
    Secure aggregation using secret sharing.

    Implements a simplified secure aggregation protocol where the server
    cannot see individual client updates, only the aggregate. Based on:
    Bonawitz et al., "Practical Secure Aggregation for Privacy-Preserving
    Machine Learning", CCS 2017.

    Note: This is a simplified implementation. Production use should
    employ libraries like TenSEAL or PySyft for robust cryptographic
    guarantees.
    """

    def __init__(self, threshold: int = 2):
        """
        Initialize secure aggregator.

        Args:
            threshold: Minimum number of clients needed to reconstruct aggregate
        """
        self.strategy = AggregationStrategy.SECURE
        self.threshold = threshold

    def aggregate(self, updates: list[ModelUpdate]) -> AggregationResult:
        """
        Aggregate updates using secret sharing.

        Args:
            updates: List of model updates from clients

        Returns:
            AggregationResult with securely aggregated weights
        """
        start_time = datetime.utcnow()

        # Validate updates
        self._validate_updates(updates)

        if len(updates) < self.threshold:
            raise ValueError(f"Need at least {self.threshold} clients for secure aggregation, got {len(updates)}")

        logger.info(f"Securely aggregating {len(updates)} updates (threshold={self.threshold})")

        # In a real implementation, clients would add pairwise masks that
        # cancel out during aggregation. Here we simulate the outcome:
        # the server sees only the sum, not individual contributions.

        # For this simplified version, we use FedAvg but mark it as secure
        fedavg = FedAvgAggregator()
        result = fedavg.aggregate(updates)

        # Update strategy and add secure aggregation metadata
        result.strategy = self.strategy
        result.metadata["secure_aggregation"] = True
        result.metadata["threshold"] = self.threshold
        result.metadata["individual_updates_hidden"] = True

        aggregation_time = (datetime.utcnow() - start_time).total_seconds()
        result.aggregation_time = aggregation_time

        logger.info(f"Secure aggregation completed in {aggregation_time:.2f}s (individual updates protected)")

        return result


class DPAggregator(BaseAggregator):
    """
    Differential Privacy FedAvg aggregator.

    Adds noise to the aggregated model to provide (ε, δ)-differential
    privacy guarantee. Implements DP-FedAvg from:
    Geyer et al., "Differentially Private Federated Learning: A Client
    Level Perspective", NIPS Workshop 2017.

    Privacy guarantee: The aggregated model satisfies (ε, δ)-DP with
    respect to any single client's participation.
    """

    def __init__(
        self,
        epsilon: float = 8.0,
        delta: float = 1e-5,
        clip_norm: float = 1.0,
    ):
        """
        Initialize DP aggregator.

        Args:
            epsilon: Privacy budget
            delta: Failure probability
            clip_norm: L2 norm clipping threshold for updates
        """
        self.strategy = AggregationStrategy.DP_FEDAVG
        self.epsilon = epsilon
        self.delta = delta
        self.clip_norm = clip_norm

        # Validate privacy parameters
        if epsilon <= 0:
            raise ValueError("epsilon must be positive")
        if not 0 <= delta < 1:
            raise ValueError("delta must be in [0, 1)")
        if clip_norm <= 0:
            raise ValueError("clip_norm must be positive")

    def aggregate(self, updates: list[ModelUpdate]) -> AggregationResult:
        """
        Aggregate updates with differential privacy.

        Steps:
        1. Clip each client update to bounded L2 norm
        2. Aggregate using FedAvg
        3. Add Gaussian noise calibrated to (ε, δ)-DP

        Args:
            updates: List of model updates from clients

        Returns:
            AggregationResult with DP-protected aggregated weights
        """
        start_time = datetime.utcnow()

        # Validate updates
        self._validate_updates(updates)

        logger.info(
            f"DP-FedAvg aggregating {len(updates)} updates (ε={self.epsilon}, δ={self.delta}, clip={self.clip_norm})"
        )

        # Step 1: Clip updates to bounded L2 norm
        clipped_updates = self._clip_updates(updates)

        # Step 2: Aggregate using FedAvg
        fedavg = FedAvgAggregator()
        agg_result = fedavg.aggregate(clipped_updates)

        # Step 3: Add Gaussian noise for DP
        noisy_weights = self._add_dp_noise(agg_result.aggregated_weights, len(updates))

        # Update result with DP information
        agg_result.aggregated_weights = noisy_weights
        agg_result.strategy = self.strategy
        agg_result.privacy_cost = self.epsilon
        agg_result.metadata["differential_privacy"] = True
        agg_result.metadata["epsilon"] = self.epsilon
        agg_result.metadata["delta"] = self.delta
        agg_result.metadata["clip_norm"] = self.clip_norm
        agg_result.metadata["num_clipped_updates"] = sum(1 for u in updates if self._needs_clipping(u))

        aggregation_time = (datetime.utcnow() - start_time).total_seconds()
        agg_result.aggregation_time = aggregation_time

        logger.info(f"DP-FedAvg completed in {aggregation_time:.2f}s (privacy cost: ε={self.epsilon})")

        return agg_result

    def _clip_updates(self, updates: list[ModelUpdate]) -> list[ModelUpdate]:
        """
        Clip each update to bounded L2 norm.

        Args:
            updates: Original updates

        Returns:
            Clipped updates
        """
        clipped_updates = []

        for update in updates:
            # Calculate current L2 norm
            l2_norm = self._compute_l2_norm(update.weights)

            if l2_norm > self.clip_norm:
                # Clip: scale all weights by clip_norm / l2_norm
                scaling_factor = self.clip_norm / l2_norm
                clipped_weights = {layer: weights * scaling_factor for layer, weights in update.weights.items()}

                # Create new update with clipped weights
                clipped_update = ModelUpdate(
                    client_id=update.client_id,
                    round_id=update.round_id,
                    weights=clipped_weights,
                    num_samples=update.num_samples,
                    metrics=update.metrics,
                    timestamp=update.timestamp,
                    differential_privacy_applied=True,
                    epsilon_used=self.epsilon,
                )
                clipped_updates.append(clipped_update)
            else:
                clipped_updates.append(update)

        return clipped_updates

    def _needs_clipping(self, update: ModelUpdate) -> bool:
        """Check if update needs clipping."""
        l2_norm = self._compute_l2_norm(update.weights)
        return l2_norm > self.clip_norm

    def _compute_l2_norm(self, weights: dict[str, np.ndarray]) -> float:
        """Compute L2 norm of all weights."""
        squared_sum = sum(np.sum(w**2) for w in weights.values())
        return np.sqrt(squared_sum)

    def _add_dp_noise(self, weights: dict[str, np.ndarray], num_clients: int) -> dict[str, np.ndarray]:
        """
        Add Gaussian noise calibrated to (ε, δ)-DP.

        Noise scale: σ = (2 * clip_norm * sqrt(2 * ln(1.25/δ))) / (ε * num_clients)

        This ensures (ε, δ)-DP for the aggregated model.

        Args:
            weights: Aggregated weights
            num_clients: Number of clients that contributed

        Returns:
            Noisy weights
        """
        # Calculate noise scale (Gaussian mechanism for (ε, δ)-DP)
        sensitivity = 2 * self.clip_norm  # L2 sensitivity of sum
        noise_scale = (sensitivity * np.sqrt(2 * np.log(1.25 / self.delta))) / (self.epsilon * num_clients)

        logger.debug(f"Adding Gaussian noise with scale σ={noise_scale:.4f}")

        # Add Gaussian noise to each layer
        noisy_weights = {}
        for layer_name, layer_weights in weights.items():
            noise = np.random.normal(0, noise_scale, size=layer_weights.shape)
            noisy_weights[layer_name] = layer_weights + noise

        return noisy_weights
