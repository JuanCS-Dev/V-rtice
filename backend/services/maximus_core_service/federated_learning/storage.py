"""
Storage and Persistence for Federated Learning

This module handles:
- Model versioning and registry
- Round history and metrics
- Model checkpointing
- Convergence tracking

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import json
import pickle
import tempfile
import numpy as np
import logging
from pathlib import Path

from .base import FLRound, FLMetrics, ModelType

logger = logging.getLogger(__name__)


class RestrictedUnpickler(pickle.Unpickler):
    """
    Restricted pickle unpickler that only allows safe classes.

    Prevents arbitrary code execution by whitelisting only specific
    classes needed for model weights (numpy arrays, basic Python types).

    Security: Protects against pickle deserialization attacks (CWE-502).
    """

    # Whitelist of allowed modules and classes
    ALLOWED_MODULES = {
        'numpy',
        'numpy.core.multiarray',
        'numpy.core.numeric',
        'numpy.core._multiarray_umath',
        'numpy._core.multiarray',  # Newer numpy versions use _core
        'numpy._core.numeric',
        'numpy._core._multiarray_umath',
        'builtins',
        'collections',
    }

    ALLOWED_CLASSES = {
        'numpy.ndarray',
        'numpy.dtype',
        'numpy.core.multiarray._reconstruct',
        'numpy._core.multiarray._reconstruct',  # Newer numpy versions
        'builtins.dict',
        'builtins.list',
        'builtins.tuple',
        'builtins.set',
        'builtins.frozenset',
        'builtins.int',
        'builtins.float',
        'builtins.str',
        'builtins.bytes',
        'builtins.bool',
        'builtins.NoneType',
        'collections.OrderedDict',
    }

    def find_class(self, module, name):
        """
        Override find_class to restrict to whitelist.

        Args:
            module: Module name
            name: Class name

        Returns:
            Class object if allowed

        Raises:
            pickle.UnpicklingError: If class not in whitelist
        """
        full_name = f"{module}.{name}"

        # Check if module or full class name is allowed
        if module in self.ALLOWED_MODULES or full_name in self.ALLOWED_CLASSES:
            return super().find_class(module, name)

        # Reject anything not whitelisted
        raise pickle.UnpicklingError(
            f"Forbidden class: {full_name}. "
            f"Only numpy arrays and basic Python types are allowed for security."
        )


def safe_pickle_load(file_obj):
    """
    Safely load pickle data using RestrictedUnpickler.

    Args:
        file_obj: File object opened in binary mode

    Returns:
        Unpickled object

    Raises:
        pickle.UnpicklingError: If forbidden class encountered
    """
    return RestrictedUnpickler(file_obj).load()


@dataclass
class ModelVersion:
    """
    Model version metadata.

    Attributes:
        version_id: Version identifier
        model_type: Type of model
        round_id: Round that produced this version
        timestamp: When version was created
        accuracy: Model accuracy on test set
        total_parameters: Total number of parameters
        file_path: Path to saved model file
        metadata: Additional metadata
    """
    version_id: int
    model_type: ModelType
    round_id: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    accuracy: float = 0.0
    total_parameters: int = 0
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "model_type": self.model_type.value,
            "round_id": self.round_id,
            "timestamp": self.timestamp.isoformat(),
            "accuracy": self.accuracy,
            "total_parameters": self.total_parameters,
            "file_path": self.file_path,
            "metadata": self.metadata,
        }


class FLModelRegistry:
    """
    Registry for storing and retrieving FL model versions.

    Maintains history of all global model versions produced during
    federated learning, enabling:
    - Model rollback
    - Performance tracking
    - Best model selection
    - Reproducibility
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize model registry.

        Args:
            storage_dir: Directory to store model files.
                        If None, uses FL_MODELS_DIR env var or creates secure temp dir.
        """
        if storage_dir is None:
            storage_dir = os.getenv(
                "FL_MODELS_DIR",
                tempfile.mkdtemp(prefix="fl_models_", suffix="_maximus")
            )
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        self.versions: Dict[int, ModelVersion] = {}
        self.best_version_id: Optional[int] = None
        self.best_accuracy: float = 0.0

        logger.info(f"FL Model Registry initialized: {storage_dir}")

    def save_global_model(
        self,
        version_id: int,
        model_type: ModelType,
        round_id: int,
        weights: Dict[str, np.ndarray],
        accuracy: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ModelVersion:
        """
        Save a global model version.

        Args:
            version_id: Version identifier
            model_type: Type of model
            round_id: Round that produced this version
            weights: Model weights
            accuracy: Model accuracy
            metadata: Additional metadata

        Returns:
            ModelVersion object
        """
        # Create file path
        file_name = f"model_v{version_id}_r{round_id}.pkl"
        file_path = self.storage_dir / file_name

        # Save weights to file
        with open(file_path, 'wb') as f:
            pickle.dump(weights, f)

        # Calculate total parameters
        total_parameters = sum(w.size for w in weights.values())

        # Create version metadata
        version = ModelVersion(
            version_id=version_id,
            model_type=model_type,
            round_id=round_id,
            accuracy=accuracy,
            total_parameters=total_parameters,
            file_path=str(file_path),
            metadata=metadata or {},
        )

        # Store version
        self.versions[version_id] = version

        # Update best model if this is better
        if accuracy > self.best_accuracy:
            self.best_accuracy = accuracy
            self.best_version_id = version_id
            logger.info(
                f"New best model: v{version_id} (accuracy={accuracy:.4f})"
            )

        logger.info(
            f"Saved model v{version_id} from round {round_id} "
            f"({total_parameters:,} parameters, {accuracy:.4f} accuracy)"
        )

        return version

    def load_global_model(
        self, version_id: int
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Load a global model version.

        Args:
            version_id: Version identifier

        Returns:
            Model weights (None if not found)
        """
        if version_id not in self.versions:
            logger.warning(f"Version {version_id} not found")
            return None

        version = self.versions[version_id]

        if not version.file_path or not os.path.exists(version.file_path):
            logger.error(f"Model file not found: {version.file_path}")
            return None

        # Load weights securely using RestrictedUnpickler
        try:
            with open(version.file_path, 'rb') as f:
                weights = safe_pickle_load(f)
            logger.info(f"Loaded model v{version_id} from {version.file_path}")
            return weights
        except pickle.UnpicklingError as e:
            logger.error(f"Security error loading model v{version_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading model v{version_id}: {e}")
            return None

    def get_best_model(self) -> Optional[Dict[str, np.ndarray]]:
        """
        Get the best model version (highest accuracy).

        Returns:
            Best model weights (None if no models saved)
        """
        if self.best_version_id is None:
            return None

        return self.load_global_model(self.best_version_id)

    def get_latest_model(self) -> Optional[Dict[str, np.ndarray]]:
        """
        Get the latest model version.

        Returns:
            Latest model weights (None if no models saved)
        """
        if not self.versions:
            return None

        latest_version_id = max(self.versions.keys())
        return self.load_global_model(latest_version_id)

    def list_versions(
        self, limit: Optional[int] = None
    ) -> List[ModelVersion]:
        """
        List all model versions.

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of ModelVersion objects (sorted by version_id descending)
        """
        versions = sorted(
            self.versions.values(),
            key=lambda v: v.version_id,
            reverse=True,
        )

        if limit:
            versions = versions[:limit]

        return versions

    def get_version_info(self, version_id: int) -> Optional[ModelVersion]:
        """
        Get information about a specific version.

        Args:
            version_id: Version identifier

        Returns:
            ModelVersion object (None if not found)
        """
        return self.versions.get(version_id)

    def delete_version(self, version_id: int) -> bool:
        """
        Delete a model version.

        Args:
            version_id: Version identifier

        Returns:
            True if deletion successful
        """
        if version_id not in self.versions:
            logger.warning(f"Version {version_id} not found")
            return False

        version = self.versions[version_id]

        # Delete file
        if version.file_path and os.path.exists(version.file_path):
            os.remove(version.file_path)
            logger.info(f"Deleted model file: {version.file_path}")

        # Remove from registry
        del self.versions[version_id]

        logger.info(f"Deleted model version {version_id}")

        return True


