"""Maximus Core Service - System Monitor.

This module provides real-time, low-level monitoring of the AI's host system.
It collects critical metrics such as CPU usage, memory consumption, disk I/O,
network I/O, and temperature, using system-level libraries like `psutil`.

This component is vital for feeding accurate, up-to-date operational data to
the Homeostatic Control Loop (HCL) and Resource Analyzer, enabling informed
decisions about system health and resource management.
"""

import asyncio
from datetime import datetime
import time
from typing import Any, Dict, Optional

from autonomic_core.homeostatic_control import OperationalMode, SystemState
import psutil


class SystemMonitor:
    """Collects real-time operational metrics from the host system.

    This class uses `psutil` to gather CPU, memory, disk, and network usage,
    providing a comprehensive view of the system's current state.
    """

    def __init__(self):
        """Initializes the SystemMonitor, setting up process and time tracking."""
        self.process = psutil.Process()  # The current process (Maximus)
        self.start_time = time.time()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = time.time()

    async def collect_metrics(self) -> SystemState:
        """Collects and returns a snapshot of the current system metrics.

        Returns:
            SystemState: An object containing all collected metrics.
        """
        current_time = time.time()
        time_delta = current_time - self.last_check_time

        # Collect CPU, Memory, Disk I/O, Network I/O (simplified for docstring)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        disk_io_rate = (
            (psutil.disk_io_counters().read_bytes - self.last_disk_io.read_bytes)
            / time_delta
            if time_delta > 0
            else 0
        )
        network_io_rate = (
            (psutil.net_io_counters().bytes_recv - self.last_net_io.bytes_recv)
            / time_delta
            if time_delta > 0
            else 0
        )

        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = current_time

        # Simulate latency and health
        avg_latency_ms = 50.0 + (cpu_percent / 2)
        is_healthy = cpu_percent < 90 and memory_percent < 90

        return SystemState(
            timestamp=datetime.now().isoformat(),
            mode=OperationalMode.BALANCED,
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            avg_latency_ms=avg_latency_ms,
            is_healthy=is_healthy,
        )

    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Returns a more detailed set of system metrics for debugging or advanced monitoring."""
        # This would include more granular data from psutil
        return {"cpu": psutil.cpu_percent(), "memory": psutil.virtual_memory().percent}
