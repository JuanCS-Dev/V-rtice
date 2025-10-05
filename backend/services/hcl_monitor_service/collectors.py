"""Maximus HCL Monitor Service - Metrics Collectors.

This module provides various collectors for gathering real-time operational
metrics and system state data from the Maximus AI system and its underlying
infrastructure. These collectors are designed to interface with different
sources (e.g., `psutil` for OS metrics, Prometheus for service metrics) and
normalize the data into a consistent format.

Key components within this module are responsible for:
- Periodically polling system resources (CPU, memory, disk, network).
- Aggregating metrics from multiple services.
- Storing a short history of collected data.
- Providing a unified interface for the HCL Monitor Service to access up-to-date
  system health information.
"""

import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime


class SystemMetricsCollector:
    """Collects real-time operational metrics from the host system and Maximus services.

    Interfaces with different sources (e.g., `psutil` for OS metrics, Prometheus
    for service metrics) and normalizes the data into a consistent format.
    """

    def __init__(self, collection_interval_seconds: float = 1.0):
        """Initializes the SystemMetricsCollector.

        Args:
            collection_interval_seconds (float): The interval in seconds between metric collections.
        """
        self.collection_interval = collection_interval_seconds
        self.is_collecting = False
        self.latest_metrics: Dict[str, Any] = {}
        self.metrics_history: List[Dict[str, Any]] = []
        self.history_max_size: int = 100

        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = datetime.now()

    async def start_collection(self):
        """Starts the continuous metric collection loop."""
        if self.is_collecting: return
        self.is_collecting = True
        print("[MetricsCollector] Starting metric collection...")
        while self.is_collecting:
            await self._collect_metrics_once()
            await asyncio.sleep(self.collection_interval)

    async def stop_collection(self):
        """Stops the continuous metric collection loop."""
        self.is_collecting = False
        print("[MetricsCollector] Stopping metric collection.")

    async def _collect_metrics_once(self):
        """Collects a single snapshot of system and service metrics."""
        current_time = datetime.now()
        time_delta = (current_time - self.last_check_time).total_seconds()

        # OS-level metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent

        current_disk_io = psutil.disk_io_counters()
        disk_read_rate = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta if time_delta > 0 else 0
        disk_write_rate = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta if time_delta > 0 else 0

        current_net_io = psutil.net_io_counters()
        net_recv_rate = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta if time_delta > 0 else 0
        net_sent_rate = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta if time_delta > 0 else 0

        self.last_disk_io = current_disk_io
        self.last_net_io = current_net_io
        self.last_check_time = current_time

        # Simulate service-level metrics (e.g., from Prometheus or direct API calls)
        service_status = {
            "maximus_core": "healthy",
            "chemical_sensing": "healthy",
            "visual_cortex": "degraded" if cpu_percent > 80 else "healthy"
        }
        avg_latency_ms = 50.0 + (cpu_percent / 2)
        error_rate = 0.01 + (cpu_percent / 1000)

        metrics = {
            "timestamp": current_time.isoformat(),
            "cpu_usage": cpu_percent,
            "memory_usage": memory_percent,
            "disk_io_read_rate": disk_read_rate,
            "disk_io_write_rate": disk_write_rate,
            "network_io_recv_rate": net_recv_rate,
            "network_io_sent_rate": net_sent_rate,
            "avg_latency_ms": avg_latency_ms,
            "error_rate": error_rate,
            "service_status": service_status
        }

        self.latest_metrics = metrics
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.history_max_size:
            self.metrics_history.pop(0)
        print(f"[MetricsCollector] Collected metrics: CPU={cpu_percent:.1f}%, Mem={memory_percent:.1f}%")

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Returns the most recently collected system metrics.

        Returns:
            Dict[str, Any]: A dictionary containing the latest system metrics.
        """
        return self.latest_metrics

    def get_metrics_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns a history of collected system metrics.

        Args:
            limit (int): The maximum number of historical metrics to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of historical system metrics.
        """
        return self.metrics_history[-limit:]
