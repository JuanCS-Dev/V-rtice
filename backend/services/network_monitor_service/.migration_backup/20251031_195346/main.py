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

import asyncio
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import NetworkEvent as NetworkEventDB
from database import get_db, init_db

app = FastAPI(title="Maximus Network Monitor Service", version="1.0.0")


class NetworkEventRequest(BaseModel):
    """Request model for submitting a network event.

    Attributes:
        timestamp (str): ISO formatted timestamp of the event.
        event_type (str): The type of network event (e.g., 'connection', 'packet_drop', 'anomaly').
        source_ip (str): Source IP address.
        destination_ip (str): Destination IP address.
        port (Optional[int]): Port number involved.
        protocol (Optional[str]): Network protocol.
        severity (str): Event severity (low, medium, high, critical).
        description (Optional[str]): Event description.
    """

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event_type: str
    source_ip: str
    destination_ip: str = ""
    port: Optional[int] = None
    protocol: Optional[str] = None
    severity: str = "medium"
    description: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Network Monitor Service."""
    print("📡 Starting Maximus Network Monitor Service...")
    init_db()
    print("✅ Database initialized")
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
async def ingest_network_event(
    event: NetworkEventRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ingests a network event for monitoring and analysis.

    Args:
        event (NetworkEventRequest): The network event to ingest.
        db (Session): Database session.

    Returns:
        Dict[str, Any]: A dictionary confirming the event ingestion.
    """
    # Store in database
    db_event = NetworkEventDB(
        timestamp=datetime.fromisoformat(event.timestamp),
        event_type=event.event_type,
        source_ip=event.source_ip,
        destination_ip=event.destination_ip,
        port=event.port,
        protocol=event.protocol,
        severity=event.severity,
        description=event.description
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    print(f"[API] Ingested network event ID {db_event.id}: {event.event_type} from {event.source_ip}")
    return {
        "status": "success",
        "message": "Event ingested.",
        "event_id": db_event.id,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/network_status")
async def get_network_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves the current status of the monitored network.

    Args:
        db (Session): Database session.

    Returns:
        Dict[str, Any]: A dictionary summarizing the network status and recent events.
    """
    # Query recent events from database
    from sqlalchemy import func, desc
    
    total_events = db.query(func.count(NetworkEventDB.id)).scalar()
    anomalies = db.query(func.count(NetworkEventDB.id)).filter(
        NetworkEventDB.event_type == "anomaly"
    ).scalar()
    recent_events = db.query(NetworkEventDB).order_by(
        desc(NetworkEventDB.timestamp)
    ).limit(10).all()
    
    critical_events = db.query(func.count(NetworkEventDB.id)).filter(
        NetworkEventDB.severity == "critical"
    ).scalar()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_events_ingested": total_events,
        "anomalies_detected": anomalies,
        "critical_events": critical_events,
        "network_health": ("optimal" if anomalies == 0 and critical_events == 0 else "degraded"),
    }


@app.get("/recent_events")
async def get_recent_events(limit: int = 10, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieves a list of recent network events.

    Args:
        limit (int): The maximum number of events to retrieve.
        db (Session): Database session.

    Returns:
        List[Dict[str, Any]]: A list of recent network events.
    """
    from sqlalchemy import desc
    
    events = db.query(NetworkEventDB).order_by(
        desc(NetworkEventDB.timestamp)
    ).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "source_ip": e.source_ip,
            "destination_ip": e.destination_ip,
            "port": e.port,
            "protocol": e.protocol,
            "severity": e.severity,
            "description": e.description
        }
        for e in events
    ]


async def simulate_network_traffic():
    """Simulates continuous network traffic and events."""
    from database import SessionLocal, NetworkEvent
    from datetime import datetime
    
    ips = [f"192.168.1.{i}" for i in range(10, 20)] + [f"10.0.0.{i}" for i in range(1, 5)]
    event_types = ["connection", "connection", "connection", "packet_drop", "anomaly"]
    protocols = ["TCP", "UDP", "ICMP"]

    while True:
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Simulate irregular traffic

        event_type = random.choice(event_types)
        source_ip = random.choice(ips)
        destination_ip = random.choice(ips)
        port = random.randint(1, 65535)
        protocol = random.choice(protocols)
        details = {}

        if event_type == "anomaly":
            details["reason"] = random.choice(["unusual_port_scan", "high_bandwidth_usage", "failed_login_attempts"])
            details["severity"] = random.choice(["medium", "high"])
        elif event_type == "connection" and random.random() < 0.1:  # 10% chance of suspicious connection
            details["suspicious"] = True
            details["reason"] = "connection to known bad IP"

        # Store directly in database (background task doesn't go through API)
        db = SessionLocal()
        try:
            db_event = NetworkEvent(
                timestamp=datetime.utcnow(),
                event_type=event_type,
                source_ip=source_ip,
                destination_ip=destination_ip,
                port=port,
                protocol=protocol,
                severity=details.get("severity", "low"),
                description=str(details) if details else None
            )
            db.add(db_event)
            db.commit()
        finally:
            db.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8031)
