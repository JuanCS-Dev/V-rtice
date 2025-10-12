"""
Reactive Fabric Core Service
Main API for orchestrating honeypots and aggregating threat intelligence

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real Implementation with PostgreSQL + Kafka
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import asyncio
import docker
from docker.errors import DockerException

from models import (
    HoneypotListResponse, HoneypotStats, HoneypotStatus,
    AttackListResponse, AttackSummary, AttackCreate, AttackSeverity,
    TTPListResponse, TTPFrequency,
    HealthResponse,
    ThreatDetectedMessage
)
from database import Database
from kafka_producer import KafkaProducer, create_threat_detected_message

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vertice:vertice_pass@postgres:5432/vertice")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Global instances
db: Optional[Database] = None
kafka_producer: Optional[KafkaProducer] = None
docker_client: Optional[docker.DockerClient] = None


# Background task for health checks
async def honeypot_health_check_task():
    """Background task to check honeypot container health."""
    global docker_client, db, kafka_producer
    
    logger.info("honeypot_health_check_task_started")
    
    while True:
        try:
            if not docker_client or not db:
                await asyncio.sleep(30)
                continue
            
            # Get all honeypots from database
            honeypots = await db.list_honeypots()
            
            for honeypot in honeypots:
                try:
                    # Check Docker container status
                    container = docker_client.containers.get(honeypot.container_name)
                    container_status = container.status  # 'running', 'exited', etc.
                    
                    # Determine honeypot status
                    if container_status == 'running':
                        new_status = HoneypotStatus.ONLINE
                    elif container_status in ['exited', 'dead']:
                        new_status = HoneypotStatus.OFFLINE
                    else:
                        new_status = HoneypotStatus.DEGRADED
                    
                    # Update database if status changed
                    if new_status != honeypot.status:
                        await db.update_honeypot_status(
                            honeypot.honeypot_id,
                            new_status,
                            datetime.utcnow()
                        )
                        
                        logger.info(
                            "honeypot_status_changed",
                            honeypot_id=honeypot.honeypot_id,
                            old_status=honeypot.status.value,
                            new_status=new_status.value
                        )
                        
                        # Publish status change to Kafka
                        if kafka_producer:
                            from kafka_producer import create_honeypot_status_message
                            status_msg = create_honeypot_status_message(
                                honeypot.honeypot_id,
                                new_status.value
                            )
                            await kafka_producer.publish_honeypot_status(status_msg)
                
                except docker.errors.NotFound:
                    logger.warning(
                        "honeypot_container_not_found",
                        honeypot_id=honeypot.honeypot_id,
                        container_name=honeypot.container_name
                    )
                    await db.update_honeypot_status(
                        honeypot.honeypot_id,
                        HoneypotStatus.OFFLINE
                    )
                
                except Exception as e:
                    logger.error(
                        "health_check_error",
                        honeypot_id=honeypot.honeypot_id,
                        error=str(e)
                    )
            
            # Wait 30 seconds before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error("health_check_task_error", error=str(e))
            await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    global db, kafka_producer, docker_client
    
    logger.info("reactive_fabric_core_starting")
    
    # Initialize database
    db = Database(DATABASE_URL)
    db_connected = await db.connect()
    if not db_connected:
        logger.error("database_connection_failed_startup")
    
    # Initialize Kafka producer
    kafka_producer = KafkaProducer(KAFKA_BROKERS)
    kafka_connected = await kafka_producer.connect()
    if not kafka_connected:
        logger.error("kafka_connection_failed_startup")
    
    # Initialize Docker client
    try:
        docker_client = docker.from_env()
        logger.info("docker_client_initialized")
    except DockerException as e:
        logger.error("docker_client_init_failed", error=str(e))
        docker_client = None
    
    # Start background tasks
    health_check_task = asyncio.create_task(honeypot_health_check_task())
    
    yield
    
    logger.info("reactive_fabric_core_shutting_down")
    
    # Cancel background tasks
    health_check_task.cancel()
    try:
        await health_check_task
    except asyncio.CancelledError:
        pass
    
    # Close connections
    if db:
        await db.disconnect()
    
    if kafka_producer:
        await kafka_producer.disconnect()
    
    if docker_client:
        docker_client.close()


# Initialize FastAPI app
app = FastAPI(
    title="Reactive Fabric Core Service",
    description="Orchestrates honeypots and aggregates threat intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration."""
    db_healthy = await db.health_check() if db else False
    kafka_healthy = await kafka_producer.health_check() if kafka_producer else False
    
    # Determine overall status
    if db_healthy and kafka_healthy:
        status = "healthy"
    elif db_healthy or kafka_healthy:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        service="reactive_fabric_core",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database_connected=db_healthy,
        kafka_connected=kafka_healthy,
        redis_connected=False  # TODO: Add Redis health check if needed
    )


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Reactive Fabric Core",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "honeypots": "/api/v1/honeypots",
            "attacks": "/api/v1/attacks/recent",
            "ttps": "/api/v1/ttps/top"
        },
        "documentation": "/docs"
    }


