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
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import HCLDataType
from database import HCLDataEntry, get_db, init_db

app = FastAPI(title="Maximus HCL Knowledge Base Service", version="1.0.0")


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
    init_db()
    print("✅ Database initialized")
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
async def store_hcl_data(
    request: StoreDataRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Stores HCL-related data in the knowledge base.

    Args:
        request (StoreDataRequest): The request body containing the data type and payload.
        db (Session): Database session.

    Returns:
        Dict[str, Any]: A dictionary confirming the data storage.
    """
    print(f"[API] Storing {request.data_type.value} data.")
    
    entry = HCLDataEntry(
        data_type=request.data_type.value,
        data=request.data,
        entry_metadata={"stored_at": datetime.now().isoformat()}
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    return {
        "status": "success",
        "message": f"{request.data_type.value} data stored.",
        "entry_id": entry.id,
    }


@app.get("/retrieve_data/{data_type}")
async def retrieve_hcl_data(
    data_type: HCLDataType,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Retrieves HCL-related data from the knowledge base.

    Args:
        data_type (HCLDataType): The type of HCL data to retrieve.
        limit (int): The maximum number of entries to retrieve.

    Returns:
        List[Dict[str, Any]]: A list of HCL data entries.
    """
    from sqlalchemy import desc
    
    print(f"[API] Retrieving {data_type.value} data (limit: {limit}).")
    
    entries = db.query(HCLDataEntry).filter(
        HCLDataEntry.data_type == data_type.value
    ).order_by(desc(HCLDataEntry.created_at)).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "data_type": e.data_type,
            "data": e.data,
            "metadata": e.metadata,
            "created_at": e.created_at.isoformat()
        }
        for e in entries
    ]


@app.get("/knowledge_summary")
async def get_knowledge_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Provides a summary of the data stored in the knowledge base.

    Returns:
        Dict[str, Any]: A dictionary summarizing the knowledge base content.
    """
    from sqlalchemy import func
    
    summary = {"timestamp": datetime.now().isoformat()}
    for data_type in [HCLDataType.METRICS, HCLDataType.ANALYSIS, HCLDataType.PLAN, HCLDataType.EXECUTION]:
        count = db.query(func.count(HCLDataEntry.id)).filter(
            HCLDataEntry.data_type == data_type.value
        ).scalar()
        
        last_entry = db.query(HCLDataEntry).filter(
            HCLDataEntry.data_type == data_type.value
        ).order_by(HCLDataEntry.created_at.desc()).first()
        
        summary[data_type.value] = {
            "count": count,
            "last_entry": last_entry.created_at.isoformat() if last_entry else "N/A",
        }
    return summary


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8017)
