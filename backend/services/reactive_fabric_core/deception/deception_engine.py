"""
Deception Engine for creating and managing deceptive elements.

This engine manages:
- Honeytokens: Fake credentials and tokens
- Decoy Systems: Fake services and endpoints
- Trap Documents: Documents with tracking capabilities
- Breadcrumb Trails: False paths for attackers

Phase 1: PASSIVE deception only - monitoring without active engagement
"""

import asyncio
import hashlib
import json
import logging
import secrets
import string
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DeceptionType(Enum):
    """Types of deception elements."""
    HONEYTOKEN = "honeytoken"
    DECOY_SYSTEM = "decoy_system"
    TRAP_DOCUMENT = "trap_document"
    BREADCRUMB = "breadcrumb"
    FAKE_DATA = "fake_data"


class TokenType(Enum):
    """Types of honeytokens."""
    API_KEY = "api_key"
    PASSWORD = "password"
    SSH_KEY = "ssh_key"
    DATABASE_CRED = "database_cred"
    AWS_KEY = "aws_key"
    OAUTH_TOKEN = "oauth_token"
    JWT = "jwt"
    COOKIE = "cookie"


class DeceptionConfig(BaseModel):
    """Configuration for Deception Engine."""

    # Honeytoken settings
    honeytoken_types: List[TokenType] = Field(
        default_factory=lambda: [
            TokenType.API_KEY,
            TokenType.PASSWORD,
            TokenType.DATABASE_CRED
        ],
        description="Types of honeytokens to generate"
    )
    honeytokens_per_type: int = Field(
        default=5, description="Number of honeytokens per type"
    )
    token_rotation_days: int = Field(
        default=30, description="Days before rotating honeytokens"
    )

    # Decoy settings
    max_decoy_systems: int = Field(
        default=10, description="Maximum number of decoy systems"
    )
    decoy_ports: List[int] = Field(
        default_factory=lambda: [22, 80, 443, 3306, 5432],
        description="Ports for decoy services"
    )

    # Trap document settings
    trap_document_types: List[str] = Field(
        default_factory=lambda: ["pdf", "docx", "xlsx", "txt"],
        description="Types of trap documents"
    )
    max_trap_documents: int = Field(
        default=20, description="Maximum trap documents"
    )

    # Monitoring settings
    alert_threshold: int = Field(
        default=1, description="Access count before alerting"
    )
    tracking_enabled: bool = Field(
        default=True, description="Enable access tracking"
    )


class Honeytoken(BaseModel):
    """Represents a honeytoken."""

    token_id: str = Field(default_factory=lambda: str(uuid4()))
    token_type: TokenType
    token_value: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    deployed_locations: List[str] = Field(default_factory=list)
    triggered: bool = False


class DecoySystem(BaseModel):
    """Represents a decoy system or service."""

    decoy_id: str = Field(default_factory=lambda: str(uuid4()))
    hostname: str
    ip_address: str
    services: List[Dict[str, Any]]  # Service configurations
    honeytokens: List[str] = Field(default_factory=list)  # Associated token IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    triggered: bool = False


class TrapDocument(BaseModel):
    """Represents a trap document with tracking."""

    document_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    document_type: str
    content_hash: str
    tracking_token: str
    deployed_paths: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_log: List[Dict[str, Any]] = Field(default_factory=list)
    triggered: bool = False


class BreadcrumbTrail(BaseModel):
    """Represents a breadcrumb trail for deception."""

    trail_id: str = Field(default_factory=lambda: str(uuid4()))
    trail_type: str  # "file_path", "network_path", "config_entry"
    false_path: str
    real_path: Optional[str] = None
    honeytokens: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    followed: bool = False
    follow_count: int = 0


