"""Maximus Digital Thalamus Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Digital
Thalamus Service. It exposes functionalities for ingesting raw sensory data,
applying filtering and prioritization, and routing processed information to
other Maximus AI services.

Endpoints are provided for:
- Submitting sensory data from various sources.
- Querying the status of sensory processing.
- Configuring sensory gating and attention control parameters.

This API allows sensory services to feed their raw data into the Maximus AI
system, and higher-level cognitive services to receive pre-processed, prioritized
sensory information for efficient decision-making.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
from datetime import datetime

from sensory_gating import SensoryGating
from signal_filtering import SignalFiltering
from attention_control import AttentionControl

app = FastAPI(title="Maximus Digital Thalamus Service", version="1.0.0")

# Initialize Thalamus components
sensory_gating = SensoryGating()
signal_filtering = SignalFiltering()
attention_control = AttentionControl()


class SensoryDataIngest(BaseModel):
    """Request model for ingesting raw sensory data.

    Attributes:
        sensor_id (str): Identifier of the sensor or source.
        sensor_type (str): Type of sensory data (e.g., 'visual', 'auditory', 'chemical', 'somatosensory').
        data (Dict[str, Any]): The raw sensory data payload.
        timestamp (str): ISO formatted timestamp of data collection.
        priority (int): Processing priority (1-10, 10 being highest).
    """
    sensor_id: str
    sensor_type: str
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 5


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Digital Thalamus Service."""
    print("🧠 Starting Maximus Digital Thalamus Service...")
    print("✅ Maximus Digital Thalamus Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Digital Thalamus Service."""
    print("👋 Shutting down Maximus Digital Thalamus Service...")
    print("🛑 Maximus Digital Thalamus Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Digital Thalamus Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Digital Thalamus Service is operational."}


@app.post("/ingest_sensory_data")
async def ingest_sensory_data(request: SensoryDataIngest) -> Dict[str, Any]:
    """Ingests raw sensory data, applies processing, and routes it.

    Args:
        request (SensoryDataIngest): The request body containing sensory data.

    Returns:
        Dict[str, Any]: A dictionary confirming ingestion and processing status.
    """
    print(f"[API] Ingesting {request.sensor_type} data from {request.sensor_id} (priority: {request.priority})")
    
    # Apply sensory gating
    if not sensory_gating.allow_data(request.sensor_type, request.priority):
        return {"status": "rejected", "reason": "Sensory gating blocked data due to low priority or overload."}

    # Apply signal filtering
    filtered_data = signal_filtering.apply_filters(request.data, request.sensor_type)

    # Apply attention control (prioritization/routing)
    processed_data = await attention_control.prioritize_and_route(filtered_data, request.sensor_type, request.priority)

    return {
        "timestamp": datetime.now().isoformat(),
        "sensor_id": request.sensor_id,
        "sensor_type": request.sensor_type,
        "status": "processed_and_routed",
        "processed_payload_summary": {"keys": list(processed_data.keys()), "size": len(str(processed_data))}
    }


@app.get("/gating_status")
async def get_gating_status() -> Dict[str, Any]:
    """Retrieves the current status of the sensory gating mechanism.

    Returns:
        Dict[str, Any]: The status of sensory gating.
    """
    return sensory_gating.get_status()


@app.get("/attention_status")
async def get_attention_status() -> Dict[str, Any]:
    """Retrieves the current status of the attention control mechanism.

    Returns:
        Dict[str, Any]: The status of attention control.
    """
    return attention_control.get_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012)
