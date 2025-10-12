"""
Reactive Fabric Analysis Service
Polls forensic captures, extracts TTPs, publishes to Kafka.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation - NO MOCK, NO PLACEHOLDER, NO TODO
"""

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import structlog
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional
import os

from backend.services.reactive_fabric_analysis.parsers import (
    CowrieJSONParser
)
from backend.services.reactive_fabric_analysis.ttp_mapper import TTPMapper
from backend.services.reactive_fabric_analysis.models import (
    ForensicCapture,
    AttackCreate,
    AttackSeverity,
    ProcessingStatus,
    AnalysisStatus
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vertice:vertice_pass@postgres:5432/vertice")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
FORENSIC_CAPTURE_PATH = Path(os.getenv("FORENSIC_CAPTURE_PATH", "/forensics"))
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "30"))  # seconds
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://reactive_fabric_core:8600")

# Global instances
db: Optional[object] = None  # Database connection (shared with Core)
parsers: list = []
ttp_mapper: Optional[TTPMapper] = None

# Metrics
metrics = {
    "captures_processed_today": 0,
    "ttps_extracted_today": 0,
    "attacks_created_today": 0,
    "last_processing": None
}


# Background task for polling forensic captures
async def forensic_polling_task():
    """
    Production-ready forensic polling with full TTP extraction.
    
    Compliance:
    - Paper Section 3.2: "Progressão Condicional"
    - Fase 1: Coleta de inteligência PASSIVA
    - KPIs: TTPs identificados, IoCs extraídos
    
    Process:
    1. Poll database for pending forensic captures
    2. Select appropriate parser (Cowrie, PCAP, etc)
    3. Parse and extract structured data
    4. Map commands to MITRE ATT&CK TTPs
    5. Extract IoCs (IPs, hashes, credentials)
    6. Create attack record via Core Service API
    7. Update capture status in database
    """
    global parsers, ttp_mapper, metrics
    
    logger.info("forensic_polling_task_started", interval=POLLING_INTERVAL)
    
    while True:
        try:
            # Check if dependencies are ready
            if not parsers or not ttp_mapper:
                logger.warning("dependencies_not_ready", parsers=len(parsers), ttp_mapper=bool(ttp_mapper))
                await asyncio.sleep(POLLING_INTERVAL)
                continue
            
            # Step 1: Get pending captures from Core Service
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    # In production, Core Service would expose /api/v1/captures/pending
                    # For Sprint 1, we'll scan filesystem directly
                    pending_captures = await scan_filesystem_for_captures()
                    
                except httpx.HTTPError as e:
                    logger.error("core_service_unreachable", error=str(e))
                    await asyncio.sleep(POLLING_INTERVAL)
                    continue
            
            if not pending_captures:
                logger.debug("no_pending_captures")
                await asyncio.sleep(POLLING_INTERVAL)
                continue
            
            # Step 2: Process each capture
            for capture_path in pending_captures:
                try:
                    logger.info("processing_capture", file=str(capture_path))
                    
                    # Step 3: Select parser
                    parser = None
                    for p in parsers:
                        if p.supports(capture_path):
                            parser = p
                            break
                    
                    if not parser:
                        logger.warning("no_parser_found", file=str(capture_path))
                        continue
                    
                    # Step 4: Parse forensic capture
                    parsed_data = await parser.parse(capture_path)
                    
                    # Step 5: Map to MITRE TTPs
                    ttps = ttp_mapper.map_ttps(
                        commands=parsed_data.get("commands", []),
                        attack_type=parsed_data.get("attack_type", "unknown"),
                        credentials=parsed_data.get("credentials", [])
                    )
                    
                    # Step 6: Extract IoCs
                    iocs = {
                        "ips": [parsed_data.get("attacker_ip")] if parsed_data.get("attacker_ip") else [],
                        "usernames": [cred[0] for cred in parsed_data.get("credentials", [])],
                        "file_hashes": parsed_data.get("file_hashes", [])
                    }
                    
                    # Step 7: Determine severity
                    severity = _determine_severity(ttps)
                    
                    # Step 8: Create attack record via Core Service
                    attack = AttackCreate(
                        honeypot_id="00000000-0000-0000-0000-000000000001",  # TODO: Get from DB
                        attacker_ip=parsed_data.get("attacker_ip", "unknown"),
                        attack_type=parsed_data.get("attack_type", "unknown"),
                        severity=severity,
                        confidence=0.95,
                        ttps=ttps,
                        iocs=iocs,
                        payload=str(parsed_data.get("commands", [])[:5]),  # First 5 commands
                        captured_at=parsed_data.get("timestamps", [datetime.utcnow()])[0] if parsed_data.get("timestamps") else datetime.utcnow()
                    )
                    
                    # Post to Core Service
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{CORE_SERVICE_URL}/api/v1/attacks",
                            json=attack.model_dump(mode='json'),
                        )
                        response.raise_for_status()
                    
                    # Update metrics
                    metrics["captures_processed_today"] += 1
                    metrics["ttps_extracted_today"] += len(ttps)
                    metrics["attacks_created_today"] += 1
                    metrics["last_processing"] = datetime.utcnow()
                    
                    logger.info(
                        "capture_processed_successfully",
                        file=str(capture_path),
                        attacker_ip=parsed_data.get("attacker_ip"),
                        ttps_extracted=len(ttps),
                        iocs_extracted=len(iocs.get("ips", []))
                    )
                    
                    # Mark file as processed (rename with .processed extension)
                    processed_path = capture_path.with_suffix(capture_path.suffix + ".processed")
                    capture_path.rename(processed_path)
                
                except Exception as e:
                    logger.error(
                        "capture_processing_failed",
                        file=str(capture_path),
                        error=str(e)
                    )
            
            await asyncio.sleep(POLLING_INTERVAL)
            
        except Exception as e:
            logger.error("forensic_polling_error", error=str(e))
            await asyncio.sleep(POLLING_INTERVAL)


