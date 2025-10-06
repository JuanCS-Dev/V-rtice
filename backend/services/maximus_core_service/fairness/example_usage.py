"""Example usage of Fairness & Bias Mitigation module for VÉRTICE platform.

This file demonstrates how to use the fairness module for evaluating fairness,
detecting bias, mitigating unfairness, and monitoring fairness over time.
"""

import numpy as np
from typing import Dict, Any

from base import ProtectedAttribute, FairnessMetric
from constraints import FairnessConstraints
from bias_detector import BiasDetector
from mitigation import MitigationEngine
from monitor import FairnessMonitor


# ============================================================================
# DATA GENERATORS
# ============================================================================

def generate_fair_data(n: int = 500) -> tuple:
    """Generate fair dataset (no bias)."""
    np.random.seed(42)

    # Features (not used directly, just for context)
    X = np.random.randn(n, 4)

    # Protected attribute (50/50 split)
    protected_attr = np.random.randint(0, 2, size=n)

    # Labels (independent of protected attribute)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    # Predictions (good model, no bias)
    predictions = (X[:, 0] + X[:, 1] + np.random.randn(n) * 0.1 > 0).astype(float)
    predictions = np.clip(predictions, 0, 1)

    return X, y, protected_attr, predictions


def generate_biased_data(n: int = 500, bias_strength: float = 0.4) -> tuple:
    """Generate biased dataset."""
    np.random.seed(43)

    X = np.random.randn(n, 4)
    protected_attr = np.random.randint(0, 2, size=n)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    # Biased predictions (disadvantage group 1)
    predictions = X[:, 0] + X[:, 1] + np.random.randn(n) * 0.1
    predictions[protected_attr == 1] -= bias_strength  # Add bias

    predictions = 1 / (1 + np.exp(-predictions))  # Sigmoid
    predictions = np.clip(predictions, 0, 1)

    return X, y, protected_attr, predictions


# ============================================================================
# EXAMPLE 1: Basic Fairness Evaluation
# ============================================================================

