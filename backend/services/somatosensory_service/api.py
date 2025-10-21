"""Maximus Somatosensory Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the
Somatosensory Service. It exposes functionalities for simulating tactile
feedback, processing pressure and temperature data, and interpreting physical
interactions.

Endpoints are provided for:
- Triggering simulated physical contact events.
- Retrieving data from mechanoreceptors and nociceptors.
- Accessing processed somatosensory information.

FASE 3 Enhancement: Integrates with Digital Thalamus for Global Workspace
broadcasting of salient somatosensory perceptions.

This API allows other Maximus AI services or external applications to interact
with the somatosensory capabilities in a standardized and efficient manner.
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# Add shared directory to path for Thalamus client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../shared"))

from endogenous_analgesia import EndogenousAnalgesia
from mechanoreceptors import Mechanoreceptors
from nociceptors import Nociceptors
from thalamus_client import ThalamusClient
from weber_fechner_law import WeberFechnerLaw

app = FastAPI(title="Maximus Somatosensory Service", version="2.0.0")

# Initialize somatosensory systems
mechanoreceptors = Mechanoreceptors()
nociceptors = Nociceptors()
weber_fechner_law = WeberFechnerLaw()
endogenous_analgesia = EndogenousAnalgesia()

# Initialize Thalamus client for Global Workspace integration
thalamus_url = os.getenv("DIGITAL_THALAMUS_URL", "http://digital_thalamus_service:8012")
thalamus_client = ThalamusClient(
    thalamus_url=thalamus_url,
    sensor_id="somatosensory_primary",
    sensor_type="somatosensory"
)


class TouchEventRequest(BaseModel):
    """Request model for simulating a touch event.

    Attributes:
        pressure (float): The simulated pressure applied (e.g., 0.0 to 1.0).
        duration (float): The duration of the touch event in seconds.
        location (Optional[str]): The simulated location of the touch (e.g., 'hand', 'surface').
        temperature (Optional[float]): The simulated temperature at the touch point.
        priority (int): The priority of the event (1-10, 10 being highest).
    """

    pressure: float
    duration: float
    location: Optional[str] = None
    temperature: Optional[float] = None
    priority: int = 5


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Somatosensory Service."""
    print("🤚 Starting Maximus Somatosensory Service v2.0...")
    print(f"   Thalamus URL: {thalamus_url}")
    print("✅ Maximus Somatosensory Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Somatosensory Service."""
    print("👋 Shutting down Maximus Somatosensory Service...")
    await thalamus_client.close()
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

    results = {
        "timestamp": datetime.now().isoformat(),
        "mechanoreceptor_data": mechanoreceptor_data,
        "nociceptor_data": nociceptor_data,
        "perceived_pressure": perceived_pressure,
        "analgesia_effect": analgesia_effect,
    }

    # FASE 3: Submit perception to Digital Thalamus for Global Workspace broadcasting
    try:
        thalamus_response = await thalamus_client.submit_perception(
            data=results,
            priority=request.priority,
            timestamp=results["timestamp"]
        )
        results["thalamus_broadcast"] = {
            "submitted": True,
            "broadcasted_to_global_workspace": thalamus_response.get("broadcasted_to_global_workspace", False),
            "salience": thalamus_response.get("salience", 0.0)
        }
        print(f"   📡 Somatosensory perception submitted to Thalamus (salience: {thalamus_response.get('salience', 0.0):.2f})")
    except Exception as e:
        print(f"   ⚠️  Failed to submit to Thalamus: {e}")
        results["thalamus_broadcast"] = {
            "submitted": False,
            "error": str(e)
        }

    return results


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