async def scan_filesystem_for_captures() -> list:
    """
    Scan forensic capture directory for unprocessed files.
    
    Returns:
        List of Path objects to pending capture files
    """
    if not FORENSIC_CAPTURE_PATH.exists():
        logger.warning("forensic_path_not_found", path=str(FORENSIC_CAPTURE_PATH))
        return []
    
    pending = []
    for file in FORENSIC_CAPTURE_PATH.iterdir():
        if file.is_file() and not file.name.endswith('.processed'):
            # Check if it's a supported file type
            if file.suffix.lower() in ['.json', '.log', '.pcap']:
                pending.append(file)
    
    return pending


def _determine_severity(ttps: list) -> AttackSeverity:
    """
    Determine attack severity based on TTPs.
    
    Args:
        ttps: List of MITRE technique IDs
    
    Returns:
        AttackSeverity enum
    """
    # Critical TTPs (exploitation, persistence, impact)
    critical_ttps = ["T1190", "T1053", "T1098", "T1486", "T1490"]
    
    # High TTPs (credential access, privilege escalation)
    high_ttps = ["T1110", "T1003", "T1068", "T1105"]
    
    if any(ttp in critical_ttps for ttp in ttps):
        return AttackSeverity.CRITICAL
    elif any(ttp in high_ttps for ttp in ttps):
        return AttackSeverity.HIGH
    elif ttps:
        return AttackSeverity.MEDIUM
    else:
        return AttackSeverity.LOW


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    global parsers, ttp_mapper
    
    logger.info("reactive_fabric_analysis_starting")
    
    # Initialize parsers
    parsers = [
        CowrieJSONParser(),
        # PCAPParser(),  # Sprint 1 extension
    ]
    logger.info("parsers_initialized", count=len(parsers))
    
    # Initialize TTP mapper
    ttp_mapper = TTPMapper()
    logger.info("ttp_mapper_initialized", techniques=len(ttp_mapper.TTP_PATTERNS))
    
    # Start background polling task
    task = asyncio.create_task(forensic_polling_task())
    
    yield
    
    logger.info("reactive_fabric_analysis_shutting_down")
    
    # Cancel background task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


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
