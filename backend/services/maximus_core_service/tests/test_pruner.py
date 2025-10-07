"""
Tests for Model Pruner

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from performance.pruner import ModelPruner, PruningConfig, PruningResult


@pytest.fixture
def simple_model():
    """Create simple model for testing."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(128, 64)
            self.fc2 = nn.Linear(64, 32)

        def forward(self, x):
            x = self.fc1(x)
            x = torch.relu(x)
            x = self.fc2(x)
            return x

    return SimpleModel()


@pytest.fixture
def pruning_config(tmp_path):
    """Create pruning config."""
    return PruningConfig(
        pruning_type="unstructured",
        pruning_method="l1",
        target_sparsity=0.3,
        iterative=False,
        output_dir=tmp_path / "pruned"
    )


def test_pruner_initialization(pruning_config):
    """Test pruner initialization."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    pruner = ModelPruner(config=pruning_config)

    assert pruner.config.pruning_type == "unstructured"
    assert pruner.config.target_sparsity == 0.3


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_unstructured_pruning(simple_model, pruning_config):
    """Test unstructured pruning."""
    pruner = ModelPruner(config=pruning_config)

    pruned_model = pruner.prune(simple_model)

    # Verify model is pruned
    assert pruned_model is not None

    # Test inference still works
    dummy_input = torch.randn(4, 128)
    output = pruned_model(dummy_input)

    assert output.shape == (4, 32)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_analyze_sparsity(simple_model, pruning_config):
    """Test sparsity analysis."""
    pruner = ModelPruner(config=pruning_config)

    # Prune model
    pruned_model = pruner.prune(simple_model)

    # Analyze sparsity
    result = pruner.analyze_sparsity(pruned_model)

    assert isinstance(result, PruningResult)
    assert result.original_params > 0
    assert result.sparsity_achieved >= 0.0
    assert result.sparsity_achieved <= 1.0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_pruning_achieves_target_sparsity(simple_model, pruning_config):
    """Test that pruning achieves approximately target sparsity."""
    target_sparsity = 0.5
    pruning_config.target_sparsity = target_sparsity

    pruner = ModelPruner(config=pruning_config)

    pruned_model = pruner.prune(simple_model)
    result = pruner.analyze_sparsity(pruned_model)

    # Should achieve close to target sparsity (within 20% margin)
    assert abs(result.sparsity_achieved - target_sparsity) < 0.2


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_pruning_preserves_functionality(simple_model, pruning_config):
    """Test that pruned model still produces outputs."""
    pruner = ModelPruner(config=pruning_config)

    pruned_model = pruner.prune(simple_model)

    # Test with various inputs
    for batch_size in [1, 4, 8]:
        dummy_input = torch.randn(batch_size, 128)
        output = pruned_model(dummy_input)

        assert output.shape == (batch_size, 32)
        assert not torch.isnan(output).any()


def test_structured_pruning_config():
    """Test structured pruning configuration."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    config = PruningConfig(
        pruning_type="structured",
        pruning_method="l1",
        target_sparsity=0.4
    )

    pruner = ModelPruner(config=config)
    assert pruner.config.pruning_type == "structured"


def test_pruning_config_validation():
    """Test pruning config validation."""
    # Valid config
    config = PruningConfig(target_sparsity=0.5)
    assert config.target_sparsity == 0.5

    # Invalid sparsity should raise error
    with pytest.raises(ValueError):
        PruningConfig(target_sparsity=1.5)

    with pytest.raises(ValueError):
        PruningConfig(target_sparsity=-0.1)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_pruning_result_to_dict(simple_model, pruning_config):
    """Test pruning result conversion to dict."""
    pruner = ModelPruner(config=pruning_config)

    pruned_model = pruner.prune(simple_model)
    result = pruner.analyze_sparsity(pruned_model)

    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert "original_params" in result_dict
    assert "sparsity_achieved" in result_dict
    assert "size_reduction_pct" in result_dict
