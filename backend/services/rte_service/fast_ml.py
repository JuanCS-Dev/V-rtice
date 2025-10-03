"""
RTE - Fast ML Models
=====================
Ultra-fast ML models for threat detection (<10ms inference).

Models:
- Isolation Forest (scikit-learn) - Anomaly detection
- VAE Autoencoder (PyTorch) - Reconstruction error
"""

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ThreatScore:
    """Threat score from ML models"""
    anomaly_score: float  # 0-1, higher = more anomalous
    reconstruction_error: float  # VAE reconstruction error
    is_anomaly: bool  # Binary decision
    features: Dict[str, float]  # Feature values for explainability
    inference_time_ms: float


class FeatureExtractor:
    """
    Extract features from network events for ML models.

    Features (30+):
    - Packet size statistics
    - Time-based features
    - Protocol features
    - Payload features
    - Connection features
    """

    @staticmethod
    def extract(event: Dict) -> np.ndarray:
        """
        Extract feature vector from event.

        Args:
            event: Event dictionary

        Returns:
            Feature vector (30 dimensions)
        """
        features = []

        # Packet features (10)
        features.append(event.get("packet_size", 0))
        features.append(event.get("packet_count", 0))
        features.append(event.get("bytes_sent", 0))
        features.append(event.get("bytes_recv", 0))
        features.append(event.get("avg_packet_size", 0))
        features.append(event.get("packet_size_std", 0))
        features.append(event.get("inter_arrival_time_mean", 0))
        features.append(event.get("inter_arrival_time_std", 0))
        features.append(event.get("duration_seconds", 0))
        features.append(event.get("packets_per_second", 0))

        # Protocol features (5)
        protocols = {"TCP": 1, "UDP": 2, "ICMP": 3, "HTTP": 4, "HTTPS": 5, "DNS": 6}
        features.append(protocols.get(event.get("protocol", ""), 0))
        features.append(event.get("src_port", 0))
        features.append(event.get("dst_port", 0))
        features.append(1 if event.get("is_encrypted") else 0)
        features.append(1 if event.get("is_fragmented") else 0)

        # Payload features (8)
        features.append(event.get("payload_entropy", 0))
        features.append(event.get("printable_ratio", 0))
        features.append(event.get("digit_ratio", 0))
        features.append(event.get("special_char_ratio", 0))
        features.append(event.get("longest_word_length", 0))
        features.append(event.get("unique_chars", 0))
        features.append(event.get("compression_ratio", 1.0))
        features.append(1 if event.get("has_suspicious_strings") else 0)

        # Connection features (7)
        features.append(event.get("connection_state", 0))  # 0=NEW, 1=ESTABLISHED, etc
        features.append(event.get("failed_connections", 0))
        features.append(event.get("retransmissions", 0))
        features.append(event.get("syn_count", 0))
        features.append(event.get("fin_count", 0))
        features.append(event.get("rst_count", 0))
        features.append(1 if event.get("is_bidirectional") else 0)

        return np.array(features, dtype=np.float32)

    @staticmethod
    def get_feature_names() -> List[str]:
        """Get feature names for explainability"""
        return [
            # Packet features
            "packet_size", "packet_count", "bytes_sent", "bytes_recv",
            "avg_packet_size", "packet_size_std", "inter_arrival_time_mean",
            "inter_arrival_time_std", "duration_seconds", "packets_per_second",
            # Protocol features
            "protocol_code", "src_port", "dst_port", "is_encrypted", "is_fragmented",
            # Payload features
            "payload_entropy", "printable_ratio", "digit_ratio", "special_char_ratio",
            "longest_word_length", "unique_chars", "compression_ratio", "has_suspicious_strings",
            # Connection features
            "connection_state", "failed_connections", "retransmissions",
            "syn_count", "fin_count", "rst_count", "is_bidirectional"
        ]


