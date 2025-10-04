"""
🤖 ML-based Detection - Machine Learning para detecção de ameaças

Integra com backend ml_service para inferência de modelos treinados.

Modelos disponíveis:
- Malware classification (PE files, scripts)
- Phishing detection (URLs, emails)
- Network intrusion detection
- DGA (Domain Generation Algorithm) detection
- Lateral movement prediction
- Ransomware behavior prediction
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class MLModelType(Enum):
    """Tipo de modelo ML"""
    MALWARE_CLASSIFIER = "malware_classifier"
    PHISHING_DETECTOR = "phishing_detector"
    NETWORK_IDS = "network_ids"
    DGA_DETECTOR = "dga_detector"
    LATERAL_MOVEMENT = "lateral_movement"
    RANSOMWARE_BEHAVIOR = "ransomware_behavior"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class MLModel:
    """
    Modelo de Machine Learning
    """
    name: str
    model_type: MLModelType
    version: str

    # Model metadata
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    # Training info
    trained_on: Optional[datetime] = None
    training_samples: int = 0

    # Features
    input_features: List[str] = field(default_factory=list)
    output_classes: List[str] = field(default_factory=list)

    # Model file (local or backend)
    model_path: Optional[str] = None
    is_loaded: bool = False

    # Metadata
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Prediction:
    """
    Predição de modelo ML
    """
    model_name: str
    model_type: MLModelType
    timestamp: datetime

    # Prediction
    predicted_class: str
    confidence: float  # 0.0 to 1.0
    probabilities: Dict[str, float] = field(default_factory=dict)  # class -> probability

    # Input data
    input_data: Dict[str, Any] = field(default_factory=dict)

    # Explanation (SHAP, LIME, etc)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""

    # Metadata
    inference_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MLDetector:
    """
    ML-based Threat Detector

    Features:
    - Multiple ML models for different threats
    - Backend inference for scale
    - Local inference fallback
    - Feature extraction
    - Model explainability (SHAP)
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        confidence_threshold: float = 0.7,
    ):
        """
        Args:
            backend_url: URL do ml_service
            use_backend: Se True, usa backend para inference
            confidence_threshold: Threshold mínimo de confiança
        """
        self.backend_url = backend_url or "http://localhost:8007"
        self.use_backend = use_backend
        self.confidence_threshold = confidence_threshold

        # Available models
        self.models: Dict[str, MLModel] = {}

        # Predictions history
        self.predictions: List[Prediction] = []

        # Feature extractors
        self.feature_extractors: Dict[MLModelType, Any] = {}

    def load_model(self, model_name: str, model_type: MLModelType) -> MLModel:
        """
        Carrega modelo ML

        Args:
            model_name: Nome do modelo
            model_type: Tipo do modelo

        Returns:
            MLModel object
        """
        if self.use_backend:
            try:
                return self._load_model_backend(model_name, model_type)
            except Exception as e:
                logger.warning(f"Backend model load failed: {e}")

        # Fallback: load local model
        return self._load_model_local(model_name, model_type)

    def _load_model_backend(self, model_name: str, model_type: MLModelType) -> MLModel:
        """
        Carrega modelo do backend

        Args:
            model_name: Model name
            model_type: Model type

        Returns:
            MLModel
        """
        import httpx

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.backend_url}/api/ml/models/{model_name}"
                )
                response.raise_for_status()

                data = response.json()

                model = MLModel(
                    name=model_name,
                    model_type=model_type,
                    version=data.get("version", "1.0"),
                    accuracy=data.get("accuracy", 0.0),
                    precision=data.get("precision", 0.0),
                    recall=data.get("recall", 0.0),
                    f1_score=data.get("f1_score", 0.0),
                    trained_on=datetime.fromisoformat(data["trained_on"]) if data.get("trained_on") else None,
                    training_samples=data.get("training_samples", 0),
                    input_features=data.get("input_features", []),
                    output_classes=data.get("output_classes", []),
                    is_loaded=True,
                    description=data.get("description", ""),
                )

                self.models[model_name] = model

                logger.info(f"Model loaded from backend: {model_name} (accuracy: {model.accuracy:.2f})")

                return model

        except Exception as e:
            logger.error(f"Backend model load failed: {e}")
            raise

    def _load_model_local(self, model_name: str, model_type: MLModelType) -> MLModel:
        """
        Carrega modelo local (placeholder - requer bibliotecas ML)

        Args:
            model_name: Model name
            model_type: Model type

        Returns:
            MLModel
        """
        # TODO: Implement local model loading with joblib/pickle
        # For now, create placeholder

        model = MLModel(
            name=model_name,
            model_type=model_type,
            version="1.0-local",
            description="Local model placeholder",
            is_loaded=False,
        )

        self.models[model_name] = model

        logger.warning(f"Local model loading not implemented for {model_name}")

        return model

    def predict(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        explain: bool = False,
    ) -> Prediction:
        """
        Faz predição com modelo ML

        Args:
            model_name: Nome do modelo
            input_data: Dados de entrada (features)
            explain: Se True, gera explicação (SHAP)

        Returns:
            Prediction object
        """
        model = self.models.get(model_name)

        if not model:
            raise ValueError(f"Model not loaded: {model_name}")

        if self.use_backend:
            try:
                return self._predict_backend(model, input_data, explain)
            except Exception as e:
                logger.warning(f"Backend prediction failed: {e}")

        # Fallback: local prediction
        return self._predict_local(model, input_data, explain)

    def _predict_backend(
        self,
        model: MLModel,
        input_data: Dict[str, Any],
        explain: bool,
    ) -> Prediction:
        """
        Predição via backend ML service

        Args:
            model: MLModel object
            input_data: Input features
            explain: Generate explanation

        Returns:
            Prediction
        """
        import httpx
        import time

        try:
            start_time = time.time()

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/ml/predict",
                    json={
                        "model_name": model.name,
                        "input_data": input_data,
                        "explain": explain,
                    }
                )
                response.raise_for_status()

                result = response.json()

                inference_time = (time.time() - start_time) * 1000  # ms

                prediction = Prediction(
                    model_name=model.name,
                    model_type=model.model_type,
                    timestamp=datetime.now(),
                    predicted_class=result.get("predicted_class"),
                    confidence=result.get("confidence", 0.0),
                    probabilities=result.get("probabilities", {}),
                    input_data=input_data,
                    feature_importance=result.get("feature_importance", {}),
                    explanation=result.get("explanation", ""),
                    inference_time_ms=inference_time,
                )

                self.predictions.append(prediction)

                return prediction

        except Exception as e:
            logger.error(f"Backend prediction failed: {e}")
            raise

    def _predict_local(
        self,
        model: MLModel,
        input_data: Dict[str, Any],
        explain: bool,
    ) -> Prediction:
        """
        Predição local (placeholder)

        Args:
            model: MLModel
            input_data: Input features
            explain: Generate explanation

        Returns:
            Prediction
        """
        # TODO: Implement local inference

        prediction = Prediction(
            model_name=model.name,
            model_type=model.model_type,
            timestamp=datetime.now(),
            predicted_class="unknown",
            confidence=0.0,
            input_data=input_data,
            explanation="Local inference not implemented",
        )

        logger.warning(f"Local prediction not implemented for {model.name}")

        return prediction

    # Specialized detection methods

    def detect_malware(
        self,
        file_path: Path,
        extract_features: bool = True,
    ) -> Prediction:
        """
        Detecta malware em arquivo usando ML

        Args:
            file_path: Path do arquivo
            extract_features: Se True, extrai features automaticamente

        Returns:
            Prediction
        """
        model_name = "malware_classifier"

        # Load model if not loaded
        if model_name not in self.models:
            self.load_model(model_name, MLModelType.MALWARE_CLASSIFIER)

        # Extract features
        if extract_features:
            features = self._extract_file_features(file_path)
        else:
            features = {"file_path": str(file_path)}

        # Predict
        return self.predict(model_name, features, explain=True)

    def detect_phishing(
        self,
        url: Optional[str] = None,
        email_content: Optional[str] = None,
    ) -> Prediction:
        """
        Detecta phishing em URL ou email

        Args:
            url: URL para analisar
            email_content: Conteúdo do email

        Returns:
            Prediction
        """
        model_name = "phishing_detector"

        if model_name not in self.models:
            self.load_model(model_name, MLModelType.PHISHING_DETECTOR)

        # Extract features
        features = {}

        if url:
            features.update(self._extract_url_features(url))

        if email_content:
            features.update(self._extract_email_features(email_content))

        return self.predict(model_name, features, explain=True)

    def detect_dga(self, domain: str) -> Prediction:
        """
        Detecta se domínio foi gerado por DGA (Domain Generation Algorithm)

        Args:
            domain: Domain name

        Returns:
            Prediction
        """
        model_name = "dga_detector"

        if model_name not in self.models:
            self.load_model(model_name, MLModelType.DGA_DETECTOR)

        # Extract domain features
        features = self._extract_domain_features(domain)

        return self.predict(model_name, features, explain=True)

    def detect_lateral_movement(
        self,
        network_events: List[Dict[str, Any]]
    ) -> Prediction:
        """
        Detecta lateral movement patterns

        Args:
            network_events: Lista de eventos de rede

        Returns:
            Prediction
        """
        model_name = "lateral_movement_detector"

        if model_name not in self.models:
            self.load_model(model_name, MLModelType.LATERAL_MOVEMENT)

        # Extract sequence features
        features = self._extract_sequence_features(network_events)

        return self.predict(model_name, features, explain=True)

    # Feature extraction methods

    def _extract_file_features(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrai features de arquivo para malware detection

        Args:
            file_path: File path

        Returns:
            Features dict
        """
        import hashlib

        features = {
            "file_size": file_path.stat().st_size,
            "file_extension": file_path.suffix,
        }

        # Calculate hash
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            features["sha256"] = file_hash

        # TODO: Extract PE features, entropy, strings, etc

        return features

    def _extract_url_features(self, url: str) -> Dict[str, Any]:
        """
        Extrai features de URL para phishing detection

        Args:
            url: URL string

        Returns:
            Features dict
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)

        features = {
            "url": url,
            "url_length": len(url),
            "domain": parsed.netloc,
            "domain_length": len(parsed.netloc),
            "path_length": len(parsed.path),
            "has_ip": any(c.isdigit() for c in parsed.netloc),
            "has_https": parsed.scheme == "https",
            "num_dots": url.count("."),
            "num_slashes": url.count("/"),
            "num_hyphens": url.count("-"),
            "num_underscores": url.count("_"),
            "num_at": url.count("@"),
        }

        return features

    def _extract_email_features(self, email_content: str) -> Dict[str, Any]:
        """
        Extrai features de email para phishing detection

        Args:
            email_content: Email text

        Returns:
            Features dict
        """
        features = {
            "email_length": len(email_content),
            "num_urls": email_content.count("http"),
            "has_urgent": any(word in email_content.lower() for word in ["urgent", "immediate", "action required"]),
            "has_money": any(word in email_content.lower() for word in ["$", "prize", "won", "lottery"]),
            "has_click_here": "click here" in email_content.lower(),
        }

        return features

    def _extract_domain_features(self, domain: str) -> Dict[str, Any]:
        """
        Extrai features de domínio para DGA detection

        Args:
            domain: Domain name

        Returns:
            Features dict
        """
        import re

        features = {
            "domain": domain,
            "domain_length": len(domain),
            "num_digits": sum(c.isdigit() for c in domain),
            "num_consonants": sum(c in "bcdfghjklmnpqrstvwxyz" for c in domain.lower()),
            "num_vowels": sum(c in "aeiou" for c in domain.lower()),
            "num_hyphens": domain.count("-"),
            "num_dots": domain.count("."),
            "entropy": self._calculate_entropy(domain),
            "has_numbers": any(c.isdigit() for c in domain),
        }

        return features

    def _extract_sequence_features(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extrai features de sequência de eventos

        Args:
            events: Event sequence

        Returns:
            Features dict
        """
        features = {
            "num_events": len(events),
            "unique_sources": len(set(e.get("source_ip", "") for e in events)),
            "unique_destinations": len(set(e.get("dest_ip", "") for e in events)),
            "time_span_seconds": 0,
        }

        # Calculate time span
        if len(events) >= 2:
            first_time = datetime.fromisoformat(events[0].get("timestamp", ""))
            last_time = datetime.fromisoformat(events[-1].get("timestamp", ""))
            features["time_span_seconds"] = (last_time - first_time).total_seconds()

        return features

    def _calculate_entropy(self, text: str) -> float:
        """
        Calcula entropia de Shannon de texto

        Args:
            text: Text string

        Returns:
            Entropy value
        """
        import math
        from collections import Counter

        if not text:
            return 0.0

        # Count character frequencies
        freq = Counter(text)
        total = len(text)

        # Calculate entropy
        entropy = 0.0
        for count in freq.values():
            prob = count / total
            entropy -= prob * math.log2(prob)

        return entropy

    def get_predictions(
        self,
        model_name: Optional[str] = None,
        predicted_class: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 100,
    ) -> List[Prediction]:
        """
        Retorna predições com filtros

        Args:
            model_name: Filter by model
            predicted_class: Filter by predicted class
            min_confidence: Minimum confidence threshold
            limit: Max predictions

        Returns:
            List of Prediction
        """
        predictions = self.predictions

        if model_name:
            predictions = [p for p in predictions if p.model_name == model_name]

        if predicted_class:
            predictions = [p for p in predictions if p.predicted_class == predicted_class]

        if min_confidence:
            predictions = [p for p in predictions if p.confidence >= min_confidence]

        # Sort by timestamp (most recent first)
        predictions = sorted(predictions, key=lambda p: p.timestamp, reverse=True)

        return predictions[:limit]

    def get_model_stats(self, model_name: str) -> Dict[str, Any]:
        """
        Retorna estatísticas de uso do modelo

        Args:
            model_name: Model name

        Returns:
            Stats dict
        """
        model_predictions = [p for p in self.predictions if p.model_name == model_name]

        if not model_predictions:
            return {}

        # Calculate stats
        confidences = [p.confidence for p in model_predictions]
        inference_times = [p.inference_time_ms for p in model_predictions]

        # Class distribution
        class_counts = {}
        for pred in model_predictions:
            class_counts[pred.predicted_class] = class_counts.get(pred.predicted_class, 0) + 1

        return {
            "total_predictions": len(model_predictions),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "avg_inference_time_ms": sum(inference_times) / len(inference_times) if inference_times else 0,
            "class_distribution": class_counts,
        }
