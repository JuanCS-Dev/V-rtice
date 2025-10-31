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

# Import Service Registry client
try:
    from shared.vertice_registry_client import auto_register_service, RegistryClient
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False
    print("⚠️  Service Registry client not available - running standalone")

app = FastAPI(title="Maximus IP Intelligence Service", version="1.0.0")

settings = get_settings()

# Global heartbeat task
_heartbeat_task = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the IP Intelligence Service."""
    global _heartbeat_task

    print("🌐 Starting Maximus IP Intelligence Service...")
    # In a real scenario, connect to external IP intelligence providers

    # Auto-register with Service Registry
    if REGISTRY_AVAILABLE:
        try:
            _heartbeat_task = await auto_register_service(
                service_name="ip_intelligence_service",
                port=8034,  # Internal container port
                health_endpoint="/health",
                metadata={"category": "investigation", "version": "1.0.0"}
            )
            print("✅ Registered with Vértice Service Registry")
        except Exception as e:
            print(f"⚠️  Failed to register with service registry: {e}")

    print("✅ Maximus IP Intelligence Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the IP Intelligence Service."""
    global _heartbeat_task

    print("👋 Shutting down Maximus IP Intelligence Service...")

    # Deregister from Service Registry
    if _heartbeat_task:
        _heartbeat_task.cancel()
    if REGISTRY_AVAILABLE:
        try:
            await RegistryClient.deregister("ip_intelligence_service")
        except:
            pass

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


@app.post("/analyze-my-ip")
async def analyze_my_ip() -> Dict:
    """Detects client's public IP and performs full analysis.
    
    Uses ip-api.com to get client's real IP address (works behind proxies/NAT).
    
    Returns:
        Dict with detected IP and full analysis (geolocation, threats, etc.)
    """
    import httpx
    
    try:
        # Detect public IP using ip-api.com (free, no auth required)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://ip-api.com/json/")
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Failed to detect public IP")
            
            data = response.json()
            detected_ip = data.get("query")
            
            if not detected_ip:
                raise HTTPException(status_code=500, detail="Could not determine public IP")
        
        # Perform full analysis on detected IP
        print(f"[API] Analyzing detected IP: {detected_ip}")
        ip_info = await get_ip_data(detected_ip)
        
        return {
            "ip": detected_ip,
            "source": "ip-api.com",
            "analysis": ip_info.dict() if ip_info else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout detecting public IP")
    except Exception as e:
        print(f"[ERROR] analyze-my-ip failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze IP: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8022)
