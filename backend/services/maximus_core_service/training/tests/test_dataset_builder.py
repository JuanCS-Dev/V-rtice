"""
Tests for Dataset Builder Module

Tests:
1. test_stratified_split - Stratified train/val/test split
2. test_temporal_split - Temporal split (chronological)
3. test_pytorch_dataset_wrapper - PyTorch Dataset compatibility

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import numpy as np
import pytest

from training.dataset_builder import DatasetBuilder, DatasetSplit, PyTorchDatasetWrapper, SplitStrategy


def test_stratified_split(synthetic_features, synthetic_labels, temp_dir):
    """Test stratified train/val/test split.

    Verifies:
    - Class distribution is balanced across splits
    - Split ratios are respected
    - No data leakage between splits
    """
    # Create dataset builder
    sample_ids = [f"sample_{i:04d}" for i in range(len(synthetic_features))]

    builder = DatasetBuilder(
        features=synthetic_features, labels=synthetic_labels, sample_ids=sample_ids, output_dir=temp_dir, random_seed=42
    )

    # Create stratified splits
    splits = builder.create_splits(strategy=SplitStrategy.STRATIFIED, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)

    # Verify splits exist
    assert "train" in splits
    assert "val" in splits
    assert "test" in splits

    # Verify split sizes
    n_total = len(synthetic_features)
    n_train = len(splits["train"].features)
    n_val = len(splits["val"].features)
    n_test = len(splits["test"].features)

    assert n_train + n_val + n_test == n_total, (
        f"Split sizes don't sum to total: {n_train} + {n_val} + {n_test} != {n_total}"
    )

    # Verify split ratios (allow 5% tolerance)
    assert abs(n_train / n_total - 0.7) < 0.05, f"Train ratio {n_train / n_total:.2f} far from 0.7"
    assert abs(n_val / n_total - 0.15) < 0.05, f"Val ratio {n_val / n_total:.2f} far from 0.15"
    assert abs(n_test / n_total - 0.15) < 0.05, f"Test ratio {n_test / n_total:.2f} far from 0.15"

    # Verify class distribution (stratification)
    unique_labels = np.unique(synthetic_labels)

    for label in unique_labels:
        # Count in original dataset
        n_label_total = (synthetic_labels == label).sum()

        # Count in splits
        n_label_train = (splits["train"].labels == label).sum()
        n_label_val = (splits["val"].labels == label).sum()
        n_label_test = (splits["test"].labels == label).sum()

        # Verify all samples are accounted for
        assert n_label_train + n_label_val + n_label_test == n_label_total, (
            f"Class {label} samples don't sum: {n_label_train} + {n_label_val} + {n_label_test} != {n_label_total}"
        )

        # Verify stratification (each split should have similar class proportions)
        train_ratio_label = n_label_train / n_label_total
        val_ratio_label = n_label_val / n_label_total
        test_ratio_label = n_label_test / n_label_total

        # Allow 10% tolerance for class distribution
        assert abs(train_ratio_label - 0.7) < 0.1, f"Class {label} train ratio {train_ratio_label:.2f} far from 0.7"

    # Verify no data leakage (no sample IDs overlap)
    train_ids = set(splits["train"].sample_ids)
    val_ids = set(splits["val"].sample_ids)
    test_ids = set(splits["test"].sample_ids)

    assert len(train_ids & val_ids) == 0, "Data leakage: train and val overlap"
    assert len(train_ids & test_ids) == 0, "Data leakage: train and test overlap"
    assert len(val_ids & test_ids) == 0, "Data leakage: val and test overlap"


def test_temporal_split(temp_dir):
    """Test temporal split (chronological).

    Verifies:
    - Training data comes before validation data
    - Validation data comes before test data
    - No data leakage
    - Time ordering is preserved
    """
    # Create temporal data (features with timestamps)
    n_samples = 100
    features = np.random.randn(n_samples, 128).astype(np.float32)
    labels = np.random.randint(0, 3, size=n_samples, dtype=np.int64)

    # Create timestamps (monotonically increasing) - use actual timestamps
    from datetime import datetime, timedelta

    base_time = datetime(2025, 1, 1, 0, 0, 0)
    timestamps = np.array([(base_time + timedelta(hours=i)).timestamp() for i in range(n_samples)], dtype=np.float64)

    # Add timestamps to sample IDs
    sample_ids = [f"sample_{i:04d}_t{int(timestamps[i])}" for i in range(n_samples)]

    # Create dataset builder WITH timestamps
    builder = DatasetBuilder(
        features=features,
        labels=labels,
        sample_ids=sample_ids,
        output_dir=temp_dir,
        random_seed=42,
        timestamps=timestamps,  # Pass timestamps for temporal split
    )

    # Create temporal splits
    splits = builder.create_splits(strategy=SplitStrategy.TEMPORAL, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)

    # Extract timestamps from sample IDs
    def extract_timestamp(sample_id: str) -> int:
        return int(sample_id.split("_t")[1])

    train_timestamps = [extract_timestamp(sid) for sid in splits["train"].sample_ids]
    val_timestamps = [extract_timestamp(sid) for sid in splits["val"].sample_ids]
    test_timestamps = [extract_timestamp(sid) for sid in splits["test"].sample_ids]

    # Verify temporal ordering
    max_train_time = max(train_timestamps)
    min_val_time = min(val_timestamps)
    max_val_time = max(val_timestamps)
    min_test_time = min(test_timestamps)

    assert max_train_time < min_val_time, (
        f"Train data overlaps with val data: max_train={max_train_time}, min_val={min_val_time}"
    )
    assert max_val_time < min_test_time, (
        f"Val data overlaps with test data: max_val={max_val_time}, min_test={min_test_time}"
    )

    # Verify each split is internally sorted
    assert train_timestamps == sorted(train_timestamps), "Train split not chronologically sorted"
    assert val_timestamps == sorted(val_timestamps), "Val split not chronologically sorted"
    assert test_timestamps == sorted(test_timestamps), "Test split not chronologically sorted"


def test_pytorch_dataset_wrapper():
    """Test PyTorch Dataset wrapper.

    Verifies:
    - Dataset implements PyTorch interface
    - __len__ returns correct size
    - __getitem__ returns correct format
    - Batching works correctly
    """
    # Check if PyTorch is available
    try:
        import torch
        from torch.utils.data import DataLoader
    except ImportError:
        pytest.skip("PyTorch not available")

    # Create synthetic data
    n_samples = 50
    features = np.random.randn(n_samples, 128).astype(np.float32)
    labels = np.random.randint(0, 3, size=n_samples, dtype=np.int64)
    sample_ids = [f"sample_{i:04d}" for i in range(n_samples)]

    # Create DatasetSplit
    dataset_split = DatasetSplit(features=features, labels=labels, sample_ids=sample_ids)

    # Create PyTorch wrapper
    pytorch_dataset = PyTorchDatasetWrapper(dataset_split)

    # Verify __len__
    assert len(pytorch_dataset) == n_samples, f"Expected length {n_samples}, got {len(pytorch_dataset)}"

    # Verify __getitem__
    feature, label = pytorch_dataset[0]

    assert isinstance(feature, torch.Tensor), f"Expected torch.Tensor for feature, got {type(feature)}"
    assert isinstance(label, torch.Tensor), f"Expected torch.Tensor for label, got {type(label)}"

    assert feature.shape == (128,), f"Expected feature shape (128,), got {feature.shape}"
    assert label.shape == (), f"Expected label shape (), got {label.shape}"

    # Verify DataLoader compatibility
    dataloader = DataLoader(pytorch_dataset, batch_size=8, shuffle=True)

    # Get first batch
    batch_features, batch_labels = next(iter(dataloader))

    assert batch_features.shape == (8, 128), f"Expected batch shape (8, 128), got {batch_features.shape}"
    assert batch_labels.shape == (8,), f"Expected batch labels shape (8,), got {batch_labels.shape}"

    # Verify all batches
    n_batches = 0
    total_samples = 0

    for batch_features, batch_labels in dataloader:
        n_batches += 1
        total_samples += len(batch_features)

        # Verify batch dimensions
        assert batch_features.dim() == 2, "Batch features should be 2D"
        assert batch_features.shape[1] == 128, "Feature dimension should be 128"
        assert batch_labels.dim() == 1, "Batch labels should be 1D"

    # Verify all samples were seen
    assert total_samples == n_samples, f"Expected {n_samples} total samples, got {total_samples}"
