"""Maximus HCL Knowledge Base Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Homeostatic Control
Loop (HCL) Knowledge Base Service. It initializes and configures the FastAPI
application, sets up event handlers for startup and shutdown, and defines the
API endpoints for storing, retrieving, and managing HCL-related data.

It handles the persistence of system metrics, analysis results, executed plans,
and learned policies, providing a centralized repository for all HCL knowledge.
This service is crucial for enabling the HCL to learn from past experiences,
adapt to changing conditions, and continuously improve its self-management capabilities.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from models import HCLDataEntry, HCLDataType

app = FastAPI(title="Maximus HCL Knowledge Base Service", version="1.0.0")

# In a real scenario, this would connect to a persistent database (e.g., PostgreSQL, MongoDB)
# For this mock, we'll use an in-memory dictionary.
knowledge_base: Dict[str, List[HCLDataEntry]] = {
    HCLDataType.METRICS.value: [],
    HCLDataType.ANALYSIS.value: [],
    HCLDataType.PLAN.value: [],
    HCLDataType.EXECUTION.value: [],
}


class StoreDataRequest(BaseModel):
    """Request model for storing HCL-related data.

    Attributes:
        data_type (HCLDataType): The type of HCL data to store.
        data (Dict[str, Any]): The actual data payload.
    """

    data_type: HCLDataType
    data: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the HCL Knowledge Base Service."""
    print("📚 Starting Maximus HCL Knowledge Base Service...")
    print("✅ Maximus HCL Knowledge Base Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the HCL Knowledge Base Service."""
    print("👋 Shutting down Maximus HCL Knowledge Base Service...")
    print("🛑 Maximus HCL Knowledge Base Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the HCL Knowledge Base Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {
        "status": "healthy",
        "message": "HCL Knowledge Base Service is operational.",
    }


@app.post("/store_data")
async def store_hcl_data(request: StoreDataRequest) -> Dict[str, Any]:
    """Stores HCL-related data in the knowledge base.

    Args:
        request (StoreDataRequest): The request body containing the data type and payload.

    Returns:
        Dict[str, Any]: A dictionary confirming the data storage.
    """
    print(f"[API] Storing {request.data_type.value} data.")
    entry = HCLDataEntry(
        timestamp=datetime.now().isoformat(),
        data_type=request.data_type,
        data=request.data,
    )
    knowledge_base[request.data_type.value].append(entry)
    await asyncio.sleep(0.05)  # Simulate database write
    return {
        "status": "success",
        "message": f"{request.data_type.value} data stored.",
        "entry_id": len(knowledge_base[request.data_type.value]) - 1,
    }


@app.get("/retrieve_data/{data_type}", response_model=List[HCLDataEntry])
async def retrieve_hcl_data(data_type: HCLDataType, limit: int = 10) -> List[HCLDataEntry]:
    """Retrieves HCL-related data from the knowledge base.

    Args:
        data_type (HCLDataType): The type of HCL data to retrieve.
        limit (int): The maximum number of entries to retrieve.

    Returns:
        List[HCLDataEntry]: A list of HCL data entries.
    """
    print(f"[API] Retrieving {data_type.value} data (limit: {limit}).")
    await asyncio.sleep(0.05)  # Simulate database read
    return knowledge_base.get(data_type.value, [])[-limit:]


@app.get("/knowledge_summary")
async def get_knowledge_summary() -> Dict[str, Any]:
    """Provides a summary of the data stored in the knowledge base.

    Returns:
        Dict[str, Any]: A dictionary summarizing the knowledge base content.
    """
    summary = {"timestamp": datetime.now().isoformat()}
    for data_type, entries in knowledge_base.items():
        summary[data_type] = {
            "count": len(entries),
            "last_entry": entries[-1].timestamp if entries else "N/A",
        }
    return summary


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8017)
