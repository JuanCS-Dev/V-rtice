"""
Machine Learning module for Wargaming Crisol.

Provides:
- Feature extraction from patches
- Patch validity prediction (ML-based)
- Model training infrastructure
"""

from .feature_extractor import PatchFeatures, PatchFeatureExtractor
from .predictor import PatchValidityPredictor, get_predictor

__all__ = [
    'PatchFeatures',
    'PatchFeatureExtractor',
    'PatchValidityPredictor',
    'get_predictor',
]
