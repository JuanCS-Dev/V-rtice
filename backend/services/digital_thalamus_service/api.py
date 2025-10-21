"""Maximus Digital Thalamus Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Digital
Thalamus Service. It exposes functionalities for ingesting raw sensory data,
applying filtering and prioritization, and routing processed information to
other Maximus AI services.

Endpoints are provided for:
- Submitting sensory data from various sources.
- Querying the status of sensory processing.
- Configuring sensory gating and attention control parameters.
- Broadcasting salient events to Global Workspace (Kafka + Redis)

This API allows sensory services to feed their raw data into the Maximus AI
system, and higher-level cognitive services to receive pre-processed, prioritized
sensory information for efficient decision-making.

FASE 3 Enhancement: Implements Global Workspace Theory with dual broadcasting
for consciousness integration.
"""

import os
from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from attention_control import AttentionControl
from global_workspace import GlobalWorkspace
from sensory_gating import SensoryGating
from signal_filtering import SignalFiltering

app = FastAPI(title="Maximus Digital Thalamus Service", version="2.0.0")

# Initialize Thalamus components
sensory_gating = SensoryGating()
signal_filtering = SignalFiltering()
attention_control = AttentionControl()

# Initialize Global Workspace (Kafka + Redis)
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-immunity:9096")
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
global_workspace = GlobalWorkspace(
    kafka_bootstrap_servers=kafka_servers,
    redis_url=redis_url
)


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
    print("🧠 Starting Maximus Digital Thalamus Service v2.0...")
    print(f"   Kafka: {kafka_servers}")
    print(f"   Redis: {redis_url}")

    try:
        await global_workspace.start()
        print("✅ Global Workspace broadcasting ACTIVE")
    except Exception as e:
        print(f"⚠️  Global Workspace failed to start: {e}")
        print("   Service will continue without broadcasting")

    print("✅ Maximus Digital Thalamus Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Digital Thalamus Service."""
    print("👋 Shutting down Maximus Digital Thalamus Service...")

    await global_workspace.stop()

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
    """Ingests raw sensory data, applies processing, and broadcasts to Global Workspace.

    FASE 3 Enhancement: After processing, salient events are broadcasted to
    the Global Workspace (Kafka + Redis) for consciousness integration.

    Args:
        request (SensoryDataIngest): The request body containing sensory data.

    Returns:
        Dict[str, Any]: A dictionary confirming ingestion, processing, and broadcast status.
    """
    print(f"[API] Ingesting {request.sensor_type} data from {request.sensor_id} (priority: {request.priority})")

    # Apply sensory gating
    # Normalize priority (1-10) to intensity (0.0-1.0)
    data_intensity = request.priority / 10.0
    if not sensory_gating.allow_data(request.sensor_type, data_intensity):
        return {
            "status": "rejected",
            "reason": "Sensory gating blocked data due to low priority or overload.",
        }

    # Apply signal filtering
    filtered_data = signal_filtering.apply_filters(request.data, request.sensor_type)

    # Apply attention control (prioritization/routing)
    processed_data = await attention_control.prioritize_and_route(filtered_data, request.sensor_type, request.priority)

    # Compute salience score (normalized priority + data intensity)
    salience = (request.priority / 10.0 + data_intensity) / 2.0

    # Broadcast to Global Workspace if event is salient enough
    broadcast_result = None
    if salience >= 0.5:  # Only broadcast moderately salient events
        try:
            broadcast_result = await global_workspace.broadcast_event(
                sensor_type=request.sensor_type,
                sensor_id=request.sensor_id,
                data=processed_data,
                salience=salience,
                metadata={
                    "priority": request.priority,
                    "original_timestamp": request.timestamp
                }
            )
            print(f"   📡 Broadcasted to Global Workspace (salience: {salience:.2f})")
        except Exception as e:
            print(f"   ⚠️  Broadcast failed: {e}")
            broadcast_result = {"broadcasted": False, "error": str(e)}

    return {
        "timestamp": datetime.now().isoformat(),
        "sensor_id": request.sensor_id,
        "sensor_type": request.sensor_type,
        "status": "processed_and_routed",
        "salience": salience,
        "broadcasted_to_global_workspace": broadcast_result is not None and broadcast_result.get("broadcasted", False),
        "broadcast_details": broadcast_result,
        "processed_payload_summary": {
            "keys": list(processed_data.keys()),
            "size": len(str(processed_data)),
        },
    }


@app.get("/gating_status")
async def get_gating_status() -> Dict[str, Any]:
    """Retrieves the current status of the sensory gating mechanism.

    Returns:
        Dict[str, Any]: The status of sensory gating.
    """
    return await sensory_gating.get_status()


@app.get("/attention_status")
async def get_attention_status() -> Dict[str, Any]:
    """Retrieves the current status of the attention control mechanism.

    Returns:
        Dict[str, Any]: The status of attention control.
    """
    return await attention_control.get_status()


@app.get("/global_workspace_status")
async def get_global_workspace_status() -> Dict[str, Any]:
    """Retrieves the current status of the Global Workspace broadcaster.

    FASE 3 Enhancement: Provides metrics on Kafka and Redis broadcasting.

    Returns:
        Dict[str, Any]: The status of Global Workspace broadcasting.
    """
    return await global_workspace.get_status()


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8012)
