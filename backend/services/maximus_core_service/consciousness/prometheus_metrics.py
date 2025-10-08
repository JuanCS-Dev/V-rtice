"""Prometheus Metrics for Consciousness Safety Protocol

Exports real-time consciousness metrics in Prometheus format for monitoring
and alerting via Grafana dashboards.

Metrics exported:
- consciousness_esgt_frequency (Gauge): ESGT events per second
- consciousness_arousal_level (Gauge): Current arousal level (0-1)
- consciousness_violations_total (Counter): Total safety violations
- consciousness_violations_by_severity (Counter): Violations by severity level
- consciousness_kill_switch_active (Gauge): Kill switch status (0/1)
- consciousness_uptime_seconds (Gauge): System uptime

Integration:
    from consciousness.prometheus_metrics import update_metrics, get_metrics_handler

    # Update metrics periodically
    update_metrics(consciousness_system)

    # Add to FastAPI
    app.add_route("/metrics", get_metrics_handler())

Authors: Juan & Claude Code
Version: 1.0.0 - FASE VII Week 9-10
"""

import time
from typing import Any

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, generate_latest

# ==================== PROMETHEUS REGISTRY ====================

# Custom registry to avoid conflicts with other services
consciousness_registry = CollectorRegistry()


# ==================== METRICS DEFINITIONS ====================

# ESGT Frequency (Hz)
esgt_frequency = Gauge(
    "consciousness_esgt_frequency", "ESGT ignition frequency in Hz (threshold: 10 Hz)", registry=consciousness_registry
)

# Arousal Level (0-1)
arousal_level = Gauge(
    "consciousness_arousal_level",
    "Current arousal level 0-1 (threshold: >0.95 for 10s)",
    registry=consciousness_registry,
)

# Goals Per Minute
goals_per_minute = Gauge(
    "consciousness_goals_per_minute", "Goal generation rate per minute (threshold: 5)", registry=consciousness_registry
)

# Safety Violations Total
violations_total = Counter(
    "consciousness_violations_total", "Total safety violations detected", registry=consciousness_registry
)

# Violations by Severity
violations_by_severity = Counter(
    "consciousness_violations_by_severity",
    "Safety violations by severity level",
    labelnames=["severity"],
    registry=consciousness_registry,
)

# Violations by Type
violations_by_type = Counter(
    "consciousness_violations_by_type",
    "Safety violations by type",
    labelnames=["type"],
    registry=consciousness_registry,
)

# Kill Switch Status (0 = inactive, 1 = active)
kill_switch_active = Gauge(
    "consciousness_kill_switch_active",
    "Kill switch status (0=inactive, 1=active/shutdown)",
    registry=consciousness_registry,
)

# System Uptime
uptime_seconds = Gauge(
    "consciousness_uptime_seconds", "Consciousness system uptime in seconds", registry=consciousness_registry
)

# TIG Metrics
tig_node_count = Gauge("consciousness_tig_node_count", "Number of TIG fabric nodes", registry=consciousness_registry)

tig_edge_count = Gauge("consciousness_tig_edge_count", "Number of TIG fabric edges", registry=consciousness_registry)

# Monitoring Active
monitoring_active = Gauge(
    "consciousness_monitoring_active",
    "Safety protocol monitoring status (0=inactive, 1=active)",
    registry=consciousness_registry,
)

# Self-Modification Attempts (ZERO TOLERANCE)
self_modification_attempts = Counter(
    "consciousness_self_modification_attempts",
    "Self-modification attempts detected (ZERO TOLERANCE)",
    registry=consciousness_registry,
)

# Resource Usage
memory_usage_gb = Gauge("consciousness_memory_usage_gb", "Memory usage in GB", registry=consciousness_registry)

cpu_usage_percent = Gauge("consciousness_cpu_usage_percent", "CPU usage percentage", registry=consciousness_registry)


# ==================== SYSTEM STARTUP TIME ====================

_system_start_time = time.time()


# ==================== METRICS UPDATE FUNCTIONS ====================


