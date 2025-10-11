"""
Unit tests for ML Metrics API (Phase 5.5).

Tests endpoints for ML prediction monitoring and analytics.

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.ml_metrics import router, TimeframeEnum, MLMetricsResponse


@pytest.fixture
def client():
    """Create test client with ML metrics router."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestMLMetricsHealthEndpoint:
    """Tests for ML metrics health check endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/api/v1/eureka/ml-metrics/health")
        assert response.status_code == 200
    
    def test_health_check_contains_status(self, client):
        """Health check should contain status field."""
        response = client.get("/api/v1/eureka/ml-metrics/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_check_contains_version(self, client):
        """Health check should contain version field."""
        response = client.get("/api/v1/eureka/ml-metrics/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "5.5.1"


class TestMLMetricsEndpoint:
    """Tests for main ML metrics endpoint."""
    
    def test_get_metrics_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/v1/eureka/ml-metrics")
        assert response.status_code == 200
    
    def test_get_metrics_with_24h_timeframe(self, client):
        """Should accept 24h timeframe."""
        response = client.get("/api/v1/eureka/ml-metrics?timeframe=24h")
        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "24h"
    
    def test_get_metrics_with_7d_timeframe(self, client):
        """Should accept 7d timeframe."""
        response = client.get("/api/v1/eureka/ml-metrics?timeframe=7d")
        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "7d"
    
    def test_get_metrics_contains_usage_breakdown(self, client):
        """Response should contain usage breakdown."""
        response = client.get("/api/v1/eureka/ml-metrics")
        data = response.json()
        
        assert "usage_breakdown" in data
        breakdown = data["usage_breakdown"]
        
        assert "ml_count" in breakdown
        assert "wargaming_count" in breakdown
        assert "total" in breakdown
        assert "ml_usage_rate" in breakdown
        
        # Validate calculation
        expected_rate = (breakdown["ml_count"] / breakdown["total"] * 100) if breakdown["total"] > 0 else 0.0
        assert abs(breakdown["ml_usage_rate"] - expected_rate) < 0.01
    
    def test_get_metrics_contains_confidence_data(self, client):
        """Response should contain confidence metrics."""
        response = client.get("/api/v1/eureka/ml-metrics")
        data = response.json()
        
        assert "avg_confidence" in data
        assert "confidence_trend" in data
        assert "confidence_distribution" in data
        
        # Validate confidence is in [0, 1]
        assert 0.0 <= data["avg_confidence"] <= 1.0
        
        # Validate distribution buckets
        distribution = data["confidence_distribution"]
        assert len(distribution) == 10  # 10 buckets (0.0-0.1, 0.1-0.2, ..., 0.9-1.0)
        
        for bucket in distribution:
            assert "bucket_min" in bucket
            assert "bucket_max" in bucket
            assert "count" in bucket
            assert 0.0 <= bucket["bucket_min"] <= 1.0
            assert 0.0 <= bucket["bucket_max"] <= 1.0
            assert bucket["count"] >= 0
    
    def test_get_metrics_contains_time_savings(self, client):
        """Response should contain time savings metrics."""
        response = client.get("/api/v1/eureka/ml-metrics")
        data = response.json()
        
        assert "time_savings_percent" in data
        assert "time_savings_absolute_minutes" in data
        assert "time_savings_trend" in data
        
        # Validate percentage
        assert 0.0 <= data["time_savings_percent"] <= 100.0
    
    def test_get_metrics_contains_confusion_matrix(self, client):
        """Response should contain confusion matrix."""
        response = client.get("/api/v1/eureka/ml-metrics")
        data = response.json()
        
        assert "confusion_matrix" in data
        matrix = data["confusion_matrix"]
        
        assert "true_positive" in matrix
        assert "false_positive" in matrix
        assert "false_negative" in matrix
        assert "true_negative" in matrix
        
        # All counts should be non-negative
        assert matrix["true_positive"] >= 0
        assert matrix["false_positive"] >= 0
        assert matrix["false_negative"] >= 0
        assert matrix["true_negative"] >= 0
    
    def test_get_metrics_contains_usage_timeline(self, client):
        """Response should contain usage timeline."""
        response = client.get("/api/v1/eureka/ml-metrics")
        data = response.json()
        
        assert "usage_timeline" in data
        timeline = data["usage_timeline"]
        
        assert "ml" in timeline
        assert "wargaming" in timeline
        assert "total" in timeline
        
        # Each series should have data points
        assert len(timeline["ml"]) > 0
        assert len(timeline["wargaming"]) > 0
        assert len(timeline["total"]) > 0
        
        # Validate structure
        for point in timeline["ml"]:
            assert "timestamp" in point
            assert "value" in point
    
    def test_get_metrics_contains_recent_predictions(self, client):
        """Response should contain recent predictions feed."""
        response = client.get("/api/v1/eureka/ml-metrics")
        data = response.json()
        
        assert "recent_predictions" in data
        predictions = data["recent_predictions"]
        
        assert len(predictions) > 0
        assert len(predictions) <= 50  # Max 50 predictions
        
        # Validate prediction structure
        for pred in predictions:
            assert "id" in pred
            assert "timestamp" in pred
            assert "cve_id" in pred
            assert "confidence" in pred
            assert "predicted_success" in pred
            assert "time_saved_seconds" in pred
            assert "used_ml" in pred
            
            # Validate confidence range
            assert 0.0 <= pred["confidence"] <= 1.0
    
    def test_confusion_matrix_accuracy_calculation(self):
        """Confusion matrix should calculate accuracy correctly."""
        from api.ml_metrics import ConfusionMatrixData
        
        matrix = ConfusionMatrixData(
            true_positive=90,
            false_positive=10,
            false_negative=5,
            true_negative=45
        )
        
        # Accuracy = (TP + TN) / total = (90 + 45) / 150 = 0.9
        expected_accuracy = (90 + 45) / 150
        assert abs(matrix.accuracy - expected_accuracy) < 0.01
    
    def test_confusion_matrix_precision_calculation(self):
        """Confusion matrix should calculate precision correctly."""
        from api.ml_metrics import ConfusionMatrixData
        
        matrix = ConfusionMatrixData(
            true_positive=90,
            false_positive=10,
            false_negative=5,
            true_negative=45
        )
        
        # Precision = TP / (TP + FP) = 90 / (90 + 10) = 0.9
        expected_precision = 90 / (90 + 10)
        assert abs(matrix.precision - expected_precision) < 0.01
    
    def test_confusion_matrix_recall_calculation(self):
        """Confusion matrix should calculate recall correctly."""
        from api.ml_metrics import ConfusionMatrixData
        
        matrix = ConfusionMatrixData(
            true_positive=90,
            false_positive=10,
            false_negative=5,
            true_negative=45
        )
        
        # Recall = TP / (TP + FN) = 90 / (90 + 5) = 0.947
        expected_recall = 90 / (90 + 5)
        assert abs(matrix.recall - expected_recall) < 0.01
    
    def test_confusion_matrix_f1_score_calculation(self):
        """Confusion matrix should calculate F1 score correctly."""
        from api.ml_metrics import ConfusionMatrixData
        
        matrix = ConfusionMatrixData(
            true_positive=90,
            false_positive=10,
            false_negative=5,
            true_negative=45
        )
        
        precision = matrix.precision
        recall = matrix.recall
        expected_f1 = 2 * (precision * recall) / (precision + recall)
        
        assert abs(matrix.f1_score - expected_f1) < 0.01


class TestTimeframeEnum:
    """Tests for timeframe enum."""
    
    def test_timeframe_values(self):
        """Should contain all expected timeframe values."""
        assert TimeframeEnum.ONE_HOUR == "1h"
        assert TimeframeEnum.TWENTY_FOUR_HOURS == "24h"
        assert TimeframeEnum.SEVEN_DAYS == "7d"
        assert TimeframeEnum.THIRTY_DAYS == "30d"


class TestMLMetricsResponse:
    """Tests for MLMetricsResponse model."""
    
    def test_can_parse_example_data(self):
        """Should parse example data from schema."""
        from api.ml_metrics import MLMetricsResponse
        
        # Get example from schema
        example = MLMetricsResponse.model_config.get("json_schema_extra", {}).get("example", {})
        
        # Should be valid according to model
        if example:
            response = MLMetricsResponse(**example)
            assert response.timeframe == "24h"
            assert response.usage_breakdown.ml_usage_rate == 72.5
            assert response.avg_confidence == 0.84
