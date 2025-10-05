"""Maximus HSAS Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Human-System
Alignment Service (HSAS). It exposes functionalities for ensuring that the AI's
actions, decisions, and communication are aligned with human values, intentions,
and ethical guidelines.

Endpoints are provided for:
- Submitting human feedback and preferences.
- Querying the AI's current alignment status.
- Requesting explanations for AI decisions.
- Facilitating human oversight and intervention mechanisms.

This API allows human operators and other Maximus AI services to interact with
the HSAS, promoting transparent, ethical, and beneficial AI behavior within the
overall Maximus AI system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime

from hsas_core import HSASCore

app = FastAPI(title="Maximus HSAS Service", version="1.0.0")

# Initialize HSAS core
hsas_core = HSASCore()


class HumanFeedback(BaseModel):
    """Request model for submitting human feedback.

    Attributes:
        feedback_type (str): The type of feedback (e.g., 'approval', 'correction', 'concern').
        context (Dict[str, Any]): The context of the AI's action or decision.
        feedback_details (str): Detailed description of the feedback.
        rating (Optional[int]): A numerical rating (e.g., 1-5).
    """
    feedback_type: str
    context: Dict[str, Any]
    feedback_details: str
    rating: Optional[int] = None


class ExplanationRequest(BaseModel):
    """Request model for requesting an explanation for an AI decision.

    Attributes:
        decision_id (str): The ID of the AI decision to explain.
        context (Optional[Dict[str, Any]]): Additional context for the explanation request.
    """
    decision_id: str
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the HSAS Service."""
    print("🤝 Starting Maximus HSAS Service...")
    print("✅ Maximus HSAS Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the HSAS Service."""
    print("👋 Shutting down Maximus HSAS Service...")
    print("🛑 Maximus HSAS Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the HSAS Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "HSAS Service is operational."}


@app.post("/submit_feedback")
async def submit_human_feedback(request: HumanFeedback) -> Dict[str, Any]:
    """Submits human feedback to the HSAS for processing and learning.

    Args:
        request (HumanFeedback): The request body containing human feedback details.

    Returns:
        Dict[str, Any]: A dictionary confirming the feedback submission.
    """
    print(f"[API] Received human feedback (type: {request.feedback_type}, rating: {request.rating})")
    await hsas_core.process_human_feedback(request.feedback_type, request.context, request.feedback_details, request.rating)
    return {"status": "success", "message": "Feedback submitted successfully.", "timestamp": datetime.now().isoformat()}


@app.post("/request_explanation")
async def request_ai_explanation(request: ExplanationRequest) -> Dict[str, Any]:
    """Requests an explanation for a specific AI decision or action.

    Args:
        request (ExplanationRequest): The request body containing the decision ID and context.

    Returns:
        Dict[str, Any]: A dictionary containing the AI's explanation.
    """
    print(f"[API] Requesting explanation for decision ID: {request.decision_id}")
    explanation = await hsas_core.generate_explanation(request.decision_id, request.context)
    return {"status": "success", "decision_id": request.decision_id, "explanation": explanation, "timestamp": datetime.now().isoformat()}


@app.get("/alignment_status")
async def get_alignment_status() -> Dict[str, Any]:
    """Retrieves the current human-system alignment status.

    Returns:
        Dict[str, Any]: A dictionary summarizing the AI's alignment with human values.
    """
    return await hsas_core.get_alignment_status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8021)
