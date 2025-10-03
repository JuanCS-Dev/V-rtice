"""
HCL Analyzer Service
====================
Predictive analysis engine for HCL.
Consumes metrics from Kafka, runs ML models, publishes predictions.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import aiohttp

from models import SARIMAForecaster, IsolationForestDetector, XGBoostFailurePredictor

# Kafka
try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("aiokafka not installed")

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICE_NAME = os.getenv("SERVICE_NAME", "hcl_analyzer")
KB_API_URL = os.getenv("KB_API_URL", "http://localhost:8000")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
MODEL_DIR = os.getenv("MODEL_DIR", "/app/models")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MODEL REGISTRY
# ============================================================================

class ModelRegistry:
    """Manages all ML models"""

    def __init__(self):
        # SARIMA models (one per metric)
        self.sarima_cpu = SARIMAForecaster("cpu_usage")
        self.sarima_memory = SARIMAForecaster("memory_usage")
        self.sarima_gpu = SARIMAForecaster("gpu_usage")

        # Isolation Forest
        self.isolation_forest = IsolationForestDetector(contamination=0.01)

        # XGBoost
        self.xgboost_failure = XGBoostFailurePredictor()

        # Loaded flags
        self.models_loaded = {
            "sarima_cpu": False,
            "sarima_memory": False,
            "sarima_gpu": False,
            "isolation_forest": False,
            "xgboost_failure": False
        }

    def load_all(self, model_dir: str):
        """Load all models from disk"""
        logger.info(f"Loading models from {model_dir}")

        models = [
            ("sarima_cpu", self.sarima_cpu, f"{model_dir}/sarima_cpu.pkl"),
            ("sarima_memory", self.sarima_memory, f"{model_dir}/sarima_memory.pkl"),
            ("sarima_gpu", self.sarima_gpu, f"{model_dir}/sarima_gpu.pkl"),
            ("isolation_forest", self.isolation_forest, f"{model_dir}/isolation_forest.pkl"),
            ("xgboost_failure", self.xgboost_failure, f"{model_dir}/xgboost_failure.pkl")
        ]

        for name, model, path in models:
            try:
                if os.path.exists(path):
                    model.load(path)
                    self.models_loaded[name] = True
                    logger.info(f"✓ Loaded {name}")
                else:
                    logger.warning(f"✗ Model not found: {path}")
            except Exception as e:
                logger.error(f"✗ Failed to load {name}: {e}")

    def save_all(self, model_dir: str):
        """Save all models to disk"""
        os.makedirs(model_dir, exist_ok=True)

        models = [
            ("sarima_cpu", self.sarima_cpu, f"{model_dir}/sarima_cpu.pkl"),
            ("sarima_memory", self.sarima_memory, f"{model_dir}/sarima_memory.pkl"),
            ("sarima_gpu", self.sarima_gpu, f"{model_dir}/sarima_gpu.pkl"),
            ("isolation_forest", self.isolation_forest, f"{model_dir}/isolation_forest.pkl"),
            ("xgboost_failure", self.xgboost_failure, f"{model_dir}/xgboost_failure.pkl")
        ]

        for name, model, path in models:
            try:
                model.save(path)
                logger.info(f"✓ Saved {name}")
            except Exception as e:
                logger.error(f"✗ Failed to save {name}: {e}")


registry = ModelRegistry()

# ============================================================================
# KNOWLEDGE BASE CLIENT
# ============================================================================

kb_session: Optional[aiohttp.ClientSession] = None

async def init_kb_client():
    """Initialize KB HTTP client"""
    global kb_session
    kb_session = aiohttp.ClientSession(
        base_url=KB_API_URL,
        timeout=aiohttp.ClientTimeout(total=30)
    )
    logger.info(f"KB client initialized: {KB_API_URL}")

async def fetch_historical_data(
    service_name: str,
    metric_name: str,
    days: int = 30
) -> pd.DataFrame:
    """Fetch historical metrics from KB"""
    if not kb_session:
        raise RuntimeError("KB client not initialized")

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    params = {
        "service_name": service_name,
        "metric_name": metric_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "aggregation": "avg",
        "interval": "1h"
    }

    try:
        async with kb_session.get("/metrics/query", params=params) as response:
            if response.status == 200:
                data = await response.json()
                df = pd.DataFrame(data['data'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.rename(columns={'value': 'metric_value'}, inplace=True)
                logger.info(f"Fetched {len(df)} data points for {metric_name}")
                return df
            else:
                error = await response.text()
                logger.error(f"KB error {response.status}: {error}")
                return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# ============================================================================
# KAFKA CONSUMER/PRODUCER
# ============================================================================

kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_producer: Optional[AIOKafkaProducer] = None

async def init_kafka():
    """Initialize Kafka consumer and producer"""
    if not KAFKA_AVAILABLE:
        logger.warning("Kafka not available")
        return

    global kafka_consumer, kafka_producer

    try:
        # Consumer (metrics from Monitor)
        kafka_consumer = AIOKafkaConsumer(
            'system.telemetry.raw',
            bootstrap_servers=KAFKA_BROKERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='hcl_analyzer',
            auto_offset_reset='latest'
        )
        await kafka_consumer.start()
        logger.info("Kafka consumer started: system.telemetry.raw")

        # Producer (predictions)
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy'
        )
        await kafka_producer.start()
        logger.info("Kafka producer started")

    except Exception as e:
        logger.error(f"Failed to start Kafka: {e}")

async def publish_prediction(prediction: Dict):
    """Publish prediction to Kafka"""
    if kafka_producer:
        try:
            await kafka_producer.send('system.predictions', value=prediction)
            logger.debug(f"Published prediction: {prediction['type']}")
        except Exception as e:
            logger.error(f"Error publishing prediction: {e}")

# ============================================================================
# ANALYSIS ENGINE
# ============================================================================

class AnalysisEngine:
    """Runs analysis on incoming metrics"""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.metrics_buffer = []
        self.buffer_size = 100

    async def process_metric(self, metric: Dict):
        """Process incoming metric"""
        # Add to buffer
        self.metrics_buffer.append(metric)

        # Keep buffer size limited
        if len(self.metrics_buffer) > self.buffer_size:
            self.metrics_buffer = self.metrics_buffer[-self.buffer_size:]

        # Run analysis every N metrics
        if len(self.metrics_buffer) >= 20:
            await self.run_analysis()

    async def run_analysis(self):
        """Run all analysis models"""
        if len(self.metrics_buffer) < 10:
            return

        # Convert buffer to DataFrame
        df = pd.DataFrame(self.metrics_buffer)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Pivot to get metrics as columns
        try:
            df_pivot = df.pivot_table(
                index='timestamp',
                columns='metric_name',
                values='metric_value',
                aggfunc='mean'
            ).reset_index()
        except Exception as e:
            logger.warning(f"Failed to pivot data: {e}")
            return

        # Run anomaly detection
        if self.registry.models_loaded['isolation_forest']:
            try:
                result = self.registry.isolation_forest.predict(df_pivot)
                if result['n_anomalies'] > 0:
                    await publish_prediction({
                        "type": "anomaly_detection",
                        "timestamp": datetime.utcnow().isoformat(),
                        "n_anomalies": result['n_anomalies'],
                        "details": result
                    })
                    logger.info(f"Detected {result['n_anomalies']} anomalies")
            except Exception as e:
                logger.error(f"Anomaly detection failed: {e}")

        # Run failure prediction
        if self.registry.models_loaded['xgboost_failure']:
            try:
                # Add synthetic failure column (in production, this comes from historical data)
                df_pivot['failure'] = 0

                result = self.registry.xgboost_failure.predict(df_pivot)
                if result['n_predicted_failures'] > 0:
                    await publish_prediction({
                        "type": "failure_prediction",
                        "timestamp": datetime.utcnow().isoformat(),
                        "n_predicted_failures": result['n_predicted_failures'],
                        "details": result
                    })
                    logger.warning(f"Predicted {result['n_predicted_failures']} failures")
            except Exception as e:
                logger.error(f"Failure prediction failed: {e}")


engine = AnalysisEngine(registry)

# ============================================================================
# KAFKA CONSUMER LOOP
# ============================================================================

consumer_task = None

async def kafka_consumer_loop():
    """Consume metrics from Kafka and analyze"""
    if not kafka_consumer:
        logger.warning("Kafka consumer not available, skipping consumer loop")
        return

    logger.info("Starting Kafka consumer loop")

    try:
        async for msg in kafka_consumer:
            try:
                metric = msg.value
                await engine.process_metric(metric)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except Exception as e:
        logger.error(f"Consumer loop error: {e}")

# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    # Startup
    logger.info("Starting HCL Analyzer Service...")

    # Initialize clients
    await init_kb_client()
    await init_kafka()

    # Load models
    registry.load_all(MODEL_DIR)

    # Start consumer loop
    if KAFKA_AVAILABLE:
        global consumer_task
        consumer_task = asyncio.create_task(kafka_consumer_loop())

    logger.info("Analyzer service ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")

    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    if kafka_consumer:
        await kafka_consumer.stop()

    if kafka_producer:
        await kafka_producer.stop()

    if kb_session:
        await kb_session.close()

    logger.info("Shutdown complete")

app = FastAPI(
    title="HCL Analyzer API",
    description="Predictive analysis engine for HCL",
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
        "models_loaded": registry.models_loaded,
        "kafka_connected": kafka_consumer is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/train/sarima/{metric_name}")
async def train_sarima(
    metric_name: str,
    background_tasks: BackgroundTasks,
    days: int = 30
):
    """Train SARIMA model"""
    async def train_task():
        # Fetch data
        df = await fetch_historical_data("system", f"{metric_name}_percent", days)

        if df.empty:
            logger.error(f"No data for {metric_name}")
            return

        # Train model
        if metric_name == "cpu_usage":
            model = registry.sarima_cpu
        elif metric_name == "memory_usage":
            model = registry.sarima_memory
        elif metric_name == "gpu_usage":
            model = registry.sarima_gpu
        else:
            logger.error(f"Unknown metric: {metric_name}")
            return

        try:
            metrics = model.train(df)
            registry.models_loaded[f"sarima_{metric_name}"] = True
            registry.save_all(MODEL_DIR)
            logger.info(f"Training complete: {metric_name} - {metrics}")
        except Exception as e:
            logger.error(f"Training failed: {e}")

    background_tasks.add_task(train_task)
    return {"status": "training started", "metric": metric_name}

@app.post("/train/isolation_forest")
async def train_isolation_forest(background_tasks: BackgroundTasks, days: int = 30):
    """Train Isolation Forest"""
    async def train_task():
        # Fetch multiple metrics
        metrics_to_fetch = ["cpu_usage", "memory_usage", "gpu_usage"]
        dfs = []

        for metric in metrics_to_fetch:
            df = await fetch_historical_data("system", f"{metric}_percent", days)
            if not df.empty:
                df.rename(columns={'metric_value': metric}, inplace=True)
                dfs.append(df[['timestamp', metric]])

        if not dfs:
            logger.error("No data for Isolation Forest training")
            return

        # Merge dataframes
        merged = dfs[0]
        for df in dfs[1:]:
            merged = pd.merge(merged, df, on='timestamp', how='outer')

        merged.fillna(method='ffill', inplace=True)

        # Train
        try:
            metrics = registry.isolation_forest.train(merged)
            registry.models_loaded["isolation_forest"] = True
            registry.save_all(MODEL_DIR)
            logger.info(f"IF training complete: {metrics}")
        except Exception as e:
            logger.error(f"IF training failed: {e}")

    background_tasks.add_task(train_task)
    return {"status": "training started"}

@app.get("/predict/sarima/{metric_name}")
async def predict_sarima(metric_name: str, hours: int = 24):
    """Get SARIMA prediction"""
    if metric_name == "cpu_usage":
        model = registry.sarima_cpu
        model_key = "sarima_cpu_usage"
    elif metric_name == "memory_usage":
        model = registry.sarima_memory
        model_key = "sarima_memory_usage"
    elif metric_name == "gpu_usage":
        model = registry.sarima_gpu
        model_key = "sarima_gpu_usage"
    else:
        raise HTTPException(status_code=400, detail="Unknown metric")

    if not registry.models_loaded.get(model_key, False):
        raise HTTPException(status_code=503, detail="Model not trained")

    try:
        prediction = model.predict(steps=hours)
        return {
            "metric": metric_name,
            "forecast_hours": hours,
            "prediction": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/status")
async def models_status():
    """Get models status"""
    return {
        "loaded": registry.models_loaded,
        "last_trained": {
            "sarima_cpu": registry.sarima_cpu.last_trained.isoformat() if registry.sarima_cpu.last_trained else None,
            "sarima_memory": registry.sarima_memory.last_trained.isoformat() if registry.sarima_memory.last_trained else None,
            "sarima_gpu": registry.sarima_gpu.last_trained.isoformat() if registry.sarima_gpu.last_trained else None,
            "isolation_forest": registry.isolation_forest.last_trained.isoformat() if registry.isolation_forest.last_trained else None,
            "xgboost_failure": registry.xgboost_failure.last_trained.isoformat() if registry.xgboost_failure.last_trained else None
        }
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )
