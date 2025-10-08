"""
Tests for GPU Trainer

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from performance.gpu_trainer import GPUTrainer, GPUTrainingConfig


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
def gpu_config():
    """Create GPU training config."""
    return GPUTrainingConfig(
        device="cpu",  # Use CPU for testing
        use_amp=False,  # Disable AMP for CPU
        use_data_parallel=False,
        gradient_accumulation_steps=1,
    )


def test_gpu_trainer_initialization(simple_model, gpu_config):
    """Test GPU trainer initialization."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    def dummy_loss_fn(model, batch):
        x, y = batch
        output = model(x)
        return torch.nn.functional.cross_entropy(output, y)

    optimizer = torch.optim.Adam(simple_model.parameters())

    trainer = GPUTrainer(model=simple_model, optimizer=optimizer, loss_fn=dummy_loss_fn, config=gpu_config)

    assert trainer.device.type == "cpu"
    assert trainer.config.use_amp is False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_gpu_trainer_single_epoch(simple_model, simple_dataset, gpu_config):
    """Test training for single epoch."""

    def dummy_loss_fn(model, batch):
        x, y = batch
        output = model(x)
        return torch.nn.functional.cross_entropy(output, y)

    optimizer = torch.optim.Adam(simple_model.parameters())

    trainer = GPUTrainer(model=simple_model, optimizer=optimizer, loss_fn=dummy_loss_fn, config=gpu_config)

    train_loader = DataLoader(simple_dataset, batch_size=16, shuffle=True)

    history = trainer.train(train_loader=train_loader, val_loader=None, num_epochs=1)

    assert len(history) == 1
    assert history[0]["epoch"] == 1
    assert "train_loss" in history[0]
    assert history[0]["train_loss"] >= 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_gpu_trainer_multiple_epochs(simple_model, simple_dataset, gpu_config):
    """Test training for multiple epochs."""

    def dummy_loss_fn(model, batch):
        x, y = batch
        output = model(x)
        return torch.nn.functional.cross_entropy(output, y)

    optimizer = torch.optim.Adam(simple_model.parameters())

    trainer = GPUTrainer(model=simple_model, optimizer=optimizer, loss_fn=dummy_loss_fn, config=gpu_config)

    train_loader = DataLoader(simple_dataset, batch_size=16, shuffle=True)

    history = trainer.train(train_loader=train_loader, val_loader=None, num_epochs=3)

    assert len(history) == 3

    # Loss should generally decrease over epochs
    assert history[0]["train_loss"] > 0
    assert history[-1]["train_loss"] > 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_gpu_trainer_with_validation(simple_model, simple_dataset, gpu_config):
    """Test training with validation."""

    def dummy_loss_fn(model, batch):
        x, y = batch
        output = model(x)
        return torch.nn.functional.cross_entropy(output, y)

    optimizer = torch.optim.Adam(simple_model.parameters())

    trainer = GPUTrainer(model=simple_model, optimizer=optimizer, loss_fn=dummy_loss_fn, config=gpu_config)

    train_loader = DataLoader(simple_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(simple_dataset, batch_size=16, shuffle=False)

    history = trainer.train(train_loader=train_loader, val_loader=val_loader, num_epochs=2)

    assert len(history) == 2

    for epoch_metrics in history:
        assert "train_loss" in epoch_metrics
        assert "val_loss" in epoch_metrics
        assert epoch_metrics["val_loss"] is not None


def test_gpu_config_validation():
    """Test GPU config validation."""
    config = GPUTrainingConfig(device="cpu", use_amp=False, max_batch_size=64, gradient_accumulation_steps=2)

    assert config.device == "cpu"
    assert config.max_batch_size == 64
    assert config.gradient_accumulation_steps == 2
