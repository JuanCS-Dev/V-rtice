"""Maximus SSL Monitor Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus SSL Monitor Service.
It initializes and configures the FastAPI application, sets up event handlers
for startup and shutdown, and defines the API endpoints for monitoring SSL/TLS
certificates.

It orchestrates the continuous monitoring of SSL/TLS certificates of various
services and domains, ensuring their validity, proper configuration, and detecting
potential security issues or expirations. This service is crucial for maintaining
the cryptographic health of monitored assets and providing real-time intelligence
to other Maximus AI services.
"""

import asyncio
from datetime import datetime, timedelta
import socket
import ssl
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Maximus SSL Monitor Service", version="1.0.0")

# In-memory storage for monitored domains and their SSL status
monitored_domains: Dict[str, Dict[str, Any]] = {}


class MonitorRequest(BaseModel):
    """Request model for adding a domain to be monitored.

    Attributes:
        domain (str): The domain name to monitor.
        port (int): The port to connect to (default: 443).
        check_interval_seconds (int): How often to check the SSL certificate in seconds.
    """

    domain: str
    port: int = 443
    check_interval_seconds: int = 3600  # Default to 1 hour


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the SSL Monitor Service."""
    print("🔒 Starting Maximus SSL Monitor Service...")
    # Start background task for continuous monitoring
    asyncio.create_task(continuous_monitoring())
    print("✅ Maximus SSL Monitor Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the SSL Monitor Service."""
    print("👋 Shutting down Maximus SSL Monitor Service...")
    print("🛑 Maximus SSL Monitor Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the SSL Monitor Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "SSL Monitor Service is operational."}


@app.post("/monitor")
async def add_to_monitor(request: MonitorRequest) -> Dict[str, Any]:
    """Adds a domain to the list of monitored SSL certificates.

    Args:
        request (MonitorRequest): The request body containing domain and monitoring parameters.

    Returns:
        Dict[str, Any]: A dictionary confirming the addition.
    """
    domain_key = f"{request.domain}:{request.port}"
    monitored_domains[domain_key] = {
        "domain": request.domain,
        "port": request.port,
        "check_interval_seconds": request.check_interval_seconds,
        "last_checked": None,
        "status": "pending",
        "certificate_info": None,
    }
    print(f"[API] Added {domain_key} to monitoring list.")
    return {"status": "success", "message": f"Monitoring started for {domain_key}."}


@app.get("/status/{domain_port}")
async def get_domain_status(domain_port: str) -> Dict[str, Any]:
    """Retrieves the current SSL status for a monitored domain.

    Args:
        domain_port (str): The domain:port identifier (e.g., 'example.com:443').

    Returns:
        Dict[str, Any]: A dictionary containing the SSL status and certificate information.

    Raises:
        HTTPException: If the domain is not found in the monitoring list.
    """
    status = monitored_domains.get(domain_port)
    if not status:
        raise HTTPException(
            status_code=404, detail="Domain not found in monitoring list."
        )
    return status


async def check_ssl_certificate(domain: str, port: int) -> Dict[str, Any]:
    """Checks the SSL certificate for a given domain and port.

    Args:
        domain (str): The domain name.
        port (int): The port.

    Returns:
        Dict[str, Any]: A dictionary containing certificate information and status.
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

                # Extract relevant info
                not_before = datetime.strptime(
                    cert["notBefore"][0:-4], "%b %d %H:%M:%S %Y"
                )
                not_after = datetime.strptime(
                    cert["notAfter"][0:-4], "%b %d %H:%M:%S %Y"
                )
                issuer = dict(x[0] for x in cert["issuer"])
                subject = dict(x[0] for x in cert["subject"])

                days_remaining = (not_after - datetime.now()).days
                status = "valid" if days_remaining > 0 else "expired"
                if days_remaining < 30:
                    status = "expiring_soon"

                return {
                    "status": status,
                    "valid_from": not_before.isoformat(),
                    "valid_until": not_after.isoformat(),
                    "days_remaining": days_remaining,
                    "issuer": issuer.get("organizationName", "N/A"),
                    "subject": subject.get("commonName", "N/A"),
                    "error": None,
                }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "details": "Could not retrieve certificate.",
        }


async def continuous_monitoring():
    """Background task for continuously monitoring SSL certificates."""
    while True:
        await asyncio.sleep(1)  # Check every second if any domain needs checking
        current_time = datetime.now()

        for domain_key, info in list(monitored_domains.items()):  # Iterate over a copy
            last_checked = info["last_checked"]
            check_interval = timedelta(seconds=info["check_interval_seconds"])

            if (
                last_checked is None
                or (current_time - datetime.fromisoformat(last_checked))
                > check_interval
            ):
                print(f"[SSLMonitor] Checking SSL for {info['domain']}:{info['port']}")
                cert_info = await check_ssl_certificate(info["domain"], info["port"])
                monitored_domains[domain_key]["last_checked"] = current_time.isoformat()
                monitored_domains[domain_key]["status"] = cert_info["status"]
                monitored_domains[domain_key]["certificate_info"] = cert_info
                print(
                    f"[SSLMonitor] {info['domain']}:{info['port']} status: {cert_info['status']}"
                )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8041)
