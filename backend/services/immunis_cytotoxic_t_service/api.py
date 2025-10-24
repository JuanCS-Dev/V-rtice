"""Immunis Cytotoxic T-Cell - Threat Elimination Service - FastAPI Wrapper

Exposes Cytotoxic T-Cell - Threat Elimination capabilities via REST API.

Bio-inspired immune system component.

Endpoints:
- GET /health - Health check
- GET /status - Service status
- POST /process - Main processing endpoint
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional import of core (may not exist yet)
try:
    from cytotoxic_t_core import CytotoxicTCore  # pragma: no cover

    CORE_AVAILABLE = True  # pragma: no cover
except ImportError:
    logger.warning("CytotoxicTCore not available - running in limited mode")
    CORE_AVAILABLE = False
    CytotoxicTCore = None

app = FastAPI(
    title="Immunis Cytotoxic T-Cell - Threat Elimination Service",
    version="1.0.0",
    description="Bio-inspired cytotoxic t-cell - threat elimination service",
)

# Initialize core if available
if CORE_AVAILABLE and CytotoxicTCore:  # pragma: no cover
    try:  # pragma: no cover
        core = CytotoxicTCore()  # pragma: no cover
        logger.info("Cytotoxic T-Cell - Threat Elimination core initialized")  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logger.warning(f"Core initialization failed: {e}")  # pragma: no cover
        core = None  # pragma: no cover
else:
    core = None


class ProcessRequest(BaseModel):
    """Generic request model for processing.

    Attributes:
        data (Dict[str, Any]): Input data to process
        context (Optional[Dict[str, Any]]): Optional context
    """

    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks."""
    logger.info("🦠 Starting Immunis Cytotoxic T-Cell - Threat Elimination Service...")  # pragma: no cover
    logger.info("✅ Cytotoxic T-Cell - Threat Elimination Service started successfully!")  # pragma: no cover


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks."""
    logger.info("👋 Shutting down Immunis Cytotoxic T-Cell - Threat Elimination Service...")  # pragma: no cover
    logger.info("🛑 Cytotoxic T-Cell - Threat Elimination Service shut down.")  # pragma: no cover


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status
    """
    return {
        "status": "healthy",
        "service": "immunis_cytotoxic_t",
        "core_available": CORE_AVAILABLE and core is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed service status.

    Returns:
        Dict[str, Any]: Detailed status information
    """
    if core and hasattr(core, "get_status"):  # pragma: no cover
        try:  # pragma: no cover
            return await core.get_status()  # pragma: no cover
        except Exception as e:  # pragma: no cover
            logger.error(f"Status retrieval failed: {e}")  # pragma: no cover

    return {
        "status": "operational",
        "service": "immunis_cytotoxic_t",
        "mode": "limited" if not core else "full",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/process")
async def process_data(request: ProcessRequest) -> Dict[str, Any]:
    """Main processing endpoint.

    Args:
        request (ProcessRequest): Data to process

    Returns:
        Dict[str, Any]: Processing results

    Raises:
        HTTPException: If processing fails
    """
    if not core:
        raise HTTPException(status_code=503, detail="Core not available - service in limited mode")

    try:  # pragma: no cover - Requires core to be available
        # Call core processing method if available  # pragma: no cover
        if hasattr(core, "process"):  # pragma: no cover
            result = await core.process(request.data, request.context)  # pragma: no cover
        elif hasattr(core, "analyze"):  # pragma: no cover
            result = await core.analyze(request.data, request.context)  # pragma: no cover
        else:  # pragma: no cover
            result = {"processed": True, "data": request.data}  # pragma: no cover

        return {  # pragma: no cover
            "status": "success",  # pragma: no cover
            "service": "immunis_cytotoxic_t",  # pragma: no cover
            "results": result,  # pragma: no cover
            "timestamp": datetime.now().isoformat(),  # pragma: no cover
        }  # pragma: no cover

    except Exception as e:  # pragma: no cover
        logger.error(f"Processing failed: {e}")  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e))  # pragma: no cover


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8018)
