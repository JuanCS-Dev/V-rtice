"""
Comprehensive Test Suite for Federated Learning Module

This test suite validates all components of the FL framework:
- Base classes and data structures
- Aggregation algorithms
- FL coordinator
- FL client
- Model adapters
- Communication layer
- Storage and persistence

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest
import numpy as np
from datetime import datetime
import tempfile
import os

from .base import (
    FLConfig,
    FLRound,
    ModelUpdate,
    ClientInfo,
    FLMetrics,
    FLStatus,
    AggregationStrategy,
    ModelType,
)
from .aggregation import (
    FedAvgAggregator,
    SecureAggregator,
    DPAggregator,
)
from .fl_coordinator import FLCoordinator, CoordinatorConfig
from .fl_client import FLClient, ClientConfig
from .model_adapters import (
    ThreatClassifierAdapter,
    MalwareDetectorAdapter,
    create_model_adapter,
)
from .communication import FLCommunicationChannel, MessageType
from .storage import FLModelRegistry, FLRoundHistory


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def fl_config():
    """Create FL configuration for testing."""
    return FLConfig(
        model_type=ModelType.THREAT_CLASSIFIER,
        aggregation_strategy=AggregationStrategy.FEDAVG,
        min_clients=2,
        max_clients=10,
        local_epochs=5,
        local_batch_size=32,
        learning_rate=0.001,
    )


@pytest.fixture
def sample_weights():
    """Create sample model weights matching LSTM ThreatClassifier exact structure."""
    return {
        "embedding": np.random.randn(10000, 128).astype(np.float32) * 0.01,
        "lstm_kernel": np.random.randn(128, 256).astype(np.float32) * 0.01,
        "lstm_recurrent": np.random.randn(64, 256).astype(np.float32) * 0.01,
        "dense1_kernel": np.random.randn(64, 32).astype(np.float32) * 0.01,
        "dense1_bias": np.zeros(32, dtype=np.float32),
        "output_kernel": np.random.randn(32, 4).astype(np.float32) * 0.01,
        "output_bias": np.zeros(4, dtype=np.float32),
    }


@pytest.fixture
def sample_updates(sample_weights):
    """Create sample model updates from multiple clients."""
    updates = []
    for i in range(3):
        weights = {
            key: val + np.random.randn(*val.shape).astype(np.float32) * 0.01
            for key, val in sample_weights.items()
        }
        update = ModelUpdate(
            client_id=f"client_{i}",
            round_id=1,
            weights=weights,
            num_samples=100 * (i + 1),
            metrics={"loss": 0.5, "accuracy": 0.85},
        )
        updates.append(update)
    return updates


# ============================================================================
# Test Base Classes
# ============================================================================

class TestBaseClasses:
    """Tests for base classes and data structures."""

    def test_fl_config_validation(self):
        """Test FL configuration validation."""
        # Valid config
        config = FLConfig(
            model_type=ModelType.THREAT_CLASSIFIER,
            min_clients=3,
            local_epochs=5,
        )
        assert config.min_clients == 3

        # Invalid: min_clients < 1
        with pytest.raises(ValueError):
            FLConfig(model_type=ModelType.THREAT_CLASSIFIER, min_clients=0)

        # Invalid: max_clients < min_clients
        with pytest.raises(ValueError):
            FLConfig(
                model_type=ModelType.THREAT_CLASSIFIER,
                min_clients=5,
                max_clients=3,
            )

    def test_model_update_creation(self, sample_weights):
        """Test model update creation and validation."""
        update = ModelUpdate(
            client_id="client_1",
            round_id=1,
            weights=sample_weights,
            num_samples=100,
            metrics={"loss": 0.45, "accuracy": 0.88},
        )

        assert update.client_id == "client_1"
        assert update.num_samples == 100
        assert update.get_total_parameters() == sum(w.size for w in sample_weights.values())
        assert update.get_update_size_mb() > 0

    def test_client_info(self):
        """Test client info creation."""
        client = ClientInfo(
            client_id="org1_client",
            organization="Org1",
            total_samples=5000,
        )

        assert client.client_id == "org1_client"
        assert client.active == True
        assert client.total_samples == 5000

    def test_fl_round_metrics(self, sample_updates):
        """Test FL round metrics calculation."""
        round_obj = FLRound(
            round_id=1,
            status=FLStatus.TRAINING,
            config=FLConfig(model_type=ModelType.THREAT_CLASSIFIER),
            selected_clients=["client_0", "client_1", "client_2"],
            received_updates=sample_updates,
        )

        assert round_obj.get_participation_rate() == 1.0
        assert round_obj.get_total_samples() == 600  # 100 + 200 + 300
        avg_metrics = round_obj.get_average_metrics()
        assert "loss" in avg_metrics
        assert "accuracy" in avg_metrics


# ============================================================================
# Test Aggregation Algorithms
# ============================================================================

class TestAggregation:
    """Tests for aggregation algorithms."""

    def test_fedavg_aggregation(self, sample_updates):
        """Test FedAvg aggregation."""
        aggregator = FedAvgAggregator()
        result = aggregator.aggregate(sample_updates)

        assert result.num_clients == 3
        assert result.total_samples == 600
        assert result.strategy == AggregationStrategy.FEDAVG
        assert len(result.aggregated_weights) == len(sample_updates[0].weights)

    def test_fedavg_weighted_average(self):
        """Test that FedAvg correctly weights by sample count."""
        # Create updates with different sample counts
        weights_a = {"layer": np.array([1.0, 1.0]).astype(np.float32)}
        weights_b = {"layer": np.array([3.0, 3.0]).astype(np.float32)}

        update_a = ModelUpdate(
            client_id="a", round_id=1, weights=weights_a, num_samples=25
        )
        update_b = ModelUpdate(
            client_id="b", round_id=1, weights=weights_b, num_samples=75
        )

        aggregator = FedAvgAggregator()
        result = aggregator.aggregate([update_a, update_b])

        # Expected: 0.25 * 1.0 + 0.75 * 3.0 = 2.5
        expected = 2.5
        actual = result.aggregated_weights["layer"][0]
        assert abs(actual - expected) < 0.01

    def test_secure_aggregation(self, sample_updates):
        """Test secure aggregation."""
        aggregator = SecureAggregator(threshold=2)
        result = aggregator.aggregate(sample_updates)

        assert result.strategy == AggregationStrategy.SECURE
        assert result.metadata["secure_aggregation"] == True
        assert len(result.aggregated_weights) > 0

    def test_dp_aggregation(self, sample_updates):
        """Test DP-FedAvg aggregation."""
        aggregator = DPAggregator(epsilon=8.0, delta=1e-5, clip_norm=1.0)
        result = aggregator.aggregate(sample_updates)

        assert result.strategy == AggregationStrategy.DP_FEDAVG
        assert result.privacy_cost == 8.0
        assert result.metadata["differential_privacy"] == True
        assert "num_clipped_updates" in result.metadata


# ============================================================================
# Test FL Coordinator
# ============================================================================

class TestFLCoordinator:
    """Tests for FL coordinator."""

    def test_coordinator_initialization(self, fl_config):
        """Test coordinator initialization."""
        config = CoordinatorConfig(fl_config=fl_config)
        coordinator = FLCoordinator(config)

        assert coordinator.global_model_weights is None
        assert len(coordinator.registered_clients) == 0
        assert coordinator.metrics.total_rounds == 0

    def test_client_registration(self, fl_config):
        """Test client registration."""
        config = CoordinatorConfig(fl_config=fl_config)
        coordinator = FLCoordinator(config)

        client_info = ClientInfo(
            client_id="client_1", organization="Org1", total_samples=1000
        )
        success = coordinator.register_client(client_info)

        assert success == True
        assert "client_1" in coordinator.registered_clients
        assert coordinator.metrics.total_clients == 1

    def test_start_round(self, fl_config, sample_weights):
        """Test starting a training round."""
        config = CoordinatorConfig(fl_config=fl_config)
        coordinator = FLCoordinator(config)
        coordinator.set_global_model(sample_weights)

        # Register clients
        for i in range(3):
            coordinator.register_client(
                ClientInfo(client_id=f"client_{i}", organization=f"Org{i}")
            )

        # Start round
        round_obj = coordinator.start_round()

        assert round_obj.round_id == 1
        assert round_obj.status == FLStatus.WAITING_FOR_CLIENTS
        assert len(round_obj.selected_clients) >= fl_config.min_clients

    def test_receive_and_aggregate(self, fl_config, sample_weights, sample_updates):
        """Test receiving updates and aggregation."""
        config = CoordinatorConfig(fl_config=fl_config)
        coordinator = FLCoordinator(config)
        coordinator.set_global_model(sample_weights)

        # Register clients
        for i in range(3):
            coordinator.register_client(
                ClientInfo(client_id=f"client_{i}", organization=f"Org{i}")
            )

        # Start round
        coordinator.start_round()

        # Receive updates
        for update in sample_updates:
            coordinator.receive_update(update)

        assert len(coordinator.current_round.received_updates) == 3

        # Aggregate
        agg_result = coordinator.aggregate_updates()

        assert agg_result.num_clients == 3
        assert coordinator.global_model_weights is not None


# ============================================================================
# Test FL Client
# ============================================================================

class TestFLClient:
    """Tests for FL client."""

    def test_client_initialization(self):
        """Test client initialization."""
        config = ClientConfig(
            client_id="client_1",
            organization="Org1",
            coordinator_url="http://localhost:8000",
        )
        adapter = ThreatClassifierAdapter()
        client = FLClient(config, adapter)

        assert client.config.client_id == "client_1"
        assert client.client_info.organization == "Org1"

    def test_fetch_global_model(self, sample_weights):
        """Test fetching global model."""
        config = ClientConfig(
            client_id="client_1",
            organization="Org1",
            coordinator_url="http://localhost:8000",
        )
        adapter = ThreatClassifierAdapter()
        client = FLClient(config, adapter)

        success = client.fetch_global_model(round_id=1, global_weights=sample_weights)

        assert success == True
        assert client.current_round_id == 1
        assert client.global_model_weights is not None

    def test_compute_update(self, sample_weights):
        """Test computing model update."""
        config = ClientConfig(
            client_id="client_1",
            organization="Org1",
            coordinator_url="http://localhost:8000",
        )
        adapter = ThreatClassifierAdapter()
        client = FLClient(config, adapter)

        client.fetch_global_model(round_id=1, global_weights=sample_weights)

        metrics = {"loss": 0.45, "accuracy": 0.88, "training_time": 10.0}
        update = client.compute_update(num_samples=500, training_metrics=metrics)

        assert update.client_id == "client_1"
        assert update.round_id == 1
        assert update.num_samples == 500
        assert "loss" in update.metrics


# ============================================================================
# Test Model Adapters
# ============================================================================

class TestModelAdapters:
    """Tests for model adapters."""

    def test_threat_classifier_adapter(self):
        """Test threat classifier adapter."""
        adapter = ThreatClassifierAdapter()

        # Get weights
        weights = adapter.get_weights()
        assert len(weights) == 7  # 7 layers
        assert "embedding" in weights

        # Set weights
        new_weights = {k: v * 2 for k, v in weights.items()}
        adapter.set_weights(new_weights)

        # Verify
        updated = adapter.get_weights()
        assert np.allclose(updated["embedding"], weights["embedding"] * 2)

    def test_malware_detector_adapter(self):
        """Test malware detector adapter."""
        adapter = MalwareDetectorAdapter()

        weights = adapter.get_weights()
        assert len(weights) == 8  # 8 layers (4 hidden + 4 bias)
        assert "hidden1_kernel" in weights

    def test_create_model_adapter_factory(self):
        """Test model adapter factory."""
        threat_adapter = create_model_adapter(ModelType.THREAT_CLASSIFIER)
        assert isinstance(threat_adapter, ThreatClassifierAdapter)

        malware_adapter = create_model_adapter(ModelType.MALWARE_DETECTOR)
        assert isinstance(malware_adapter, MalwareDetectorAdapter)


# ============================================================================
# Test Communication
# ============================================================================

class TestCommunication:
    """Tests for communication layer."""

    def test_weight_serialization(self, sample_weights):
        """Test weight serialization and deserialization."""
        channel = FLCommunicationChannel()

        # Serialize
        serialized = channel.serialize_weights(sample_weights)

        assert len(serialized) == len(sample_weights)
        for layer_name in sample_weights:
            assert "data" in serialized[layer_name]
            assert "shape" in serialized[layer_name]
            assert "dtype" in serialized[layer_name]

        # Deserialize
        deserialized = channel.deserialize_weights(serialized)

        # Verify
        for layer_name in sample_weights:
            assert np.allclose(
                deserialized[layer_name], sample_weights[layer_name]
            )

    def test_message_creation(self):
        """Test message creation."""
        channel = FLCommunicationChannel()

        message = channel.create_message(
            MessageType.ROUND_START,
            payload={"round_id": 1, "clients": ["a", "b"]},
            sender_id="coordinator",
        )

        assert message["type"] == "round_start"
        assert "timestamp" in message
        assert message["sender_id"] == "coordinator"

    def test_message_parsing(self):
        """Test message parsing."""
        channel = FLCommunicationChannel()

        message_data = channel.create_message(
            MessageType.UPDATE_SUBMIT,
            payload={"round_id": 1},
            sender_id="client_1",
        )

        parsed = channel.parse_message(message_data)

        assert parsed.message_type == MessageType.UPDATE_SUBMIT
        assert parsed.sender_id == "client_1"


# ============================================================================
# Test Storage
# ============================================================================

class TestStorage:
    """Tests for storage and persistence."""

    def test_model_registry(self, sample_weights):
        """Test model registry save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = FLModelRegistry(storage_dir=tmpdir)

            # Save model
            version = registry.save_global_model(
                version_id=1,
                model_type=ModelType.THREAT_CLASSIFIER,
                round_id=1,
                weights=sample_weights,
                accuracy=0.88,
            )

            assert version.version_id == 1
            assert os.path.exists(version.file_path)

            # Load model
            loaded_weights = registry.load_global_model(version_id=1)

            assert loaded_weights is not None
            for layer_name in sample_weights:
                assert np.allclose(
                    loaded_weights[layer_name], sample_weights[layer_name]
                )

    def test_round_history(self, fl_config, sample_updates):
        """Test round history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history = FLRoundHistory(storage_dir=tmpdir)

            round_obj = FLRound(
                round_id=1,
                status=FLStatus.COMPLETED,
                config=fl_config,
                selected_clients=["a", "b", "c"],
                received_updates=sample_updates,
            )

            # Save round
            success = history.save_round(round_obj)
            assert success == True

            # Get stats
            stats = history.get_round_stats()
            assert stats["total_rounds"] == 1
            assert stats["total_updates"] == 3


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_complete_fl_round(self, fl_config, sample_weights):
        """Test complete FL round with coordinator and clients."""
        # Initialize coordinator
        config = CoordinatorConfig(fl_config=fl_config)
        coordinator = FLCoordinator(config)
        coordinator.set_global_model(sample_weights)

        # Create clients
        clients = []
        for i in range(3):
            client_config = ClientConfig(
                client_id=f"client_{i}",
                organization=f"Org{i}",
                coordinator_url="http://localhost:8000",
            )
            adapter = ThreatClassifierAdapter()
            client = FLClient(client_config, adapter)
            clients.append(client)

            # Register with coordinator
            coordinator.register_client(client.get_client_info())

        # Start round
        round_obj = coordinator.start_round()

        # Simulate training data
        train_data = np.random.randn(100, 50)
        train_labels = np.random.randint(0, 4, 100)

        # Clients participate
        for client in clients:
            # Fetch global model
            client.fetch_global_model(
                round_obj.round_id, coordinator.global_model_weights
            )

            # Train and submit update
            metrics = client.train_local_model(
                train_data, train_labels, fl_config
            )
            update = client.compute_update(len(train_data), metrics)
            coordinator.receive_update(update)

        # Aggregate
        agg_result = coordinator.aggregate_updates()

        assert agg_result.num_clients == 3
        assert coordinator.global_model_weights is not None

        # Complete round
        completed = coordinator.complete_round()

        assert completed.status == FLStatus.COMPLETED
        assert completed.get_participation_rate() == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
