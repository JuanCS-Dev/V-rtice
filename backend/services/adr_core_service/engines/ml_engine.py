"""Machine Learning Engine for the ADR Core Service.

This module contains the `MLEngine`, which provides machine learning capabilities
for threat detection and classification. It includes models for anomaly
detection and threat classification, along with feature extraction and
training functionalities.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List
import time
import pickle
import os

logger = logging.getLogger(__name__)


class MLEngine:
    """Provides ML-based threat detection and classification.

    This engine uses scikit-learn models for anomaly detection (Isolation Forest)
    and threat classification (Random Forest). It handles feature extraction,
    model training, and inference.

    Attributes:
        config (Dict[str, Any]): Configuration for the engine.
        enabled (bool): Whether the engine is active.
        models_dir (str): Directory to save/load trained models.
        anomaly_detector: The Isolation Forest model for anomaly detection.
        threat_classifier: The Random Forest model for threat classification.
        scaler: A StandardScaler for feature normalization.
        anomaly_detector_trained (bool): True if the anomaly model is trained.
        threat_classifier_trained (bool): True if the classification model is trained.
        stats (Dict[str, Any]): A dictionary for tracking engine statistics.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initializes the MLEngine.

        Args:
            config (Dict[str, Any]): A configuration dictionary, including
                `models_dir` to specify where to store trained models.
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.models_dir = config.get('models_dir', '/tmp/adr_models')
        os.makedirs(self.models_dir, exist_ok=True)

        self.anomaly_detector = None
        self.threat_classifier = None
        self.scaler = None
        self.anomaly_detector_trained = False
        self.threat_classifier_trained = False

        try:
            from sklearn.ensemble import IsolationForest, RandomForestClassifier
            from sklearn.preprocessing import StandardScaler

            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.threat_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            self._load_models()

        except ImportError:
            logger.warning("scikit-learn not found, ML features will be disabled.")
            self.enabled = False

        self.stats = {
            'total_inferences': 0,
            'anomalies_detected': 0,
            'threats_classified': 0,
            'avg_inference_time_ms': 0,
        }
        logger.info(f"ML Engine initialized (enabled: {self.enabled}).")

    async def detect_anomaly(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Detects anomalies in a feature set using the Isolation Forest model.

        Args:
            features (Dict[str, Any]): A dictionary of features for analysis.

        Returns:
            Dict[str, Any]: A dictionary containing the anomaly detection result,
                including a boolean `is_anomaly` and an `anomaly_score`.
        """
        if not self.enabled or not self.anomaly_detector_trained:
            return {'is_anomaly': False, 'error': 'Anomaly detector not available or not trained.'}

        start_time = time.time()
        try:
            feature_vector = self._extract_features(features).reshape(1, -1)
            scaled_vector = self.scaler.transform(feature_vector)
            
            prediction = self.anomaly_detector.predict(scaled_vector)
            score = self.anomaly_detector.decision_function(scaled_vector)

            is_anomaly = prediction[0] == -1
            if is_anomaly:
                self.stats['anomalies_detected'] += 1

            self._update_inference_stats(time.time() - start_time)

            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': float(score[0]),
                'model_trained': self.anomaly_detector_trained
            }
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {'is_anomaly': False, 'error': str(e)}

    async def classify_threat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Classifies a threat based on its features using the Random Forest model.

        Args:
            data (Dict[str, Any]): The threat data to classify.

        Returns:
            Dict[str, Any]: A dictionary containing the classification result,
                including the `threat_type` and `confidence`.
        """
        if not self.enabled or not self.threat_classifier_trained:
            return {'threat_type': 'unknown', 'error': 'Classifier not available or not trained.'}

        start_time = time.time()
        try:
            feature_vector = self._extract_features(data).reshape(1, -1)
            scaled_vector = self.scaler.transform(feature_vector)

            prediction = self.threat_classifier.predict(scaled_vector)
            probabilities = self.threat_classifier.predict_proba(scaled_vector)
            
            threat_type = self.threat_types.get(prediction[0], 'unknown')
            confidence = float(max(probabilities[0]))

            if threat_type != 'benign':
                self.stats['threats_classified'] += 1

            self._update_inference_stats(time.time() - start_time)

            return {
                'threat_type': threat_type,
                'confidence': confidence,
                'is_malicious': threat_type != 'benign',
                'model_trained': self.threat_classifier_trained
            }
        except Exception as e:
            logger.error(f"Threat classification failed: {e}")
            return {'threat_type': 'unknown', 'error': str(e)}

    def _extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extracts and orders a numerical feature vector from raw data."""
        # This is a simplified feature extraction. A real implementation would be
        # more complex and handle categorical data properly.
        feature_keys = sorted([k for k, v in data.items() if isinstance(v, (int, float))])
        features = [data[key] for key in feature_keys]
        return np.array(features, dtype=np.float64)

    def _update_inference_stats(self, duration_s: float):
        """Updates the inference time statistics."""
        self.stats['total_inferences'] += 1
        total_inferences = self.stats['total_inferences']
        current_avg_time = self.stats['avg_inference_time_ms']
        duration_ms = duration_s * 1000
        self.stats['avg_inference_time_ms'] = \
            (current_avg_time * (total_inferences - 1) + duration_ms) / total_inferences

    def _save_model(self, model, filename: str):
        """Saves a trained model to disk using pickle."""
        if not self.enabled:
            return
        path = os.path.join(self.models_dir, filename)
        try:
            with open(path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save model to {path}: {e}")

    def _load_models(self):
        """Loads trained models from disk if they exist."""
        if not self.enabled:
            return
        # Load anomaly detector
        anomaly_path = os.path.join(self.models_dir, 'anomaly_detector.pkl')
        if os.path.exists(anomaly_path):
            with open(anomaly_path, 'rb') as f:
                self.anomaly_detector = pickle.load(f)
                self.anomaly_detector_trained = True
                logger.info("Loaded pre-trained anomaly detector model.")
        # Load threat classifier
        classifier_path = os.path.join(self.models_dir, 'threat_classifier.pkl')
        if os.path.exists(classifier_path):
            with open(classifier_path, 'rb') as f:
                self.threat_classifier = pickle.load(f)
                self.threat_classifier_trained = True
                logger.info("Loaded pre-trained threat classifier model.")
        # Load scaler
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
                logger.info("Loaded pre-trained feature scaler.")

    def get_stats(self) -> Dict[str, Any]:
        """Returns a copy of the current engine statistics.

        Returns:
            Dict[str, Any]: A dictionary containing engine performance metrics.
        """
        return self.stats.copy()