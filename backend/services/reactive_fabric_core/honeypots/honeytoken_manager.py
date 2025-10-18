"""
Intelligent Honeytoken Management System
Creates, plants, and monitors honeytokens across all honeypots
"""

import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

import aioredis
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class HoneytokenType(Enum):
    """Types of honeytokens"""
    AWS_CREDENTIALS = "aws_credentials"
    API_TOKEN = "api_token"
    SSH_KEY = "ssh_key"
    DATABASE_CREDS = "database_credentials"
    OAUTH_TOKEN = "oauth_token"
    DOCUMENT = "document"
    COOKIE = "cookie"
    ENVIRONMENT_VAR = "environment_variable"

class HoneytokenStatus(Enum):
    """Status of honeytoken"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    REVOKED = "revoked"

class Honeytoken:
    """Represents a single honeytoken"""

    def __init__(self,
                 token_id: str,
                 token_type: HoneytokenType,
                 value: str,
                 metadata: Dict[str, Any]):
        """
        Initialize honeytoken

        Args:
            token_id: Unique identifier
            token_type: Type of honeytoken
            value: The actual token value
            metadata: Additional metadata
        """
        self.token_id = token_id
        self.token_type = token_type
        self.value = value
        self.metadata = metadata
        self.status = HoneytokenStatus.ACTIVE
        self.created_at = datetime.now()
        self.triggered_at: Optional[datetime] = None
        self.trigger_count = 0
        self.trigger_sources: List[str] = []

    def trigger(self, source_ip: str, context: Dict[str, Any]):
        """Mark token as triggered"""
        self.status = HoneytokenStatus.TRIGGERED
        self.triggered_at = datetime.now()
        self.trigger_count += 1
        self.trigger_sources.append(source_ip)
        self.metadata["last_trigger"] = {
            "source_ip": source_ip,
            "timestamp": self.triggered_at.isoformat(),
            "context": context
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "token_id": self.token_id,
            "token_type": self.token_type.value,
            "value": self.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "trigger_count": self.trigger_count,
            "trigger_sources": self.trigger_sources,
            "metadata": self.metadata
        }

class HoneytokenManager:
    """
    Centralized management of honeytokens across all honeypots

    Features:
    - Dynamic token generation
    - Real-time monitoring
    - Automatic alerting
    - Context-aware placement
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize honeytoken manager

        Args:
            redis_url: Redis connection URL for tracking
        """
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

        # Token storage
        self.active_tokens: Dict[str, Honeytoken] = {}
        self.triggered_tokens: List[Honeytoken] = []

        # Callbacks for alerts
        self.trigger_callbacks: List[Callable] = []

        # Statistics
        self.stats = {
            "total_generated": 0,
            "total_triggered": 0,
            "total_active": 0
        }

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            logger.info("Honeytoken manager initialized with Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using in-memory storage.")

    async def generate_aws_credentials(self,
                                      placement: str = "config_file",
                                      region: str = "us-east-1") -> Honeytoken:
        """
        Generate fake AWS credentials that look realistic

        Args:
            placement: Where token will be placed
            region: AWS region to simulate

        Returns:
            Honeytoken with AWS credentials
        """
        # Generate realistic-looking access key
        access_key = f"AKIA{self._generate_random_string(16, uppercase=True)}"

        # Generate secret key (40 chars, base64-like)
        secret_key = self._generate_random_string(40)

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.AWS_CREDENTIALS,
            value=json.dumps({
                "access_key_id": access_key,
                "secret_access_key": secret_key,
                "region": region
            }),
            metadata={
                "placement": placement,
                "region": region,
                "purpose": "Production AWS credentials (CONFIDENTIAL)"
            }
        )

        await self._register_token(honeytoken)

        logger.info(f"Generated AWS credentials honeytoken: {access_key}")
        return honeytoken

    async def generate_api_token(self,
                                 service: str,
                                 prefix: str = "sk_live") -> Honeytoken:
        """
        Generate fake API token for services like Stripe, SendGrid, etc.

        Args:
            service: Service name (stripe, sendgrid, github, etc.)
            prefix: Token prefix

        Returns:
            Honeytoken with API token
        """
        # Generate token with realistic format
        token_body = self._generate_random_string(32)
        api_token = f"{prefix}_{token_body}"

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.API_TOKEN,
            value=api_token,
            metadata={
                "service": service,
                "prefix": prefix,
                "environment": "production"
            }
        )

        await self._register_token(honeytoken)

        logger.info(f"Generated {service} API token: {api_token[:20]}...")
        return honeytoken

    async def generate_ssh_keypair(self,
                                   key_name: str = "production-server",
                                   key_size: int = 2048) -> Honeytoken:
        """
        Generate fake SSH key pair

        Args:
            key_name: Name for the key
            key_size: RSA key size

        Returns:
            Honeytoken with SSH keys
        """
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        ).decode()

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.SSH_KEY,
            value=json.dumps({
                "private_key": private_pem,
                "public_key": public_pem,
                "key_name": key_name
            }),
            metadata={
                "key_name": key_name,
                "key_size": key_size,
                "server": f"{key_name}.internal.company.com"
            }
        )

        await self._register_token(honeytoken)

        logger.info(f"Generated SSH keypair honeytoken: {key_name}")
        return honeytoken

    async def generate_database_credentials(self,
                                           db_type: str = "postgresql",
                                           environment: str = "production") -> Honeytoken:
        """
        Generate fake database credentials

        Args:
            db_type: Database type
            environment: Environment name

        Returns:
            Honeytoken with DB credentials
        """
        username = f"{db_type}_admin"
        password = self._generate_strong_password()
        host = f"{db_type}-{environment}.internal.company.com"

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.DATABASE_CREDS,
            value=json.dumps({
                "host": host,
                "port": 5432 if db_type == "postgresql" else 3306,
                "username": username,
                "password": password,
                "database": f"{environment}_data"
            }),
            metadata={
                "db_type": db_type,
                "environment": environment,
                "purpose": "Backup database access"
            }
        )

        await self._register_token(honeytoken)

        logger.info(f"Generated {db_type} credentials honeytoken")
        return honeytoken

    async def generate_document_with_watermark(self,
                                              doc_type: str = "pdf",
                                              content: str = "Confidential") -> Honeytoken:
        """
        Generate document with invisible tracking

        Args:
            doc_type: Document type
            content: Document content

        Returns:
            Honeytoken for tracked document
        """
        doc_id = str(uuid.uuid4())
        tracking_url = f"https://tracking.internal.company.com/pixel/{doc_id}.gif"

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.DOCUMENT,
            value=json.dumps({
                "document_id": doc_id,
                "tracking_url": tracking_url,
                "filename": f"confidential_{doc_id}.{doc_type}"
            }),
            metadata={
                "doc_type": doc_type,
                "content_preview": content[:50],
                "tracking_method": "invisible_pixel"
            }
        )

        await self._register_token(honeytoken)

        logger.info(f"Generated tracked document honeytoken: {doc_id}")
        return honeytoken

    async def plant_tokens_in_honeypot(self,
                                      honeypot_id: str,
                                      honeypot_type: str) -> List[Honeytoken]:
        """
        Intelligently plant honeytokens in a honeypot based on type

        Args:
            honeypot_id: Honeypot identifier
            honeypot_type: Type of honeypot (ssh, web, database)

        Returns:
            List of planted honeytokens
        """
        planted = []

        if honeypot_type == "ssh":
            # Plant SSH keys and AWS credentials
            ssh_token = await self.generate_ssh_keypair(
                key_name=f"{honeypot_id}_deploy_key"
            )
            planted.append(ssh_token)

            aws_token = await self.generate_aws_credentials(
                placement="~/.aws/credentials"
            )
            planted.append(aws_token)

        elif honeypot_type == "web":
            # Plant API tokens in config files
            stripe_token = await self.generate_api_token("stripe", "sk_live")
            planted.append(stripe_token)

            github_token = await self.generate_api_token("github", "ghp")
            planted.append(github_token)

            # Plant database credentials
            db_token = await self.generate_database_credentials()
            planted.append(db_token)

        elif honeypot_type == "database":
            # Plant various credentials in tables
            aws_token = await self.generate_aws_credentials(
                placement="api_credentials_table"
            )
            planted.append(aws_token)

            ssh_token = await self.generate_ssh_keypair(
                key_name="production_backup_key"
            )
            planted.append(ssh_token)

        logger.info(f"Planted {len(planted)} honeytokens in {honeypot_id}")
        return planted

    async def check_token_triggered(self, token_value: str) -> Optional[Honeytoken]:
        """
        Check if a specific token has been triggered

        Args:
            token_value: Token value to check

        Returns:
            Honeytoken if found and triggered, None otherwise
        """
        for token in self.active_tokens.values():
            if token.value == token_value or token_value in token.value:
                if token.status == HoneytokenStatus.TRIGGERED:
                    return token

        return None

    async def trigger_token(self,
                           token_id: str,
                           source_ip: str,
                           context: Dict[str, Any]) -> bool:
        """
        Mark a token as triggered (used by attacker)

        Args:
            token_id: Token identifier
            source_ip: IP that used the token
            context: Additional context about trigger

        Returns:
            True if token was found and triggered
        """
        if token_id not in self.active_tokens:
            logger.warning(f"Token {token_id} not found")
            return False

        token = self.active_tokens[token_id]
        token.trigger(source_ip, context)

        # Move to triggered list
        self.triggered_tokens.append(token)

        # Update stats
        self.stats["total_triggered"] += 1
        self.stats["total_active"] -= 1

        # Store in Redis
        if self.redis:
            await self.redis.hset(
                f"honeytoken_triggered:{token_id}",
                mapping={
                    "token_type": token.token_type.value,
                    "source_ip": source_ip,
                    "triggered_at": token.triggered_at.isoformat(),
                    "context": json.dumps(context)
                }
            )

        # Trigger callbacks
        for callback in self.trigger_callbacks:
            try:
                await callback(token, source_ip, context)
            except Exception as e:
                logger.error(f"Error in trigger callback: {e}")

        logger.critical(
            f"HONEYTOKEN TRIGGERED! Type: {token.token_type.value}, "
            f"Source: {source_ip}, Token: {token_id[:8]}"
        )

        return True

    async def register_trigger_callback(self, callback: Callable):
        """
        Register callback for honeytoken triggers

        Args:
            callback: Async function to call when token is triggered
        """
        self.trigger_callbacks.append(callback)

    async def _register_token(self, token: Honeytoken):
        """Register a new token"""
        self.active_tokens[token.token_id] = token
        self.stats["total_generated"] += 1
        self.stats["total_active"] += 1

        # Store in Redis for persistence
        if self.redis:
            await self.redis.hset(
                f"honeytoken:{token.token_id}",
                mapping={
                    "token_type": token.token_type.value,
                    "value": token.value,
                    "created_at": token.created_at.isoformat(),
                    "metadata": json.dumps(token.metadata)
                }
            )

    def _generate_random_string(self,
                                length: int,
                                uppercase: bool = False) -> str:
        """Generate cryptographically secure random string"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        if uppercase:
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        return ''.join(secrets.choice(chars) for _ in range(length))

    def _generate_strong_password(self, length: int = 16) -> str:
        """Generate strong password"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))

    def get_stats(self) -> Dict:
        """Get honeytoken statistics"""
        return {
            **self.stats,
            "active_tokens": len(self.active_tokens),
            "triggered_tokens": len(self.triggered_tokens),
            "trigger_rate": (
                self.stats["total_triggered"] / self.stats["total_generated"]
                if self.stats["total_generated"] > 0 else 0
            )
        }

    def get_recent_triggers(self, limit: int = 10) -> List[Dict]:
        """Get recent honeytoken triggers"""
        recent = sorted(
            self.triggered_tokens,
            key=lambda t: t.triggered_at or datetime.min,
            reverse=True
        )[:limit]

        return [token.to_dict() for token in recent]

    async def cleanup_expired(self, max_age_days: int = 30):
        """Clean up old expired tokens"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        expired = [
            token_id for token_id, token in self.active_tokens.items()
            if token.created_at < cutoff_date and token.trigger_count == 0
        ]

        for token_id in expired:
            token = self.active_tokens[token_id]
            token.status = HoneytokenStatus.EXPIRED
            del self.active_tokens[token_id]

            if self.redis:
                await self.redis.delete(f"honeytoken:{token_id}")

        logger.info(f"Cleaned up {len(expired)} expired honeytokens")
        return len(expired)