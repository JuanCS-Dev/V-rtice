"""
System Monitor - Prometheus-based telemetry collector

Aggregates 50+ sensor metrics from all services every 15 seconds.
Streams to Kafka and stores in TimescaleDB.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
try:
    from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback stubs if prometheus not available
    CollectorRegistry = None
    Gauge = None
    push_to_gateway = None
import psutil
import json

from .sensor_definitions import (
    ComputeSensors,
    NetworkSensors,
    ApplicationSensors,
    MLModelSensors,
    StorageSensors
)
from .kafka_streamer import KafkaMetricsStreamer

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Main Prometheus collector for 50+ system metrics.

    Implements digital interoception - continuous awareness of internal system state.
    Analogous to the autonomic nervous system's monitoring of vital signs.

    Performance Targets:
        - Scrape interval: 15s
        - Collection latency: <1s
        - Storage retention: 90 days detailed, 2 years aggregated
    """

    def __init__(
        self,
        kafka_broker: str = "localhost:9092",
        kafka_topic: str = "system.telemetry.raw",
        prometheus_pushgateway: str = "localhost:9091",
        scrape_interval: int = 15
    ):
        """
        Initialize System Monitor.

        Args:
            kafka_broker: Kafka broker address for real-time streaming
            kafka_topic: Topic for telemetry data
            prometheus_pushgateway: Pushgateway for Prometheus metrics
            scrape_interval: Seconds between metric collection (default: 15s)
        """
        self.scrape_interval = scrape_interval
        self.prometheus_pushgateway = prometheus_pushgateway

        # Initialize sensors
        self.compute_sensors = ComputeSensors()
        self.network_sensors = NetworkSensors()
        self.application_sensors = ApplicationSensors()
        self.ml_sensors = MLModelSensors()
        self.storage_sensors = StorageSensors()

        # Initialize Kafka streamer
        self.kafka_streamer = KafkaMetricsStreamer(
            broker=kafka_broker,
            topic=kafka_topic
        )

        # Prometheus registry
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()

        # Metrics cache
        self.latest_metrics: Dict[str, Any] = {}

        logger.info(
            f"SystemMonitor initialized (scrape_interval={scrape_interval}s, "
            f"kafka_topic={kafka_topic})"
        )

    def _setup_prometheus_metrics(self):
        """Setup Prometheus Gauge metrics for all sensors."""
        # Compute metrics
        self.prom_cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage', registry=self.registry)
        self.prom_memory_usage = Gauge('memory_usage_percent', 'Memory usage percentage', registry=self.registry)
        self.prom_gpu_usage = Gauge('gpu_usage_percent', 'GPU usage percentage', registry=self.registry)

        # Network metrics
        self.prom_latency = Gauge('network_latency_p99_ms', 'Network latency p99 in ms', registry=self.registry)
        self.prom_bandwidth = Gauge('bandwidth_saturation_percent', 'Bandwidth saturation', registry=self.registry)

        # Application metrics
        self.prom_error_rate = Gauge('application_error_rate', 'Application errors per second', registry=self.registry)
        self.prom_throughput = Gauge('application_throughput_rps', 'Requests per second', registry=self.registry)

        # ML metrics
        self.prom_inference_latency = Gauge('ml_inference_latency_ms', 'ML inference latency', registry=self.registry)
        self.prom_model_drift = Gauge('ml_model_drift', 'Model drift KL divergence', registry=self.registry)

        # Storage metrics
        self.prom_disk_io = Gauge('disk_io_wait_percent', 'Disk I/O wait percentage', registry=self.registry)
        self.prom_query_latency = Gauge('db_query_latency_ms', 'Database query latency', registry=self.registry)

    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect all 50+ metrics from all sensors.

        Returns:
            Dictionary of metric_name -> value pairs
        """
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'collection_latency_ms': 0
            }

            start_time = asyncio.get_event_loop().time()

            # Collect from all sensors concurrently
            compute_metrics = await self.compute_sensors.collect()
            network_metrics = await self.network_sensors.collect()
            app_metrics = await self.application_sensors.collect()
            ml_metrics = await self.ml_sensors.collect()
            storage_metrics = await self.storage_sensors.collect()

            # Merge all metrics
            metrics.update(compute_metrics)
            metrics.update(network_metrics)
            metrics.update(app_metrics)
            metrics.update(ml_metrics)
            metrics.update(storage_metrics)

            # Calculate collection latency
            end_time = asyncio.get_event_loop().time()
            metrics['collection_latency_ms'] = (end_time - start_time) * 1000

            # Update Prometheus metrics
            self._update_prometheus(metrics)

            # Cache latest metrics
            self.latest_metrics = metrics

            # Log summary
            logger.debug(
                f"Collected {len(metrics)} metrics in "
                f"{metrics['collection_latency_ms']:.2f}ms"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}", exc_info=True)
            return {'timestamp': datetime.utcnow().isoformat(), 'error': str(e)}

    def _update_prometheus(self, metrics: Dict[str, Any]):
        """Update Prometheus Gauge metrics."""
        try:
            # Compute
            if 'cpu_usage' in metrics:
                self.prom_cpu_usage.set(metrics['cpu_usage'])
            if 'memory_usage' in metrics:
                self.prom_memory_usage.set(metrics['memory_usage'])
            if 'gpu_usage' in metrics:
                self.prom_gpu_usage.set(metrics['gpu_usage'])

            # Network
            if 'latency_p99' in metrics:
                self.prom_latency.set(metrics['latency_p99'])
            if 'bandwidth_saturation' in metrics:
                self.prom_bandwidth.set(metrics['bandwidth_saturation'])

            # Application
            if 'error_rate' in metrics:
                self.prom_error_rate.set(metrics['error_rate'])
            if 'throughput' in metrics:
                self.prom_throughput.set(metrics['throughput'])

            # ML
            if 'inference_latency' in metrics:
                self.prom_inference_latency.set(metrics['inference_latency'])
            if 'model_drift' in metrics:
                self.prom_model_drift.set(metrics['model_drift'])

            # Storage
            if 'disk_io_wait' in metrics:
                self.prom_disk_io.set(metrics['disk_io_wait'])
            if 'query_latency' in metrics:
                self.prom_query_latency.set(metrics['query_latency'])

            # Push to Prometheus Pushgateway
            push_to_gateway(
                self.prometheus_pushgateway,
                job='system_monitor',
                registry=self.registry
            )

        except Exception as e:
            logger.warning(f"Error updating Prometheus: {e}")

    async def run(self):
        """
        Main monitoring loop - runs indefinitely.

        Collects metrics every scrape_interval seconds and streams to Kafka.
        """
        logger.info(f"Starting System Monitor (interval={self.scrape_interval}s)")

        while True:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()

                # Stream to Kafka for real-time processing
                await self.kafka_streamer.send(metrics)

                # Wait for next scrape interval
                await asyncio.sleep(self.scrape_interval)

            except asyncio.CancelledError:
                logger.info("SystemMonitor cancelled, shutting down")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.scrape_interval)

    def get_latest_metrics(self) -> Dict[str, Any]:
        """
        Get most recent metrics without waiting for new collection.

        Returns:
            Dictionary of latest metrics
        """
        return self.latest_metrics.copy()

    async def shutdown(self):
        """Graceful shutdown - close Kafka connection."""
        logger.info("Shutting down SystemMonitor")
        await self.kafka_streamer.close()
