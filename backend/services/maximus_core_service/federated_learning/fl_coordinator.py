"""
Federated Learning Coordinator (Central Server)

The coordinator manages federated learning training rounds:
- Maintains global model
- Selects clients for each round
- Receives and aggregates model updates
- Distributes updated global model
- Tracks metrics and performance

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import tempfile
import numpy as np
import random

from .base import (
    FLRound,
    ModelUpdate,
    FLConfig,
    FLMetrics,
    ClientInfo,
    FLStatus,
    AggregationStrategy,
)
from .aggregation import (
    FedAvgAggregator,
    SecureAggregator,
    DPAggregator,
    AggregationResult,
)

logger = logging.getLogger(__name__)


@dataclass
class CoordinatorConfig:
    """
    Configuration for FL coordinator.

    Attributes:
        fl_config: Federated learning configuration
        max_rounds: Maximum number of training rounds
        convergence_threshold: Accuracy improvement threshold for convergence
        min_improvement_rounds: Minimum rounds without improvement to stop
        evaluation_frequency: Evaluate global model every N rounds
        auto_save: Whether to automatically save models
        save_directory: Directory to save models
    """
    fl_config: FLConfig
    max_rounds: int = 100
    convergence_threshold: float = 0.001
    min_improvement_rounds: int = 5
    evaluation_frequency: int = 1
    auto_save: bool = True
    save_directory: str = field(default_factory=lambda: os.getenv(
        "FL_MODELS_DIR",
        tempfile.mkdtemp(prefix="fl_models_", suffix="_maximus")
    ))


class FLCoordinator:
    """
    Central coordinator for federated learning.

    Manages the entire federated learning lifecycle:
    1. Client registration and selection
    2. Round initialization
    3. Update collection and aggregation
    4. Global model distribution
    5. Convergence monitoring
    """

    def __init__(self, config: CoordinatorConfig):
        """
        Initialize FL coordinator.

        Args:
            config: Coordinator configuration
        """
        self.config = config
        self.fl_config = config.fl_config

        # Initialize state
        self.global_model_weights: Optional[Dict[str, np.ndarray]] = None
        self.current_round: Optional[FLRound] = None
        self.round_history: List[FLRound] = []
        self.registered_clients: Dict[str, ClientInfo] = {}
        self.metrics = FLMetrics()

        # Initialize aggregator based on strategy
        self.aggregator = self._create_aggregator()

        # Convergence tracking
        self.best_accuracy = 0.0
        self.rounds_without_improvement = 0

        logger.info(
            f"FL Coordinator initialized with {config.fl_config.model_type.value} "
            f"using {config.fl_config.aggregation_strategy.value}"
        )

    def _create_aggregator(self):
        """Create aggregator based on configuration."""
        strategy = self.fl_config.aggregation_strategy

        if strategy == AggregationStrategy.FEDAVG:
            return FedAvgAggregator()
        elif strategy == AggregationStrategy.SECURE:
            return SecureAggregator(threshold=self.fl_config.min_clients)
        elif strategy == AggregationStrategy.DP_FEDAVG:
            return DPAggregator(
                epsilon=self.fl_config.dp_epsilon,
                delta=self.fl_config.dp_delta,
                clip_norm=self.fl_config.dp_clip_norm,
            )
        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")

    def register_client(self, client_info: ClientInfo) -> bool:
        """
        Register a new client.

        Args:
            client_info: Information about the client

        Returns:
            True if registration successful
        """
        if client_info.client_id in self.registered_clients:
            logger.warning(
                f"Client {client_info.client_id} already registered, updating info"
            )

        self.registered_clients[client_info.client_id] = client_info
        self.metrics.total_clients = len(self.registered_clients)
        self.metrics.active_clients = sum(
            1 for c in self.registered_clients.values() if c.active
        )

        logger.info(
            f"Registered client {client_info.client_id} "
            f"({client_info.organization}) with {client_info.total_samples} samples"
        )

        return True

    def unregister_client(self, client_id: str) -> bool:
        """
        Unregister a client.

        Args:
            client_id: ID of client to unregister

        Returns:
            True if unregistration successful
        """
        if client_id not in self.registered_clients:
            logger.warning(f"Cannot unregister unknown client {client_id}")
            return False

        del self.registered_clients[client_id]
        self.metrics.total_clients = len(self.registered_clients)
        self.metrics.active_clients = sum(
            1 for c in self.registered_clients.values() if c.active
        )

        logger.info(f"Unregistered client {client_id}")
        return True

    def set_global_model(self, weights: Dict[str, np.ndarray]) -> None:
        """
        Set the initial global model weights.

        Args:
            weights: Initial model weights
        """
        self.global_model_weights = weights
        logger.info(
            f"Set global model with {sum(w.size for w in weights.values())} "
            "parameters"
        )

    def get_global_model(self) -> Optional[Dict[str, np.ndarray]]:
        """
        Get current global model weights.

        Returns:
            Global model weights (None if not initialized)
        """
        return self.global_model_weights

    def start_round(self) -> FLRound:
        """
        Start a new federated learning round.

        Returns:
            FLRound object for the new round

        Raises:
            RuntimeError: If conditions not met (e.g., not enough clients)
        """
        # Check if we can start a round
        if self.current_round and self.current_round.status in [
            FLStatus.WAITING_FOR_CLIENTS,
            FLStatus.TRAINING,
            FLStatus.AGGREGATING,
        ]:
            raise RuntimeError(
                f"Cannot start new round: current round {self.current_round.round_id} "
                f"is still {self.current_round.status.value}"
            )

        if self.global_model_weights is None:
            raise RuntimeError("Global model not initialized")

        active_clients = [
            client_id for client_id, info in self.registered_clients.items()
            if info.active
        ]

        if len(active_clients) < self.fl_config.min_clients:
            raise RuntimeError(
                f"Not enough active clients: {len(active_clients)} < "
                f"{self.fl_config.min_clients}"
            )

        # Select clients for this round
        selected_clients = self._select_clients(active_clients)

        # Create new round
        round_id = len(self.round_history) + 1
        self.current_round = FLRound(
            round_id=round_id,
            status=FLStatus.WAITING_FOR_CLIENTS,
            config=self.fl_config,
            selected_clients=selected_clients,
            global_model_version=self.fl_config.model_version,
        )

        logger.info(
            f"Started round {round_id} with {len(selected_clients)} clients: "
            f"{selected_clients}"
        )

        return self.current_round

    def _select_clients(self, active_clients: List[str]) -> List[str]:
        """
        Select clients for the current round.

        Args:
            active_clients: List of active client IDs

        Returns:
            List of selected client IDs
        """
        # Calculate number of clients to select
        num_to_select = min(
            int(len(active_clients) * self.fl_config.client_fraction),
            self.fl_config.max_clients,
        )
        num_to_select = max(num_to_select, self.fl_config.min_clients)

        # Random sampling without replacement
        selected = random.sample(active_clients, num_to_select)

        return selected

    def receive_update(self, update: ModelUpdate) -> bool:
        """
        Receive a model update from a client.

        Args:
            update: Model update from client

        Returns:
            True if update accepted

        Raises:
            RuntimeError: If no round in progress or update invalid
        """
        if self.current_round is None:
            raise RuntimeError("No round in progress")

        if self.current_round.status not in [
            FLStatus.WAITING_FOR_CLIENTS,
            FLStatus.TRAINING,
        ]:
            raise RuntimeError(
                f"Round {self.current_round.round_id} not accepting updates: "
                f"{self.current_round.status.value}"
            )

        # Validate update
        if update.client_id not in self.current_round.selected_clients:
            raise RuntimeError(
                f"Client {update.client_id} not selected for round "
                f"{self.current_round.round_id}"
            )

        if update.round_id != self.current_round.round_id:
            raise RuntimeError(
                f"Update round ID {update.round_id} != current round "
                f"{self.current_round.round_id}"
            )

        # Check for duplicate
        if any(u.client_id == update.client_id for u in self.current_round.received_updates):
            logger.warning(
                f"Duplicate update from client {update.client_id}, replacing"
            )
            self.current_round.received_updates = [
                u for u in self.current_round.received_updates
                if u.client_id != update.client_id
            ]

        # Add update
        self.current_round.received_updates.append(update)
        self.current_round.status = FLStatus.TRAINING

        logger.info(
            f"Received update from {update.client_id} "
            f"({update.num_samples} samples, {update.computation_time:.1f}s) - "
            f"{len(self.current_round.received_updates)}/"
            f"{len(self.current_round.selected_clients)} received"
        )

        # Check if we have enough updates to aggregate
        if len(self.current_round.received_updates) >= self.fl_config.min_clients:
            logger.info(
                f"Minimum updates received ({self.fl_config.min_clients}), "
                "ready to aggregate"
            )

        return True

    def aggregate_updates(self) -> AggregationResult:
        """
        Aggregate received updates into global model.

        Returns:
            AggregationResult with aggregated weights

        Raises:
            RuntimeError: If not enough updates received
        """
        if self.current_round is None:
            raise RuntimeError("No round in progress")

        if len(self.current_round.received_updates) < self.fl_config.min_clients:
            raise RuntimeError(
                f"Not enough updates: {len(self.current_round.received_updates)} < "
                f"{self.fl_config.min_clients}"
            )

        # Update status
        self.current_round.status = FLStatus.AGGREGATING

        logger.info(
            f"Aggregating {len(self.current_round.received_updates)} updates "
            f"for round {self.current_round.round_id}"
        )

        # Aggregate using configured strategy
        agg_result = self.aggregator.aggregate(self.current_round.received_updates)

        # Update global model
        self.global_model_weights = agg_result.aggregated_weights
        self.fl_config.model_version += 1

        # Store aggregation result
        self.current_round.aggregation_result = agg_result.to_dict()
        self.current_round.metrics = agg_result.metadata.get(
            "average_client_metrics", {}
        )

        logger.info(
            f"Aggregation complete: {agg_result.num_clients} clients, "
            f"{agg_result.total_samples} samples, "
            f"{agg_result.aggregation_time:.2f}s"
        )

        return agg_result

    def complete_round(self) -> FLRound:
        """
        Complete the current round.

        Returns:
            Completed FLRound object

        Raises:
            RuntimeError: If no round in progress or aggregation not done
        """
        if self.current_round is None:
            raise RuntimeError("No round in progress")

        if self.current_round.aggregation_result is None:
            raise RuntimeError("Cannot complete round: aggregation not done")

        # Mark as completed
        self.current_round.status = FLStatus.COMPLETED
        self.current_round.end_time = datetime.utcnow()

        # Add to history
        self.round_history.append(self.current_round)

        # Update metrics
        self._update_metrics()

        completed_round = self.current_round
        self.current_round = None

        logger.info(
            f"Round {completed_round.round_id} completed in "
            f"{completed_round.get_duration_seconds():.1f}s - "
            f"participation: {completed_round.get_participation_rate():.1%}"
        )

        return completed_round

    def _update_metrics(self) -> None:
        """Update coordinator metrics after round completion."""
        if not self.round_history:
            return

        self.metrics.total_rounds = len(self.round_history)

        # Calculate average participation rate
        participation_rates = [
            r.get_participation_rate() for r in self.round_history
        ]
        self.metrics.average_participation_rate = np.mean(participation_rates)

        # Calculate average round duration
        durations = [
            r.get_duration_seconds() for r in self.round_history
            if r.get_duration_seconds() is not None
        ]
        if durations:
            self.metrics.average_round_duration = np.mean(durations)

        # Total samples trained
        self.metrics.total_samples_trained = sum(
            r.get_total_samples() for r in self.round_history
        )

        # Update timestamp
        self.metrics.last_updated = datetime.utcnow()

    def evaluate_global_model(
        self, test_data: Any, test_labels: Any, model_adapter: Any
    ) -> Dict[str, float]:
        """
        Evaluate global model on test set.

        Args:
            test_data: Test dataset
            test_labels: Test labels
            model_adapter: Model adapter for evaluation

        Returns:
            Dictionary of evaluation metrics
        """
        if self.global_model_weights is None:
            raise RuntimeError("Global model not initialized")

        logger.info("Evaluating global model on test set")

        # Set model weights
        model_adapter.set_weights(self.global_model_weights)

        # Evaluate
        eval_metrics = model_adapter.evaluate(test_data, test_labels)

        # Update metrics
        self.metrics.global_model_accuracy = eval_metrics.get("accuracy", 0.0)

        # Check for convergence
        accuracy = eval_metrics.get("accuracy", 0.0)
        improvement = accuracy - self.best_accuracy

        if improvement > self.config.convergence_threshold:
            self.best_accuracy = accuracy
            self.rounds_without_improvement = 0
            logger.info(f"New best accuracy: {accuracy:.4f} (+{improvement:.4f})")
        else:
            self.rounds_without_improvement += 1
            logger.info(
                f"No improvement: {accuracy:.4f} "
                f"({self.rounds_without_improvement} rounds)"
            )

        # Check convergence
        if self.rounds_without_improvement >= self.config.min_improvement_rounds:
            self.metrics.convergence_status = True
            logger.info(
                f"Model converged after {self.metrics.total_rounds} rounds "
                f"(accuracy: {self.best_accuracy:.4f})"
            )

        return eval_metrics

    def has_converged(self) -> bool:
        """Check if training has converged."""
        return self.metrics.convergence_status

    def should_stop(self) -> bool:
        """
        Check if training should stop.

        Returns:
            True if max rounds reached or model converged
        """
        if self.metrics.total_rounds >= self.config.max_rounds:
            logger.info(f"Max rounds ({self.config.max_rounds}) reached")
            return True

        if self.has_converged():
            logger.info("Model has converged")
            return True

        return False

    def get_metrics(self) -> FLMetrics:
        """Get current FL metrics."""
        return self.metrics

    def get_round_status(self) -> Optional[Dict[str, Any]]:
        """
        Get status of current round.

        Returns:
            Dictionary with round status (None if no round in progress)
        """
        if self.current_round is None:
            return None

        return {
            "round_id": self.current_round.round_id,
            "status": self.current_round.status.value,
            "selected_clients": self.current_round.selected_clients,
            "received_updates": len(self.current_round.received_updates),
            "expected_updates": len(self.current_round.selected_clients),
            "progress": (
                len(self.current_round.received_updates) /
                len(self.current_round.selected_clients)
            ),
            "elapsed_time": (
                (datetime.utcnow() - self.current_round.start_time).total_seconds()
            ),
        }
