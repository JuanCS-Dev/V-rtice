"""
Reactive Fabric Analysis Service
Polls forensic captures, extracts TTPs, publishes to Kafka

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 0: Foundation Setup
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import structlog
import asyncio
from pathlib import Path
from datetime import datetime
import os

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vertice:pass@postgres:5432/vertice")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
FORENSIC_CAPTURE_PATH = Path(os.getenv("FORENSIC_CAPTURE_PATH", "/forensics"))
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "30"))  # seconds


# Background task for polling forensic captures
async def forensic_polling_task():
    """
    Background task that polls /forensics/ directory for new captures.
    
    Sprint 1 TODO:
    - Monitor /forensics/ for new .json, .pcap, .log files
    - Parse captures (Cowrie JSON, TShark PCAP)
    - Extract IoCs (IPs, usernames, file hashes)
    - Map to MITRE ATT&CK techniques
    - Store in PostgreSQL
    - Publish summary to Kafka topic 'reactive_fabric.threat_detected'
    """
    logger.info("forensic_polling_task_started", interval=POLLING_INTERVAL)
    
    while True:
        try:
            # Sprint 0: Just log that we're polling
            logger.debug("polling_forensic_captures", path=str(FORENSIC_CAPTURE_PATH))
            
            # Sprint 1 TODO: Actual polling logic here
            # 1. List files in FORENSIC_CAPTURE_PATH
            # 2. Filter new files (track processed files in DB)
            # 3. Parse each file type:
            #    - Cowrie JSON: extract commands, credentials, IPs
            #    - PCAP: use TShark to extract network data
            # 4. Extract TTPs via pattern matching
            # 5. Store in DB
            # 6. Publish to Kafka
            
            await asyncio.sleep(POLLING_INTERVAL)
            
        except Exception as e:
            logger.error("forensic_polling_error", error=str(e))
            await asyncio.sleep(POLLING_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    logger.info("reactive_fabric_analysis_starting")
    
    # Start background polling task
    task = asyncio.create_task(forensic_polling_task())
    
    # TODO Sprint 1: Initialize database connection
    # TODO Sprint 1: Initialize Kafka producer
    
    yield
    
    logger.info("reactive_fabric_analysis_shutting_down")
    
    # Cancel background task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # TODO Sprint 1: Close database connections
    # TODO Sprint 1: Close Kafka producer


# Initialize FastAPI app
app = FastAPI(
    title="Reactive Fabric Analysis Service",
    description="Analyzes forensic captures and extracts TTPs",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check if forensic directory is accessible
    forensic_accessible = FORENSIC_CAPTURE_PATH.exists()
    
    return {
        "status": "healthy" if forensic_accessible else "degraded",
        "service": "reactive_fabric_analysis",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "forensic_path_accessible": forensic_accessible
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Reactive Fabric Analysis",
        "status": "operational",
        "polling_interval": f"{POLLING_INTERVAL}s",
        "forensic_path": str(FORENSIC_CAPTURE_PATH),
        "documentation": "/docs"
    }


@app.get("/api/v1/status")
async def get_status():
    """
    Get analysis service status and statistics.
    
    Sprint 1 TODO:
    - Return number of captures processed
    - Return number of TTPs extracted
    - Return last processing time
    """
    return {
        "status": "operational",
        "captures_processed_today": 0,
        "ttps_extracted_today": 0,
        "last_processing": None,
        "polling_interval_seconds": POLLING_INTERVAL
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8601,
        reload=True,
        log_level="info"
    )
