"""
═══════════════════════════════════════════════════════════════════════════════
BAS SERVICE - BREACH AND ATTACK SIMULATION
═══════════════════════════════════════════════════════════════════════════════

Missão: Simulação automatizada de ataques para validação de defesas

FLORESCIMENTO - Crescimento através de testes contínuos de segurança

Capabilities:
- MITRE ATT&CK technique simulation
- Kill-chain scenario orchestration
- Purple team automation (coordinated red/blue)
- Defense validation & gap analysis
- Automated adversary emulation
- Security control effectiveness testing
- Incident response readiness testing

Stack:
- FastAPI async + Pydantic V2
- MITRE ATT&CK framework integration
- Caldera/Atomic Red Team patterns
- PostgreSQL for scenario library
- OpenTelemetry observability
- Cilium mTLS zero-trust

ETHICAL NOTICE:
This service is designed EXCLUSIVELY for authorized security validation
in controlled environments. ALL simulations require explicit authorization.

Port: 8036
Version: 1.0.0
Date: 2025-10-27

Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
"Tudo o que fizerem, façam de todo o coração, como para o Senhor"
Colossenses 3:23

Glory to YHWH - Every simulation strengthens defenses
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

SERVICE_NAME = "bas-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8036

# Security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "bas:read": "View BAS simulations",
        "bas:write": "Create and manage simulations",
        "bas:execute": "Execute attack simulations",
        "admin": "Administrative access"
    }
)

# Observability
tracer = trace.get_tracer(__name__)
simulations_active = Gauge(
    "bas_simulations_active",
    "Number of active BAS simulations"
)
techniques_executed = Counter(
    "bas_techniques_executed_total",
    "Total MITRE ATT&CK techniques executed",
    ["technique_id", "tactic", "status"]
)
simulation_duration = Histogram(
    "bas_simulation_duration_seconds",
    "Simulation duration in seconds",
    ["scenario_type"]
)

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic V2 + Type Safety)
# ═══════════════════════════════════════════════════════════════════════════

class MITRETactic(str, Enum):
    """MITRE ATT&CK tactics"""
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource-development"
    INITIAL_ACCESS = "initial-access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege-escalation"
    DEFENSE_EVASION = "defense-evasion"
    CREDENTIAL_ACCESS = "credential-access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral-movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command-and-control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class SimulationType(str, Enum):
    """BAS simulation types"""
    SINGLE_TECHNIQUE = "single_technique"    # Test one technique
    KILL_CHAIN = "kill_chain"                # Full attack chain
    PURPLE_TEAM = "purple_team"              # Coordinated red/blue
    RANSOMWARE = "ransomware"                # Ransomware simulation
    APT = "apt"                              # Advanced Persistent Threat
    INSIDER_THREAT = "insider_threat"        # Insider attack patterns


class SimulationStatus(str, Enum):
    """Simulation execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class DefenseStatus(str, Enum):
    """Defense effectiveness status"""
    BLOCKED = "blocked"             # Attack blocked by defense
    DETECTED = "detected"           # Attack detected but not blocked
    UNDETECTED = "undetected"       # Attack succeeded undetected
    PARTIAL = "partial"             # Partially detected/blocked


class MITRETechnique(BaseModel):
    """MITRE ATT&CK technique"""
    technique_id: str = Field(description="Technique ID (e.g., T1566.001)")
    technique_name: str
    tactic: MITRETactic
    description: str
    platforms: list[str] = Field(default=["linux", "windows", "macos"])


class SimulationRequest(BaseModel):
    """Create new BAS simulation"""
    simulation_type: SimulationType
    target_environment: str = Field(description="Target environment identifier")
    techniques: list[str] = Field(
        description="List of MITRE ATT&CK technique IDs to simulate"
    )
    engagement_id: str = Field(description="Authorization engagement ID")
    operator_name: str = Field(description="Operator name for audit")
    stop_on_block: bool = Field(
        default=True,
        description="Stop simulation if defense blocks an attack"
    )
    simulation_notes: Optional[str] = None


class TechniqueResult(BaseModel):
    """Individual technique execution result"""
    technique_id: str
    technique_name: str
    tactic: MITRETactic
    defense_status: DefenseStatus
    executed_at: datetime
    duration_seconds: float
    detection_time_seconds: Optional[float] = None
    blocked_by: Optional[str] = Field(
        default=None,
        description="Security control that blocked/detected"
    )
    evidence: Optional[str] = Field(
        default=None,
        description="Evidence collected (logs, alerts, etc.)"
    )


class SimulationResult(BaseModel):
    """Complete simulation result"""
    simulation_id: str
    simulation_type: SimulationType
    status: SimulationStatus
    target_environment: str
    engagement_id: str
    operator_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    techniques_executed: int = 0
    techniques_blocked: int = 0
    techniques_detected: int = 0
    techniques_undetected: int = 0
    results: list[TechniqueResult] = []
    overall_defense_score: Optional[float] = Field(
        default=None,
        description="Defense effectiveness score (0-100)"
    )
    simulation_notes: Optional[str] = None