class FLRoundHistory:
    """
    History of federated learning rounds.

    Tracks all training rounds for analysis, debugging, and
    convergence monitoring.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize round history.

        Args:
            storage_dir: Directory to store round data.
                        If None, uses FL_ROUNDS_DIR env var or creates secure temp dir.
        """
        if storage_dir is None:
            storage_dir = os.getenv(
                "FL_ROUNDS_DIR",
                tempfile.mkdtemp(prefix="fl_rounds_", suffix="_maximus")
            )
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        self.rounds: List[FLRound] = []

        logger.info(f"FL Round History initialized: {storage_dir}")

    def save_round(self, round_obj: FLRound) -> bool:
        """
        Save a completed round.

        Args:
            round_obj: FLRound object

        Returns:
            True if save successful
        """
        # Add to history
        self.rounds.append(round_obj)

        # Save to file
        file_name = f"round_{round_obj.round_id:04d}.json"
        file_path = self.storage_dir / file_name

        with open(file_path, 'w') as f:
            json.dump(round_obj.to_dict(), f, indent=2)

        duration = round_obj.get_duration_seconds()
        duration_str = f"{duration:.1f}s" if duration is not None else "in progress"
        logger.info(
            f"Saved round {round_obj.round_id} to {file_path} "
            f"(duration={duration_str})"
        )

        return True

    def get_round(self, round_id: int) -> Optional[FLRound]:
        """
        Get a specific round.

        Args:
            round_id: Round identifier

        Returns:
            FLRound object (None if not found)
        """
        for round_obj in self.rounds:
            if round_obj.round_id == round_id:
                return round_obj

        return None

    def get_round_stats(self) -> Dict[str, Any]:
        """
        Get statistics across all rounds.

        Returns:
            Dictionary of statistics
        """
        if not self.rounds:
            return {
                "total_rounds": 0,
                "total_updates": 0,
                "total_samples": 0,
            }

        total_updates = sum(len(r.received_updates) for r in self.rounds)
        total_samples = sum(r.get_total_samples() for r in self.rounds)

        durations = [
            r.get_duration_seconds() for r in self.rounds
            if r.get_duration_seconds() is not None
        ]

        participation_rates = [
            r.get_participation_rate() for r in self.rounds
        ]

        avg_metrics = {}
        if self.rounds[-1].metrics:
            metric_names = self.rounds[-1].metrics.keys()
            for metric_name in metric_names:
                values = [
                    r.metrics.get(metric_name, 0.0) for r in self.rounds
                    if r.metrics
                ]
                if values:
                    avg_metrics[metric_name] = np.mean(values)

        return {
            "total_rounds": len(self.rounds),
            "total_updates": total_updates,
            "total_samples": total_samples,
            "average_duration_seconds": np.mean(durations) if durations else 0.0,
            "average_participation_rate": np.mean(participation_rates) if participation_rates else 0.0,
            "average_metrics": avg_metrics,
        }

    def get_convergence_data(self) -> Dict[str, List[float]]:
        """
        Get convergence data for plotting.

        Returns:
            Dictionary mapping metric names to lists of values
        """
        convergence_data = {
            "round_id": [],
            "duration": [],
            "participation_rate": [],
        }

        # Collect metric names from first round
        if self.rounds and self.rounds[0].metrics:
            for metric_name in self.rounds[0].metrics.keys():
                convergence_data[metric_name] = []

        # Collect data from all rounds
        for round_obj in self.rounds:
            convergence_data["round_id"].append(round_obj.round_id)

            duration = round_obj.get_duration_seconds()
            convergence_data["duration"].append(duration if duration else 0.0)

            convergence_data["participation_rate"].append(
                round_obj.get_participation_rate()
            )

            if round_obj.metrics:
                for metric_name, value in round_obj.metrics.items():
                    if metric_name in convergence_data:
                        convergence_data[metric_name].append(value)

        return convergence_data

    def plot_convergence(
        self, metric_name: str = "loss", save_path: Optional[str] = None
    ) -> str:
        """
        Plot convergence curve for a specific metric.

        Args:
            metric_name: Name of metric to plot
            save_path: Path to save plot (if None, returns ASCII art)

        Returns:
            Plot description or path
        """
        convergence_data = self.get_convergence_data()

        if metric_name not in convergence_data:
            return f"Metric '{metric_name}' not found in round history"

        values = convergence_data[metric_name]
        round_ids = convergence_data["round_id"]

        # Simple ASCII plot
        plot_lines = [
            f"\nConvergence Plot: {metric_name}",
            "=" * 50,
        ]

        max_val = max(values) if values else 1.0
        min_val = min(values) if values else 0.0
        range_val = max_val - min_val if max_val > min_val else 1.0

        for r_id, value in zip(round_ids, values):
            normalized = (value - min_val) / range_val
            bar_length = int(normalized * 40)
            bar = "#" * bar_length
            plot_lines.append(f"Round {r_id:2d}: {value:6.3f} |{bar}")

        plot_lines.append("=" * 50)
        plot_lines.append(f"Min: {min_val:.3f}, Max: {max_val:.3f}")

        plot_str = "\n".join(plot_lines)

        if save_path:
            with open(save_path, 'w') as f:
                f.write(plot_str)
            return f"Plot saved to {save_path}"
        else:
            return plot_str
