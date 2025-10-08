"""Unit tests for XAI (Explainability) module.

Tests all XAI components: LIME, SHAP, Counterfactual, Feature Tracker, Engine.
"""

import numpy as np
import pytest

from .base import DetailLevel, ExplanationCache, ExplanationResult, ExplanationType, FeatureImportance
from .counterfactual import CounterfactualGenerator
from .engine import ExplanationEngine
from .feature_tracker import FeatureImportanceTracker
from .lime_cybersec import CyberSecLIME
from .shap_cybersec import CyberSecSHAP

# ============================================================================
# TEST FIXTURES
# ============================================================================


class DummyThreatClassifier:
    """Dummy threat classifier for testing."""

    def __init__(self):
        # Simple linear classifier: threat_score * 0.8 + anomaly_score * 0.2
        self.coef_ = np.array([0.8, 0.2, 0.1, 0.1])  # coefficients
        self.feature_importances_ = np.array([0.4, 0.3, 0.2, 0.1])  # for tree SHAP

    def predict_proba(self, X):
        """Predict threat probability."""
        # Simple linear combination
        scores = X.dot(self.coef_)
        # Sigmoid to [0, 1]
        proba = 1 / (1 + np.exp(-scores))
        return np.column_stack([1 - proba, proba])

    def predict(self, X):
        """Predict threat label."""
        proba = self.predict_proba(X)
        return (proba[:, 1] > 0.5).astype(int)


@pytest.fixture
def dummy_model():
    """Dummy model fixture."""
    return DummyThreatClassifier()


@pytest.fixture
def sample_instance():
    """Sample cybersecurity instance."""
    return {
        "threat_score": 0.85,
        "anomaly_score": 0.72,
        "src_port": 8080,
        "dst_port": 443,
        "decision_id": "test-decision-001",
    }


@pytest.fixture
def sample_prediction():
    """Sample prediction (high threat)."""
    return 0.89  # High threat probability


# ============================================================================
# TEST BASE CLASSES
# ============================================================================


def test_feature_importance_validation():
    """Test FeatureImportance validation."""
    # Valid feature
    feature = FeatureImportance(
        feature_name="threat_score", importance=0.75, value=0.85, description="Threat score: 0.85", contribution=0.75
    )

    assert feature.feature_name == "threat_score"
    assert feature.importance == 0.75

    # Invalid: empty name
    with pytest.raises(ValueError, match="feature_name is required"):
        FeatureImportance(feature_name="", importance=0.5, value=0.5, description="test", contribution=0.5)

    # Invalid: non-numeric importance
    with pytest.raises(ValueError, match="importance must be a number"):
        FeatureImportance(feature_name="test", importance="invalid", value=0.5, description="test", contribution=0.5)


def test_explanation_result_validation():
    """Test ExplanationResult validation."""
    feature = FeatureImportance(feature_name="test", importance=0.5, value=1.0, description="Test", contribution=0.5)

    # Valid result
    result = ExplanationResult(
        explanation_id="exp-001",
        decision_id="dec-001",
        explanation_type=ExplanationType.LIME,
        detail_level=DetailLevel.DETAILED,
        summary="Test explanation",
        top_features=[feature],
        all_features=[feature],
        confidence=0.85,
    )

    assert result.confidence == 0.85

    # Invalid: confidence out of range
    with pytest.raises(ValueError, match="Confidence must be between"):
        ExplanationResult(
            explanation_id="exp-001",
            decision_id="dec-001",
            explanation_type=ExplanationType.LIME,
            detail_level=DetailLevel.DETAILED,
            summary="Test",
            top_features=[feature],
            all_features=[feature],
            confidence=1.5,  # Invalid
        )


