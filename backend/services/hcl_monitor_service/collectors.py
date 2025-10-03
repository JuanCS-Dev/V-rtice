"""
HCL Monitor - Metric Collectors
================================
Real collectors for system metrics: CPU, GPU, Memory, Network, etc.
No mocks - actual system monitoring.
"""

import psutil
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Try to import NVIDIA GPU monitoring (optional)
try:
    import pynvml
    NVIDIA_AVAILABLE = True
    pynvml.nvmlInit()
except (ImportError, Exception) as e:
    NVIDIA_AVAILABLE = False
    logger.warning(f"NVIDIA GPU monitoring not available: {e}")


@dataclass
class Metric:
    """Single metric data point"""
    service_name: str
    metric_name: str
    metric_value: float
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict:
        return {
            "service_name": self.service_name,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags or {}
        }


class CPUCollector:
    """Collects CPU metrics"""

    def __init__(self, service_name: str = "system"):
        self.service_name = service_name
        self.last_cpu_times = None

    async def collect(self) -> List[Metric]:
        """Collect CPU metrics"""
        metrics = []
        timestamp = datetime.utcnow()

        # Overall CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics.append(Metric(
            service_name=self.service_name,
            metric_name="cpu_usage_percent",
            metric_value=cpu_percent,
            timestamp=timestamp
        ))

        # Per-core CPU usage
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        for i, usage in enumerate(per_cpu):
            metrics.append(Metric(
                service_name=self.service_name,
                metric_name="cpu_usage_percent",
                metric_value=usage,
                timestamp=timestamp,
                tags={"core": str(i)}
            ))

        # CPU frequency
        freq = psutil.cpu_freq()
        if freq:
            metrics.append(Metric(
                service_name=self.service_name,
                metric_name="cpu_frequency_mhz",
                metric_value=freq.current,
                timestamp=timestamp
            ))

        # Load average (Linux/Unix)
        try:
            load1, load5, load15 = psutil.getloadavg()
            metrics.append(Metric(
                service_name=self.service_name,
                metric_name="load_average_1m",
                metric_value=load1,
                timestamp=timestamp
            ))
            metrics.append(Metric(
                service_name=self.service_name,
                metric_name="load_average_5m",
                metric_value=load5,
                timestamp=timestamp
            ))
            metrics.append(Metric(
                service_name=self.service_name,
                metric_name="load_average_15m",
                metric_value=load15,
                timestamp=timestamp
            ))
        except (AttributeError, OSError):
            pass  # Not available on all platforms

        return metrics


class MemoryCollector:
    """Collects memory metrics"""

    def __init__(self, service_name: str = "system"):
        self.service_name = service_name

    async def collect(self) -> List[Metric]:
        """Collect memory metrics"""
        metrics = []
        timestamp = datetime.utcnow()

        # Virtual memory
        vmem = psutil.virtual_memory()
        metrics.extend([
            Metric(
                service_name=self.service_name,
                metric_name="memory_usage_percent",
                metric_value=vmem.percent,
                timestamp=timestamp
            ),
            Metric(
                service_name=self.service_name,
                metric_name="memory_total_bytes",
                metric_value=vmem.total,
                timestamp=timestamp
            ),
            Metric(
                service_name=self.service_name,
                metric_name="memory_available_bytes",
                metric_value=vmem.available,
                timestamp=timestamp
            ),
            Metric(
                service_name=self.service_name,
                metric_name="memory_used_bytes",
                metric_value=vmem.used,
                timestamp=timestamp
            )
        ])

        # Swap memory
        swap = psutil.swap_memory()
        metrics.extend([
            Metric(
                service_name=self.service_name,
                metric_name="swap_usage_percent",
                metric_value=swap.percent,
                timestamp=timestamp
            ),
            Metric(
                service_name=self.service_name,
                metric_name="swap_used_bytes",
                metric_value=swap.used,
                timestamp=timestamp
            )
        ])

        return metrics


