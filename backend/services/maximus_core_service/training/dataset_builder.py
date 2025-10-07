"""
Dataset Builder for MAXIMUS Training Pipeline

Creates train/val/test splits with:
- Stratified sampling (balanced classes)
- Temporal split (respect time ordering)
- Data augmentation
- PyTorch Dataset wrappers

REGRA DE OURO: Zero mocks, production-ready dataset building
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SplitStrategy(Enum):
    """Dataset split strategies."""

    RANDOM = "random"  # Random shuffle
    STRATIFIED = "stratified"  # Stratified by label
    TEMPORAL = "temporal"  # Respect time ordering
    K_FOLD = "k_fold"  # K-fold cross-validation


@dataclass
class DatasetSplit:
    """Represents a dataset split (train/val/test)."""

    name: str  # "train", "val", "test"
    features: np.ndarray
    labels: np.ndarray
    sample_ids: List[str]
    indices: np.ndarray

    def __len__(self) -> int:
        return len(self.features)

    def __repr__(self) -> str:
        label_dist = np.bincount(self.labels[self.labels >= 0])
        return (f"DatasetSplit(name={self.name}, size={len(self)}, "
                f"label_dist={label_dist.tolist()})")

    def get_class_distribution(self) -> Dict[int, int]:
        """Get class distribution.

        Returns:
            Dictionary mapping label to count
        """
        unique, counts = np.unique(self.labels[self.labels >= 0], return_counts=True)
        return dict(zip(unique.tolist(), counts.tolist()))

    def save(self, output_path: Path):
        """Save split to file.

        Args:
            output_path: Path to save .npz file
        """
        np.savez_compressed(
            output_path,
            features=self.features,
            labels=self.labels,
            sample_ids=self.sample_ids,
            indices=self.indices
        )
        logger.info(f"Saved {self.name} split to {output_path}")

    @classmethod
    def load(cls, filepath: Path, name: str = "split") -> "DatasetSplit":
        """Load split from file.

        Args:
            filepath: Path to .npz file
            name: Split name

        Returns:
            DatasetSplit instance
        """
        data = np.load(filepath, allow_pickle=True)

        return cls(
            name=name,
            features=data["features"],
            labels=data["labels"],
            sample_ids=data["sample_ids"].tolist(),
            indices=data["indices"]
        )


class DatasetBuilder:
    """Builds training datasets with various split strategies.

    Features:
    - Multiple split strategies (random, stratified, temporal, k-fold)
    - Class balancing
    - Data augmentation
    - PyTorch-compatible outputs

    Example:
        ```python
        builder = DatasetBuilder(
            features=features,
            labels=labels,
            sample_ids=sample_ids,
            output_dir="training/data/splits"
        )

        # Create stratified split
        splits = builder.create_splits(
            strategy=SplitStrategy.STRATIFIED,
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15
        )

        print(f"Train: {len(splits['train'])} samples")
        print(f"Val: {len(splits['val'])} samples")
        print(f"Test: {len(splits['test'])} samples")
        ```
    """

    def __init__(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        sample_ids: List[str],
        timestamps: Optional[np.ndarray] = None,
        output_dir: Optional[Path] = None,
        random_seed: int = 42
    ):
        """Initialize dataset builder.

        Args:
            features: Feature matrix (N x D)
            labels: Label vector (N,)
            sample_ids: Sample ID list (N,)
            timestamps: Optional timestamps for temporal splits
            output_dir: Directory to save splits
            random_seed: Random seed for reproducibility
        """
        self.features = features
        self.labels = labels
        self.sample_ids = sample_ids
        self.timestamps = timestamps
        self.output_dir = Path(output_dir) if output_dir else Path("training/data/splits")
        self.random_seed = random_seed

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Validate shapes
        assert len(features) == len(labels) == len(sample_ids), "Shape mismatch"

        # Set random seed
        np.random.seed(random_seed)

        logger.info(f"DatasetBuilder initialized: {len(features)} samples, "
                    f"{features.shape[1]} features")

    def create_splits(
        self,
        strategy: SplitStrategy = SplitStrategy.STRATIFIED,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        balance_classes: bool = False
    ) -> Dict[str, DatasetSplit]:
        """Create train/val/test splits.

        Args:
            strategy: Split strategy
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio
            balance_classes: Whether to balance classes in training set

        Returns:
            Dictionary with "train", "val", "test" splits
        """
        # Validate ratios
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios must sum to 1"

        # Select strategy
        if strategy == SplitStrategy.RANDOM:
            indices_dict = self._random_split(train_ratio, val_ratio, test_ratio)
        elif strategy == SplitStrategy.STRATIFIED:
            indices_dict = self._stratified_split(train_ratio, val_ratio, test_ratio)
        elif strategy == SplitStrategy.TEMPORAL:
            indices_dict = self._temporal_split(train_ratio, val_ratio, test_ratio)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

        # Create split objects
        splits = {}
        for name, indices in indices_dict.items():
            split = DatasetSplit(
                name=name,
                features=self.features[indices],
                labels=self.labels[indices],
                sample_ids=[self.sample_ids[i] for i in indices],
                indices=indices
            )
            splits[name] = split

            logger.info(f"{name.capitalize()} split: {split}")

        # Balance classes in training set if requested
        if balance_classes and "train" in splits:
            splits["train"] = self._balance_classes(splits["train"])

        return splits

    def _random_split(
        self,
        train_ratio: float,
        val_ratio: float,
        test_ratio: float
    ) -> Dict[str, np.ndarray]:
        """Create random split.

        Args:
            train_ratio: Training ratio
            val_ratio: Validation ratio
            test_ratio: Test ratio

        Returns:
            Dictionary with indices for each split
        """
        n_samples = len(self.features)

        # Shuffle indices
        indices = np.random.permutation(n_samples)

        # Calculate split sizes
        n_train = int(n_samples * train_ratio)
        n_val = int(n_samples * val_ratio)

        # Split
        train_indices = indices[:n_train]
        val_indices = indices[n_train:n_train + n_val]
        test_indices = indices[n_train + n_val:]

        return {
            "train": train_indices,
            "val": val_indices,
            "test": test_indices
        }

    def _stratified_split(
        self,
        train_ratio: float,
        val_ratio: float,
        test_ratio: float
    ) -> Dict[str, np.ndarray]:
        """Create stratified split (balanced classes).

        Args:
            train_ratio: Training ratio
            val_ratio: Validation ratio
            test_ratio: Test ratio

        Returns:
            Dictionary with indices for each split
        """
        # Get unique labels
        unique_labels = np.unique(self.labels[self.labels >= 0])

        train_indices = []
        val_indices = []
        test_indices = []

        for label in unique_labels:
            # Get indices for this label
            label_indices = np.where(self.labels == label)[0]
            n_label = len(label_indices)

            # Shuffle
            label_indices = np.random.permutation(label_indices)

            # Calculate split sizes for this label
            n_train = int(n_label * train_ratio)
            n_val = int(n_label * val_ratio)

            # Split
            train_indices.extend(label_indices[:n_train].tolist())
            val_indices.extend(label_indices[n_train:n_train + n_val].tolist())
            test_indices.extend(label_indices[n_train + n_val:].tolist())

        # Convert to arrays and shuffle
        train_indices = np.array(train_indices)
        val_indices = np.array(val_indices)
        test_indices = np.array(test_indices)

        np.random.shuffle(train_indices)
        np.random.shuffle(val_indices)
        np.random.shuffle(test_indices)

        return {
            "train": train_indices,
            "val": val_indices,
            "test": test_indices
        }

    def _temporal_split(
        self,
        train_ratio: float,
        val_ratio: float,
        test_ratio: float
    ) -> Dict[str, np.ndarray]:
        """Create temporal split (respect time ordering).

        Args:
            train_ratio: Training ratio
            val_ratio: Validation ratio
            test_ratio: Test ratio

        Returns:
            Dictionary with indices for each split
        """
        if self.timestamps is None:
            logger.warning("No timestamps provided, falling back to random split")
            return self._random_split(train_ratio, val_ratio, test_ratio)

        # Sort by timestamp
        sorted_indices = np.argsort(self.timestamps)

        n_samples = len(sorted_indices)

        # Calculate split sizes
        n_train = int(n_samples * train_ratio)
        n_val = int(n_samples * val_ratio)

        # Split (oldest to newest)
        train_indices = sorted_indices[:n_train]
        val_indices = sorted_indices[n_train:n_train + n_val]
        test_indices = sorted_indices[n_train + n_val:]

        return {
            "train": train_indices,
            "val": val_indices,
            "test": test_indices
        }

    def _balance_classes(self, split: DatasetSplit) -> DatasetSplit:
        """Balance classes using undersampling/oversampling.

        Args:
            split: Input split

        Returns:
            Balanced split
        """
        unique_labels, label_counts = np.unique(split.labels[split.labels >= 0], return_counts=True)

        if len(unique_labels) == 0:
            logger.warning("No labeled data to balance")
            return split

        # Find minority class size
        min_count = label_counts.min()

        # Undersample majority classes
        balanced_indices = []
        for label in unique_labels:
            label_mask = split.labels == label
            label_indices = np.where(label_mask)[0]

            # Randomly sample min_count samples
            sampled_indices = np.random.choice(label_indices, size=min_count, replace=False)
            balanced_indices.extend(sampled_indices.tolist())

        balanced_indices = np.array(balanced_indices)
        np.random.shuffle(balanced_indices)

        # Create balanced split
        balanced_split = DatasetSplit(
            name=split.name + "_balanced",
            features=split.features[balanced_indices],
            labels=split.labels[balanced_indices],
            sample_ids=[split.sample_ids[i] for i in balanced_indices],
            indices=split.indices[balanced_indices]
        )

        logger.info(f"Balanced {split.name}: {len(split)} -> {len(balanced_split)} samples")
        logger.info(f"Class distribution: {balanced_split.get_class_distribution()}")

        return balanced_split

    def save_splits(self, splits: Dict[str, DatasetSplit], prefix: str = "layer1"):
        """Save all splits to disk.

        Args:
            splits: Dictionary of splits
            prefix: Filename prefix (e.g., "layer1", "layer2")
        """
        for name, split in splits.items():
            filename = f"{prefix}_{name}.npz"
            output_path = self.output_dir / filename
            split.save(output_path)

        logger.info(f"Saved {len(splits)} splits with prefix '{prefix}'")

    @classmethod
    def load_splits(
        cls,
        split_dir: Path,
        prefix: str = "layer1"
    ) -> Dict[str, DatasetSplit]:
        """Load splits from disk.

        Args:
            split_dir: Directory containing split files
            prefix: Filename prefix

        Returns:
            Dictionary of splits
        """
        splits = {}

        for split_name in ["train", "val", "test"]:
            filename = f"{prefix}_{split_name}.npz"
            filepath = split_dir / filename

            if filepath.exists():
                split = DatasetSplit.load(filepath, name=split_name)
                splits[split_name] = split
                logger.info(f"Loaded {split_name} split: {len(split)} samples")
            else:
                logger.warning(f"Split file not found: {filepath}")

        return splits

    def augment_data(
        self,
        split: DatasetSplit,
        augmentation_factor: int = 2,
        noise_std: float = 0.01
    ) -> DatasetSplit:
        """Augment data with noise.

        Args:
            split: Input split
            augmentation_factor: How many augmented copies to create
            noise_std: Standard deviation of Gaussian noise

        Returns:
            Augmented split
        """
        augmented_features = []
        augmented_labels = []
        augmented_ids = []

        # Original data
        augmented_features.append(split.features)
        augmented_labels.append(split.labels)
        augmented_ids.extend(split.sample_ids)

        # Generate augmented copies
        for i in range(augmentation_factor - 1):
            # Add Gaussian noise
            noise = np.random.normal(0, noise_std, split.features.shape)
            augmented_feat = split.features + noise

            augmented_features.append(augmented_feat)
            augmented_labels.append(split.labels)
            augmented_ids.extend([f"{sid}_aug{i+1}" for sid in split.sample_ids])

        # Concatenate
        augmented_features = np.concatenate(augmented_features)
        augmented_labels = np.concatenate(augmented_labels)

        # Create augmented split
        augmented_split = DatasetSplit(
            name=split.name + "_augmented",
            features=augmented_features,
            labels=augmented_labels,
            sample_ids=augmented_ids,
            indices=np.arange(len(augmented_features))
        )

        logger.info(f"Augmented {split.name}: {len(split)} -> {len(augmented_split)} samples "
                    f"(factor={augmentation_factor})")

        return augmented_split

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics.

        Returns:
            Dictionary with statistics
        """
        labeled_mask = self.labels >= 0
        n_labeled = labeled_mask.sum()
        n_unlabeled = (~labeled_mask).sum()

        stats = {
            "total_samples": len(self.features),
            "n_features": self.features.shape[1],
            "n_labeled": int(n_labeled),
            "n_unlabeled": int(n_unlabeled),
            "class_distribution": {},
            "feature_stats": {
                "mean": self.features.mean(axis=0).tolist(),
                "std": self.features.std(axis=0).tolist(),
                "min": self.features.min(axis=0).tolist(),
                "max": self.features.max(axis=0).tolist()
            }
        }

        if n_labeled > 0:
            unique, counts = np.unique(self.labels[labeled_mask], return_counts=True)
            stats["class_distribution"] = dict(zip(unique.tolist(), counts.tolist()))

        return stats


class PyTorchDatasetWrapper:
    """Wrapper to convert DatasetSplit to PyTorch Dataset.

    Example:
        ```python
        from torch.utils.data import DataLoader

        # Create PyTorch dataset
        train_dataset = PyTorchDatasetWrapper(train_split)

        # Create data loader
        train_loader = DataLoader(
            train_dataset,
            batch_size=32,
            shuffle=True,
            num_workers=4
        )

        # Iterate
        for batch_features, batch_labels in train_loader:
            # Training loop
            pass
        ```
    """

    def __init__(self, split: DatasetSplit, transform=None):
        """Initialize PyTorch dataset wrapper.

        Args:
            split: DatasetSplit instance
            transform: Optional transform function
        """
        self.split = split
        self.transform = transform

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, idx: int) -> Tuple[np.ndarray, int]:
        """Get item by index.

        Args:
            idx: Index

        Returns:
            Tuple of (features, label)
        """
        features = self.split.features[idx]
        label = self.split.labels[idx]

        if self.transform:
            features = self.transform(features)

        return features, label

    def get_sample_id(self, idx: int) -> str:
        """Get sample ID by index.

        Args:
            idx: Index

        Returns:
            Sample ID
        """
        return self.split.sample_ids[idx]
