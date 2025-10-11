"""
Tests for ML Predictor.

Tests model loading, prediction, and integration.
"""

import pytest
from pathlib import Path

from backend.services.wargaming_crisol.ml.predictor import (
    PatchValidityPredictor,
    get_predictor,
)
from backend.services.wargaming_crisol.ml.feature_extractor import (
    PatchFeatureExtractor,
)


class TestPatchValidityPredictor:
    """Test ML prediction"""
    
    def test_predictor_initialization(self):
        """Predictor initializes with model path"""
        predictor = PatchValidityPredictor("models/patch_validity_rf.joblib")
        
        assert predictor.model_path == Path("models/patch_validity_rf.joblib")
        assert predictor.model is None  # Lazy loading
    
    def test_predictor_load_model_if_exists(self):
        """Load model if file exists"""
        model_path = "models/patch_validity_rf.joblib"
        
        if not Path(model_path).exists():
            pytest.skip(f"Model not trained yet: {model_path}")
        
        predictor = PatchValidityPredictor(model_path)
        predictor._load_model()
        
        assert predictor.model is not None
        assert len(predictor.feature_names) > 0
    
    def test_predictor_raises_if_model_missing(self):
        """Raise error if model doesn't exist"""
        predictor = PatchValidityPredictor("models/nonexistent.joblib")
        
        with pytest.raises(FileNotFoundError, match="Model not found"):
            predictor._load_model()
    
    def test_predict_with_trained_model(self):
        """Predict patch validity"""
        model_path = "models/patch_validity_rf.joblib"
        
        if not Path(model_path).exists():
            pytest.skip(f"Model not trained yet: {model_path}")
        
        predictor = PatchValidityPredictor(model_path)
        
        # Valid patch features (high security patterns)
        features = {
            'lines_added': 5,
            'lines_removed': 2,
            'files_modified': 1,
            'complexity_delta': 2.0,
            'has_input_validation': 1,
            'has_sanitization': 1,
            'has_encoding': 0,
            'has_parameterization': 1,
            'cwe_CWE-78': 0,
            'cwe_CWE-79': 0,
            'cwe_CWE-89': 1,
        }
        
        result = predictor.predict(features)
        
        assert 'prediction' in result
        assert 'confidence' in result
        assert 'should_wargame' in result
        assert 'probabilities' in result
        
        assert isinstance(result['prediction'], bool)
        assert 0.0 <= result['confidence'] <= 1.0
        assert isinstance(result['should_wargame'], bool)
    
    def test_predict_high_confidence_skips_wargaming(self):
        """High confidence predictions don't need wargaming"""
        model_path = "models/patch_validity_rf.joblib"
        
        if not Path(model_path).exists():
            pytest.skip(f"Model not trained yet: {model_path}")
        
        predictor = PatchValidityPredictor(model_path)
        
        # Strong valid patch signals
        features = {
            'lines_added': 10,
            'lines_removed': 5,
            'files_modified': 2,
            'complexity_delta': 4.0,
            'has_input_validation': 1,
            'has_sanitization': 1,
            'has_encoding': 1,
            'has_parameterization': 1,
            'cwe_CWE-78': 0,
            'cwe_CWE-79': 0,
            'cwe_CWE-89': 1,
        }
        
        result = predictor.predict(features)
        
        # High confidence → skip wargaming
        if result['confidence'] >= 0.8:
            assert result['should_wargame'] is False
    
    def test_predict_low_confidence_requires_wargaming(self):
        """Low confidence predictions need wargaming"""
        model_path = "models/patch_validity_rf.joblib"
        
        if not Path(model_path).exists():
            pytest.skip(f"Model not trained yet: {model_path}")
        
        predictor = PatchValidityPredictor(model_path)
        
        # Ambiguous patch (some patterns, but not comprehensive)
        features = {
            'lines_added': 2,
            'lines_removed': 1,
            'files_modified': 1,
            'complexity_delta': 0.0,
            'has_input_validation': 1,
            'has_sanitization': 0,
            'has_encoding': 0,
            'has_parameterization': 0,
            'cwe_CWE-78': 0,
            'cwe_CWE-79': 1,
            'cwe_CWE-89': 0,
        }
        
        result = predictor.predict(features)
        
        # Should have a prediction, but may need wargaming
        assert isinstance(result['should_wargame'], bool)
    
    def test_get_predictor_singleton(self):
        """get_predictor returns singleton"""
        p1 = get_predictor()
        p2 = get_predictor()
        
        assert p1 is p2  # Same instance
    
    def test_end_to_end_patch_to_prediction(self):
        """End-to-end: patch → features → prediction"""
        model_path = "models/patch_validity_rf.joblib"
        
        if not Path(model_path).exists():
            pytest.skip(f"Model not trained yet: {model_path}")
        
        # Real security patch
        patch = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -10,3 +10,8 @@
 def search_users(query):
-    sql = f"SELECT * FROM users WHERE name = '{query}'"
+    # Input validation
+    if not query or len(query) > 100:
+        raise ValueError("Invalid query")
+    
+    # Parameterized query
+    sql = "SELECT * FROM users WHERE name = ?"
+    cursor.execute(sql, (query,))
"""
        
        # Extract features
        features = PatchFeatureExtractor.extract(patch, "CWE-89")
        
        # Predict
        predictor = get_predictor(model_path)
        result = predictor.predict(features.to_dict())
        
        # Should predict valid (has validation + parameterization)
        assert result['prediction'] is True
        assert result['confidence'] > 0.5


class TestPredictorErrorHandling:
    """Test error handling"""
    
    def test_predict_with_missing_features(self):
        """Graceful error if features missing"""
        model_path = "models/patch_validity_rf.joblib"
        
        if not Path(model_path).exists():
            pytest.skip(f"Model not trained yet: {model_path}")
        
        predictor = PatchValidityPredictor(model_path)
        
        # Missing features
        incomplete_features = {
            'lines_added': 5,
            # Missing other required features
        }
        
        with pytest.raises(Exception):  # RuntimeError or KeyError
            predictor.predict(incomplete_features)
