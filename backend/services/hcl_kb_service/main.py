"""
HCL Knowledge Base Service
===========================
FastAPI service for storing and querying HCL decisions, metrics, and model versions.
Production-ready with async PostgreSQL + TimescaleDB.
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timedelta
import os
import logging
import uuid

from models import (
    Base, HCLDecision, SystemMetric, HCLModelVersion,
    DecisionCreate, DecisionUpdate, DecisionResponse,
    MetricCreate, MetricQuery,
    ModelVersionCreate, ModelVersionResponse,
    AnalyticsQuery, AnalyticsResponse
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://vertice:vertice@localhost:5432/hcl_kb"
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

# Async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Dependency for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting HCL Knowledge Base Service...")

    # Create tables (in production, use Alembic migrations)
    async with engine.begin() as conn:
        # Note: TimescaleDB hypertable creation handled by schema.sql
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")
    logger.info("Service ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()
    logger.info("Shutdown complete")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="HCL Knowledge Base API",
    description="Stores and queries HCL decisions, metrics, and model versions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(select(1))
        return {
            "status": "healthy",
            "service": "hcl_kb_service",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ============================================================================
# DECISIONS API
# ============================================================================

@app.post("/decisions", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    decision: DecisionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a new HCL decision.
    Called by HCL Planner after making a decision.
    """
    try:
        db_decision = HCLDecision(
            trigger_type=decision.trigger_type,
            trigger_details=decision.trigger_details,
            operational_mode=decision.operational_mode,
            previous_mode=decision.previous_mode,
            actions_taken=[action.model_dump() for action in decision.actions_taken],
            state_before=decision.state_before.model_dump(),
            decision_latency_ms=decision.decision_latency_ms,
            planner_used=decision.planner_used,
            outcome="PENDING"  # Will be updated later
        )

        db.add(db_decision)
        await db.commit()
        await db.refresh(db_decision)

        logger.info(f"Decision created: {db_decision.id} mode={decision.operational_mode}")
        return db_decision

    except Exception as e:
        logger.error(f"Error creating decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/decisions/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: uuid.UUID,
    update: DecisionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update decision with outcome after measuring results.
    Called by HCL Monitor 5 minutes after action execution.
    """
    try:
        result = await db.execute(
            select(HCLDecision).where(HCLDecision.id == decision_id)
        )
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        decision.state_after = update.state_after.model_dump()
        decision.outcome = update.outcome
        decision.outcome_measured_at = datetime.utcnow()
        decision.execution_latency_ms = update.execution_latency_ms

        # Compute reward signal if provided
        if update.reward_signal is not None:
            decision.reward_signal = update.reward_signal
        else:
            # Auto-compute basic reward
            state_before = decision.state_before
            state_after = update.state_after.model_dump()

            # Simple reward: negative delta in resource usage is good
            cpu_delta = state_after['cpu_usage'] - state_before['cpu_usage']
            memory_delta = state_after['memory_usage'] - state_before['memory_usage']
            latency_delta = state_after['network_latency_p99'] - state_before['network_latency_p99']

            reward = 0.0
            if update.outcome == "SUCCESS":
                reward += 10.0
                reward -= (cpu_delta * 0.1)  # Penalize CPU increase
                reward -= (memory_delta * 0.1)  # Penalize memory increase
                reward -= (latency_delta * 0.05)  # Penalize latency increase
            elif update.outcome == "FAILED":
                reward = -10.0

            decision.reward_signal = reward

        await db.commit()
        await db.refresh(decision)

        logger.info(f"Decision updated: {decision_id} outcome={update.outcome} reward={decision.reward_signal:.2f}")
        return decision

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get decision by ID"""
    result = await db.execute(
        select(HCLDecision).where(HCLDecision.id == decision_id)
    )
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision


@app.get("/decisions", response_model=List[DecisionResponse])
async def list_decisions(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    operational_mode: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    planner_used: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List decisions with filters"""
    query = select(HCLDecision).order_by(HCLDecision.timestamp.desc())

    # Filters
    conditions = []
    if start_time:
        conditions.append(HCLDecision.timestamp >= start_time)
    if end_time:
        conditions.append(HCLDecision.timestamp <= end_time)
    if operational_mode:
        conditions.append(HCLDecision.operational_mode == operational_mode)
    if outcome:
        conditions.append(HCLDecision.outcome == outcome)
    if planner_used:
        conditions.append(HCLDecision.planner_used == planner_used)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    decisions = result.scalars().all()

    return decisions


# ============================================================================
# METRICS API
# ============================================================================

@app.post("/metrics/batch", status_code=status.HTTP_201_CREATED)
async def create_metrics_batch(
    metrics: List[MetricCreate],
    db: AsyncSession = Depends(get_db)
):
    """
    Batch insert metrics (high-performance).
    Called by HCL Monitor every 15 seconds.
    """
    try:
        db_metrics = [
            SystemMetric(
                timestamp=m.timestamp or datetime.utcnow(),
                service_name=m.service_name,
                metric_name=m.metric_name,
                metric_value=m.metric_value,
                tags=m.tags
            )
            for m in metrics
        ]

        db.add_all(db_metrics)
        await db.commit()

        logger.debug(f"Inserted {len(metrics)} metrics")
        return {"inserted": len(metrics)}

    except Exception as e:
        logger.error(f"Error inserting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/query")
async def query_metrics(
    service_name: str = Query(...),
    metric_name: str = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    aggregation: str = Query("avg", regex="^(avg|max|min|stddev)$"),
    interval: str = Query("1m", regex="^(1m|5m|1h|1d)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Query metrics with time-bucketing and aggregation.
    Uses TimescaleDB time_bucket for performance.
    """
    try:
        # Map aggregation
        agg_func = {
            "avg": func.avg,
            "max": func.max,
            "min": func.min,
            "stddev": func.stddev
        }[aggregation]

        # Map interval to PostgreSQL interval
        bucket_interval = {
            "1m": "1 minute",
            "5m": "5 minutes",
            "1h": "1 hour",
            "1d": "1 day"
        }[interval]

        # Use continuous aggregate if available (faster)
        if interval in ["1m", "5m"]:
            # Query pre-computed aggregate
            query = select(
                func.time_bucket(bucket_interval, SystemMetric.timestamp).label("bucket"),
                agg_func(SystemMetric.metric_value).label("value")
            ).where(
                and_(
                    SystemMetric.service_name == service_name,
                    SystemMetric.metric_name == metric_name,
                    SystemMetric.timestamp >= start_time,
                    SystemMetric.timestamp <= end_time
                )
            ).group_by("bucket").order_by("bucket")
        else:
            # Query raw data
            query = select(
                func.time_bucket(bucket_interval, SystemMetric.timestamp).label("bucket"),
                agg_func(SystemMetric.metric_value).label("value")
            ).where(
                and_(
                    SystemMetric.service_name == service_name,
                    SystemMetric.metric_name == metric_name,
                    SystemMetric.timestamp >= start_time,
                    SystemMetric.timestamp <= end_time
                )
            ).group_by("bucket").order_by("bucket")

        result = await db.execute(query)
        data = result.fetchall()

        return {
            "service": service_name,
            "metric": metric_name,
            "aggregation": aggregation,
            "interval": interval,
            "data": [{"timestamp": row[0].isoformat(), "value": float(row[1])} for row in data]
        }

    except Exception as e:
        logger.error(f"Error querying metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL VERSIONS API
# ============================================================================

@app.post("/models", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
async def register_model_version(
    model: ModelVersionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register new ML model version after training"""
    try:
        db_model = HCLModelVersion(
            model_name=model.model_name,
            version=model.version,
            training_dataset_start=model.training_dataset_start,
            training_dataset_end=model.training_dataset_end,
            training_samples=model.training_samples,
            metrics=model.metrics,
            model_path=model.model_path,
            model_size_bytes=model.model_size_bytes,
            hyperparameters=model.hyperparameters,
            training_duration_seconds=model.training_duration_seconds,
            training_logs=model.training_logs
        )

        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)

        logger.info(f"Model registered: {model.model_name} v{model.version}")
        return db_model

    except Exception as e:
        logger.error(f"Error registering model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Deploy model version (mark as active)"""
    try:
        # Get model
        result = await db.execute(
            select(HCLModelVersion).where(HCLModelVersion.id == model_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Undeploy previous versions
        await db.execute(
            select(HCLModelVersion).where(
                and_(
                    HCLModelVersion.model_name == model.model_name,
                    HCLModelVersion.deployed == True
                )
            )
        )
        previous = result.scalars().all()
        for prev in previous:
            prev.deployed = False

        # Deploy this version
        model.deployed = True
        model.deployed_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Model deployed: {model.model_name} v{model.version}")
        return {"status": "deployed", "model": model.model_name, "version": model.version}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_name}/deployed", response_model=ModelVersionResponse)
async def get_deployed_model(
    model_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get currently deployed model version"""
    result = await db.execute(
        select(HCLModelVersion).where(
            and_(
                HCLModelVersion.model_name == model_name,
                HCLModelVersion.deployed == True
            )
        )
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail=f"No deployed model for {model_name}")

    return model


# ============================================================================
# ANALYTICS API
# ============================================================================

@app.get("/analytics/summary")
async def get_analytics_summary(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get HCL performance summary"""
    try:
        # Total decisions
        total_result = await db.execute(
            select(func.count()).select_from(HCLDecision).where(
                and_(
                    HCLDecision.timestamp >= start_time,
                    HCLDecision.timestamp <= end_time
                )
            )
        )
        total = total_result.scalar()

        # Success rate
        success_result = await db.execute(
            select(func.count()).select_from(HCLDecision).where(
                and_(
                    HCLDecision.timestamp >= start_time,
                    HCLDecision.timestamp <= end_time,
                    HCLDecision.outcome == "SUCCESS"
                )
            )
        )
        success = success_result.scalar()

        success_rate = (success / total * 100) if total > 0 else 0.0

        # Average reward
        reward_result = await db.execute(
            select(func.avg(HCLDecision.reward_signal)).where(
                and_(
                    HCLDecision.timestamp >= start_time,
                    HCLDecision.timestamp <= end_time,
                    HCLDecision.reward_signal.isnot(None)
                )
            )
        )
        avg_reward = reward_result.scalar() or 0.0

        # Mode distribution
        mode_result = await db.execute(
            select(
                HCLDecision.operational_mode,
                func.count().label("count")
            ).where(
                and_(
                    HCLDecision.timestamp >= start_time,
                    HCLDecision.timestamp <= end_time
                )
            ).group_by(HCLDecision.operational_mode)
        )
        mode_dist = {row[0]: row[1] for row in mode_result.fetchall()}

        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_decisions": total,
            "success_count": success,
            "success_rate": round(success_rate, 2),
            "avg_reward": round(avg_reward, 2),
            "mode_distribution": mode_dist
        }

    except Exception as e:
        logger.error(f"Error computing analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
