"""Anomaly detection backend using scikit-learn Isolation Forest."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import List, Optional

import joblib
from sklearn.ensemble import IsolationForest  # type: ignore[import]

from ...config import get_settings, TegumentarSettings
from .feature_extractor import FeatureVector

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Wrapper around Isolation Forest for zero-day detection."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._model: Optional[IsolationForest] = None

    def load(self) -> None:
        path = Path(self._settings.anomaly_model_path)
        if not path.exists():
            logger.warning(
                "Anomaly model missing at %s. Training baseline model.", path
            )
            self._train_default_model(path)
        self._model = joblib.load(path)
        if not isinstance(self._model, IsolationForest):
            raise TypeError("Loaded model is not an IsolationForest instance")
        logger.info("Loaded anomaly detector model from %s", path)

    def score(self, feature_vector: FeatureVector) -> float:
        if self._model is None:
            self.load()
        assert self._model is not None  # for type-checkers
        score = self._model.decision_function([feature_vector.as_list()])[0]
        # Convert to anomaly score (lower -> more anomalous)
        return 1.0 - score

    def _train_default_model(self, output_path: Path) -> None:
        dataset_path = (
            Path(__file__).resolve().parents[2]
            / "resources"
            / "ml"
            / "baseline_dataset.csv"
        )
        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Baseline dataset not found at {dataset_path}; provide training data or model."
            )

        features: List[List[float]] = []
        with dataset_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                features.append(
                    [
                        float(row["payload_length"]),
                        float(row["entropy"]),
                        float(row["printable_ratio"]),
                        float(row["digit_ratio"]),
                        float(row["average_byte_value"]),
                        float(row["tcp_flag_score"]),
                        float(row["inter_packet_interval"]),
                    ]
                )

        if not features:
            raise ValueError("Baseline dataset is empty.")

        model = IsolationForest(
            n_estimators=200,
            contamination=0.02,
            max_features=1.0,
            random_state=42,
        )
        model.fit(features)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, output_path)
        logger.info("Trained baseline anomaly model with %d samples", len(features))


__all__ = ["AnomalyDetector"]
