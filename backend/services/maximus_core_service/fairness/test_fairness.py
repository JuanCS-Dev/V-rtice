"""Comprehensive Test Suite for Fairness Module.

Tests all fairness components:
- Base classes and data structures
- Fairness constraints evaluation
- Bias detection methods
- Mitigation strategies
- Continuous monitoring

Target Metrics:
- Fairness violations: <1%
- Bias detection accuracy: >95%
- False positive rate: <5%
"""

import numpy as np
import pytest
from base import (
    BiasDetectionResult,
    FairnessMetric,
    FairnessResult,
    FairnessViolationException,
    InsufficientDataException,
    ProtectedAttribute,
)
from bias_detector import BiasDetector
from constraints import FairnessConstraints
from mitigation import MitigationEngine
from monitor import FairnessAlert, FairnessMonitor, FairnessSnapshot

# ============================================================================
# Test Data Generators
# ============================================================================


def generate_fair_data(n: int = 1000) -> tuple:
    """Generate fair dataset (no bias)."""
    np.random.seed(42)

    # Features
    X = np.random.randn(n, 4)

    # Protected attribute (50/50 split)
    protected_attr = np.random.binint(0, 2, size=n)

    # Labels (independent of protected attribute)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    # Predictions (good model, no bias)
    predictions = (X[:, 0] + X[:, 1] + np.random.randn(n) * 0.1 > 0).astype(float)
    predictions = np.clip(predictions, 0, 1)

    return X, y, protected_attr, predictions


def generate_biased_data(n: int = 1000, bias_strength: float = 0.3) -> tuple:
    """Generate biased dataset."""
    np.random.seed(42)

    # Features
    X = np.random.randn(n, 4)

    # Protected attribute
    protected_attr = np.random.binint(0, 2, size=n)

    # Labels (independent of protected attribute)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    # Biased predictions (disadvantage group 1)
    predictions = X[:, 0] + X[:, 1] + np.random.randn(n) * 0.1

    # Add bias: reduce scores for protected group
    predictions[protected_attr == 1] -= bias_strength

    predictions = 1 / (1 + np.exp(-predictions))  # Sigmoid
    predictions = np.clip(predictions, 0, 1)

    return X, y, protected_attr, predictions


# ============================================================================
# Base Classes Tests
# ============================================================================


def test_protected_attribute_enum():
    """Test ProtectedAttribute enum."""
    assert ProtectedAttribute.GEOGRAPHIC_LOCATION.value == "geographic_location"
    assert ProtectedAttribute.ORGANIZATION_SIZE.value == "organization_size"
    assert ProtectedAttribute.INDUSTRY_VERTICAL.value == "industry_vertical"
    assert len(list(ProtectedAttribute)) == 3


def test_fairness_metric_enum():
    """Test FairnessMetric enum."""
    assert FairnessMetric.DEMOGRAPHIC_PARITY.value == "demographic_parity"
    assert FairnessMetric.EQUALIZED_ODDS.value == "equalized_odds"
    assert len(list(FairnessMetric)) == 6


def test_fairness_result_validation():
    """Test FairnessResult validation."""
    # Valid result
    result = FairnessResult(
        metric=FairnessMetric.DEMOGRAPHIC_PARITY,
        protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
        group_0_value=0.5,
        group_1_value=0.6,
        difference=0.1,
        ratio=0.833,
        is_fair=True,
        threshold=0.1,
        sample_size_0=500,
        sample_size_1=500,
    )
    assert result.difference == 0.1

    # Invalid group_0_value (out of range)
    with pytest.raises(ValueError, match="group_0_value must be in"):
        FairnessResult(
            metric=FairnessMetric.DEMOGRAPHIC_PARITY,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            group_0_value=1.5,  # Invalid
            group_1_value=0.6,
            difference=0.1,
            ratio=0.833,
            is_fair=True,
            threshold=0.1,
        )


def test_fairness_result_disparity_percentage():
    """Test disparity percentage calculation."""
    result = FairnessResult(
        metric=FairnessMetric.DEMOGRAPHIC_PARITY,
        protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
        group_0_value=0.5,
        group_1_value=0.4,
        difference=0.1,
        ratio=0.8,
        is_fair=True,
        threshold=0.1,
    )

    disparity_pct = result.get_disparity_percentage()
    assert disparity_pct == pytest.approx(20.0, rel=0.01)  # 0.1/0.5 * 100 = 20%


