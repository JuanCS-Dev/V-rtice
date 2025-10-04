"""HCL Monitor Service - Main FastAPI Application.

This service is the "Interoception" of the Maximus AI's Unconscious Layer. It is
responsible for continuously collecting system and service metrics in real-time
and publishing them to the HCL Knowledge Base (via REST) and a Kafka topic for
consumption by other services like the HCL Analyzer.
"""

from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import asyncio
import aiohttp
import logging
import os
import json
from typing import List

from .collectors import CollectorManager, Metric

# ============================================================================
# Configuration and Initialization
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", "15"))
KB_API_URL = os.getenv("KB_API_URL", "http://localhost:8000")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
ENABLE_KAFKA = os.getenv("ENABLE_KAFKA", "false").lower() == "true"

# Global state dictionary
state = {}

# Conditional Kafka import
if ENABLE_KAFKA:
    try:
        from aiokafka import AIOKafkaProducer
        state['kafka_available'] = True
    except ImportError:
        logger.warning("aiokafka not found, Kafka is disabled.")
        state['kafka_available'] = False
else:
    state['kafka_available'] = False

# ============================================================================
# Kafka and KB Integration
# ============================================================================

async def send_to_kafka(metrics: List[Metric]):
    """Sends a list of metrics to the configured Kafka topic."""
    if not state.get('kafka_producer'): return
    try:
        for metric in metrics:
            await state['kafka_producer'].send('system.telemetry.raw', value=metric.to_dict())
        await state['kafka_producer'].flush()
    except Exception as e:
        logger.error(f"Failed to send metrics to Kafka: {e}")

async def send_to_kb(metrics: List[Metric]):
    """Sends a batch of metrics to the HCL Knowledge Base service."""
    if not state.get('kb_session'): return
    try:
        payload = [m.to_dict() for m in metrics]
        async with state['kb_session'].post('/metrics/batch', json=payload) as response:
            if response.status != 201:
                logger.error(f"KB service returned error {response.status}: {await response.text()}")
    except Exception as e:
        logger.error(f"Failed to send metrics to Knowledge Base: {e}")

# ============================================================================
# Main Collection Loop
# ============================================================================

async def collection_loop():
    """The main background task that periodically collects and sends metrics."""
    logger.info(f"Starting collection loop with {COLLECTION_INTERVAL}s interval.")
    while True:
        try:
            metrics = await state['collector_manager'].collect_all()
            if metrics:
                await asyncio.gather(send_to_kb(metrics), send_to_kafka(metrics))
        except Exception as e:
            logger.error(f"Error in collection loop: {e}")
        await asyncio.sleep(COLLECTION_INTERVAL)

# ============================================================================
# FastAPI Lifespan and Application Setup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    logger.info("Starting HCL Monitor Service...")
    state['collector_manager'] = CollectorManager()
    state['kb_session'] = aiohttp.ClientSession(base_url=KB_API_URL)
    
    if state.get('kafka_available'):
        state['kafka_producer'] = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        await state['kafka_producer'].start()
    
    state['collection_task'] = asyncio.create_task(collection_loop())
    
    yield
    
    logger.info("Shutting down HCL Monitor Service...")
    state['collection_task'].cancel()
    if state.get('kb_session'): await state['kb_session'].close()
    if state.get('kafka_producer'): await state['kafka_producer'].stop()

app = FastAPI(
    title="HCL Monitor Service",
    description="Collects and distributes system metrics for the HCL ecosystem.",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Provides a basic health check of the service."""
    return {
        "status": "healthy",
        "service": "hcl_monitor",
        "kafka_enabled": state.get('kafka_available', False),
        "collection_interval_seconds": COLLECTION_INTERVAL
    }

@app.get("/metrics/latest")
async def get_latest_metrics():
    """Returns the most recently collected batch of metrics for debugging."""
    metrics = await state['collector_manager'].collect_all()
    return {"count": len(metrics), "metrics": [m.to_dict() for m in metrics]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)