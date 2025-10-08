"""Example usage of XAI (Explainability) module for VÉRTICE platform.

This file demonstrates how to use the XAI module for explaining cybersecurity
model predictions using LIME, SHAP, and counterfactual explanations.
"""

import asyncio

import numpy as np

from .base import DetailLevel, ExplanationType
from .counterfactual import CounterfactualGenerator
from .engine import ExplanationEngine
from .lime_cybersec import CyberSecLIME
from .shap_cybersec import CyberSecSHAP

# ============================================================================
# EXAMPLE 1: Basic LIME Explanation
# ============================================================================


async def example_1_basic_lime():
    """Example 1: Basic LIME explanation for threat detection."""
    print("=" * 80)
    print("EXAMPLE 1: Basic LIME Explanation")
    print("=" * 80)

    # Create a dummy threat classifier
    class SimpleThreatClassifier:
        """Simple threat classifier for demonstration."""

        def predict_proba(self, X):
            # Simple rule: high threat if threat_score > 0.7 or anomaly_score > 0.8
            threat_scores = X[:, 0]  # First column is threat_score
            anomaly_scores = X[:, 1]  # Second column is anomaly_score

            # Combine scores
            combined = threat_scores * 0.7 + anomaly_scores * 0.3
            threat_proba = 1 / (1 + np.exp(-5 * (combined - 0.6)))  # Sigmoid

            return np.column_stack([1 - threat_proba, threat_proba])

    model = SimpleThreatClassifier()

    # Cybersecurity instance
    instance = {
        "threat_score": 0.85,
        "anomaly_score": 0.72,
        "src_port": 8080,
        "dst_port": 443,
        "packet_size": 1500,
        "request_rate": 120,
        "decision_id": "example-001",
    }

    # Get prediction
    # Convert instance to array (feature order matters!)
    feature_order = ["threat_score", "anomaly_score", "src_port", "dst_port", "packet_size", "request_rate"]
    instance_array = np.array([[instance[f] for f in feature_order]])
    prediction = model.predict_proba(instance_array)[0][1]

    print(f"\n📊 Instance: {instance}")
    print(f"🎯 Prediction: {prediction:.2f} (threat probability)")

    # Initialize LIME
    lime = CyberSecLIME({"num_samples": 1000})

    # Generate explanation
    print("\n🔍 Generating LIME explanation...")
    explanation = await lime.explain(
        model=model, instance=instance, prediction=prediction, detail_level=DetailLevel.DETAILED
    )

    print(f"\n✅ Explanation generated in {explanation.latency_ms}ms")
    print(f"📝 Summary: {explanation.summary}")
    print(f"🎯 Confidence: {explanation.confidence:.2f}")
    print("\n🔝 Top 5 Features:")

    for i, feature in enumerate(explanation.top_features[:5], 1):
        print(f"  {i}. {feature.feature_name}: {feature.importance:+.3f} (value: {feature.value})")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# EXAMPLE 2: SHAP Explanation
# ============================================================================


async def example_2_shap_explanation():
    """Example 2: SHAP explanation with waterfall visualization."""
    print("=" * 80)
    print("EXAMPLE 2: SHAP Explanation (Waterfall)")
    print("=" * 80)

    # Use same model from Example 1
    class SimpleThreatClassifier:
        def predict_proba(self, X):
            threat_scores = X[:, 0]
            anomaly_scores = X[:, 1]
            combined = threat_scores * 0.7 + anomaly_scores * 0.3
            threat_proba = 1 / (1 + np.exp(-5 * (combined - 0.6)))
            return np.column_stack([1 - threat_proba, threat_proba])

    model = SimpleThreatClassifier()

    instance = {
        "threat_score": 0.85,
        "anomaly_score": 0.72,
        "src_port": 8080,
        "dst_port": 443,
        "decision_id": "example-002",
    }

    feature_order = ["threat_score", "anomaly_score", "src_port", "dst_port"]
    instance_array = np.array([[instance[f] for f in feature_order]])
    prediction = model.predict_proba(instance_array)[0][1]

    print(f"\n📊 Instance: {instance}")
    print(f"🎯 Prediction: {prediction:.2f}")

    # Initialize SHAP
    shap = CyberSecSHAP({"algorithm": "kernel"})

    # Generate explanation
    print("\n🔍 Generating SHAP explanation...")
    explanation = await shap.explain(
        model=model, instance=instance, prediction=prediction, detail_level=DetailLevel.DETAILED
    )

    print(f"\n✅ Explanation generated in {explanation.latency_ms}ms")
    print(f"📝 Summary: {explanation.summary}")

    # Display waterfall data
    if explanation.visualization_data:
        waterfall = explanation.visualization_data["waterfall_data"]
        base_value = explanation.visualization_data["base_value"]

        print(f"\n📊 SHAP Waterfall (base value: {base_value:.3f}):")
        print(f"  {'Feature':<20} {'SHAP Value':>12} {'Cumulative':>12}")
        print(f"  {'-' * 20} {'-' * 12} {'-' * 12}")

        for item in waterfall[:5]:
            print(f"  {item['feature']:<20} {item['shap_value']:>+12.4f} {item['cumulative_after']:>12.4f}")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# EXAMPLE 3: Counterfactual Explanation
