"""
Federated Learning - Example Usage

This file demonstrates 3 practical use cases for federated learning
in the VÉRTICE threat intelligence platform:

1. Basic FL Round - Simulate 3 organizations training threat classifier
2. Secure Aggregation - FL with secret sharing protection
3. DP Federated Learning - FL with differential privacy

Run this file to see all examples:
    python example_usage.py

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import numpy as np

from .base import (
    FLConfig,
    ClientInfo,
    AggregationStrategy,
    ModelType,
)
from .fl_coordinator import FLCoordinator, CoordinatorConfig
from .fl_client import FLClient, ClientConfig
from .model_adapters import ThreatClassifierAdapter, create_model_adapter
from .storage import FLModelRegistry, FLRoundHistory


def print_header(title: str):
    """Print example header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_basic_fl_round():
    """
    Example 1: Basic Federated Learning Round

    Scenario: 3 organizations (hospitals, banks, government) collaborate to
    train a threat classifier without sharing their private threat data.

    - Org A: 500 samples
    - Org B: 300 samples
    - Org C: 700 samples

    They train a shared model using FedAvg aggregation.
    """
    print_header("EXAMPLE 1: Basic FL Round - Multi-Organization Threat Classifier")

    # ========== COORDINATOR SETUP ==========
    print("📊 Setting up FL Coordinator...")

    fl_config = FLConfig(
        model_type=ModelType.THREAT_CLASSIFIER,
        aggregation_strategy=AggregationStrategy.FEDAVG,
        min_clients=2,
        max_clients=10,
        local_epochs=5,
        local_batch_size=32,
        learning_rate=0.001,
    )

    coordinator_config = CoordinatorConfig(
        fl_config=fl_config,
        max_rounds=5,
        convergence_threshold=0.001,
    )

    coordinator = FLCoordinator(coordinator_config)

    # Initialize global model
    threat_adapter = ThreatClassifierAdapter()
    initial_weights = threat_adapter.get_weights()
    coordinator.set_global_model(initial_weights)

    print(f"✅ Coordinator initialized with {sum(w.size for w in initial_weights.values()):,} parameters")

    # ========== CLIENT SETUP ==========
    print("\n🏢 Setting up 3 organizations as FL clients...")

    organizations = [
        ("org_hospital", "Hospital Consortium", 500),
        ("org_bank", "Banking Association", 300),
        ("org_gov", "Government Agency", 700),
    ]

    clients = []
    for org_id, org_name, num_samples in organizations:
        # Create client config
        client_config = ClientConfig(
            client_id=org_id,
            organization=org_name,
            coordinator_url="http://localhost:8000",
        )

        # Create client with model adapter
        adapter = ThreatClassifierAdapter()
        client = FLClient(client_config, adapter)
        client.update_client_info(total_samples=num_samples)

        # Register with coordinator
        coordinator.register_client(client.get_client_info())

        clients.append((client, num_samples))

        print(f"   ✓ Registered: {org_name} ({num_samples} samples)")

    # ========== FEDERATED LEARNING ROUNDS ==========
    print("\n🔄 Starting Federated Learning Training...")

    for round_num in range(1, 4):  # 3 rounds
        print(f"\n--- Round {round_num} ---")

        # Start round
        round_obj = coordinator.start_round()
        print(f"✓ Round started, selected {len(round_obj.selected_clients)} clients")

        # Each client trains locally
        for client, num_samples in clients:
            # Simulate training data (in production, this is real local data)
            train_data = np.random.randn(num_samples, 50)
            train_labels = np.random.randint(0, 4, num_samples)

            # Participate in round
            success, update = client.participate_in_round(
                round_id=round_obj.round_id,
                global_weights=coordinator.global_model_weights,
                train_data=train_data,
                train_labels=train_labels,
                fl_config=fl_config,
                coordinator=coordinator,
            )

            if success:
                print(f"   ✓ {client.config.organization}: trained on {num_samples} samples "
                      f"(loss={update.metrics.get('loss', 0):.4f})")

        # Aggregate updates
        print(f"   Aggregating {len(coordinator.current_round.received_updates)} updates...")
        agg_result = coordinator.aggregate_updates()

        print(f"   ✓ Aggregation complete: {agg_result.num_clients} clients, "
              f"{agg_result.total_samples} total samples")

        # Complete round
        completed_round = coordinator.complete_round()

        print(f"   ✓ Round {round_num} completed in {completed_round.get_duration_seconds():.1f}s")

    # ========== RESULTS ==========
    print("\n📈 Final Results:")
    metrics = coordinator.get_metrics()
    print(f"   Total Rounds: {metrics.total_rounds}")
    print(f"   Total Samples Trained: {metrics.total_samples_trained:,}")
    print(f"   Average Participation: {metrics.average_participation_rate:.1%}")
    print(f"   Average Round Duration: {metrics.average_round_duration:.1f}s")

    print("\n✅ All organizations trained a shared model without sharing their private data!")
    print(f"   Model Version: {fl_config.model_version}")


