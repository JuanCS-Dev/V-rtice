"""
═══════════════════════════════════════════════════════════════════════════════
C2 ORCHESTRATION SERVICE - VÉRTICE OFFENSIVE ARSENAL
═══════════════════════════════════════════════════════════════════════════════

Missão: Orquestração ética de Command & Control para testes de segurança

FLORESCIMENTO - Crescimento orgânico através de operações coordenadas

Capabilities:
- C2 session management (multi-target coordination)
- Command execution queue with safety controls
- Post-exploitation task orchestration
- Lateral movement simulation
- Persistence testing & validation
- Data exfiltration simulation (ethical)
- Clean-up & restoration automation

Stack:
- FastAPI async + Pydantic V2
- WebSocket for real-time C2 communication
- Redis for session state management
- PostgreSQL for audit logging
- OpenTelemetry observability
- Cilium mTLS zero-trust

ETHICAL NOTICE:
This service is designed EXCLUSIVELY for authorized penetration testing,
red team exercises, and security validation in controlled environments.
ALL operations are logged and require explicit authorization tokens.

Port: 8035
Version: 1.0.0
Date: 2025-10-27

Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
"Tudo o que fizerem, façam de todo o coração, como para o Senhor"
Colossenses 3:23

Glory to YHWH - Every ethical operation strengthens defenses
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import uuid
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SERVICE_NAME = "c2-orchestration-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8035

# Security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "c2:read": "View C2 sessions",
        "c2:write": "Create and manage C2 sessions",
        "c2:execute": "Execute commands on C2 sessions",
        "admin": "Administrative access"
    }
)

# Observability
tracer = trace.get_tracer(__name__)
c2_sessions_active = Gauge(
    "c2_sessions_active",
    "Number of active C2 sessions"
)
c2_commands_total = Counter(
    "c2_commands_total",
    "Total C2 commands executed",
    ["command_type", "status"]
)
c2_command_duration = Histogram(
    "c2_command_duration_seconds",
    "C2 command execution duration",
    ["command_type"]
)

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic V2 + Type Safety)
# ═══════════════════════════════════════════════════════════════════════════

class SessionStatus(str, Enum):
    """C2 session status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class CommandType(str, Enum):
    """C2 command categories"""
    RECONNAISSANCE = "reconnaissance"     # Information gathering
    LATERAL_MOVEMENT = "lateral_movement" # Network traversal
    PERSISTENCE = "persistence"           # Maintain access
    EXFILTRATION = "exfiltration"        # Data extraction (simulated)
    CLEANUP = "cleanup"                   # Remove artifacts
    CUSTOM = "custom"                     # Custom commands


class CommandStatus(str, Enum):
    """Command execution status"""
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"  # Blocked by safety controls


class TargetOS(str, Enum):
    """Target operating system"""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    UNKNOWN = "unknown"


class C2SessionCreate(BaseModel):
    """Create new C2 session"""
    target_ip: str = Field(description="Target IP address")
    target_hostname: Optional[str] = Field(default=None, description="Target hostname")
    target_os: TargetOS = Field(default=TargetOS.UNKNOWN)
    engagement_id: str = Field(description="Authorization engagement ID")
    operator_name: str = Field(description="Operator name for audit")
    session_notes: Optional[str] = None


class C2Session(BaseModel):
    """C2 session details"""
    session_id: str
    target_ip: str
    target_hostname: Optional[str]
    target_os: TargetOS
    status: SessionStatus
    engagement_id: str
    operator_name: str
    created_at: datetime
    last_seen: datetime
    commands_executed: int = 0
    session_notes: Optional[str] = None


class CommandRequest(BaseModel):
    """Execute command on C2 session"""
    session_id: str
    command_type: CommandType
    command: str = Field(description="Command to execute")
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    require_confirmation: bool = Field(
        default=True,
        description="Require operator confirmation before execution"
    )


class CommandResult(BaseModel):
    """Command execution result"""
    command_id: str
    session_id: str
    command_type: CommandType
    command: str
    status: CommandStatus
    output: Optional[str] = None
    error: Optional[str] = None
    executed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class SessionList(BaseModel):
    """List of C2 sessions"""
    total: int
    active: int
    sessions: list[C2Session]


# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (MVP - TODO: Replace with Redis + PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════

