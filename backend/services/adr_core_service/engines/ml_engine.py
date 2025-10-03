"""
ML Engine - Machine Learning for threat detection and classification
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import pickle
import os

logger = logging.getLogger(__name__)


class MLEngine:
    """
    Machine Learning Engine for ADR

    Features:
    - Anomaly detection (Isolation Forest)
    - Threat classification (Random Forest)
    - Behavioral analysis
    - Feature extraction
    - Model training and inference
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.models_dir = config.get('models_dir', '/tmp/adr_models')

        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)

        # REAL ML Models
        try:
            from sklearn.ensemble import IsolationForest, RandomForestClassifier
            from sklearn.preprocessing import StandardScaler

            # Anomaly Detection: Isolation Forest
            self.anomaly_detector = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                max_features=1.0
            )

            # Threat Classification: Random Forest
            self.threat_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )

            # Feature scaler
            self.scaler = StandardScaler()

            # Model states
            self.anomaly_detector_trained = False
            self.threat_classifier_trained = False

            # Load pre-trained models if available
            self._load_models()

        except ImportError:
            logger.warning("scikit-learn not available, ML features disabled")
            self.anomaly_detector = None
            self.threat_classifier = None
            self.scaler = None
            self.enabled = False

        # Behavioral baseline (for unsupervised learning)
        self.baseline_data = []
        self.max_baseline_samples = 1000

        # Threat type mapping
        self.threat_types = {
            0: 'benign',
            1: 'malware',
            2: 'exploit',
            3: 'phishing',
            4: 'ddos',
            5: 'data_exfiltration',
            6: 'privilege_escalation',
            7: 'lateral_movement'
        }

        # Statistics
        self.stats = {
            'total_inferences': 0,
            'anomalies_detected': 0,
            'threats_classified': 0,
            'avg_inference_time_ms': 0,
            'total_inference_time_ms': 0,
            'baseline_samples': 0,
            'models_trained': False
        }

        logger.info(f"Initialized ML Engine (enabled={self.enabled})")

    async def detect_anomaly(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect anomalies using Isolation Forest ML model

        Args:
            features: Feature vector for analysis

        Returns:
            Anomaly detection result with score and confidence
        """
        start_time = time.time()

        try:
            if not self.enabled or self.anomaly_detector is None:
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.0,
                    'error': 'ML engine disabled or not available'
                }

            # Feature extraction
            feature_vector = self._extract_features(features)

            if feature_vector is None or len(feature_vector) == 0:
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.0,
                    'error': 'Failed to extract features'
                }

            # Add to baseline for training if not trained yet
            if not self.anomaly_detector_trained:
                self.baseline_data.append(feature_vector)
                self.stats['baseline_samples'] = len(self.baseline_data)

                # Auto-train when we have enough samples
                if len(self.baseline_data) >= 50:
                    await self.train_anomaly_detector(self.baseline_data)

            # Reshape for prediction (sklearn expects 2D array)
            feature_vector_2d = feature_vector.reshape(1, -1)

            # Scale features
            if self.anomaly_detector_trained and hasattr(self, 'scaler_fitted') and self.scaler_fitted:
                feature_vector_2d = self.scaler.transform(feature_vector_2d)

            # Predict: -1 for anomaly, 1 for normal
            prediction = self.anomaly_detector.predict(feature_vector_2d)
            is_anomaly = prediction[0] == -1

            # Anomaly score (decision function - higher = more normal, lower = more anomalous)
            anomaly_score_raw = self.anomaly_detector.decision_function(feature_vector_2d)[0]

            # Normalize score to 0-1 range (0 = normal, 1 = highly anomalous)
            # Typical range is [-0.5, 0.5], but can vary
            anomaly_score = max(0.0, min(1.0, 0.5 - anomaly_score_raw))

            # Confidence based on how far from decision boundary
            confidence = min(1.0, abs(anomaly_score_raw) * 2)

            result = {
                'is_anomaly': is_anomaly,
                'anomaly_score': round(anomaly_score, 3),
                'confidence': round(confidence, 3),
                'raw_score': round(anomaly_score_raw, 3),
                'features_used': list(features.keys()),
                'feature_count': len(feature_vector),
                'model_trained': self.anomaly_detector_trained,
                'baseline_samples': len(self.baseline_data)
            }

            if is_anomaly:
                self.stats['anomalies_detected'] += 1

            self.stats['total_inferences'] += 1

            # Update timing stats
            inference_time_ms = (time.time() - start_time) * 1000
            self.stats['total_inference_time_ms'] += inference_time_ms
            self.stats['avg_inference_time_ms'] = (
                self.stats['total_inference_time_ms'] / self.stats['total_inferences']
            )

            return result

        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return {'is_anomaly': False, 'anomaly_score': 0.0, 'error': str(e)}

    async def classify_threat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify threat using Random Forest ML model

        Args:
            data: Threat data to classify

        Returns:
            Classification result with probabilities
        """
        start_time = time.time()

        try:
            if not self.enabled or self.threat_classifier is None:
                return {
                    'threat_type': 'unknown',
                    'confidence': 0.0,
                    'is_malicious': False,
                    'error': 'ML engine disabled or not available'
                }

            # Extract features
            feature_vector = self._extract_features(data)

            if feature_vector is None or len(feature_vector) == 0:
                return {
                    'threat_type': 'unknown',
                    'confidence': 0.0,
                    'is_malicious': False,
                    'error': 'Failed to extract features'
                }

            if not self.threat_classifier_trained:
                # Use heuristic classification until model is trained
                return self._heuristic_classification(data, feature_vector)

            # Reshape for prediction
            feature_vector_2d = feature_vector.reshape(1, -1)

            # Scale features if scaler is fitted
            if hasattr(self, 'scaler_fitted') and self.scaler_fitted:
                feature_vector_2d = self.scaler.transform(feature_vector_2d)

            # Predict class
            prediction = self.threat_classifier.predict(feature_vector_2d)[0]
            threat_type = self.threat_types.get(prediction, 'unknown')

            # Get prediction probabilities
            probabilities = self.threat_classifier.predict_proba(feature_vector_2d)[0]
            confidence = float(max(probabilities))

            # Get top 3 threat types by probability
            top_3_indices = np.argsort(probabilities)[-3:][::-1]
            top_threats = [
                {
                    'type': self.threat_types.get(idx, 'unknown'),
                    'probability': round(float(probabilities[idx]), 3)
                }
                for idx in top_3_indices
            ]

            is_malicious = threat_type != 'benign' and confidence > 0.5

            result = {
                'threat_type': threat_type,
                'confidence': round(confidence, 3),
                'is_malicious': is_malicious,
                'top_threats': top_threats,
                'features_used': list(data.keys()),
                'feature_count': len(feature_vector),
                'model': 'random_forest_classifier_v1',
                'model_trained': self.threat_classifier_trained
            }

            if is_malicious:
                self.stats['threats_classified'] += 1

            self.stats['total_inferences'] += 1

            # Update timing
            inference_time_ms = (time.time() - start_time) * 1000
            self.stats['total_inference_time_ms'] += inference_time_ms
            self.stats['avg_inference_time_ms'] = (
                self.stats['total_inference_time_ms'] / self.stats['total_inferences']
            )

            return result

        except Exception as e:
            logger.error(f"Threat classification error: {e}")
            return {'threat_type': 'unknown', 'confidence': 0.0, 'error': str(e)}

    def _extract_features(self, data: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Extract feature vector from threat data

        Features extracted:
        - Network: ports, protocols, packet sizes, connection counts
        - Process: CPU, memory, file operations, registry access
        - Behavioral: API calls, syscalls, network activity patterns
        - Content: entropy, file signatures, string patterns
        """
        try:
            features = []

            # NETWORK FEATURES (10 features)
            features.append(float(data.get('source_port', 0)))
            features.append(float(data.get('dest_port', 0)))
            features.append(float(data.get('packet_size', 0)))
            features.append(float(data.get('packet_count', 0)))
            features.append(float(data.get('bytes_sent', 0)))
            features.append(float(data.get('bytes_received', 0)))
            features.append(float(data.get('connection_duration', 0)))
            features.append(float(data.get('protocol', 0)))  # TCP=6, UDP=17, etc
            features.append(float(data.get('syn_count', 0)))
            features.append(float(data.get('failed_connections', 0)))

            # PROCESS FEATURES (8 features)
            features.append(float(data.get('cpu_usage', 0)))
            features.append(float(data.get('memory_usage', 0)))
            features.append(float(data.get('thread_count', 0)))
            features.append(float(data.get('handle_count', 0)))
            features.append(float(data.get('file_operations', 0)))
            features.append(float(data.get('registry_operations', 0)))
            features.append(float(data.get('process_creation_count', 0)))
            features.append(float(data.get('dll_load_count', 0)))

            # BEHAVIORAL FEATURES (7 features)
            features.append(float(data.get('api_call_count', 0)))
            features.append(float(data.get('syscall_count', 0)))
            features.append(float(data.get('suspicious_api_calls', 0)))
            features.append(float(data.get('network_connections', 0)))
            features.append(float(data.get('dns_queries', 0)))
            features.append(float(data.get('http_requests', 0)))
            features.append(float(data.get('file_modifications', 0)))

            # CONTENT FEATURES (5 features)
            features.append(float(data.get('entropy', 0)))  # File/data entropy
            features.append(float(data.get('string_count', 0)))
            features.append(float(data.get('suspicious_strings', 0)))
            features.append(float(data.get('pe_sections', 0)))  # PE file sections
            features.append(float(data.get('embedded_files', 0)))

            # TEMPORAL FEATURES (5 features)
            features.append(float(data.get('events_per_second', 0)))
            features.append(float(data.get('burst_activity', 0)))
            features.append(float(data.get('time_since_start', 0)))
            features.append(float(data.get('activity_variance', 0)))
            features.append(float(data.get('periodic_behavior', 0)))

            # Convert to numpy array
            feature_array = np.array(features, dtype=np.float64)

            # Handle NaN and inf values
            feature_array = np.nan_to_num(feature_array, nan=0.0, posinf=0.0, neginf=0.0)

            return feature_array

        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None

    def _heuristic_classification(self, data: Dict[str, Any], features: np.ndarray) -> Dict[str, Any]:
        """
        Rule-based classification when ML model is not trained
        """
        threat_type = 'benign'
        confidence = 0.5
        indicators = []

        # Check for malware indicators
        if data.get('suspicious_api_calls', 0) > 10:
            threat_type = 'malware'
            confidence = 0.7
            indicators.append('High suspicious API calls')

        # Check for exploit indicators
        if data.get('buffer_overflow_detected', False) or data.get('shellcode_detected', False):
            threat_type = 'exploit'
            confidence = 0.8
            indicators.append('Buffer overflow or shellcode detected')

        # Check for phishing indicators
        if data.get('suspicious_url', False) or data.get('credential_theft', False):
            threat_type = 'phishing'
            confidence = 0.75
            indicators.append('Suspicious URL or credential theft')

        # Check for DDoS indicators
        if data.get('packet_count', 0) > 1000 and data.get('connection_duration', 0) < 1:
            threat_type = 'ddos'
            confidence = 0.65
            indicators.append('High packet rate with short duration')

        # Check for data exfiltration
        if data.get('bytes_sent', 0) > 1000000:  # > 1MB sent
            threat_type = 'data_exfiltration'
            confidence = 0.6
            indicators.append('Large data transfer detected')

        return {
            'threat_type': threat_type,
            'confidence': confidence,
            'is_malicious': threat_type != 'benign',
            'method': 'heuristic_rules',
            'indicators': indicators,
            'model_trained': False
        }

    async def train_anomaly_detector(self, training_data: List[np.ndarray]) -> Dict[str, Any]:
        """
        Train Isolation Forest on baseline data
        """
        try:
            if not self.enabled or self.anomaly_detector is None:
                return {'success': False, 'error': 'ML engine disabled'}

            # Convert list to 2D array
            X_train = np.array(training_data)

            # Fit scaler
            X_train_scaled = self.scaler.fit_transform(X_train)
            self.scaler_fitted = True

            # Train Isolation Forest
            self.anomaly_detector.fit(X_train_scaled)
            self.anomaly_detector_trained = True
            self.stats['models_trained'] = True

            # Save model
            self._save_model(self.anomaly_detector, 'anomaly_detector.pkl')
            self._save_model(self.scaler, 'scaler.pkl')

            logger.info(f"Trained anomaly detector on {len(training_data)} samples")

            return {
                'success': True,
                'samples': len(training_data),
                'features': X_train.shape[1] if len(X_train.shape) > 1 else 0,
                'model': 'isolation_forest'
            }

        except Exception as e:
            logger.error(f"Training error: {e}")
            return {'success': False, 'error': str(e)}

    async def train_threat_classifier(self, X: List[np.ndarray], y: List[int]) -> Dict[str, Any]:
        """
        Train Random Forest classifier on labeled threat data

        Args:
            X: Feature vectors
            y: Labels (threat types as integers 0-7)
        """
        try:
            if not self.enabled or self.threat_classifier is None:
                return {'success': False, 'error': 'ML engine disabled'}

            # Convert to arrays
            X_train = np.array(X)
            y_train = np.array(y)

            if len(X_train) < 10:
                return {'success': False, 'error': 'Need at least 10 samples to train'}

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            self.scaler_fitted = True

            # Train classifier
            self.threat_classifier.fit(X_train_scaled, y_train)
            self.threat_classifier_trained = True
            self.stats['models_trained'] = True

            # Save model
            self._save_model(self.threat_classifier, 'threat_classifier.pkl')

            # Calculate accuracy (simple train accuracy)
            train_accuracy = self.threat_classifier.score(X_train_scaled, y_train)

            logger.info(f"Trained threat classifier on {len(X_train)} samples")

            return {
                'success': True,
                'samples': len(X_train),
                'features': X_train.shape[1],
                'classes': len(np.unique(y_train)),
                'train_accuracy': round(train_accuracy, 3),
                'model': 'random_forest'
            }

        except Exception as e:
            logger.error(f"Training error: {e}")
            return {'success': False, 'error': str(e)}

    def _save_model(self, model, filename: str):
        """Save model to disk"""
        try:
            filepath = os.path.join(self.models_dir, filename)
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Saved model to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            # Load anomaly detector
            anomaly_path = os.path.join(self.models_dir, 'anomaly_detector.pkl')
            if os.path.exists(anomaly_path):
                with open(anomaly_path, 'rb') as f:
                    self.anomaly_detector = pickle.load(f)
                    self.anomaly_detector_trained = True
                    logger.info("Loaded pre-trained anomaly detector")

            # Load threat classifier
            classifier_path = os.path.join(self.models_dir, 'threat_classifier.pkl')
            if os.path.exists(classifier_path):
                with open(classifier_path, 'rb') as f:
                    self.threat_classifier = pickle.load(f)
                    self.threat_classifier_trained = True
                    logger.info("Loaded pre-trained threat classifier")

            # Load scaler
            scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                    self.scaler_fitted = True
                    logger.info("Loaded pre-trained scaler")

            if self.anomaly_detector_trained or self.threat_classifier_trained:
                self.stats['models_trained'] = True

        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get ML engine statistics"""
        stats = self.stats.copy()
        stats.update({
            'anomaly_detector_trained': self.anomaly_detector_trained,
            'threat_classifier_trained': self.threat_classifier_trained,
            'scaler_fitted': hasattr(self, 'scaler_fitted') and self.scaler_fitted
        })
        return stats
