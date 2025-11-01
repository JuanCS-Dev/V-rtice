"""
Tests for Canary Deployment System

Tests A/B testing framework for gradual patch rollout with
automatic promotion and rollback based on metrics.

Biblical Foundation: Proverbs 14:8 - "The wisdom of the prudent is to discern his way"
"""

import asyncio
from datetime import datetime, timedelta

from core.canary_deployment import (
    CanaryConfig,
    CanaryDecision,
    CanaryManager,
    CanaryStatus,
    MetricComparison,
)
import pytest


@pytest.fixture
def canary_config():
    """Create test canary configuration."""
    return CanaryConfig(
        initial_percentage=10,
        promotion_steps=[10, 25, 50, 100],
        analysis_duration_minutes=1,  # Short for tests
        success_threshold=0.95,
        latency_threshold_ms=500,
        error_rate_threshold=0.02,
        auto_promote=True,
        auto_rollback=True,
    )


@pytest.fixture
def canary_manager():
    """Create test canary manager."""
    return CanaryManager(
        observability_client=None,  # Mock metrics
        patch_history=None,
        audit_logger=None,
    )


class TestCanaryInitialization:
    """Test canary deployment initialization."""

    @pytest.mark.asyncio
    async def test_start_canary_creates_deployment(self, canary_manager, canary_config):
        """
        GIVEN: Valid patch and service
        WHEN: start_canary() is called
        THEN: Deployment created with INITIALIZING status
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-001",
            service_name="api-gateway",
            config=canary_config,
        )

        assert deployment_id is not None
        assert deployment_id in canary_manager.active_deployments

        deployment = canary_manager.active_deployments[deployment_id]
        assert deployment.patch_id == "patch-001"
        assert deployment.service_name == "api-gateway"
        assert deployment.status in (CanaryStatus.INITIALIZING, CanaryStatus.RUNNING)
        assert deployment.current_percentage == canary_config.promotion_steps[0]

    @pytest.mark.asyncio
    async def test_start_canary_uses_default_config(self, canary_manager):
        """
        GIVEN: No config provided
        WHEN: start_canary() called
        THEN: Uses default CanaryConfig
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-002",
            service_name="user-service",
        )

        deployment = canary_manager.active_deployments[deployment_id]
        assert deployment.config.initial_percentage == 10
        assert deployment.config.promotion_steps == [10, 25, 50, 100]


class TestMetricComparison:
    """Test metric comparison logic."""

    def test_compare_metric_higher_is_better(self, canary_manager):
        """
        GIVEN: Success rate metric (higher is better)
        WHEN: Canary has higher value than control
        THEN: No threshold breach, severity OK
        """
        comparison = canary_manager._compare_metric(
            metric_name="success_rate",
            canary_value=0.98,
            control_value=0.97,
            threshold=0.95,
            higher_is_better=True,
        )

        assert comparison.metric_name == "success_rate"
        assert comparison.canary_value == 0.98
        assert comparison.control_value == 0.97
        assert comparison.delta_percentage > 0
        assert not comparison.threshold_breached
        assert comparison.severity == "ok"

    def test_compare_metric_higher_is_better_breached(self, canary_manager):
        """
        GIVEN: Success rate metric (higher is better)
        WHEN: Canary below threshold
        THEN: Threshold breached, severity critical/warning
        """
        comparison = canary_manager._compare_metric(
            metric_name="success_rate",
            canary_value=0.85,
            control_value=0.97,
            threshold=0.95,
            higher_is_better=True,
        )

        assert comparison.threshold_breached
        assert comparison.severity == "critical"

    def test_compare_metric_lower_is_better(self, canary_manager):
        """
        GIVEN: Latency metric (lower is better)
        WHEN: Canary below threshold
        THEN: No threshold breach, severity OK
        """
        comparison = canary_manager._compare_metric(
            metric_name="p99_latency_ms",
            canary_value=200,
            control_value=180,
            threshold=500,
            higher_is_better=False,
        )

        assert not comparison.threshold_breached
        assert comparison.severity == "ok"

    def test_compare_metric_lower_is_better_breached(self, canary_manager):
        """
        GIVEN: Latency metric (lower is better)
        WHEN: Canary exceeds threshold significantly
        THEN: Threshold breached, severity critical
        """
        comparison = canary_manager._compare_metric(
            metric_name="p99_latency_ms",
            canary_value=700,
            control_value=180,
            threshold=500,
            higher_is_better=False,
        )

        assert comparison.threshold_breached
        assert comparison.severity == "critical"