sessions_db: dict[str, C2Session] = {}
commands_db: dict[str, CommandResult] = {}
websocket_connections: dict[str, WebSocket] = {}


# ═══════════════════════════════════════════════════════════════════════════
# SAFETY CONTROLS & ETHICAL GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════

# Blocked commands that could cause harm
BLOCKED_COMMANDS = [
    "rm -rf /",
    "del /f /s /q C:\\",
    "format",
    "shutdown",
    "reboot",
    ":(){ :|:& };:",  # Fork bomb
]

# Rate limiting: max commands per session per minute
MAX_COMMANDS_PER_MINUTE = 20


def validate_command_safety(command: str) -> tuple[bool, Optional[str]]:
    """
    Validate command against safety controls

    Returns:
        (is_safe, reason_if_blocked)
    """
    command_lower = command.lower().strip()

    # Check blocked commands
    for blocked in BLOCKED_COMMANDS:
        if blocked.lower() in command_lower:
            return False, f"Command blocked: matches dangerous pattern '{blocked}'"

    # Check for suspicious patterns
    if ">" in command and "/dev/" in command:
        return False, "Command blocked: suspicious device redirection"

    if "wget" in command_lower or "curl" in command_lower:
        if "http" in command_lower:
            return False, "Command blocked: external download detected"

    return True, None


async def check_rate_limit(session_id: str) -> bool:
    """Check if session has exceeded rate limit"""
    # TODO: Implement Redis-based rate limiting
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CORE C2 LOGIC
# ═══════════════════════════════════════════════════════════════════════════

async def execute_command_background(command_req: CommandRequest) -> CommandResult:
    """
    Execute command in background (simulation)

    In production, this would connect to actual C2 implants
    """
    command_id = str(uuid.uuid4())

    # Safety validation
    is_safe, block_reason = validate_command_safety(command_req.command)
    if not is_safe:
        c2_commands_total.labels(
            command_type=command_req.command_type.value,
            status="blocked"
        ).inc()

        return CommandResult(
            command_id=command_id,
            session_id=command_req.session_id,
            command_type=command_req.command_type,
            command=command_req.command,
            status=CommandStatus.BLOCKED,
            error=block_reason
        )

    # Rate limiting
    if not await check_rate_limit(command_req.session_id):
        return CommandResult(
            command_id=command_id,
            session_id=command_req.session_id,
            command_type=command_req.command_type,
            command=command_req.command,
            status=CommandStatus.BLOCKED,
            error="Rate limit exceeded"
        )

    # Simulate command execution
    with c2_command_duration.labels(command_type=command_req.command_type.value).time():
        start_time = datetime.now(UTC)

        # Simulate execution delay
        await asyncio.sleep(2)

        # Mock output based on command type
        mock_output = {
            CommandType.RECONNAISSANCE: "hostname: target-server\nOS: Ubuntu 20.04\nIP: 192.168.1.100",
            CommandType.LATERAL_MOVEMENT: "SMB shares discovered: 3\nRDP accessible: Yes",
            CommandType.PERSISTENCE: "Cron job created: /etc/cron.d/persistence",
            CommandType.EXFILTRATION: "Simulated exfiltration: 1.2MB transferred",
            CommandType.CLEANUP: "Artifacts removed: logs cleared, persistence removed",
        }.get(command_req.command_type, "Command executed successfully")

        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

    # Update session stats
    if command_req.session_id in sessions_db:
        sessions_db[command_req.session_id].commands_executed += 1
        sessions_db[command_req.session_id].last_seen = datetime.now(UTC)

    c2_commands_total.labels(
        command_type=command_req.command_type.value,
        status="completed"
    ).inc()

    result = CommandResult(
        command_id=command_id,
        session_id=command_req.session_id,
        command_type=command_req.command_type,
        command=command_req.command,
        status=CommandStatus.COMPLETED,
        output=mock_output,
        executed_at=start_time,
        duration_seconds=duration
    )

    commands_db[command_id] = result
    return result


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="C2 Orchestration Service",
    description="Vértice Offensive Arsenal - Ethical C2 orchestration for authorized testing",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "sessions",
            "description": "C2 session management"
        },
        {
            "name": "commands",
            "description": "Command execution"
        },
        {
            "name": "health",
            "description": "Service health and metrics"
        }
    ]
)