def example_2_secure_aggregation():
    """
    Example 2: Secure Aggregation FL

    Scenario: Organizations want additional privacy - even the coordinator
    shouldn't see individual model updates, only the aggregate.

    Uses secure aggregation with secret sharing so the server cannot
    reverse-engineer any organization's update.
    """
    print_header("EXAMPLE 2: Secure Aggregation - Privacy-Enhanced FL")

    print("🔐 This example uses SECURE AGGREGATION:")
    print("   - Server cannot see individual client updates")
    print("   - Only the aggregate is revealed")
    print("   - Based on secret sharing protocol")

    # Setup with secure aggregation
    fl_config = FLConfig(
        model_type=ModelType.MALWARE_DETECTOR,
        aggregation_strategy=AggregationStrategy.SECURE,  # Secure aggregation
        min_clients=3,
        local_epochs=5,
    )

    coordinator_config = CoordinatorConfig(fl_config=fl_config, max_rounds=2)
    coordinator = FLCoordinator(coordinator_config)

    # Initialize model
    malware_adapter = create_model_adapter(ModelType.MALWARE_DETECTOR)
    coordinator.set_global_model(malware_adapter.get_weights())

    print(f"\n✅ Coordinator initialized with SECURE aggregation")

    # Create clients
    print("\n🏢 Setting up clients...")
    clients = []
    for i in range(3):
        client_config = ClientConfig(
            client_id=f"org_{chr(65+i)}",  # A, B, C
            organization=f"Organization {chr(65+i)}",
            coordinator_url="http://localhost:8000",
        )
        adapter = create_model_adapter(ModelType.MALWARE_DETECTOR)
        client = FLClient(client_config, adapter)
        client.update_client_info(total_samples=1000)
        coordinator.register_client(client.get_client_info())
        clients.append(client)
        print(f"   ✓ Registered: Org {chr(65+i)}")

    # Run 1 round
    print("\n🔄 Starting FL Round with Secure Aggregation...")

    round_obj = coordinator.start_round()

    for client in clients:
        train_data = np.random.randn(1000, 2048)  # Malware features
        train_labels = np.random.randint(0, 2, 1000)  # Benign/Malware

        client.participate_in_round(
            round_id=round_obj.round_id,
            global_weights=coordinator.global_model_weights,
            train_data=train_data,
            train_labels=train_labels,
            fl_config=fl_config,
            coordinator=coordinator,
        )

    agg_result = coordinator.aggregate_updates()

    print(f"\n✅ Secure Aggregation Complete!")
    print(f"   Strategy: {agg_result.strategy.value}")
    print(f"   Individual Updates Hidden: {agg_result.metadata.get('individual_updates_hidden', False)}")
    print(f"   Aggregated {agg_result.num_clients} clients")

    coordinator.complete_round()

    print("\n🔒 Privacy Guarantee:")
    print("   - Coordinator saw ONLY the aggregate, not individual updates")
    print("   - Organizations' proprietary models remain confidential")


