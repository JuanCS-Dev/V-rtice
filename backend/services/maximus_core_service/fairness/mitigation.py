"""Bias Mitigation Engine for Cybersecurity AI Models.

This module implements bias mitigation strategies to reduce unfair treatment
across protected groups while maintaining model performance.

Mitigation Strategies:
    - Pre-processing: Reweighing training data
    - In-processing: Regularization-based debiasing
    - Post-processing: Threshold optimization
    - Calibration adjustment
"""

import logging
from collections.abc import Callable
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from .base import FairnessException, FairnessMetric, MitigationResult, ProtectedAttribute
from .constraints import FairnessConstraints

logger = logging.getLogger(__name__)


class MitigationEngine:
    """Bias mitigation engine for cybersecurity AI models.

    Implements multiple mitigation strategies to reduce bias while
    maintaining acceptable model performance.

    Attributes:
        fairness_constraints: FairnessConstraints instance for evaluation
        performance_threshold: Minimum acceptable performance after mitigation
        fairness_improvement_threshold: Minimum fairness improvement required
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize MitigationEngine.

        Args:
            config: Configuration dictionary
        """
        config = config or {}

        # Initialize fairness constraints evaluator
        self.fairness_constraints = FairnessConstraints(config.get("fairness_config", {}))

        # Performance constraints
        self.performance_threshold = config.get("performance_threshold", 0.75)  # Min 75% accuracy
        self.max_performance_loss = config.get("max_performance_loss", 0.05)  # Max 5% loss

        # Fairness improvement threshold
        self.fairness_improvement_threshold = config.get("fairness_improvement_threshold", 0.05)

        # Mitigation strategies to try (in order)
        self.mitigation_strategies = config.get(
            "mitigation_strategies", ["threshold_optimization", "reweighing", "calibration_adjustment"]
        )

        logger.info(
            f"MitigationEngine initialized with {len(self.mitigation_strategies)} strategies, "
            f"performance_threshold={self.performance_threshold}"
        )

    def mitigate_reweighing(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
        model: Any | None = None,
    ) -> MitigationResult:
        """Mitigate bias using reweighing strategy (pre-processing).

        Assigns weights to training samples to balance representation across
        protected groups and outcome classes.

        Args:
            X_train: Training features
            y_train: Training labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            model: Model to retrain (optional)

        Returns:
            MitigationResult with mitigation outcome
        """
        logger.info("Starting reweighing mitigation...")

        # Calculate sample weights
        weights = self._calculate_reweighing_weights(y_train, protected_attribute, protected_value)

        # Evaluate fairness before mitigation
        if model is not None:
            predictions_before = self._get_predictions(model, X_train)
            fairness_before = self._evaluate_fairness(predictions_before, y_train, protected_attribute, protected_value)
            performance_before = self._evaluate_performance(predictions_before, y_train)
        else:
            fairness_before = {}
            performance_before = {}

        # Retrain model with weights (if model provided)
        if model is not None:
            model_after = self._retrain_with_weights(model, X_train, y_train, weights)
            predictions_after = self._get_predictions(model_after, X_train)
            fairness_after = self._evaluate_fairness(predictions_after, y_train, protected_attribute, protected_value)
            performance_after = self._evaluate_performance(predictions_after, y_train)
        else:
            fairness_after = fairness_before
            performance_after = performance_before

        # Calculate performance impact
        performance_impact = {
            key: performance_after.get(key, 0) - performance_before.get(key, 0) for key in performance_before.keys()
        }

        # Check success criteria
        fairness_improved = self._check_fairness_improvement(fairness_before, fairness_after)
        performance_acceptable = self._check_performance_acceptable(performance_before, performance_after)

        success = fairness_improved and performance_acceptable

        result = MitigationResult(
            mitigation_method="reweighing",
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            fairness_before=fairness_before,
            fairness_after=fairness_after,
            performance_impact=performance_impact,
            success=success,
            metadata={
                "weights_min": float(np.min(weights)),
                "weights_max": float(np.max(weights)),
                "weights_mean": float(np.mean(weights)),
                "weights_std": float(np.std(weights)),
                "performance_before": performance_before,
                "performance_after": performance_after,
            },
        )

        logger.info(
            f"Reweighing complete: success={success}, "
            f"fairness_improved={fairness_improved}, "
            f"performance_acceptable={performance_acceptable}"
        )

        return result

    def mitigate_threshold_optimization(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
        metric: FairnessMetric = FairnessMetric.EQUALIZED_ODDS,
    ) -> MitigationResult:
        """Mitigate bias using threshold optimization (post-processing).

        Finds optimal classification thresholds for each group to satisfy
        fairness constraints while maintaining performance.

        Args:
            predictions: Model prediction scores (probabilities)
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            metric: Target fairness metric

        Returns:
            MitigationResult with mitigation outcome
        """
        logger.info(f"Starting threshold optimization for {metric.value}...")

        # Evaluate fairness before (using 0.5 threshold)
        binary_preds_before = (predictions > 0.5).astype(int)
        fairness_before = self._evaluate_fairness(
            binary_preds_before, true_labels, protected_attribute, protected_value
        )
        performance_before = self._evaluate_performance(binary_preds_before, true_labels)

        # Find optimal thresholds
        threshold_0, threshold_1 = self._find_optimal_thresholds(
            predictions, true_labels, protected_attribute, protected_value, metric
        )

        # Apply optimized thresholds
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        binary_preds_after = np.zeros_like(predictions, dtype=int)
        binary_preds_after[group_0_mask] = (predictions[group_0_mask] > threshold_0).astype(int)
        binary_preds_after[group_1_mask] = (predictions[group_1_mask] > threshold_1).astype(int)

        # Evaluate fairness after
        fairness_after = self._evaluate_fairness(binary_preds_after, true_labels, protected_attribute, protected_value)
        performance_after = self._evaluate_performance(binary_preds_after, true_labels)

        # Calculate performance impact
        performance_impact = {
            key: performance_after.get(key, 0) - performance_before.get(key, 0) for key in performance_before.keys()
        }

        # Check success
        fairness_improved = self._check_fairness_improvement(fairness_before, fairness_after)
        performance_acceptable = self._check_performance_acceptable(performance_before, performance_after)

        success = fairness_improved and performance_acceptable

        result = MitigationResult(
            mitigation_method="threshold_optimization",
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            fairness_before=fairness_before,
            fairness_after=fairness_after,
            performance_impact=performance_impact,
            success=success,
            metadata={
                "threshold_group_0": float(threshold_0),
                "threshold_group_1": float(threshold_1),
                "target_metric": metric.value,
                "performance_before": performance_before,
                "performance_after": performance_after,
            },
        )

        logger.info(
            f"Threshold optimization complete: success={success}, thresholds=({threshold_0:.3f}, {threshold_1:.3f})"
        )

        return result

    def mitigate_calibration_adjustment(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> MitigationResult:
        """Mitigate bias using calibration adjustment (post-processing).

        Adjusts prediction scores to ensure equal calibration across groups.

        Args:
            predictions: Model prediction scores
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            MitigationResult with mitigation outcome
        """
        logger.info("Starting calibration adjustment mitigation...")

        # Evaluate before
        binary_preds_before = (predictions > 0.5).astype(int)
        fairness_before = self._evaluate_fairness(
            binary_preds_before, true_labels, protected_attribute, protected_value
        )
        performance_before = self._evaluate_performance(binary_preds_before, true_labels)

        # Calculate calibration curves for each group
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        # Fit calibration models
        calibrator_0 = self._fit_calibrator(predictions[group_0_mask], true_labels[group_0_mask])
        calibrator_1 = self._fit_calibrator(predictions[group_1_mask], true_labels[group_1_mask])

        # Apply calibration
        adjusted_predictions = predictions.copy()
        adjusted_predictions[group_0_mask] = calibrator_0(predictions[group_0_mask])
        adjusted_predictions[group_1_mask] = calibrator_1(predictions[group_1_mask])

        # Ensure predictions are in [0, 1]
        adjusted_predictions = np.clip(adjusted_predictions, 0, 1)

        # Evaluate after
        binary_preds_after = (adjusted_predictions > 0.5).astype(int)
        fairness_after = self._evaluate_fairness(binary_preds_after, true_labels, protected_attribute, protected_value)
        performance_after = self._evaluate_performance(binary_preds_after, true_labels)

        # Calculate impact
        performance_impact = {
            key: performance_after.get(key, 0) - performance_before.get(key, 0) for key in performance_before.keys()
        }

        # Check success
        fairness_improved = self._check_fairness_improvement(fairness_before, fairness_after)
        performance_acceptable = self._check_performance_acceptable(performance_before, performance_after)

        success = fairness_improved and performance_acceptable

        result = MitigationResult(
            mitigation_method="calibration_adjustment",
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            fairness_before=fairness_before,
            fairness_after=fairness_after,
            performance_impact=performance_impact,
            success=success,
            metadata={
                "predictions_before_mean": float(np.mean(predictions)),
                "predictions_after_mean": float(np.mean(adjusted_predictions)),
                "performance_before": performance_before,
                "performance_after": performance_after,
            },
        )

        logger.info(f"Calibration adjustment complete: success={success}")

        return result

    def mitigate_auto(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
        X_train: np.ndarray | None = None,
        y_train: np.ndarray | None = None,
        model: Any | None = None,
    ) -> MitigationResult:
        """Automatically select and apply best mitigation strategy.

        Tries multiple strategies and returns the best result.

        Args:
            predictions: Model predictions
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            X_train: Training features (for reweighing)
            y_train: Training labels (for reweighing)
            model: Model (for reweighing)

        Returns:
            Best MitigationResult
        """
        logger.info("Starting automatic mitigation strategy selection...")

        results = []

        # Try each strategy
        for strategy in self.mitigation_strategies:
            try:
                if strategy == "threshold_optimization":
                    result = self.mitigate_threshold_optimization(
                        predictions, true_labels, protected_attribute, protected_value
                    )
                    results.append(result)

                elif strategy == "calibration_adjustment":
                    result = self.mitigate_calibration_adjustment(
                        predictions, true_labels, protected_attribute, protected_value
                    )
                    results.append(result)

                elif strategy == "reweighing" and X_train is not None and model is not None:
                    result = self.mitigate_reweighing(X_train, y_train, protected_attribute, protected_value, model)
                    results.append(result)

            except Exception as e:
                logger.error(f"Strategy {strategy} failed: {e}")
                continue

        if not results:
            raise FairnessException("All mitigation strategies failed")

        # Select best result
        best_result = self._select_best_result(results)

        logger.info(
            f"Auto mitigation complete: selected {best_result.mitigation_method}, success={best_result.success}"
        )

        return best_result

    def _calculate_reweighing_weights(
        self, y: np.ndarray, protected_attribute: np.ndarray, protected_value: Any
    ) -> np.ndarray:
        """Calculate reweighing weights for training samples.

        Args:
            y: Labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            Sample weights array
        """
        weights = np.ones(len(y))

        # Calculate expected probabilities
        n = len(y)
        n_pos = np.sum(y == 1)
        n_neg = np.sum(y == 0)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n_0 = np.sum(group_0_mask)
        n_1 = np.sum(group_1_mask)

        # Expected probabilities (if independent)
        p_y_pos = n_pos / n
        p_y_neg = n_neg / n
        p_a_0 = n_0 / n
        p_a_1 = n_1 / n

        # Observed probabilities for each group-outcome combination
        n_0_pos = np.sum((group_0_mask) & (y == 1))
        n_0_neg = np.sum((group_0_mask) & (y == 0))
        n_1_pos = np.sum((group_1_mask) & (y == 1))
        n_1_neg = np.sum((group_1_mask) & (y == 0))

        p_0_pos = n_0_pos / n if n_0_pos > 0 else 0.0001
        p_0_neg = n_0_neg / n if n_0_neg > 0 else 0.0001
        p_1_pos = n_1_pos / n if n_1_pos > 0 else 0.0001
        p_1_neg = n_1_neg / n if n_1_neg > 0 else 0.0001

        # Reweighing factors
        w_0_pos = (p_y_pos * p_a_0) / p_0_pos if p_0_pos > 0 else 1.0
        w_0_neg = (p_y_neg * p_a_0) / p_0_neg if p_0_neg > 0 else 1.0
        w_1_pos = (p_y_pos * p_a_1) / p_1_pos if p_1_pos > 0 else 1.0
        w_1_neg = (p_y_neg * p_a_1) / p_1_neg if p_1_neg > 0 else 1.0

        # Assign weights
        weights[(group_0_mask) & (y == 1)] = w_0_pos
        weights[(group_0_mask) & (y == 0)] = w_0_neg
        weights[(group_1_mask) & (y == 1)] = w_1_pos
        weights[(group_1_mask) & (y == 0)] = w_1_neg

        return weights

    def _find_optimal_thresholds(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any,
        metric: FairnessMetric,
    ) -> tuple[float, float]:
        """Find optimal classification thresholds for each group.

        Args:
            predictions: Prediction scores
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            metric: Target fairness metric

        Returns:
            Tuple of (threshold_group_0, threshold_group_1)
        """
        # Search space for thresholds
        thresholds = np.linspace(0.1, 0.9, 50)

        best_score = float("-inf")
        best_thresholds = (0.5, 0.5)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        # Grid search over threshold combinations
        for t0 in thresholds:
            for t1 in thresholds:
                # Apply thresholds
                binary_preds = np.zeros_like(predictions, dtype=int)
                binary_preds[group_0_mask] = (predictions[group_0_mask] > t0).astype(int)
                binary_preds[group_1_mask] = (predictions[group_1_mask] > t1).astype(int)

                # Evaluate fairness
                fairness_results = self.fairness_constraints.evaluate_all_metrics(
                    binary_preds, true_labels, protected_attribute, protected_value
                )

                # Evaluate performance
                accuracy = np.mean(binary_preds == true_labels)

                # Combined score: balance fairness and performance
                fairness_score = 0.0
                if metric in fairness_results:
                    fairness_score = 1.0 - fairness_results[metric].difference

                # Weighted combination (60% fairness, 40% performance)
                combined_score = 0.6 * fairness_score + 0.4 * accuracy

                if combined_score > best_score:
                    best_score = combined_score
                    best_thresholds = (t0, t1)

        return best_thresholds

    def _fit_calibrator(self, predictions: np.ndarray, true_labels: np.ndarray) -> Callable:
        """Fit isotonic calibration model.

        Args:
            predictions: Prediction scores
            true_labels: True labels

        Returns:
            Calibration function
        """
        # Use Platt scaling (logistic regression)

        # Reshape for sklearn
        X = predictions.reshape(-1, 1)
        y = true_labels

        # Fit logistic regression
        calibrator = LogisticRegression(max_iter=1000)
        calibrator.fit(X, y)

        # Return calibration function
        def calibrate(scores: np.ndarray) -> np.ndarray:
            return calibrator.predict_proba(scores.reshape(-1, 1))[:, 1]

        return calibrate

    def _retrain_with_weights(self, model: Any, X: np.ndarray, y: np.ndarray, weights: np.ndarray) -> Any:
        """Retrain model with sample weights.

        Args:
            model: Original model
            X: Training features
            y: Training labels
            weights: Sample weights

        Returns:
            Retrained model
        """
        # Check if model supports sample weights
        if hasattr(model, "fit"):
            try:
                # Try to fit with sample weights
                model.fit(X, y, sample_weight=weights)
            except TypeError:
                # Fallback: fit without weights
                logger.warning("Model doesn't support sample_weight, fitting without weights")
                model.fit(X, y)

        return model

    def _get_predictions(self, model: Any, X: np.ndarray) -> np.ndarray:
        """Get predictions from model.

        Args:
            model: Trained model
            X: Features

        Returns:
            Predictions array
        """
        if hasattr(model, "predict_proba"):
            return model.predict_proba(X)[:, 1]
        if hasattr(model, "predict"):
            return model.predict(X)
        raise FairnessException("Model has no predict or predict_proba method")

    def _evaluate_fairness(
        self, predictions: np.ndarray, true_labels: np.ndarray, protected_attribute: np.ndarray, protected_value: Any
    ) -> dict[str, float]:
        """Evaluate fairness metrics.

        Args:
            predictions: Predictions
            true_labels: True labels
            protected_attribute: Protected attribute
            protected_value: Protected group value

        Returns:
            Dictionary of fairness metrics
        """
        results = self.fairness_constraints.evaluate_all_metrics(
            predictions, true_labels, protected_attribute, protected_value
        )

        # Convert to simple dict
        fairness_dict = {}
        for metric, result in results.items():
            fairness_dict[f"{metric.value}_difference"] = result.difference
            fairness_dict[f"{metric.value}_ratio"] = result.ratio
            fairness_dict[f"{metric.value}_is_fair"] = 1.0 if result.is_fair else 0.0

        return fairness_dict

    def _evaluate_performance(self, predictions: np.ndarray, true_labels: np.ndarray) -> dict[str, float]:
        """Evaluate model performance.

        Args:
            predictions: Predictions
            true_labels: True labels

        Returns:
            Dictionary of performance metrics
        """
        # Convert to binary if needed
        if predictions.dtype == float:
            binary_preds = (predictions > 0.5).astype(int)
        else:
            binary_preds = predictions

        # Accuracy
        accuracy = np.mean(binary_preds == true_labels)

        # Precision, Recall, F1
        tp = np.sum((binary_preds == 1) & (true_labels == 1))
        fp = np.sum((binary_preds == 1) & (true_labels == 0))
        fn = np.sum((binary_preds == 0) & (true_labels == 1))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {"accuracy": float(accuracy), "precision": float(precision), "recall": float(recall), "f1": float(f1)}

    def _check_fairness_improvement(self, before: dict[str, float], after: dict[str, float]) -> bool:
        """Check if fairness improved.

        Args:
            before: Fairness metrics before mitigation
            after: Fairness metrics after mitigation

        Returns:
            True if fairness improved
        """
        if not before or not after:
            return False

        # Check if any fairness metric improved significantly
        for key in before:
            if "_difference" in key and key in after:
                if before[key] - after[key] > self.fairness_improvement_threshold:
                    return True

        return False

    def _check_performance_acceptable(self, before: dict[str, float], after: dict[str, float]) -> bool:
        """Check if performance is acceptable after mitigation.

        Args:
            before: Performance metrics before
            after: Performance metrics after

        Returns:
            True if performance is acceptable
        """
        if not before or not after:
            return True  # Assume acceptable if no data

        # Check accuracy
        accuracy_before = before.get("accuracy", 0)
        accuracy_after = after.get("accuracy", 0)

        # Must maintain minimum threshold
        if accuracy_after < self.performance_threshold:
            return False

        # Must not lose more than max_performance_loss
        if accuracy_before - accuracy_after > self.max_performance_loss:
            return False

        return True

    def _select_best_result(self, results: list[MitigationResult]) -> MitigationResult:
        """Select best mitigation result.

        Args:
            results: List of mitigation results

        Returns:
            Best result
        """
        if not results:
            raise FairnessException("No results to select from")

        # Filter successful results
        successful = [r for r in results if r.success]

        if successful:
            # Among successful, pick the one with best fairness improvement
            best = max(
                successful,
                key=lambda r: sum(
                    r.fairness_before.get(k, 0) - r.fairness_after.get(k, 0)
                    for k in r.fairness_before.keys()
                    if "_difference" in k
                ),
            )
            return best

        # If none successful, return the one with least performance loss
        best = min(results, key=lambda r: abs(r.performance_impact.get("accuracy", 0)))
        return best
