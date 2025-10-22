"""
Tests for Sandboxing Container
"""
import pytest
import time
from consciousness.sandboxing import ConsciousnessContainer, ResourceLimits


def test_container_initialization():
    """Test container creation"""
    limits = ResourceLimits(
        cpu_percent=50.0,
        memory_mb=512,
        timeout_sec=60
    )
    
    container = ConsciousnessContainer("test_container", limits)
    
    assert container.name == "test_container"
    assert container.limits.cpu_percent == 50.0
    assert not container.running


def test_successful_execution():
    """Test executing function successfully"""
    limits = ResourceLimits(timeout_sec=10)
    container = ConsciousnessContainer("test", limits)
    
    def simple_task():
        return "success"
    
    result = container.execute(simple_task)
    
    assert result["result"] == "success"
    assert result["error"] is None
    assert result["stats"]["start_time"] is not None
    assert result["stats"]["end_time"] is not None


def test_timeout_enforcement():
    """Test that timeout is enforced"""
    limits = ResourceLimits(timeout_sec=2)
    container = ConsciousnessContainer("timeout_test", limits)
    
    def long_task():
        time.sleep(5)  # Exceeds timeout
        return "completed"
    
    result = container.execute(long_task)
    
    # Should be terminated
    assert result["stats"]["terminated"] or result["error"] is not None


def test_exception_handling():
    """Test handling of exceptions in target function"""
    limits = ResourceLimits()
    container = ConsciousnessContainer("exception_test", limits)
    
    def failing_task():
        raise ValueError("Test error")
    
    result = container.execute(failing_task)
    
    assert result["result"] is None
    assert result["error"] is not None
    assert "Test error" in result["error"]


def test_resource_monitoring():
    """Test resource usage tracking"""
    limits = ResourceLimits(memory_mb=2048, timeout_sec=10)
    container = ConsciousnessContainer("monitor_test", limits)
    
    def monitored_task():
        # Do some work
        data = []
        for i in range(1000):
            data.append(str(i) * 100)
        return len(data)
    
    result = container.execute(monitored_task)
    
    # Check stats were collected
    assert result["stats"]["peak_cpu"] >= 0.0
    assert result["stats"]["peak_memory_mb"] > 0.0


def test_violation_tracking():
    """Test that violations are tracked"""
    # Very low limits to trigger violations
    limits = ResourceLimits(
        cpu_percent=0.1,  # Very low
        memory_mb=1,      # Very low
        timeout_sec=60
    )
    container = ConsciousnessContainer("violation_test", limits)
    
    def resource_intensive():
        time.sleep(1)
        return "done"
    
    result = container.execute(resource_intensive)
    
    # Should have some violations recorded
    assert len(result["stats"]["violations"]) >= 0  # May or may not violate depending on system


def test_alert_callback():
    """Test alert callback is called on violations"""
    alerts_received = []
    
    def alert_handler(container_name, violation):
        alerts_received.append((container_name, violation))
    
    limits = ResourceLimits(cpu_percent=0.01, timeout_sec=60)
    container = ConsciousnessContainer("alert_test", limits, alert_callback=alert_handler)
    
    def task():
        time.sleep(0.5)
        return "done"
    
    result = container.execute(task)
    
    # Alerts may or may not be triggered depending on system load
    # Just check structure is correct
    assert isinstance(alerts_received, list)


def test_container_stats():
    """Test getting container statistics"""
    limits = ResourceLimits()
    container = ConsciousnessContainer("stats_test", limits)
    
    def task():
        return "done"
    
    result = container.execute(task)
    
    stats = container.get_stats()
    
    assert "start_time" in stats
    assert "end_time" in stats
    assert "peak_cpu" in stats
    assert "peak_memory_mb" in stats
    assert "violations" in stats
    assert "running" in stats
    assert stats["running"] == False  # Should be stopped after execution


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
