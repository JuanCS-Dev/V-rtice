"""Tatacá Ingestion Service - Main Application.

ETL pipeline service for ingesting criminal investigation data from multiple
sources into the Vertice platform.

Coordinates data extraction, transformation, and loading into both PostgreSQL
(Aurora) and Neo4j (Seriema Graph) for structured storage and graph analysis.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    IngestJobRequest,
    IngestJobResponse,
    IngestJobStatus,
    JobStatus,
    DataSource,
    EntityType
)
from scheduler import JobScheduler
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Global scheduler instance
scheduler: Optional[JobScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global scheduler

    logger.info("🔄 Starting Tatacá Ingestion Service...")

    # Initialize scheduler
    scheduler = JobScheduler()
    await scheduler.initialize()

    logger.info("✅ Tatacá Ingestion Service started successfully")

    yield

    # Shutdown
    logger.info("🔄 Shutting down Tatacá Ingestion Service...")

    if scheduler:
        await scheduler.shutdown()

    logger.info("✅ Tatacá Ingestion Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Tatacá Ingestion Service",
    description="ETL pipeline for criminal investigation data ingestion",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Models

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    postgres_healthy: bool
    neo4j_healthy: bool
    active_jobs: int


class TriggerIngestRequest(BaseModel):
    """Quick ingestion trigger request."""
    source: DataSource
    entity_type: Optional[EntityType] = None
    filters: Dict[str, Any] = {}


# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns service status and component health.
    """
    postgres_healthy = False
    neo4j_healthy = False
    active_jobs = 0

    if scheduler:
        # Check PostgreSQL
        if scheduler.postgres_loader:
            postgres_healthy = await scheduler.postgres_loader.health_check()

        # Check Neo4j
        if scheduler.neo4j_loader:
            neo4j_healthy = await scheduler.neo4j_loader.health_check()

        # Count active jobs
        active_jobs = len(scheduler.running_jobs)

    return HealthResponse(
        status="healthy",
        service="tataca_ingestion",
        version="1.0.0",
        postgres_healthy=postgres_healthy,
        neo4j_healthy=neo4j_healthy,
        active_jobs=active_jobs
    )


@app.post("/jobs", response_model=IngestJobResponse)
async def create_job(request: IngestJobRequest):
    """
    Create a new ingestion job.

    Creates and queues a job to ingest data from the specified source with
    optional filtering and destination configuration.

    Args:
        request: Job creation request

    Returns:
        Job creation response with job ID

    Raises:
        HTTPException: If job creation fails
    """
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not initialized")

        response = await scheduler.create_job(request)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/jobs/{job_id}", response_model=IngestJobStatus)
async def get_job_status(job_id: str):
    """
    Get status of a specific job.

    Args:
        job_id: Job identifier

    Returns:
        Job status information

    Raises:
        HTTPException: If job not found
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    job_status = await scheduler.get_job_status(job_id)

    if not job_status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job_status


@app.get("/jobs", response_model=List[IngestJobStatus])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return")
):
    """
    List ingestion jobs.

    Args:
        status: Optional status filter
        limit: Maximum number of jobs to return

    Returns:
        List of job statuses
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    jobs = await scheduler.list_jobs(status_filter=status, limit=limit)
    return jobs


