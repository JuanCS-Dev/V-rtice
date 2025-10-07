"""
Sensor Definitions - 50+ metric sensors organized by category

Categories:
    - Compute (CPU, GPU, Memory)
    - Network (Latency, Bandwidth, Connections)
    - Application (Error rate, Throughput, Queue depth)
    - ML Models (Inference latency, Drift, Cache)
    - Storage (Disk I/O, DB connections, Query latency)
"""

import asyncio
import json
import logging
import subprocess
from typing import Any, Dict

import psutil

logger = logging.getLogger(__name__)


class ComputeSensors:
    """
    Compute resource sensors - CPU, GPU, Memory, Swap.

    Metrics:
        - cpu_usage (%): Overall CPU utilization
        - cpu_per_core (%): Per-core CPU usage
        - gpu_usage (%): GPU utilization (if available)
        - gpu_temperature (°C): GPU temperature
        - memory_usage (%): RAM usage
        - memory_available (GB): Available RAM
        - swap_usage (%): Swap usage
    """

    async def collect(self) -> Dict[str, Any]:
        """Collect all compute metrics."""
        metrics = {}

        try:
            # CPU metrics
            metrics["cpu_usage"] = psutil.cpu_percent(interval=0.1)
            metrics["cpu_per_core"] = psutil.cpu_percent(interval=0.1, percpu=True)
            metrics["cpu_count"] = psutil.cpu_count()

            # Memory metrics
            mem = psutil.virtual_memory()
            metrics["memory_usage"] = mem.percent
            metrics["memory_total_gb"] = mem.total / (1024**3)
            metrics["memory_available_gb"] = mem.available / (1024**3)
            metrics["memory_used_gb"] = mem.used / (1024**3)

            # Swap metrics
            swap = psutil.swap_memory()
            metrics["swap_usage"] = swap.percent
            metrics["swap_total_gb"] = swap.total / (1024**3)

            # GPU metrics (if nvidia-smi available)
            try:
                gpu_metrics = await self._get_gpu_metrics()
                metrics.update(gpu_metrics)
            except Exception as e:
                logger.debug(f"GPU metrics unavailable: {e}")
                metrics["gpu_usage"] = 0
                metrics["gpu_temperature"] = 0

        except Exception as e:
            logger.error(f"Error collecting compute metrics: {e}")

        return metrics

    async def _get_gpu_metrics(self) -> Dict[str, Any]:
        """Get GPU metrics via nvidia-smi."""
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            lines = stdout.decode().strip().split("\n")
            gpu_data = lines[0].split(",")  # First GPU

            return {
                "gpu_usage": float(gpu_data[0]),
                "gpu_temperature": float(gpu_data[1]),
                "gpu_memory_used_mb": float(gpu_data[2]),
                "gpu_memory_total_mb": float(gpu_data[3]),
                "gpu_memory_usage": (float(gpu_data[2]) / float(gpu_data[3])) * 100,
            }
        else:
            raise Exception(f"nvidia-smi failed: {stderr.decode()}")


