"""
ML-based Patch Validity Predictor.

Predicts whether a patch will pass wargaming validation without running exploits.
Uses trained Random Forest classifier.

NO MOCK - Real scikit-learn model.
PRODUCTION-READY - Model loading, inference, error handling.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PatchValidityPredictor:
    """
    ML-based patch validity prediction.
    
    Loads trained Random Forest model and predicts patch validity
    from extracted features.
    
    Biological analogy: Like T-cell memory recognizing known pathogens,
    this model recognizes patterns of valid/invalid patches.
    """
    
    def __init__(self, model_path: str = "models/patch_validity_rf.joblib"):
        """
        Initialize predictor with trained model.
        
        Args:
            model_path: Path to saved scikit-learn model
            
        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        self.model_path = Path(model_path)
        self.model: Optional[Any] = None
        self.feature_names: list = []
        
        # Lazy loading - model loaded on first predict()
        logger.info(f"PatchValidityPredictor initialized (model: {model_path})")
    
    def _load_model(self) -> None:
        """
        Load model from disk (lazy loading).
        
        Raises:
            FileNotFoundError: If model doesn't exist
            ImportError: If joblib not available
        """
        if self.model is not None:
            return  # Already loaded
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}. "
                f"Train model first using scripts/ml/train.py"
            )
        
        try:
            import joblib
            self.model = joblib.load(self.model_path)
            self.feature_names = list(self.model.feature_names_in_)
            logger.info(f"✅ Model loaded: {self.model_path}")
        except ImportError:
            raise ImportError("joblib not installed. Install: pip install joblib scikit-learn")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict patch validity from features.
        
        Args:
            features: Dict with keys matching training features
                     (output of PatchFeatureExtractor.to_dict())
            
        Returns:
            {
                'prediction': bool (True = valid patch),
                'confidence': float (0-1, max probability),
                'should_wargame': bool (True if confidence <0.8),
                'probabilities': [prob_invalid, prob_valid]
            }
            
        Raises:
            RuntimeError: If model not loaded or prediction fails
            
        Example:
            >>> predictor = PatchValidityPredictor()
            >>> features = {'lines_added': 10, 'has_validation': 1, ...}
            >>> result = predictor.predict(features)
            >>> result['prediction']
            True
            >>> result['confidence']
            0.92
        """
        # Lazy load model
        if self.model is None:
            self._load_model()
        
        try:
            import numpy as np
            
            # Convert features dict to numpy array (matching training order)
            X = np.array([features[feat] for feat in self.feature_names]).reshape(1, -1)
            
            # Predict
            prediction = bool(self.model.predict(X)[0])
            probabilities = self.model.predict_proba(X)[0].tolist()
            confidence = float(max(probabilities))
            
            # Decision: run wargaming if confidence < 0.8
            should_wargame = confidence < 0.8
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'should_wargame': should_wargame,
                'probabilities': probabilities,
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError(f"Prediction error: {e}")


# Global singleton
_predictor: Optional[PatchValidityPredictor] = None


def get_predictor(model_path: str = "models/patch_validity_rf.joblib") -> PatchValidityPredictor:
    """
    Get singleton predictor instance.
    
    Args:
        model_path: Path to model (only used on first call)
        
    Returns:
        PatchValidityPredictor instance
        
    Example:
        >>> predictor = get_predictor()
        >>> result = predictor.predict(features)
    """
    global _predictor
    
    if _predictor is None:
        _predictor = PatchValidityPredictor(model_path)
    
    return _predictor
