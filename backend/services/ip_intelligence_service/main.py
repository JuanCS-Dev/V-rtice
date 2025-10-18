"""Maximus IP Intelligence Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus IP Intelligence
Service. It initializes and configures the FastAPI application, sets up event
handlers for startup and shutdown, and defines the API endpoints for querying
and managing IP intelligence data.

It handles the integration with external IP intelligence databases and APIs,
performing real-time lookups for IP addresses, and enriching security event
data with IP-related context. This service is crucial for identifying suspicious
or malicious IP addresses, supporting network forensics, threat hunting, and
geo-fencing security policies within the Maximus AI system.
"""

import asyncio
from datetime import datetime
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException

from config import get_settings
from database import get_ip_data, update_ip_data
from models import IPInfo, IPQuery

app = FastAPI(title="Maximus IP Intelligence Service", version="1.0.0")

settings = get_settings()


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the IP Intelligence Service."""
    print("🌐 Starting Maximus IP Intelligence Service...")
    # In a real scenario, connect to external IP intelligence providers
    print("✅ Maximus IP Intelligence Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the IP Intelligence Service."""
    print("👋 Shutting down Maximus IP Intelligence Service...")
    print("🛑 Maximus IP Intelligence Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the IP Intelligence Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "IP Intelligence Service is operational."}


@app.post("/query_ip", response_model=IPInfo)
async def query_ip_intelligence(query: IPQuery) -> IPInfo:
    """Queries for intelligence data about a specific IP address.

    Args:
        query (IPQuery): The request body containing the IP address to query.

    Returns:
        IPInfo: Detailed information about the IP address.

    Raises:
        HTTPException: If the IP address is not found or an error occurs.
    """
    print(f"[API] Querying IP intelligence for: {query.ip_address}")
    
    # Try to get from local cache first
    ip_info = await get_ip_data(query.ip_address)
    
    if not ip_info:
        # Fetch from external APIs
        print(f"[API] IP {query.ip_address} not in cache, querying external sources...")
        from api_clients import lookup_ip_intelligence
        
        ip_info = await lookup_ip_intelligence(query.ip_address)
        
        # Cache the result
        if ip_info:
            await update_ip_data(ip_info)
    
    if not ip_info:
        raise HTTPException(
            status_code=404,
            detail=f"IP intelligence not found for {query.ip_address}"
        )
    
    return ip_info


@app.get("/ip/{ip_address}", response_model=IPInfo)
async def get_ip_details(ip_address: str) -> IPInfo:
    """Retrieves intelligence data for a specific IP address directly by path parameter.

    Args:
        ip_address (str): The IP address to retrieve details for.

    Returns:
        IPInfo: Detailed information about the IP address.

    Raises:
        HTTPException: If the IP address is not found or an error occurs.
    """
    print(f"[API] Getting IP details for: {ip_address}")
    ip_info = await get_ip_data(ip_address)
    if not ip_info:
        raise HTTPException(
            status_code=404,
            detail=f"IP address {ip_address} not found in intelligence database.",
        )
    return ip_info


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8022)
