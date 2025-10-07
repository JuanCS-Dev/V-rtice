"""
Base Classes and Data Structures for Federated Learning

This module provides foundational classes and enums for the federated
learning framework.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional
import numpy as np


class FLStatus(Enum):
    """Federated learning round status."""
    INITIALIZING = "initializing"
    WAITING_FOR_CLIENTS = "waiting_for_clients"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"


class AggregationStrategy(Enum):
    """Aggregation strategy for federated learning."""
    FEDAVG = "fedavg"  # Federated Averaging (McMahan et al., 2017)
    SECURE = "secure"  # Secure aggregation with secret sharing
    DP_FEDAVG = "dp_fedavg"  # FedAvg with differential privacy
    WEIGHTED = "weighted"  # Weighted averaging by client data size


class ModelType(Enum):
    """Supported model types for federated learning."""
    THREAT_CLASSIFIER = "threat_classifier"  # narrative_manipulation_filter
    MALWARE_DETECTOR = "malware_detector"  # immunis_macrophage_service
    CUSTOM = "custom"


@dataclass
class FLConfig:
    """
    Configuration for federated learning.

    Attributes:
        model_type: Type of model to train
        aggregation_strategy: Strategy for aggregating updates
        min_clients: Minimum number of clients required per round
        max_clients: Maximum number of clients per round
        client_fraction: Fraction of clients to sample per round (0.0-1.0)
        local_epochs: Number of local training epochs per round
        local_batch_size: Batch size for local training
        learning_rate: Learning rate for local training
        use_differential_privacy: Whether to apply DP to updates
        dp_epsilon: Privacy budget (if DP enabled)
        dp_delta: Failure probability (if DP enabled)
        dp_clip_norm: Gradient clipping norm (if DP enabled)
        use_secure_aggregation: Whether to use secure aggregation
        communication_timeout: Timeout for client communication (seconds)
        model_version: Current global model version
    """
    model_type: ModelType
    aggregation_strategy: AggregationStrategy = AggregationStrategy.FEDAVG
    min_clients: int = 3
    max_clients: int = 100
    client_fraction: float = 1.0
    local_epochs: int = 5
    local_batch_size: int = 32
    learning_rate: float = 0.001
    use_differential_privacy: bool = False
    dp_epsilon: float = 8.0
    dp_delta: float = 1e-5
    dp_clip_norm: float = 1.0
    use_secure_aggregation: bool = False
    communication_timeout: int = 600  # 10 minutes
    model_version: int = 0

    def __post_init__(self):
        """Validate configuration."""
        if self.min_clients < 1:
            raise ValueError("min_clients must be at least 1")
        if self.max_clients < self.min_clients:
            raise ValueError("max_clients must be >= min_clients")
        if not 0.0 < self.client_fraction <= 1.0:
            raise ValueError("client_fraction must be in (0.0, 1.0]")
        if self.local_epochs < 1:
            raise ValueError("local_epochs must be at least 1")
        if self.local_batch_size < 1:
            raise ValueError("local_batch_size must be at least 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if self.use_differential_privacy:
            if self.dp_epsilon <= 0:
                raise ValueError("dp_epsilon must be positive")
            if not 0 <= self.dp_delta < 1:
                raise ValueError("dp_delta must be in [0, 1)")
            if self.dp_clip_norm <= 0:
                raise ValueError("dp_clip_norm must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "model_type": self.model_type.value,
            "aggregation_strategy": self.aggregation_strategy.value,
            "min_clients": self.min_clients,
            "max_clients": self.max_clients,
            "client_fraction": self.client_fraction,
            "local_epochs": self.local_epochs,
            "local_batch_size": self.local_batch_size,
            "learning_rate": self.learning_rate,
            "use_differential_privacy": self.use_differential_privacy,
            "dp_epsilon": self.dp_epsilon,
            "dp_delta": self.dp_delta,
            "dp_clip_norm": self.dp_clip_norm,
            "use_secure_aggregation": self.use_secure_aggregation,
            "communication_timeout": self.communication_timeout,
            "model_version": self.model_version,
        }


@dataclass
class ClientInfo:
    """
    Information about a federated learning client.

    Attributes:
        client_id: Unique identifier for the client
        organization: Organization name
        client_version: Client software version
        capabilities: Client capabilities (e.g., GPU, memory)
        last_seen: Last communication timestamp
        total_samples: Total number of training samples
        active: Whether client is currently active
        public_key: Public key for secure communication (optional)
    """
    client_id: str
    organization: str
    client_version: str = "1.0.0"
    capabilities: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    total_samples: int = 0
    active: bool = True
    public_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert client info to dictionary."""
        return {
            "client_id": self.client_id,
            "organization": self.organization,
            "client_version": self.client_version,
            "capabilities": self.capabilities,
            "last_seen": self.last_seen.isoformat(),
            "total_samples": self.total_samples,
            "active": self.active,
            "public_key": self.public_key,
        }


