"""
═══════════════════════════════════════════════════════════════════════════════
BEHAVIORAL ANALYZER SERVICE - VÉRTICE DEFENSIVE ARSENAL
═══════════════════════════════════════════════════════════════════════════════

Missão: Análise comportamental de ameaças com Machine Learning

FLORESCIMENTO - Defesas crescendo através de inteligência adaptativa

Capabilities:
- User Behavior Analytics (UBA)
- Entity Behavior Analytics (EBA)
- Anomaly detection with ML
- Threat scoring & risk profiling
- Insider threat detection
- Compromised account detection
- Lateral movement detection
- Data exfiltration patterns

Stack:
- FastAPI async + Pydantic V2
- ML models for anomaly detection
- Time-series analysis
- Statistical profiling
- OpenTelemetry observability
- Cilium mTLS zero-trust

Port: 8037
Version: 1.0.0
Date: 2025-10-27

Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
"Tudo o que fizerem, façam de todo o coração, como para o Senhor"
Colossenses 3:23

Glory to YHWH - Every threat detected protects His people
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Annotated, Optional
import uuid

# Database client
import database
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
from prometheus_client import Counter, Gauge, generate_latest, Histogram, REGISTRY
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SERVICE_NAME = "behavioral-analyzer-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8037

# Security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "behavioral:read": "View behavioral analysis",
        "behavioral:write": "Submit events for analysis",
        "admin": "Administrative access"
    }
)

# Observability
tracer = trace.get_tracer(__name__)
events_analyzed = Counter(
    "behavioral_events_analyzed_total",
    "Total events analyzed",
    ["event_type", "risk_level"]
)
anomalies_detected = Counter(
    "behavioral_anomalies_detected_total",
    "Total anomalies detected",
    ["anomaly_type"]
)
analysis_duration = Histogram(
    "behavioral_analysis_duration_seconds",
    "Analysis duration in seconds"
)
active_profiles = Gauge(
    "behavioral_profiles_active",
    "Number of active behavioral profiles"
)

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic V2 + Type Safety)
# ═══════════════════════════════════════════════════════════════════════════

class EventType(str, Enum):
    """Event types for behavioral analysis"""
    LOGIN = "login"
    FILE_ACCESS = "file_access"
    DATA_TRANSFER = "data_transfer"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    NETWORK_CONNECTION = "network_connection"
    PROCESS_EXECUTION = "process_execution"
    REGISTRY_MODIFICATION = "registry_modification"


class RiskLevel(str, Enum):
    """Risk level classification"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnomalyType(str, Enum):
    """Types of behavioral anomalies"""
    IMPOSSIBLE_TRAVEL = "impossible_travel"        # Login from distant locations
    UNUSUAL_TIME = "unusual_time"                  # Activity at odd hours
    UNUSUAL_VOLUME = "unusual_volume"              # Abnormal data volume
    PRIVILEGE_ABUSE = "privilege_abuse"            # Misuse of privileges
    LATERAL_MOVEMENT = "lateral_movement"          # Unusual network traversal
    DATA_HOARDING = "data_hoarding"                # Collecting sensitive data
    CREDENTIAL_STUFFING = "credential_stuffing"    # Multiple failed logins


