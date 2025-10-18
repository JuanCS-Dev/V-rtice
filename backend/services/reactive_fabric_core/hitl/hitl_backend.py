"""
HITL Console Backend
FastAPI-based Human-in-the-Loop decision system with JWT + 2FA
"""

import asyncio
import logging
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp

logger = logging.getLogger(__name__)
import os

# Security Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class DecisionStatus(str, Enum):
    """Decision workflow status"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class DecisionPriority(str, Enum):
    """Decision priority levels"""
    CRITICAL = "critical"  # APT, nation-state
    HIGH = "high"          # Targeted attacks
    MEDIUM = "medium"      # Opportunistic
    LOW = "low"            # Noise


class ActionType(str, Enum):
    """Available response actions"""
    BLOCK_IP = "block_ip"
    QUARANTINE_SYSTEM = "quarantine_system"
    ACTIVATE_KILLSWITCH = "activate_killswitch"
    DEPLOY_COUNTERMEASURE = "deploy_countermeasure"
    ESCALATE_TO_SOC = "escalate_to_soc"
    NO_ACTION = "no_action"
    CUSTOM = "custom"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserCreate(BaseModel):
    """User registration model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole = UserRole.ANALYST


class UserInDB(BaseModel):
    """User database model"""
    username: str
    email: str
    full_name: str
    role: UserRole
    hashed_password: str
    is_active: bool = True
    is_2fa_enabled: bool = False
    totp_secret: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None


class TwoFactorSetup(BaseModel):
    """2FA setup response"""
    secret: str
    qr_code_url: str
    backup_codes: List[str]


class DecisionRequest(BaseModel):
    """Decision request from CANDI"""
    analysis_id: str
    incident_id: Optional[str]
    threat_level: str
    source_ip: str
    attributed_actor: Optional[str]
    confidence: float
    iocs: List[str]
    ttps: List[str]
    recommended_actions: List[str]
    forensic_summary: str
    priority: DecisionPriority
    created_at: datetime


class DecisionResponse(BaseModel):
    """Human decision response"""
    decision_id: str
    status: DecisionStatus
    approved_actions: List[ActionType]
    notes: str
    decided_by: str
    decided_at: datetime
    escalation_reason: Optional[str] = None


class DecisionCreate(BaseModel):
    """Create decision response"""
    decision_id: str
    status: DecisionStatus
    approved_actions: List[ActionType]
    notes: str
    escalation_reason: Optional[str] = None


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="HITL Console API",
    description="Human-in-the-Loop Decision System for Reactive Fabric",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# IN-MEMORY STORAGE (Replace with DB in production)
# ============================================================================

class HITLDatabase:
    """In-memory database for HITL system"""

    def __init__(self):
        self.users: Dict[str, UserInDB] = {}
        self.decisions: Dict[str, DecisionRequest] = {}
        self.responses: Dict[str, DecisionResponse] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []

        # Create default admin user
        self._create_default_admin()

    def _create_default_admin(self):
        """Create default admin user for initial setup"""
        admin = UserInDB(
            username="admin",
            email="admin@reactive-fabric.local",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            hashed_password=pwd_context.hash("ChangeMe123!"),
            is_active=True,
            is_2fa_enabled=False,
            created_at=datetime.now()
        )
        self.users["admin"] = admin
        logger.info("Default admin user created (username: admin, password: ChangeMe123!)")

    def add_user(self, user: UserInDB):
        """Add user to database"""
        self.users[user.username] = user

    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        return self.users.get(username)

    def add_decision(self, decision: DecisionRequest):
        """Add decision request"""
        self.decisions[decision.analysis_id] = decision

    def get_decision(self, analysis_id: str) -> Optional[DecisionRequest]:
        """Get decision request"""
        return self.decisions.get(analysis_id)

    def add_response(self, response: DecisionResponse):
        """Add decision response"""
        self.responses[response.decision_id] = response

    def get_pending_decisions(self, priority: Optional[DecisionPriority] = None) -> List[DecisionRequest]:
        """Get pending decisions"""
        pending = [
            d for d in self.decisions.values()
            if d.analysis_id not in self.responses
        ]

        if priority:
            pending = [d for d in pending if d.priority == priority]

        # Sort by priority and timestamp
        priority_order = {
            DecisionPriority.CRITICAL: 0,
            DecisionPriority.HIGH: 1,
            DecisionPriority.MEDIUM: 2,
            DecisionPriority.LOW: 3
        }
        pending.sort(key=lambda x: (priority_order[x.priority], x.created_at))

        return pending

    def audit(self, event: str, user: str, details: Dict[str, Any]):
        """Add audit log entry"""
        self.audit_log.append({
            "timestamp": datetime.now(),
            "event": event,
            "user": user,
            "details": details
        })