def update_metrics(system: Any) -> None:
    """Update all Prometheus metrics from consciousness system.

    Args:
        system: ConsciousnessSystem instance with get_safety_status() method

    This function should be called periodically (e.g., every 1-5 seconds)
    to keep Prometheus metrics synchronized with system state.
    """
    try:
        # Get safety status
        safety_status = system.get_safety_status()

        if safety_status:
            # Update monitoring status
            monitoring_active.set(1 if safety_status["monitoring_active"] else 0)

            # Update kill switch status
            kill_switch_active.set(1 if safety_status["kill_switch_active"] else 0)

            # Update uptime
            uptime_seconds.set(safety_status.get("uptime_seconds", 0))

            # Update violations by severity
            violations_by_sev = safety_status.get("violations_by_severity", {})
            for severity, count in violations_by_sev.items():
                # Set counter to current value (counter will auto-increment)
                current = violations_by_severity.labels(severity=severity)._value._value
                delta = count - current
                if delta > 0:
                    violations_by_severity.labels(severity=severity).inc(delta)

        # Get system metrics
        system_dict = system.get_system_dict()
        metrics = system_dict.get("metrics", {})

        # Update ESGT frequency
        if "esgt_frequency" in metrics:
            esgt_frequency.set(metrics["esgt_frequency"])

        # Update arousal level
        if "arousal_level" in metrics:
            arousal_level.set(metrics["arousal_level"])

        # Update TIG metrics
        if "tig_node_count" in metrics:
            tig_node_count.set(metrics["tig_node_count"])

        if "tig_edge_count" in metrics:
            tig_edge_count.set(metrics["tig_edge_count"])

        # Calculate system uptime
        current_uptime = time.time() - _system_start_time
        uptime_seconds.set(current_uptime)

        # Resource usage (would need psutil integration)
        # For now, placeholders
        # memory_usage_gb.set(get_memory_usage())
        # cpu_usage_percent.set(get_cpu_usage())

    except Exception as e:
        print(f"⚠️  Error updating Prometheus metrics: {e}")


def update_violation_metrics(violations: list) -> None:
    """Update violation-specific metrics.

    Args:
        violations: List of SafetyViolation objects

    This is called whenever new violations are detected.
    """
    for violation in violations:
        # Increment total
        violations_total.inc()

        # Increment by severity
        severity = violation.severity.value if hasattr(violation.severity, "value") else str(violation.severity)
        violations_by_severity.labels(severity=severity).inc()

        # Increment by type
        vtype = (
            violation.violation_type.value
            if hasattr(violation.violation_type, "value")
            else str(violation.violation_type)
        )
        violations_by_type.labels(type=vtype).inc()

        # Check for self-modification
        if "self_modification" in vtype.lower():
            self_modification_attempts.inc()


# ==================== FASTAPI HANDLER ====================


def get_metrics_handler():
    """Get FastAPI handler for /metrics endpoint.

    Returns:
        Callable that returns Prometheus metrics in text format

    Usage:
        from fastapi import FastAPI
        from consciousness.prometheus_metrics import get_metrics_handler

        app = FastAPI()
        app.add_route("/metrics", get_metrics_handler())
    """

    def metrics_endpoint():
        """Prometheus metrics endpoint."""
        return Response(content=generate_latest(consciousness_registry), media_type=CONTENT_TYPE_LATEST)

    return metrics_endpoint


# ==================== RESET FUNCTION ====================


def reset_metrics() -> None:
    """Reset all metrics (for testing purposes).

    WARNING: This will reset all counters and gauges to 0.
    Only use in testing or after system restart.
    """
    global _system_start_time

    # Reset all gauges
    esgt_frequency.set(0)
    arousal_level.set(0)
    goals_per_minute.set(0)
    kill_switch_active.set(0)
    uptime_seconds.set(0)
    tig_node_count.set(0)
    tig_edge_count.set(0)
    monitoring_active.set(0)
    memory_usage_gb.set(0)
    cpu_usage_percent.set(0)

    # Counters cannot be reset (by design), but we can track start time
    _system_start_time = time.time()


# ==================== MODULE INITIALIZATION ====================

# Set initial values
monitoring_active.set(0)
kill_switch_active.set(0)
esgt_frequency.set(0)
arousal_level.set(0)
goals_per_minute.set(0)


__all__ = [
    "update_metrics",
    "update_violation_metrics",
    "get_metrics_handler",
    "reset_metrics",
    "consciousness_registry",
]