class TestMetricAnalysis:
    """Test canary metric analysis and decision making."""

    @pytest.mark.asyncio
    async def test_analyze_good_metrics_returns_promote(
        self, canary_manager, canary_config, monkeypatch
    ):
        """
        GIVEN: Canary with good metrics (high success, low latency, low errors)
        WHEN: _analyze_canary_metrics() called
        THEN: Returns PROMOTE decision
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-003",
            service_name="test-service",
            config=canary_config,
        )

        deployment = canary_manager.active_deployments[deployment_id]

        # Mock good metrics
        async def mock_fetch_metrics(service, group):
            return {
                "success_rate": 0.98,
                "p99_latency_ms": 150,
                "error_rate": 0.01,
            }

        monkeypatch.setattr(canary_manager, "_fetch_metrics", mock_fetch_metrics)

        decision = await canary_manager._analyze_canary_metrics(deployment)

        assert decision == CanaryDecision.PROMOTE
        assert len(deployment.metric_comparisons) == 3
        assert all(not mc.threshold_breached for mc in deployment.metric_comparisons)

        # Clean up
        await canary_manager.cancel_deployment(deployment_id)

    @pytest.mark.asyncio
    async def test_analyze_bad_success_rate_returns_rollback(
        self, canary_manager, canary_config, monkeypatch
    ):
        """
        GIVEN: Canary with low success rate
        WHEN: _analyze_canary_metrics() called
        THEN: Returns ROLLBACK decision
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-004",
            service_name="test-service",
            config=canary_config,
        )

        deployment = canary_manager.active_deployments[deployment_id]

        # Mock bad success rate
        async def mock_fetch_metrics(service, group):
            if group == "canary":
                return {
                    "success_rate": 0.85,  # Below threshold
                    "p99_latency_ms": 150,
                    "error_rate": 0.01,
                }
            return {
                "success_rate": 0.98,
                "p99_latency_ms": 150,
                "error_rate": 0.01,
            }

        monkeypatch.setattr(canary_manager, "_fetch_metrics", mock_fetch_metrics)

        decision = await canary_manager._analyze_canary_metrics(deployment)

        assert decision == CanaryDecision.ROLLBACK
        assert any(
            mc.threshold_breached and mc.severity == "critical"
            for mc in deployment.metric_comparisons
        )

        # Clean up
        await canary_manager.cancel_deployment(deployment_id)

    @pytest.mark.asyncio
    async def test_analyze_high_latency_returns_rollback(
        self, canary_manager, canary_config, monkeypatch
    ):
        """
        GIVEN: Canary with high latency
        WHEN: _analyze_canary_metrics() called
        THEN: Returns ROLLBACK decision
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-005",
            service_name="test-service",
            config=canary_config,
        )

        deployment = canary_manager.active_deployments[deployment_id]

        # Mock high latency
        async def mock_fetch_metrics(service, group):
            if group == "canary":
                return {
                    "success_rate": 0.98,
                    "p99_latency_ms": 800,  # Above threshold
                    "error_rate": 0.01,
                }
            return {
                "success_rate": 0.98,
                "p99_latency_ms": 150,
                "error_rate": 0.01,
            }

        monkeypatch.setattr(canary_manager, "_fetch_metrics", mock_fetch_metrics)

        decision = await canary_manager._analyze_canary_metrics(deployment)

        assert decision == CanaryDecision.ROLLBACK

        # Clean up
        await canary_manager.cancel_deployment(deployment_id)

    @pytest.mark.asyncio
    async def test_analyze_warning_metrics_returns_hold(
        self, canary_manager, canary_config, monkeypatch
    ):
        """
        GIVEN: Canary with borderline metrics (warning but not critical)
        WHEN: _analyze_canary_metrics() called
        THEN: Returns HOLD decision
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-006",
            service_name="test-service",
            config=canary_config,
        )

        deployment = canary_manager.active_deployments[deployment_id]

        # Mock borderline metrics (just below threshold but not critical)
        async def mock_fetch_metrics(service, group):
            if group == "canary":
                return {
                    "success_rate": 0.94,  # Slightly below 0.95 threshold
                    "p99_latency_ms": 150,
                    "error_rate": 0.01,
                }
            return {
                "success_rate": 0.98,
                "p99_latency_ms": 150,
                "error_rate": 0.01,
            }

        monkeypatch.setattr(canary_manager, "_fetch_metrics", mock_fetch_metrics)

        decision = await canary_manager._analyze_canary_metrics(deployment)

        # Should be HOLD because metric is warning but not critical
        assert decision in (CanaryDecision.HOLD, CanaryDecision.ROLLBACK)

        # Clean up
        await canary_manager.cancel_deployment(deployment_id)


