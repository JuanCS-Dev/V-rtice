"""Maximus AI Immune System - API Endpoints.

This module defines the FastAPI application and its endpoints for the AI Immune
System Service. It exposes functionalities for monitoring the AI's health,
detecting anomalies, triggering immune responses, and managing adaptive learning.

Endpoints are provided for:
- Submitting system telemetry for anomaly detection.
- Querying the current immune status and threat levels.
- Initiating defensive actions or adaptive learning processes.

This API allows other Maximus AI services or external systems to interact with
the AI Immune System, enabling proactive self-defense and resilience for the
overall Maximus AI.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
from datetime import datetime

from circuit_breaker import CircuitBreaker
from consensus_validator import ConsensusValidator
from adaptive_learning import AdaptiveLearning

app = FastAPI(title="Maximus AI Immune System", version="1.0.0")

# Initialize immune system components
circuit_breaker = CircuitBreaker()
consensus_validator = ConsensusValidator()
adaptive_learning = AdaptiveLearning()


class TelemetryData(BaseModel):
    """Request model for submitting telemetry data.

    Attributes:
        service_id (str): Identifier of the service submitting telemetry.
        metrics (Dict[str, Any]): A dictionary of metrics (e.g., CPU, memory, error rates).
        event_type (Optional[str]): The type of event (e.g., 'heartbeat', 'error', 'anomaly').
    """
    service_id: str
    metrics: Dict[str, Any]
    event_type: Optional[str] = None


class ImmuneResponseRequest(BaseModel):
    """Request model for triggering an immune response.

    Attributes:
        threat_id (str): Identifier of the detected threat.
        response_type (str): The type of immune response to trigger (e.g., 'isolate', 'quarantine', 'heal').
        parameters (Optional[Dict[str, Any]]): Parameters for the immune response.
    """
    threat_id: str
    response_type: str
    parameters: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the AI Immune System Service."""
    print("🛡️ Starting Maximus AI Immune System Service...")
    print("✅ Maximus AI Immune System Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the AI Immune System Service."""
    print("👋 Shutting down Maximus AI Immune System Service...")
    print("🛑 Maximus AI Immune System Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the AI Immune System Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "AI Immune System Service is operational."}


@app.post("/telemetry")
async def submit_telemetry(data: TelemetryData) -> Dict[str, Any]:
    """Submits telemetry data for anomaly detection and immune system monitoring.

    Args:
        data (TelemetryData): The telemetry data from a service.

    Returns:
        Dict[str, Any]: A dictionary containing the immune system's assessment of the telemetry.
    """
    print(f"[API] Received telemetry from {data.service_id} (event: {data.event_type})")
    
    # Simulate anomaly detection
    is_anomalous = await consensus_validator.validate_telemetry(data.service_id, data.metrics)
    
    # Simulate circuit breaker logic
    if is_anomalous:
        circuit_breaker.trip(data.service_id)
        print(f"[API] Circuit breaker tripped for {data.service_id} due to anomaly.")

    return {
        "timestamp": datetime.now().isoformat(),
        "service_id": data.service_id,
        "anomaly_detected": is_anomalous,
        "circuit_breaker_status": circuit_breaker.get_status(data.service_id)
    }


@app.post("/immune_response")
async def trigger_immune_response(request: ImmuneResponseRequest) -> Dict[str, Any]:
    """Triggers a specific immune response to a detected threat.

    Args:
        request (ImmuneResponseRequest): The request body containing threat ID and response type.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the immune response.
    """
    print(f"[API] Triggering immune response '{request.response_type}' for threat {request.threat_id}")
    await asyncio.sleep(0.5) # Simulate response execution

    # Simulate adaptive learning based on response outcome
    learning_outcome = await adaptive_learning.learn_from_response(request.threat_id, request.response_type, {"success": True})

    return {
        "timestamp": datetime.now().isoformat(),
        "threat_id": request.threat_id,
        "response_type": request.response_type,
        "status": "executed",
        "learning_outcome": learning_outcome
    }


@app.get("/circuit_breaker/{service_id}/status")
async def get_circuit_breaker_status(service_id: str) -> Dict[str, Any]:
    """Retrieves the current status of the circuit breaker for a specific service.

    Args:
        service_id (str): The ID of the service.

    Returns:
        Dict[str, Any]: The status of the circuit breaker.
    """
    return circuit_breaker.get_status(service_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
