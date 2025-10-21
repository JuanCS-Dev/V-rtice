"""Maximus Visual Cortex Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Visual
Cortex Service. It exposes functionalities for simulating image processing,
object recognition, scene understanding, and visual data interpretation.

Endpoints are provided for:
- Submitting images or video frames for analysis.
- Retrieving object detection and recognition results.
- Accessing scene understanding and visual context information.

FASE 3 Enhancement: Integrates with Digital Thalamus for Global Workspace
broadcasting of salient visual perceptions.

This API allows other Maximus AI services or external applications to interact
with the visual perception capabilities in a standardized and efficient manner.
"""

import base64
import os
import sys
from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add shared directory to path for Thalamus client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../shared"))

from attention_system_core import AttentionSystemCore
from event_driven_vision_core import EventDrivenVisionCore
from malware_vision_core import MalwareVisionCore
from network_vision_core import NetworkVisionCore
from thalamus_client import ThalamusClient

app = FastAPI(title="Maximus Visual Cortex Service", version="2.0.0")

# Initialize vision cores
event_driven_vision = EventDrivenVisionCore()
attention_system = AttentionSystemCore()
network_vision = NetworkVisionCore()
malware_vision = MalwareVisionCore()

# Initialize Thalamus client for Global Workspace integration
thalamus_url = os.getenv("DIGITAL_THALAMUS_URL", "http://digital_thalamus_service:8012")
thalamus_client = ThalamusClient(
    thalamus_url=thalamus_url,
    sensor_id="visual_cortex_primary",
    sensor_type="visual"
)


class ImageAnalysisRequest(BaseModel):
    """Request model for submitting an image for analysis.

    Attributes:
        image_base64 (str): The image content encoded in base64.
        analysis_type (str): The type of analysis to perform (e.g., 'object_detection', 'scene_understanding').
        priority (int): The priority of the analysis (1-10, 10 being highest).
    """

    image_base64: str
    analysis_type: str
    priority: int = 5


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Visual Cortex Service."""
    print("👁️ Starting Maximus Visual Cortex Service v2.0...")  # pragma: no cover
    print(f"   Thalamus URL: {thalamus_url}")
    print("✅ Maximus Visual Cortex Service started successfully.")  # pragma: no cover


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Visual Cortex Service."""
    print("👋 Shutting down Maximus Visual Cortex Service...")  # pragma: no cover
    await thalamus_client.close()
    print("🛑 Maximus Visual Cortex Service shut down.")  # pragma: no cover


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Visual Cortex Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Visual Cortex Service is operational."}


@app.post("/analyze_image")
async def analyze_image_endpoint(request: ImageAnalysisRequest) -> Dict[str, Any]:
    """Submits an image for analysis and returns the results.

    Args:
        request (ImageAnalysisRequest): The request body containing the image and analysis parameters.

    Returns:
        Dict[str, Any]: The results of the image analysis.

    Raises:
        HTTPException: If the image processing fails or an invalid analysis type is provided.
    """
    print(f"[API] Received image analysis request (type: {request.analysis_type}, priority: {request.priority})")
    try:
        # Decode base64 image (simplified, actual image processing would happen here)
        image_data = base64.b64decode(request.image_base64)

        results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": request.analysis_type,
        }

        if request.analysis_type == "object_detection":
            detection_results = await event_driven_vision.process_image(image_data)
            results["object_detections"] = detection_results
        elif request.analysis_type == "scene_understanding":
            scene_results = await attention_system.analyze_scene(image_data)
            results["scene_understanding"] = scene_results
        elif request.analysis_type == "network_traffic_visualization":
            network_results = await network_vision.analyze_network_traffic_image(image_data)
            results["network_traffic_analysis"] = network_results
        elif request.analysis_type == "malware_signature_detection":
            malware_results = await malware_vision.detect_malware_signature(image_data)
            results["malware_detection"] = malware_results
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis type: {request.analysis_type}",
            )

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
            print(f"   📡 Visual perception submitted to Thalamus (salience: {thalamus_response.get('salience', 0.0):.2f})")
        except Exception as e:
            print(f"   ⚠️  Failed to submit to Thalamus: {e}")
            results["thalamus_broadcast"] = {
                "submitted": False,
                "error": str(e)
            }

        return results
    except HTTPException:
        raise  # Re-raise HTTPException as-is (e.g., 400 for invalid type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@app.get("/event_driven_vision/status")
async def get_event_driven_vision_status() -> Dict[str, Any]:
    """Retrieves the current status of the event-driven vision core.

    Returns:
        Dict[str, Any]: The status of the event-driven vision core.
    """
    return await event_driven_vision.get_status()


@app.get("/attention_system/status")
async def get_attention_system_status() -> Dict[str, Any]:
    """Retrieves the current status of the attention system core.

    Returns:
        Dict[str, Any]: The status of the attention system core.
    """
    return await attention_system.get_status()


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8003)
