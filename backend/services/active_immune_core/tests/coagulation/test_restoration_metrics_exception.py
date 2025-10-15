"""Test Prometheus metrics exception handling in restoration.py

Target: Lines 140-152 - ValueError exception handling for duplicate metrics
"""

import pytest
from prometheus_client import Counter, REGISTRY
from coagulation.restoration import RestorationMetrics


class TestRestorationMetricsException:
    """Test Prometheus metrics exception handling (lines 140-152)"""

    def test_metrics_already_registered_exception_handling(self):
        """Lines 140-152: Handle ValueError when metrics already registered"""

        # Reset class-level metrics to force re-creation
        RestorationMetrics._restorations_total = None
        RestorationMetrics._restoration_duration = None
        RestorationMetrics._assets_restored = None
        RestorationMetrics._rollbacks_total = None

        # First instantiation should succeed (creates metrics)
        metrics1 = RestorationMetrics()
        assert metrics1.restorations_total is not None
        assert metrics1.restoration_duration is not None
        assert metrics1.assets_restored is not None
        assert metrics1.rollbacks_total is not None

        # Now reset the class-level metrics again to force the ValueError path
        # This simulates the case where metrics are in REGISTRY but class vars are None
        RestorationMetrics._restorations_total = None
        RestorationMetrics._restoration_duration = None
        RestorationMetrics._assets_restored = None
        RestorationMetrics._rollbacks_total = None

        # Second instantiation should trigger ValueError (metrics already in REGISTRY)
        # and execute the exception handling code (lines 140-152)
        metrics2 = RestorationMetrics()

        # Should successfully retrieve existing metrics from REGISTRY (lines 142-152)
        assert metrics2.restorations_total is not None
        assert metrics2.restoration_duration is not None
        assert metrics2.assets_restored is not None
        assert metrics2.rollbacks_total is not None

    def test_metrics_singleton_pattern(self):
        """Verify metrics singleton pattern works across multiple instantiations"""

        # Create multiple instances
        m1 = RestorationMetrics()
        m2 = RestorationMetrics()
        m3 = RestorationMetrics()

        # All should share the same class-level metrics
        assert m1.restorations_total is m2.restorations_total
        assert m2.restorations_total is m3.restorations_total

        # Verify all metrics are not None
        assert m1.restorations_total is not None
        assert m1.restoration_duration is not None
        assert m1.assets_restored is not None
        assert m1.rollbacks_total is not None

    def test_metrics_retrieval_from_registry(self):
        """Lines 142-152: Test retrieval of existing metrics from REGISTRY"""

        # Ensure metrics exist
        metrics = RestorationMetrics()

        # Verify metrics are in REGISTRY by checking they're not None
        # The exception path (lines 140-152) is triggered when metrics already exist
        # and are retrieved from REGISTRY
        assert metrics.restorations_total is not None
        assert metrics.restoration_duration is not None
        assert metrics.assets_restored is not None
        assert metrics.rollbacks_total is not None

        # Create another instance - should use existing metrics
        metrics2 = RestorationMetrics()
        assert metrics2.restorations_total is metrics.restorations_total
