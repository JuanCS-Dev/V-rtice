"""HCL Analyzer Service - Predictive Analysis Engine.

This service acts as a predictive analysis engine for the HCL (Hardware
Compatibility List) ecosystem. It consumes system telemetry from a Kafka topic,
runs machine learning models to forecast resource usage and predict failures,
and publishes the resulting predictions back to Kafka.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict
import pandas as pd

from .models import SARIMAForecaster, IsolationForestDetector, XGBoostFailurePredictor

# Conditional Kafka import
try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

# ============================================================================
# Configuration and Initialization
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
MODEL_DIR = "/app/models"

class ModelRegistry:
    """A simple registry to manage all machine learning models."""
    def __init__(self):
        self.sarima_cpu = SARIMAForecaster("cpu_usage")
        self.isolation_forest = IsolationForestDetector()
        self.xgboost_failure = XGBoostFailurePredictor()
        self.models_loaded = {"sarima_cpu": False, "isolation_forest": False, "xgboost_failure": False}

    def load_all(self, model_dir: str):
        """Loads all registered models from the specified directory."""
        for name, model in [("sarima_cpu", self.sarima_cpu), ("isolation_forest", self.isolation_forest)]:
            path = f"{model_dir}/{name}.pkl"
            if os.path.exists(path):
                model.load(path)
                self.models_loaded[name] = True

registry = ModelRegistry()

# ============================================================================
# Kafka Consumer and Producer Logic
# ============================================================================

async def kafka_consumer_loop(consumer, producer):
    """The main loop for consuming metrics and producing predictions."""
    logger.info("Starting Kafka consumer loop...")
    async for msg in consumer:
        try:
            metric = msg.value
            # In a real implementation, this would trigger analysis
            # For now, we just log it.
            logger.debug(f"Received metric: {metric}")
        except Exception as e:
            logger.error(f"Error processing Kafka message: {e}")

# ============================================================================
# FastAPI Lifespan and Application Setup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    logger.info("Starting HCL Analyzer Service...")
    registry.load_all(MODEL_DIR)
    
    consumer_task = None
    if KAFKA_AVAILABLE:
        consumer = AIOKafkaConsumer('system.telemetry.raw', bootstrap_servers=KAFKA_BROKERS, value_deserializer=lambda m: json.loads(m.decode('utf-8')))
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        await consumer.start()
        await producer.start()
        consumer_task = asyncio.create_task(kafka_consumer_loop(consumer, producer))
    
    yield
    
    logger.info("Shutting down HCL Analyzer Service...")
    if consumer_task: consumer_task.cancel()
    if KAFKA_AVAILABLE:
        await consumer.stop()
        await producer.stop()

app = FastAPI(
    title="HCL Analyzer Service",
    description="Predictive analysis engine for HCL metrics.",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Provides a health check of the service, including model status."""
    return {
        "status": "healthy",
        "models_loaded": registry.models_loaded,
        "kafka_available": KAFKA_AVAILABLE
    }

@app.post("/train/sarima/{metric_name}", status_code=202)
async def train_sarima(metric_name: str, background_tasks: BackgroundTasks):
    """Triggers a background task to train a SARIMA forecasting model.

    Args:
        metric_name (str): The name of the metric to train (e.g., 'cpu_usage').
        background_tasks (BackgroundTasks): FastAPI background task manager.
    """
    def train_task():
        # Placeholder for fetching data and training
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(pd.date_range(end=datetime.utcnow(), periods=100, freq='H')),
            'metric_value': np.random.rand(100) * 100
        })
        if metric_name == "cpu_usage":
            registry.sarima_cpu.train(df)
            registry.sarima_cpu.save(f"{MODEL_DIR}/sarima_cpu.pkl")
            registry.models_loaded["sarima_cpu"] = True

    background_tasks.add_task(train_task)
    return {"message": f"SARIMA training started for {metric_name}."}

@app.get("/predict/sarima/{metric_name}")
async def predict_sarima(metric_name: str, hours: int = 24):
    """Generates a forecast using a trained SARIMA model.

    Args:
        metric_name (str): The metric to forecast (e.g., 'cpu_usage').
        hours (int): The number of hours into the future to forecast.

    Returns:
        Dict: The forecast, including predictions and confidence intervals.
    """
    if not registry.models_loaded.get(f"sarima_{metric_name}"):
        raise HTTPException(status_code=503, detail=f"SARIMA model for {metric_name} is not trained.")
    
    model = registry.sarima_cpu # Simplified for example
    prediction = model.predict(steps=hours)
    return {"metric": metric_name, "forecast": prediction}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)