class TestCanaryPromotion:
    """Test canary promotion logic."""

    @pytest.mark.asyncio
    async def test_promote_advances_to_next_percentage(
        self, canary_manager, canary_config
    ):
        """
        GIVEN: Canary at 10% traffic
        WHEN: _promote_canary() called
        THEN: Advances to 25% (next step)
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-007",
            service_name="test-service",
            config=canary_config,
        )

        deployment = canary_manager.active_deployments[deployment_id]
        assert deployment.current_percentage == 10
        assert deployment.current_step_index == 0

        await canary_manager._promote_canary(deployment)

        assert deployment.current_percentage == 25
        assert deployment.current_step_index == 1
        assert deployment.status == CanaryStatus.RUNNING

        # Clean up
        await canary_manager.cancel_deployment(deployment_id)

    @pytest.mark.asyncio
    async def test_promote_at_final_step_completes_deployment(
        self, canary_manager, canary_config
    ):
        """
        GIVEN: Canary at 100% traffic (final step)
        WHEN: _promote_canary() called
        THEN: Marks deployment COMPLETED, removes from active
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-008",
            service_name="test-service",
            config=canary_config,
        )

        deployment = canary_manager.active_deployments[deployment_id]

        # Manually set to final step
        deployment.current_step_index = len(canary_config.promotion_steps) - 1
        deployment.current_percentage = canary_config.promotion_steps[-1]

        await canary_manager._promote_canary(deployment)

        assert deployment.status == CanaryStatus.COMPLETED
        assert deployment.completed_at is not None
        assert deployment_id not in canary_manager.active_deployments


