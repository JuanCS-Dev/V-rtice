"""
Model Evaluator for MAXIMUS Training Pipeline

Comprehensive model evaluation:
- Standard metrics (accuracy, precision, recall, F1)
- ROC-AUC, PR-AUC
- Confusion matrix
- Per-class metrics
- Latency benchmarking
- Model comparison

REGRA DE OURO: Zero mocks, production-ready evaluation
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for a model."""

    # Classification metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float | None = None
    pr_auc: float | None = None

    # Confusion matrix
    confusion_matrix: np.ndarray | None = None

    # Per-class metrics
    per_class_metrics: dict[int, dict[str, float]] | None = None

    # Performance
    avg_inference_time_ms: float | None = None
    throughput_samples_per_sec: float | None = None

    # Additional metrics
    additional_metrics: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        result = {
            "accuracy": float(self.accuracy),
            "precision": float(self.precision),
            "recall": float(self.recall),
            "f1_score": float(self.f1_score),
        }

        if self.roc_auc is not None:
            result["roc_auc"] = float(self.roc_auc)
        if self.pr_auc is not None:
            result["pr_auc"] = float(self.pr_auc)

        if self.confusion_matrix is not None:
            result["confusion_matrix"] = self.confusion_matrix.tolist()

        if self.per_class_metrics is not None:
            result["per_class_metrics"] = self.per_class_metrics

        if self.avg_inference_time_ms is not None:
            result["avg_inference_time_ms"] = float(self.avg_inference_time_ms)
        if self.throughput_samples_per_sec is not None:
            result["throughput_samples_per_sec"] = float(self.throughput_samples_per_sec)

        if self.additional_metrics:
            result["additional_metrics"] = self.additional_metrics

        return result