def test_explanation_cache():
    """Test ExplanationCache functionality."""
    cache = ExplanationCache(max_size=2, ttl_seconds=3600)

    feature = FeatureImportance(feature_name="test", importance=0.5, value=1.0, description="Test", contribution=0.5)

    result1 = ExplanationResult(
        explanation_id="exp-001",
        decision_id="dec-001",
        explanation_type=ExplanationType.LIME,
        detail_level=DetailLevel.DETAILED,
        summary="Test 1",
        top_features=[feature],
        all_features=[feature],
        confidence=0.85,
    )

    # Test cache set and get
    cache_key = cache.generate_key("dec-001", ExplanationType.LIME, DetailLevel.DETAILED)
    cache.set(cache_key, result1)

    cached = cache.get(cache_key)
    assert cached is not None
    assert cached.explanation_id == "exp-001"

    # Test cache miss
    miss_key = cache.generate_key("dec-999", ExplanationType.LIME, DetailLevel.DETAILED)
    assert cache.get(miss_key) is None

    # Test eviction
    result2 = ExplanationResult(
        explanation_id="exp-002",
        decision_id="dec-002",
        explanation_type=ExplanationType.SHAP,
        detail_level=DetailLevel.SUMMARY,
        summary="Test 2",
        top_features=[feature],
        all_features=[feature],
        confidence=0.90,
    )

    result3 = ExplanationResult(
        explanation_id="exp-003",
        decision_id="dec-003",
        explanation_type=ExplanationType.COUNTERFACTUAL,
        detail_level=DetailLevel.TECHNICAL,
        summary="Test 3",
        top_features=[feature],
        all_features=[feature],
        confidence=0.75,
    )

    key2 = cache.generate_key("dec-002", ExplanationType.SHAP, DetailLevel.SUMMARY)
    key3 = cache.generate_key("dec-003", ExplanationType.COUNTERFACTUAL, DetailLevel.TECHNICAL)

    cache.set(key2, result2)
    cache.set(key3, result3)  # Should evict oldest (result1)

    # key1 should be evicted
    assert cache.get(cache_key) is None
    # key2 and key3 should still be there
    assert cache.get(key2) is not None
    assert cache.get(key3) is not None


# ============================================================================
# TEST LIME
# ============================================================================


@pytest.mark.asyncio
async def test_lime_basic(dummy_model, sample_instance, sample_prediction):
    """Test basic LIME explanation."""
    lime = CyberSecLIME()

    explanation = await lime.explain(
        model=dummy_model, instance=sample_instance, prediction=sample_prediction, detail_level=DetailLevel.DETAILED
    )

    # Check result structure
    assert explanation.explanation_type == ExplanationType.LIME
    assert explanation.confidence > 0.0
    assert len(explanation.top_features) > 0
    assert explanation.latency_ms > 0

    # Check that threat_score and anomaly_score are in top features (they should be most important)
    feature_names = [f.feature_name for f in explanation.top_features]
    assert "threat_score" in feature_names or "anomaly_score" in feature_names


@pytest.mark.asyncio
async def test_lime_detail_levels(dummy_model, sample_instance, sample_prediction):
    """Test LIME with different detail levels."""
    lime = CyberSecLIME()

    # Summary
    summary_exp = await lime.explain(dummy_model, sample_instance, sample_prediction, DetailLevel.SUMMARY)
    assert len(summary_exp.top_features) == 3

    # Detailed
    detailed_exp = await lime.explain(dummy_model, sample_instance, sample_prediction, DetailLevel.DETAILED)
    assert len(detailed_exp.top_features) == 10 or len(detailed_exp.top_features) == len(sample_instance) - 1

    # Technical
    technical_exp = await lime.explain(dummy_model, sample_instance, sample_prediction, DetailLevel.TECHNICAL)
    assert len(technical_exp.top_features) == len(technical_exp.all_features)


# ============================================================================
# TEST SHAP
# ============================================================================


@pytest.mark.asyncio
async def test_shap_basic(dummy_model, sample_instance, sample_prediction):
    """Test basic SHAP explanation."""
    shap = CyberSecSHAP()

    explanation = await shap.explain(
        model=dummy_model, instance=sample_instance, prediction=sample_prediction, detail_level=DetailLevel.DETAILED
    )

    # Check result structure
    assert explanation.explanation_type == ExplanationType.SHAP
    assert explanation.confidence > 0.0
    assert len(explanation.top_features) > 0
    assert explanation.visualization_data is not None
    assert explanation.visualization_data["type"] == "shap_waterfall"


# ============================================================================
# TEST COUNTERFACTUAL
# ============================================================================


@pytest.mark.asyncio
async def test_counterfactual_basic(dummy_model, sample_instance, sample_prediction):
    """Test basic counterfactual generation."""
    cf_gen = CounterfactualGenerator()

    explanation = await cf_gen.explain(
        model=dummy_model, instance=sample_instance, prediction=sample_prediction, detail_level=DetailLevel.DETAILED
    )

    # Check result structure
    assert explanation.explanation_type == ExplanationType.COUNTERFACTUAL
    assert explanation.counterfactual is not None
    # Counterfactual may or may not be found depending on model behavior
    # Just check it doesn't crash


# ============================================================================
# TEST FEATURE TRACKER
# ============================================================================