class NetworkSensors:
    """
    Network resource sensors.

    Metrics:
        - latency_p99 (ms): 99th percentile latency (simulated/from metrics)
        - latency_p95 (ms): 95th percentile latency
        - bandwidth_saturation (%): Network bandwidth utilization
        - connection_pool (active/max): Active connections
        - packet_loss (%): Packet loss rate
        - bytes_sent (bytes/s): Outgoing bandwidth
        - bytes_recv (bytes/s): Incoming bandwidth
    """

    def __init__(self):
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = asyncio.get_event_loop().time()

    async def collect(self) -> Dict[str, Any]:
        """Collect all network metrics."""
        metrics = {}

        try:
            # Current net I/O
            current_net_io = psutil.net_io_counters()
            current_time = asyncio.get_event_loop().time()
            time_delta = current_time - self.last_check_time

            if time_delta > 0:
                # Calculate bytes/s
                bytes_sent_per_sec = (
                    current_net_io.bytes_sent - self.last_net_io.bytes_sent
                ) / time_delta
                bytes_recv_per_sec = (
                    current_net_io.bytes_recv - self.last_net_io.bytes_recv
                ) / time_delta

                metrics["bytes_sent_per_sec"] = bytes_sent_per_sec
                metrics["bytes_recv_per_sec"] = bytes_recv_per_sec

                # Estimate bandwidth saturation (assuming 1Gbps = 125MB/s)
                total_bandwidth = bytes_sent_per_sec + bytes_recv_per_sec
                max_bandwidth = 125 * 1024 * 1024  # 1Gbps in bytes/s
                metrics["bandwidth_saturation"] = min(
                    (total_bandwidth / max_bandwidth) * 100, 100
                )

            # Connection stats
            connections = psutil.net_connections()
            metrics["connection_count"] = len(connections)
            metrics["connection_established"] = len(
                [c for c in connections if c.status == "ESTABLISHED"]
            )

            # Packet stats
            metrics["packets_sent"] = current_net_io.packets_sent
            metrics["packets_recv"] = current_net_io.packets_recv
            metrics["packets_dropped_in"] = current_net_io.dropin
            metrics["packets_dropped_out"] = current_net_io.dropout

            total_packets = current_net_io.packets_sent + current_net_io.packets_recv
            dropped_packets = current_net_io.dropin + current_net_io.dropout
            metrics["packet_loss"] = (
                (dropped_packets / total_packets * 100) if total_packets > 0 else 0
            )

            # Simulated latency metrics (would come from actual monitoring in production)
            metrics["latency_p50"] = (
                10.0  # Placeholder - integrate with real monitoring
            )
            metrics["latency_p95"] = 25.0
            metrics["latency_p99"] = 50.0

            # Update for next iteration
            self.last_net_io = current_net_io
            self.last_check_time = current_time

        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")

        return metrics


class ApplicationSensors:
    """
    Application-level sensors.

    Metrics:
        - error_rate (errors/s): Application errors per second
        - request_queue (depth): Pending requests
        - response_time_p50 (ms): Median response time
        - response_time_p95 (ms): 95th percentile response time
        - response_time_p99 (ms): 99th percentile response time
        - throughput (req/s): Requests per second
        - active_users: Current active users
    """

    def __init__(self):
        self.error_count = 0
        self.request_count = 0
        self.last_check_time = asyncio.get_event_loop().time()

    async def collect(self) -> Dict[str, Any]:
        """Collect all application metrics."""
        metrics = {}

        try:
            current_time = asyncio.get_event_loop().time()
            time_delta = current_time - self.last_check_time

            if time_delta > 0:
                # Calculate rates
                metrics["error_rate"] = self.error_count / time_delta
                metrics["throughput"] = self.request_count / time_delta

                # Reset counters
                self.error_count = 0
                self.request_count = 0
                self.last_check_time = current_time

            # Simulated metrics (would come from application metrics in production)
            metrics["request_queue_depth"] = 5  # Placeholder
            metrics["response_time_p50"] = 150.0  # ms
            metrics["response_time_p95"] = 350.0
            metrics["response_time_p99"] = 500.0
            metrics["active_users"] = 42  # Placeholder

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")

        return metrics

    def record_error(self):
        """Increment error counter."""
        self.error_count += 1

    def record_request(self):
        """Increment request counter."""
        self.request_count += 1