@app.post("/ingest/trigger", response_model=IngestJobResponse)
async def trigger_ingestion(request: TriggerIngestRequest):
    """
    Quick trigger for data ingestion.

    Convenience endpoint to quickly trigger ingestion from a data source
    without needing to configure all job parameters.

    Args:
        request: Trigger request

    Returns:
        Job creation response
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    # Build full job request
    job_request = IngestJobRequest(
        source=request.source,
        entity_type=request.entity_type,
        filters=request.filters,
        load_to_postgres=True,
        load_to_neo4j=True,
        metadata={"triggered_via": "quick_trigger"}
    )

    response = await scheduler.create_job(job_request)
    return response


@app.get("/sources", response_model=Dict[str, Any])
async def list_data_sources():
    """
    List available data sources.

    Returns information about configured data sources and their status.

    Returns:
        Dictionary of data sources and their availability
    """
    sources = {
        "sinesp": {
            "enabled": settings.ENABLE_SINESP_CONNECTOR,
            "description": "Sistema Nacional de Informações de Segurança Pública",
            "entities": ["veiculo", "ocorrencia"],
            "url": settings.SINESP_SERVICE_URL
        },
        "prisional": {
            "enabled": settings.ENABLE_PRISIONAL_CONNECTOR,
            "description": "Sistema Prisional",
            "entities": ["pessoa"],
            "status": "not_implemented"
        },
        "antecedentes": {
            "enabled": settings.ENABLE_ANTECEDENTES_CONNECTOR,
            "description": "Antecedentes Criminais",
            "entities": ["pessoa", "ocorrencia"],
            "status": "not_implemented"
        }
    }

    return {
        "sources": sources,
        "total": len(sources),
        "enabled": sum(1 for s in sources.values() if s.get("enabled"))
    }


@app.get("/entities", response_model=Dict[str, Any])
async def list_entity_types():
    """
    List supported entity types.

    Returns information about entity types that can be ingested.

    Returns:
        Dictionary of entity types and their schemas
    """
    entities = {
        "pessoa": {
            "description": "Pessoa (individual)",
            "fields": ["cpf", "nome", "data_nascimento", "mae", "pai", "rg", "telefone"],
            "primary_key": "cpf",
            "relationships": ["possui", "reside_em", "envolvido_em"]
        },
        "veiculo": {
            "description": "Veículo (vehicle)",
            "fields": ["placa", "renavam", "chassi", "marca", "modelo", "ano", "cor", "situacao"],
            "primary_key": "placa",
            "relationships": ["possui", "envolvido_em", "registrado_em"]
        },
        "endereco": {
            "description": "Endereço (address)",
            "fields": ["cep", "logradouro", "numero", "bairro", "cidade", "estado"],
            "primary_key": "composite",
            "relationships": ["reside_em", "ocorreu_em", "registrado_em"]
        },
        "ocorrencia": {
            "description": "Ocorrência criminal (criminal occurrence)",
            "fields": ["numero_bo", "tipo", "data_hora", "descricao", "local", "status"],
            "primary_key": "numero_bo",
            "relationships": ["envolvido_em", "ocorreu_em"]
        }
    }

    return {
        "entities": entities,
        "total": len(entities)
    }


@app.get("/stats", response_model=Dict[str, Any])
async def get_statistics():
    """
    Get ingestion statistics.

    Returns:
        Statistics about ingestion jobs and records
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    all_jobs = await scheduler.list_jobs(limit=10000)

    stats = {
        "total_jobs": len(all_jobs),
        "by_status": {
            "pending": sum(1 for j in all_jobs if j.status == JobStatus.PENDING),
            "running": sum(1 for j in all_jobs if j.status == JobStatus.RUNNING),
            "completed": sum(1 for j in all_jobs if j.status == JobStatus.COMPLETED),
            "failed": sum(1 for j in all_jobs if j.status == JobStatus.FAILED),
        },
        "by_source": {},
        "records_processed": sum(j.records_processed for j in all_jobs),
        "records_failed": sum(j.records_failed for j in all_jobs),
        "active_jobs": len(scheduler.running_jobs)
    }

    # Count by source
    for job in all_jobs:
        source = job.source.value
        if source not in stats["by_source"]:
            stats["by_source"][source] = 0
        stats["by_source"][source] += 1

    return stats


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or running job.

    Args:
        job_id: Job identifier

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    job_status = await scheduler.get_job_status(job_id)

    if not job_status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job_status.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in {job_status.status} status"
        )

    # Mark as cancelled
    job_status.status = JobStatus.CANCELLED
    job_status.completed_at = datetime.utcnow()

    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancelled successfully"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