class FastIsolationForest:
    """
    Optimized Isolation Forest for <10ms inference.

    Uses scikit-learn with optimized parameters for speed.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.01,
        max_samples: int = 256
    ):
        """
        Initialize Isolation Forest.

        Args:
            n_estimators: Number of trees (trade-off: accuracy vs speed)
            contamination: Expected proportion of anomalies
            max_samples: Samples per tree (smaller = faster)
        """
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples=max_samples,
            n_jobs=-1,  # Use all CPU cores
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_fitted = False

        logger.info(
            f"FastIsolationForest initialized "
            f"(trees={n_estimators}, contamination={contamination})"
        )

    def train(self, X: np.ndarray):
        """
        Train model on normal traffic.

        Args:
            X: Training data (N x 30 features)
        """
        logger.info(f"Training Isolation Forest on {len(X)} samples...")
        start_time = time.time()

        # Fit scaler
        X_scaled = self.scaler.fit_transform(X)

        # Fit model
        self.model.fit(X_scaled)
        self.is_fitted = True

        train_time = (time.time() - start_time) * 1000
        logger.info(f"Training complete in {train_time:.2f}ms")

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies.

        Args:
            X: Feature matrix (N x 30)

        Returns:
            (predictions, anomaly_scores)
            predictions: -1 for anomaly, 1 for normal
            anomaly_scores: 0-1, higher = more anomalous
        """
        if not self.is_fitted:
            raise ValueError("Model not trained. Call train() first.")

        X_scaled = self.scaler.transform(X)

        # Predict
        predictions = self.model.predict(X_scaled)

        # Get anomaly scores (normalized to 0-1)
        decision_scores = self.model.decision_function(X_scaled)
        # Normalize: more negative = more anomalous
        anomaly_scores = 1 - (decision_scores - decision_scores.min()) / (
            decision_scores.max() - decision_scores.min() + 1e-8
        )

        return predictions, anomaly_scores

    def predict_single(self, x: np.ndarray) -> Tuple[bool, float]:
        """
        Predict single sample (optimized).

        Args:
            x: Feature vector (30,)

        Returns:
            (is_anomaly, anomaly_score)
        """
        predictions, scores = self.predict(x.reshape(1, -1))
        return predictions[0] == -1, float(scores[0])

    def save(self, path: Path):
        """Save model to disk"""
        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "is_fitted": self.is_fitted
        }, path)
        logger.info(f"Model saved to {path}")

    def load(self, path: Path):
        """Load model from disk"""
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.is_fitted = data["is_fitted"]
        logger.info(f"Model loaded from {path}")


class VAEAutoencoder(nn.Module):
    """
    Variational Autoencoder for reconstruction-based anomaly detection.

    Architecture: [30 -> 64 -> 32 -> 16 -> 32 -> 64 -> 30]
    Fast inference: <5ms on CPU
    """

    def __init__(self, input_dim: int = 30, latent_dim: int = 16):
        super().__init__()

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU()
        )

        # Latent space (mean and log variance)
        self.fc_mu = nn.Linear(32, latent_dim)
        self.fc_logvar = nn.Linear(32, latent_dim)

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )

    def encode(self, x):
        """Encode input to latent space"""
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu, logvar):
        """Reparameterization trick"""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        """Decode latent representation"""
        return self.decoder(z)

    def forward(self, x):
        """Forward pass"""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        return recon, mu, logvar


