"""Maximus Core Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Core Service.
It initializes and starts the Maximus AI system, including its autonomic core,
and exposes its capabilities via an API (e.g., FastAPI).

It handles the setup of the application, defines API endpoints for interaction,
and manages the lifecycle of the Maximus AI, ensuring it can receive requests,
process them, and return intelligent responses.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import asyncio

from maximus_integrated import MaximusIntegrated

app = FastAPI(title="Maximus Core Service", version="1.0.0")
maximus_ai: Optional[MaximusIntegrated] = None


class QueryRequest(BaseModel):
    """Request model for processing a query.

    Attributes:
        query (str): The natural language query to be processed by Maximus AI.
        context (Optional[Dict[str, Any]]): Additional contextual information for the query.
    """
    query: str
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Initializes the Maximus AI system and starts its autonomic core on application startup."""
    global maximus_ai
    print("🚀 Starting Maximus Core Service...")
    maximus_ai = MaximusIntegrated()
    await maximus_ai.start_autonomic_core()
    print("✅ Maximus Core Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Shuts down the Maximus AI system and its autonomic core on application shutdown."""
    global maximus_ai
    print("👋 Shutting down Maximus Core Service...")
    if maximus_ai:
        await maximus_ai.stop_autonomic_core()
    print("🛑 Maximus Core Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Maximus Core Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    if maximus_ai:
        status = await maximus_ai.get_system_status()
        return {"status": "healthy", "maximus_status": status}
    raise HTTPException(status_code=503, detail="Maximus AI not initialized.")


@app.post("/query")
async def process_query_endpoint(request: QueryRequest) -> Dict[str, Any]:
    """Processes a natural language query using the Maximus AI.

    Args:
        request (QueryRequest): The request body containing the query and optional context.

    Returns:
        Dict[str, Any]: The response from the Maximus AI, including the final answer, confidence score, and other metadata.

    Raises:
        HTTPException: If the Maximus AI is not initialized.
    """
    if not maximus_ai:
        raise HTTPException(status_code=503, detail="Maximus AI not initialized.")
    try:
        response = await maximus_ai.process_query(request.query, request.context)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    # This block is for local development and running the FastAPI app directly.
    # In a production Docker environment, uvicorn is typically run via command line.
    uvicorn.run(app, host="0.0.0.0", port=8000)