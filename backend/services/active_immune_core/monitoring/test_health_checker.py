"""Tests for HealthChecker - PRODUCTION-READY

Comprehensive test suite with 35+ tests covering all functionality.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
from datetime import datetime

import pytest

from monitoring.health_checker import (
    ComponentHealth,
    HealthChecker,
    HealthStatus,
)


@pytest.fixture
def health_checker():
    """Create fresh HealthChecker for each test"""
    return HealthChecker(check_interval=1, failure_threshold=3, enable_auto_check=False)


@pytest.fixture
async def async_health_checker():
    """Create HealthChecker for async tests"""
    checker = HealthChecker(check_interval=1, enable_auto_check=False)
    yield checker
    # Cleanup
    await checker.stop_auto_check()


class TestHealthStatus:
    """Test HealthStatus enum"""

    def test_health_status_values(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestComponentHealth:
    """Test ComponentHealth class"""

    def test_init(self):
        """Test ComponentHealth initialization"""
        comp = ComponentHealth("test_component")
        assert comp.name == "test_component"
        assert comp.status == HealthStatus.UNKNOWN
        assert comp.consecutive_failures == 0
        assert comp.total_checks == 0
        assert comp.total_failures == 0
        assert len(comp.history) == 0

    def test_init_with_check_func(self):
        """Test ComponentHealth with check function"""

        async def check():
            return HealthStatus.HEALTHY, {"detail": "ok"}

        comp = ComponentHealth("test", check_func=check)
        assert comp.check_func is not None

    @pytest.mark.asyncio
    async def test_check_no_func(self):
        """Test check with no check function"""
        comp = ComponentHealth("test")
        status = await comp.check()
        assert status == HealthStatus.HEALTHY
        assert comp.total_checks == 1

    @pytest.mark.asyncio
    async def test_check_healthy(self):
        """Test check returning healthy"""

        async def check():
            return HealthStatus.HEALTHY, {"detail": "all good"}

        comp = ComponentHealth("test", check_func=check)
        status = await comp.check()

        assert status == HealthStatus.HEALTHY
        assert comp.total_checks == 1
        assert comp.total_failures == 0
        assert comp.consecutive_failures == 0
        assert comp.last_healthy is not None

    @pytest.mark.asyncio
    async def test_check_unhealthy(self):
        """Test check returning unhealthy"""

        async def check():
            return HealthStatus.UNHEALTHY, {"detail": "problem"}

        comp = ComponentHealth("test", check_func=check)
        status = await comp.check()

        assert status == HealthStatus.UNHEALTHY
        assert comp.total_checks == 1
        assert comp.total_failures == 1
        assert comp.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_check_exception(self):
        """Test check function raising exception"""

        async def check():
            raise ValueError("Test error")

        comp = ComponentHealth("test", check_func=check)
        status = await comp.check()

        assert status == HealthStatus.UNHEALTHY
        assert "error" in comp.details
        assert comp.total_failures == 1

    @pytest.mark.asyncio
    async def test_consecutive_failures(self):
        """Test consecutive failures counter"""

        async def check():
            return HealthStatus.UNHEALTHY

        comp = ComponentHealth("test", check_func=check)

        await comp.check()
        assert comp.consecutive_failures == 1

        await comp.check()
        assert comp.consecutive_failures == 2

        await comp.check()
        assert comp.consecutive_failures == 3

    @pytest.mark.asyncio
    async def test_consecutive_failures_reset(self):
        """Test consecutive failures reset on success"""
        call_count = 0

        async def check():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return HealthStatus.UNHEALTHY
            return HealthStatus.HEALTHY

        comp = ComponentHealth("test", check_func=check)

        await comp.check()
        assert comp.consecutive_failures == 1

        await comp.check()
        assert comp.consecutive_failures == 2

        await comp.check()
        assert comp.consecutive_failures == 0

    def test_get_failure_rate_zero(self):
        """Test failure rate with no checks"""
        comp = ComponentHealth("test")
        assert comp.get_failure_rate() == 0.0

    @pytest.mark.asyncio
    async def test_get_failure_rate(self):
        """Test failure rate calculation"""
        call_count = 0

        async def check():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return HealthStatus.UNHEALTHY
            return HealthStatus.HEALTHY

        comp = ComponentHealth("test", check_func=check)

        # 3 failures
        await comp.check()
        await comp.check()
        await comp.check()

        assert comp.get_failure_rate() == 1.0  # 3/3

        # 1 success
        await comp.check()
        assert comp.get_failure_rate() == 0.75  # 3/4

    def test_time_since_healthy_none(self):
        """Test time since healthy when never healthy"""
        comp = ComponentHealth("test")
        assert comp.time_since_healthy() is None

    @pytest.mark.asyncio
    async def test_time_since_healthy(self):
        """Test time since healthy calculation"""

        async def check():
            return HealthStatus.HEALTHY

        comp = ComponentHealth("test", check_func=check)
        await comp.check()

        await asyncio.sleep(0.1)

        time_since = comp.time_since_healthy()
        assert time_since is not None
        assert time_since >= 0.1

    def test_to_dict(self):
        """Test converting component to dict"""
        comp = ComponentHealth("test")
        comp.status = HealthStatus.HEALTHY
        comp.details = {"info": "test"}
        comp.total_checks = 5
        comp.total_failures = 1

        data = comp.to_dict()

        assert data["name"] == "test"
        assert data["status"] == "healthy"
        assert data["details"] == {"info": "test"}
        assert data["consecutive_failures"] == 0
        assert data["failure_rate"] == 0.2

    @pytest.mark.asyncio
    async def test_history_tracking(self):
        """Test health status history tracking"""

        async def check():
            return HealthStatus.HEALTHY

        comp = ComponentHealth("test", check_func=check)
        comp.max_history = 5

        # Add some checks
        for _ in range(10):
            await comp.check()

        # Should only keep last 5
        assert len(comp.history) == 5


class TestHealthCheckerInit:
    """Test HealthChecker initialization"""

    def test_init_defaults(self):
        """Test HealthChecker with default parameters"""
        checker = HealthChecker()
        assert checker.check_interval == 30
        assert checker.failure_threshold == 3
        assert checker.enable_auto_check is False
        assert len(checker._components) == 0

    def test_init_custom_params(self):
        """Test HealthChecker with custom parameters"""
        checker = HealthChecker(check_interval=60, failure_threshold=5, enable_auto_check=True)
        assert checker.check_interval == 60
        assert checker.failure_threshold == 5
        assert checker.enable_auto_check is True


class TestComponentRegistration:
    """Test component registration"""

    def test_register_component(self, health_checker):
        """Test registering component"""
        comp = health_checker.register_component("test_component")
        assert comp.name == "test_component"
        assert "test_component" in health_checker._components

    def test_register_component_with_check_func(self, health_checker):
        """Test registering component with check function"""

        async def check():
            return HealthStatus.HEALTHY

        comp = health_checker.register_component("test", check_func=check)
        assert comp.check_func is not None

    def test_register_multiple_components(self, health_checker):
        """Test registering multiple components"""
        health_checker.register_component("comp1")
        health_checker.register_component("comp2")
        health_checker.register_component("comp3")

        assert len(health_checker._components) == 3

    def test_unregister_component(self, health_checker):
        """Test unregistering component"""
        health_checker.register_component("test")
        assert "test" in health_checker._components

        result = health_checker.unregister_component("test")
        assert result is True
        assert "test" not in health_checker._components

    def test_unregister_nonexistent_component(self, health_checker):
        """Test unregistering non-existent component"""
        result = health_checker.unregister_component("nonexistent")
        assert result is False

    def test_get_component(self, health_checker):
        """Test getting component"""
        health_checker.register_component("test")
        comp = health_checker.get_component("test")
        assert comp is not None
        assert comp.name == "test"

    def test_get_nonexistent_component(self, health_checker):
        """Test getting non-existent component"""
        comp = health_checker.get_component("nonexistent")
        assert comp is None


class TestComponentChecks:
    """Test component health checks"""

    @pytest.mark.asyncio
    async def test_check_component(self, health_checker):
        """Test checking specific component"""
        health_checker.register_component("test")
        status = await health_checker.check_component("test")
        assert status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_nonexistent_component(self, health_checker):
        """Test checking non-existent component"""
        status = await health_checker.check_component("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_check_all_components_empty(self, health_checker):
        """Test checking all components with none registered"""
        components = await health_checker.check_all_components()
        assert len(components) == 0

    @pytest.mark.asyncio
    async def test_check_all_components(self, health_checker):
        """Test checking all components"""
        health_checker.register_component("comp1")
        health_checker.register_component("comp2")
        health_checker.register_component("comp3")

        components = await health_checker.check_all_components()
        assert len(components) == 3

        for comp in components.values():
            assert comp.total_checks == 1

    @pytest.mark.asyncio
    async def test_check_all_components_parallel(self, health_checker):
        """Test that all components are checked in parallel"""
        check_times = []

        async def slow_check():
            start = datetime.now()
            await asyncio.sleep(0.1)
            check_times.append(datetime.now() - start)
            return HealthStatus.HEALTHY

        for i in range(5):
            health_checker.register_component(f"comp{i}", check_func=slow_check)

        start_time = datetime.now()
        await health_checker.check_all_components()
        total_time = (datetime.now() - start_time).total_seconds()

        # Should be ~0.1s (parallel), not ~0.5s (sequential)
        assert total_time < 0.3


class TestHealthCheck:
    """Test overall health check"""

    @pytest.mark.asyncio
    async def test_check_health_no_components(self, health_checker):
        """Test health check with no components"""
        report = await health_checker.check_health()

        assert report["status"] == "unknown"
        assert report["summary"]["total_components"] == 0

    @pytest.mark.asyncio
    async def test_check_health_all_healthy(self, health_checker):
        """Test health check with all components healthy"""
        for i in range(3):
            health_checker.register_component(f"comp{i}")

        report = await health_checker.check_health()

        assert report["status"] == "healthy"
        assert report["summary"]["healthy"] == 3
        assert report["summary"]["total_components"] == 3

    @pytest.mark.asyncio
    async def test_check_health_some_degraded(self, health_checker):
        """Test health check with some degraded components"""

        async def healthy():
            return HealthStatus.HEALTHY

        async def degraded():
            return HealthStatus.DEGRADED

        health_checker.register_component("comp1", check_func=healthy)
        health_checker.register_component("comp2", check_func=degraded)

        report = await health_checker.check_health()

        assert report["status"] == "degraded"
        assert report["summary"]["healthy"] == 1
        assert report["summary"]["degraded"] == 1

    @pytest.mark.asyncio
    async def test_check_health_some_unhealthy(self, health_checker):
        """Test health check with some unhealthy components"""

        async def healthy():
            return HealthStatus.HEALTHY

        async def unhealthy():
            return HealthStatus.UNHEALTHY

        health_checker.register_component("comp1", check_func=healthy)
        health_checker.register_component("comp2", check_func=unhealthy)

        report = await health_checker.check_health()

        assert report["status"] == "unhealthy"
        assert report["summary"]["healthy"] == 1
        assert report["summary"]["unhealthy"] == 1

    @pytest.mark.asyncio
    async def test_check_health_includes_timestamp(self, health_checker):
        """Test that health check includes timestamp"""
        health_checker.register_component("test")
        report = await health_checker.check_health()

        assert "timestamp" in report
        # Should be valid ISO format
        datetime.fromisoformat(report["timestamp"])

    @pytest.mark.asyncio
    async def test_check_health_includes_components(self, health_checker):
        """Test that health check includes component details"""
        health_checker.register_component("test")
        report = await health_checker.check_health()

        assert "components" in report
        assert "test" in report["components"]
        assert report["components"]["test"]["name"] == "test"


class TestReadinessCheck:
    """Test readiness check"""

    @pytest.mark.asyncio
    async def test_check_readiness_no_critical_components(self, health_checker):
        """Test readiness check with no critical components"""
        report = await health_checker.check_readiness()

        assert report["ready"] is False
        assert "not registered" in str(report["reasons"])

    @pytest.mark.asyncio
    async def test_check_readiness_all_healthy(self, health_checker):
        """Test readiness check with all critical components healthy"""
        # Register critical components
        health_checker.register_component("agents")
        health_checker.register_component("coordination")
        health_checker.register_component("infrastructure")

        report = await health_checker.check_readiness()

        # Should be ready (all components healthy by default)
        assert report["ready"] is True

    @pytest.mark.asyncio
    async def test_check_readiness_critical_unhealthy(self, health_checker):
        """Test readiness check with critical component unhealthy"""

        async def unhealthy():
            return HealthStatus.UNHEALTHY

        health_checker.register_component("agents", check_func=unhealthy)
        health_checker.register_component("coordination")
        health_checker.register_component("infrastructure")

        report = await health_checker.check_readiness()

        assert report["ready"] is False
        assert any("agents" in str(reason) for reason in report["reasons"])

    @pytest.mark.asyncio
    async def test_check_readiness_includes_critical_components(self, health_checker):
        """Test that readiness check includes critical component list"""
        report = await health_checker.check_readiness()

        assert "critical_components" in report
        assert "agents" in report["critical_components"]
        assert "coordination" in report["critical_components"]
        assert "infrastructure" in report["critical_components"]


class TestAutoCheck:
    """Test automatic health checking"""

    @pytest.mark.asyncio
    async def test_start_auto_check_not_enabled(self, health_checker):
        """Test starting auto-check when not enabled"""
        await health_checker.start_auto_check()
        assert health_checker._running is False

    @pytest.mark.asyncio
    async def test_start_auto_check_enabled(self):
        """Test starting auto-check when enabled"""
        checker = HealthChecker(check_interval=1, enable_auto_check=True)
        checker.register_component("test")

        await checker.start_auto_check()
        assert checker._running is True

        # Let it run for a bit
        await asyncio.sleep(0.5)

        # Stop it
        await checker.stop_auto_check()
        assert checker._running is False

    @pytest.mark.asyncio
    async def test_start_auto_check_already_running(self):
        """Test starting auto-check when already running"""
        checker = HealthChecker(check_interval=1, enable_auto_check=True)

        await checker.start_auto_check()
        assert checker._running is True

        # Try to start again
        await checker.start_auto_check()
        assert checker._running is True  # Should still be running

        await checker.stop_auto_check()

    @pytest.mark.asyncio
    async def test_stop_auto_check(self):
        """Test stopping auto-check"""
        checker = HealthChecker(check_interval=1, enable_auto_check=True)

        await checker.start_auto_check()
        assert checker._running is True

        await checker.stop_auto_check()
        assert checker._running is False

    @pytest.mark.asyncio
    async def test_auto_check_performs_checks(self):
        """Test that auto-check actually performs checks"""
        checker = HealthChecker(check_interval=0.1, enable_auto_check=True)
        comp = checker.register_component("test")

        await checker.start_auto_check()

        # Wait for a few checks
        await asyncio.sleep(0.3)

        await checker.stop_auto_check()

        # Should have performed multiple checks
        assert comp.total_checks >= 2


class TestHealthSummary:
    """Test health summary"""

    def test_get_health_summary_empty(self, health_checker):
        """Test health summary with no components"""
        summary = health_checker.get_health_summary()

        assert summary["total_components"] == 0
        assert len(summary["components_status"]) == 0

    def test_get_health_summary(self, health_checker):
        """Test health summary with components"""
        comp1 = health_checker.register_component("comp1")
        comp2 = health_checker.register_component("comp2")

        comp1.status = HealthStatus.HEALTHY
        comp2.status = HealthStatus.DEGRADED

        summary = health_checker.get_health_summary()

        assert summary["total_components"] == 2
        assert summary["components_status"]["comp1"] == "healthy"
        assert summary["components_status"]["comp2"] == "degraded"


class TestRepr:
    """Test string representation"""

    def test_repr(self, health_checker):
        """Test repr string"""
        health_checker.register_component("test1")
        health_checker.register_component("test2")

        repr_str = repr(health_checker)

        assert "HealthChecker" in repr_str
        assert "components=2" in repr_str


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_check_function_timeout(self, health_checker):
        """Test check function that times out"""

        async def slow_check():
            await asyncio.sleep(10)
            return HealthStatus.HEALTHY

        health_checker.register_component("slow", check_func=slow_check)

        # Check with timeout
        try:
            await asyncio.wait_for(health_checker.check_component("slow"), timeout=0.1)
        except asyncio.TimeoutError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_check_function_returns_invalid(self, health_checker):
        """Test check function returning invalid data"""

        async def invalid_check():
            return "invalid"

        comp = health_checker.register_component("invalid", check_func=invalid_check)
        status = await comp.check()

        # Should handle gracefully (set as returned value)
        assert status == "invalid"

    @pytest.mark.asyncio
    async def test_concurrent_component_access(self, health_checker):
        """Test concurrent access to components"""
        health_checker.register_component("test")

        # Run multiple checks concurrently
        await asyncio.gather(
            health_checker.check_component("test"),
            health_checker.check_component("test"),
            health_checker.check_component("test"),
        )

        comp = health_checker.get_component("test")
        assert comp.total_checks == 3