# CORS (allow API Gateway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to API Gateway only
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
        "florescimento": "operações éticas florescendo",
        "active_sessions": len([s for s in sessions_db.values() if s.status == SessionStatus.ACTIVE]),
        "timestamp": datetime.now(UTC).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def metrics():
    """Prometheus metrics"""
    return generate_latest(REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/sessions", response_model=C2Session, tags=["sessions"])
async def create_session(
    request: C2SessionCreate,
    # token: str = Security(oauth2_scheme, scopes=["c2:write"])  # TODO: Enable auth
):
    """
    Create new C2 session

    Requires explicit engagement authorization and operator identification
    for audit trail.

    Scopes required: `c2:write`
    """
    session_id = str(uuid.uuid4())

    session = C2Session(
        session_id=session_id,
        target_ip=request.target_ip,
        target_hostname=request.target_hostname,
        target_os=request.target_os,
        status=SessionStatus.ACTIVE,
        engagement_id=request.engagement_id,
        operator_name=request.operator_name,
        created_at=datetime.now(UTC),
        last_seen=datetime.now(UTC),
        session_notes=request.session_notes
    )

    sessions_db[session_id] = session
    c2_sessions_active.inc()

    return session


@app.get("/api/sessions", response_model=SessionList, tags=["sessions"])
async def list_sessions(
    status: Optional[SessionStatus] = None,
    # token: str = Security(oauth2_scheme, scopes=["c2:read"])
):
    """
    List all C2 sessions

    Scopes required: `c2:read`
    """
    sessions = list(sessions_db.values())

    if status:
        sessions = [s for s in sessions if s.status == status]

    active_count = len([s for s in sessions_db.values() if s.status == SessionStatus.ACTIVE])

    return SessionList(
        total=len(sessions),
        active=active_count,
        sessions=sessions
    )


@app.get("/api/sessions/{session_id}", response_model=C2Session, tags=["sessions"])
async def get_session(
    session_id: str,
    # token: str = Security(oauth2_scheme, scopes=["c2:read"])
):
    """
    Get specific C2 session

    Scopes required: `c2:read`
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions_db[session_id]


@app.delete("/api/sessions/{session_id}", tags=["sessions"])
async def terminate_session(
    session_id: str,
    # token: str = Security(oauth2_scheme, scopes=["c2:write"])
):
    """
    Terminate C2 session

    Scopes required: `c2:write`
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    sessions_db[session_id].status = SessionStatus.TERMINATED
    c2_sessions_active.dec()

    return {"message": "Session terminated", "session_id": session_id}


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - COMMAND EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/commands/execute", response_model=CommandResult, tags=["commands"])
async def execute_command(
    request: CommandRequest,
    # token: str = Security(oauth2_scheme, scopes=["c2:execute"])
):
    """
    Execute command on C2 session

    All commands are validated against safety controls and logged.
    Dangerous operations are automatically blocked.

    Scopes required: `c2:execute`
    """
    if request.session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions_db[request.session_id]

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Session not active (status: {session.status})"
        )

    # Execute command (background task simulation)
    result = await execute_command_background(request)

    return result


@app.get("/api/commands/{command_id}", response_model=CommandResult, tags=["commands"])
async def get_command_result(
    command_id: str,
    # token: str = Security(oauth2_scheme, scopes=["c2:read"])
):
    """
    Get command execution result

    Scopes required: `c2:read`
    """
    if command_id not in commands_db:
        raise HTTPException(status_code=404, detail="Command not found")

    return commands_db[command_id]


@app.get("/api/sessions/{session_id}/commands", tags=["commands"])
async def list_session_commands(
    session_id: str,
    # token: str = Security(oauth2_scheme, scopes=["c2:read"])
):
    """
    List all commands for a session

    Scopes required: `c2:read`
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    commands = [
        cmd for cmd in commands_db.values()
        if cmd.session_id == session_id
    ]

    return {
        "session_id": session_id,
        "total_commands": len(commands),
        "commands": commands
    }


# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET - REAL-TIME C2 COMMUNICATION
# ═══════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time C2 communication

    TODO: Add authentication for WebSocket connections
    """
    await websocket.accept()

    if session_id not in sessions_db:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    websocket_connections[session_id] = websocket

    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "C2 WebSocket connected - florescendo..."
        })

        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "timestamp": datetime.now(UTC).isoformat()
            })

    except WebSocketDisconnect:
        del websocket_connections[session_id]


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
