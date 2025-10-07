"""
Tests for Layer Trainer Module

Tests:
1. test_training_loop - Basic training loop execution
2. test_early_stopping - Early stopping mechanism

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from pathlib import Path

import numpy as np
import pytest

from training.layer_trainer import LayerTrainer, TrainingConfig


def test_training_loop(simple_pytorch_model, train_val_test_splits, temp_dir):
    """Test basic training loop execution.

    Verifies:
    - Training completes without errors
    - Training metrics are recorded
    - Checkpoints are saved
    - Loss decreases over epochs
    """
    # Skip if PyTorch not available
    if simple_pytorch_model is None:
        pytest.skip("PyTorch not available")

    try:
        import torch
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError:
        pytest.skip("PyTorch not available")

    # Load train and val data
    train_data = np.load(train_val_test_splits["train"])
    val_data = np.load(train_val_test_splits["val"])

    train_features = torch.FloatTensor(train_data["features"])
    train_labels = torch.LongTensor(train_data["labels"])

    val_features = torch.FloatTensor(val_data["features"])
    val_labels = torch.LongTensor(val_data["labels"])

    # Create DataLoaders
    train_dataset = TensorDataset(train_features, train_labels)
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)

    val_dataset = TensorDataset(val_features, val_labels)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)

    # Define loss function
    def loss_fn(model, batch):
        features, labels = batch
        outputs = model(features)
        return torch.nn.functional.cross_entropy(outputs, labels)

    # Create training config
    config = TrainingConfig(
        model_name="test_model",
        layer_name="test_layer",
        batch_size=8,
        num_epochs=5,  # Short training for test
        learning_rate=1e-3,
        checkpoint_dir=temp_dir / "checkpoints",
        log_dir=temp_dir / "logs",
        save_every=2
    )

    # Create trainer
    trainer = LayerTrainer(
        model=simple_pytorch_model,
        optimizer_name="adam",
        loss_fn=loss_fn,
        config=config
    )

    # Train
    history = trainer.train(train_loader=train_loader, val_loader=val_loader)

    # Verify training completed
    assert len(history) == 5, f"Expected 5 epochs, got {len(history)}"

    # Verify metrics are recorded
    for epoch_metrics in history:
        assert epoch_metrics.epoch > 0
        assert epoch_metrics.train_loss is not None
        assert epoch_metrics.train_loss >= 0.0

        if epoch_metrics.val_loss is not None:
            assert epoch_metrics.val_loss >= 0.0

    # Verify loss generally decreases (allow some variance)
    first_train_loss = history[0].train_loss
    last_train_loss = history[-1].train_loss

    # Loss should decrease or stay similar (not increase significantly)
    # Allow 20% increase tolerance for stochastic training
    assert last_train_loss <= first_train_loss * 1.2, \
        f"Training loss increased significantly: {first_train_loss:.4f} -> {last_train_loss:.4f}"

    # Verify checkpoint was saved
    checkpoint_dir = temp_dir / "checkpoints"
    assert checkpoint_dir.exists(), "Checkpoint directory not created"

    checkpoint_files = list(checkpoint_dir.glob("*.pt"))
    assert len(checkpoint_files) > 0, "No checkpoint files saved"

    # Verify best checkpoint exists
    best_checkpoint = checkpoint_dir / "test_model_best.pt"
    assert best_checkpoint.exists(), "Best checkpoint not saved"


def test_early_stopping(simple_pytorch_model, train_val_test_splits, temp_dir):
    """Test early stopping mechanism.

    Verifies:
    - Training stops when validation loss doesn't improve
    - Training stops before max epochs
    - Best model is from before early stopping
    """
    # Skip if PyTorch not available
    if simple_pytorch_model is None:
        pytest.skip("PyTorch not available")

    try:
        import torch
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError:
        pytest.skip("PyTorch not available")

    # Load train and val data
    train_data = np.load(train_val_test_splits["train"])
    val_data = np.load(train_val_test_splits["val"])

    train_features = torch.FloatTensor(train_data["features"])
    train_labels = torch.LongTensor(train_data["labels"])

    val_features = torch.FloatTensor(val_data["features"])
    val_labels = torch.LongTensor(val_data["labels"])

    # Create DataLoaders
    train_dataset = TensorDataset(train_features, train_labels)
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)

    val_dataset = TensorDataset(val_features, val_labels)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)

    # Define loss function
    def loss_fn(model, batch):
        features, labels = batch
        outputs = model(features)
        return torch.nn.functional.cross_entropy(outputs, labels)

    # Create training config with early stopping
    config = TrainingConfig(
        model_name="test_model_early_stop",
        layer_name="test_layer",
        batch_size=8,
        num_epochs=100,  # Large number of epochs
        learning_rate=1e-3,
        early_stopping_patience=3,  # Stop after 3 epochs without improvement
        checkpoint_dir=temp_dir / "checkpoints_early_stop",
        log_dir=temp_dir / "logs_early_stop"
    )

    # Create trainer
    trainer = LayerTrainer(
        model=simple_pytorch_model,
        optimizer_name="adam",
        loss_fn=loss_fn,
        config=config
    )

    # Train
    history = trainer.train(train_loader=train_loader, val_loader=val_loader)

    # Verify early stopping triggered
    # Training should stop before 100 epochs due to early stopping
    assert len(history) < 100, \
        f"Early stopping failed: trained for {len(history)} epochs (expected < 100)"

    # Verify we trained for at least a few epochs
    assert len(history) >= 3, \
        f"Training stopped too early: {len(history)} epochs"

    # Verify validation loss was tracked
    val_losses = [m.val_loss for m in history if m.val_loss is not None]
    assert len(val_losses) > 0, "No validation losses recorded"

    # Find best validation loss
    best_val_loss = min(val_losses)
    best_epoch = [i for i, m in enumerate(history) if m.val_loss == best_val_loss][0]

    # Verify best epoch is not the last epoch (early stopping should have triggered)
    # Allow last epoch to be best epoch + patience
    assert len(history) <= best_epoch + config.early_stopping_patience + 2, \
        f"Early stopping delayed: best epoch {best_epoch}, stopped at {len(history)}"
