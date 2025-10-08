"""
Pytest Fixtures for Training Pipeline Tests

Shared fixtures:
- Synthetic security events
- Temporary directories
- Mock data sources
- Test models

REGRA DE OURO: Zero mocks, production-ready fixtures
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs.

    Yields:
        Path: Temporary directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def synthetic_events() -> list[dict]:
    """Generate synthetic security events for testing.

    Returns:
        List of synthetic event dictionaries
    """
    events = []
    base_time = datetime(2025, 10, 1, 12, 0, 0)

    event_types = ["network_connection", "process_creation", "file_access", "user_login"]
    severities = ["low", "medium", "high", "critical"]

    for i in range(100):
        event = {
            "event_id": f"evt_{i:04d}",
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "event_type": event_types[i % len(event_types)],
            "severity": severities[i % len(severities)],
            "source": "test_sensor",
            # Network features
            "source_ip": f"192.168.1.{(i % 254) + 1}",
            "dest_ip": f"10.0.0.{(i % 254) + 1}",
            "source_port": 1024 + (i % 60000),
            "dest_port": 80 + (i % 10),
            "protocol": ["tcp", "udp", "icmp"][i % 3],
            "bytes_sent": 1024 * (i % 100),
            "bytes_received": 512 * (i % 50),
            # Process features
            "process_name": f"process_{i % 10}",
            "process_id": 1000 + i,
            "process_path": f"/usr/bin/process_{i % 10}",
            "parent_process_id": 1000 + (i // 2),
            "parent_process_name": f"parent_{i % 5}",
            "command_line": f"process_{i % 10} --arg{i}",
            # File features
            "file_path": f"/var/log/file_{i % 20}.log",
            "file_hash": f"{'a' * 32}{i:04d}",
            "file_size": 1024 * (i % 1000),
            "file_extension": [".log", ".txt", ".exe", ".dll"][i % 4],
            # User features
            "user_name": f"user_{i % 10}",
            "user_id": 1000 + (i % 10),
            "user_domain": "test.local",
            # Label (for supervised learning)
            "label": i % 3,  # 3 classes: 0=benign, 1=suspicious, 2=malicious
            # Raw data
            "raw": f"Raw event data {i}",
        }

        events.append(event)

    return events


@pytest.fixture
def synthetic_events_file(temp_dir, synthetic_events) -> Path:
    """Create JSON file with synthetic events.

    Args:
        temp_dir: Temporary directory fixture
        synthetic_events: Synthetic events fixture

    Returns:
        Path to JSON file
    """
    events_file = temp_dir / "synthetic_events.json"

    with open(events_file, "w") as f:
        json.dump(synthetic_events, f, indent=2)

    return events_file


@pytest.fixture
def synthetic_features() -> np.ndarray:
    """Generate synthetic feature matrix.

    Returns:
        Feature matrix (100, 128)
    """
    np.random.seed(42)
    return np.random.randn(100, 128).astype(np.float32)


@pytest.fixture
def synthetic_labels() -> np.ndarray:
    """Generate synthetic labels.

    Returns:
        Label vector (100,)
    """
    np.random.seed(42)
    return np.random.randint(0, 3, size=100, dtype=np.int64)


@pytest.fixture
def synthetic_dataset(synthetic_features, synthetic_labels, temp_dir) -> Path:
    """Create synthetic dataset file.

    Args:
        synthetic_features: Feature matrix
        synthetic_labels: Label vector
        temp_dir: Temporary directory

    Returns:
        Path to dataset file (.npz)
    """
    dataset_path = temp_dir / "dataset.npz"

    sample_ids = [f"sample_{i:04d}" for i in range(len(synthetic_features))]

    np.savez(dataset_path, features=synthetic_features, labels=synthetic_labels, sample_ids=np.array(sample_ids))

    return dataset_path


@pytest.fixture
def train_val_test_splits(synthetic_features, synthetic_labels, temp_dir) -> dict[str, Path]:
    """Create train/val/test split files.

    Args:
        synthetic_features: Feature matrix
        synthetic_labels: Label vector
        temp_dir: Temporary directory

    Returns:
        Dictionary mapping split name to path
    """
    # Split indices
    n_samples = len(synthetic_features)
    indices = np.arange(n_samples)
    np.random.seed(42)
    np.random.shuffle(indices)

    n_train = int(0.7 * n_samples)
    n_val = int(0.15 * n_samples)

    train_indices = indices[:n_train]
    val_indices = indices[n_train : n_train + n_val]
    test_indices = indices[n_train + n_val :]

    splits = {}

    for split_name, split_indices in [("train", train_indices), ("val", val_indices), ("test", test_indices)]:
        split_path = temp_dir / f"{split_name}.npz"

        sample_ids = [f"sample_{i:04d}" for i in split_indices]

        np.savez(
            split_path,
            features=synthetic_features[split_indices],
            labels=synthetic_labels[split_indices],
            sample_ids=np.array(sample_ids),
        )

        splits[split_name] = split_path

    return splits


@pytest.fixture
def simple_pytorch_model():
    """Create simple PyTorch model for testing.

    Returns:
        PyTorch model or None if torch not available
    """
    try:
        import torch
        import torch.nn as nn

        class SimpleModel(nn.Module):
            """Simple feedforward model for testing."""

            def __init__(self, input_dim=128, hidden_dim=64, output_dim=3):
                super().__init__()
                self.layers = nn.Sequential(
                    nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, output_dim)
                )

            def forward(self, x):
                return self.layers(x)

        return SimpleModel()

    except ImportError:
        return None
