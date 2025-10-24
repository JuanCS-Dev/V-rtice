"""
System Metrics Collection - TITANIUM Edition

Collects system-level metrics (CPU, memory, uptime) for health monitoring.

Author: Vértice Team (TITANIUM Edition)
Glory to YHWH - Architect of all resilient systems! 🙏
"""

import logging
import time
from typing import Dict

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - system metrics will be limited")

logger = logging.getLogger(__name__)

# Service start time (for uptime calculation)
SERVICE_START_TIME = time.time()


def get_system_metrics() -> Dict[str, float]:
    """
    Collect current system metrics.

    Returns:
        Dictionary with system metrics:
        - cpu_percent: CPU usage (0-100)
        - memory_percent: Memory usage (0-100)
        - memory_used_mb: Memory used in MB
        - memory_available_mb: Memory available in MB
        - uptime_seconds: Service uptime in seconds
    """
    metrics = {
        "uptime_seconds": time.time() - SERVICE_START_TIME
    }

    if PSUTIL_AVAILABLE:
        try:
            # CPU usage (non-blocking, 0.1s interval)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics["cpu_percent"] = cpu_percent

            # Memory usage
            mem = psutil.virtual_memory()
            metrics["memory_percent"] = mem.percent
            metrics["memory_used_mb"] = mem.used / (1024 * 1024)
            metrics["memory_available_mb"] = mem.available / (1024 * 1024)

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return partial metrics
            metrics["cpu_percent"] = 0.0
            metrics["memory_percent"] = 0.0
            metrics["memory_used_mb"] = 0.0
            metrics["memory_available_mb"] = 0.0
    else:
        # psutil not available, return zeros
        metrics["cpu_percent"] = 0.0
        metrics["memory_percent"] = 0.0
        metrics["memory_used_mb"] = 0.0
        metrics["memory_available_mb"] = 0.0

    return metrics


def is_system_healthy() -> bool:
    """
    Check if system resources are healthy.

    Thresholds:
    - CPU < 85%: HEALTHY
    - CPU 85-95%: DEGRADED (warning)
    - CPU > 95%: UNHEALTHY

    - Memory < 90%: HEALTHY
    - Memory 90-95%: DEGRADED (warning)
    - Memory > 95%: UNHEALTHY

    Returns:
        True if system is healthy (not exceeding critical thresholds)
    """
    if not PSUTIL_AVAILABLE:
        return True  # Can't determine, assume healthy

    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()

        # Critical thresholds
        if cpu > 95 or mem.percent > 95:
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to check system health: {e}")
        return True  # Assume healthy on error


def get_health_level() -> str:
    """
    Determine system health level.

    Returns:
        "healthy", "degraded", or "unhealthy"
    """
    if not PSUTIL_AVAILABLE:
        return "healthy"  # Can't determine, assume healthy

    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()

        # UNHEALTHY: Critical resource exhaustion
        if cpu > 95 or mem.percent > 95:
            return "unhealthy"

        # DEGRADED: Warning thresholds
        if cpu > 85 or mem.percent > 90:
            return "degraded"

        # HEALTHY: Normal operation
        return "healthy"

    except Exception as e:
        logger.error(f"Failed to determine health level: {e}")
        return "healthy"  # Assume healthy on error