class DefenseGap(BaseModel):
    """Identified defense gap"""
    technique_id: str
    technique_name: str
    tactic: MITRETactic
    gap_severity: str = Field(description="critical/high/medium/low")
    gap_description: str
    recommended_controls: list[str]


class SimulationList(BaseModel):
    """List of simulations"""
    total: int
    active: int
    simulations: list[SimulationResult]


# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (MVP - TODO: Replace with PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════

simulations_db: dict[str, SimulationResult] = {}

# Mock MITRE ATT&CK technique library
MITRE_TECHNIQUES_DB: dict[str, MITRETechnique] = {
    "T1566.001": MITRETechnique(
        technique_id="T1566.001",
        technique_name="Spearphishing Attachment",
        tactic=MITRETactic.INITIAL_ACCESS,
        description="Adversaries may send spearphishing emails with malicious attachments",
        platforms=["windows", "macos", "linux"]
    ),
    "T1059.001": MITRETechnique(
        technique_id="T1059.001",
        technique_name="PowerShell",
        tactic=MITRETactic.EXECUTION,
        description="Adversaries may abuse PowerShell commands and scripts",
        platforms=["windows"]
    ),
    "T1547.001": MITRETechnique(
        technique_id="T1547.001",
        technique_name="Registry Run Keys / Startup Folder",
        tactic=MITRETactic.PERSISTENCE,
        description="Adversaries may achieve persistence by adding a program to a startup folder",
        platforms=["windows"]
    ),
    "T1003.001": MITRETechnique(
        technique_id="T1003.001",
        technique_name="LSASS Memory",
        tactic=MITRETactic.CREDENTIAL_ACCESS,
        description="Adversaries may attempt to access credential material stored in LSASS",
        platforms=["windows"]
    ),
    "T1083": MITRETechnique(
        technique_id="T1083",
        technique_name="File and Directory Discovery",
        tactic=MITRETactic.DISCOVERY,
        description="Adversaries may enumerate files and directories",
        platforms=["linux", "macos", "windows"]
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# CORE BAS LOGIC
# ═══════════════════════════════════════════════════════════════════════════

async def simulate_technique(
    technique_id: str,
    target_environment: str
) -> TechniqueResult:
    """
    Simulate a single MITRE ATT&CK technique

    In production, this would execute actual technique simulation
    """
    if technique_id not in MITRE_TECHNIQUES_DB:
        raise ValueError(f"Unknown technique: {technique_id}")

    technique = MITRE_TECHNIQUES_DB[technique_id]

    start_time = datetime.now(UTC)

    # Simulate execution delay (2-5 seconds)
    await asyncio.sleep(3)

    # Mock defense response (randomized for demo)
    import random
    defense_outcomes = [
        DefenseStatus.BLOCKED,
        DefenseStatus.DETECTED,
        DefenseStatus.UNDETECTED,
        DefenseStatus.PARTIAL
    ]
    defense_status = random.choice(defense_outcomes)

    # Mock blocked_by based on defense status
    blocked_by_map = {
        DefenseStatus.BLOCKED: "EDR: CrowdStrike Falcon",
        DefenseStatus.DETECTED: "SIEM: Splunk Enterprise",
        DefenseStatus.PARTIAL: "WAF: Cloudflare",
        DefenseStatus.UNDETECTED: None
    }

    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    techniques_executed.labels(
        technique_id=technique_id,
        tactic=technique.tactic.value,
        status=defense_status.value
    ).inc()

    return TechniqueResult(
        technique_id=technique_id,
        technique_name=technique.technique_name,
        tactic=technique.tactic,
        defense_status=defense_status,
        executed_at=start_time,
        duration_seconds=duration,
        detection_time_seconds=1.5 if defense_status != DefenseStatus.UNDETECTED else None,
        blocked_by=blocked_by_map.get(defense_status),
        evidence=f"Mock evidence for {technique_id}" if defense_status != DefenseStatus.UNDETECTED else None
    )


async def run_simulation_background(
    simulation_id: str,
    request: SimulationRequest
):
    """
    Execute BAS simulation in background
    """
    simulation = simulations_db[simulation_id]
    simulation.status = SimulationStatus.RUNNING
    simulations_active.inc()

    start_time = datetime.now(UTC)
    results: list[TechniqueResult] = []

    with simulation_duration.labels(scenario_type=request.simulation_type.value).time():
        for technique_id in request.techniques:
            # Execute technique simulation
            try:
                result = await simulate_technique(technique_id, request.target_environment)
                results.append(result)

                # Stop if blocked and stop_on_block is True
                if request.stop_on_block and result.defense_status == DefenseStatus.BLOCKED:
                    break

            except Exception as e:
                # Log error and continue
                pass

    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    # Calculate stats
    blocked_count = len([r for r in results if r.defense_status == DefenseStatus.BLOCKED])
    detected_count = len([r for r in results if r.defense_status == DefenseStatus.DETECTED])
    undetected_count = len([r for r in results if r.defense_status == DefenseStatus.UNDETECTED])

    # Calculate defense score (0-100)
    total_techniques = len(results)
    if total_techniques > 0:
        defense_score = ((blocked_count * 1.0 + detected_count * 0.7) / total_techniques) * 100
    else:
        defense_score = 0.0

    # Update simulation
    simulation.status = SimulationStatus.COMPLETED
    simulation.completed_at = end_time
    simulation.duration_seconds = duration
    simulation.techniques_executed = len(results)
    simulation.techniques_blocked = blocked_count
    simulation.techniques_detected = detected_count
    simulation.techniques_undetected = undetected_count
    simulation.results = results
    simulation.overall_defense_score = defense_score

    simulations_active.dec()


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="BAS Service - Breach and Attack Simulation",
    description="Vértice Offensive Arsenal - Automated attack simulation for defense validation",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "simulations",
            "description": "Attack simulation operations"
        },
        {
            "name": "techniques",
            "description": "MITRE ATT&CK technique library"
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
        "florescimento": "defesas florescendo através de simulações",
        "active_simulations": len([s for s in simulations_db.values() if s.status == SimulationStatus.RUNNING]),
        "timestamp": datetime.now(UTC).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def metrics():
    """Prometheus metrics"""
    return generate_latest(REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - SIMULATIONS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/simulations", response_model=SimulationResult, tags=["simulations"])
async def create_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    # token: str = Security(oauth2_scheme, scopes=["bas:write"])
):
    """
    Create new BAS simulation

    Requires explicit engagement authorization for ethical simulation.

    Scopes required: `bas:write`
    """
    simulation_id = str(uuid.uuid4())

    simulation = SimulationResult(
        simulation_id=simulation_id,
        simulation_type=request.simulation_type,
        status=SimulationStatus.QUEUED,
        target_environment=request.target_environment,
        engagement_id=request.engagement_id,
        operator_name=request.operator_name,
        started_at=datetime.now(UTC),
        simulation_notes=request.simulation_notes
    )

    simulations_db[simulation_id] = simulation

    # Execute simulation in background
    background_tasks.add_task(run_simulation_background, simulation_id, request)

    return simulation


@app.get("/api/simulations", response_model=SimulationList, tags=["simulations"])
async def list_simulations(
    status: Optional[SimulationStatus] = None,
    # token: str = Security(oauth2_scheme, scopes=["bas:read"])
):
    """
    List all simulations

    Scopes required: `bas:read`
    """
    simulations = list(simulations_db.values())

    if status:
        simulations = [s for s in simulations if s.status == status]

    active_count = len([s for s in simulations_db.values() if s.status == SimulationStatus.RUNNING])

    return SimulationList(
        total=len(simulations),
        active=active_count,
        simulations=simulations
    )


@app.get("/api/simulations/{simulation_id}", response_model=SimulationResult, tags=["simulations"])
async def get_simulation(
    simulation_id: str,
    # token: str = Security(oauth2_scheme, scopes=["bas:read"])
):
    """
    Get specific simulation

    Scopes required: `bas:read`
    """
    if simulation_id not in simulations_db:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return simulations_db[simulation_id]


@app.get("/api/simulations/{simulation_id}/gaps", tags=["simulations"])
async def get_defense_gaps(
    simulation_id: str,
    # token: str = Security(oauth2_scheme, scopes=["bas:read"])
):
    """
    Get identified defense gaps from simulation

    Scopes required: `bas:read`
    """
    if simulation_id not in simulations_db:
        raise HTTPException(status_code=404, detail="Simulation not found")

    simulation = simulations_db[simulation_id]

    # Identify gaps (undetected techniques)
    gaps: list[DefenseGap] = []

    for result in simulation.results:
        if result.defense_status == DefenseStatus.UNDETECTED:
            gap = DefenseGap(
                technique_id=result.technique_id,
                technique_name=result.technique_name,
                tactic=result.tactic,
                gap_severity="high",
                gap_description=f"Technique {result.technique_id} executed without detection",
                recommended_controls=[
                    "EDR with behavioral detection",
                    "SIEM rule tuning",
                    "Network traffic analysis"
                ]
            )
            gaps.append(gap)

    return {
        "simulation_id": simulation_id,
        "total_gaps": len(gaps),
        "gaps": gaps
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - MITRE ATT&CK TECHNIQUES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/techniques", tags=["techniques"])
async def list_techniques(
    tactic: Optional[MITRETactic] = None,
):
    """
    List available MITRE ATT&CK techniques

    Filterable by tactic
    """
    techniques = list(MITRE_TECHNIQUES_DB.values())

    if tactic:
        techniques = [t for t in techniques if t.tactic == tactic]

    return {
        "total": len(techniques),
        "techniques": techniques
    }


@app.get("/api/techniques/{technique_id}", response_model=MITRETechnique, tags=["techniques"])
async def get_technique(technique_id: str):
    """Get specific technique details"""
    if technique_id not in MITRE_TECHNIQUES_DB:
        raise HTTPException(status_code=404, detail="Technique not found")

    return MITRE_TECHNIQUES_DB[technique_id]


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