class GPUCollector:
    """Collects NVIDIA GPU metrics"""

    def __init__(self, service_name: str = "system"):
        self.service_name = service_name
        self.enabled = NVIDIA_AVAILABLE

        if self.enabled:
            self.device_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"Detected {self.device_count} NVIDIA GPUs")
        else:
            logger.warning("GPU monitoring disabled (NVIDIA drivers not available)")

    async def collect(self) -> List[Metric]:
        """Collect GPU metrics"""
        if not self.enabled:
            return []

        metrics = []
        timestamp = datetime.utcnow()

        try:
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)

                # GPU name
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')

                tags = {"gpu_id": str(i), "gpu_name": name}

                # GPU utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                metrics.append(Metric(
                    service_name=self.service_name,
                    metric_name="gpu_usage_percent",
                    metric_value=util.gpu,
                    timestamp=timestamp,
                    tags=tags
                ))
                metrics.append(Metric(
                    service_name=self.service_name,
                    metric_name="gpu_memory_usage_percent",
                    metric_value=util.memory,
                    timestamp=timestamp,
                    tags=tags
                ))

                # GPU memory
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                metrics.extend([
                    Metric(
                        service_name=self.service_name,
                        metric_name="gpu_memory_total_bytes",
                        metric_value=mem.total,
                        timestamp=timestamp,
                        tags=tags
                    ),
                    Metric(
                        service_name=self.service_name,
                        metric_name="gpu_memory_used_bytes",
                        metric_value=mem.used,
                        timestamp=timestamp,
                        tags=tags
                    ),
                    Metric(
                        service_name=self.service_name,
                        metric_name="gpu_memory_free_bytes",
                        metric_value=mem.free,
                        timestamp=timestamp,
                        tags=tags
                    )
                ])

                # GPU temperature
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    metrics.append(Metric(
                        service_name=self.service_name,
                        metric_name="gpu_temperature_celsius",
                        metric_value=temp,
                        timestamp=timestamp,
                        tags=tags
                    ))
                except pynvml.NVMLError:
                    pass  # Temperature not available

                # GPU power
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
                    metrics.append(Metric(
                        service_name=self.service_name,
                        metric_name="gpu_power_watts",
                        metric_value=power,
                        timestamp=timestamp,
                        tags=tags
                    ))
                except pynvml.NVMLError:
                    pass  # Power not available

        except pynvml.NVMLError as e:
            logger.error(f"Error collecting GPU metrics: {e}")

        return metrics


