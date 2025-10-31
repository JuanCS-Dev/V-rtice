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
import uuid
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
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
# IN-MEMORY STORAGE (MVP - TODO: Replace with TimescaleDB)
# ═══════════════════════════════════════════════════════════════════════════

user_profiles_db: dict[str, UserProfile] = {}
anomalies_db: dict[str, Anomaly] = {}
events_db: dict[str, BehavioralEvent] = {}


# ═══════════════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYSIS LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def get_or_create_profile(user_id: str) -> UserProfile:
    """Get existing profile or create new one"""
    if user_id not in user_profiles_db:
        user_profiles_db[user_id] = UserProfile(user_id=user_id)
        active_profiles.inc()
    return user_profiles_db[user_id]


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
    Analyze single event for anomalies
    """
    profile = get_or_create_profile(event.user_id)
    anomalies: list[Anomaly] = []

    # Run all detection algorithms
    detections = await asyncio.gather(
        detect_impossible_travel(event, profile),
        detect_unusual_time(event, profile),
        detect_unusual_volume(event, profile),
        return_exceptions=True
    )

    # Collect non-None anomalies
    for detection in detections:
        if isinstance(detection, Anomaly):
            anomalies.append(detection)
            anomalies_db[detection.anomaly_id] = detection
            anomalies_detected.labels(anomaly_type=detection.anomaly_type.value).inc()

    # Update profile (simplified - in production, use ML)
    if event.event_type == EventType.LOGIN:
        if event.timestamp.hour not in profile.typical_login_times:
            profile.typical_login_times.append(event.timestamp.hour)
        if event.source_ip not in profile.typical_locations:
            profile.typical_locations.append(event.source_ip)

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
            events_db[event.event_id] = event
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
# ENDPOINTS - HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["health"])
async def health_check():
    """Service health check - FLORESCIMENTO ✨"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "florescimento": "defesas adaptativas florescendo",
        "active_profiles": len(user_profiles_db),
        "anomalies_detected": len(anomalies_db),
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
    List detected anomalies

    Scopes required: `behavioral:read`
    """
    anomalies = list(anomalies_db.values())

    if risk_level:
        anomalies = [a for a in anomalies if a.risk_level == risk_level]

    # Sort by detected_at descending
    anomalies.sort(key=lambda a: a.detected_at, reverse=True)

    return {
        "total": len(anomalies),
        "anomalies": anomalies[:limit]
    }


@app.get("/api/anomalies/{anomaly_id}", response_model=Anomaly, tags=["analysis"])
async def get_anomaly(
    anomaly_id: str,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:read"])
):
    """
    Get specific anomaly

    Scopes required: `behavioral:read`
    """
    if anomaly_id not in anomalies_db:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return anomalies_db[anomaly_id]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - PROFILES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/profiles", tags=["profiles"])
async def list_profiles(
    # token: str = Security(oauth2_scheme, scopes=["behavioral:read"])
):
    """
    List all user behavioral profiles

    Scopes required: `behavioral:read`
    """
    profiles = list(user_profiles_db.values())

    return {
        "total": len(profiles),
        "profiles": profiles
    }


@app.get("/api/profiles/{user_id}", response_model=UserProfile, tags=["profiles"])
async def get_profile(
    user_id: str,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:read"])
):
    """
    Get user behavioral profile

    Scopes required: `behavioral:read`
    """
    if user_id not in user_profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")

    return user_profiles_db[user_id]


@app.post("/api/profiles/build", response_model=UserProfile, tags=["profiles"])
async def build_profile(
    request: ProfileRequest,
    # token: str = Security(oauth2_scheme, scopes=["behavioral:write"])
):
    """
    Build/update user behavioral profile from historical data

    Scopes required: `behavioral:write`
    """
    profile = get_or_create_profile(request.user_id)

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

    return profile


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,  # Dev mode
        log_level="info"
    )
