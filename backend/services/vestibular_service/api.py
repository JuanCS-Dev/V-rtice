"""Maximus Vestibular Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Vestibular
Service. It exposes functionalities for maintaining the AI's sense of balance,
spatial orientation, and self-motion perception within its operational environment.

Endpoints are provided for:
- Submitting simulated motion sensor data (accelerometers, gyroscopes).
- Querying the AI's current orientation and velocity.
- Retrieving information about detected changes in motion or balance.

This API allows other Maximus AI services or external systems to leverage the
Vestibular Service's capabilities, enabling Maximus to navigate, interact
physically, and maintain stability with a robust sense of its own motion and
spatial position.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from otolith_organs import OtolithOrgans
from pydantic import BaseModel, Field
from semicircular_canals import SemicircularCanals
import uvicorn

app = FastAPI(title="Maximus Vestibular Service", version="1.0.0")

# Initialize vestibular components
otolith_organs = OtolithOrgans()
semicircular_canals = SemicircularCanals()


class MotionDataIngest(BaseModel):
    """Request model for ingesting motion sensor data.

    Attributes:
        sensor_id (str): Identifier of the motion sensor.
        accelerometer_data (List[float]): [x, y, z] acceleration values.
        gyroscope_data (List[float]): [x, y, z] angular velocity values.
        timestamp (str): ISO formatted timestamp of data collection.
    """

    sensor_id: str
    accelerometer_data: List[float]
    gyroscope_data: List[float]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Vestibular Service."""
    print("🤸 Starting Maximus Vestibular Service...")
    print("✅ Maximus Vestibular Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Vestibular Service."""
    print("👋 Shutting down Maximus Vestibular Service...")
    print("🛑 Maximus Vestibular Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Vestibular Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Vestibular Service is operational."}


@app.post("/ingest_motion_data")
async def ingest_motion_data(request: MotionDataIngest) -> Dict[str, Any]:
    """Ingests motion sensor data and processes it for spatial orientation.

    Args:
        request (MotionDataIngest): The request body containing motion sensor data.

    Returns:
        Dict[str, Any]: A dictionary containing the processed spatial orientation data.
    """
    print(f"[API] Ingesting motion data from {request.sensor_id}.")

    linear_motion = otolith_organs.process_accelerometer_data(
        request.accelerometer_data
    )
    angular_motion = semicircular_canals.process_gyroscope_data(request.gyroscope_data)

    # Simulate integration of both for overall orientation
    current_orientation = {
        "pitch": angular_motion.get("pitch_change", 0) * 10,
        "roll": angular_motion.get("roll_change", 0) * 10,
        "yaw": angular_motion.get("yaw_change", 0) * 10,
        "linear_acceleration": linear_motion.get("linear_acceleration", [0, 0, 0]),
    }

    return {
        "status": "processed",
        "timestamp": datetime.now().isoformat(),
        "sensor_id": request.sensor_id,
        "linear_motion_perception": linear_motion,
        "angular_motion_perception": angular_motion,
        "current_orientation": current_orientation,
    }


@app.get("/orientation")
async def get_current_orientation() -> Dict[str, Any]:
    """Retrieves the AI's current spatial orientation and motion perception.

    Returns:
        Dict[str, Any]: A dictionary summarizing the current orientation and motion.
    """
    # In a real system, this would aggregate data from both components
    return {
        "status": "active",
        "last_update": datetime.now().isoformat(),
        "current_pitch": 0.5,
        "current_roll": 0.2,
        "current_yaw": 1.0,
        "linear_acceleration": [0.1, 0.0, 0.0],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
