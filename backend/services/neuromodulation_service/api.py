"""Maximus Neuromodulation Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the
Neuromodulation Service. It exposes functionalities for dynamically adjusting
the AI's internal states, cognitive biases, and processing parameters to
optimize its performance for specific tasks or environmental conditions.

Endpoints are provided for:
- Modulating attention levels and focus.
- Adjusting learning rates and memory consolidation.
- Influencing motivational states (e.g., 'curiosity', 'caution').

This API allows other Maximus AI services or human operators to fine-tune the
AI's cognitive functions, enabling it to adapt its behavior and optimize its
effectiveness in real-time for various operational scenarios.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from acetylcholine_core import AcetylcholineCore
from dopamine_core import DopamineCore
from neuromodulation_controller import NeuromodulationController
from noradrenaline_core import NoradrenalineCore
from serotonin_core import SerotoninCore

app = FastAPI(title="Maximus Neuromodulation Service", version="1.0.0")

# Initialize neuromodulator cores
dopamine_core = DopamineCore()
serotonin_core = SerotoninCore()
noradrenaline_core = NoradrenalineCore()
acetylcholine_core = AcetylcholineCore()

# Initialize main controller
neuromodulation_controller = NeuromodulationController(
    dopamine_core=dopamine_core,
    serotonin_core=serotonin_core,
    noradrenaline_core=noradrenaline_core,
    acetylcholine_core=acetylcholine_core,
)


class ModulationRequest(BaseModel):
    """Request model for applying neuromodulation.

    Attributes:
        modulator_type (str): The type of neuromodulator (e.g., 'dopamine', 'serotonin').
        parameter (str): The specific parameter to modulate (e.g., 'reward_sensitivity', 'attention_level').
        value (float): The new value for the parameter.
        context (Optional[Dict[str, Any]]): Additional context for the modulation.
    """

    modulator_type: str
    parameter: str
    value: float
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Neuromodulation Service."""
    print("🧠 Starting Maximus Neuromodulation Service...")
    print("✅ Maximus Neuromodulation Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Neuromodulation Service."""
    print("👋 Shutting down Maximus Neuromodulation Service...")
    print("🛑 Maximus Neuromodulation Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Neuromodulation Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Neuromodulation Service is operational."}


@app.post("/modulate")
async def apply_neuromodulation(request: ModulationRequest) -> Dict[str, Any]:
    """Applies neuromodulation to a specific AI parameter.

    Args:
        request (ModulationRequest): The request body containing modulation details.

    Returns:
        Dict[str, Any]: A dictionary summarizing the modulation effect.

    Raises:
        HTTPException: If the modulator type or parameter is unsupported.
    """
    print(f"[API] Applying {request.modulator_type} modulation to {request.parameter} with value {request.value}")
    try:
        result = await neuromodulation_controller.modulate_parameter(
            request.modulator_type, request.parameter, request.value, request.context
        )
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "modulation_result": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modulation failed: {str(e)}")


@app.get("/status")
async def get_neuromodulation_status() -> Dict[str, Any]:
    """Retrieves the current status of the Neuromodulation Service.

    Returns:
        Dict[str, Any]: A dictionary summarizing the status of all neuromodulator cores.
    """
    return await neuromodulation_controller.get_overall_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8033)
