"""
immunis_cytotoxic_t_service - FastAPI service
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("Starting immunis_cytotoxic_t_service...")
    yield
    logger.info("Shutting down immunis_cytotoxic_t_service...")


app = FastAPI(
    title="immunis_cytotoxic_t_service",
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
    return {"status": "healthy", "service": "immunis_cytotoxic_t_service"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "immunis_cytotoxic_t_service",
        "version": "0.1.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