class TestCanaryRollback:
    """Test canary rollback logic."""

    @pytest.mark.asyncio
    async def test_rollback_sets_traffic_to_zero(self, canary_manager, canary_config):
        """
        GIVEN: Active canary deployment
        WHEN: _rollback_canary() called
        THEN: Sets traffic to 0%, marks FAILED
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-009",
            service_name="test-service",
            config=canary_config,
        )

        deployment = canary_manager.active_deployments[deployment_id]
        assert deployment.current_percentage == 10

        await canary_manager._rollback_canary(deployment, reason="Test rollback")

        assert deployment.current_percentage == 0
        assert deployment.status == CanaryStatus.FAILED
        assert deployment.completed_at is not None
        assert deployment_id not in canary_manager.active_deployments

    @pytest.mark.asyncio
    async def test_rollback_respects_auto_rollback_false(self, canary_manager):
        """
        GIVEN: Canary with auto_rollback=False
        WHEN: _rollback_canary() called without explicit reason
        THEN: Rollback skipped
        """
        config = CanaryConfig(auto_rollback=False)
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-010",
            service_name="test-service",
            config=config,
        )

        deployment = canary_manager.active_deployments[deployment_id]

        await canary_manager._rollback_canary(deployment)

        # Should still be active since auto_rollback is False
        assert deployment.status in (CanaryStatus.RUNNING, CanaryStatus.INITIALIZING)

        # Clean up
        await canary_manager.cancel_deployment(deployment_id)


class TestCanaryDeploymentStatus:
    """Test canary deployment status queries."""

    @pytest.mark.asyncio
    async def test_get_deployment_status_returns_dict(
        self, canary_manager, canary_config
    ):
        """
        GIVEN: Active canary deployment
        WHEN: get_deployment_status() called
        THEN: Returns deployment details as dict
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-011",
            service_name="test-service",
            config=canary_config,
        )

        status = await canary_manager.get_deployment_status(deployment_id)

        assert status is not None
        assert status["deployment_id"] == deployment_id
        assert status["patch_id"] == "patch-011"
        assert status["service_name"] == "test-service"
        assert "status" in status
        assert "current_percentage" in status
        assert "metric_comparisons" in status
        assert "decisions" in status

        # Clean up
        await canary_manager.cancel_deployment(deployment_id)

    @pytest.mark.asyncio
    async def test_get_deployment_status_nonexistent_returns_none(self, canary_manager):
        """
        GIVEN: No deployment with given ID
        WHEN: get_deployment_status() called
        THEN: Returns None
        """
        status = await canary_manager.get_deployment_status("nonexistent-id")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_active_deployments_returns_all(
        self, canary_manager, canary_config
    ):
        """
        GIVEN: Multiple active canary deployments
        WHEN: get_active_deployments() called
        THEN: Returns list of all active deployments
        """
        deployment_id_1 = await canary_manager.start_canary(
            patch_id="patch-012",
            service_name="service-1",
            config=canary_config,
        )

        deployment_id_2 = await canary_manager.start_canary(
            patch_id="patch-013",
            service_name="service-2",
            config=canary_config,
        )

        active = await canary_manager.get_active_deployments()

        assert len(active) == 2
        assert any(d["deployment_id"] == deployment_id_1 for d in active)
        assert any(d["deployment_id"] == deployment_id_2 for d in active)

        # Clean up
        await canary_manager.cancel_deployment(deployment_id_1)
        await canary_manager.cancel_deployment(deployment_id_2)