def test_bias_detection_result_validation():
    """Test BiasDetectionResult validation."""
    # Valid result
    result = BiasDetectionResult(
        bias_detected=True,
        protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
        detection_method="chi_square",
        p_value=0.01,
        effect_size=0.3,
        confidence=0.99,
        severity="medium",
    )
    assert result.bias_detected is True

    # Invalid p_value
    with pytest.raises(ValueError, match="p_value must be in"):
        BiasDetectionResult(
            bias_detected=True,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="chi_square",
            p_value=1.5,  # Invalid
            confidence=0.99,
            severity="medium",
        )


# ============================================================================
# Fairness Constraints Tests
# ============================================================================


def test_demographic_parity_fair():
    """Test demographic parity on fair data."""
    _, _, protected_attr, predictions = generate_fair_data(n=500)

    constraints = FairnessConstraints({"demographic_parity_threshold": 0.1})
    result = constraints.evaluate_demographic_parity(predictions, protected_attr, protected_value=1)

    assert result.is_fair is True
    assert result.difference <= 0.1
    assert result.metric == FairnessMetric.DEMOGRAPHIC_PARITY


def test_demographic_parity_unfair():
    """Test demographic parity on biased data."""
    _, _, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.5)

    constraints = FairnessConstraints({"demographic_parity_threshold": 0.1})
    result = constraints.evaluate_demographic_parity(predictions, protected_attr, protected_value=1)

    assert result.is_fair is False
    assert result.difference > 0.1


def test_equalized_odds():
    """Test equalized odds metric."""
    _, y, protected_attr, predictions = generate_fair_data(n=500)

    constraints = FairnessConstraints({"equalized_odds_threshold": 0.1})
    result = constraints.evaluate_equalized_odds(predictions, y, protected_attr, protected_value=1)

    assert result.metric == FairnessMetric.EQUALIZED_ODDS
    assert "tpr_0" in result.metadata
    assert "fpr_0" in result.metadata


def test_equal_opportunity():
    """Test equal opportunity metric."""
    _, y, protected_attr, predictions = generate_fair_data(n=500)

    constraints = FairnessConstraints({"equal_opportunity_threshold": 0.1})
    result = constraints.evaluate_equal_opportunity(predictions, y, protected_attr, protected_value=1)

    assert result.metric == FairnessMetric.EQUAL_OPPORTUNITY
    # TPR values should be similar for fair data
    assert abs(result.group_0_value - result.group_1_value) <= 0.15


def test_calibration():
    """Test calibration metric."""
    _, y, protected_attr, predictions = generate_fair_data(n=500)

    constraints = FairnessConstraints({"calibration_threshold": 0.1})
    result = constraints.evaluate_calibration(predictions, y, protected_attr, protected_value=1, num_bins=10)

    assert result.metric == FairnessMetric.CALIBRATION
    # Calibration errors should be low for fair data
    assert result.group_0_value < 0.2
    assert result.group_1_value < 0.2


def test_insufficient_data_exception():
    """Test insufficient data handling."""
    # Very small dataset
    predictions = np.array([0.5, 0.6, 0.7])
    protected_attr = np.array([0, 1, 0])

    constraints = FairnessConstraints({"min_sample_size": 30})

    with pytest.raises(InsufficientDataException):
        constraints.evaluate_demographic_parity(predictions, protected_attr, protected_value=1)


def test_fairness_violation_exception():
    """Test fairness violation exception in reject mode."""
    _, _, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.5)

    constraints = FairnessConstraints({"demographic_parity_threshold": 0.1, "enforcement_mode": "reject"})

    with pytest.raises(FairnessViolationException):
        constraints.evaluate_demographic_parity(predictions, protected_attr, protected_value=1)


# ============================================================================
# Bias Detector Tests
# ============================================================================


def test_statistical_parity_bias_fair():
    """Test statistical parity on fair data."""
    _, _, protected_attr, predictions = generate_fair_data(n=500)

    detector = BiasDetector({"significance_level": 0.05})
    result = detector.detect_statistical_parity_bias(predictions, protected_attr, protected_value=1)

    # Should not detect bias in fair data
    assert result.bias_detected is False or result.severity == "low"
    assert result.p_value is not None


def test_statistical_parity_bias_unfair():
    """Test statistical parity on biased data."""
    _, _, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.5)

    detector = BiasDetector({"significance_level": 0.05})
    result = detector.detect_statistical_parity_bias(predictions, protected_attr, protected_value=1)

    # Should detect bias in biased data
    assert result.bias_detected is True
    assert result.p_value < 0.05
    assert result.severity in ["medium", "high", "critical"]


