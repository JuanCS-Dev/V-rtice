"""Maximus HCL Monitor Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Homeostatic Control
Loop (HCL) Monitor Service. It initializes and configures the FastAPI
application, sets up event handlers for startup and shutdown, and defines the
API endpoints for collecting and exposing system metrics.

It orchestrates the continuous collection of real-time operational data from
various Maximus AI services and the underlying infrastructure. This service is
crucial for providing accurate and up-to-date monitoring information to the
HCL Analyzer Service, enabling effective self-management and adaptive behavior.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime

from collectors import SystemMetricsCollector

app = FastAPI(title="Maximus HCL Monitor Service", version="1.0.0")

# Initialize metrics collector
system_metrics_collector = SystemMetricsCollector()


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the HCL Monitor Service."""
    print("📈 Starting Maximus HCL Monitor Service...")
    # Start background task for continuous metric collection
    asyncio.create_task(system_metrics_collector.start_collection())
    print("✅ Maximus HCL Monitor Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the HCL Monitor Service."""
    print("👋 Shutting down Maximus HCL Monitor Service...")
    await system_metrics_collector.stop_collection()
    print("🛑 Maximus HCL Monitor Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the HCL Monitor Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "HCL Monitor Service is operational."}


@app.get("/metrics")
async def get_current_metrics() -> Dict[str, Any]:
    """Retrieves the latest collected system metrics.

    Returns:
        Dict[str, Any]: A dictionary containing the current system metrics.
    """
    return system_metrics_collector.get_latest_metrics()


@app.get("/metrics/history", response_model=List[Dict[str, Any]])
async def get_metrics_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves a history of collected system metrics.

    Args:
        limit (int): The maximum number of historical metrics to retrieve.

    Returns:
        List[Dict[str, Any]]: A list of historical system metrics.
    """
    return system_metrics_collector.get_metrics_history(limit)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8018)