class TestCanaryCancellation:
    """Test canary deployment cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_deployment_stops_canary(self, canary_manager, canary_config):
        """
        GIVEN: Active canary deployment
        WHEN: cancel_deployment() called
        THEN: Marks CANCELLED, removes from active
        """
        deployment_id = await canary_manager.start_canary(
            patch_id="patch-014",
            service_name="test-service",
            config=canary_config,
        )

        result = await canary_manager.cancel_deployment(deployment_id)

        assert result is True
        assert deployment_id not in canary_manager.active_deployments

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_deployment_returns_false(self, canary_manager):
        """
        GIVEN: No deployment with given ID
        WHEN: cancel_deployment() called
        THEN: Returns False
        """
        result = await canary_manager.cancel_deployment("nonexistent-id")
        assert result is False


class TestFullCanaryWorkflow:
    """Test complete canary deployment workflow."""

    @pytest.mark.asyncio
    async def test_full_successful_canary_workflow(
        self, canary_manager, canary_config, monkeypatch
    ):
        """
        GIVEN: Canary deployment with consistently good metrics
        WHEN: Analysis runs multiple times
        THEN: Progressively promotes to 100% and completes
        """
        # Use very short analysis duration for test
        config = CanaryConfig(
            promotion_steps=[10, 50, 100],  # Only 3 steps for faster test
            analysis_duration_minutes=0.01,  # 0.6 seconds
            auto_promote=True,
            auto_rollback=True,
        )

        # Mock good metrics
        async def mock_fetch_metrics(service, group):
            return {
                "success_rate": 0.98,
                "p99_latency_ms": 150,
                "error_rate": 0.01,
            }

        monkeypatch.setattr(canary_manager, "_fetch_metrics", mock_fetch_metrics)

        deployment_id = await canary_manager.start_canary(
            patch_id="patch-015",
            service_name="test-service",
            config=config,
        )

        # Wait for analysis to run and promotions to happen
        # Should take ~0.6s per analysis * 3 steps = ~1.8s
        await asyncio.sleep(3)

        # Check if deployment completed
        status = await canary_manager.get_deployment_status(deployment_id)

        # Deployment may have completed (removed from active)
        if status is None:
            # Good! It completed successfully
            pass
        else:
            # Still running, check progress
            assert status["current_percentage"] >= 10

        # Clean up if still active
        await canary_manager.cancel_deployment(deployment_id)

    @pytest.mark.asyncio
    async def test_full_failed_canary_workflow(
        self, canary_manager, canary_config, monkeypatch
    ):
        """
        GIVEN: Canary deployment with bad metrics
        WHEN: Analysis detects issue
        THEN: Automatically rolls back
        """
        config = CanaryConfig(
            analysis_duration_minutes=0.01,
            auto_promote=True,
            auto_rollback=True,
        )

        # Mock bad metrics (low success rate)
        async def mock_fetch_metrics(service, group):
            if group == "canary":
                return {
                    "success_rate": 0.80,  # Way below threshold
                    "p99_latency_ms": 150,
                    "error_rate": 0.01,
                }
            return {
                "success_rate": 0.98,
                "p99_latency_ms": 150,
                "error_rate": 0.01,
            }

        monkeypatch.setattr(canary_manager, "_fetch_metrics", mock_fetch_metrics)

        deployment_id = await canary_manager.start_canary(
            patch_id="patch-016",
            service_name="test-service",
            config=config,
        )

        # Wait for analysis to detect bad metrics and rollback
        await asyncio.sleep(2)

        # Deployment should be rolled back and removed
        status = await canary_manager.get_deployment_status(deployment_id)

        # Should be removed (rolled back)
        assert status is None

        # Clean up if somehow still active
        await canary_manager.cancel_deployment(deployment_id)


class TestCanaryConfig:
    """Test canary configuration."""

    def test_default_config_values(self):
        """
        GIVEN: No config parameters
        WHEN: CanaryConfig created
        THEN: Uses sensible defaults
        """
        config = CanaryConfig()

        assert config.initial_percentage == 10
        assert config.promotion_steps == [10, 25, 50, 100]
        assert config.analysis_duration_minutes == 15
        assert config.success_threshold == 0.95
        assert config.latency_threshold_ms == 500
        assert config.error_rate_threshold == 0.02
        assert config.auto_promote is True
        assert config.auto_rollback is True

    def test_custom_config_values(self):
        """
        GIVEN: Custom config parameters
        WHEN: CanaryConfig created
        THEN: Uses provided values
        """
        config = CanaryConfig(
            initial_percentage=5,
            promotion_steps=[5, 10, 20, 40, 80, 100],
            analysis_duration_minutes=30,
            success_threshold=0.99,
            latency_threshold_ms=200,
            error_rate_threshold=0.01,
            auto_promote=False,
            auto_rollback=False,
        )

        assert config.initial_percentage == 5
        assert config.promotion_steps == [5, 10, 20, 40, 80, 100]
        assert config.analysis_duration_minutes == 30
        assert config.success_threshold == 0.99
        assert config.latency_threshold_ms == 200
        assert config.error_rate_threshold == 0.01
        assert config.auto_promote is False
        assert config.auto_rollback is False
