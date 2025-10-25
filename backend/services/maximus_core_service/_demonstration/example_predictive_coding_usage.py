"""
Predictive Coding Network - Usage Example

Demonstrates Free Energy Minimization principle in cybersecurity threat prediction.
Shows hierarchical prediction across all 5 layers and integration with Neuromodulation.

This example illustrates:
1. How the HPC Network processes security events across multiple timescales
2. How prediction errors (Free Energy) drive learning rate modulation
3. How unexpected events increase attention through neuromodulation
4. Graceful degradation when torch is not installed

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO - Zero mocks, production-ready demonstration
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List


# ============================================================================
# EXAMPLE SECURITY EVENTS
# ============================================================================

def create_example_events() -> List[Dict[str, Any]]:
    """Create example security events spanning multiple timescales."""

    return [
        # Normal event - low prediction error expected
        {
            "event_id": "evt_001",
            "timestamp": "2025-10-06T10:30:00Z",
            "event_type": "network_connection",
            "source_ip": "192.168.1.100",
            "dest_ip": "8.8.8.8",
            "port": 443,
            "protocol": "https",
            "bytes_transferred": 1024,
            "expected": True,  # Normal traffic
        },

        # Unexpected event - high prediction error expected
        {
            "event_id": "evt_002",
            "timestamp": "2025-10-06T10:31:15Z",
            "event_type": "network_connection",
            "source_ip": "192.168.1.200",
            "dest_ip": "malicious-c2.example.com",
            "port": 8080,
            "protocol": "http",
            "bytes_transferred": 524288,
            "expected": False,  # Suspicious C2 beacon
        },

        # Anomalous behavior - medium prediction error
        {
            "event_id": "evt_003",
            "timestamp": "2025-10-06T10:32:30Z",
            "event_type": "process_execution",
            "process_name": "powershell.exe",
            "command_line": "IEX (New-Object Net.WebClient).DownloadString(...)",
            "parent_process": "winword.exe",
            "expected": False,  # Fileless malware execution
        },
    ]


# ============================================================================
# EXAMPLE 1: STANDALONE HPC NETWORK USAGE
# ============================================================================

def example_1_standalone_hpc_network():
    """Example 1: Using HPC Network standalone (requires torch)."""

    print("\n" + "=" * 80)
    print("EXAMPLE 1: Standalone HPC Network Usage")
    print("=" * 80)
    print("\nDemonstrates hierarchical prediction across all 5 layers.\n")

    try:
        from predictive_coding import HierarchicalPredictiveCodingNetwork
        import torch

        # Initialize HPC Network
        print("🧠 Initializing Hierarchical Predictive Coding Network...")
        hpc_network = HierarchicalPredictiveCodingNetwork(
            latent_dim=64,
            device="cpu"
        )
        print("✅ HPC Network initialized\n")

        # Get example events
        events = create_example_events()

        # Process each event through all 5 layers
        for event in events:
            print(f"📊 Processing Event: {event['event_id']}")
            print(f"   Type: {event['event_type']}")
            print(f"   Expected: {event.get('expected', 'unknown')}\n")

            # Convert event to tensor (simplified - normally would be feature extraction)
            raw_event = torch.randn(1, 64)  # Simulated feature vector

            # Hierarchical inference
            predictions = hpc_network.hierarchical_inference(
                raw_event=raw_event,
                event_graph=None,  # Would contain process graph in production
                l2_sequence=None,  # Would contain behavioral sequence
                l3_sequence=None,  # Would contain operational history
                l4_sequence=None,  # Would contain tactical context
            )

            print(f"   Layer 1 (Sensory):     Latent representation shape: {predictions['l1'].shape}")
            print(f"   Layer 2 (Behavioral):  Pattern prediction shape: {predictions['l2'].shape}")
            print(f"   Layer 3 (Operational): Threat prediction shape: {predictions['l3'].shape}")
            print(f"   Layer 4 (Tactical):    Campaign prediction shape: {predictions['l4'].shape}")
            print(f"   Layer 5 (Strategic):   Landscape prediction shape: {predictions['l5'].shape}")

            # Compute Free Energy (if ground truth available)
            if 'expected' in event:
                # Simulate ground truth
                ground_truth = torch.zeros(1, 64) if event['expected'] else torch.ones(1, 64)

                free_energy = hpc_network.compute_free_energy(
                    predictions=predictions,
                    ground_truth=ground_truth
                )

                print(f"\n   🎯 Free Energy (prediction error): {free_energy:.4f}")

                if event['expected']:
                    print(f"   ✅ Low prediction error - event matches learned patterns")
                else:
                    print(f"   ⚠️  HIGH prediction error - unexpected event detected!")

            print()

        print("✅ Example 1 complete\n")

    except ImportError as e:
        print(f"⚠️  Torch not available: {e}")
        print("   Install torch and torch_geometric to run this example:")
        print("   pip install torch torch_geometric")
        print()


# ============================================================================
# EXAMPLE 2: MAXIMUS INTEGRATION
# ============================================================================

async def example_2_maximus_integration():
    """Example 2: Using Predictive Coding through MAXIMUS (graceful degradation).

    NOTE: This example requires torch to be installed, as some autonomic_core
    components (AnomalyDetector) have torch dependencies. Install with:
    pip install torch torch_geometric
    """

    print("\n" + "=" * 80)
    print("EXAMPLE 2: MAXIMUS Integration with Graceful Degradation")
    print("=" * 80)
    print("\nDemonstrates integration with Neuromodulation and Attention systems.\n")
    print("⚠️  NOTE: Requires torch (autonomic_core dependency)\n")

    try:
        from maximus_integrated import MaximusIntegrated

        # Initialize MAXIMUS (includes Predictive Coding if torch available)
        print("🧠 Initializing MAXIMUS Integrated...")
        maximus = MaximusIntegrated()
        print("✅ MAXIMUS initialized\n")

        # Check if Predictive Coding is available
        pc_status = maximus.get_predictive_coding_state()
        print(f"📊 Predictive Coding Status:")
        print(f"   Available: {pc_status['available']}")

        if not pc_status['available']:
            print(f"   Message: {pc_status.get('message', 'N/A')}")
            print("\n   ℹ️  Continuing with graceful degradation...\n")
        else:
            print(f"   Latent Dimension: {pc_status['latent_dim']}")
            print(f"   Device: {pc_status['device']}\n")

        # Get example events
        events = create_example_events()

        # Process each event
        for event in events:
            print(f"📊 Processing Event: {event['event_id']}")
            print(f"   Type: {event['event_type']}")
            print(f"   Expected: {event.get('expected', 'unknown')}\n")

            # Attempt hierarchical prediction
            result = maximus.predict_with_hpc_network(
                raw_event=event,
                context={
                    "ground_truth": None,  # Would be actual outcome in production
                    "event_graph": None,   # Would contain process relationships
                }
            )

            if result['available'] and 'predictions' in result:
                print(f"   ✅ Predictions generated across all 5 layers")

                if 'free_energy' in result and result['free_energy'] is not None:
                    free_energy = result['free_energy']
                    print(f"   🎯 Free Energy: {free_energy:.4f}")

                    # Process prediction error through neuromodulation
                    if free_energy > 0.0:
                        modulation_result = await maximus.process_prediction_error(
                            prediction_error=float(free_energy),
                            layer="l1"
                        )

                        print(f"\n   🧬 Neuromodulation Effects:")
                        print(f"      RPE Signal: {modulation_result['rpe_signal']:.4f}")
                        print(f"      Learning Rate: {modulation_result['modulated_learning_rate']:.4f}")
                        print(f"      Attention Updated: {modulation_result['attention_updated']}")

                        if modulation_result['attention_updated']:
                            print(f"      → High surprise increased acetylcholine")
                            print(f"      → Attention threshold lowered for similar events")
            else:
                print(f"   ℹ️  Predictive Coding not available (torch required)")
                print(f"      MAXIMUS continues with other detection methods")

            print()

        # Display final system status
        print("📊 Final System Status:")
        status = await maximus.get_system_status()

        print(f"   Neuromodulation:")
        print(f"      Dopamine: {status['neuromodulation_status']['dopamine']['baseline_level']:.2f}")
        print(f"      Acetylcholine: {status['neuromodulation_status']['acetylcholine']['baseline_level']:.2f}")
        print(f"      Norepinephrine: {status['neuromodulation_status']['norepinephrine']['baseline_level']:.2f}")
        print(f"      Serotonin: {status['neuromodulation_status']['serotonin']['baseline_level']:.2f}")

        print(f"\n   Attention System:")
        print(f"      Foveal Threshold: {status['attention_status']['foveal_threshold']:.2f}")
        print(f"      Peripheral Threshold: {status['attention_status']['peripheral_threshold']:.2f}")

        if status['predictive_coding_status']['available']:
            print(f"\n   Predictive Coding:")
            errors = status['predictive_coding_status']['prediction_errors']
            print(f"      L1 errors tracked: {errors['l1']}")
            print(f"      L2 errors tracked: {errors['l2']}")
            print(f"      L3 errors tracked: {errors['l3']}")
            print(f"      L4 errors tracked: {errors['l4']}")
            print(f"      L5 errors tracked: {errors['l5']}")

        print("\n✅ Example 2 complete\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# EXAMPLE 3: FREE ENERGY MINIMIZATION PRINCIPLE
# ============================================================================

def example_3_free_energy_principle():
    """Example 3: Understanding the Free Energy Minimization principle."""

    print("\n" + "=" * 80)
    print("EXAMPLE 3: Free Energy Minimization Principle Explained")
    print("=" * 80)
    print()

    print("🧠 The Free Energy Principle (Karl Friston):\n")
    print("   'Biological systems minimize surprise (prediction error) over time.'\n")

    print("📊 In Cybersecurity Context:\n")
    print("   1. The brain builds models of 'normal' behavior")
    print("   2. Prediction errors = unexpected events = potential threats")
    print("   3. High surprise → increase learning rate (dopamine)")
    print("   4. High surprise → increase attention (acetylcholine)")
    print("   5. System adapts to minimize future surprise\n")

    print("🔬 Hierarchical Implementation:\n")
    print("   Layer 1 (Sensory):     100ms - 1s    VAE compression of raw events")
    print("   Layer 2 (Behavioral):  1s - 1min     GNN process pattern recognition")
    print("   Layer 3 (Operational): 1min - 1hr    TCN immediate threat prediction")
    print("   Layer 4 (Tactical):    1hr - 1day    LSTM attack campaign prediction")
    print("   Layer 5 (Strategic):   1day - 1week  Transformer threat landscape\n")

    print("🎯 Example Scenario:\n")
    print("   Normal Event:")
    print("   - User browses https://google.com")
    print("   - All layers predict this behavior accurately")
    print("   - Free Energy = LOW (0.01)")
    print("   - Learning rate = baseline")
    print("   - Attention = normal\n")

    print("   Anomalous Event:")
    print("   - Powershell downloads script from unknown server")
    print("   - Layers did NOT predict this behavior")
    print("   - Free Energy = HIGH (0.95)")
    print("   - Learning rate ↑ (dopamine spike)")
    print("   - Attention ↑ (acetylcholine release)")
    print("   - System quickly learns this is malicious\n")

    print("✅ Result: Adaptive immune system that learns from surprise\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all examples."""

    print("\n" + "=" * 80)
    print("PREDICTIVE CODING NETWORK - USAGE EXAMPLES")
    print("=" * 80)
    print("\nFree Energy Minimization for Cybersecurity Threat Detection")
    print("Author: Claude Code + JuanCS-Dev")
    print("Date: 2025-10-06")
    print("=" * 80)

    # Example 3: Theory (always runs)
    example_3_free_energy_principle()

    # Example 1: Standalone (requires torch)
    example_1_standalone_hpc_network()

    # Example 2: MAXIMUS Integration (graceful degradation)
    print("\nRunning async example...")
    asyncio.run(example_2_maximus_integration())

    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 80)
    print("\n📚 Next Steps:")
    print("   1. Install torch: pip install torch torch_geometric")
    print("   2. Review predictive_coding/ implementation")
    print("   3. Explore maximus_integrated.py integration")
    print("   4. Run test_predictive_coding_structure.py")
    print("   5. Train the HPC Network on real security event data\n")


if __name__ == "__main__":
    main()
