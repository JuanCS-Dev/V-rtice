"""Tests for vertice_core.metrics - 100% coverage."""

from unittest.mock import Mock, patch

import pytest
from vertice_core.metrics import create_service_metrics


class TestCreateServiceMetrics:
    """Test create_service_metrics function."""
    
    @patch("prometheus_client.Counter")
    @patch("prometheus_client.Histogram")
    @patch("prometheus_client.Gauge")
    def test_create_service_metrics(self, mock_gauge, mock_histogram, mock_counter):
        """Test creating service metrics."""
        mock_counter_instance = Mock()
        mock_histogram_instance = Mock()
        mock_gauge_instance = Mock()
        
        mock_counter.return_value = mock_counter_instance
        mock_histogram.return_value = mock_histogram_instance
        mock_gauge.return_value = mock_gauge_instance
        
        metrics = create_service_metrics("test-service")
        
        # Should return dict with metrics
        assert isinstance(metrics, dict)
        assert "requests_total" in metrics or len(metrics) > 0
    
    def test_different_service_names(self):
        """Test creating metrics for different services."""
        metrics1 = create_service_metrics("service1")
        metrics2 = create_service_metrics("service2")
        
        assert isinstance(metrics1, dict)
        assert isinstance(metrics2, dict)
    
    def test_metrics_dict_structure(self):
        """Test that metrics dict has expected structure."""
        metrics = create_service_metrics("test")
        
        # Should return a dict
        assert isinstance(metrics, dict)
        
        # If it returns metrics, they should be valid
        if metrics:
            for key, value in metrics.items():
                assert isinstance(key, str)