class DiskCollector:
    """Collects disk I/O metrics"""

    def __init__(self, service_name: str = "system"):
        self.service_name = service_name
        self.last_disk_io = None

    async def collect(self) -> List[Metric]:
        """Collect disk metrics"""
        metrics = []
        timestamp = datetime.utcnow()

        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                tags = {"device": partition.device, "mountpoint": partition.mountpoint}

                metrics.extend([
                    Metric(
                        service_name=self.service_name,
                        metric_name="disk_usage_percent",
                        metric_value=usage.percent,
                        timestamp=timestamp,
                        tags=tags
                    ),
                    Metric(
                        service_name=self.service_name,
                        metric_name="disk_total_bytes",
                        metric_value=usage.total,
                        timestamp=timestamp,
                        tags=tags
                    ),
                    Metric(
                        service_name=self.service_name,
                        metric_name="disk_used_bytes",
                        metric_value=usage.used,
                        timestamp=timestamp,
                        tags=tags
                    )
                ])
            except PermissionError:
                pass  # Skip partitions we can't access

        # Disk I/O counters
        disk_io = psutil.disk_io_counters(perdisk=False)
        if disk_io and self.last_disk_io:
            # Calculate rates
            time_delta = 1.0  # Assuming 1 second between calls
            read_rate = (disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
            write_rate = (disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta

            metrics.extend([
                Metric(
                    service_name=self.service_name,
                    metric_name="disk_read_bytes_per_sec",
                    metric_value=read_rate,
                    timestamp=timestamp
                ),
                Metric(
                    service_name=self.service_name,
                    metric_name="disk_write_bytes_per_sec",
                    metric_value=write_rate,
                    timestamp=timestamp
                )
            ])

        self.last_disk_io = disk_io

        return metrics


class NetworkCollector:
    """Collects network metrics"""

    def __init__(self, service_name: str = "system"):
        self.service_name = service_name
        self.last_net_io = None

    async def collect(self) -> List[Metric]:
        """Collect network metrics"""
        metrics = []
        timestamp = datetime.utcnow()

        # Network I/O
        net_io = psutil.net_io_counters()
        if net_io and self.last_net_io:
            time_delta = 1.0  # Assuming 1 second between calls
            sent_rate = (net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
            recv_rate = (net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta

            metrics.extend([
                Metric(
                    service_name=self.service_name,
                    metric_name="network_sent_bytes_per_sec",
                    metric_value=sent_rate,
                    timestamp=timestamp
                ),
                Metric(
                    service_name=self.service_name,
                    metric_name="network_recv_bytes_per_sec",
                    metric_value=recv_rate,
                    timestamp=timestamp
                ),
                Metric(
                    service_name=self.service_name,
                    metric_name="network_packets_sent_per_sec",
                    metric_value=(net_io.packets_sent - self.last_net_io.packets_sent) / time_delta,
                    timestamp=timestamp
                ),
                Metric(
                    service_name=self.service_name,
                    metric_name="network_packets_recv_per_sec",
                    metric_value=(net_io.packets_recv - self.last_net_io.packets_recv) / time_delta,
                    timestamp=timestamp
                )
            ])

        self.last_net_io = net_io

        # Connection count
        connections = psutil.net_connections(kind='inet')
        conn_states = {}
        for conn in connections:
            state = conn.status
            conn_states[state] = conn_states.get(state, 0) + 1

        for state, count in conn_states.items():
            metrics.append(Metric(
                service_name=self.service_name,
                metric_name="network_connections",
                metric_value=count,
                timestamp=timestamp,
                tags={"state": state}
            ))

        return metrics


class ServiceCollector:
    """Collects metrics from other services via HTTP /metrics or /health"""

    def __init__(self, service_name: str, endpoint: str):
        self.service_name = service_name
        self.endpoint = endpoint
        self.session: Optional[aiohttp.ClientSession] = None

    async def init_session(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))

    async def collect(self) -> List[Metric]:
        """Collect metrics from service endpoint"""
        await self.init_session()
        metrics = []
        timestamp = datetime.utcnow()

        try:
            async with self.session.get(self.endpoint) as response:
                if response.status == 200:
                    data = await response.json()

                    # Service is healthy
                    metrics.append(Metric(
                        service_name=self.service_name,
                        metric_name="service_up",
                        metric_value=1.0,
                        timestamp=timestamp
                    ))

                    # Extract metrics from response
                    if "metrics" in data:
                        for key, value in data["metrics"].items():
                            if isinstance(value, (int, float)):
                                metrics.append(Metric(
                                    service_name=self.service_name,
                                    metric_name=key,
                                    metric_value=float(value),
                                    timestamp=timestamp
                                ))

                    # Response time
                    metrics.append(Metric(
                        service_name=self.service_name,
                        metric_name="response_time_ms",
                        metric_value=response.headers.get("X-Response-Time", 0),
                        timestamp=timestamp
                    ))
                else:
                    # Service error
                    metrics.append(Metric(
                        service_name=self.service_name,
                        metric_name="service_up",
                        metric_value=0.0,
                        timestamp=timestamp
                    ))

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to collect from {self.service_name}: {e}")
            metrics.append(Metric(
                service_name=self.service_name,
                metric_name="service_up",
                metric_value=0.0,
                timestamp=timestamp
            ))

        return metrics

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()


class CollectorManager:
    """Manages all collectors"""

    def __init__(self):
        self.collectors = [
            CPUCollector(),
            MemoryCollector(),
            GPUCollector(),
            DiskCollector(),
            NetworkCollector()
        ]

        # Add service collectors (configurable)
        self.service_collectors: List[ServiceCollector] = []

    def add_service(self, service_name: str, endpoint: str):
        """Add a service to monitor"""
        collector = ServiceCollector(service_name, endpoint)
        self.service_collectors.append(collector)
        logger.info(f"Added service collector: {service_name} @ {endpoint}")

    async def collect_all(self) -> List[Metric]:
        """Collect from all collectors"""
        all_metrics = []

        # Collect from system collectors
        for collector in self.collectors:
            try:
                metrics = await collector.collect()
                all_metrics.extend(metrics)
            except Exception as e:
                logger.error(f"Error in {collector.__class__.__name__}: {e}")

        # Collect from service collectors
        for collector in self.service_collectors:
            try:
                metrics = await collector.collect()
                all_metrics.extend(metrics)
            except Exception as e:
                logger.error(f"Error collecting from {collector.service_name}: {e}")

        logger.debug(f"Collected {len(all_metrics)} metrics")
        return all_metrics

    async def close(self):
        """Close all service collectors"""
        for collector in self.service_collectors:
            await collector.close()
