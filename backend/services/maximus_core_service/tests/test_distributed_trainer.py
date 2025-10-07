"""
Tests for Distributed Trainer

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest

try:
    import torch
    import torch.nn as nn
    import torch.distributed as dist
    from torch.utils.data import TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from performance.distributed_trainer import DistributedTrainer, DistributedConfig


@pytest.fixture
def simple_model():
    """Create simple model for testing."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(10, 5)

        def forward(self, x):
            return self.fc(x)

    return SimpleModel()


@pytest.fixture
def simple_dataset():
    """Create simple dataset for testing."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    X = torch.randn(100, 10)
    y = torch.randint(0, 5, (100,))

    return TensorDataset(X, y)


@pytest.fixture
def dist_config():
    """Create distributed config for single process testing."""
    return DistributedConfig(
        backend="gloo",  # Use gloo for CPU testing
        world_size=1,
        rank=0,
        batch_size_per_gpu=16,
        sync_batch_norm=False  # Disable for single process
    )


def test_distributed_config_validation():
    """Test distributed config validation."""
    config = DistributedConfig(
        backend="nccl",
        world_size=4,
        rank=0,
        batch_size_per_gpu=32
    )

    assert config.backend == "nccl"
    assert config.world_size == 4
    assert config.rank == 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_distributed_trainer_single_process(simple_model, simple_dataset, dist_config):
    """Test distributed trainer with single process (no actual distribution)."""

    def dummy_loss_fn(model, batch):
        x, y = batch
        output = model(x)
        return torch.nn.functional.cross_entropy(output, y)

    optimizer = torch.optim.Adam(simple_model.parameters())

    # Note: This test runs in single-process mode (world_size=1)
    # Full distributed testing requires multi-process setup

    trainer = DistributedTrainer(
        model=simple_model,
        optimizer=optimizer,
        loss_fn=dummy_loss_fn,
        config=dist_config
    )

    assert trainer.world_size == 1
    assert trainer.rank == 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_distributed_trainer_is_main_process(simple_model, dist_config):
    """Test main process check."""

    def dummy_loss_fn(model, batch):
        x, y = batch
        output = model(x)
        return torch.nn.functional.cross_entropy(output, y)

    optimizer = torch.optim.Adam(simple_model.parameters())

    trainer = DistributedTrainer(
        model=simple_model,
        optimizer=optimizer,
        loss_fn=dummy_loss_fn,
        config=dist_config
    )

    # With rank=0, should be main process
    assert trainer.is_main_process() is True


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_distributed_trainer_device_setup(simple_model, dist_config):
    """Test device setup."""

    def dummy_loss_fn(model, batch):
        x, y = batch
        output = model(x)
        return torch.nn.functional.cross_entropy(output, y)

    optimizer = torch.optim.Adam(simple_model.parameters())

    trainer = DistributedTrainer(
        model=simple_model,
        optimizer=optimizer,
        loss_fn=dummy_loss_fn,
        config=dist_config
    )

    # Should set device (CPU or CUDA)
    assert trainer.device is not None


def test_distributed_utility_functions():
    """Test distributed utility functions."""
    from performance.distributed_trainer import (
        get_rank,
        get_world_size,
        is_dist_available_and_initialized
    )

    # When not initialized, should return safe defaults
    rank = get_rank()
    world_size = get_world_size()

    assert rank == 0  # Default rank
    assert world_size == 1  # Default world size

    # Check availability
    available = is_dist_available_and_initialized()
    # May be True or False depending on environment
    assert isinstance(available, bool)
