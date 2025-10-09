"""Immunis Helper T-Cell - Coordination Service - FastAPI Wrapper

Exposes Helper T-Cell - Coordination capabilities via REST API.

Bio-inspired immune system component.

Endpoints:
- GET /health - Health check
- GET /status - Service status
- POST /process - Main processing endpoint
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

import time

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional import of core (may not exist yet)
try:
    from helper_t_core import HelperTCore

    CORE_AVAILABLE = True
except ImportError:
    logger.warning("HelperTCore not available - running in limited mode")
    CORE_AVAILABLE = False
    HelperTCore = None

security = HTTPBearer(auto_error=False)

app = FastAPI(
    title="Immunis Helper T-Cell - Coordination Service",
    version="1.0.0",
    description="Bio-inspired helper t-cell - coordination service",
)

FAILURE_THRESHOLD = 3
FAILURE_WINDOW_SECONDS = 60
_failure_timestamps: List[float] = []

# Initialize core if available
if CORE_AVAILABLE and HelperTCore:
    try:
        core = HelperTCore()
        logger.info("Helper T-Cell - Coordination core initialized")
    except Exception as e:
        logger.warning(f"Core initialization failed: {e}")
        core = None
else:
    core = None


def _prune_failures(now: float) -> None:
    cutoff = now - FAILURE_WINDOW_SECONDS
    while _failure_timestamps and _failure_timestamps[0] < cutoff:
        _failure_timestamps.pop(0)


async def log_failure() -> None:
    now = time.time()
    _prune_failures(now)
    _failure_timestamps.append(now)
    if len(_failure_timestamps) >= FAILURE_THRESHOLD:
        logger.warning("Multiple consecutive failures detected. Potential immune suppression attempt.")


async def log_success() -> None:
    now = time.time()
    _prune_failures(now)
    if _failure_timestamps:
        _failure_timestamps.clear()

async def require_identity(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> str:
    if credentials is None:
        logger.warning('Missing credentials')
        raise HTTPException(status_code=401, detail='Authentication required')
    token = credentials.credentials
    if token != 'trusted-token':
        logger.error('Invalid helper T token')
        raise HTTPException(status_code=403, detail='Invalid token')
    return token

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
    logger.info("🦠 Starting Immunis Helper T-Cell - Coordination Service...")
    logger.info("✅ Helper T-Cell - Coordination Service started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks."""
    logger.info("👋 Shutting down Immunis Helper T-Cell - Coordination Service...")
    logger.info("🛑 Helper T-Cell - Coordination Service shut down.")


@app.get("/health")
async def health_check(request: Request, _: str = Depends(require_identity)) -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status
    """
    return {
        "status": "healthy",
        "service": "immunis_helper_t",
        "core_available": CORE_AVAILABLE and core is not None,
        "degraded": is_degraded(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status")
async def get_status(request: Request, _: str = Depends(require_identity)) -> Dict[str, Any]:
    """Get detailed service status.

    Returns:
        Dict[str, Any]: Detailed status information
    """
    if core and hasattr(core, "get_status"):
        try:
            return await core.get_status()
        except Exception as e:
            logger.error(f"Status retrieval failed: {e}")

    return {
        "status": "operational",
        "service": "immunis_helper_t",
        "mode": "limited" if not core else "full",
        "degraded": is_degraded(),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/process")
async def process_data(request: Request, payload: ProcessRequest, _: str = Depends(require_identity)) -> Dict[str, Any]:
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
    if is_degraded():
        raise HTTPException(status_code=503, detail="Helper T service in protective quarantine")

    try:
        # Call core processing method if available
        start = time.perf_counter()
        if hasattr(core, "process"):
            result = await core.process(payload.data, payload.context)
        elif hasattr(core, "analyze"):
            result = await core.analyze(payload.data, payload.context)
        else:
            result = {"processed": True, "data": payload.data}
        latency_ms = (time.perf_counter() - start) * 1000
        await log_success()

        return {
            "status": "success",
            "service": "immunis_helper_t",
            "results": result,
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await log_failure()
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail="Helper T processing error") from e


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8017)