def test_disparate_impact_4_5ths():
    """Test disparate impact (4/5ths rule)."""
    _, _, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.5)

    detector = BiasDetector({"disparate_impact_threshold": 0.8})
    result = detector.detect_disparate_impact(predictions, protected_attr, protected_value=1)

    assert result.detection_method == "disparate_impact_4_5ths_rule"
    assert "disparate_impact_ratio" in result.metadata

    # Biased data should violate 4/5ths rule
    assert result.bias_detected is True


def test_distribution_bias():
    """Test distribution comparison (KS test)."""
    _, _, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.4)

    detector = BiasDetector({"significance_level": 0.05})
    result = detector.detect_distribution_bias(predictions, protected_attr, protected_value=1)

    assert result.detection_method == "distribution_ks_test"
    assert "ks_statistic" in result.metadata
    assert "cohens_d" in result.metadata


def test_performance_disparity():
    """Test performance disparity detection."""
    _, y, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.3)

    detector = BiasDetector({"sensitivity": "medium"})
    result = detector.detect_performance_disparity(predictions, y, protected_attr, protected_value=1)

    assert result.detection_method == "performance_disparity"
    assert "accuracy_group_0" in result.metadata
    assert "accuracy_group_1" in result.metadata
    assert "f1_group_0" in result.metadata


def test_detect_all_biases():
    """Test running all bias detection methods."""
    _, y, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.4)

    detector = BiasDetector()
    results = detector.detect_all_biases(predictions, protected_attr, y, protected_value=1)

    # Should have results for all methods
    assert "statistical_parity" in results
    assert "disparate_impact" in results
    assert "distribution" in results
    assert "performance_disparity" in results

    # At least some should detect bias
    bias_detected_count = sum(1 for r in results.values() if r.bias_detected)
    assert bias_detected_count >= 2


# ============================================================================
# Mitigation Engine Tests
# ============================================================================


def test_threshold_optimization():
    """Test threshold optimization mitigation."""
    _, y, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.3)

    engine = MitigationEngine({"performance_threshold": 0.7, "max_performance_loss": 0.1})

    result = engine.mitigate_threshold_optimization(predictions, y, protected_attr, protected_value=1)

    assert result.mitigation_method == "threshold_optimization"
    assert "threshold_group_0" in result.metadata
    assert "threshold_group_1" in result.metadata
    assert result.fairness_before is not None
    assert result.fairness_after is not None


def test_calibration_adjustment():
    """Test calibration adjustment mitigation."""
    _, y, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.25)

    engine = MitigationEngine()
    result = engine.mitigate_calibration_adjustment(predictions, y, protected_attr, protected_value=1)

    assert result.mitigation_method == "calibration_adjustment"
    assert result.performance_impact is not None
    # Should improve fairness
    assert len(result.fairness_after) > 0


def test_auto_mitigation():
    """Test automatic mitigation strategy selection."""
    _, y, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.3)

    engine = MitigationEngine({"mitigation_strategies": ["threshold_optimization", "calibration_adjustment"]})

    result = engine.mitigate_auto(predictions, y, protected_attr, protected_value=1)

    # Should select one strategy
    assert result.mitigation_method in ["threshold_optimization", "calibration_adjustment"]


# ============================================================================
# Fairness Monitor Tests
# ============================================================================


def test_fairness_monitor_evaluation():
    """Test fairness monitoring evaluation."""
    _, y, protected_attr, predictions = generate_fair_data(n=300)

    monitor = FairnessMonitor({"history_max_size": 100, "alert_threshold": "medium"})

    snapshot = monitor.evaluate_fairness(
        predictions,
        y,
        protected_attr,
        protected_value=1,
        model_id="test_model_1",
        protected_attr_type=ProtectedAttribute.GEOGRAPHIC_LOCATION,
    )

    assert isinstance(snapshot, FairnessSnapshot)
    assert snapshot.model_id == "test_model_1"
    assert len(snapshot.fairness_results) > 0
    assert len(snapshot.bias_results) > 0
    assert len(monitor.history) == 1


def test_fairness_monitor_alerts():
    """Test alert generation on violations."""
    _, y, protected_attr, predictions = generate_biased_data(n=300, bias_strength=0.5)

    monitor = FairnessMonitor(
        {
            "alert_threshold": "low",  # Alert on any violation
            "enable_auto_mitigation": False,
        }
    )

    snapshot = monitor.evaluate_fairness(
        predictions,
        y,
        protected_attr,
        protected_value=1,
        model_id="biased_model",
        protected_attr_type=ProtectedAttribute.GEOGRAPHIC_LOCATION,
    )

    # Should generate alerts for biased data
    alerts = monitor.get_alerts(limit=10)
    assert len(alerts) > 0
    assert all(isinstance(a, FairnessAlert) for a in alerts)


