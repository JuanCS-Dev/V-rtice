"""Maximus Auditory Cortex Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Auditory
Cortex Service. It exposes functionalities for simulating audio processing,
speech recognition, sound event detection, and auditory data interpretation.

Endpoints are provided for:
- Submitting audio data for analysis.
- Retrieving speech-to-text transcripts.
- Accessing sound event detection and localization results.

FASE 3 Enhancement: Integrates with Digital Thalamus for Global Workspace
broadcasting of salient auditory perceptions.

This API allows other Maximus AI services or external applications to interact
with the auditory perception capabilities in a standardized and efficient manner.
"""

import base64
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add shared directory to path for Thalamus client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../shared"))

from binaural_correlation import BinauralCorrelation
from c2_beacon_detector import C2BeaconDetector
from cocktail_party_triage import CocktailPartyTriage
from thalamus_client import ThalamusClient
from ttp_signature_recognition import TTPSignatureRecognition

app = FastAPI(title="Maximus Auditory Cortex Service", version="2.0.0")

# Initialize auditory processing cores
binaural_correlation = BinauralCorrelation()
cocktail_party_triage = CocktailPartyTriage()
ttp_recognition = TTPSignatureRecognition()
c2_detector = C2BeaconDetector()

# Initialize Thalamus client for Global Workspace integration
thalamus_url = os.getenv("DIGITAL_THALAMUS_URL", "http://digital_thalamus_service:8012")
thalamus_client = ThalamusClient(
    thalamus_url=thalamus_url,
    sensor_id="auditory_cortex_primary",
    sensor_type="auditory"
)


class AudioAnalysisRequest(BaseModel):
    """Request model for submitting audio for analysis.

    Attributes:
        audio_base64 (str): The audio content encoded in base64.
        analysis_type (str): The type of analysis to perform (e.g., 'speech_to_text', 'sound_event_detection').
        language (Optional[str]): The language of the audio (e.g., 'en-US').
        priority (int): The priority of the analysis (1-10, 10 being highest).
    """

    audio_base64: str
    analysis_type: str
    language: Optional[str] = "en-US"
    priority: int = 5


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Auditory Cortex Service."""
    print("👂 Starting Maximus Auditory Cortex Service v2.0...")  # pragma: no cover
    print(f"   Thalamus URL: {thalamus_url}")
    print("✅ Maximus Auditory Cortex Service started successfully.")  # pragma: no cover


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Auditory Cortex Service."""
    print("👋 Shutting down Maximus Auditory Cortex Service...")  # pragma: no cover
    await thalamus_client.close()
    print("🛑 Maximus Auditory Cortex Service shut down.")  # pragma: no cover


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Auditory Cortex Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Auditory Cortex Service is operational."}


@app.post("/analyze_audio")
async def analyze_audio_endpoint(request: AudioAnalysisRequest) -> Dict[str, Any]:
    """Submits audio data for analysis and returns the results.

    Args:
        request (AudioAnalysisRequest): The request body containing the audio and analysis parameters.

    Returns:
        Dict[str, Any]: The results of the audio analysis.

    Raises:
        HTTPException: If the audio processing fails or an invalid analysis type is provided.
    """
    print(f"[API] Received audio analysis request (type: {request.analysis_type}, priority: {request.priority})")
    try:
        # Decode base64 audio (simplified, actual audio processing would happen here)
        audio_data = base64.b64decode(request.audio_base64)

        results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": request.analysis_type,
        }

        if request.analysis_type == "speech_to_text":
            transcript = await cocktail_party_triage.process_audio_for_speech(audio_data, request.language)
            results["transcript"] = transcript
        elif request.analysis_type == "sound_event_detection":
            events = await binaural_correlation.detect_sound_events(audio_data)
            results["sound_events"] = events
        elif request.analysis_type == "ttp_recognition":
            ttp_results = await ttp_recognition.recognize_ttp_signature(audio_data)
            results["ttp_recognition"] = ttp_results
        elif request.analysis_type == "c2_beacon_detection":
            c2_detection = await c2_detector.detect_c2_beacon(audio_data)
            results["c2_beacon_detection"] = c2_detection
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
            print(f"   📡 Auditory perception submitted to Thalamus (salience: {thalamus_response.get('salience', 0.0):.2f})")
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
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")


@app.get("/binaural_correlation/status")
async def get_binaural_correlation_status() -> Dict[str, Any]:
    """Retrieves the current status of the binaural correlation system.

    Returns:
        Dict[str, Any]: The status of the binaural correlation system.
    """
    return await binaural_correlation.get_status()


@app.get("/cocktail_party_triage/status")
async def get_cocktail_party_triage_status() -> Dict[str, Any]:
    """Retrieves the current status of the cocktail party triage system.

    Returns:
        Dict[str, Any]: The status of the cocktail party triage system.
    """
    return await cocktail_party_triage.get_status()


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8004)
