"""Maximus Somatosensory Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the
Somatosensory Service. It exposes functionalities for simulating tactile
feedback, processing pressure and temperature data, and interpreting physical
interactions.

Endpoints are provided for:
- Triggering simulated physical contact events.
- Retrieving data from mechanoreceptors and nociceptors.
- Accessing processed somatosensory information.

This API allows other Maximus AI services or external applications to interact
with the somatosensory capabilities in a standardized and efficient manner.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from endogenous_analgesia import EndogenousAnalgesia
from mechanoreceptors import Mechanoreceptors
from nociceptors import Nociceptors
from weber_fechner_law import WeberFechnerLaw

app = FastAPI(title="Maximus Somatosensory Service", version="1.0.0")

# Initialize somatosensory systems
mechanoreceptors = Mechanoreceptors()
nociceptors = Nociceptors()
weber_fechner_law = WeberFechnerLaw()
endogenous_analgesia = EndogenousAnalgesia()


class TouchEventRequest(BaseModel):
    """Request model for simulating a touch event.

    Attributes:
        pressure (float): The simulated pressure applied (e.g., 0.0 to 1.0).
        duration (float): The duration of the touch event in seconds.
        location (Optional[str]): The simulated location of the touch (e.g., 'hand', 'surface').
        temperature (Optional[float]): The simulated temperature at the touch point.
    """

    pressure: float
    duration: float
    location: Optional[str] = None
    temperature: Optional[float] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Somatosensory Service."""
    print("✋ Starting Maximus Somatosensory Service...")
    print("✅ Maximus Somatosensory Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Somatosensory Service."""
    print("👋 Shutting down Maximus Somatosensory Service...")
    print("🛑 Maximus Somatosensory Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Somatosensory Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Somatosensory Service is operational."}


@app.post("/touch")
async def simulate_touch_event(request: TouchEventRequest) -> Dict[str, Any]:
    """Simulates a touch event and processes it through mechanoreceptors and nociceptors.

    Args:
        request (TouchEventRequest): The request body containing touch parameters.

    Returns:
        Dict[str, Any]: The processed somatosensory data.
    """
    print(
        f"[API] Simulating touch event: Pressure={request.pressure}, Duration={request.duration}, Location={request.location}"
    )

    mechanoreceptor_data = await mechanoreceptors.process_touch(request.pressure, request.duration, request.location)
    nociceptor_data = await nociceptors.process_stimulus(request.pressure, request.temperature, request.location)

    # Apply Weber-Fechner Law for perceived intensity
    perceived_pressure = weber_fechner_law.calculate_perceived_intensity(request.pressure)

    # Simulate endogenous analgesia if pain is detected
    pain_level = nociceptor_data.get("pain_level", 0.0)
    analgesia_effect = endogenous_analgesia.modulate_pain(pain_level)
    nociceptor_data["modulated_pain_level"] = max(0.0, pain_level - analgesia_effect)

    return {
        "timestamp": datetime.now().isoformat(),
        "mechanoreceptor_data": mechanoreceptor_data,
        "nociceptor_data": nociceptor_data,
        "perceived_pressure": perceived_pressure,
        "analgesia_effect": analgesia_effect,
    }


@app.get("/mechanoreceptors/status")
async def get_mechanoreceptor_status() -> Dict[str, Any]:
    """Retrieves the current status of the mechanoreceptor system.

    Returns:
        Dict[str, Any]: The status of the mechanoreceptor system.
    """
    return await mechanoreceptors.get_status()


@app.get("/nociceptors/status")
async def get_nociceptor_status() -> Dict[str, Any]:
    """Retrieves the current status of the nociceptor system.

    Returns:
        Dict[str, Any]: The status of the nociceptor system.
    """
    return await nociceptors.get_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