# ============================================================================


async def example_3_counterfactual():
    """Example 3: Counterfactual explanation for alternative scenarios."""
    print("=" * 80)
    print("EXAMPLE 3: Counterfactual Explanation")
    print("=" * 80)

    class SimpleThreatClassifier:
        def predict_proba(self, X):
            threat_scores = X[:, 0]
            anomaly_scores = X[:, 1]
            combined = threat_scores * 0.7 + anomaly_scores * 0.3
            threat_proba = 1 / (1 + np.exp(-5 * (combined - 0.6)))
            return np.column_stack([1 - threat_proba, threat_proba])

    model = SimpleThreatClassifier()

    # High threat instance
    instance = {
        "threat_score": 0.95,  # Very high
        "anomaly_score": 0.88,  # Very high
        "src_port": 1337,
        "dst_port": 22,
        "decision_id": "example-003",
    }

    feature_order = ["threat_score", "anomaly_score", "src_port", "dst_port"]
    instance_array = np.array([[instance[f] for f in feature_order]])
    prediction = model.predict_proba(instance_array)[0][1]

    print(f"\n📊 Original Instance: {instance}")
    print(f"🎯 Original Prediction: {prediction:.2f} (HIGH THREAT)")

    # Initialize Counterfactual Generator
    cf_gen = CounterfactualGenerator({"num_candidates": 20, "max_iterations": 500})

    # Generate counterfactual
    print("\n🔍 Generating counterfactual explanation...")
    print("   Finding minimal changes to flip prediction to LOW THREAT...")

    explanation = await cf_gen.explain(
        model=model, instance=instance, prediction=prediction, detail_level=DetailLevel.DETAILED
    )

    print(f"\n✅ Counterfactual generated in {explanation.latency_ms}ms")
    print(f"🎯 Confidence: {explanation.confidence:.2f}")
    print("\n💡 Counterfactual Scenario:")
    print(f"   {explanation.counterfactual}")

    if explanation.metadata.get("num_changes", 0) > 0:
        print("\n📋 Required Changes:")
        for i, feature in enumerate(explanation.top_features, 1):
            print(f"  {i}. {feature.description}")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# EXAMPLE 4: Using Explanation Engine (Unified Interface)
# ============================================================================


async def example_4_explanation_engine():
    """Example 4: Using ExplanationEngine for unified XAI."""
    print("=" * 80)
    print("EXAMPLE 4: Explanation Engine (Unified Interface)")
    print("=" * 80)

    class SimpleThreatClassifier:
        def predict_proba(self, X):
            threat_scores = X[:, 0]
            anomaly_scores = X[:, 1]
            combined = threat_scores * 0.7 + anomaly_scores * 0.3
            threat_proba = 1 / (1 + np.exp(-5 * (combined - 0.6)))
            return np.column_stack([1 - threat_proba, threat_proba])

    model = SimpleThreatClassifier()

    instance = {
        "threat_score": 0.78,
        "anomaly_score": 0.65,
        "src_port": 8080,
        "dst_port": 443,
        "decision_id": "example-004",
    }

    feature_order = ["threat_score", "anomaly_score", "src_port", "dst_port"]
    instance_array = np.array([[instance[f] for f in feature_order]])
    prediction = model.predict_proba(instance_array)[0][1]

    print(f"\n📊 Instance: {instance}")
    print(f"🎯 Prediction: {prediction:.2f}")

    # Initialize Explanation Engine
    engine = ExplanationEngine({"enable_cache": True, "enable_tracking": True, "default_explanation_type": "lime"})

    print("\n🔍 Generating multiple explanation types in parallel...")

    # Generate multiple explanations
    explanations = await engine.explain_multiple(
        model=model,
        instance=instance,
        prediction=prediction,
        explanation_types=[ExplanationType.LIME, ExplanationType.SHAP],
        detail_level=DetailLevel.SUMMARY,
    )

    print(f"\n✅ Generated {len(explanations)} explanations")

    for exp_type, explanation in explanations.items():
        print(f"\n📝 {exp_type.value.upper()}:")
        print(f"   {explanation.summary}")
        print(f"   Latency: {explanation.latency_ms}ms, Confidence: {explanation.confidence:.2f}")

    # Get engine statistics
    print("\n📊 Engine Statistics:")
    stats = engine.get_statistics()
    print(f"   Total explanations: {stats['total_explanations']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate']:.1%}")

    # Get top features (tracked across all explanations)
    if engine.tracker:
        top_features = engine.get_top_features(n=3)
        print("\n🔝 Top Features (across all explanations):")
        for i, feature in enumerate(top_features, 1):
            print(f"   {i}. {feature['feature_name']}: mean={feature['mean_importance']:.3f}, trend={feature['trend']}")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# EXAMPLE 5: Feature Drift Detection
