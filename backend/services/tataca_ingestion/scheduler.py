"""Tatacá Ingestion - Job Scheduler.

Manages ingestion jobs with scheduling, retry logic, and concurrent execution
control.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from config import get_settings
from connectors import SinespConnector
from loaders import Neo4jLoader, PostgresLoader
from models import (
    DataSource,
    EntityType,
    IngestJobRequest,
    IngestJobResponse,
    IngestJobStatus,
    JobStatus,
)
from transformers import EntityTransformer, RelationshipExtractor

logger = logging.getLogger(__name__)
settings = get_settings()


class JobScheduler:
    """
    Manages ingestion jobs with scheduling and execution.

    Handles job creation, execution, monitoring, retry logic, and concurrent
    job management for the ETL pipeline.
    """

    def __init__(self):
        """Initialize job scheduler."""
        self.jobs: Dict[str, IngestJobStatus] = {}
        self.running_jobs: set = set()
        self.max_concurrent_jobs = settings.MAX_CONCURRENT_JOBS

        # Initialize components
        self.transformer = EntityTransformer()
        self.relationship_extractor = RelationshipExtractor()

        # Loaders (initialized on startup)
        self.postgres_loader: Optional[PostgresLoader] = None
        self.neo4j_loader: Optional[Neo4jLoader] = None

        # Background task for processing queue
        self._queue_task: Optional[asyncio.Task] = None
        self._job_queue: asyncio.Queue = asyncio.Queue()

    async def initialize(self):
        """Initialize loaders and start background workers."""
        try:
            logger.info("Initializing job scheduler...")

            # Initialize PostgreSQL loader
            self.postgres_loader = PostgresLoader()
            await self.postgres_loader.initialize()

            # Initialize Neo4j loader
            self.neo4j_loader = Neo4jLoader()
            await self.neo4j_loader.initialize()

            # Start queue processor
            self._queue_task = asyncio.create_task(self._process_queue())

            logger.info("✅ Job scheduler initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize job scheduler: {e}", exc_info=True)
            raise

    async def shutdown(self):
        """Shutdown scheduler and close loaders."""
        logger.info("Shutting down job scheduler...")

        # Cancel queue processor
        if self._queue_task:
            self._queue_task.cancel()
            try:
                await self._queue_task
            except asyncio.CancelledError:
                pass

        # Close loaders
        if self.postgres_loader:
            await self.postgres_loader.close()

        if self.neo4j_loader:
            await self.neo4j_loader.close()

        logger.info("Job scheduler shutdown complete")

    async def create_job(self, request: IngestJobRequest) -> IngestJobResponse:
        """
        Create a new ingestion job.

        Args:
            request: Job creation request

        Returns:
            Job creation response with job ID
        """
        try:
            # Generate job ID
            job_id = str(uuid.uuid4())

            # Create job status
            job_status = IngestJobStatus(
                job_id=job_id,
                status=JobStatus.PENDING,
                source=request.source,
                created_at=datetime.utcnow(),
                metadata={
                    "entity_type": (request.entity_type.value if request.entity_type else "all"),
                    "filters": request.filters,
                    "load_to_postgres": request.load_to_postgres,
                    "load_to_neo4j": request.load_to_neo4j,
                    **request.metadata,
                },
            )

            # Store job
            self.jobs[job_id] = job_status

            # Add to queue
            await self._job_queue.put((job_id, request))

            logger.info(f"Created job {job_id} for source {request.source}")

            return IngestJobResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                source=request.source,
                created_at=job_status.created_at,
                message="Job created and queued for processing",
            )

        except Exception as e:
            logger.error(f"Error creating job: {e}", exc_info=True)
            raise

    async def get_job_status(self, job_id: str) -> Optional[IngestJobStatus]:
        """
        Get status of a job.

        Args:
            job_id: Job identifier

        Returns:
            Job status or None if not found
        """
        return self.jobs.get(job_id)

    async def list_jobs(self, status_filter: Optional[JobStatus] = None, limit: int = 100) -> List[IngestJobStatus]:
        """
        List jobs with optional filtering.

        Args:
            status_filter: Filter by job status
            limit: Maximum number of jobs to return

        Returns:
            List of job statuses
        """
        jobs = list(self.jobs.values())

        # Filter by status if specified
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Apply limit
        return jobs[:limit]

    async def _process_queue(self):
        """Background worker to process job queue."""
        logger.info("Job queue processor started")

        while True:
            try:
                # Wait for job or until cancelled
                job_id, request = await self._job_queue.get()

                # Check concurrent job limit
                while len(self.running_jobs) >= self.max_concurrent_jobs:
                    await asyncio.sleep(1)

                # Execute job in background
                self.running_jobs.add(job_id)
                asyncio.create_task(self._execute_job(job_id, request))

            except asyncio.CancelledError:
                logger.info("Job queue processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in queue processor: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _execute_job(self, job_id: str, request: IngestJobRequest):
        """
        Execute an ingestion job.

        Args:
            job_id: Job identifier
            request: Job request
        """
        try:
            logger.info(f"Executing job {job_id}")

            # Update status to running
            job_status = self.jobs[job_id]
            job_status.status = JobStatus.RUNNING
            job_status.started_at = datetime.utcnow()

            # Execute based on source
            if request.source == DataSource.SINESP:
                await self._execute_sinesp_job(job_id, request)
            elif request.source == DataSource.PRISIONAL:
                await self._execute_prisional_job(job_id, request)
            elif request.source == DataSource.ANTECEDENTES:
                await self._execute_antecedentes_job(job_id, request)
            else:
                raise ValueError(f"Unsupported data source: {request.source}")

            # Update status to completed
            job_status.status = JobStatus.COMPLETED
            job_status.completed_at = datetime.utcnow()

            logger.info(
                f"Job {job_id} completed: {job_status.records_processed} processed, {job_status.records_failed} failed"
            )

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)

            # Update status to failed
            job_status = self.jobs[job_id]
            job_status.status = JobStatus.FAILED
            job_status.completed_at = datetime.utcnow()
            job_status.error_message = str(e)

        finally:
            # Remove from running set
            self.running_jobs.discard(job_id)

    async def _execute_sinesp_job(self, job_id: str, request: IngestJobRequest):
        """Execute SINESP ingestion job."""
        job_status = self.jobs[job_id]

        async with SinespConnector() as connector:
            # Check entity type
            if request.entity_type == EntityType.VEICULO:
                # Fetch vehicles
                placas = request.filters.get("placas", [])

                if placas:
                    veiculos = await connector.fetch_vehicles_batch(placas)

                    for veiculo in veiculos:
                        try:
                            # Transform
                            transform_result = self.transformer.transform_veiculo(
                                veiculo.model_dump(), DataSource.SINESP
                            )

                            if not transform_result.success:
                                job_status.records_failed += 1
                                continue

                            # Load to PostgreSQL
                            if request.load_to_postgres and self.postgres_loader:
                                await self.postgres_loader.load_entity(EntityType.VEICULO, transform_result.entity_data)

                            # Load to Neo4j
                            if request.load_to_neo4j and self.neo4j_loader:
                                await self.neo4j_loader.load_entity(EntityType.VEICULO, transform_result.entity_data)

                            job_status.records_processed += 1

                        except Exception as e:
                            logger.error(f"Error processing vehicle: {e}")
                            job_status.records_failed += 1

            elif request.entity_type == EntityType.OCORRENCIA:
                # Fetch occurrences
                ocorrencias = await connector.fetch_occurrences(request.filters)

                for ocorrencia in ocorrencias:
                    try:
                        # Transform
                        transform_result = self.transformer.transform_ocorrencia(
                            ocorrencia.model_dump(), DataSource.SINESP
                        )

                        if not transform_result.success:
                            job_status.records_failed += 1
                            continue

                        # Load to PostgreSQL
                        if request.load_to_postgres and self.postgres_loader:
                            await self.postgres_loader.load_entity(EntityType.OCORRENCIA, transform_result.entity_data)

                        # Load to Neo4j
                        if request.load_to_neo4j and self.neo4j_loader:
                            await self.neo4j_loader.load_entity(EntityType.OCORRENCIA, transform_result.entity_data)

                        job_status.records_processed += 1

                    except Exception as e:
                        logger.error(f"Error processing occurrence: {e}")
                        job_status.records_failed += 1

    async def _execute_prisional_job(self, job_id: str, request: IngestJobRequest):
        """Execute prisional system ingestion job.

        Blocked by: GitHub Issue #TATACA_PRISIONAL_CONNECTOR
        Requires: Prison system API connector implementation
        """
        logger.warning(f"Prisional connector not implemented yet for job {job_id}")
        job_status = self.jobs[job_id]
        job_status.records_processed = 0
        job_status.records_failed = 0

    async def _execute_antecedentes_job(self, job_id: str, request: IngestJobRequest):
        """Execute antecedentes ingestion job.

        Blocked by: GitHub Issue #TATACA_ANTECEDENTES_CONNECTOR
        Requires: Criminal background system API connector implementation
        """
        logger.warning(f"Antecedentes connector not implemented yet for job {job_id}")
        job_status = self.jobs[job_id]
        job_status.records_processed = 0
        job_status.records_failed = 0
