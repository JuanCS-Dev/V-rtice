"""Fast Anomaly Detector - <10ms Inference with Isolation Forest

Lightweight ML-based anomaly detection optimized for speed.
Uses pre-trained Isolation Forest for real-time detection.
"""

import logging
import time
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import pickle
from pathlib import Path

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available - anomaly detection disabled")

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Anomaly detection result."""
    is_anomaly: bool
    anomaly_score: float  # -1 to 1 (higher = more anomalous)
    feature_contributions: Dict[str, float]
    detection_time_ms: float


class FastAnomalyDetector:
    """Fast anomaly detection using Isolation Forest.

    Optimized for <10ms inference on 30+ features.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        contamination: float = 0.1,
        n_estimators: int = 100
    ):
        """Initialize fast anomaly detector.

        Args:
            model_path: Path to pre-trained model (optional)
            contamination: Expected proportion of anomalies
            n_estimators: Number of trees in forest
        """
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.trained = False

        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available - detector disabled")
            return

        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            # Initialize untrained model
            self.model = IsolationForest(
                n_estimators=n_estimators,
                contamination=contamination,
                max_samples='auto',
                n_jobs=-1,  # Parallel processing
                random_state=42
            )
            self.scaler = StandardScaler()

        logger.info("FastAnomalyDetector initialized")

    def extract_features(self, event: Dict) -> np.ndarray:
        """Extract feature vector from event.

        Features (30+):
        - Packet size, rate, protocol
        - Process CPU, memory, syscalls
        - File access patterns
        - Network connection stats
        - Temporal features
        """
        features = []

        # Network features (10)
        features.extend([
            event.get('packet_size', 0),
            event.get('packet_rate', 0),
            event.get('protocol_tcp', 0),
            event.get('protocol_udp', 0),
            event.get('src_port', 0),
            event.get('dst_port', 0),
            event.get('connection_duration', 0),
            event.get('bytes_sent', 0),
            event.get('bytes_received', 0),
            event.get('unique_destinations', 0)
        ])

        # Process features (10)
        features.extend([
            event.get('cpu_usage', 0),
            event.get('memory_usage', 0),
            event.get('syscall_count', 0),
            event.get('file_writes', 0),
            event.get('file_reads', 0),
            event.get('network_connections', 0),
            event.get('child_processes', 0),
            event.get('dll_loads', 0),
            event.get('registry_writes', 0),
            event.get('process_uptime', 0)
        ])

        # File features (5)
        features.extend([
            event.get('file_entropy', 0),
            event.get('file_size', 0),
            event.get('is_executable', 0),
            event.get('is_script', 0),
            event.get('file_age_seconds', 0)
        ])

        # Temporal features (5)
        features.extend([
            event.get('hour_of_day', 0),
            event.get('day_of_week', 0),
            event.get('is_weekend', 0),
            event.get('time_since_last_event', 0),
            event.get('event_frequency', 0)
        ])

        return np.array(features, dtype=np.float32)

    def train(self, normal_events: List[Dict]):
        """Train on normal (benign) events.

        Args:
            normal_events: List of normal event dictionaries
        """
        if not SKLEARN_AVAILABLE or not self.model:
            logger.error("Cannot train - scikit-learn unavailable")
            return

        logger.info(f"Training on {len(normal_events)} normal events...")

        # Extract features
        X = np.array([self.extract_features(event) for event in normal_events])

        # Store feature names
        self.feature_names = [
            # Network (10)
            'packet_size', 'packet_rate', 'tcp', 'udp', 'src_port', 'dst_port',
            'conn_duration', 'bytes_sent', 'bytes_recv', 'unique_dests',
            # Process (10)
            'cpu', 'memory', 'syscalls', 'file_writes', 'file_reads',
            'net_conns', 'child_procs', 'dll_loads', 'reg_writes', 'uptime',
            # File (5)
            'file_entropy', 'file_size', 'is_exe', 'is_script', 'file_age',
            # Temporal (5)
            'hour', 'day', 'weekend', 'time_delta', 'frequency'
        ]

        # Fit scaler
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        # Train Isolation Forest
        train_start = time.time()
        self.model.fit(X_scaled)
        train_time = (time.time() - train_start) * 1000

        self.trained = True

        logger.info(f"Training complete in {train_time:.1f}ms")

    def detect(self, event: Dict) -> AnomalyResult:
        """Detect anomaly in single event.

        Args:
            event: Event dictionary with features

        Returns:
            AnomalyResult with detection outcome
        """
        if not SKLEARN_AVAILABLE or not self.model or not self.trained:
            logger.warning("Detector not trained - returning neutral result")
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                feature_contributions={},
                detection_time_ms=0.0
            )

        detect_start = time.time()

        # Extract and scale features
        features = self.extract_features(event).reshape(1, -1)
        features_scaled = self.scaler.transform(features)

        # Predict
        prediction = self.model.predict(features_scaled)[0]  # -1 = anomaly, 1 = normal
        score = self.model.score_samples(features_scaled)[0]  # Lower = more anomalous

        is_anomaly = (prediction == -1)

        # Normalize score to 0-1 (higher = more anomalous)
        anomaly_score = 1.0 / (1.0 + np.exp(score))  # Sigmoid normalization

        # Feature contributions (approximate)
        feature_contributions = self._compute_contributions(features[0])

        detection_time = (time.time() - detect_start) * 1000

        if detection_time > 10:
            logger.warning(f"Detection exceeded 10ms target: {detection_time:.1f}ms")

        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=float(anomaly_score),
            feature_contributions=feature_contributions,
            detection_time_ms=detection_time
        )

    def _compute_contributions(self, features: np.ndarray) -> Dict[str, float]:
        """Compute feature contributions to anomaly score (approximate).

        Args:
            features: Feature vector

        Returns:
            Dictionary mapping feature names to contribution scores
        """
        contributions = {}

        # Simple approach: normalized absolute values
        normalized = np.abs(features) / (np.max(np.abs(features)) + 1e-8)

        for i, name in enumerate(self.feature_names):
            if i < len(normalized):
                contributions[name] = float(normalized[i])

        # Return top 5 contributors
        sorted_contrib = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_contrib[:5])

    def save_model(self, path: str):
        """Save trained model to file."""
        if not self.trained:
            logger.warning("Model not trained - nothing to save")
            return

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'trained': self.trained
        }

        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load trained model from file."""
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)

            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.trained = model_data['trained']

            logger.info(f"Model loaded from {path}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def get_statistics(self) -> Dict:
        """Get detector statistics."""
        return {
            'trained': self.trained,
            'n_features': len(self.feature_names),
            'sklearn_available': SKLEARN_AVAILABLE,
            'model_type': 'IsolationForest' if self.model else None
        }
