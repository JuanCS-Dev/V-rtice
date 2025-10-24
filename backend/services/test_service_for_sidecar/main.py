"""
Mock Service for Sidecar Testing

This is a minimal FastAPI service used exclusively for testing the
Vértice Registry Sidecar Agent.
"""

from fastapi import FastAPI
import time

app = FastAPI(title="Test Service", version="1.0.0")

start_time = time.time()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "uptime": time.time() - start_time,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Test Service for Sidecar - Running!"}
