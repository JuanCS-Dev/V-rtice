"""HCL Knowledge Base Service - Main FastAPI Application.

This service provides a persistent storage layer for the HCL ecosystem. It uses
a PostgreSQL database with the TimescaleDB extension to efficiently store and
query time-series metrics, HCL decisions, and ML model versions.

It exposes a RESTful API for other HCL services (Monitor, Planner, Executor)
to record and retrieve data.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func, and_
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
import os
import logging
import uuid

from .models import (
    Base, HCLDecision, SystemMetric, HCLModelVersion,
    DecisionCreate, DecisionUpdate, DecisionResponse,
    MetricCreate, ModelVersionCreate, ModelVersionResponse
)

# ============================================================================
# Configuration and Database Setup
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/hcl_kb")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    """Provides a database session dependency for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    logger.info("Starting HCL Knowledge Base Service...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified.")
    yield
    await engine.dispose()
    logger.info("HCL Knowledge Base Service shut down.")

app = FastAPI(
    title="HCL Knowledge Base API",
    description="Stores and queries HCL decisions, metrics, and model versions.",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Provides a basic health check of the service and its database connection."""
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")

@app.post("/decisions", response_model=DecisionResponse, status_code=201)
async def create_decision(decision: DecisionCreate, db: AsyncSession = Depends(get_db)):
    """Records a new HCL decision made by the Planner.

    Args:
        decision (DecisionCreate): The decision data to record.
        db (AsyncSession): The database session dependency.

    Returns:
        HCLDecision: The created decision object.
    """
    db_decision = HCLDecision(**decision.dict(), outcome="PENDING")
    db.add(db_decision)
    await db.commit()
    await db.refresh(db_decision)
    return db_decision

@app.patch("/decisions/{decision_id}", response_model=DecisionResponse)
async def update_decision(decision_id: uuid.UUID, update: DecisionUpdate, db: AsyncSession = Depends(get_db)):
    """Updates a decision with its outcome and measured results.

    Args:
        decision_id (uuid.UUID): The ID of the decision to update.
        update (DecisionUpdate): The update data, including the final state and outcome.
        db (AsyncSession): The database session dependency.

    Returns:
        HCLDecision: The updated decision object.
    """
    result = await db.execute(select(HCLDecision).where(HCLDecision.id == decision_id))
    db_decision = result.scalar_one_or_none()
    if not db_decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_decision, key, value)
    
    await db.commit()
    await db.refresh(db_decision)
    return db_decision

@app.post("/metrics/batch", status_code=201)
async def create_metrics_batch(metrics: List[MetricCreate], db: AsyncSession = Depends(get_db)):
    """Receives and stores a batch of system metrics from the HCL Monitor.

    Args:
        metrics (List[MetricCreate]): A list of metric data points.
        db (AsyncSession): The database session dependency.

    Returns:
        Dict: A confirmation of the number of metrics inserted.
    """
    db_metrics = [SystemMetric(**m.dict()) for m in metrics]
    db.add_all(db_metrics)
    await db.commit()
    return {"inserted": len(db_metrics)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)