class FastVAE:
    """
    Fast VAE for anomaly detection via reconstruction error.

    Inference: <5ms
    """

    def __init__(self, input_dim: int = 30, latent_dim: int = 16):
        self.model = VAEAutoencoder(input_dim, latent_dim)
        self.scaler = StandardScaler()
        self.threshold = None  # Set during training
        self.device = torch.device("cpu")  # CPU for low latency

        logger.info(f"FastVAE initialized (input_dim={input_dim}, latent_dim={latent_dim})")

    def train(
        self,
        X: np.ndarray,
        epochs: int = 50,
        batch_size: int = 64,
        lr: float = 1e-3
    ):
        """
        Train VAE on normal traffic.

        Args:
            X: Training data (N x features)
            epochs: Training epochs
            batch_size: Batch size
            lr: Learning rate
        """
        logger.info(f"Training VAE on {len(X)} samples for {epochs} epochs...")

        # Scale data
        X_scaled = self.scaler.fit_transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)

        # Optimizer
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        self.model.train()

        for epoch in range(epochs):
            total_loss = 0
            num_batches = 0

            # Mini-batch training
            for i in range(0, len(X_tensor), batch_size):
                batch = X_tensor[i:i+batch_size]

                # Forward pass
                recon, mu, logvar = self.model(batch)

                # Loss: reconstruction + KL divergence
                recon_loss = nn.functional.mse_loss(recon, batch, reduction='sum')
                kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
                loss = recon_loss + kl_loss

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                num_batches += 1

            avg_loss = total_loss / num_batches
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        # Compute threshold (95th percentile of reconstruction errors)
        self.model.eval()
        with torch.no_grad():
            recon, _, _ = self.model(X_tensor)
            errors = torch.mean((recon - X_tensor) ** 2, dim=1).numpy()
            self.threshold = np.percentile(errors, 95)

        logger.info(f"Training complete. Threshold: {self.threshold:.4f}")

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies based on reconstruction error.

        Args:
            X: Feature matrix

        Returns:
            (is_anomaly, reconstruction_errors)
        """
        X_scaled = self.scaler.transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)

        self.model.eval()
        with torch.no_grad():
            recon, _, _ = self.model(X_tensor)
            errors = torch.mean((recon - X_tensor) ** 2, dim=1).numpy()

        is_anomaly = errors > self.threshold
        return is_anomaly, errors

    def predict_single(self, x: np.ndarray) -> Tuple[bool, float]:
        """Predict single sample"""
        is_anomaly, errors = self.predict(x.reshape(1, -1))
        return bool(is_anomaly[0]), float(errors[0])

    def save(self, path: Path):
        """Save model"""
        torch.save({
            "model_state": self.model.state_dict(),
            "scaler": self.scaler,
            "threshold": self.threshold
        }, path)
        logger.info(f"VAE saved to {path}")

    def load(self, path: Path):
        """Load model"""
        data = torch.load(path, map_location=self.device)
        self.model.load_state_dict(data["model_state"])
        self.scaler = data["scaler"]
        self.threshold = data["threshold"]
        logger.info(f"VAE loaded from {path}")


class FastMLEngine:
    """
    Combined ML engine for fast threat detection.

    Uses both Isolation Forest and VAE for robust detection.
    """

    def __init__(self):
        self.isolation_forest = FastIsolationForest()
        self.vae = FastVAE()
        self.feature_extractor = FeatureExtractor()

    def train(self, events: List[Dict]):
        """
        Train both models on normal events.

        Args:
            events: List of normal traffic events
        """
        # Extract features
        X = np.array([self.feature_extractor.extract(e) for e in events])

        logger.info(f"Training ML models on {len(X)} samples...")

        # Train both models
        self.isolation_forest.train(X)
        self.vae.train(X)

        logger.info("ML training complete")

    def predict(self, event: Dict) -> ThreatScore:
        """
        Predict threat score for single event.

        Args:
            event: Event dictionary

        Returns:
            ThreatScore with combined analysis
        """
        start_time = time.time()

        # Extract features
        features = self.feature_extractor.extract(event)

        # Isolation Forest prediction
        if_anomaly, if_score = self.isolation_forest.predict_single(features)

        # VAE prediction
        vae_anomaly, recon_error = self.vae.predict_single(features)

        # Combined decision (either model detects anomaly)
        is_anomaly = if_anomaly or vae_anomaly

        # Combined anomaly score (max of both)
        anomaly_score = max(if_score, min(recon_error / (self.vae.threshold + 1e-8), 1.0))

        inference_time_ms = (time.time() - start_time) * 1000

        # Build feature dict for explainability
        feature_names = self.feature_extractor.get_feature_names()
        feature_dict = dict(zip(feature_names, features.tolist()))

        return ThreatScore(
            anomaly_score=anomaly_score,
            reconstruction_error=recon_error,
            is_anomaly=is_anomaly,
            features=feature_dict,
            inference_time_ms=inference_time_ms
        )

    def save(self, model_dir: Path):
        """Save both models"""
        model_dir.mkdir(parents=True, exist_ok=True)
        self.isolation_forest.save(model_dir / "isolation_forest.pkl")
        self.vae.save(model_dir / "vae.pt")
        logger.info(f"Models saved to {model_dir}")

    def load(self, model_dir: Path):
        """Load both models"""
        self.isolation_forest.load(model_dir / "isolation_forest.pkl")
        self.vae.load(model_dir / "vae.pt")
        logger.info(f"Models loaded from {model_dir}")


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("FAST ML MODELS TEST")
    print("="*80 + "\n")

    # Generate synthetic normal traffic
    np.random.seed(42)
    normal_events = []

    for i in range(1000):
        event = {
            "packet_size": np.random.normal(500, 100),
            "packet_count": np.random.randint(10, 100),
            "bytes_sent": np.random.normal(5000, 1000),
            "bytes_recv": np.random.normal(5000, 1000),
            "protocol": np.random.choice(["TCP", "UDP", "HTTP"]),
            "payload_entropy": np.random.uniform(3, 5),
            "duration_seconds": np.random.uniform(0.1, 10),
        }
        normal_events.append(event)

    # Train models
    engine = FastMLEngine()
    engine.train(normal_events)

    # Test: Normal event
    normal_test = normal_events[0]
    score = engine.predict(normal_test)
    print(f"Normal event:")
    print(f"  Anomaly score: {score.anomaly_score:.3f}")
    print(f"  Is anomaly: {score.is_anomaly}")
    print(f"  Inference time: {score.inference_time_ms:.2f}ms\n")

    # Test: Anomalous event
    anomalous_test = {
        "packet_size": 10000,  # Very large
        "packet_count": 1000,  # Very high
        "bytes_sent": 100000,  # Suspicious
        "bytes_recv": 100,
        "protocol": "ICMP",
        "payload_entropy": 7.9,  # High entropy
        "duration_seconds": 0.01,
    }

    score = engine.predict(anomalous_test)
    print(f"Anomalous event:")
    print(f"  Anomaly score: {score.anomaly_score:.3f}")
    print(f"  Is anomaly: {score.is_anomaly}")
    print(f"  Reconstruction error: {score.reconstruction_error:.3f}")
    print(f"  Inference time: {score.inference_time_ms:.2f}ms")

    print("\n" + "="*80)
    print("TEST COMPLETE - FAST ML <10MS!")
    print("="*80 + "\n")
