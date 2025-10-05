"""Maximus Network Monitor Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Network Monitor
Service. It initializes and configures the FastAPI application, sets up event
handlers for startup and shutdown, and defines the API endpoints for collecting
and exposing network telemetry.

It orchestrates the continuous observation and analysis of network traffic,
connections, and events, detecting anomalies, suspicious connections, and
potential intrusions. This service is crucial for providing real-time network
intelligence to other Maximus AI services for situational awareness, threat
detection, and incident response.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime
import random

app = FastAPI(title="Maximus Network Monitor Service", version="1.0.0")

# In-memory storage for network events (mock)
network_events: List[Dict[str, Any]] = []


class NetworkEvent(BaseModel):
    """Request model for submitting a network event.

    Attributes:
        timestamp (str): ISO formatted timestamp of the event.
        event_type (str): The type of network event (e.g., 'connection', 'packet_drop', 'anomaly').
        source_ip (str): Source IP address.
        destination_ip (str): Destination IP address.
        port (Optional[int]): Port number involved.
        protocol (Optional[str]): Network protocol.
        details (Optional[Dict[str, Any]]): Additional event details.
    """
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event_type: str
    source_ip: str
    destination_ip: str
    port: Optional[int] = None
    protocol: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Network Monitor Service."""
    print("📡 Starting Maximus Network Monitor Service...")
    # Start background task for simulating network traffic
    asyncio.create_task(simulate_network_traffic())
    print("✅ Maximus Network Monitor Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Network Monitor Service."""
    print("👋 Shutting down Maximus Network Monitor Service...")
    print("🛑 Maximus Network Monitor Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Network Monitor Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Network Monitor Service is operational."}


@app.post("/ingest_event")
async def ingest_network_event(event: NetworkEvent) -> Dict[str, Any]:
    """Ingests a network event for monitoring and analysis.

    Args:
        event (NetworkEvent): The network event to ingest.

    Returns:
        Dict[str, Any]: A dictionary confirming the event ingestion.
    """
    network_events.append(event.dict())
    if len(network_events) > 1000: # Keep history size manageable
        network_events.pop(0)
    print(f"[API] Ingested network event: {event.event_type} from {event.source_ip} to {event.destination_ip}")
    return {"status": "success", "message": "Event ingested.", "timestamp": datetime.now().isoformat()}


@app.get("/network_status")
async def get_network_status() -> Dict[str, Any]:
    """Retrieves the current status of the monitored network.

    Returns:
        Dict[str, Any]: A dictionary summarizing the network status and recent events.
    """
    # Simulate analysis of recent events
    anomalies = [e for e in network_events if e.get("event_type") == "anomaly"]
    suspicious_connections = [e for e in network_events if e.get("event_type") == "connection" and e.get("details", {}).get("suspicious")]

    return {
        "timestamp": datetime.now().isoformat(),
        "total_events_ingested": len(network_events),
        "anomalies_detected": len(anomalies),
        "suspicious_connections": len(suspicious_connections),
        "network_health": "optimal" if not anomalies and not suspicious_connections else "degraded"
    }


@app.get("/recent_events", response_model=List[NetworkEvent])
async def get_recent_events(limit: int = 10) -> List[NetworkEvent]:
    """Retrieves a list of recent network events.

    Args:
        limit (int): The maximum number of events to retrieve.

    Returns:
        List[NetworkEvent]: A list of recent network events.
    """
    return network_events[-limit:]


async def simulate_network_traffic():
    """Simulates continuous network traffic and events."""
    ips = [f"192.168.1.{i}" for i in range(10, 20)] + [f"10.0.0.{i}" for i in range(1, 5)]
    event_types = ["connection", "connection", "connection", "packet_drop", "anomaly"]
    protocols = ["TCP", "UDP", "ICMP"]

    while True:
        await asyncio.sleep(random.uniform(0.5, 2.0)) # Simulate irregular traffic
        
        event_type = random.choice(event_types)
        source_ip = random.choice(ips)
        destination_ip = random.choice(ips)
        port = random.randint(1, 65535)
        protocol = random.choice(protocols)
        details = {}

        if event_type == "anomaly":
            details["reason"] = random.choice(["unusual_port_scan", "high_bandwidth_usage", "failed_login_attempts"])
            details["severity"] = random.choice(["medium", "high"])
        elif event_type == "connection" and random.random() < 0.1: # 10% chance of suspicious connection
            details["suspicious"] = True
            details["reason"] = "connection to known bad IP"

        event = NetworkEvent(
            event_type=event_type,
            source_ip=source_ip,
            destination_ip=destination_ip,
            port=port,
            protocol=protocol,
            details=details
        )
        await ingest_network_event(event)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8031)