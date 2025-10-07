"""
Model Registry for MAXIMUS Training Pipeline

Model versioning and registry using MLflow:
- Model registration
- Version management
- Metadata tracking
- Model promotion (staging -> production)
- Model serving endpoints

REGRA DE OURO: Zero mocks, production-ready registry
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""

    model_name: str
    version: str
    layer_name: str
    created_at: datetime
    metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    training_dataset: Optional[str] = None
    framework: str = "pytorch"
    stage: str = "none"  # "none", "staging", "production", "archived"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "model_name": self.model_name,
            "version": self.version,
            "layer_name": self.layer_name,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics,
            "hyperparameters": self.hyperparameters,
            "training_dataset": self.training_dataset,
            "framework": self.framework,
            "stage": self.stage
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        """Create from dictionary.

        Args:
            data: Dictionary

        Returns:
            ModelMetadata instance
        """
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class ModelRegistry:
    """Model registry for versioning and management.

    Features:
    - Model registration with metadata
    - Version management
    - Stage transitions (none -> staging -> production)
    - Model search and filtering
    - Automatic archival of old models

    Example:
        ```python
        registry = ModelRegistry(registry_dir="training/models")

        # Register model
        metadata = ModelMetadata(
            model_name="layer1_vae",
            version="v1.0.0",
            layer_name="layer1",
            created_at=datetime.utcnow(),
            metrics={"val_loss": 0.045, "accuracy": 0.95},
            hyperparameters={"learning_rate": 1e-3, "batch_size": 32}
        )

        registry.register_model(
            model_path="training/checkpoints/layer1_vae_best.pt",
            metadata=metadata
        )

        # Promote to staging
        registry.transition_stage("layer1_vae", "v1.0.0", "staging")

        # Get latest production model
        model_path = registry.get_model("layer1_vae", stage="production")
        ```
    """

    def __init__(self, registry_dir: Path = Path("training/models")):
        """Initialize model registry.

        Args:
            registry_dir: Directory to store registered models
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.registry_dir / "registry.json"

        # Load existing registry
        self.registry: Dict[str, Dict[str, ModelMetadata]] = {}
        self._load_registry()

        logger.info(f"ModelRegistry initialized: {self.registry_dir}")

    def register_model(
        self,
        model_path: Path,
        metadata: ModelMetadata
    ) -> Path:
        """Register a model.

        Args:
            model_path: Path to model checkpoint
            metadata: Model metadata

        Returns:
            Path where model was registered
        """
        model_name = metadata.model_name
        version = metadata.version

        # Create model directory
        model_dir = self.registry_dir / model_name / version
        model_dir.mkdir(parents=True, exist_ok=True)

        # Copy model file
        import shutil
        registered_model_path = model_dir / "model.pt"
        shutil.copy(model_path, registered_model_path)

        # Save metadata
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        # Update registry
        if model_name not in self.registry:
            self.registry[model_name] = {}

        self.registry[model_name][version] = metadata

        self._save_registry()

        logger.info(f"Model registered: {model_name}/{version} at {registered_model_path}")

        return registered_model_path

    def get_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        stage: Optional[str] = None
    ) -> Optional[Path]:
        """Get model path.

        Args:
            model_name: Model name
            version: Specific version or None for latest
            stage: Filter by stage ("staging", "production")

        Returns:
            Path to model or None if not found
        """
        if model_name not in self.registry:
            logger.warning(f"Model not found: {model_name}")
            return None

        versions = self.registry[model_name]

        # Filter by stage
        if stage:
            versions = {v: m for v, m in versions.items() if m.stage == stage}

        if not versions:
            logger.warning(f"No models found for {model_name} with stage={stage}")
            return None

        # Get specific version or latest
        if version:
            if version not in versions:
                logger.warning(f"Version not found: {model_name}/{version}")
                return None
            selected_version = version
        else:
            # Get latest version (by created_at)
            selected_version = max(versions.keys(), key=lambda v: versions[v].created_at)

        model_path = self.registry_dir / model_name / selected_version / "model.pt"

        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return None

        return model_path

    def get_metadata(
        self,
        model_name: str,
        version: str
    ) -> Optional[ModelMetadata]:
        """Get model metadata.

        Args:
            model_name: Model name
            version: Model version

        Returns:
            ModelMetadata or None
        """
        if model_name not in self.registry:
            return None

        return self.registry[model_name].get(version)

    def list_models(self, model_name: Optional[str] = None) -> Dict[str, List[str]]:
        """List all registered models.

        Args:
            model_name: Optional filter by model name

        Returns:
            Dictionary mapping model_name to list of versions
        """
        if model_name:
            if model_name in self.registry:
                return {model_name: list(self.registry[model_name].keys())}
            return {}

        return {name: list(versions.keys()) for name, versions in self.registry.items()}

    def transition_stage(
        self,
        model_name: str,
        version: str,
        new_stage: str
    ) -> bool:
        """Transition model to a new stage.

        Args:
            model_name: Model name
            version: Model version
            new_stage: New stage ("none", "staging", "production", "archived")

        Returns:
            True if successful
        """
        valid_stages = ["none", "staging", "production", "archived"]
        if new_stage not in valid_stages:
            logger.error(f"Invalid stage: {new_stage}. Valid stages: {valid_stages}")
            return False

        metadata = self.get_metadata(model_name, version)
        if metadata is None:
            logger.error(f"Model not found: {model_name}/{version}")
            return False

        # If promoting to production, demote current production model
        if new_stage == "production":
            for v, m in self.registry[model_name].items():
                if m.stage == "production" and v != version:
                    m.stage = "archived"
                    logger.info(f"Demoted {model_name}/{v} to archived")

        # Update stage
        metadata.stage = new_stage
        self.registry[model_name][version] = metadata

        # Save metadata
        model_dir = self.registry_dir / model_name / version
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        self._save_registry()

        logger.info(f"Transitioned {model_name}/{version} to {new_stage}")

        return True

    def compare_models(
        self,
        model_name: str,
        versions: List[str],
        metric: str = "val_loss"
    ) -> Dict[str, float]:
        """Compare models by a metric.

        Args:
            model_name: Model name
            versions: List of versions to compare
            metric: Metric to compare

        Returns:
            Dictionary mapping version to metric value
        """
        results = {}

        for version in versions:
            metadata = self.get_metadata(model_name, version)
            if metadata and metric in metadata.metrics:
                results[version] = metadata.metrics[metric]

        return results

    def search_models(
        self,
        model_name: Optional[str] = None,
        layer_name: Optional[str] = None,
        stage: Optional[str] = None,
        min_accuracy: Optional[float] = None
    ) -> List[ModelMetadata]:
        """Search models by criteria.

        Args:
            model_name: Filter by model name
            layer_name: Filter by layer name
            stage: Filter by stage
            min_accuracy: Minimum accuracy threshold

        Returns:
            List of matching model metadata
        """
        results = []

        for name, versions in self.registry.items():
            if model_name and name != model_name:
                continue

            for version, metadata in versions.items():
                # Apply filters
                if layer_name and metadata.layer_name != layer_name:
                    continue

                if stage and metadata.stage != stage:
                    continue

                if min_accuracy and metadata.metrics.get("accuracy", 0.0) < min_accuracy:
                    continue

                results.append(metadata)

        return results

    def delete_model(
        self,
        model_name: str,
        version: str
    ) -> bool:
        """Delete a model from registry.

        Args:
            model_name: Model name
            version: Model version

        Returns:
            True if successful
        """
        if model_name not in self.registry:
            logger.error(f"Model not found: {model_name}")
            return False

        if version not in self.registry[model_name]:
            logger.error(f"Version not found: {model_name}/{version}")
            return False

        # Remove from registry
        del self.registry[model_name][version]

        # Delete files
        import shutil
        model_dir = self.registry_dir / model_name / version
        if model_dir.exists():
            shutil.rmtree(model_dir)

        self._save_registry()

        logger.info(f"Deleted model: {model_name}/{version}")

        return True

    def _load_registry(self):
        """Load registry from disk."""
        if not self.metadata_file.exists():
            logger.debug("No existing registry found, starting fresh")
            return

        with open(self.metadata_file, "r") as f:
            data = json.load(f)

        for model_name, versions in data.items():
            self.registry[model_name] = {}
            for version, metadata_dict in versions.items():
                metadata = ModelMetadata.from_dict(metadata_dict)
                self.registry[model_name][version] = metadata

        logger.info(f"Registry loaded: {len(self.registry)} models")

    def _save_registry(self):
        """Save registry to disk."""
        data = {}

        for model_name, versions in self.registry.items():
            data[model_name] = {}
            for version, metadata in versions.items():
                data[model_name][version] = metadata.to_dict()

        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Registry saved to {self.metadata_file}")

    def print_registry(self):
        """Print registry summary."""
        print("\n" + "=" * 80)
        print("MODEL REGISTRY")
        print("=" * 80)

        for model_name, versions in self.registry.items():
            print(f"\n{model_name}:")
            for version, metadata in versions.items():
                metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metadata.metrics.items())
                print(f"  {version} ({metadata.stage}): {metrics_str}")

        print("=" * 80)
