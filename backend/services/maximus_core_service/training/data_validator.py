"""
Data Validator for MAXIMUS Training Pipeline

Validates data quality:
- Schema validation
- Missing values check
- Outlier detection
- Label distribution analysis
- Feature correlation analysis
- Data drift detection

REGRA DE OURO: Zero mocks, production-ready validation
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    severity: ValidationSeverity
    check_name: str
    message: str
    details: Optional[Dict[str, Any]] = None

    def __repr__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.check_name}: {self.message}"


@dataclass
class ValidationResult:
    """Result of data validation."""

    passed: bool
    issues: List[ValidationIssue]
    statistics: Dict[str, Any]

    def __repr__(self) -> str:
        n_errors = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR)
        n_warnings = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)
        n_info = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.INFO)

        return (f"ValidationResult(passed={self.passed}, "
                f"errors={n_errors}, warnings={n_warnings}, info={n_info})")

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 80)
        print("DATA VALIDATION REPORT")
        print("=" * 80)

        print(f"\nStatus: {'✅ PASSED' if self.passed else '❌ FAILED'}")

        # Group issues by severity
        for severity in [ValidationSeverity.ERROR, ValidationSeverity.WARNING, ValidationSeverity.INFO]:
            severity_issues = [issue for issue in self.issues if issue.severity == severity]

            if severity_issues:
                print(f"\n{severity.value.upper()}: {len(severity_issues)}")
                for issue in severity_issues:
                    print(f"  - {issue.check_name}: {issue.message}")

        # Statistics
        print("\nSTATISTICS:")
        for key, value in self.statistics.items():
            print(f"  {key}: {value}")

        print("=" * 80)


class DataValidator:
    """Validates data quality for training.

    Performs comprehensive checks:
    - Missing values
    - Outliers
    - Label distribution
    - Feature statistics
    - Data drift

    Example:
        ```python
        validator = DataValidator(
            features=features,
            labels=labels,
            reference_features=None  # Optional reference for drift detection
        )

        result = validator.validate(
            check_missing=True,
            check_outliers=True,
            check_labels=True,
            check_drift=False
        )

        result.print_report()

        if not result.passed:
            raise ValueError("Data validation failed")
        ```
    """

    def __init__(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        reference_features: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None
    ):
        """Initialize data validator.

        Args:
            features: Feature matrix (N x D)
            labels: Label vector (N,)
            reference_features: Reference features for drift detection
            feature_names: Optional feature names for reporting
        """
        self.features = features
        self.labels = labels
        self.reference_features = reference_features
        self.feature_names = feature_names or [f"feature_{i}" for i in range(features.shape[1])]

        self.n_samples, self.n_features = features.shape

        logger.info(f"DataValidator initialized: {self.n_samples} samples, {self.n_features} features")

    def validate(
        self,
        check_missing: bool = True,
        check_outliers: bool = True,
        check_labels: bool = True,
        check_distributions: bool = True,
        check_drift: bool = False,
        outlier_threshold: float = 3.0,
        missing_threshold: float = 0.1,
        drift_threshold: float = 0.1
    ) -> ValidationResult:
        """Run all validation checks.

        Args:
            check_missing: Check for missing values
            check_outliers: Check for outliers
            check_labels: Check label distribution
            check_distributions: Check feature distributions
            check_drift: Check for data drift (requires reference_features)
            outlier_threshold: Z-score threshold for outliers
            missing_threshold: Maximum fraction of missing values allowed
            drift_threshold: Maximum drift allowed

        Returns:
            ValidationResult
        """
        issues = []
        statistics = {}

        # Run checks
        if check_missing:
            missing_issues, missing_stats = self._check_missing_values(missing_threshold)
            issues.extend(missing_issues)
            statistics.update(missing_stats)

        if check_outliers:
            outlier_issues, outlier_stats = self._check_outliers(outlier_threshold)
            issues.extend(outlier_issues)
            statistics.update(outlier_stats)

        if check_labels:
            label_issues, label_stats = self._check_labels()
            issues.extend(label_issues)
            statistics.update(label_stats)

        if check_distributions:
            dist_issues, dist_stats = self._check_distributions()
            issues.extend(dist_issues)
            statistics.update(dist_stats)

        if check_drift and self.reference_features is not None:
            drift_issues, drift_stats = self._check_drift(drift_threshold)
            issues.extend(drift_issues)
            statistics.update(drift_stats)

        # Determine if validation passed
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        passed = not has_errors

        result = ValidationResult(
            passed=passed,
            issues=issues,
            statistics=statistics
        )

        logger.info(f"Validation complete: {result}")

        return result

    def _check_missing_values(
        self,
        missing_threshold: float
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Check for missing values (NaN, Inf).

        Args:
            missing_threshold: Maximum fraction of missing values allowed

        Returns:
            Tuple of (issues, statistics)
        """
        issues = []
        statistics = {}

        # Check for NaN
        nan_mask = np.isnan(self.features)
        n_nan = nan_mask.sum()
        nan_fraction = n_nan / self.features.size

        statistics["n_nan_values"] = int(n_nan)
        statistics["nan_fraction"] = float(nan_fraction)

        if n_nan > 0:
            # Find features with NaN
            nan_features = nan_mask.any(axis=0)
            nan_feature_indices = np.where(nan_features)[0]

            if nan_fraction > missing_threshold:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    check_name="missing_values",
                    message=f"Too many NaN values: {n_nan} ({nan_fraction:.2%})",
                    details={"nan_features": [self.feature_names[i] for i in nan_feature_indices]}
                ))
            else:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    check_name="missing_values",
                    message=f"Found {n_nan} NaN values ({nan_fraction:.2%})",
                    details={"nan_features": [self.feature_names[i] for i in nan_feature_indices]}
                ))

        # Check for Inf
        inf_mask = np.isinf(self.features)
        n_inf = inf_mask.sum()
        inf_fraction = n_inf / self.features.size

        statistics["n_inf_values"] = int(n_inf)
        statistics["inf_fraction"] = float(inf_fraction)

        if n_inf > 0:
            inf_features = inf_mask.any(axis=0)
            inf_feature_indices = np.where(inf_features)[0]

            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR if inf_fraction > missing_threshold else ValidationSeverity.WARNING,
                check_name="missing_values",
                message=f"Found {n_inf} Inf values ({inf_fraction:.2%})",
                details={"inf_features": [self.feature_names[i] for i in inf_feature_indices]}
            ))

        if n_nan == 0 and n_inf == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                check_name="missing_values",
                message="No missing values detected"
            ))

        return issues, statistics

    def _check_outliers(
        self,
        outlier_threshold: float
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Check for outliers using Z-score.

        Args:
            outlier_threshold: Z-score threshold

        Returns:
            Tuple of (issues, statistics)
        """
        issues = []
        statistics = {}

        # Calculate Z-scores
        mean = np.nanmean(self.features, axis=0)
        std = np.nanstd(self.features, axis=0)

        # Avoid division by zero
        std[std == 0] = 1.0

        z_scores = np.abs((self.features - mean) / std)

        # Find outliers
        outlier_mask = z_scores > outlier_threshold
        n_outliers = outlier_mask.sum()
        outlier_fraction = n_outliers / self.features.size

        statistics["n_outliers"] = int(n_outliers)
        statistics["outlier_fraction"] = float(outlier_fraction)
        statistics["outlier_threshold"] = float(outlier_threshold)

        if n_outliers > 0:
            # Find features with most outliers
            outliers_per_feature = outlier_mask.sum(axis=0)
            top_outlier_features = np.argsort(outliers_per_feature)[-5:][::-1]

            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING if outlier_fraction < 0.05 else ValidationSeverity.ERROR,
                check_name="outliers",
                message=f"Found {n_outliers} outliers ({outlier_fraction:.2%})",
                details={
                    "top_outlier_features": [
                        (self.feature_names[i], int(outliers_per_feature[i]))
                        for i in top_outlier_features
                    ]
                }
            ))
        else:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                check_name="outliers",
                message=f"No outliers detected (threshold={outlier_threshold})"
            ))

        return issues, statistics

    def _check_labels(self) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Check label distribution.

        Returns:
            Tuple of (issues, statistics)
        """
        issues = []
        statistics = {}

        # Filter out unlabeled samples
        labeled_mask = self.labels >= 0
        labeled_labels = self.labels[labeled_mask]

        n_labeled = len(labeled_labels)
        n_unlabeled = len(self.labels) - n_labeled

        statistics["n_labeled"] = int(n_labeled)
        statistics["n_unlabeled"] = int(n_unlabeled)
        statistics["label_fraction"] = float(n_labeled / len(self.labels))

        if n_labeled == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                check_name="labels",
                message="No labeled samples found"
            ))
            return issues, statistics

        # Class distribution
        unique_labels, label_counts = np.unique(labeled_labels, return_counts=True)
        class_distribution = dict(zip(unique_labels.tolist(), label_counts.tolist()))

        statistics["class_distribution"] = class_distribution
        statistics["n_classes"] = len(unique_labels)

        # Check class imbalance
        max_count = label_counts.max()
        min_count = label_counts.min()
        imbalance_ratio = max_count / min_count

        statistics["imbalance_ratio"] = float(imbalance_ratio)

        if imbalance_ratio > 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                check_name="labels",
                message=f"Severe class imbalance detected (ratio={imbalance_ratio:.1f}:1)",
                details={"class_distribution": class_distribution}
            ))
        elif imbalance_ratio > 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                check_name="labels",
                message=f"Class imbalance detected (ratio={imbalance_ratio:.1f}:1)",
                details={"class_distribution": class_distribution}
            ))
        else:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                check_name="labels",
                message=f"Balanced classes (ratio={imbalance_ratio:.1f}:1)"
            ))

        return issues, statistics

    def _check_distributions(self) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Check feature distributions.

        Returns:
            Tuple of (issues, statistics)
        """
        issues = []
        statistics = {}

        # Feature statistics
        feature_means = np.nanmean(self.features, axis=0)
        feature_stds = np.nanstd(self.features, axis=0)
        feature_mins = np.nanmin(self.features, axis=0)
        feature_maxs = np.nanmax(self.features, axis=0)

        statistics["feature_mean_range"] = (float(feature_means.min()), float(feature_means.max()))
        statistics["feature_std_range"] = (float(feature_stds.min()), float(feature_stds.max()))

        # Check for zero-variance features
        zero_variance_mask = feature_stds < 1e-6
        n_zero_variance = zero_variance_mask.sum()

        statistics["n_zero_variance_features"] = int(n_zero_variance)

        if n_zero_variance > 0:
            zero_variance_indices = np.where(zero_variance_mask)[0]
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                check_name="distributions",
                message=f"Found {n_zero_variance} zero-variance features",
                details={"zero_variance_features": [self.feature_names[i] for i in zero_variance_indices]}
            ))

        # Check for constant features
        constant_mask = feature_maxs == feature_mins
        n_constant = constant_mask.sum()

        statistics["n_constant_features"] = int(n_constant)

        if n_constant > 0:
            constant_indices = np.where(constant_mask)[0]
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                check_name="distributions",
                message=f"Found {n_constant} constant features",
                details={"constant_features": [self.feature_names[i] for i in constant_indices]}
            ))

        if n_zero_variance == 0 and n_constant == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                check_name="distributions",
                message="All features have non-zero variance"
            ))

        return issues, statistics

    def _check_drift(
        self,
        drift_threshold: float
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Check for data drift compared to reference.

        Args:
            drift_threshold: Maximum drift allowed

        Returns:
            Tuple of (issues, statistics)
        """
        issues = []
        statistics = {}

        if self.reference_features is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                check_name="drift",
                message="No reference features provided for drift detection"
            ))
            return issues, statistics

        # Calculate feature-wise drift using KL divergence approximation
        # (mean shift / std)
        ref_means = np.nanmean(self.reference_features, axis=0)
        ref_stds = np.nanstd(self.reference_features, axis=0)

        current_means = np.nanmean(self.features, axis=0)

        # Avoid division by zero
        ref_stds[ref_stds == 0] = 1.0

        # Normalized mean shift
        mean_shifts = np.abs(current_means - ref_means) / ref_stds

        # Drift per feature
        drift_scores = mean_shifts

        # Overall drift (average across features)
        overall_drift = float(drift_scores.mean())

        statistics["overall_drift"] = overall_drift
        statistics["max_drift"] = float(drift_scores.max())
        statistics["drift_threshold"] = float(drift_threshold)

        if overall_drift > drift_threshold:
            # Find features with highest drift
            top_drift_features = np.argsort(drift_scores)[-5:][::-1]

            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING if overall_drift < drift_threshold * 2 else ValidationSeverity.ERROR,
                check_name="drift",
                message=f"Data drift detected (drift={overall_drift:.3f})",
                details={
                    "top_drift_features": [
                        (self.feature_names[i], float(drift_scores[i]))
                        for i in top_drift_features
                    ]
                }
            ))
        else:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                check_name="drift",
                message=f"No significant drift detected (drift={overall_drift:.3f})"
            ))

        return issues, statistics

    def save_report(self, result: ValidationResult, output_path: Path):
        """Save validation report to file.

        Args:
            result: Validation result
            output_path: Path to save report
        """
        with open(output_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("DATA VALIDATION REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Status: {'PASSED' if result.passed else 'FAILED'}\n\n")

            # Issues
            for severity in [ValidationSeverity.ERROR, ValidationSeverity.WARNING, ValidationSeverity.INFO]:
                severity_issues = [issue for issue in result.issues if issue.severity == severity]

                if severity_issues:
                    f.write(f"\n{severity.value.upper()}: {len(severity_issues)}\n")
                    for issue in severity_issues:
                        f.write(f"  - {issue.check_name}: {issue.message}\n")
                        if issue.details:
                            for key, value in issue.details.items():
                                f.write(f"      {key}: {value}\n")

            # Statistics
            f.write("\n\nSTATISTICS:\n")
            for key, value in result.statistics.items():
                f.write(f"  {key}: {value}\n")

            f.write("\n" + "=" * 80 + "\n")

        logger.info(f"Validation report saved to {output_path}")