def test_feature_tracker():
    """Test feature importance tracker."""
    tracker = FeatureImportanceTracker(max_history=100)

    # Create test features
    features = [
        FeatureImportance(
            feature_name="threat_score", importance=0.75, value=0.85, description="Threat score", contribution=0.75
        ),
        FeatureImportance(
            feature_name="anomaly_score", importance=0.60, value=0.72, description="Anomaly score", contribution=0.60
        ),
    ]

    # Track explanations
    for i in range(10):
        tracker.track_explanation(features)

    # Check statistics
    stats = tracker.get_statistics()
    assert stats["total_explanations"] == 10
    assert stats["num_features_tracked"] == 2

    # Check top features
    top_features = tracker.get_top_features(n=2)
    assert len(top_features) == 2
    assert top_features[0]["feature_name"] == "threat_score"  # Should be top

    # Test drift detection (no drift expected with constant importances)
    drift = tracker.detect_drift("threat_score", window_size=5, threshold=0.2)
    assert drift["drift_detected"] == False


# ============================================================================
# TEST EXPLANATION ENGINE
# ============================================================================


@pytest.mark.asyncio
async def test_engine_basic(dummy_model, sample_instance, sample_prediction):
    """Test ExplanationEngine basic functionality."""
    engine = ExplanationEngine()

    # Test LIME explanation
    lime_exp = await engine.explain(
        model=dummy_model,
        instance=sample_instance,
        prediction=sample_prediction,
        explanation_type=ExplanationType.LIME,
        detail_level=DetailLevel.DETAILED,
    )

    assert lime_exp.explanation_type == ExplanationType.LIME
    assert engine.total_explanations_generated == 1


@pytest.mark.asyncio
async def test_engine_cache(dummy_model, sample_instance, sample_prediction):
    """Test engine caching."""
    engine = ExplanationEngine({"enable_cache": True})

    # First call (cache miss)
    exp1 = await engine.explain(
        dummy_model, sample_instance, sample_prediction, ExplanationType.LIME, DetailLevel.DETAILED
    )

    assert engine.cache_misses == 1
    assert engine.cache_hits == 0

    # Second call with same parameters (cache hit)
    exp2 = await engine.explain(
        dummy_model, sample_instance, sample_prediction, ExplanationType.LIME, DetailLevel.DETAILED
    )

    assert engine.cache_hits == 1

    # Explanations should be identical
    assert exp1.explanation_id == exp2.explanation_id


@pytest.mark.asyncio
async def test_engine_multiple_explanations(dummy_model, sample_instance, sample_prediction):
    """Test generating multiple explanation types."""
    engine = ExplanationEngine()

    explanations = await engine.explain_multiple(
        model=dummy_model,
        instance=sample_instance,
        prediction=sample_prediction,
        explanation_types=[ExplanationType.LIME, ExplanationType.SHAP],
        detail_level=DetailLevel.DETAILED,
    )

    assert len(explanations) == 2
    assert ExplanationType.LIME in explanations
    assert ExplanationType.SHAP in explanations


@pytest.mark.asyncio
async def test_engine_health_check():
    """Test engine health check."""
    engine = ExplanationEngine()

    health = await engine.health_check()

    assert "status" in health
    assert "explainers" in health


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_lime_performance(dummy_model, sample_instance, sample_prediction):
    """Test LIME performance (<2s requirement)."""
    lime = CyberSecLIME({"num_samples": 1000})  # Reduced for faster test

    explanation = await lime.explain(dummy_model, sample_instance, sample_prediction, DetailLevel.DETAILED)

    # Should be under 2 seconds (2000ms)
    assert explanation.latency_ms < 2000, f"LIME too slow: {explanation.latency_ms}ms"


@pytest.mark.asyncio
async def test_shap_performance(dummy_model, sample_instance, sample_prediction):
    """Test SHAP performance (<2s requirement)."""
    shap = CyberSecSHAP()

    explanation = await shap.explain(dummy_model, sample_instance, sample_prediction, DetailLevel.DETAILED)

    # Should be under 2 seconds (2000ms)
    assert explanation.latency_ms < 2000, f"SHAP too slow: {explanation.latency_ms}ms"


# ============================================================================
# INTEGRATION TEST
# ============================================================================


@pytest.mark.asyncio
async def test_full_xai_workflow(dummy_model, sample_instance, sample_prediction):
    """Test complete XAI workflow."""
    # Initialize engine
    engine = ExplanationEngine({"enable_cache": True, "enable_tracking": True})

    # Generate explanations
    lime_exp = await engine.explain(
        dummy_model, sample_instance, sample_prediction, ExplanationType.LIME, DetailLevel.DETAILED
    )

    shap_exp = await engine.explain(
        dummy_model, sample_instance, sample_prediction, ExplanationType.SHAP, DetailLevel.DETAILED
    )

    # Check statistics
    stats = engine.get_statistics()
    assert stats["total_explanations"] == 2

    # Check top features (should be tracked)
    top_features = engine.get_top_features(n=5)
    assert len(top_features) > 0

    # Check drift (should be none with only 2 explanations)
    drift = engine.detect_drift()
    assert drift["drift_detected"] == False


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
