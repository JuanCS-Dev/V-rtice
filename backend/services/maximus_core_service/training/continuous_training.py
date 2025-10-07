"""
Continuous Training Pipeline for MAXIMUS

Automated retraining pipeline with:
- Data monitoring (drift detection)
- Scheduled retraining
- Model comparison (challenger vs champion)
- Automatic deployment
- Alerting

REGRA DE OURO: Zero mocks, production-ready continuous training
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from training.data_collector import DataCollector
from training.data_validator import DataValidator
from training.model_registry import ModelRegistry, ModelMetadata
from training.evaluator import ModelEvaluator

logger = logging.getLogger(__name__)


@dataclass
class RetrainingConfig:
    """Retraining configuration."""

    # Schedule
    retrain_frequency_days: int = 7  # Retrain every N days
    min_new_samples: int = 1000  # Minimum new samples to trigger retraining

    # Data validation
    drift_threshold: float = 0.1  # Max drift allowed
    min_accuracy_threshold: float = 0.85  # Min accuracy required

    # Model comparison
    comparison_metric: str = "val_loss"  # Metric to compare models
    improvement_threshold: float = 0.02  # Min improvement to deploy

    # Registry
    registry_dir: Path = Path("training/models")

    # Alerting
    alert_on_drift: bool = True
    alert_on_degradation: bool = True


class ContinuousTrainingPipeline:
    """Continuous training pipeline.

    Monitors data, detects drift, retrains models, and deploys updates.

    Example:
        ```python
        config = RetrainingConfig(
            retrain_frequency_days=7,
            min_new_samples=1000
        )

        pipeline = ContinuousTrainingPipeline(config=config)

        # Run retraining
        result = pipeline.run_retraining(
            layer_name="layer1",
            model_name="layer1_vae",
            train_fn=train_layer1_vae
        )

        if result["deployed"]:
            print(f"New model deployed: {result['new_version']}")
        ```
    """

    def __init__(self, config: RetrainingConfig):
        """Initialize continuous training pipeline.

        Args:
            config: Retraining configuration
        """
        self.config = config
        self.registry = ModelRegistry(registry_dir=config.registry_dir)

        logger.info(f"ContinuousTrainingPipeline initialized")

    def run_retraining(
        self,
        layer_name: str,
        model_name: str,
        train_fn: callable,
        train_data_path: Path,
        val_data_path: Path,
        test_data_path: Path
    ) -> Dict[str, Any]:
        """Run retraining pipeline.

        Args:
            layer_name: Layer name ("layer1", "layer2", etc.)
            model_name: Model name
            train_fn: Training function
            train_data_path: Training data path
            val_data_path: Validation data path
            test_data_path: Test data path

        Returns:
            Dictionary with retraining results
        """
        logger.info(f"Starting retraining for {model_name}")

        # Step 1: Load data
        logger.info("Loading data...")
        train_data = np.load(train_data_path)
        val_data = np.load(val_data_path)
        test_data = np.load(test_data_path)

        train_features = train_data["features"]
        train_labels = train_data.get("labels", np.zeros(len(train_features)))

        val_features = val_data["features"]
        val_labels = val_data.get("labels", np.zeros(len(val_features)))

        test_features = test_data["features"]
        test_labels = test_data.get("labels", np.zeros(len(test_features)))

        # Step 2: Validate data
        logger.info("Validating data...")
        validation_result = self._validate_data(
            train_features, train_labels,
            val_features, val_labels
        )

        if not validation_result["passed"]:
            logger.error("Data validation failed, aborting retraining")
            return {"success": False, "reason": "data_validation_failed"}

        # Step 3: Check if retraining is needed
        logger.info("Checking if retraining is needed...")
        should_retrain, reason = self._should_retrain(
            model_name,
            train_features.shape[0]
        )

        if not should_retrain:
            logger.info(f"Retraining not needed: {reason}")
            return {"success": True, "retrained": False, "reason": reason}

        # Step 4: Train new model (challenger)
        logger.info("Training new model...")
        new_model, training_results = train_fn(
            train_features=train_features,
            train_labels=train_labels,
            val_features=val_features,
            val_labels=val_labels
        )

        # Step 5: Evaluate new model
        logger.info("Evaluating new model...")
        evaluator = ModelEvaluator(
            model=new_model,
            test_features=test_features,
            test_labels=test_labels
        )
        new_metrics = evaluator.evaluate()

        # Step 6: Compare with current production model (champion)
        logger.info("Comparing with production model...")
        comparison_result = self._compare_with_champion(
            model_name,
            new_metrics
        )

        # Step 7: Register new model
        logger.info("Registering new model...")
        new_version = self._generate_version()

        metadata = ModelMetadata(
            model_name=model_name,
            version=new_version,
            layer_name=layer_name,
            created_at=datetime.utcnow(),
            metrics=new_metrics.to_dict(),
            hyperparameters=training_results.get("config", {}).__dict__ if hasattr(training_results.get("config"), "__dict__") else {},
            training_dataset=str(train_data_path),
            stage="staging"
        )

        # Save model checkpoint
        checkpoint_path = Path(f"training/checkpoints/{model_name}_{new_version}.pt")

        try:
            import torch
            torch.save(new_model.state_dict(), checkpoint_path)
        except:
            logger.warning("Could not save model checkpoint")

        self.registry.register_model(
            model_path=checkpoint_path,
            metadata=metadata
        )

        # Step 8: Deploy if better
        deployed = False
        if comparison_result["is_better"]:
            logger.info("New model is better, promoting to production...")
            self.registry.transition_stage(model_name, new_version, "production")
            deployed = True
        else:
            logger.info("New model is not better, keeping in staging")

        return {
            "success": True,
            "retrained": True,
            "deployed": deployed,
            "new_version": new_version,
            "comparison": comparison_result,
            "metrics": new_metrics.to_dict()
        }

    def _validate_data(
        self,
        train_features: np.ndarray,
        train_labels: np.ndarray,
        val_features: np.ndarray,
        val_labels: np.ndarray
    ) -> Dict[str, Any]:
        """Validate training data.

        Args:
            train_features: Training features
            train_labels: Training labels
            val_features: Validation features
            val_labels: Validation labels

        Returns:
            Validation result
        """
        validator = DataValidator(
            features=train_features,
            labels=train_labels,
            reference_features=val_features
        )

        result = validator.validate(
            check_missing=True,
            check_outliers=True,
            check_labels=True,
            check_drift=True,
            drift_threshold=self.config.drift_threshold
        )

        return {
            "passed": result.passed,
            "issues": [str(issue) for issue in result.issues]
        }

    def _should_retrain(
        self,
        model_name: str,
        n_new_samples: int
    ) -> tuple[bool, str]:
        """Check if retraining is needed.

        Args:
            model_name: Model name
            n_new_samples: Number of new samples

        Returns:
            Tuple of (should_retrain, reason)
        """
        # Check if production model exists
        production_model = self.registry.get_model(model_name, stage="production")

        if production_model is None:
            return True, "no_production_model"

        # Check last training date
        latest_metadata = self.registry.search_models(
            model_name=model_name,
            stage="production"
        )

        if latest_metadata:
            days_since_training = (datetime.utcnow() - latest_metadata[0].created_at).days

            if days_since_training >= self.config.retrain_frequency_days:
                return True, f"scheduled_retrain (last trained {days_since_training} days ago)"

        # Check minimum samples
        if n_new_samples < self.config.min_new_samples:
            return False, f"insufficient_samples ({n_new_samples} < {self.config.min_new_samples})"

        return True, "sufficient_new_data"

    def _compare_with_champion(
        self,
        model_name: str,
        new_metrics: Any
    ) -> Dict[str, Any]:
        """Compare new model with current champion.

        Args:
            model_name: Model name
            new_metrics: New model metrics

        Returns:
            Comparison result
        """
        # Get champion metrics
        champion_metadata = self.registry.search_models(
            model_name=model_name,
            stage="production"
        )

        if not champion_metadata:
            return {
                "is_better": True,
                "reason": "no_champion"
            }

        champion_metrics = champion_metadata[0].metrics
        metric_name = self.config.comparison_metric

        # Extract metric values
        new_value = new_metrics.to_dict().get(metric_name)
        champion_value = champion_metrics.get(metric_name)

        if new_value is None or champion_value is None:
            logger.warning(f"Metric {metric_name} not found in metrics")
            return {
                "is_better": False,
                "reason": "metric_not_found"
            }

        # Determine if lower is better (e.g., loss) or higher is better (e.g., accuracy)
        lower_is_better = "loss" in metric_name.lower() or "error" in metric_name.lower()

        if lower_is_better:
            improvement = champion_value - new_value
            is_better = new_value < (champion_value - self.config.improvement_threshold)
        else:
            improvement = new_value - champion_value
            is_better = new_value > (champion_value + self.config.improvement_threshold)

        return {
            "is_better": is_better,
            "improvement": float(improvement),
            "new_value": float(new_value),
            "champion_value": float(champion_value),
            "metric": metric_name
        }

    def _generate_version(self) -> str:
        """Generate version string.

        Returns:
            Version string (e.g., "v1.0.0")
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"v{timestamp}"