# ============================================================================


async def example_5_feature_drift():
    """Example 5: Detecting feature importance drift over time."""
    print("=" * 80)
    print("EXAMPLE 5: Feature Importance Drift Detection")
    print("=" * 80)

    class SimpleThreatClassifier:
        def __init__(self, threat_weight=0.7):
            self.threat_weight = threat_weight

        def predict_proba(self, X):
            threat_scores = X[:, 0]
            anomaly_scores = X[:, 1]
            combined = threat_scores * self.threat_weight + anomaly_scores * (1 - self.threat_weight)
            threat_proba = 1 / (1 + np.exp(-5 * (combined - 0.6)))
            return np.column_stack([1 - threat_proba, threat_proba])

    # Initialize engine
    engine = ExplanationEngine({"enable_tracking": True})

    print("\n🔄 Simulating 100 explanations with stable model...")

    # Generate 100 explanations with stable model
    model_stable = SimpleThreatClassifier(threat_weight=0.7)

    for i in range(100):
        instance = {
            "threat_score": np.random.uniform(0.5, 1.0),
            "anomaly_score": np.random.uniform(0.5, 1.0),
            "src_port": int(np.random.uniform(1024, 65535)),
            "dst_port": 443,
        }

        feature_order = ["threat_score", "anomaly_score", "src_port", "dst_port"]
        instance_array = np.array([[instance[f] for f in feature_order]])
        prediction = model_stable.predict_proba(instance_array)[0][1]

        await engine.explain(
            model_stable,
            instance,
            prediction,
            ExplanationType.LIME,
            DetailLevel.SUMMARY,
            use_cache=False,  # Disable cache for this simulation
        )

    print("✅ Generated 100 baseline explanations")

    # Check drift (should be none)
    drift_result_baseline = engine.detect_drift(feature_name="threat_score", window_size=50, threshold=0.2)

    print("\n📊 Baseline Drift Check (threat_score):")
    print(f"   Drift detected: {drift_result_baseline['drift_detected']}")

    # Now simulate model change (drift)
    print("\n🔄 Simulating 100 explanations with CHANGED model (drift)...")

    model_drifted = SimpleThreatClassifier(threat_weight=0.4)  # Changed importance!

    for i in range(100):
        instance = {
            "threat_score": np.random.uniform(0.5, 1.0),
            "anomaly_score": np.random.uniform(0.5, 1.0),
            "src_port": int(np.random.uniform(1024, 65535)),
            "dst_port": 443,
        }

        feature_order = ["threat_score", "anomaly_score", "src_port", "dst_port"]
        instance_array = np.array([[instance[f] for f in feature_order]])
        prediction = model_drifted.predict_proba(instance_array)[0][1]

        await engine.explain(
            model_drifted, instance, prediction, ExplanationType.LIME, DetailLevel.SUMMARY, use_cache=False
        )

    print("✅ Generated 100 drifted explanations")

    # Check drift again (should detect change)
    drift_result_drifted = engine.detect_drift(feature_name="threat_score", window_size=50, threshold=0.2)

    print("\n📊 After Model Change (threat_score):")
    print(f"   Drift detected: {drift_result_drifted['drift_detected']}")

    if drift_result_drifted["drift_detected"]:
        print("   ⚠️  DRIFT ALERT!")
        print(f"   Direction: {drift_result_drifted['direction']}")
        print(f"   Relative change: {drift_result_drifted['relative_change']:.1%}")
        print(f"   Severity: {drift_result_drifted['severity']}")

    # Global drift check
    print("\n🌍 Global Drift Check (all top features):")
    global_drift = engine.detect_drift()

    print(f"   Drift detected: {global_drift['drift_detected']}")
    print(f"   Drifted features: {global_drift['num_drifted_features']}/{global_drift['total_features_checked']}")
    print(f"   Severity: {global_drift['severity']}")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# RUN ALL EXAMPLES
# ============================================================================


async def run_all_examples():
    """Run all examples sequentially."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "XAI MODULE - EXAMPLE USAGE" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    await example_1_basic_lime()
    await example_2_shap_explanation()
    await example_3_counterfactual()
    await example_4_explanation_engine()
    await example_5_feature_drift()

    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "ALL EXAMPLES COMPLETE" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())