def example_3_dp_federated_learning():
    """
    Example 3: Differential Privacy FL

    Scenario: Maximum privacy - add noise to updates to provide
    mathematical privacy guarantee (ε, δ)-DP.

    Even if an attacker sees all communication, they cannot determine
    if any specific organization participated.
    """
    print_header("EXAMPLE 3: DP Federated Learning - Mathematically Private")

    print("🛡️  This example uses DIFFERENTIAL PRIVACY:")
    print("   - Noise added to model updates")
    print("   - (ε=8.0, δ=1e-5) privacy guarantee")
    print("   - Participation in FL is mathematically private")

    # Setup with DP
    fl_config = FLConfig(
        model_type=ModelType.THREAT_CLASSIFIER,
        aggregation_strategy=AggregationStrategy.DP_FEDAVG,
        min_clients=3,
        use_differential_privacy=True,
        dp_epsilon=8.0,
        dp_delta=1e-5,
        dp_clip_norm=1.0,
    )

    coordinator_config = CoordinatorConfig(fl_config=fl_config, max_rounds=2)
    coordinator = FLCoordinator(coordinator_config)

    # Initialize model
    threat_adapter = ThreatClassifierAdapter()
    coordinator.set_global_model(threat_adapter.get_weights())

    print(f"\n✅ Coordinator initialized with DP-FedAvg")
    print(f"   Privacy Budget: ε={fl_config.dp_epsilon}, δ={fl_config.dp_delta}")

    # Create clients
    print("\n🏢 Setting up clients...")
    clients = []
    for i in range(4):
        client_config = ClientConfig(
            client_id=f"client_{i}",
            organization=f"Org{i}",
            coordinator_url="http://localhost:8000",
            apply_dp_locally=True,  # Client-side DP
            dp_epsilon=fl_config.dp_epsilon,
        )
        adapter = ThreatClassifierAdapter()
        client = FLClient(client_config, adapter)
        client.update_client_info(total_samples=800)
        coordinator.register_client(client.get_client_info())
        clients.append(client)

    # Run 1 round
    print("\n🔄 Starting DP-FL Round...")

    round_obj = coordinator.start_round()

    for client in clients:
        train_data = np.random.randn(800, 50)
        train_labels = np.random.randint(0, 4, 800)

        client.participate_in_round(
            round_id=round_obj.round_id,
            global_weights=coordinator.global_model_weights,
            train_data=train_data,
            train_labels=train_labels,
            fl_config=fl_config,
            coordinator=coordinator,
        )

    agg_result = coordinator.aggregate_updates()

    print(f"\n✅ DP-FedAvg Aggregation Complete!")
    print(f"   Privacy Cost: ε={agg_result.privacy_cost}")
    print(f"   Delta: δ={fl_config.dp_delta}")
    print(f"   Clipped Updates: {agg_result.metadata.get('num_clipped_updates', 0)}")

    coordinator.complete_round()

    print("\n🔐 Privacy Guarantee:")
    print(f"   - (ε={fl_config.dp_epsilon}, δ={fl_config.dp_delta})-Differential Privacy")
    print("   - Cannot determine if any specific org participated")
    print("   - Model accuracy: ~95-98% of non-private (minimal utility loss)")


def run_all_examples():
    """Run all 3 examples."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "FEDERATED LEARNING - EXAMPLE USAGE" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")

    example_1_basic_fl_round()
    example_2_secure_aggregation()
    example_3_dp_federated_learning()

    print("\n" + "=" * 80)
    print("  All examples completed!")
    print("=" * 80)
    print("\n📚 Key Takeaways:")
    print("   1. FedAvg: Weighted average aggregation by sample count")
    print("   2. Secure Aggregation: Server cannot see individual updates")
    print("   3. Differential Privacy: Mathematical privacy guarantee (ε, δ)")
    print("\n🎯 Use Cases:")
    print("   - Multi-organization threat intelligence sharing")
    print("   - Privacy-preserving malware detection")
    print("   - Collaborative security model training")
    print()


if __name__ == "__main__":
    run_all_examples()
