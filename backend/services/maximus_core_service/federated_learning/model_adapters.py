"""
Model Adapters for Federated Learning

This module provides adapters for integrating VÉRTICE machine learning
models with the federated learning framework. Each adapter implements
a common interface for:
- Weight extraction and setting
- Local training
- Model evaluation

Supported models:
- Threat Classifier (narrative_manipulation_filter)
- Malware Detector (immunis_macrophage_service)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from .base import ModelType

logger = logging.getLogger(__name__)


class BaseModelAdapter(ABC):
    """
    Base class for model adapters.

    All model adapters must implement this interface to be compatible
    with the federated learning framework.
    """

    def __init__(self, model_type: ModelType):
        """
        Initialize model adapter.

        Args:
            model_type: Type of model
        """
        self.model_type = model_type
        self.model = None

    @abstractmethod
    def get_weights(self) -> dict[str, np.ndarray]:
        """
        Extract trainable weights from model.

        Returns:
            Dictionary mapping layer names to weight arrays
        """
        pass

    @abstractmethod
    def set_weights(self, weights: dict[str, np.ndarray]) -> None:
        """
        Set model weights.

        Args:
            weights: Dictionary mapping layer names to weight arrays
        """
        pass

    @abstractmethod
    def train_epochs(
        self,
        train_data: Any,
        train_labels: Any,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        validation_split: float = 0.1,
    ) -> dict[str, float]:
        """
        Train model for specified number of epochs.

        Args:
            train_data: Training data
            train_labels: Training labels
            epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            validation_split: Fraction of data for validation

        Returns:
            Dictionary of training metrics (loss, accuracy, etc.)
        """
        pass

    @abstractmethod
    def evaluate(self, test_data: Any, test_labels: Any) -> dict[str, float]:
        """
        Evaluate model on test data.

        Args:
            test_data: Test data
            test_labels: Test labels

        Returns:
            Dictionary of evaluation metrics (loss, accuracy, etc.)
        """
        pass

    def get_model_info(self) -> dict[str, Any]:
        """
        Get model information.

        Returns:
            Dictionary with model metadata
        """
        weights = self.get_weights()
        return {
            "model_type": self.model_type.value,
            "num_layers": len(weights),
            "layer_names": list(weights.keys()),
            "total_parameters": sum(w.size for w in weights.values()),
            "total_size_mb": sum(w.nbytes for w in weights.values()) / (1024 * 1024),
        }


class ThreatClassifierAdapter(BaseModelAdapter):
    """
    Adapter for narrative_manipulation_filter threat classifier.

    This adapter interfaces with the threat classification model used
    for detecting manipulative narratives, misinformation, and threats.

    Model Architecture (Simulated):
    - Embedding layer: 10000 vocab -> 128 dim
    - LSTM layer: 128 -> 64
    - Dense layer: 64 -> 32
    - Output layer: 32 -> 4 (threat categories)
    """

    def __init__(self):
        """Initialize threat classifier adapter."""
        super().__init__(ModelType.THREAT_CLASSIFIER)

        # Initialize simulated model architecture
        # In production, this would load the actual narrative_manipulation_filter model
        self._initialize_model()

        logger.info("ThreatClassifierAdapter initialized")

    def _initialize_model(self) -> None:
        """Initialize model weights with random values (simulated)."""
        # Simulate model layers
        self.model = {
            "embedding": np.random.randn(10000, 128).astype(np.float32) * 0.01,
            "lstm_kernel": np.random.randn(128, 256).astype(np.float32) * 0.01,
            "lstm_recurrent": np.random.randn(64, 256).astype(np.float32) * 0.01,
            "dense1_kernel": np.random.randn(64, 32).astype(np.float32) * 0.01,
            "dense1_bias": np.zeros(32, dtype=np.float32),
            "output_kernel": np.random.randn(32, 4).astype(np.float32) * 0.01,
            "output_bias": np.zeros(4, dtype=np.float32),
        }

    def get_weights(self) -> dict[str, np.ndarray]:
        """Extract weights from threat classifier."""
        if self.model is None:
            raise RuntimeError("Model not initialized")

        return {name: weights.copy() for name, weights in self.model.items()}

    def set_weights(self, weights: dict[str, np.ndarray]) -> None:
        """Set threat classifier weights."""
        if self.model is None:
            raise RuntimeError("Model not initialized")

        # Validate weights match expected structure
        expected_layers = set(self.model.keys())
        provided_layers = set(weights.keys())

        if expected_layers != provided_layers:
            raise ValueError(f"Weight mismatch: expected {expected_layers}, got {provided_layers}")

        # Set weights
        for layer_name, layer_weights in weights.items():
            if layer_weights.shape != self.model[layer_name].shape:
                raise ValueError(
                    f"Shape mismatch for layer {layer_name}: "
                    f"expected {self.model[layer_name].shape}, "
                    f"got {layer_weights.shape}"
                )
            self.model[layer_name] = layer_weights.copy()

        logger.debug("Updated threat classifier weights")

    def train_epochs(
        self,
        train_data: Any,
        train_labels: Any,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        validation_split: float = 0.1,
    ) -> dict[str, float]:
        """
        Train threat classifier.

        Simulates training by applying small random perturbations to weights.
        In production, this would call the actual training loop.

        Args:
            train_data: Training text data
            train_labels: Threat category labels
            epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            validation_split: Validation fraction

        Returns:
            Training metrics
        """
        logger.info(f"Training threat classifier: {epochs} epochs, batch_size={batch_size}, lr={learning_rate}")

        # Simulate training by perturbing weights
        for layer_name in self.model:
            perturbation = np.random.randn(*self.model[layer_name].shape).astype(np.float32)
            self.model[layer_name] += learning_rate * perturbation * 0.01

        # Simulate metrics
        # In production, these would be actual loss/accuracy from training
        metrics = {
            "loss": 0.45 + np.random.rand() * 0.1,
            "accuracy": 0.82 + np.random.rand() * 0.1,
            "val_loss": 0.48 + np.random.rand() * 0.1,
            "val_accuracy": 0.80 + np.random.rand() * 0.1,
            "epochs_completed": epochs,
        }

        logger.info(f"Training completed: loss={metrics['loss']:.4f}, accuracy={metrics['accuracy']:.4f}")

        return metrics

    def evaluate(self, test_data: Any, test_labels: Any) -> dict[str, float]:
        """
        Evaluate threat classifier on test data.

        Args:
            test_data: Test text data
            test_labels: Test threat labels

        Returns:
            Evaluation metrics
        """
        logger.info("Evaluating threat classifier on test set")

        # Simulate evaluation
        # In production, this would run actual inference
        metrics = {
            "loss": 0.47 + np.random.rand() * 0.1,
            "accuracy": 0.81 + np.random.rand() * 0.1,
            "precision": 0.79 + np.random.rand() * 0.1,
            "recall": 0.83 + np.random.rand() * 0.1,
            "f1_score": 0.81 + np.random.rand() * 0.1,
        }

        logger.info(f"Evaluation: accuracy={metrics['accuracy']:.4f}")

        return metrics


class MalwareDetectorAdapter(BaseModelAdapter):
    """
    Adapter for immunis_macrophage_service malware detector.

    This adapter interfaces with the malware detection model used by
    the Immunis Macrophage service for identifying malicious files.

    Model Architecture (Simulated):
    - Input layer: 2048 features (file characteristics)
    - Hidden layer 1: 2048 -> 512
    - Hidden layer 2: 512 -> 128
    - Hidden layer 3: 128 -> 32
    - Output layer: 32 -> 2 (benign/malware)
    """

    def __init__(self):
        """Initialize malware detector adapter."""
        super().__init__(ModelType.MALWARE_DETECTOR)

        # Initialize simulated model
        self._initialize_model()

        logger.info("MalwareDetectorAdapter initialized")

    def _initialize_model(self) -> None:
        """Initialize model weights with random values (simulated)."""
        # Simulate deep neural network for malware detection
        self.model = {
            "hidden1_kernel": np.random.randn(2048, 512).astype(np.float32) * 0.01,
            "hidden1_bias": np.zeros(512, dtype=np.float32),
            "hidden2_kernel": np.random.randn(512, 128).astype(np.float32) * 0.01,
            "hidden2_bias": np.zeros(128, dtype=np.float32),
            "hidden3_kernel": np.random.randn(128, 32).astype(np.float32) * 0.01,
            "hidden3_bias": np.zeros(32, dtype=np.float32),
            "output_kernel": np.random.randn(32, 2).astype(np.float32) * 0.01,
            "output_bias": np.zeros(2, dtype=np.float32),
        }

    def get_weights(self) -> dict[str, np.ndarray]:
        """Extract weights from malware detector."""
        if self.model is None:
            raise RuntimeError("Model not initialized")

        return {name: weights.copy() for name, weights in self.model.items()}

    def set_weights(self, weights: dict[str, np.ndarray]) -> None:
        """Set malware detector weights."""
        if self.model is None:
            raise RuntimeError("Model not initialized")

        # Validate weights
        expected_layers = set(self.model.keys())
        provided_layers = set(weights.keys())

        if expected_layers != provided_layers:
            raise ValueError(f"Weight mismatch: expected {expected_layers}, got {provided_layers}")

        # Set weights
        for layer_name, layer_weights in weights.items():
            if layer_weights.shape != self.model[layer_name].shape:
                raise ValueError(
                    f"Shape mismatch for layer {layer_name}: "
                    f"expected {self.model[layer_name].shape}, "
                    f"got {layer_weights.shape}"
                )
            self.model[layer_name] = layer_weights.copy()

        logger.debug("Updated malware detector weights")

    def train_epochs(
        self,
        train_data: Any,
        train_labels: Any,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        validation_split: float = 0.1,
    ) -> dict[str, float]:
        """
        Train malware detector.

        Simulates training by applying small random perturbations to weights.
        In production, this would call the actual training loop.

        Args:
            train_data: File feature vectors
            train_labels: Malware labels (0=benign, 1=malware)
            epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            validation_split: Validation fraction

        Returns:
            Training metrics
        """
        logger.info(f"Training malware detector: {epochs} epochs, batch_size={batch_size}, lr={learning_rate}")

        # Simulate training
        for layer_name in self.model:
            perturbation = np.random.randn(*self.model[layer_name].shape).astype(np.float32)
            self.model[layer_name] += learning_rate * perturbation * 0.01

        # Simulate metrics
        metrics = {
            "loss": 0.18 + np.random.rand() * 0.05,
            "accuracy": 0.94 + np.random.rand() * 0.03,
            "val_loss": 0.20 + np.random.rand() * 0.05,
            "val_accuracy": 0.93 + np.random.rand() * 0.03,
            "epochs_completed": epochs,
        }

        logger.info(f"Training completed: loss={metrics['loss']:.4f}, accuracy={metrics['accuracy']:.4f}")

        return metrics

    def evaluate(self, test_data: Any, test_labels: Any) -> dict[str, float]:
        """
        Evaluate malware detector on test data.

        Args:
            test_data: Test file feature vectors
            test_labels: Test malware labels

        Returns:
            Evaluation metrics
        """
        logger.info("Evaluating malware detector on test set")

        # Simulate evaluation
        metrics = {
            "loss": 0.19 + np.random.rand() * 0.05,
            "accuracy": 0.93 + np.random.rand() * 0.03,
            "precision": 0.92 + np.random.rand() * 0.03,
            "recall": 0.94 + np.random.rand() * 0.03,
            "f1_score": 0.93 + np.random.rand() * 0.03,
            "auc_roc": 0.96 + np.random.rand() * 0.02,
            "false_positive_rate": 0.02 + np.random.rand() * 0.01,
        }

        logger.info(f"Evaluation: accuracy={metrics['accuracy']:.4f}, FPR={metrics['false_positive_rate']:.4f}")

        return metrics


def create_model_adapter(model_type: ModelType) -> BaseModelAdapter:
    """
    Factory function to create model adapter.

    Args:
        model_type: Type of model

    Returns:
        Model adapter instance

    Raises:
        ValueError: If model type not supported
    """
    if model_type == ModelType.THREAT_CLASSIFIER:
        return ThreatClassifierAdapter()
    if model_type == ModelType.MALWARE_DETECTOR:
        return MalwareDetectorAdapter()
    raise ValueError(f"Unsupported model type: {model_type}")