# ============================================================================
# API v1 ENDPOINTS (Sprint 1)
# ============================================================================

@app.get("/api/v1/honeypots", response_model=HoneypotListResponse)
async def list_honeypots():
    """
    List all registered honeypots with statistics.
    
    Returns:
        List of honeypots with status, metrics, and configuration.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get honeypot statistics
        stats = await db.get_honeypot_stats()
        
        # Count online/offline
        online = sum(1 for s in stats if s.status == HoneypotStatus.ONLINE)
        offline = sum(1 for s in stats if s.status == HoneypotStatus.OFFLINE)
        
        return HoneypotListResponse(
            honeypots=stats,
            total=len(stats),
            online=online,
            offline=offline
        )
    
    except Exception as e:
        logger.error("list_honeypots_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/honeypots/{honeypot_id}/stats")
async def get_honeypot_stats(honeypot_id: str):
    """
    Get detailed statistics for a specific honeypot.
    
    Args:
        honeypot_id: Unique identifier of honeypot (e.g., ssh_001)
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get honeypot
        honeypot = await db.get_honeypot_by_id(honeypot_id)
        if not honeypot:
            raise HTTPException(status_code=404, detail="Honeypot not found")
        
        # Get statistics
        attacks_today = await db.get_attacks_today(honeypot_id)
        unique_ips_today = await db.get_unique_ips_today(honeypot_id)
        recent_attacks = await db.get_attacks_by_honeypot(honeypot_id, limit=10)
        
        # Calculate uptime
        uptime_seconds = None
        if docker_client and honeypot.status == HoneypotStatus.ONLINE:
            try:
                container = docker_client.containers.get(honeypot.container_name)
                # Docker doesn't directly expose uptime, approximating from last health check
                if honeypot.last_health_check:
                    uptime_seconds = int((datetime.utcnow() - honeypot.last_health_check).total_seconds())
            except Exception:
                pass
        
        return {
            "honeypot_id": honeypot_id,
            "type": honeypot.type.value,
            "status": honeypot.status.value,
            "uptime_seconds": uptime_seconds,
            "metrics": {
                "attacks_today": attacks_today,
                "unique_ips_today": unique_ips_today,
                "total_attacks": len(recent_attacks),
                "last_attack": recent_attacks[0].captured_at.isoformat() if recent_attacks else None
            },
            "recent_attacks": [
                {
                    "id": str(attack.id),
                    "attacker_ip": attack.attacker_ip,
                    "attack_type": attack.attack_type,
                    "severity": attack.severity.value,
                    "captured_at": attack.captured_at.isoformat()
                }
                for attack in recent_attacks[:5]
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_honeypot_stats_error", honeypot_id=honeypot_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/attacks/recent", response_model=AttackListResponse)
async def get_recent_attacks(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """
    Get recent attacks across all honeypots.
    
    Args:
        limit: Maximum number of attacks to return (1-200)
        offset: Pagination offset
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        attacks = await db.get_recent_attacks(limit, offset)
        total = await db.count_attacks()
        
        return AttackListResponse(
            attacks=attacks,
            total=total,
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error("get_recent_attacks_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/ttps/top", response_model=TTPListResponse)
async def get_top_ttps(limit: int = Query(default=10, ge=1, le=50)):
    """
    Get most frequently observed TTPs (MITRE ATT&CK techniques).
    
    Args:
        limit: Maximum number of TTPs to return (1-50)
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        ttps = await db.get_top_ttps(limit)
        
        return TTPListResponse(
            ttps=ttps,
            total=len(ttps),
            limit=limit
        )
    
    except Exception as e:
        logger.error("get_top_ttps_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/honeypots/{honeypot_id}/restart")
async def restart_honeypot(honeypot_id: str):
    """
    Restart a specific honeypot (emergency action).
    
    Args:
        honeypot_id: Unique identifier of honeypot to restart
    
    Note: Requires admin privileges in production.
    """
    if not db or not docker_client:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        # Get honeypot from database
        honeypot = await db.get_honeypot_by_id(honeypot_id)
        if not honeypot:
            raise HTTPException(status_code=404, detail="Honeypot not found")
        
        # Restart Docker container
        container = docker_client.containers.get(honeypot.container_name)
        container.restart(timeout=10)
        
        logger.info(
            "honeypot_restarted",
            honeypot_id=honeypot_id,
            container_name=honeypot.container_name
        )
        
        # Update status in database
        await db.update_honeypot_status(
            honeypot_id,
            HoneypotStatus.DEGRADED,  # Will be updated by health check task
            datetime.utcnow()
        )
        
        return {
            "honeypot_id": honeypot_id,
            "action": "restart",
            "status": "success",
            "message": f"Container {honeypot.container_name} restarted"
        }
    
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("restart_honeypot_error", honeypot_id=honeypot_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# METRICS (Prometheus)
# ============================================================================

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Sprint 1 TODO:
    - Implement Prometheus client
    - Export metrics:
      - honeypot_connections_total
      - honeypot_attacks_detected
      - honeypot_ttps_extracted
      - honeypot_uptime_seconds
    """
    return {
        "status": "not_implemented",
        "message": "Sprint 1 feature - Prometheus metrics"
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8600,
        reload=True,
        log_level="info"
    )

# ============================================================================
# INTERNAL API (Used by Analysis Service)
# ============================================================================

@app.post("/api/v1/attacks", status_code=201)
async def create_attack(attack: AttackCreate):
    """
    Create a new attack record (internal endpoint for Analysis Service).
    
    Args:
        attack: AttackCreate model with attack details
    
    Returns:
        Created attack with ID
    """
    if not db or not kafka_producer:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        # Create attack in database
        created_attack = await db.create_attack(attack)
        if not created_attack:
            raise HTTPException(status_code=500, detail="Failed to create attack")
        
        logger.info(
            "attack_created",
            attack_id=str(created_attack.id),
            honeypot_id=str(attack.honeypot_id),
            attacker_ip=attack.attacker_ip,
            attack_type=attack.attack_type,
            severity=attack.severity.value
        )
        
        # Get honeypot info for Kafka message
        honeypot = await db.get_honeypot_by_id(str(attack.honeypot_id))
        honeypot_id_str = honeypot.honeypot_id if honeypot else str(attack.honeypot_id)
        
        # Publish to Kafka for immune system
        threat_msg = create_threat_detected_message(
            event_id=f"rf_attack_{created_attack.id}",
            honeypot_id=honeypot_id_str,
            attacker_ip=attack.attacker_ip,
            attack_type=attack.attack_type,
            severity=attack.severity.value,
            ttps=attack.ttps,
            iocs=attack.iocs,
            confidence=attack.confidence,
            metadata={"attack_db_id": str(created_attack.id)}
        )
        
        kafka_published = await kafka_producer.publish_threat_detected(threat_msg)
        
        if not kafka_published:
            logger.warning("kafka_publish_failed_but_attack_created", attack_id=str(created_attack.id))
        
        return {
            "id": str(created_attack.id),
            "honeypot_id": honeypot_id_str,
            "attacker_ip": created_attack.attacker_ip,
            "attack_type": created_attack.attack_type,
            "severity": created_attack.severity.value,
            "captured_at": created_attack.captured_at.isoformat(),
            "kafka_published": kafka_published
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_attack_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