@dataclass
class ModelUpdate:
    """
    Model update from a federated learning client.

    Attributes:
        client_id: ID of the client sending the update
        round_id: Round ID this update belongs to
        weights: Updated model weights (layer_name -> np.ndarray)
        num_samples: Number of samples used for training
        metrics: Training metrics (loss, accuracy, etc.)
        timestamp: When the update was created
        differential_privacy_applied: Whether DP was applied
        epsilon_used: Privacy budget used (if DP applied)
        computation_time: Time taken for local training (seconds)
        signature: Digital signature for verification (optional)
    """
    client_id: str
    round_id: int
    weights: Dict[str, np.ndarray]
    num_samples: int
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    differential_privacy_applied: bool = False
    epsilon_used: float = 0.0
    computation_time: float = 0.0
    signature: Optional[str] = None

    def __post_init__(self):
        """Validate model update."""
        if self.num_samples < 1:
            raise ValueError("num_samples must be at least 1")
        if not self.weights:
            raise ValueError("weights cannot be empty")
        if self.differential_privacy_applied and self.epsilon_used <= 0:
            raise ValueError("epsilon_used must be positive when DP applied")

    def get_total_parameters(self) -> int:
        """Get total number of parameters in the update."""
        return sum(w.size for w in self.weights.values())

    def get_update_size_mb(self) -> float:
        """Get size of update in megabytes."""
        total_bytes = sum(w.nbytes for w in self.weights.values())
        return total_bytes / (1024 * 1024)

    def to_dict(self, include_weights: bool = False) -> Dict[str, Any]:
        """
        Convert update to dictionary.

        Args:
            include_weights: Whether to include full weight arrays
        """
        result = {
            "client_id": self.client_id,
            "round_id": self.round_id,
            "num_samples": self.num_samples,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
            "differential_privacy_applied": self.differential_privacy_applied,
            "epsilon_used": self.epsilon_used,
            "computation_time": self.computation_time,
            "total_parameters": self.get_total_parameters(),
            "update_size_mb": self.get_update_size_mb(),
        }

        if include_weights:
            # Convert numpy arrays to lists for JSON serialization
            result["weights"] = {
                layer: weights.tolist()
                for layer, weights in self.weights.items()
            }
        else:
            result["weight_layers"] = list(self.weights.keys())

        return result


@dataclass
class FLRound:
    """
    Federated learning training round.

    Attributes:
        round_id: Unique round identifier
        status: Current round status
        config: Configuration for this round
        selected_clients: Clients selected for this round
        received_updates: Updates received so far
        global_model_version: Version of global model before this round
        start_time: Round start timestamp
        end_time: Round end timestamp (None if ongoing)
        aggregation_result: Result of aggregation (None if not completed)
        metrics: Round-level metrics
    """
    round_id: int
    status: FLStatus
    config: FLConfig
    selected_clients: List[str] = field(default_factory=list)
    received_updates: List[ModelUpdate] = field(default_factory=list)
    global_model_version: int = 0
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    aggregation_result: Optional[Dict[str, Any]] = None
    metrics: Dict[str, float] = field(default_factory=dict)

    def get_participation_rate(self) -> float:
        """Get fraction of selected clients that submitted updates."""
        if not self.selected_clients:
            return 0.0
        return len(self.received_updates) / len(self.selected_clients)

    def get_duration_seconds(self) -> Optional[float]:
        """Get round duration in seconds (None if not completed)."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def get_total_samples(self) -> int:
        """Get total number of samples across all updates."""
        return sum(update.num_samples for update in self.received_updates)

    def get_average_metrics(self) -> Dict[str, float]:
        """
        Get weighted average of client metrics.

        Returns:
            Dictionary of metric_name -> weighted_average
        """
        if not self.received_updates:
            return {}

        total_samples = self.get_total_samples()
        metric_names = set()
        for update in self.received_updates:
            metric_names.update(update.metrics.keys())

        avg_metrics = {}
        for metric_name in metric_names:
            weighted_sum = sum(
                update.metrics.get(metric_name, 0.0) * update.num_samples
                for update in self.received_updates
            )
            avg_metrics[metric_name] = weighted_sum / total_samples

        return avg_metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert round to dictionary."""
        return {
            "round_id": self.round_id,
            "status": self.status.value,
            "selected_clients": self.selected_clients,
            "num_received_updates": len(self.received_updates),
            "participation_rate": self.get_participation_rate(),
            "global_model_version": self.global_model_version,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration_seconds(),
            "total_samples": self.get_total_samples(),
            "average_metrics": self.get_average_metrics(),
            "metrics": self.metrics,
            "config": self.config.to_dict(),
        }


@dataclass
class FLMetrics:
    """
    Federated learning performance metrics.

    Attributes:
        total_rounds: Total number of rounds completed
        total_clients: Total number of registered clients
        active_clients: Number of currently active clients
        average_participation_rate: Average client participation rate
        average_round_duration: Average round duration (seconds)
        total_samples_trained: Total samples trained across all rounds
        global_model_accuracy: Accuracy of global model on test set
        convergence_status: Whether model has converged
        privacy_budget_used: Total privacy budget used (if DP enabled)
        last_updated: When metrics were last updated
    """
    total_rounds: int = 0
    total_clients: int = 0
    active_clients: int = 0
    average_participation_rate: float = 0.0
    average_round_duration: float = 0.0
    total_samples_trained: int = 0
    global_model_accuracy: float = 0.0
    convergence_status: bool = False
    privacy_budget_used: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_rounds": self.total_rounds,
            "total_clients": self.total_clients,
            "active_clients": self.active_clients,
            "average_participation_rate": self.average_participation_rate,
            "average_round_duration": self.average_round_duration,
            "total_samples_trained": self.total_samples_trained,
            "global_model_accuracy": self.global_model_accuracy,
            "convergence_status": self.convergence_status,
            "privacy_budget_used": self.privacy_budget_used,
            "last_updated": self.last_updated.isoformat(),
        }