class MLModelSensors:
    """
    Machine Learning model sensors.

    Metrics:
        - inference_latency (ms): Average inference time
        - inference_latency_p99 (ms): 99th percentile inference time
        - batch_efficiency (%): GPU batch utilization
        - model_drift (KL divergence): Distribution shift from training data
        - cache_hit_rate (%): Feature cache hit rate
        - predictions_per_sec: Throughput
    """

    def __init__(self):
        self.inference_times = []
        self.cache_hits = 0
        self.cache_misses = 0

    async def collect(self) -> Dict[str, Any]:
        """Collect all ML model metrics."""
        metrics = {}

        try:
            # Inference latency
            if self.inference_times:
                import numpy as np

                metrics["inference_latency"] = np.mean(self.inference_times)
                metrics["inference_latency_p99"] = np.percentile(
                    self.inference_times, 99
                )
                metrics["predictions_per_sec"] = (
                    len(self.inference_times) / 15.0
                )  # Over scrape interval
                self.inference_times = []  # Reset
            else:
                metrics["inference_latency"] = 0
                metrics["inference_latency_p99"] = 0
                metrics["predictions_per_sec"] = 0

            # Cache metrics
            total_requests = self.cache_hits + self.cache_misses
            metrics["cache_hit_rate"] = (
                (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
            )
            self.cache_hits = 0
            self.cache_misses = 0

            # Model drift (simulated - would require actual distribution comparison)
            metrics["model_drift"] = 0.05  # KL divergence placeholder

            # Batch efficiency (simulated)
            metrics["batch_efficiency"] = 75.0  # % placeholder

        except Exception as e:
            logger.error(f"Error collecting ML model metrics: {e}")

        return metrics

    def record_inference(self, latency_ms: float):
        """Record an inference time."""
        self.inference_times.append(latency_ms)

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses += 1


class StorageSensors:
    """
    Storage and database sensors.

    Metrics:
        - disk_io_wait (%): I/O wait percentage
        - disk_read_bytes_per_sec: Read throughput
        - disk_write_bytes_per_sec: Write throughput
        - database_connections_active: Active DB connections
        - database_connections_max: Maximum allowed connections
        - query_latency (ms): Average query latency
        - index_efficiency (%): Index usage rate
    """

    def __init__(self):
        self.last_disk_io = psutil.disk_io_counters()
        self.last_check_time = asyncio.get_event_loop().time()
        self.query_times = []

    async def collect(self) -> Dict[str, Any]:
        """Collect all storage metrics."""
        metrics = {}

        try:
            # Disk I/O
            current_disk_io = psutil.disk_io_counters()
            current_time = asyncio.get_event_loop().time()
            time_delta = current_time - self.last_check_time

            if time_delta > 0:
                # Calculate bytes/s
                read_bytes_per_sec = (
                    current_disk_io.read_bytes - self.last_disk_io.read_bytes
                ) / time_delta
                write_bytes_per_sec = (
                    current_disk_io.write_bytes - self.last_disk_io.write_bytes
                ) / time_delta

                metrics["disk_read_bytes_per_sec"] = read_bytes_per_sec
                metrics["disk_write_bytes_per_sec"] = write_bytes_per_sec

            # Disk usage
            disk_usage = psutil.disk_usage("/")
            metrics["disk_usage_percent"] = disk_usage.percent
            metrics["disk_free_gb"] = disk_usage.free / (1024**3)

            # I/O wait (from CPU times - iowait)
            cpu_times = psutil.cpu_times_percent(interval=0.1)
            metrics["disk_io_wait"] = (
                cpu_times.iowait if hasattr(cpu_times, "iowait") else 0
            )

            # Query latency
            if self.query_times:
                import numpy as np

                metrics["query_latency"] = np.mean(self.query_times)
                metrics["query_latency_p99"] = np.percentile(self.query_times, 99)
                self.query_times = []
            else:
                metrics["query_latency"] = 0
                metrics["query_latency_p99"] = 0

            # Database connection metrics (simulated - would query actual DB)
            metrics["database_connections_active"] = 15  # Placeholder
            metrics["database_connections_max"] = 100
            metrics["database_connection_usage"] = 15.0  # %

            # Index efficiency (simulated)
            metrics["index_efficiency"] = 92.0  # % placeholder

            # Update for next iteration
            self.last_disk_io = current_disk_io
            self.last_check_time = current_time

        except Exception as e:
            logger.error(f"Error collecting storage metrics: {e}")

        return metrics

    def record_query(self, latency_ms: float):
        """Record a query latency."""
        self.query_times.append(latency_ms)