# Initialize database
db = HITLDatabase()


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, role=payload.get("role"))

    except JWTError:
        raise credentials_exception

    user = db.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_active_analyst(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Require analyst or admin role"""
    if current_user.role not in [UserRole.ANALYST, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


async def get_current_admin(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register", response_model=Dict[str, str])
async def register_user(
    user_data: UserCreate,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Register new user (admin only)

    Args:
        user_data: User registration data
        current_admin: Current admin user

    Returns:
        Success message with username
    """
    # Check if user already exists
    if db.get_user(user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create new user
    new_user = UserInDB(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        created_at=datetime.now()
    )

    db.add_user(new_user)

    # Audit log
    db.audit("USER_CREATED", current_admin.username, {
        "new_user": user_data.username,
        "role": user_data.role.value
    })

    logger.info(f"User registered: {user_data.username} (role: {user_data.role.value})")

    return {
        "message": "User registered successfully",
        "username": user_data.username
    }


@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login and get JWT tokens

    Args:
        form_data: OAuth2 form with username and password

    Returns:
        JWT access and refresh tokens
    """
    user = db.get_user(form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        db.audit("LOGIN_FAILED", form_data.username, {"reason": "invalid_credentials"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Check if 2FA is enabled
    if user.is_2fa_enabled:
        # Return temporary token that requires 2FA
        temp_token = create_access_token(
            data={"sub": user.username, "role": user.role.value, "requires_2fa": True},
            expires_delta=timedelta(minutes=5)
        )
        return Token(
            access_token=temp_token,
            refresh_token="",
            requires_2fa=True
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )

    # Update last login
    user.last_login = datetime.now()

    # Audit log
    db.audit("LOGIN_SUCCESS", user.username, {"ip": "unknown"})

    logger.info(f"User logged in: {user.username}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@app.post("/api/auth/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(current_user: UserInDB = Depends(get_current_user)):
    """
    Setup 2FA for user

    Args:
        current_user: Current authenticated user

    Returns:
        TOTP secret and QR code URL
    """
    # Generate TOTP secret
    secret = pyotp.random_base32()

    # Create QR code URL
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Reactive Fabric HITL"
    )

    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

    # Store secret (in production, hash backup codes)
    current_user.totp_secret = secret
    current_user.is_2fa_enabled = False  # Will be enabled after verification

    # Audit log
    db.audit("2FA_SETUP", current_user.username, {"status": "initiated"})

    logger.info(f"2FA setup initiated for user: {current_user.username}")

    return TwoFactorSetup(
        secret=secret,
        qr_code_url=qr_url,
        backup_codes=backup_codes
    )


@app.post("/api/auth/2fa/verify")
async def verify_2fa(
    code: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Verify 2FA code

    Args:
        code: 6-digit TOTP code
        current_user: Current user

    Returns:
        Success message
    """
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not set up")

    totp = pyotp.TOTP(current_user.totp_secret)

    if not totp.verify(code, valid_window=1):
        db.audit("2FA_VERIFY_FAILED", current_user.username, {"reason": "invalid_code"})
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    # Enable 2FA
    current_user.is_2fa_enabled = True

    # Audit log
    db.audit("2FA_ENABLED", current_user.username, {})

    logger.info(f"2FA enabled for user: {current_user.username}")

    return {"message": "2FA verified and enabled"}


@app.get("/api/auth/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """
    Get current user info

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_2fa_enabled": current_user.is_2fa_enabled,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "HITL Console Backend"
    }


@app.get("/api/status")
async def get_status(current_user: UserInDB = Depends(get_current_user)):
    """
    Get system status

    Args:
        current_user: Current authenticated user

    Returns:
        System status information
    """
    pending_decisions = db.get_pending_decisions()

    return {
        "timestamp": datetime.now().isoformat(),
        "pending_decisions": len(pending_decisions),
        "critical_pending": len([d for d in pending_decisions if d.priority == DecisionPriority.CRITICAL]),
        "total_users": len(db.users),
        "total_decisions": len(db.decisions),
        "total_responses": len(db.responses)
    }


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("=" * 60)
    logger.info("HITL Console Backend Starting...")
    logger.info("=" * 60)
    logger.info("Default Admin: username='admin', password='ChangeMe123!'")
    logger.info("API Docs: http://localhost:8000/api/docs")
    logger.info("=" * 60)


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

try:
    from .websocket_manager import manager, heartbeat_task, AlertType
except ImportError:
    from websocket_manager import manager, heartbeat_task, AlertType

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """
    WebSocket endpoint for real-time alerts

    Args:
        websocket: WebSocket connection
        username: Username for authentication
    """
    # JWT token validation
    try:
        # Extract token from query params or headers
        token = None
        if hasattr(websocket, 'query_params'):
            token = websocket.query_params.get('token')
        
        if token:
            # Validate JWT token
            import jwt
            
            secret_key = os.getenv("JWT_SECRET_KEY", "vertice-secret-key")
            
            try:
                payload = jwt.decode(token, secret_key, algorithms=["HS256"])
                
                # Verify username matches token
                if payload.get('username') != username:
                    await websocket.close(code=1008, reason="Username mismatch")
                    return
                    
                logger.info(f"JWT validated for user: {username}")
                
            except jwt.ExpiredSignatureError:
                await websocket.close(code=1008, reason="Token expired")
                return
            except jwt.InvalidTokenError:
                await websocket.close(code=1008, reason="Invalid token")
                return
        else:
            logger.warning(f"No JWT token provided for {username}, allowing in dev mode")
    
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
    
    await manager.connect(websocket, username)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle subscription changes
            if data.get("type") == "subscribe":
                alert_types = {AlertType(t) for t in data.get("alert_types", [])}
                manager.subscribe(username, alert_types)

                await manager.send_personal_message(
                    {"type": "subscribed", "alert_types": [t.value for t in alert_types]},
                    websocket
                )

            elif data.get("type") == "unsubscribe":
                alert_types = {AlertType(t) for t in data.get("alert_types", [])}
                manager.unsubscribe(username, alert_types)

                await manager.send_personal_message(
                    {"type": "unsubscribed", "alert_types": [t.value for t in alert_types]},
                    websocket
                )

            elif data.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()},
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: {username}")


@app.get("/api/ws/stats")
async def get_websocket_stats(current_user: UserInDB = Depends(get_current_user)):
    """
    Get WebSocket connection statistics

    Args:
        current_user: Current authenticated user

    Returns:
        WebSocket statistics
    """
    return manager.get_stats()


# ============================================================================
# DECISION MANAGEMENT ENDPOINTS
# ============================================================================

from fastapi import Query

class DecisionStats(BaseModel):
    """Decision statistics"""
    total_pending: int
    critical_pending: int
    high_pending: int
    medium_pending: int
    low_pending: int
    total_completed: int
    avg_response_time_minutes: float
    decisions_last_24h: int


@app.post("/api/decisions/submit", response_model=Dict[str, str])
async def submit_decision_request(
    decision: DecisionRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Submit new decision request (from CANDI)"""
    # Check if decision already exists
    existing = db.get_decision(decision.analysis_id)
    if existing:
        raise HTTPException(status_code=400, detail="Decision already exists")

    # Add to queue
    db.add_decision(decision)

    # Audit log
    db.audit("DECISION_SUBMITTED", current_user.username, {
        "analysis_id": decision.analysis_id,
        "priority": decision.priority.value,
        "threat_level": decision.threat_level
    })

    logger.info(
        f"Decision submitted: {decision.analysis_id} "
        f"(priority: {decision.priority.value}, threat: {decision.threat_level})"
    )

    return {
        "message": "Decision request submitted successfully",
        "analysis_id": decision.analysis_id
    }


@app.get("/api/decisions/pending", response_model=List[DecisionRequest])
async def get_pending_decisions(
    priority: Optional[DecisionPriority] = None,
    limit: int = Query(50, le=100),
    current_analyst: UserInDB = Depends(get_current_active_analyst)
):
    """Get pending decisions"""
    pending = db.get_pending_decisions(priority)
    return pending[:limit]


@app.get("/api/decisions/{analysis_id}", response_model=DecisionRequest)
async def get_decision(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get specific decision request"""
    decision = db.get_decision(analysis_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@app.post("/api/decisions/{analysis_id}/decide", response_model=DecisionResponse)
async def make_decision(
    analysis_id: str,
    decision_data: DecisionCreate,
    current_analyst: UserInDB = Depends(get_current_active_analyst)
):
    """Make decision on request"""
    # Get decision request
    request = db.get_decision(analysis_id)
    if not request:
        raise HTTPException(status_code=404, detail="Decision request not found")

    # Check if already decided
    if analysis_id in db.responses:
        raise HTTPException(status_code=400, detail="Decision already made")

    # Validate escalation
    if decision_data.status == DecisionStatus.ESCALATED:
        if not decision_data.escalation_reason:
            raise HTTPException(status_code=400, detail="Escalation reason required")

    # Create response
    response = DecisionResponse(
        decision_id=analysis_id,
        status=decision_data.status,
        approved_actions=decision_data.approved_actions,
        notes=decision_data.notes,
        decided_by=current_analyst.username,
        decided_at=datetime.now(),
        escalation_reason=decision_data.escalation_reason
    )

    db.add_response(response)

    # Audit log
    db.audit("DECISION_MADE", current_analyst.username, {
        "analysis_id": analysis_id,
        "status": decision_data.status.value,
        "actions": [a.value for a in decision_data.approved_actions]
    })

    logger.info(
        f"Decision made on {analysis_id} by {current_analyst.username}: "
        f"{decision_data.status.value}"
    )

    return response


@app.get("/api/decisions/{analysis_id}/response", response_model=DecisionResponse)
async def get_decision_response(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get decision response"""
    response = db.responses.get(analysis_id)
    if not response:
        raise HTTPException(status_code=404, detail="Decision response not found")
    return response


@app.get("/api/decisions/stats/summary", response_model=DecisionStats)
async def get_decision_stats(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get decision statistics"""
    pending = db.get_pending_decisions()

    # Count by priority
    critical = len([d for d in pending if d.priority == DecisionPriority.CRITICAL])
    high = len([d for d in pending if d.priority == DecisionPriority.HIGH])
    medium = len([d for d in pending if d.priority == DecisionPriority.MEDIUM])
    low = len([d for d in pending if d.priority == DecisionPriority.LOW])

    # Calculate response time (simplified)
    completed = db.responses.values()
    if completed:
        response_times = []
        for response in completed:
            request = db.get_decision(response.decision_id)
            if request:
                delta = (response.decided_at - request.created_at).total_seconds() / 60
                response_times.append(delta)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
    else:
        avg_response_time = 0.0

    # Decisions in last 24h
    cutoff = datetime.now() - timedelta(hours=24)
    recent = len([d for d in db.decisions.values() if d.created_at > cutoff])

    return DecisionStats(
        total_pending=len(pending),
        critical_pending=critical,
        high_pending=high,
        medium_pending=medium,
        low_pending=low,
        total_completed=len(db.responses),
        avg_response_time_minutes=avg_response_time,
        decisions_last_24h=recent
    )


@app.post("/api/decisions/{analysis_id}/escalate", response_model=DecisionResponse)
async def escalate_decision(
    analysis_id: str,
    escalation_reason: str,
    current_analyst: UserInDB = Depends(get_current_active_analyst)
):
    """Escalate decision to higher authority"""
    request = db.get_decision(analysis_id)
    if not request:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Create escalation response
    response = DecisionResponse(
        decision_id=analysis_id,
        status=DecisionStatus.ESCALATED,
        approved_actions=[],
        notes=f"Escalated by {current_analyst.username}",
        decided_by=current_analyst.username,
        decided_at=datetime.now(),
        escalation_reason=escalation_reason
    )

    db.add_response(response)

    # Audit log
    db.audit("DECISION_ESCALATED", current_analyst.username, {
        "analysis_id": analysis_id,
        "reason": escalation_reason
    })

    logger.warning(f"Decision escalated: {analysis_id} - {escalation_reason}")

    return response


# ============================================================================
# STARTUP TASKS
# ============================================================================

@app.on_event("startup")
async def start_background_tasks():
    """Start background tasks"""
    # Start heartbeat task
    asyncio.create_task(heartbeat_task())
    logger.info("Background tasks started")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("HITL_PORT", "8002"))  # Default port 8002 (avoid conflicts)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
