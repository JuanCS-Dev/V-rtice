"""Bias Detection Module for Cybersecurity AI Models.

This module implements statistical bias detection methods to identify unfair
treatment across protected groups in threat detection and security decisions.

Detection Methods:
    - Statistical parity tests (chi-square)
    - Disparate impact analysis (4/5ths rule)
    - Effect size calculations (Cohen's d)
    - Distribution comparison tests
    - Causal fairness indicators
"""

import logging
from typing import Any

import numpy as np
from scipy import stats

from .base import BiasDetectionResult, InsufficientDataException, ProtectedAttribute

logger = logging.getLogger(__name__)


class BiasDetector:
    """Bias detector for cybersecurity AI models.

    Implements multiple statistical tests and methods to detect bias
    in model predictions across different protected groups.

    Attributes:
        min_sample_size: Minimum samples required per group
        significance_level: Statistical significance level (alpha)
        disparate_impact_threshold: Threshold for disparate impact (default 0.8 = 4/5ths rule)
        effect_size_thresholds: Thresholds for Cohen's d effect size
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize BiasDetector.

        Args:
            config: Configuration dictionary
        """
        config = config or {}

        # Statistical parameters
        self.min_sample_size = config.get("min_sample_size", 30)
        self.significance_level = config.get("significance_level", 0.05)  # 95% confidence
        self.disparate_impact_threshold = config.get("disparate_impact_threshold", 0.8)  # 4/5ths rule

        # Effect size thresholds (Cohen's d)
        self.effect_size_thresholds = config.get("effect_size_thresholds", {"small": 0.2, "medium": 0.5, "large": 0.8})

        # Detection sensitivity
        self.sensitivity = config.get("sensitivity", "medium")  # low, medium, high

        logger.info(
            f"BiasDetector initialized with significance_level={self.significance_level}, "
            f"sensitivity={self.sensitivity}"
        )

    def detect_statistical_parity_bias(
        self, predictions: np.ndarray, protected_attribute: np.ndarray, protected_value: Any = 1
    ) -> BiasDetectionResult:
        """Detect bias using statistical parity (chi-square test).

        Tests whether prediction rates differ significantly between groups.
        H0: Predictions are independent of protected attribute.

        Args:
            predictions: Model predictions (0/1 or probabilities)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            BiasDetectionResult with detection outcome
        """
        # Convert to binary if needed
        if predictions.dtype == float and np.max(predictions) <= 1.0:
            binary_predictions = (predictions > 0.5).astype(int)
        else:
            binary_predictions = predictions.astype(int)

        # Split into groups
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Create contingency table
        # Rows: [Group 0, Group 1]
        # Cols: [Negative Prediction, Positive Prediction]
        group_0_neg = np.sum((binary_predictions == 0) & group_0_mask)
        group_0_pos = np.sum((binary_predictions == 1) & group_0_mask)
        group_1_neg = np.sum((binary_predictions == 0) & group_1_mask)
        group_1_pos = np.sum((binary_predictions == 1) & group_1_mask)

        contingency_table = np.array([[group_0_neg, group_0_pos], [group_1_neg, group_1_pos]])

        # Chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

        # Bias detected if p-value < significance level
        bias_detected = p_value < self.significance_level

        # Calculate effect size (Cramér's V for 2x2 table = phi coefficient)
        n_total = n0 + n1
        cramer_v = np.sqrt(chi2 / n_total)

        # Determine severity based on p-value and effect size
        severity = self._determine_severity(p_value, cramer_v, method="chi_square")

        # Confidence in detection
        confidence = 1.0 - p_value if bias_detected else p_value

        # Identify affected groups
        pos_rate_0 = group_0_pos / n0
        pos_rate_1 = group_1_pos / n1
        affected_groups = []

        if bias_detected:
            if pos_rate_0 > pos_rate_1:
                affected_groups.append(f"Protected group (lower positive rate: {pos_rate_1:.2%} vs {pos_rate_0:.2%})")
            else:
                affected_groups.append(f"Reference group (lower positive rate: {pos_rate_0:.2%} vs {pos_rate_1:.2%})")

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,  # Will be set by caller
            detection_method="statistical_parity_chi_square",
            p_value=float(p_value),
            effect_size=float(cramer_v),
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n_total),
            metadata={
                "chi2_statistic": float(chi2),
                "degrees_of_freedom": int(dof),
                "contingency_table": contingency_table.tolist(),
                "pos_rate_group_0": float(pos_rate_0),
                "pos_rate_group_1": float(pos_rate_1),
                "cramers_v": float(cramer_v),
            },
        )

        logger.debug(
            f"Statistical Parity Test: chi2={chi2:.3f}, p={p_value:.4f}, "
            f"bias_detected={bias_detected}, severity={severity}"
        )

        return result

    def detect_disparate_impact(
        self, predictions: np.ndarray, protected_attribute: np.ndarray, protected_value: Any = 1
    ) -> BiasDetectionResult:
        """Detect bias using disparate impact analysis (4/5ths rule).

        Tests whether the selection rate for the protected group is at least
        80% (4/5ths) of the selection rate for the reference group.

        Args:
            predictions: Model predictions (0/1 or probabilities)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            BiasDetectionResult with detection outcome
        """
        # Convert to binary
        if predictions.dtype == float and np.max(predictions) <= 1.0:
            binary_predictions = (predictions > 0.5).astype(int)
        else:
            binary_predictions = predictions.astype(int)

        # Split into groups
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Calculate selection rates (positive prediction rates)
        selection_rate_0 = np.mean(binary_predictions[group_0_mask])
        selection_rate_1 = np.mean(binary_predictions[group_1_mask])

        # Calculate disparate impact ratio
        # Ratio of protected group rate to reference group rate
        if selection_rate_0 > 0:
            di_ratio = selection_rate_1 / selection_rate_0
        else:
            di_ratio = 1.0 if selection_rate_1 == 0 else float("inf")

        # Bias detected if ratio < threshold (4/5ths = 0.8)
        bias_detected = di_ratio < self.disparate_impact_threshold

        # Also check reverse bias (protected group favored too much)
        if di_ratio > (1.0 / self.disparate_impact_threshold):
            bias_detected = True

        # Determine severity based on how far from threshold
        deviation = abs(di_ratio - 1.0)
        if deviation < 0.1:
            severity = "low"
        elif deviation < 0.3:
            severity = "medium"
        elif deviation < 0.5:
            severity = "high"
        else:
            severity = "critical"

        # Confidence based on sample size and deviation
        confidence = min(1.0, deviation * np.sqrt(min(n0, n1) / self.min_sample_size))

        # Identify affected groups
        affected_groups = []
        if bias_detected:
            if di_ratio < self.disparate_impact_threshold:
                affected_groups.append(
                    f"Protected group (selection rate {selection_rate_1:.2%} is {di_ratio:.1%} "
                    f"of reference group rate {selection_rate_0:.2%})"
                )
            else:
                affected_groups.append(f"Reference group (protected group favored with ratio {di_ratio:.2f})")

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="disparate_impact_4_5ths_rule",
            p_value=None,  # Not applicable for this method
            effect_size=float(abs(1.0 - di_ratio)),  # Deviation from parity
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n0 + n1),
            metadata={
                "disparate_impact_ratio": float(di_ratio),
                "selection_rate_group_0": float(selection_rate_0),
                "selection_rate_group_1": float(selection_rate_1),
                "threshold": self.disparate_impact_threshold,
                "passes_4_5ths_rule": di_ratio >= self.disparate_impact_threshold,
            },
        )

        logger.debug(
            f"Disparate Impact: ratio={di_ratio:.3f}, threshold={self.disparate_impact_threshold}, "
            f"bias_detected={bias_detected}, severity={severity}"
        )

        return result

    def detect_distribution_bias(
        self, predictions: np.ndarray, protected_attribute: np.ndarray, protected_value: Any = 1
    ) -> BiasDetectionResult:
        """Detect bias using distribution comparison (Kolmogorov-Smirnov test).

        Tests whether prediction distributions differ between groups.
        Useful for continuous predictions (scores, probabilities).

        Args:
            predictions: Model predictions (continuous values)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            BiasDetectionResult with detection outcome
        """
        # Split into groups
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Get predictions for each group
        preds_0 = predictions[group_0_mask]
        preds_1 = predictions[group_1_mask]

        # Kolmogorov-Smirnov test
        ks_statistic, p_value = stats.ks_2samp(preds_0, preds_1)

        # Bias detected if distributions differ significantly
        bias_detected = p_value < self.significance_level

        # Calculate effect size (Cohen's d)
        mean_0 = np.mean(preds_0)
        mean_1 = np.mean(preds_1)
        std_0 = np.std(preds_0, ddof=1)
        std_1 = np.std(preds_1, ddof=1)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n0 - 1) * std_0**2 + (n1 - 1) * std_1**2) / (n0 + n1 - 2))

        cohens_d = (mean_0 - mean_1) / pooled_std if pooled_std > 0 else 0.0

        # Determine severity
        severity = self._determine_severity(p_value, abs(cohens_d), method="ks_test")

        # Confidence
        confidence = 1.0 - p_value if bias_detected else p_value

        # Affected groups
        affected_groups = []
        if bias_detected:
            if mean_0 > mean_1:
                affected_groups.append(f"Protected group (lower mean score: {mean_1:.3f} vs {mean_0:.3f})")
            else:
                affected_groups.append(f"Reference group (lower mean score: {mean_0:.3f} vs {mean_1:.3f})")

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="distribution_ks_test",
            p_value=float(p_value),
            effect_size=float(abs(cohens_d)),
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n0 + n1),
            metadata={
                "ks_statistic": float(ks_statistic),
                "mean_group_0": float(mean_0),
                "mean_group_1": float(mean_1),
                "std_group_0": float(std_0),
                "std_group_1": float(std_1),
                "cohens_d": float(cohens_d),
                "effect_size_category": self._categorize_effect_size(abs(cohens_d)),
            },
        )

        logger.debug(
            f"Distribution Test: KS={ks_statistic:.3f}, p={p_value:.4f}, "
            f"Cohen's d={cohens_d:.3f}, bias_detected={bias_detected}"
        )

        return result

    def detect_performance_disparity(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> BiasDetectionResult:
        """Detect bias through performance disparity across groups.

        Tests whether model performance (accuracy, F1) differs between groups.

        Args:
            predictions: Model predictions (0/1)
            true_labels: True labels (0/1)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            BiasDetectionResult with detection outcome
        """
        # Convert to binary
        if predictions.dtype == float and np.max(predictions) <= 1.0:
            binary_predictions = (predictions > 0.5).astype(int)
        else:
            binary_predictions = predictions.astype(int)

        binary_labels = true_labels.astype(int)

        # Split into groups
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Calculate accuracy for each group
        accuracy_0 = np.mean(binary_predictions[group_0_mask] == binary_labels[group_0_mask])
        accuracy_1 = np.mean(binary_predictions[group_1_mask] == binary_labels[group_1_mask])

        # Calculate F1 score for each group
        f1_0 = self._calculate_f1_score(binary_predictions[group_0_mask], binary_labels[group_0_mask])
        f1_1 = self._calculate_f1_score(binary_predictions[group_1_mask], binary_labels[group_1_mask])

        # Performance disparity
        accuracy_diff = abs(accuracy_0 - accuracy_1)
        f1_diff = abs(f1_0 - f1_1)

        # Bias detected if performance differs significantly (threshold based on sensitivity)
        thresholds = {
            "low": 0.15,  # 15% difference
            "medium": 0.10,  # 10% difference
            "high": 0.05,  # 5% difference
        }
        threshold = thresholds.get(self.sensitivity, 0.10)

        bias_detected = (accuracy_diff > threshold) or (f1_diff > threshold)

        # Severity based on max difference
        max_diff = max(accuracy_diff, f1_diff)
        if max_diff < 0.05:
            severity = "low"
        elif max_diff < 0.10:
            severity = "medium"
        elif max_diff < 0.20:
            severity = "high"
        else:
            severity = "critical"

        # Confidence based on sample sizes and difference magnitude
        confidence = min(1.0, max_diff * 5 * np.sqrt(min(n0, n1) / self.min_sample_size))

        # Affected groups
        affected_groups = []
        if bias_detected:
            if accuracy_0 > accuracy_1:
                affected_groups.append(f"Protected group (lower accuracy: {accuracy_1:.2%} vs {accuracy_0:.2%})")
            elif accuracy_1 > accuracy_0:
                affected_groups.append(f"Reference group (lower accuracy: {accuracy_0:.2%} vs {accuracy_1:.2%})")

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="performance_disparity",
            p_value=None,  # Could add statistical test if needed
            effect_size=float(max_diff),
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n0 + n1),
            metadata={
                "accuracy_group_0": float(accuracy_0),
                "accuracy_group_1": float(accuracy_1),
                "accuracy_difference": float(accuracy_diff),
                "f1_group_0": float(f1_0),
                "f1_group_1": float(f1_1),
                "f1_difference": float(f1_diff),
                "threshold": threshold,
            },
        )

        logger.debug(
            f"Performance Disparity: acc_diff={accuracy_diff:.3f}, f1_diff={f1_diff:.3f}, "
            f"bias_detected={bias_detected}, severity={severity}"
        )

        return result

    def detect_all_biases(
        self,
        predictions: np.ndarray,
        protected_attribute: np.ndarray,
        true_labels: np.ndarray | None = None,
        protected_value: Any = 1,
    ) -> dict[str, BiasDetectionResult]:
        """Run all applicable bias detection methods.

        Args:
            predictions: Model predictions
            protected_attribute: Protected attribute values
            true_labels: True labels (optional, needed for some methods)
            protected_value: Value indicating protected group

        Returns:
            Dictionary mapping method names to results
        """
        results = {}

        # Statistical parity (chi-square)
        try:
            results["statistical_parity"] = self.detect_statistical_parity_bias(
                predictions, protected_attribute, protected_value
            )
        except Exception as e:
            logger.error(f"Statistical parity detection failed: {e}")

        # Disparate impact
        try:
            results["disparate_impact"] = self.detect_disparate_impact(
                predictions, protected_attribute, protected_value
            )
        except Exception as e:
            logger.error(f"Disparate impact detection failed: {e}")

        # Distribution comparison
        try:
            results["distribution"] = self.detect_distribution_bias(predictions, protected_attribute, protected_value)
        except Exception as e:
            logger.error(f"Distribution bias detection failed: {e}")

        # Performance disparity (requires true labels)
        if true_labels is not None:
            try:
                results["performance_disparity"] = self.detect_performance_disparity(
                    predictions, true_labels, protected_attribute, protected_value
                )
            except Exception as e:
                logger.error(f"Performance disparity detection failed: {e}")

        return results

    def _determine_severity(self, p_value: float, effect_size: float, method: str) -> str:
        """Determine severity of bias based on p-value and effect size.

        Args:
            p_value: Statistical p-value
            effect_size: Effect size measure
            method: Detection method used

        Returns:
            Severity level: low, medium, high, or critical
        """
        # Very strong statistical significance + large effect
        if p_value < 0.001 and effect_size > self.effect_size_thresholds["large"]:
            return "critical"

        # Strong significance + medium/large effect
        if p_value < 0.01 and effect_size > self.effect_size_thresholds["medium"]:
            return "high"

        # Moderate significance + small/medium effect
        if p_value < self.significance_level and effect_size > self.effect_size_thresholds["small"]:
            return "medium"

        # Weak evidence of bias
        return "low"

    def _categorize_effect_size(self, cohens_d: float) -> str:
        """Categorize Cohen's d effect size.

        Args:
            cohens_d: Cohen's d value

        Returns:
            Category: negligible, small, medium, large, or very_large
        """
        abs_d = abs(cohens_d)

        if abs_d < self.effect_size_thresholds["small"]:
            return "negligible"
        if abs_d < self.effect_size_thresholds["medium"]:
            return "small"
        if abs_d < self.effect_size_thresholds["large"]:
            return "medium"
        if abs_d < 1.2:
            return "large"
        return "very_large"

    def _calculate_f1_score(self, predictions: np.ndarray, true_labels: np.ndarray) -> float:
        """Calculate F1 score.

        Args:
            predictions: Binary predictions
            true_labels: True labels

        Returns:
            F1 score
        """
        # True positives, false positives, false negatives
        tp = np.sum((predictions == 1) & (true_labels == 1))
        fp = np.sum((predictions == 1) & (true_labels == 0))
        fn = np.sum((predictions == 0) & (true_labels == 1))

        # Precision and recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return f1