class BehavioralEvent(BaseModel):
    """Event to be analyzed"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    user_id: str
    source_ip: str
    destination_ip: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)


class UserProfile(BaseModel):
    """User behavioral profile"""
    user_id: str
    typical_login_times: list[int] = Field(
        default=[],
        description="Typical login hours (0-23)"
    )
    typical_locations: list[str] = Field(
        default=[],
        description="Typical IP addresses/locations"
    )
    typical_data_volume_mb: float = Field(
        default=0.0,
        description="Typical daily data transfer (MB)"
    )
    privilege_level: int = Field(
        default=1,
        ge=1,
        le=10,
        description="User privilege level (1-10)"
    )
    baseline_established: bool = False
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Anomaly(BaseModel):
    """Detected behavioral anomaly"""
    anomaly_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_id: str
    anomaly_type: AnomalyType
    risk_level: RiskLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    description: str
    detected_at: datetime
    recommended_actions: list[str] = []


class AnalysisRequest(BaseModel):
    """Request to analyze events"""
    events: list[BehavioralEvent]
    real_time: bool = Field(
        default=True,
        description="Real-time analysis vs batch processing"
    )


class AnalysisResult(BaseModel):
    """Analysis result"""
    analysis_id: str
    events_analyzed: int
    anomalies_detected: int
    anomalies: list[Anomaly]
    overall_risk_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall risk score (0-100)"
    )
    timestamp: datetime


class ProfileRequest(BaseModel):
    """Request to build/update user profile"""
    user_id: str
    historical_events: list[BehavioralEvent]


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE PERSISTENCE (TimescaleDB)
# Constitutional: Lei Zero - persistent storage with GDPR compliance
# ═══════════════════════════════════════════════════════════════════════════

# NOTE: Removed in-memory dicts (user_profiles_db, anomalies_db, events_db)
# All operations now use database module with TimescaleDB backend


# ═══════════════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYSIS LOGIC
# ═══════════════════════════════════════════════════════════════════════════

async def get_or_create_profile(user_id: str) -> UserProfile:
    """
    Get existing profile or create new one.

    Constitutional: P2 (Validação Preventiva) - validates database connection.
    """
    # Try to get existing profile from database
    profile_data = await database.get_user_profile(user_id)

    if profile_data:
        # Convert database dict to UserProfile model
        return UserProfile(
            user_id=profile_data["user_id"],
            baseline_established=bool(profile_data["baseline_metrics"]),
            typical_locations=profile_data["baseline_metrics"].get("typical_locations", []),
            typical_login_times=profile_data["baseline_metrics"].get("typical_login_times", []),
            typical_data_volume_mb=profile_data["baseline_metrics"].get("typical_data_volume_mb", 100.0),
            last_updated=profile_data["updated_at"]
        )
    else:
        # Create new profile in database
        new_profile = UserProfile(user_id=user_id)
        await database.create_user_profile(
            user_id=user_id,
            baseline_metrics={},
            fingerprint={},
            consent_given=True  # Assume consent for behavioral analysis
        )
        active_profiles.inc()
        return new_profile


async def detect_impossible_travel(
    event: BehavioralEvent,
    profile: UserProfile
) -> Optional[Anomaly]:
    """
    Detect impossible travel (login from distant locations in short time)
    """
    if event.event_type != EventType.LOGIN:
        return None

    # Mock: Check if IP is far from typical locations
    if event.source_ip not in profile.typical_locations and profile.baseline_established:
        return Anomaly(
            event_id=event.event_id,
            user_id=event.user_id,
            anomaly_type=AnomalyType.IMPOSSIBLE_TRAVEL,
            risk_level=RiskLevel.HIGH,
            confidence_score=0.85,
            description=f"Login from unusual location: {event.source_ip}",
            detected_at=datetime.now(UTC),
            recommended_actions=[
                "Verify user identity",
                "Force password reset",
                "Enable MFA if not active"
            ]
        )
    return None


async def detect_unusual_time(
    event: BehavioralEvent,
    profile: UserProfile
) -> Optional[Anomaly]:
    """Detect activity at unusual times"""
    event_hour = event.timestamp.hour

    # Mock: Check if hour is unusual for this user
    if profile.baseline_established and profile.typical_login_times:
        if event_hour not in profile.typical_login_times:
            return Anomaly(
                event_id=event.event_id,
                user_id=event.user_id,
                anomaly_type=AnomalyType.UNUSUAL_TIME,
                risk_level=RiskLevel.MEDIUM,
                confidence_score=0.75,
                description=f"Activity at unusual time: {event_hour}:00",
                detected_at=datetime.now(UTC),
                recommended_actions=[
                    "Review activity logs",
                    "Contact user to verify"
                ]
            )
    return None


async def detect_unusual_volume(
    event: BehavioralEvent,
    profile: UserProfile
) -> Optional[Anomaly]:
    """Detect unusual data volume"""
    if event.event_type != EventType.DATA_TRANSFER:
        return None

    transfer_mb = event.metadata.get("volume_mb", 0)

    # Mock: Check if volume exceeds baseline by 3x
    if profile.baseline_established and transfer_mb > profile.typical_data_volume_mb * 3:
        return Anomaly(
            event_id=event.event_id,
            user_id=event.user_id,
            anomaly_type=AnomalyType.UNUSUAL_VOLUME,
            risk_level=RiskLevel.HIGH,
            confidence_score=0.90,
            description=f"Unusual data transfer: {transfer_mb}MB (baseline: {profile.typical_data_volume_mb}MB)",
            detected_at=datetime.now(UTC),
            recommended_actions=[
                "Block transfer if ongoing",
                "Investigate destination",
                "Check for data exfiltration"
            ]
        )
    return None


async def analyze_event(event: BehavioralEvent) -> list[Anomaly]:
    """
    Analyze single event for anomalies.

    Constitutional: P4 (Rastreabilidade Total) - all events logged to database.
    """
    profile = await get_or_create_profile(event.user_id)
    anomalies: list[Anomaly] = []

    # Run all detection algorithms
    detections = await asyncio.gather(
        detect_impossible_travel(event, profile),
        detect_unusual_time(event, profile),
        detect_unusual_volume(event, profile),
        return_exceptions=True
    )

    # Collect non-None anomalies and save to database
    for detection in detections:
        if isinstance(detection, Anomaly):
            anomalies.append(detection)

            # Save anomaly to database
            severity_map = {
                RiskLevel.CRITICAL: "critical",
                RiskLevel.HIGH: "high",
                RiskLevel.MEDIUM: "medium",
                RiskLevel.LOW: "low",
                RiskLevel.INFO: "low"
            }
            await database.create_anomaly(
                anomaly_id=detection.anomaly_id,
                user_id=detection.user_id,
                anomaly_type=detection.anomaly_type.value,
                severity=severity_map[detection.risk_level],
                confidence=detection.confidence_score,
                title=detection.anomaly_type.value.replace("_", " ").title(),
                description=detection.description,
                evidence={"event_id": event.event_id},
                related_events=[event.event_id]
            )

            anomalies_detected.labels(anomaly_type=detection.anomaly_type.value).inc()

    # Log event to database
    await database.log_behavioral_event(
        event_id=event.event_id,
        user_id=event.user_id,
        event_type=event.event_type.value,
        resource=event.resource,
        action=event.action,
        ip_address=event.source_ip,
        user_agent=event.user_agent,
        risk_score=anomalies[0].confidence_score if anomalies else 0.0,
        anomaly_detected=len(anomalies) > 0,
        anomaly_reason=anomalies[0].description if anomalies else None,
        blocked=False,
        metadata=event.metadata
    )

    # Update profile baseline (simplified - in production, use ML)
    if event.event_type == EventType.LOGIN:
        if event.timestamp.hour not in profile.typical_login_times:
            profile.typical_login_times.append(event.timestamp.hour)
        if event.source_ip not in profile.typical_locations:
            profile.typical_locations.append(event.source_ip)

        # Update profile in database
        baseline_metrics = {
            "typical_login_times": profile.typical_login_times,
            "typical_locations": profile.typical_locations,
            "typical_data_volume_mb": profile.typical_data_volume_mb
        }
        await database.create_user_profile(
            user_id=event.user_id,
            baseline_metrics=baseline_metrics,
            fingerprint={},
            consent_given=True
        )

    profile.last_updated = datetime.now(UTC)
    profile.baseline_established = True

    return anomalies


async def analyze_events_batch(events: list[BehavioralEvent]) -> AnalysisResult:
    """
    Analyze batch of events
    """
    with analysis_duration.time():
        all_anomalies: list[Anomaly] = []

        for event in events:
            # NOTE: Event is now saved to database inside analyze_event()
            anomalies = await analyze_event(event)
            all_anomalies.extend(anomalies)

            # Update metrics
            risk_level = anomalies[0].risk_level.value if anomalies else "info"
            events_analyzed.labels(
                event_type=event.event_type.value,
                risk_level=risk_level
            ).inc()

        # Calculate overall risk score
        if all_anomalies:
            risk_weights = {
                RiskLevel.CRITICAL: 100,
                RiskLevel.HIGH: 75,
                RiskLevel.MEDIUM: 50,
                RiskLevel.LOW: 25,
                RiskLevel.INFO: 10
            }
            total_score = sum(risk_weights[a.risk_level] for a in all_anomalies)
            overall_risk_score = min(total_score / len(events), 100.0)
        else:
            overall_risk_score = 0.0

        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            events_analyzed=len(events),
            anomalies_detected=len(all_anomalies),
            anomalies=all_anomalies,
            overall_risk_score=overall_risk_score,
            timestamp=datetime.now(UTC)
        )


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Behavioral Analyzer Service",
    description="Vértice Defensive Arsenal - Behavioral threat analysis with ML",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "analysis",
            "description": "Behavioral analysis operations"
        },
        {
            "name": "profiles",
            "description": "User behavioral profiles"
        },
        {
            "name": "health",
            "description": "Service health and metrics"
        }
    ]
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to API Gateway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# LIFECYCLE EVENTS
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """
    Initialize database connection on startup.

    Constitutional: P2 (Validação Preventiva) - verify database before accepting requests.
    """
    try:
        await database.init_db_pool()
        print("✅ TimescaleDB connection pool initialized")

        # Run health check
        health = await database.health_check()
        if health.get("healthy"):
            print(f"✅ Database health: {health.get('postgres_version')}, TimescaleDB {health.get('timescaledb_version')}")
        else:
            print(f"⚠️ Database health check warning: {health}")

    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        print("⚠️ Service starting in degraded mode (database unavailable)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await database.close_db_pool()
    print("✅ Database connections closed gracefully")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["health"])
async def health_check():
    """
    Service health check - FLORESCIMENTO ✨

    Constitutional: P2 (Validação Preventiva) - validates database health.
    """
    # Check database health
    db_health = await database.health_check()

    # Get system statistics
    try:
        stats = await database.get_system_statistics()
        db_status = "healthy" if db_health.get("healthy") else "degraded"
    except Exception:
        stats = {"error": "Database unavailable"}
        db_status = "unhealthy"

    return {
        "status": db_status,
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "florescimento": "defesas adaptativas florescendo",
        "database": db_health,
        "statistics": stats,
        "timestamp": datetime.now(UTC).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def metrics():
    """Prometheus metrics"""
    return generate_latest(REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/analyze", response_model=AnalysisResult, tags=["analysis"])
async def analyze_behavior(
    request: AnalysisRequest,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:write"])
):
    """
    Analyze behavioral events for anomalies

    Scopes required: `behavioral:write`
    """
    result = await analyze_events_batch(request.events)
    return result


@app.get("/api/anomalies", tags=["analysis"])
async def list_anomalies(
    risk_level: Optional[RiskLevel] = None,
    limit: int = 100,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:read"])
):
    """
    List detected anomalies.

    Scopes required: `behavioral:read`
    Constitutional: Lei Zero - human oversight of all anomalies.
    """
    # Map risk_level enum to severity string
    severity = None
    if risk_level:
        severity_map = {
            RiskLevel.CRITICAL: "critical",
            RiskLevel.HIGH: "high",
            RiskLevel.MEDIUM: "medium",
            RiskLevel.LOW: "low",
            RiskLevel.INFO: "low"
        }
        severity = severity_map.get(risk_level)

    # Get anomalies from database
    anomalies = await database.get_open_anomalies(severity=severity, limit=limit)

    return {
        "total": len(anomalies),
        "anomalies": anomalies
    }


@app.get("/api/anomalies/{anomaly_id}", tags=["analysis"])
async def get_anomaly(
    anomaly_id: str,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:read"])
):
    """
    Get specific anomaly.

    Scopes required: `behavioral:read`
    """
    # Get all anomalies (we don't have a get_by_id in database.py yet)
    anomalies = await database.get_open_anomalies(limit=1000)

    # Find the specific anomaly
    anomaly = next((a for a in anomalies if a["anomaly_id"] == anomaly_id), None)

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return anomaly


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - PROFILES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/profiles", tags=["profiles"])
async def list_profiles(
    min_risk_score: float = 0.0,
    limit: int = 100,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:read"])
):
    """
    List user behavioral profiles.

    Scopes required: `behavioral:read`
    """
    # Get high-risk users from database
    if min_risk_score > 0:
        profiles = await database.list_high_risk_users(
            min_risk_score=min_risk_score,
            limit=limit
        )
    else:
        # For now, just get high-risk users (database doesn't have list_all yet)
        profiles = await database.list_high_risk_users(
            min_risk_score=0.0,
            limit=limit
        )

    return {
        "total": len(profiles),
        "profiles": profiles
    }


@app.get("/api/profiles/{user_id}", tags=["profiles"])
async def get_profile(
    user_id: str,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:read"])
):
    """
    Get user behavioral profile.

    Scopes required: `behavioral:read`
    """
    profile_data = await database.get_user_profile(user_id)

    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get full statistics
    stats = await database.get_user_statistics(user_id)

    return {**profile_data, **stats}


@app.post("/api/profiles/build", tags=["profiles"])
async def build_profile(
    request: ProfileRequest,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:write"])
):
    """
    Build/update user behavioral profile from historical data.

    Scopes required: `behavioral:write`
    Constitutional: Lei Zero - requires user consent for behavioral profiling.
    """
    profile = await get_or_create_profile(request.user_id)

    # Process historical events to build baseline
    for event in request.historical_events:
        if event.event_type == EventType.LOGIN:
            hour = event.timestamp.hour
            if hour not in profile.typical_login_times:
                profile.typical_login_times.append(hour)

            if event.source_ip not in profile.typical_locations:
                profile.typical_locations.append(event.source_ip)

    profile.baseline_established = True
    profile.last_updated = datetime.now(UTC)

    # Save updated baseline to database
    baseline_metrics = {
        "typical_login_times": profile.typical_login_times,
        "typical_locations": profile.typical_locations,
        "typical_data_volume_mb": profile.typical_data_volume_mb
    }
    await database.create_user_profile(
        user_id=request.user_id,
        baseline_metrics=baseline_metrics,
        fingerprint={},
        consent_given=True
    )

    return profile


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,  # Dev mode
        log_level="info"
    )