class ModelEvaluator:
    """Evaluates trained models on test data.

    Features:
    - Classification metrics
    - ROC/PR curves
    - Confusion matrix
    - Per-class analysis
    - Latency benchmarking
    - Model comparison

    Example:
        ```python
        evaluator = ModelEvaluator(model=trained_model, test_features=test_features, test_labels=test_labels)

        # Evaluate
        metrics = evaluator.evaluate()

        # Print report
        evaluator.print_report(metrics)

        # Save report
        evaluator.save_report(metrics, "evaluation_report.json")
        ```
    """

    def __init__(
        self, model: Any, test_features: np.ndarray, test_labels: np.ndarray, class_names: list[str] | None = None
    ):
        """Initialize evaluator.

        Args:
            model: Trained model
            test_features: Test features (N, D)
            test_labels: Test labels (N,)
            class_names: Optional class names for reporting
        """
        self.model = model
        self.test_features = test_features
        self.test_labels = test_labels
        self.class_names = class_names

        # Filter out unlabeled samples
        labeled_mask = test_labels >= 0
        self.test_features = test_features[labeled_mask]
        self.test_labels = test_labels[labeled_mask]

        self.n_samples = len(self.test_labels)
        self.n_classes = len(np.unique(self.test_labels))

        logger.info(f"ModelEvaluator initialized: {self.n_samples} samples, {self.n_classes} classes")

    def evaluate(
        self, compute_roc_auc: bool = True, compute_pr_auc: bool = True, benchmark_latency: bool = True
    ) -> EvaluationMetrics:
        """Evaluate model on test data.

        Args:
            compute_roc_auc: Compute ROC-AUC
            compute_pr_auc: Compute PR-AUC
            benchmark_latency: Benchmark inference latency

        Returns:
            Evaluation metrics
        """
        # Get predictions
        predictions, probabilities = self._get_predictions()

        # Classification metrics
        accuracy = self._compute_accuracy(predictions)
        precision = self._compute_precision(predictions)
        recall = self._compute_recall(predictions)
        f1 = self._compute_f1(predictions)

        # Confusion matrix
        confusion_matrix = self._compute_confusion_matrix(predictions)

        # Per-class metrics
        per_class_metrics = self._compute_per_class_metrics(predictions)

        # ROC-AUC
        roc_auc = None
        if compute_roc_auc and probabilities is not None and self.n_classes == 2:
            roc_auc = self._compute_roc_auc(probabilities)

        # PR-AUC
        pr_auc = None
        if compute_pr_auc and probabilities is not None and self.n_classes == 2:
            pr_auc = self._compute_pr_auc(probabilities)

        # Latency benchmark
        avg_latency, throughput = None, None
        if benchmark_latency:
            avg_latency, throughput = self._benchmark_latency()

        metrics = EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            confusion_matrix=confusion_matrix,
            per_class_metrics=per_class_metrics,
            avg_inference_time_ms=avg_latency,
            throughput_samples_per_sec=throughput,
        )

        logger.info(f"Evaluation complete: accuracy={accuracy:.4f}, f1={f1:.4f}")

        return metrics

    def _get_predictions(self) -> tuple[np.ndarray, np.ndarray | None]:
        """Get model predictions.

        Returns:
            Tuple of (predictions, probabilities)
            - predictions: (N,) class predictions
            - probabilities: (N, C) class probabilities or None
        """
        try:
            # Try PyTorch model
            import torch

            if hasattr(self.model, "eval"):
                self.model.eval()

                with torch.no_grad():
                    inputs = torch.FloatTensor(self.test_features)

                    if hasattr(self.model, "to"):
                        device = next(self.model.parameters()).device
                        inputs = inputs.to(device)

                    outputs = self.model(inputs)

                    # Handle different output formats
                    if isinstance(outputs, tuple):
                        # VAE-like models: (reconstruction, mean, logvar)
                        outputs = outputs[0]

                    # Get probabilities
                    if outputs.dim() == 1:
                        # Binary classification
                        probabilities = torch.sigmoid(outputs).cpu().numpy()
                        predictions = (probabilities > 0.5).astype(int)
                    else:
                        # Multi-class
                        probabilities = torch.softmax(outputs, dim=1).cpu().numpy()
                        predictions = probabilities.argmax(axis=1)

                    return predictions, probabilities

        except ImportError:
            pass

        # Fallback: sklearn-like models
        if hasattr(self.model, "predict"):
            predictions = self.model.predict(self.test_features)

            probabilities = None
            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(self.test_features)

            return predictions, probabilities

        raise ValueError("Model does not have predict() or forward() method")

    def _compute_accuracy(self, predictions: np.ndarray) -> float:
        """Compute accuracy.

        Args:
            predictions: Predicted labels

        Returns:
            Accuracy
        """
        correct = (predictions == self.test_labels).sum()
        return float(correct / len(predictions))

    def _compute_precision(self, predictions: np.ndarray) -> float:
        """Compute precision (macro-averaged).

        Args:
            predictions: Predicted labels

        Returns:
            Precision
        """
        precisions = []

        for class_id in np.unique(self.test_labels):
            tp = ((predictions == class_id) & (self.test_labels == class_id)).sum()
            fp = ((predictions == class_id) & (self.test_labels != class_id)).sum()

            if tp + fp > 0:
                precision = tp / (tp + fp)
                precisions.append(precision)

        return float(np.mean(precisions)) if precisions else 0.0

    def _compute_recall(self, predictions: np.ndarray) -> float:
        """Compute recall (macro-averaged).

        Args:
            predictions: Predicted labels

        Returns:
            Recall
        """
        recalls = []

        for class_id in np.unique(self.test_labels):
            tp = ((predictions == class_id) & (self.test_labels == class_id)).sum()
            fn = ((predictions != class_id) & (self.test_labels == class_id)).sum()

            if tp + fn > 0:
                recall = tp / (tp + fn)
                recalls.append(recall)

        return float(np.mean(recalls)) if recalls else 0.0

    def _compute_f1(self, predictions: np.ndarray) -> float:
        """Compute F1 score (macro-averaged).

        Args:
            predictions: Predicted labels

        Returns:
            F1 score
        """
        precision = self._compute_precision(predictions)
        recall = self._compute_recall(predictions)

        if precision + recall > 0:
            return float(2 * precision * recall / (precision + recall))
        return 0.0

    def _compute_confusion_matrix(self, predictions: np.ndarray) -> np.ndarray:
        """Compute confusion matrix.

        Args:
            predictions: Predicted labels

        Returns:
            Confusion matrix (C, C)
        """
        cm = np.zeros((self.n_classes, self.n_classes), dtype=int)

        for true_label, pred_label in zip(self.test_labels, predictions, strict=False):
            cm[true_label, pred_label] += 1

        return cm

    def _compute_per_class_metrics(self, predictions: np.ndarray) -> dict[int, dict[str, float]]:
        """Compute per-class metrics.

        Args:
            predictions: Predicted labels

        Returns:
            Dictionary mapping class_id to metrics
        """
        per_class = {}

        for class_id in np.unique(self.test_labels):
            tp = ((predictions == class_id) & (self.test_labels == class_id)).sum()
            fp = ((predictions == class_id) & (self.test_labels != class_id)).sum()
            fn = ((predictions != class_id) & (self.test_labels == class_id)).sum()
            tn = ((predictions != class_id) & (self.test_labels != class_id)).sum()

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            per_class[int(class_id)] = {
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "support": int(tp + fn),
            }

        return per_class

    def _compute_roc_auc(self, probabilities: np.ndarray) -> float:
        """Compute ROC-AUC (binary classification only).

        Args:
            probabilities: Class probabilities

        Returns:
            ROC-AUC score
        """
        try:
            from sklearn.metrics import roc_auc_score

            # Binary classification
            if len(probabilities.shape) == 1:
                scores = probabilities
            else:
                scores = probabilities[:, 1]

            auc = roc_auc_score(self.test_labels, scores)
            return float(auc)

        except ImportError:
            logger.warning("sklearn not available for ROC-AUC computation")
            return 0.0

    def _compute_pr_auc(self, probabilities: np.ndarray) -> float:
        """Compute PR-AUC (binary classification only).

        Args:
            probabilities: Class probabilities

        Returns:
            PR-AUC score
        """
        try:
            from sklearn.metrics import average_precision_score

            # Binary classification
            if len(probabilities.shape) == 1:
                scores = probabilities
            else:
                scores = probabilities[:, 1]

            auc = average_precision_score(self.test_labels, scores)
            return float(auc)

        except ImportError:
            logger.warning("sklearn not available for PR-AUC computation")
            return 0.0

    def _benchmark_latency(self, n_iterations: int = 100) -> tuple[float, float]:
        """Benchmark inference latency.

        Args:
            n_iterations: Number of iterations

        Returns:
            Tuple of (avg_latency_ms, throughput_samples_per_sec)
        """
        import time

        latencies = []

        # Warmup
        _ = self._get_predictions()

        # Benchmark
        for _ in range(n_iterations):
            start = time.time()
            _ = self._get_predictions()
            end = time.time()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

        avg_latency = np.mean(latencies)
        throughput = (self.n_samples / avg_latency) * 1000  # samples per second

        return float(avg_latency), float(throughput)

    def print_report(self, metrics: EvaluationMetrics):
        """Print evaluation report.

        Args:
            metrics: Evaluation metrics
        """
        print("\n" + "=" * 80)
        print("MODEL EVALUATION REPORT")
        print("=" * 80)

        print("\nOverall Metrics:")
        print(f"  Accuracy:  {metrics.accuracy:.4f}")
        print(f"  Precision: {metrics.precision:.4f}")
        print(f"  Recall:    {metrics.recall:.4f}")
        print(f"  F1 Score:  {metrics.f1_score:.4f}")

        if metrics.roc_auc:
            print(f"  ROC-AUC:   {metrics.roc_auc:.4f}")
        if metrics.pr_auc:
            print(f"  PR-AUC:    {metrics.pr_auc:.4f}")

        if metrics.per_class_metrics:
            print("\nPer-Class Metrics:")
            for class_id, class_metrics in metrics.per_class_metrics.items():
                class_name = self.class_names[class_id] if self.class_names else f"Class {class_id}"
                print(f"  {class_name}:")
                print(f"    Precision: {class_metrics['precision']:.4f}")
                print(f"    Recall:    {class_metrics['recall']:.4f}")
                print(f"    F1 Score:  {class_metrics['f1_score']:.4f}")
                print(f"    Support:   {class_metrics['support']}")

        if metrics.avg_inference_time_ms:
            print("\nPerformance:")
            print(f"  Avg Inference Time: {metrics.avg_inference_time_ms:.2f} ms")
            print(f"  Throughput:         {metrics.throughput_samples_per_sec:.0f} samples/sec")

        print("=" * 80)

    def save_report(self, metrics: EvaluationMetrics, output_path: Path):
        """Save evaluation report to JSON.

        Args:
            metrics: Evaluation metrics
            output_path: Path to save report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "n_samples": self.n_samples,
            "n_classes": self.n_classes,
            "metrics": metrics.to_dict(),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Evaluation report saved to {output_path}")
