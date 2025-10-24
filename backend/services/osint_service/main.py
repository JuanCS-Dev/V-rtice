"""
osint_service - FastAPI service
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging FIRST (before any usage)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Service Registry client
try:
    from shared.vertice_registry_client import auto_register_service, RegistryClient
    REGISTRY_AVAILABLE = True
except ImportError:
    logger.warning("Service Registry client not available - running in standalone mode")
    REGISTRY_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("Starting osint_service...")

    # Auto-register with Service Registry
    heartbeat_task = None
    if REGISTRY_AVAILABLE:
        try:
            heartbeat_task = await auto_register_service(
                service_name="osint_service",
                port=8049,  # Internal container port
                health_endpoint="/health",
                metadata={"category": "investigation", "version": "0.1.0"}
            )
            logger.info("✅ Registered with Vértice Service Registry")
        except Exception as e:
            logger.warning(f"Failed to register with service registry: {e}")

    yield

    # Cleanup
    logger.info("Shutting down osint_service...")
    if heartbeat_task:
        heartbeat_task.cancel()
    if REGISTRY_AVAILABLE:
        try:
            await RegistryClient.deregister("osint_service")
        except:
            pass


app = FastAPI(
    title="osint_service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "osint_service"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "osint_service",
        "version": "0.1.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
