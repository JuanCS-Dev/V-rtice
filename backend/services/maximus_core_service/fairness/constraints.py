"""Fairness Constraints Implementation.

This module implements fairness constraints for cybersecurity AI models,
including demographic parity, equalized odds, and calibration metrics.
"""

import logging
from typing import Any

import numpy as np

from .base import (
    FairnessMetric,
    FairnessResult,
    FairnessViolationException,
    InsufficientDataException,
    ProtectedAttribute,
)

logger = logging.getLogger(__name__)


class FairnessConstraints:
    """Fairness constraints validator for cybersecurity models.

    Implements multiple fairness metrics to ensure equitable treatment
    across different protected groups in threat detection and security decisions.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize FairnessConstraints.

        Args:
            config: Configuration dictionary with thresholds
        """
        config = config or {}

        # Fairness thresholds (max allowed disparity)
        self.thresholds = {
            FairnessMetric.DEMOGRAPHIC_PARITY: config.get("demographic_parity_threshold", 0.1),  # 10%
            FairnessMetric.EQUALIZED_ODDS: config.get("equalized_odds_threshold", 0.1),
            FairnessMetric.EQUAL_OPPORTUNITY: config.get("equal_opportunity_threshold", 0.1),
            FairnessMetric.CALIBRATION: config.get("calibration_threshold", 0.1),
            FairnessMetric.PREDICTIVE_PARITY: config.get("predictive_parity_threshold", 0.1),
            FairnessMetric.TREATMENT_EQUALITY: config.get("treatment_equality_threshold", 0.2),
        }

        # Minimum sample size per group
        self.min_sample_size = config.get("min_sample_size", 30)

        # Enforcement mode
        self.enforcement_mode = config.get("enforcement_mode", "warn")  # 'warn' or 'reject'

        logger.info(f"FairnessConstraints initialized with enforcement_mode={self.enforcement_mode}")

    def evaluate_demographic_parity(
        self, predictions: np.ndarray, protected_attribute: np.ndarray, protected_value: Any = 1
    ) -> FairnessResult:
        """Evaluate demographic parity: P(Ŷ=1|A=0) ≈ P(Ŷ=1|A=1).

        Args:
            predictions: Model predictions (0/1 or probabilities)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group (default=1)

        Returns:
            FairnessResult with demographic parity evaluation
        """
        # Convert probabilities to binary if needed
        if predictions.dtype == float and np.max(predictions) <= 1.0:
            binary_predictions = (predictions > 0.5).astype(int)
        else:
            binary_predictions = predictions.astype(int)

        # Split into groups
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        # Check sample sizes
        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Calculate positive prediction rates
        pr_0 = np.mean(binary_predictions[group_0_mask])
        pr_1 = np.mean(binary_predictions[group_1_mask])

        # Calculate disparity
        difference = abs(pr_0 - pr_1)
        ratio = min(pr_0, pr_1) / max(pr_0, pr_1) if max(pr_0, pr_1) > 0 else 1.0

        # Check fairness
        threshold = self.thresholds[FairnessMetric.DEMOGRAPHIC_PARITY]
        is_fair = difference <= threshold

        result = FairnessResult(
            metric=FairnessMetric.DEMOGRAPHIC_PARITY,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,  # Will be updated by caller
            group_0_value=pr_0,
            group_1_value=pr_1,
            difference=difference,
            ratio=ratio,
            is_fair=is_fair,
            threshold=threshold,
            sample_size_0=int(n0),
            sample_size_1=int(n1),
        )

        logger.debug(f"Demographic Parity: Group0={pr_0:.3f}, Group1={pr_1:.3f}, Diff={difference:.3f}, Fair={is_fair}")

        if not is_fair and self.enforcement_mode == "reject":
            raise FairnessViolationException(FairnessMetric.DEMOGRAPHIC_PARITY, result)

        return result

    def evaluate_equalized_odds(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> FairnessResult:
        """Evaluate equalized odds: TPR and FPR equal across groups.

        Args:
            predictions: Model predictions (0/1)
            true_labels: True labels (0/1)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            FairnessResult with equalized odds evaluation
        """
        # Convert to binary
        binary_predictions = (predictions > 0.5).astype(int) if predictions.dtype == float else predictions.astype(int)
        binary_labels = true_labels.astype(int)

        # Split into groups
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        # Check sample sizes
        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Calculate TPR and FPR for each group
        tpr_0 = self._calculate_tpr(binary_predictions[group_0_mask], binary_labels[group_0_mask])
        tpr_1 = self._calculate_tpr(binary_predictions[group_1_mask], binary_labels[group_1_mask])

        fpr_0 = self._calculate_fpr(binary_predictions[group_0_mask], binary_labels[group_0_mask])
        fpr_1 = self._calculate_fpr(binary_predictions[group_1_mask], binary_labels[group_1_mask])

        # Equalized odds requires BOTH TPR and FPR to be similar
        tpr_diff = abs(tpr_0 - tpr_1)
        fpr_diff = abs(fpr_0 - fpr_1)

        # Combined metric: max of TPR and FPR differences
        max_difference = max(tpr_diff, fpr_diff)
        avg_ratio = (
            (min(tpr_0, tpr_1) / max(tpr_0, tpr_1) + min(fpr_0, fpr_1) / max(fpr_0, fpr_1)) / 2
            if max(tpr_0, tpr_1) > 0 and max(fpr_0, fpr_1) > 0
            else 1.0
        )

        threshold = self.thresholds[FairnessMetric.EQUALIZED_ODDS]
        is_fair = max_difference <= threshold

        result = FairnessResult(
            metric=FairnessMetric.EQUALIZED_ODDS,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            group_0_value=(tpr_0 + fpr_0) / 2,  # Average for simplicity
            group_1_value=(tpr_1 + fpr_1) / 2,
            difference=max_difference,
            ratio=avg_ratio,
            is_fair=is_fair,
            threshold=threshold,
            sample_size_0=int(n0),
            sample_size_1=int(n1),
            metadata={
                "tpr_0": tpr_0,
                "tpr_1": tpr_1,
                "fpr_0": fpr_0,
                "fpr_1": fpr_1,
                "tpr_diff": tpr_diff,
                "fpr_diff": fpr_diff,
            },
        )

        logger.debug(
            f"Equalized Odds: TPR_diff={tpr_diff:.3f}, FPR_diff={fpr_diff:.3f}, "
            f"Max_diff={max_difference:.3f}, Fair={is_fair}"
        )

        if not is_fair and self.enforcement_mode == "reject":
            raise FairnessViolationException(FairnessMetric.EQUALIZED_ODDS, result)

        return result

    def evaluate_equal_opportunity(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> FairnessResult:
        """Evaluate equal opportunity: TPR equal across groups.

        Args:
            predictions: Model predictions (0/1)
            true_labels: True labels (0/1)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            FairnessResult with equal opportunity evaluation
        """
        binary_predictions = (predictions > 0.5).astype(int) if predictions.dtype == float else predictions.astype(int)
        binary_labels = true_labels.astype(int)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Calculate TPR for each group
        tpr_0 = self._calculate_tpr(binary_predictions[group_0_mask], binary_labels[group_0_mask])
        tpr_1 = self._calculate_tpr(binary_predictions[group_1_mask], binary_labels[group_1_mask])

        difference = abs(tpr_0 - tpr_1)
        ratio = min(tpr_0, tpr_1) / max(tpr_0, tpr_1) if max(tpr_0, tpr_1) > 0 else 1.0

        threshold = self.thresholds[FairnessMetric.EQUAL_OPPORTUNITY]
        is_fair = difference <= threshold

        result = FairnessResult(
            metric=FairnessMetric.EQUAL_OPPORTUNITY,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            group_0_value=tpr_0,
            group_1_value=tpr_1,
            difference=difference,
            ratio=ratio,
            is_fair=is_fair,
            threshold=threshold,
            sample_size_0=int(n0),
            sample_size_1=int(n1),
        )

        logger.debug(f"Equal Opportunity: TPR0={tpr_0:.3f}, TPR1={tpr_1:.3f}, Diff={difference:.3f}, Fair={is_fair}")

        if not is_fair and self.enforcement_mode == "reject":
            raise FairnessViolationException(FairnessMetric.EQUAL_OPPORTUNITY, result)

        return result

    def evaluate_calibration(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
        num_bins: int = 10,
    ) -> FairnessResult:
        """Evaluate calibration: P(Y=1|Ŷ=p,A=0) ≈ P(Y=1|Ŷ=p,A=1).

        Args:
            predictions: Model prediction probabilities
            true_labels: True labels (0/1)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            num_bins: Number of bins for calibration

        Returns:
            FairnessResult with calibration evaluation
        """
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        # Calculate calibration error for each group
        cal_error_0 = self._calculate_calibration_error(predictions[group_0_mask], true_labels[group_0_mask], num_bins)

        cal_error_1 = self._calculate_calibration_error(predictions[group_1_mask], true_labels[group_1_mask], num_bins)

        # Difference in calibration errors
        difference = abs(cal_error_0 - cal_error_1)
        ratio = (
            min(cal_error_0, cal_error_1) / max(cal_error_0, cal_error_1) if max(cal_error_0, cal_error_1) > 0 else 1.0
        )

        threshold = self.thresholds[FairnessMetric.CALIBRATION]
        is_fair = difference <= threshold

        result = FairnessResult(
            metric=FairnessMetric.CALIBRATION,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            group_0_value=cal_error_0,
            group_1_value=cal_error_1,
            difference=difference,
            ratio=ratio,
            is_fair=is_fair,
            threshold=threshold,
            sample_size_0=int(n0),
            sample_size_1=int(n1),
        )

        logger.debug(
            f"Calibration: Error0={cal_error_0:.3f}, Error1={cal_error_1:.3f}, Diff={difference:.3f}, Fair={is_fair}"
        )

        if not is_fair and self.enforcement_mode == "reject":
            raise FairnessViolationException(FairnessMetric.CALIBRATION, result)

        return result

    def evaluate_all_metrics(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray | None,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> dict[FairnessMetric, FairnessResult]:
        """Evaluate all applicable fairness metrics.

        Args:
            predictions: Model predictions
            true_labels: True labels (optional, needed for some metrics)
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            Dictionary mapping metrics to results
        """
        results = {}

        # Demographic parity (doesn't need labels)
        try:
            results[FairnessMetric.DEMOGRAPHIC_PARITY] = self.evaluate_demographic_parity(
                predictions, protected_attribute, protected_value
            )
        except Exception as e:
            logger.error(f"Demographic parity evaluation failed: {e}")

        # Metrics that need true labels
        if true_labels is not None:
            try:
                results[FairnessMetric.EQUALIZED_ODDS] = self.evaluate_equalized_odds(
                    predictions, true_labels, protected_attribute, protected_value
                )
            except Exception as e:
                logger.error(f"Equalized odds evaluation failed: {e}")

            try:
                results[FairnessMetric.EQUAL_OPPORTUNITY] = self.evaluate_equal_opportunity(
                    predictions, true_labels, protected_attribute, protected_value
                )
            except Exception as e:
                logger.error(f"Equal opportunity evaluation failed: {e}")

            try:
                results[FairnessMetric.CALIBRATION] = self.evaluate_calibration(
                    predictions, true_labels, protected_attribute, protected_value
                )
            except Exception as e:
                logger.error(f"Calibration evaluation failed: {e}")

        return results

    def _calculate_tpr(self, predictions: np.ndarray, true_labels: np.ndarray) -> float:
        """Calculate True Positive Rate.

        Args:
            predictions: Binary predictions
            true_labels: True labels

        Returns:
            TPR value
        """
        positives = true_labels == 1
        if np.sum(positives) == 0:
            return 0.0

        true_positives = np.sum((predictions == 1) & (true_labels == 1))
        return true_positives / np.sum(positives)

    def _calculate_fpr(self, predictions: np.ndarray, true_labels: np.ndarray) -> float:
        """Calculate False Positive Rate.

        Args:
            predictions: Binary predictions
            true_labels: True labels

        Returns:
            FPR value
        """
        negatives = true_labels == 0
        if np.sum(negatives) == 0:
            return 0.0

        false_positives = np.sum((predictions == 1) & (true_labels == 0))
        return false_positives / np.sum(negatives)

    def _calculate_calibration_error(self, predictions: np.ndarray, true_labels: np.ndarray, num_bins: int) -> float:
        """Calculate Expected Calibration Error (ECE).

        Args:
            predictions: Prediction probabilities
            true_labels: True labels
            num_bins: Number of bins

        Returns:
            ECE value
        """
        # Create bins
        bins = np.linspace(0, 1, num_bins + 1)
        bin_indices = np.digitize(predictions, bins) - 1
        bin_indices = np.clip(bin_indices, 0, num_bins - 1)

        # Calculate ECE
        ece = 0.0
        total_samples = len(predictions)

        for i in range(num_bins):
            bin_mask = bin_indices == i
            if np.sum(bin_mask) == 0:
                continue

            bin_predictions = predictions[bin_mask]
            bin_labels = true_labels[bin_mask]

            # Average predicted probability in bin
            avg_pred = np.mean(bin_predictions)

            # Actual positive rate in bin
            actual_rate = np.mean(bin_labels)

            # Weighted error
            bin_weight = np.sum(bin_mask) / total_samples
            ece += bin_weight * abs(avg_pred - actual_rate)

        return ece
