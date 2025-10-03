"""
HCL Monitor Service
===================
Collects system metrics in real-time and sends to Knowledge Base + Kafka.
The "Interoception" of Maximus AI's Unconscious Layer.
"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from contextlib import asynccontextmanager
import asyncio
import aiohttp
import logging
import os
import json
from typing import List
from datetime import datetime

from collectors import CollectorManager, Metric

# ============================================================================
# CONFIGURATION
# ============================================================================

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "hcl_monitor")
COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", "15"))  # seconds
KB_API_URL = os.getenv("KB_API_URL", "http://localhost:8000")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
ENABLE_KAFKA = os.getenv("ENABLE_KAFKA", "false").lower() == "true"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Counters
metrics_collected_total = Counter(
    'hcl_metrics_collected_total',
    'Total metrics collected',
    ['service']
)

metrics_sent_total = Counter(
    'hcl_metrics_sent_total',
    'Total metrics sent to KB',
    ['destination']
)

collection_errors_total = Counter(
    'hcl_collection_errors_total',
    'Total collection errors',
    ['collector']
)

# Gauges (latest values)
cpu_usage = Gauge('hcl_cpu_usage_percent', 'CPU usage')
memory_usage = Gauge('hcl_memory_usage_percent', 'Memory usage')
gpu_usage = Gauge('hcl_gpu_usage_percent', 'GPU usage', ['gpu_id'])
disk_usage = Gauge('hcl_disk_usage_percent', 'Disk usage', ['mountpoint'])

# Histogram
collection_duration = Histogram(
    'hcl_collection_duration_seconds',
    'Collection duration'
)

# ============================================================================
# KAFKA PRODUCER (optional)
# ============================================================================

kafka_producer = None

if ENABLE_KAFKA:
    try:
        from aiokafka import AIOKafkaProducer
        logger.info("Kafka enabled")
    except ImportError:
        logger.warning("aiokafka not installed, Kafka disabled")
        ENABLE_KAFKA = False

async def init_kafka():
    """Initialize Kafka producer"""
    if not ENABLE_KAFKA:
        return None

    global kafka_producer
    try:
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy'
        )
        await kafka_producer.start()
        logger.info(f"Kafka producer started: {KAFKA_BROKERS}")
        return kafka_producer
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        return None

async def send_to_kafka(metrics: List[Metric]):
    """Send metrics to Kafka topic"""
    if not kafka_producer:
        return

    try:
        for metric in metrics:
            await kafka_producer.send(
                'system.telemetry.raw',
                value=metric.to_dict()
            )
        await kafka_producer.flush()
        metrics_sent_total.labels(destination='kafka').inc(len(metrics))
    except Exception as e:
        logger.error(f"Error sending to Kafka: {e}")

# ============================================================================
# KNOWLEDGE BASE CLIENT
# ============================================================================

kb_session: aiohttp.ClientSession = None

async def init_kb_client():
    """Initialize KB HTTP client"""
    global kb_session
    kb_session = aiohttp.ClientSession(
        base_url=KB_API_URL,
        timeout=aiohttp.ClientTimeout(total=30)
    )
    logger.info(f"KB client initialized: {KB_API_URL}")

async def send_to_kb(metrics: List[Metric]):
    """Send metrics to Knowledge Base"""
    if not kb_session:
        return

    try:
        # Batch insert
        payload = [m.to_dict() for m in metrics]

        async with kb_session.post('/metrics/batch', json=payload) as response:
            if response.status == 201:
                metrics_sent_total.labels(destination='kb').inc(len(metrics))
                logger.debug(f"Sent {len(metrics)} metrics to KB")
            else:
                error = await response.text()
                logger.error(f"KB error {response.status}: {error}")

    except Exception as e:
        logger.error(f"Error sending to KB: {e}")

# ============================================================================
# COLLECTION LOOP
# ============================================================================

collector_manager = CollectorManager()
collection_task = None

async def collection_loop():
    """Main collection loop"""
    logger.info(f"Starting collection loop (interval={COLLECTION_INTERVAL}s)")

    while True:
        try:
            # Collect metrics
            with collection_duration.time():
                metrics = await collector_manager.collect_all()

            metrics_collected_total.labels(service='system').inc(len(metrics))

            # Update Prometheus gauges
            for metric in metrics:
                if metric.metric_name == "cpu_usage_percent" and not metric.tags:
                    cpu_usage.set(metric.metric_value)
                elif metric.metric_name == "memory_usage_percent":
                    memory_usage.set(metric.metric_value)
                elif metric.metric_name == "gpu_usage_percent" and metric.tags:
                    gpu_usage.labels(gpu_id=metric.tags['gpu_id']).set(metric.metric_value)
                elif metric.metric_name == "disk_usage_percent" and metric.tags:
                    disk_usage.labels(mountpoint=metric.tags['mountpoint']).set(metric.metric_value)

            # Send to destinations
            await asyncio.gather(
                send_to_kb(metrics),
                send_to_kafka(metrics),
                return_exceptions=True
            )

        except Exception as e:
            logger.error(f"Error in collection loop: {e}")
            collection_errors_total.labels(collector='main').inc()

        await asyncio.sleep(COLLECTION_INTERVAL)

# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting HCL Monitor Service...")

    # Initialize clients
    await init_kb_client()
    await init_kafka()

    # Add services to monitor (from environment)
    services_to_monitor = os.getenv("SERVICES_TO_MONITOR", "")
    for service_config in services_to_monitor.split(";"):
        if service_config:
            parts = service_config.split(",")
            if len(parts) == 2:
                service_name, endpoint = parts
                collector_manager.add_service(service_name.strip(), endpoint.strip())

    # Start collection loop
    global collection_task
    collection_task = asyncio.create_task(collection_loop())

    logger.info("Monitor service ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Stop collection
    if collection_task:
        collection_task.cancel()
        try:
            await collection_task
        except asyncio.CancelledError:
            pass

    # Close clients
    await collector_manager.close()

    if kb_session:
        await kb_session.close()

    if kafka_producer:
        await kafka_producer.stop()

    logger.info("Shutdown complete")

app = FastAPI(
    title="HCL Monitor API",
    description="System metrics collection for HCL",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "collection_interval": COLLECTION_INTERVAL,
        "kb_connected": kb_session is not None,
        "kafka_enabled": ENABLE_KAFKA,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.get("/metrics/latest")
async def get_latest_metrics():
    """Get latest collected metrics (for debugging)"""
    metrics = await collector_manager.collect_all()
    return {
        "count": len(metrics),
        "metrics": [m.to_dict() for m in metrics[:100]]  # Limit to 100
    }

@app.post("/collect/trigger")
async def trigger_collection(background_tasks: BackgroundTasks):
    """Manually trigger a collection (for testing)"""
    async def collect_and_send():
        metrics = await collector_manager.collect_all()
        await asyncio.gather(
            send_to_kb(metrics),
            send_to_kafka(metrics),
            return_exceptions=True
        )

    background_tasks.add_task(collect_and_send)
    return {"status": "collection triggered"}

@app.get("/collectors")
async def list_collectors():
    """List active collectors"""
    return {
        "system_collectors": [c.__class__.__name__ for c in collector_manager.collectors],
        "service_collectors": [
            {"name": c.service_name, "endpoint": c.endpoint}
            for c in collector_manager.service_collectors
        ]
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable in production
        log_level="info"
    )
