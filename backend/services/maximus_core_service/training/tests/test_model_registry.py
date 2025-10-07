"""
Tests for Model Registry Module

Tests:
1. test_model_registration - Register and retrieve models
2. test_stage_transitions - Model stage lifecycle

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from training.model_registry import ModelRegistry, ModelMetadata


def test_model_registration(temp_dir, simple_pytorch_model):
    """Test model registration and retrieval.

    Verifies:
    - Models can be registered
    - Metadata is saved correctly
    - Models can be retrieved
    - Version management works
    """
    # Skip if PyTorch not available
    if simple_pytorch_model is None:
        pytest.skip("PyTorch not available")

    try:
        import torch
    except ImportError:
        pytest.skip("PyTorch not available")

    # Create registry
    registry = ModelRegistry(registry_dir=temp_dir / "registry")

    # Save model checkpoint
    checkpoint_path = temp_dir / "model_v1.pt"
    torch.save(simple_pytorch_model.state_dict(), checkpoint_path)

    # Create metadata
    metadata = ModelMetadata(
        model_name="test_model",
        version="v1.0.0",
        layer_name="layer1",
        created_at=datetime.utcnow(),
        metrics={"val_loss": 0.045, "accuracy": 0.95},
        hyperparameters={"learning_rate": 1e-3, "batch_size": 32},
        training_dataset="training/data/train.npz"
    )

    # Register model
    registered_path = registry.register_model(
        model_path=checkpoint_path,
        metadata=metadata
    )

    # Verify registration
    assert registered_path.exists(), f"Registered model not found at {registered_path}"

    # Retrieve model
    retrieved_path = registry.get_model("test_model", version="v1.0.0")
    assert retrieved_path is not None, "Failed to retrieve registered model"
    assert retrieved_path.exists(), f"Retrieved model path doesn't exist: {retrieved_path}"

    # Verify metadata
    retrieved_metadata = registry.get_metadata("test_model", "v1.0.0")
    assert retrieved_metadata is not None, "Failed to retrieve metadata"
    assert retrieved_metadata.model_name == "test_model"
    assert retrieved_metadata.version == "v1.0.0"
    assert retrieved_metadata.metrics["val_loss"] == 0.045
    assert retrieved_metadata.metrics["accuracy"] == 0.95

    # Register second version
    checkpoint_path_v2 = temp_dir / "model_v2.pt"
    torch.save(simple_pytorch_model.state_dict(), checkpoint_path_v2)

    metadata_v2 = ModelMetadata(
        model_name="test_model",
        version="v2.0.0",
        layer_name="layer1",
        created_at=datetime.utcnow(),
        metrics={"val_loss": 0.030, "accuracy": 0.97},
        hyperparameters={"learning_rate": 5e-4, "batch_size": 64},
        training_dataset="training/data/train_v2.npz"
    )

    registry.register_model(checkpoint_path_v2, metadata_v2)

    # List models
    models = registry.list_models("test_model")
    assert "test_model" in models
    assert len(models["test_model"]) == 2, f"Expected 2 versions, got {len(models['test_model'])}"
    assert "v1.0.0" in models["test_model"]
    assert "v2.0.0" in models["test_model"]

    # Get latest version (without specifying version)
    latest_path = registry.get_model("test_model")
    assert latest_path is not None

    # Compare models
    comparison = registry.compare_models("test_model", ["v1.0.0", "v2.0.0"], metric="val_loss")
    assert comparison["v1.0.0"] == 0.045
    assert comparison["v2.0.0"] == 0.030

    # Search models
    results = registry.search_models(layer_name="layer1", min_accuracy=0.9)
    assert len(results) == 2, f"Expected 2 models with accuracy >= 0.9, got {len(results)}"


def test_stage_transitions(temp_dir, simple_pytorch_model):
    """Test model stage lifecycle.

    Verifies:
    - Models can transition between stages
    - Promoting to production demotes old production models
    - Stage filtering works
    """
    # Skip if PyTorch not available
    if simple_pytorch_model is None:
        pytest.skip("PyTorch not available")

    try:
        import torch
    except ImportError:
        pytest.skip("PyTorch not available")

    # Create registry
    registry = ModelRegistry(registry_dir=temp_dir / "registry_stages")

    # Register model v1
    checkpoint_path_v1 = temp_dir / "model_v1_stage.pt"
    torch.save(simple_pytorch_model.state_dict(), checkpoint_path_v1)

    metadata_v1 = ModelMetadata(
        model_name="test_model",
        version="v1.0.0",
        layer_name="layer1",
        created_at=datetime.utcnow(),
        metrics={"val_loss": 0.050, "accuracy": 0.93},
        hyperparameters={},
        stage="none"
    )

    registry.register_model(checkpoint_path_v1, metadata_v1)

    # Verify initial stage
    metadata = registry.get_metadata("test_model", "v1.0.0")
    assert metadata.stage == "none"

    # Transition to staging
    success = registry.transition_stage("test_model", "v1.0.0", "staging")
    assert success, "Failed to transition to staging"

    metadata = registry.get_metadata("test_model", "v1.0.0")
    assert metadata.stage == "staging"

    # Transition to production
    success = registry.transition_stage("test_model", "v1.0.0", "production")
    assert success, "Failed to transition to production"

    metadata = registry.get_metadata("test_model", "v1.0.0")
    assert metadata.stage == "production"

    # Register model v2
    checkpoint_path_v2 = temp_dir / "model_v2_stage.pt"
    torch.save(simple_pytorch_model.state_dict(), checkpoint_path_v2)

    metadata_v2 = ModelMetadata(
        model_name="test_model",
        version="v2.0.0",
        layer_name="layer1",
        created_at=datetime.utcnow(),
        metrics={"val_loss": 0.030, "accuracy": 0.97},
        hyperparameters={},
        stage="staging"
    )

    registry.register_model(checkpoint_path_v2, metadata_v2)

    # Promote v2 to production (should demote v1)
    success = registry.transition_stage("test_model", "v2.0.0", "production")
    assert success, "Failed to promote v2 to production"

    # Verify v2 is production
    metadata_v2 = registry.get_metadata("test_model", "v2.0.0")
    assert metadata_v2.stage == "production"

    # Verify v1 was demoted to archived
    metadata_v1 = registry.get_metadata("test_model", "v1.0.0")
    assert metadata_v1.stage == "archived", \
        f"Expected v1 to be archived, but stage is {metadata_v1.stage}"

    # Get production model
    production_path = registry.get_model("test_model", stage="production")
    assert production_path is not None

    # Verify it's v2
    production_metadata = registry.search_models(model_name="test_model", stage="production")
    assert len(production_metadata) == 1
    assert production_metadata[0].version == "v2.0.0"

    # Get archived models
    archived_models = registry.search_models(model_name="test_model", stage="archived")
    assert len(archived_models) == 1
    assert archived_models[0].version == "v1.0.0"

    # Invalid stage should fail
    success = registry.transition_stage("test_model", "v2.0.0", "invalid_stage")
    assert not success, "Invalid stage transition should fail"