def test_fairness_trends():
    """Test fairness trends analysis."""
    monitor = FairnessMonitor({"history_max_size": 1000})

    # Generate multiple snapshots
    for i in range(50):
        _, y, protected_attr, predictions = generate_fair_data(n=200)
        monitor.evaluate_fairness(
            predictions,
            y,
            protected_attr,
            protected_value=1,
            model_id="trend_model",
            protected_attr_type=ProtectedAttribute.GEOGRAPHIC_LOCATION,
        )

    trends = monitor.get_fairness_trends(model_id="trend_model", lookback_hours=24)

    assert "trends" in trends
    assert trends["num_snapshots"] == 50


def test_drift_detection():
    """Test drift detection in fairness metrics."""
    monitor = FairnessMonitor({"drift_window_size": 20, "drift_threshold": 0.15})

    # Generate stable period
    for i in range(40):
        _, y, protected_attr, predictions = generate_fair_data(n=200)
        monitor.evaluate_fairness(predictions, y, protected_attr, protected_value=1, model_id="drift_model")

    # Generate drifted period (introduce bias)
    for i in range(40):
        _, y, protected_attr, predictions = generate_biased_data(n=200, bias_strength=0.4)
        monitor.evaluate_fairness(predictions, y, protected_attr, protected_value=1, model_id="drift_model")

    drift_result = monitor.detect_drift(model_id="drift_model")

    # Should detect drift
    assert drift_result["drift_detected"] is True
    assert drift_result["num_drifted_metrics"] > 0


def test_monitor_statistics():
    """Test monitor statistics."""
    monitor = FairnessMonitor()

    # Run some evaluations
    for i in range(10):
        _, y, protected_attr, predictions = generate_fair_data(n=200)
        monitor.evaluate_fairness(predictions, y, protected_attr, protected_value=1, model_id=f"model_{i}")

    stats = monitor.get_statistics()

    assert stats["total_evaluations"] == 10
    assert stats["snapshots_in_history"] == 10
    assert "violation_rate" in stats


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_fairness_workflow():
    """Test complete fairness workflow: detect -> mitigate -> monitor."""
    # 1. Generate biased data
    _, y, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.4)

    # 2. Detect bias
    detector = BiasDetector()
    bias_results = detector.detect_all_biases(predictions, protected_attr, y, protected_value=1)

    assert any(r.bias_detected for r in bias_results.values())

    # 3. Mitigate
    engine = MitigationEngine()
    mitigation_result = engine.mitigate_auto(predictions, y, protected_attr, protected_value=1)

    assert mitigation_result is not None

    # 4. Monitor
    monitor = FairnessMonitor()
    snapshot = monitor.evaluate_fairness(predictions, y, protected_attr, protected_value=1, model_id="integrated_test")

    assert len(monitor.history) == 1


def test_violation_rate_target():
    """Test that violation rate is <1% on fair data (target metric)."""
    monitor = FairnessMonitor({"alert_threshold": "medium"})

    # Run 100 evaluations on fair data
    for i in range(100):
        _, y, protected_attr, predictions = generate_fair_data(n=300)
        monitor.evaluate_fairness(predictions, y, protected_attr, protected_value=1, model_id="fair_model")

    stats = monitor.get_statistics()
    violation_rate = stats["violation_rate"]

    # Target: <1% violations on fair data
    assert violation_rate < 0.01, f"Violation rate {violation_rate:.2%} exceeds 1% target"


def test_bias_detection_accuracy():
    """Test bias detection accuracy >95% (target metric)."""
    detector = BiasDetector({"significance_level": 0.05})

    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0

    # Test on 50 fair datasets
    for i in range(50):
        _, _, protected_attr, predictions = generate_fair_data(n=300)
        result = detector.detect_statistical_parity_bias(predictions, protected_attr, protected_value=1)

        if result.bias_detected:
            false_positives += 1
        else:
            true_negatives += 1

    # Test on 50 biased datasets
    for i in range(50):
        _, _, protected_attr, predictions = generate_biased_data(n=300, bias_strength=0.4)
        result = detector.detect_statistical_parity_bias(predictions, protected_attr, protected_value=1)

        if result.bias_detected:
            true_positives += 1
        else:
            false_negatives += 1

    accuracy = (true_positives + true_negatives) / 100
    fpr = false_positives / 50 if (false_positives + true_negatives) > 0 else 0

    # Target: >95% accuracy
    assert accuracy > 0.95, f"Detection accuracy {accuracy:.1%} below 95% target"

    # Target: <5% false positive rate
    assert fpr < 0.05, f"False positive rate {fpr:.1%} exceeds 5% target"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