class DeceptionEvent(BaseModel):
    """Event triggered by deception element interaction."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    deception_type: DeceptionType
    element_id: str  # ID of triggered element
    source_ip: Optional[str] = None
    source_user: Optional[str] = None
    action: str  # "accessed", "modified", "copied", etc.
    severity: str  # "low", "medium", "high", "critical"
    details: Dict[str, Any] = Field(default_factory=dict)


class HoneytokenGenerator:
    """Generates various types of honeytokens."""

    @staticmethod
    def generate_api_key() -> str:
        """Generate fake API key."""
        prefix = secrets.choice(["sk", "pk", "api", "key"])
        chars = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(chars) for _ in range(32))
        return f"{prefix}_{key}"

    @staticmethod
    def generate_password() -> str:
        """Generate fake password."""
        words = ["Admin", "Secret", "Password", "System", "Database"]
        numbers = ''.join(secrets.choice(string.digits) for _ in range(4))
        special = secrets.choice("!@#$%")
        return f"{secrets.choice(words)}{numbers}{special}"

    @staticmethod
    def generate_ssh_key() -> str:
        """Generate fake SSH private key header."""
        key_type = secrets.choice(["RSA", "DSA", "ECDSA", "ED25519"])
        fake_key = ''.join(secrets.choice(string.ascii_letters + string.digits)
                          for _ in range(64))
        return f"-----BEGIN {key_type} PRIVATE KEY-----\n{fake_key}\n-----END {key_type} PRIVATE KEY-----"

    @staticmethod
    def generate_database_cred() -> Dict[str, str]:
        """Generate fake database credentials."""
        return {
            "host": f"db-{secrets.token_hex(4)}.internal",
            "port": str(secrets.choice([3306, 5432, 1433, 27017])),
            "username": f"db_user_{secrets.token_hex(4)}",
            "password": HoneytokenGenerator.generate_password(),
            "database": f"prod_db_{secrets.token_hex(4)}"
        }

    @staticmethod
    def generate_aws_key() -> Dict[str, str]:
        """Generate fake AWS credentials."""
        access_key = f"AKIA{''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))}"
        secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
        return {
            "access_key_id": access_key,
            "secret_access_key": secret_key,
            "region": secrets.choice(["us-east-1", "us-west-2", "eu-west-1"])
        }

    @staticmethod
    def generate_jwt() -> str:
        """Generate fake JWT token."""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": f"user_{secrets.token_hex(4)}",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        # Simplified fake JWT (not cryptographically valid)
        import base64
        header_b64 = base64.b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = secrets.token_urlsafe(32)
        return f"{header_b64}.{payload_b64}.{signature}"


class DeceptionEngine:
    """
    Main deception engine for creating and managing deceptive elements.

    Phase 1: PASSIVE deception only - creates elements and monitors access,
    but does not actively engage with attackers.
    """

    def __init__(self, config: DeceptionConfig):
        """Initialize deception engine."""
        self.config = config
        self.generator = HoneytokenGenerator()

        # Storage for deception elements
        self.honeytokens: Dict[str, Honeytoken] = {}
        self.decoy_systems: Dict[str, DecoySystem] = {}
        self.trap_documents: Dict[str, TrapDocument] = {}
        self.breadcrumbs: Dict[str, BreadcrumbTrail] = {}
        self.events: List[DeceptionEvent] = []

        # Tracking
        self._running = False
        self.triggers_count = 0

    async def initialize(self) -> None:
        """Initialize deception elements."""
        # Generate initial honeytokens
        await self._generate_honeytokens()

        # Create decoy systems
        await self._create_decoy_systems()

        # Deploy trap documents
        await self._deploy_trap_documents()

        # Create breadcrumb trails
        await self._create_breadcrumbs()

        logger.info(
            f"Deception Engine initialized - "
            f"Tokens: {len(self.honeytokens)}, "
            f"Decoys: {len(self.decoy_systems)}, "
            f"Traps: {len(self.trap_documents)}"
        )

    async def _generate_honeytokens(self) -> None:
        """Generate honeytokens based on configuration."""
        for token_type in self.config.honeytoken_types:
            for i in range(self.config.honeytokens_per_type):
                token = await self._create_honeytoken(token_type)
                self.honeytokens[token.token_id] = token

    async def _create_honeytoken(self, token_type: TokenType) -> Honeytoken:
        """Create a single honeytoken."""
        token_value = ""
        metadata = {}

        if token_type == TokenType.API_KEY:
            token_value = self.generator.generate_api_key()
            metadata = {"service": "internal_api", "scope": "read"}

        elif token_type == TokenType.PASSWORD:
            token_value = self.generator.generate_password()
            metadata = {"username": f"admin_{secrets.token_hex(4)}", "system": "production"}

        elif token_type == TokenType.SSH_KEY:
            token_value = self.generator.generate_ssh_key()
            metadata = {"host": f"server-{secrets.token_hex(4)}.internal", "user": "root"}

        elif token_type == TokenType.DATABASE_CRED:
            creds = self.generator.generate_database_cred()
            token_value = json.dumps(creds)
            metadata = creds

        elif token_type == TokenType.AWS_KEY:
            creds = self.generator.generate_aws_key()
            token_value = json.dumps(creds)
            metadata = creds

        elif token_type == TokenType.JWT:
            token_value = self.generator.generate_jwt()
            metadata = {"issuer": "auth.internal", "audience": "api.internal"}

        else:
            token_value = secrets.token_urlsafe(32)
            metadata = {"type": "generic"}

        return Honeytoken(
            token_type=token_type,
            token_value=token_value,
            metadata=metadata
        )

    async def _create_decoy_systems(self) -> None:
        """Create decoy systems."""
        for i in range(min(5, self.config.max_decoy_systems)):
            decoy = DecoySystem(
                hostname=f"prod-server-{secrets.token_hex(4)}",
                ip_address=f"10.0.{i}.{secrets.randbelow(255)}",
                services=[
                    {
                        "name": "ssh",
                        "port": 22,
                        "banner": "OpenSSH_7.4"
                    },
                    {
                        "name": "http",
                        "port": 80,
                        "banner": "Apache/2.4.41"
                    }
                ]
            )

            # Associate honeytokens with decoy
            token_ids = list(self.honeytokens.keys())[:2]
            decoy.honeytokens = token_ids

            self.decoy_systems[decoy.decoy_id] = decoy

    async def _deploy_trap_documents(self) -> None:
        """Deploy trap documents."""
        doc_names = [
            "passwords.txt",
            "api_keys.xlsx",
            "database_backup.sql",
            "aws_credentials.json",
            "financial_report.pdf",
            "employee_data.csv"
        ]

        for name in doc_names[:self.config.max_trap_documents]:
            doc_type = name.split('.')[-1]
            if doc_type in self.config.trap_document_types:
                trap = TrapDocument(
                    filename=name,
                    document_type=doc_type,
                    content_hash=hashlib.sha256(name.encode()).hexdigest(),
                    tracking_token=secrets.token_urlsafe(16),
                    deployed_paths=[
                        f"/tmp/{name}",
                        f"/var/www/html/backup/{name}",
                        f"/home/admin/Documents/{name}"
                    ]
                )
                self.trap_documents[trap.document_id] = trap

    async def _create_breadcrumbs(self) -> None:
        """Create breadcrumb trails."""
        trails = [
            BreadcrumbTrail(
                trail_type="file_path",
                false_path="/etc/secret_config/master_key.pem",
                real_path=None
            ),
            BreadcrumbTrail(
                trail_type="network_path",
                false_path="admin.internal.company.com",
                real_path=None
            ),
            BreadcrumbTrail(
                trail_type="config_entry",
                false_path="DATABASE_MASTER_PASSWORD=SuperSecret123!",
                real_path=None
            )
        ]

        for trail in trails:
            # Associate honeytokens with breadcrumbs
            if self.honeytokens:
                trail.honeytokens = [list(self.honeytokens.keys())[0]]
            self.breadcrumbs[trail.trail_id] = trail

    async def check_honeytoken(self, token_value: str, source_ip: str = None) -> Optional[DeceptionEvent]:
        """
        Check if accessed token is a honeytoken.

        Phase 1: PASSIVE - only logs and returns event, no active response.
        """
        for token_id, token in self.honeytokens.items():
            if token.token_value == token_value or token_value in token.token_value:
                # Token triggered!
                token.triggered = True
                token.access_count += 1
                token.last_accessed = datetime.utcnow()

                # Create event
                event = DeceptionEvent(
                    deception_type=DeceptionType.HONEYTOKEN,
                    element_id=token_id,
                    source_ip=source_ip,
                    action="accessed",
                    severity="high",
                    details={
                        "token_type": token.token_type.value,
                        "metadata": token.metadata,
                        "access_count": token.access_count
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.warning(
                    f"HONEYTOKEN TRIGGERED - Type: {token.token_type.value}, "
                    f"Source: {source_ip}, Count: {token.access_count}"
                )

                return event

        return None

    async def check_decoy_interaction(
        self,
        target_ip: str,
        source_ip: str,
        action: str = "connection"
    ) -> Optional[DeceptionEvent]:
        """
        Check if interaction is with a decoy system.

        Phase 1: PASSIVE - only logs interaction, doesn't engage.
        """
        for decoy_id, decoy in self.decoy_systems.items():
            if decoy.ip_address == target_ip or decoy.hostname == target_ip:
                # Decoy triggered!
                decoy.triggered = True
                decoy.interaction_count += 1
                decoy.last_interaction = datetime.utcnow()

                # Create event
                event = DeceptionEvent(
                    deception_type=DeceptionType.DECOY_SYSTEM,
                    element_id=decoy_id,
                    source_ip=source_ip,
                    action=action,
                    severity="high" if decoy.interaction_count > 3 else "medium",
                    details={
                        "hostname": decoy.hostname,
                        "services": decoy.services,
                        "interaction_count": decoy.interaction_count
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.warning(
                    f"DECOY TRIGGERED - System: {decoy.hostname}, "
                    f"Source: {source_ip}, Action: {action}"
                )

                return event

        return None

    async def check_trap_document(
        self,
        filename: str,
        action: str,
        source_ip: str = None,
        source_user: str = None
    ) -> Optional[DeceptionEvent]:
        """
        Check if accessed document is a trap.

        Phase 1: PASSIVE - only logs access, doesn't modify or block.
        """
        for doc_id, trap in self.trap_documents.items():
            if trap.filename == filename or filename in trap.deployed_paths:
                # Trap triggered!
                trap.triggered = True
                trap.access_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": action,
                    "source_ip": source_ip,
                    "source_user": source_user
                })

                # Create event
                event = DeceptionEvent(
                    deception_type=DeceptionType.TRAP_DOCUMENT,
                    element_id=doc_id,
                    source_ip=source_ip,
                    source_user=source_user,
                    action=action,
                    severity="critical" if action in ["copied", "exfiltrated"] else "high",
                    details={
                        "filename": trap.filename,
                        "document_type": trap.document_type,
                        "access_count": len(trap.access_log)
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.warning(
                    f"TRAP DOCUMENT TRIGGERED - File: {trap.filename}, "
                    f"Action: {action}, Source: {source_ip or source_user}"
                )

                return event

        return None

    async def check_breadcrumb(self, path: str, source_ip: str = None) -> Optional[DeceptionEvent]:
        """
        Check if path matches a breadcrumb trail.

        Phase 1: PASSIVE - only tracks following, doesn't redirect.
        """
        for trail_id, trail in self.breadcrumbs.items():
            if trail.false_path == path or path in trail.false_path:
                # Breadcrumb followed!
                trail.followed = True
                trail.follow_count += 1

                # Create event
                event = DeceptionEvent(
                    deception_type=DeceptionType.BREADCRUMB,
                    element_id=trail_id,
                    source_ip=source_ip,
                    action="followed",
                    severity="medium",
                    details={
                        "trail_type": trail.trail_type,
                        "false_path": trail.false_path,
                        "follow_count": trail.follow_count
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.info(
                    f"BREADCRUMB FOLLOWED - Type: {trail.trail_type}, "
                    f"Path: {trail.false_path}, Source: {source_ip}"
                )

                return event

        return None

    async def get_deception_status(self) -> Dict[str, Any]:
        """Get current status of deception elements."""
        total_honeytokens = len(self.honeytokens)
        triggered_tokens = sum(1 for t in self.honeytokens.values() if t.triggered)

        total_decoys = len(self.decoy_systems)
        triggered_decoys = sum(1 for d in self.decoy_systems.values() if d.triggered)

        total_traps = len(self.trap_documents)
        triggered_traps = sum(1 for t in self.trap_documents.values() if t.triggered)

        total_breadcrumbs = len(self.breadcrumbs)
        followed_breadcrumbs = sum(1 for b in self.breadcrumbs.values() if b.followed)

        return {
            "active": self._running,
            "honeytokens": {
                "total": total_honeytokens,
                "triggered": triggered_tokens,
                "percentage": (triggered_tokens / total_honeytokens * 100) if total_honeytokens > 0 else 0
            },
            "decoy_systems": {
                "total": total_decoys,
                "triggered": triggered_decoys,
                "percentage": (triggered_decoys / total_decoys * 100) if total_decoys > 0 else 0
            },
            "trap_documents": {
                "total": total_traps,
                "triggered": triggered_traps,
                "percentage": (triggered_traps / total_traps * 100) if total_traps > 0 else 0
            },
            "breadcrumbs": {
                "total": total_breadcrumbs,
                "followed": followed_breadcrumbs,
                "percentage": (followed_breadcrumbs / total_breadcrumbs * 100) if total_breadcrumbs > 0 else 0
            },
            "total_triggers": self.triggers_count,
            "recent_events": self.events[-10:]  # Last 10 events
        }

    async def rotate_honeytokens(self) -> int:
        """
        Rotate old honeytokens.

        Returns number of tokens rotated.
        """
        rotated = 0
        cutoff = datetime.utcnow() - timedelta(days=self.config.token_rotation_days)

        for token_id in list(self.honeytokens.keys()):
            token = self.honeytokens[token_id]
            if token.created_at < cutoff and not token.triggered:
                # Create replacement token
                new_token = await self._create_honeytoken(token.token_type)
                self.honeytokens[new_token.token_id] = new_token

                # Remove old token
                del self.honeytokens[token_id]
                rotated += 1

        logger.info(f"Rotated {rotated} honeytokens")
        return rotated

    async def start(self) -> None:
        """Start deception engine."""
        self._running = True
        await self.initialize()
        logger.info("Deception Engine started (Phase 1: PASSIVE mode)")

    async def stop(self) -> None:
        """Stop deception engine."""
        self._running = False
        logger.info(
            f"Deception Engine stopped - "
            f"Total triggers: {self.triggers_count}, "
            f"Events: {len(self.events)}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            "running": self._running,
            "honeytokens": len(self.honeytokens),
            "decoy_systems": len(self.decoy_systems),
            "trap_documents": len(self.trap_documents),
            "breadcrumbs": len(self.breadcrumbs),
            "total_triggers": self.triggers_count,
            "events_logged": len(self.events)
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DeceptionEngine(running={self._running}, "
            f"honeytokens={len(self.honeytokens)}, "
            f"triggers={self.triggers_count})"
        )