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
    ip_info = await get_ip_data(query.ip_address)
    if not ip_info:
        # Simulate fetching from external source if not in local DB
        print(f"[API] IP {query.ip_address} not in local cache, simulating external lookup.")
        await asyncio.sleep(0.5)  # Simulate external API call
        # Mock external lookup result
        if query.ip_address == "8.8.8.8":
            ip_info = IPInfo(
                ip_address="8.8.8.8",
                country="US",
                city="Mountain View",
                isp="Google LLC",
                reputation="Clean",
                threat_score=0.0,
                last_checked=datetime.now().isoformat(),
            )
        elif query.ip_address == "1.2.3.4":
            ip_info = IPInfo(
                ip_address="1.2.3.4",
                country="RU",
                city="Moscow",
                isp="EvilCorp Hosting",
                reputation="Malicious",
                threat_score=0.9,
                last_checked=datetime.now().isoformat(),
            )
        else:
            ip_info = IPInfo(
                ip_address=query.ip_address,
                country="Unknown",
                city="Unknown",
                isp="Unknown",
                reputation="Neutral",
                threat_score=0.5,
                last_checked=datetime.now().isoformat(),
            )
        await update_ip_data(ip_info)  # Store in local DB

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