def example_1_basic_fairness_evaluation():
    """Example 1: Evaluate fairness metrics on a model."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Fairness Evaluation")
    print("=" * 80)

    # Generate test data
    _, y, protected_attr, predictions = generate_fair_data(n=600)

    print(f"\n📊 Dataset:")
    print(f"  Total samples: {len(predictions)}")
    print(f"  Group 0 size: {np.sum(protected_attr == 0)}")
    print(f"  Group 1 size: {np.sum(protected_attr == 1)}")
    print(f"  Positive rate: {np.mean(predictions > 0.5):.2%}")

    # Initialize fairness constraints
    constraints = FairnessConstraints({
        'demographic_parity_threshold': 0.1,
        'equalized_odds_threshold': 0.1,
        'enforcement_mode': 'warn'
    })

    # Evaluate all metrics
    print("\n🔍 Evaluating fairness metrics...")
    results = constraints.evaluate_all_metrics(
        predictions,
        y,
        protected_attr,
        protected_value=1
    )

    print(f"\n✅ Evaluation complete: {len(results)} metrics evaluated\n")

    # Display results
    for metric, result in results.items():
        status = "✅ FAIR" if result.is_fair else "❌ UNFAIR"
        print(f"{metric.value}:")
        print(f"  Status: {status}")
        print(f"  Difference: {result.difference:.3f} (threshold: {result.threshold})")
        print(f"  Ratio: {result.ratio:.3f}")
        print(f"  Group 0: {result.group_0_value:.3f} (n={result.sample_size_0})")
        print(f"  Group 1: {result.group_1_value:.3f} (n={result.sample_size_1})")
        print()

    print("=" * 80 + "\n")


# ============================================================================
# EXAMPLE 2: Bias Detection
# ============================================================================

def example_2_bias_detection():
    """Example 2: Detect bias using statistical tests."""
    print("=" * 80)
    print("EXAMPLE 2: Bias Detection")
    print("=" * 80)

    # Generate biased data
    _, y, protected_attr, predictions = generate_biased_data(n=600, bias_strength=0.5)

    print(f"\n📊 Dataset:")
    print(f"  Total samples: {len(predictions)}")
    print(f"  Group 0 positive rate: {np.mean(predictions[protected_attr == 0] > 0.5):.2%}")
    print(f"  Group 1 positive rate: {np.mean(predictions[protected_attr == 1] > 0.5):.2%}")

    # Initialize bias detector
    detector = BiasDetector({
        'significance_level': 0.05,
        'disparate_impact_threshold': 0.8,
        'sensitivity': 'medium'
    })

    # Run all bias detection methods
    print("\n🔍 Running bias detection tests...")
    bias_results = detector.detect_all_biases(
        predictions,
        protected_attr,
        y,
        protected_value=1
    )

    print(f"\n✅ Detection complete: {len(bias_results)} tests performed\n")

    # Display results
    for method, result in bias_results.items():
        status = "⚠️ BIAS DETECTED" if result.bias_detected else "✅ NO BIAS"
        print(f"{method}:")
        print(f"  Status: {status}")
        print(f"  Severity: {result.severity}")
        print(f"  Confidence: {result.confidence:.2%}")

        if result.p_value is not None:
            print(f"  p-value: {result.p_value:.4f}")
        if result.effect_size is not None:
            print(f"  Effect size: {result.effect_size:.3f}")

        if result.affected_groups:
            print(f"  Affected groups: {result.affected_groups[0]}")

        # Show metadata
        if 'disparate_impact_ratio' in result.metadata:
            print(f"  DI ratio: {result.metadata['disparate_impact_ratio']:.3f}")

        print()

    print("=" * 80 + "\n")


# ============================================================================
# EXAMPLE 3: Bias Mitigation
# ============================================================================

def example_3_bias_mitigation():
    """Example 3: Apply bias mitigation strategy."""
    print("=" * 80)
    print("EXAMPLE 3: Bias Mitigation")
    print("=" * 80)

    # Generate biased data
    _, y, protected_attr, predictions = generate_biased_data(n=600, bias_strength=0.4)

    print(f"\n📊 Dataset (BIASED):")
    print(f"  Total samples: {len(predictions)}")
    print(f"  Group 0 positive rate: {np.mean(predictions[protected_attr == 0] > 0.5):.2%}")
    print(f"  Group 1 positive rate: {np.mean(predictions[protected_attr == 1] > 0.5):.2%}")

    # Initialize mitigation engine
    engine = MitigationEngine({
        'performance_threshold': 0.75,
        'max_performance_loss': 0.05,
        'fairness_improvement_threshold': 0.05
    })

    # Apply threshold optimization
    print("\n🔧 Applying threshold optimization mitigation...")
    result = engine.mitigate_threshold_optimization(
        predictions,
        y,
        protected_attr,
        protected_value=1,
        metric=FairnessMetric.EQUALIZED_ODDS
    )

    print(f"\n✅ Mitigation complete:")
    print(f"  Method: {result.mitigation_method}")
    print(f"  Success: {result.success}")
    print(f"  Threshold Group 0: {result.metadata['threshold_group_0']:.3f}")
    print(f"  Threshold Group 1: {result.metadata['threshold_group_1']:.3f}")

    # Show fairness improvement
    print("\n📊 Fairness Improvement:")
    for key in result.fairness_before.keys():
        if '_difference' in key:
            before = result.fairness_before.get(key, 0)
            after = result.fairness_after.get(key, 0)
            improvement = before - after
            print(f"  {key}: {before:.3f} → {after:.3f} (Δ {improvement:+.3f})")

    # Show performance impact
    print("\n📈 Performance Impact:")
    for metric, impact in result.performance_impact.items():
        print(f"  {metric}: {impact:+.3f}")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# EXAMPLE 4: Continuous Fairness Monitoring
# ============================================================================

def example_4_continuous_monitoring():
    """Example 4: Continuous fairness monitoring with alerts."""
    print("=" * 80)
    print("EXAMPLE 4: Continuous Fairness Monitoring")
    print("=" * 80)

    # Initialize monitor
    monitor = FairnessMonitor({
        'history_max_size': 100,
        'alert_threshold': 'medium',
        'enable_auto_mitigation': False
    })

    print("\n📡 Starting fairness monitoring...")

    # Simulate 20 fair evaluations
    print("\n1️⃣ Phase 1: Fair model (20 evaluations)")
    for i in range(20):
        _, y, protected_attr, predictions = generate_fair_data(n=300)
        monitor.evaluate_fairness(
            predictions,
            y,
            protected_attr,
            protected_value=1,
            model_id='threat_model_v1',
            protected_attr_type=ProtectedAttribute.GEOGRAPHIC_LOCATION
        )

    stats_1 = monitor.get_statistics()
    print(f"  Evaluations: {stats_1['total_evaluations']}")
    print(f"  Violations: {stats_1['total_violations']}")
    print(f"  Violation rate: {stats_1['violation_rate']:.2%}")

    # Simulate 20 biased evaluations
    print("\n2️⃣ Phase 2: Model drift - bias introduced (20 evaluations)")
    for i in range(20):
        _, y, protected_attr, predictions = generate_biased_data(n=300, bias_strength=0.45)
        monitor.evaluate_fairness(
            predictions,
            y,
            protected_attr,
            protected_value=1,
            model_id='threat_model_v1',
            protected_attr_type=ProtectedAttribute.GEOGRAPHIC_LOCATION
        )

    stats_2 = monitor.get_statistics()
    print(f"  Evaluations: {stats_2['total_evaluations']}")
    print(f"  Violations: {stats_2['total_violations']}")
    print(f"  Violation rate: {stats_2['violation_rate']:.2%}")

    # Get alerts
    print("\n⚠️  Fairness Alerts:")
    alerts = monitor.get_alerts(severity='medium', limit=5)
    print(f"  Total alerts: {len(alerts)}")

    for i, alert in enumerate(alerts[:3], 1):
        print(f"\n  Alert {i}:")
        print(f"    Severity: {alert.severity}")
        print(f"    Metric: {alert.metric.value}")
        print(f"    Summary: {alert.violation_details['summary']}")
        print(f"    Action: {alert.recommended_action}")

    # Detect drift
    print("\n🔍 Drift Detection:")
    drift_result = monitor.detect_drift(model_id='threat_model_v1')
    print(f"  Drift detected: {drift_result['drift_detected']}")
    print(f"  Drifted metrics: {drift_result['num_drifted_metrics']}/{drift_result['total_metrics_checked']}")

    if drift_result['drift_detected']:
        for metric, details in drift_result['metrics'].items():
            if details['drift_detected']:
                print(f"\n  {metric}:")
                print(f"    Recent mean: {details['recent_mean']:.3f}")
                print(f"    Older mean: {details['older_mean']:.3f}")
                print(f"    Change: {details['relative_change']:+.1%}")
                print(f"    Direction: {details['direction']}")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# EXAMPLE 5: Auto-Mitigation Workflow
# ============================================================================

def example_5_auto_mitigation():
    """Example 5: Complete workflow with auto-mitigation."""
    print("=" * 80)
    print("EXAMPLE 5: Complete Fairness Workflow (Detect → Mitigate → Verify)")
    print("=" * 80)

    # Step 1: Generate biased data
    _, y, protected_attr, predictions = generate_biased_data(n=500, bias_strength=0.5)

    print(f"\n📊 Step 1: Initial Data (BIASED)")
    print(f"  Samples: {len(predictions)}")
    print(f"  Group 0 positive rate: {np.mean(predictions[protected_attr == 0] > 0.5):.2%}")
    print(f"  Group 1 positive rate: {np.mean(predictions[protected_attr == 1] > 0.5):.2%}")

    # Step 2: Detect bias
    print(f"\n🔍 Step 2: Detect Bias")
    detector = BiasDetector()
    bias_results = detector.detect_all_biases(
        predictions, protected_attr, y, protected_value=1
    )

    bias_count = sum(1 for r in bias_results.values() if r.bias_detected)
    print(f"  Bias detected in {bias_count}/{len(bias_results)} tests")

    # Step 3: Auto-mitigate
    print(f"\n🔧 Step 3: Auto-Mitigation")
    engine = MitigationEngine({
        'mitigation_strategies': [
            'threshold_optimization',
            'calibration_adjustment'
        ]
    })

    mitigation_result = engine.mitigate_auto(
        predictions, y, protected_attr, protected_value=1
    )

    print(f"  Selected strategy: {mitigation_result.mitigation_method}")
    print(f"  Success: {mitigation_result.success}")

    # Step 4: Verify improvement
    print(f"\n✅ Step 4: Verify Improvement")

    # Show before/after for key metrics
    for key in mitigation_result.fairness_before.keys():
        if '_difference' in key:
            before = mitigation_result.fairness_before.get(key, 0)
            after = mitigation_result.fairness_after.get(key, 0)
            improvement = before - after

            metric_name = key.replace('_difference', '')
            status = "✅" if improvement > 0 else "⚠️"

            print(f"  {status} {metric_name}:")
            print(f"     Before: {before:.3f}")
            print(f"     After:  {after:.3f}")
            print(f"     Improvement: {improvement:+.3f}")

    # Performance trade-off
    print(f"\n📈 Performance Trade-off:")
    for metric, impact in mitigation_result.performance_impact.items():
        status = "✅" if impact >= -0.02 else "⚠️"  # < 2% loss is good
        print(f"  {status} {metric}: {impact:+.3f}")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# RUN ALL EXAMPLES
# ============================================================================

def run_all_examples():
    """Run all examples sequentially."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "FAIRNESS & BIAS MITIGATION - EXAMPLE USAGE" + " " * 21 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    example_1_basic_fairness_evaluation()
    example_2_bias_detection()
    example_3_bias_mitigation()
    example_4_continuous_monitoring()
    example_5_auto_mitigation()

    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 27 + "ALL EXAMPLES COMPLETE" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")


if __name__ == "__main__":
    # Run all examples
    run_all_examples()
