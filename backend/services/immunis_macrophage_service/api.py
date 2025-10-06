"""Immunis Macrophage Service - FastAPI Wrapper

Exposes Macrophage phagocytosis capabilities via REST API.

Bio-inspired malware phagocytosis:
- Engulfs malicious samples
- Analyzes via Cuckoo Sandbox
- Extracts IOCs and generates YARA signatures
- Presents antigens to Dendritic Cells via Kafka

Endpoints:
- POST /phagocytose - Engulf and analyze malware sample
- POST /present_antigen - Present antigen to Dendritic Cells
- POST /cleanup - Cleanup old artifacts
- GET /status - Get service status
- GET /health - Health check
- GET /artifacts - List processed artifacts
- GET /signatures - List generated YARA signatures
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
from datetime import datetime
import logging
import os
import tempfile

from macrophage_core import MacrophageCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Immunis Macrophage Service",
    version="1.0.0",
    description="Bio-inspired malware phagocytosis service (engulf, analyze, present antigens)"
)

# Initialize Macrophage core
cuckoo_url = os.getenv("CUCKOO_API_URL", "http://localhost:8090")
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

macrophage_core = MacrophageCore(
    cuckoo_url=cuckoo_url,
    kafka_bootstrap_servers=kafka_servers
)


class PhagocytoseRequest(BaseModel):
    """Request model for phagocytosis.

    Attributes:
        file_path (str): Path to malware sample (temporary file)
        malware_family (str): Malware family name (if known)
    """
    file_path: str
    malware_family: str = "unknown"


class PresentAntigenRequest(BaseModel):
    """Request model for antigen presentation.

    Attributes:
        artifact (Dict[str, Any]): Processed artifact to present
    """
    artifact: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Macrophage Service."""
    logger.info("🦠 Starting Immunis Macrophage Service...")
    logger.info(f"   Cuckoo URL: {cuckoo_url}")
    logger.info(f"   Kafka: {kafka_servers}")
    logger.info("✅ Macrophage Service started successfully - Ready for phagocytosis!")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Macrophage Service."""
    logger.info("👋 Shutting down Immunis Macrophage Service...")

    # Final cleanup
    summary = await macrophage_core.cleanup_debris()
    logger.info(f"   Final cleanup: {summary['artifacts_removed']} artifacts removed")

    logger.info("🛑 Macrophage Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status
    """
    status = await macrophage_core.get_status()

    return {
        "status": "healthy",
        "service": "immunis_macrophage",
        "cuckoo_enabled": status["cuckoo_enabled"],
        "kafka_enabled": status["kafka_enabled"],
        "artifacts_count": status["processed_artifacts_count"],
        "signatures_count": status["generated_signatures_count"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed Macrophage service status.

    Returns:
        Dict[str, Any]: Detailed status information
    """
    return await macrophage_core.get_status()


@app.post("/phagocytose")
async def phagocytose_sample(
    file: UploadFile = File(...),
    malware_family: str = "unknown"
) -> Dict[str, Any]:
    """Phagocytose (engulf and analyze) malware sample.

    This is the primary endpoint for malware analysis. The Macrophage will:
    1. Submit sample to Cuckoo Sandbox for dynamic analysis
    2. Extract IOCs from analysis results
    3. Generate YARA signature
    4. Return processed artifact

    Args:
        file (UploadFile): Malware sample file to analyze
        malware_family (str): Malware family name (optional)

    Returns:
        Dict[str, Any]: Processed artifact with analysis results

    Raises:
        HTTPException: If phagocytosis fails
    """
    try:
        logger.info(f"Received phagocytose request: {file.filename}")

        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        logger.info(f"Sample saved to: {tmp_file_path}")

        # Phagocytose sample
        artifact = await macrophage_core.phagocytose(
            sample_path=tmp_file_path,
            malware_family=malware_family
        )

        # Cleanup temporary file
        try:
            os.unlink(tmp_file_path)
        except:
            pass

        return {
            "status": "success",
            "message": "Phagocytosis complete",
            "artifact": artifact,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error during phagocytosis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/present_antigen")
async def present_antigen(request: PresentAntigenRequest) -> Dict[str, Any]:
    """Present processed threat information (antigen) to Dendritic Cells.

    Args:
        request (PresentAntigenRequest): Artifact to present

    Returns:
        Dict[str, Any]: Presentation confirmation

    Raises:
        HTTPException: If presentation fails
    """
    try:
        logger.info(f"Presenting antigen: {request.artifact.get('sample_hash', 'unknown')[:16]}...")

        result = await macrophage_core.present_antigen(request.artifact)

        return {
            "status": "success",
            "presentation_result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error presenting antigen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup")
async def trigger_cleanup() -> Dict[str, Any]:
    """Trigger cleanup of old artifacts and signatures.

    Returns:
        Dict[str, Any]: Cleanup statistics
    """
    logger.info("Manual cleanup triggered")

    summary = await macrophage_core.cleanup_debris()

    return {
        "status": "success",
        "cleanup_summary": summary,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/artifacts")
async def get_artifacts(limit: int = 10) -> Dict[str, Any]:
    """Get list of processed artifacts.

    Args:
        limit (int): Maximum number of artifacts to return

    Returns:
        Dict[str, Any]: List of artifacts
    """
    artifacts = macrophage_core.processed_artifacts[-limit:]

    return {
        "status": "success",
        "total_artifacts": len(macrophage_core.processed_artifacts),
        "returned_count": len(artifacts),
        "artifacts": artifacts,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/signatures")
async def get_signatures(limit: int = 10) -> Dict[str, Any]:
    """Get list of generated YARA signatures.

    Args:
        limit (int): Maximum number of signatures to return

    Returns:
        Dict[str, Any]: List of YARA signatures
    """
    signatures = macrophage_core.generated_signatures[-limit:]

    return {
        "status": "success",
        "total_signatures": len(macrophage_core.generated_signatures),
        "returned_count": len(signatures),
        "signatures": signatures,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get operational metrics.

    Returns:
        Dict[str, Any]: Performance and operational metrics
    """
    status = await macrophage_core.get_status()

    return {
        "service": "immunis_macrophage",
        "metrics": {
            "total_artifacts_processed": status["processed_artifacts_count"],
            "total_signatures_generated": status["generated_signatures_count"],
            "cuckoo_sandbox_enabled": status["cuckoo_enabled"],
            "kafka_messaging_enabled": status["kafka_enabled"],
            "last_cleanup": status["last_cleanup"]
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012)
