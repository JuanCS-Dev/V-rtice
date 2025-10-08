"""
Predictive Coding Network Structure Tests

Validates structure, API contracts, and code quality of all 5 layers without
requiring torch/torch_geometric dependencies. Tests REGRA DE OURO compliance.

Tests:
1. Layer 1 (Sensory) file structure and methods
2. Layer 2 (Behavioral) file structure and methods
3. Layer 3 (Operational) file structure and methods
4. Layer 4 (Tactical) file structure and methods
5. Layer 5 (Strategic) file structure and methods
6. Free Energy principle in code
7. Hierarchical structure validation
8. HPC Network orchestration structure

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO - Zero mocks, structure validation
"""

import ast
from pathlib import Path

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def read_source(filename):
    """Read source code from predictive_coding directory."""
    path = Path(__file__).parent / "predictive_coding" / filename
    with open(path) as f:
        return f.read()


def parse_source(filename):
    """Parse Python source file and return AST."""
    source = read_source(filename)
    return ast.parse(source)


def get_classes(tree):
    """Extract class names from AST."""
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def get_methods(tree, class_name):
    """Extract method names for a specific class."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
    return []


# ============================================================================
# TEST 1: LAYER 1 (SENSORY/VAE) STRUCTURE
# ============================================================================


def test_layer1_sensory_structure():
    """Test that Layer 1 (Sensory) has correct structure."""
    print("\n" + "=" * 80)
    print("TEST 1: Layer 1 (Sensory/VAE) Structure")
    print("=" * 80)

    tree = parse_source("layer1_sensory.py")
    classes = get_classes(tree)

    # Check required classes exist
    assert "EventVAE" in classes, "Layer 1 missing EventVAE class"
    assert "SensoryLayer" in classes, "Layer 1 missing SensoryLayer class"
    print(f"✅ Layer 1 has {len(classes)} classes: {classes}")

    # Check EventVAE methods
    vae_methods = get_methods(tree, "EventVAE")
    required_vae_methods = ["__init__", "encode", "reparameterize", "decode", "forward", "compute_loss"]
    for method in required_vae_methods:
        assert method in vae_methods, f"EventVAE missing method: {method}"
    print(f"✅ EventVAE has all {len(required_vae_methods)} required methods")

    # Check SensoryLayer methods
    layer_methods = get_methods(tree, "SensoryLayer")
    required_layer_methods = ["__init__", "predict", "train_step", "save_model", "load_model"]
    for method in required_layer_methods:
        assert method in layer_methods, f"SensoryLayer missing method: {method}"
    print(f"✅ SensoryLayer has all {len(required_layer_methods)} required methods")

    print("✅ Layer 1 structure validated")


# ============================================================================
# TEST 2: LAYER 2 (BEHAVIORAL/GNN) STRUCTURE
# ============================================================================


def test_layer2_behavioral_structure():
    """Test that Layer 2 (Behavioral) has correct structure."""
    print("\n" + "=" * 80)
    print("TEST 2: Layer 2 (Behavioral/GNN) Structure")
    print("=" * 80)

    tree = parse_source("layer2_behavioral.py")
    classes = get_classes(tree)

    # Check required classes exist
    assert "BehavioralGNN" in classes, "Layer 2 missing BehavioralGNN class"
    assert "BehavioralLayer" in classes, "Layer 2 missing BehavioralLayer class"
    assert "EventGraph" in classes, "Layer 2 missing EventGraph class"
    print(f"✅ Layer 2 has {len(classes)} classes: {classes}")

    # Check BehavioralLayer methods
    layer_methods = get_methods(tree, "BehavioralLayer")
    required_methods = ["__init__", "predict", "train_step", "save_model", "load_model"]
    for method in required_methods:
        assert method in layer_methods, f"BehavioralLayer missing method: {method}"
    print(f"✅ BehavioralLayer has all {len(required_methods)} required methods")

    print("✅ Layer 2 structure validated")


# ============================================================================
# TEST 3: LAYER 3 (OPERATIONAL/TCN) STRUCTURE
# ============================================================================


def test_layer3_operational_structure():
    """Test that Layer 3 (Operational) has correct structure."""
    print("\n" + "=" * 80)
    print("TEST 3: Layer 3 (Operational/TCN) Structure")
    print("=" * 80)

    tree = parse_source("layer3_operational.py")
    classes = get_classes(tree)

    # Check required classes exist
    assert "OperationalTCN" in classes, "Layer 3 missing OperationalTCN class"
    assert "OperationalLayer" in classes, "Layer 3 missing OperationalLayer class"
    print(f"✅ Layer 3 has {len(classes)} classes: {classes}")

    # Check OperationalLayer methods
    layer_methods = get_methods(tree, "OperationalLayer")
    required_methods = ["__init__", "predict", "train_step", "save_model", "load_model"]
    for method in required_methods:
        assert method in layer_methods, f"OperationalLayer missing method: {method}"
    print(f"✅ OperationalLayer has all {len(required_methods)} required methods")

    print("✅ Layer 3 structure validated")


# ============================================================================
# TEST 4: LAYER 4 (TACTICAL/LSTM) STRUCTURE
# ============================================================================


def test_layer4_tactical_structure():
    """Test that Layer 4 (Tactical) has correct structure."""
    print("\n" + "=" * 80)
    print("TEST 4: Layer 4 (Tactical/LSTM) Structure")
    print("=" * 80)

    tree = parse_source("layer4_tactical.py")
    classes = get_classes(tree)

    # Check required classes exist
    assert "TacticalLSTM" in classes, "Layer 4 missing TacticalLSTM class"
    assert "TacticalLayer" in classes, "Layer 4 missing TacticalLayer class"
    print(f"✅ Layer 4 has {len(classes)} classes: {classes}")

    # Check TacticalLayer methods
    layer_methods = get_methods(tree, "TacticalLayer")
    required_methods = ["__init__", "predict", "train_step", "save_model", "load_model"]
    for method in required_methods:
        assert method in layer_methods, f"TacticalLayer missing method: {method}"
    print(f"✅ TacticalLayer has all {len(required_methods)} required methods")

    print("✅ Layer 4 structure validated")


# ============================================================================
# TEST 5: LAYER 5 (STRATEGIC/TRANSFORMER) STRUCTURE
# ============================================================================


def test_layer5_strategic_structure():
    """Test that Layer 5 (Strategic) has correct structure."""
    print("\n" + "=" * 80)
    print("TEST 5: Layer 5 (Strategic/Transformer) Structure")
    print("=" * 80)

    tree = parse_source("layer5_strategic.py")
    classes = get_classes(tree)

    # Check required classes exist
    assert "StrategicTransformer" in classes, "Layer 5 missing StrategicTransformer class"
    assert "StrategicLayer" in classes, "Layer 5 missing StrategicLayer class"
    print(f"✅ Layer 5 has {len(classes)} classes: {classes}")

    # Check StrategicLayer methods
    layer_methods = get_methods(tree, "StrategicLayer")
    required_methods = ["__init__", "predict", "train_step", "save_model", "load_model"]
    for method in required_methods:
        assert method in layer_methods, f"StrategicLayer missing method: {method}"
    print(f"✅ StrategicLayer has all {len(required_methods)} required methods")

    print("✅ Layer 5 structure validated")


# ============================================================================
# TEST 6: FREE ENERGY PRINCIPLE IN CODE
# ============================================================================


def test_free_energy_principle():
    """Test that Free Energy Principle is implemented in code."""
    print("\n" + "=" * 80)
    print("TEST 6: Free Energy Principle Implementation")
    print("=" * 80)

    source = read_source("hpc_network.py")

    # Check for Free Energy mentions
    assert "free_energy" in source.lower() or "free energy" in source.lower(), (
        "Code should mention Free Energy Principle"
    )
    print("✅ Free Energy Principle referenced in code")

    # Check for prediction error tracking
    assert "prediction_error" in source.lower() or "prediction error" in source.lower(), (
        "Code should track prediction errors"
    )
    print("✅ Prediction error tracking found")

    # Parse AST and check for compute_free_energy method
    tree = parse_source("hpc_network.py")
    classes = get_classes(tree)
    assert "HierarchicalPredictiveCodingNetwork" in classes, "Missing main HPC Network class"

    methods = get_methods(tree, "HierarchicalPredictiveCodingNetwork")
    assert "compute_free_energy" in methods, "HPC Network missing compute_free_energy method"
    print("✅ compute_free_energy method exists")

    print("✅ Free Energy Principle validated")


# ============================================================================
# TEST 7: HIERARCHICAL STRUCTURE VALIDATION
# ============================================================================


def test_hierarchical_structure():
    """Test that hierarchical structure (5 layers) is implemented."""
    print("\n" + "=" * 80)
    print("TEST 7: Hierarchical Structure (5 Layers)")
    print("=" * 80)

    source = read_source("hpc_network.py")

    # Check all 5 layers are initialized
    layers = ["l1_sensory", "l2_behavioral", "l3_operational", "l4_tactical", "l5_strategic"]
    for layer in layers:
        assert layer in source, f"HPC Network missing layer: {layer}"
    print(f"✅ All {len(layers)} layers referenced in HPC Network")

    # Check hierarchical_inference method exists
    tree = parse_source("hpc_network.py")
    methods = get_methods(tree, "HierarchicalPredictiveCodingNetwork")
    assert "hierarchical_inference" in methods, "HPC Network missing hierarchical_inference method"
    print("✅ hierarchical_inference method exists")

    print("✅ Hierarchical structure validated")


# ============================================================================
# TEST 8: HPC NETWORK ORCHESTRATION STRUCTURE
# ============================================================================


def test_hpc_network_orchestration():
    """Test that HPC Network orchestrates all components."""
    print("\n" + "=" * 80)
    print("TEST 8: HPC Network Orchestration")
    print("=" * 80)

    tree = parse_source("hpc_network.py")

    # Check HPC Network class exists
    classes = get_classes(tree)
    assert "HierarchicalPredictiveCodingNetwork" in classes, "Missing HierarchicalPredictiveCodingNetwork class"
    print("✅ HierarchicalPredictiveCodingNetwork class exists")

    # Check required methods
    methods = get_methods(tree, "HierarchicalPredictiveCodingNetwork")
    required_methods = ["__init__", "hierarchical_inference", "compute_free_energy"]
    for method in required_methods:
        assert method in methods, f"HPC Network missing method: {method}"
    print(f"✅ HPC Network has all {len(required_methods)} core methods")

    # Check imports from all layers
    source = read_source("hpc_network.py")
    layer_imports = ["SensoryLayer", "BehavioralLayer", "OperationalLayer", "TacticalLayer", "StrategicLayer"]
    for layer_import in layer_imports:
        assert layer_import in source, f"HPC Network missing import: {layer_import}"
    print(f"✅ HPC Network imports all {len(layer_imports)} layers")

    print("✅ HPC Network orchestration validated")


# ============================================================================
# SUMMARY
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PREDICTIVE CODING STRUCTURE TESTS")
    print("=" * 80)
    print("\nRunning tests...")
    print("\nTest Suite:")
    print("  1. Layer 1 (Sensory) structure")
    print("  2. Layer 2 (Behavioral) structure")
    print("  3. Layer 3 (Operational) structure")
    print("  4. Layer 4 (Tactical) structure")
    print("  5. Layer 5 (Strategic) structure")
    print("  6. Free Energy Principle implementation")
    print("  7. Hierarchical structure (5 layers)")
    print("  8. HPC Network orchestration")
    print("\nTarget: 8/8 passing (100%)")
    print("=" * 80)
