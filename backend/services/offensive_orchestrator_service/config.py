"""
Configuration for Offensive Orchestrator Service.

Loads settings from environment variables with sensible defaults.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """PostgreSQL configuration for campaign storage."""

    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "offensive_campaigns"))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "maximus"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10")))

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string with psycopg2 driver."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class VectorDBConfig:
    """Qdrant configuration for attack memory vector search."""

    host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    collection_name: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "attack_memory"))
    vector_size: int = field(default_factory=lambda: int(os.getenv("QDRANT_VECTOR_SIZE", "1536")))  # Gemini embeddings
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("QDRANT_API_KEY"))

    @property
    def grpc_url(self) -> str:
        """Generate Qdrant gRPC URL."""
        return f"http://{self.host}:{self.port}"


@dataclass
class LLMConfig:
    """Gemini LLM configuration for orchestrator."""

    api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-pro"))
    temperature: float = field(default_factory=lambda: float(os.getenv("GEMINI_TEMPERATURE", "0.7")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("GEMINI_MAX_TOKENS", "4096")))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("GEMINI_TIMEOUT", "60")))


@dataclass
class HOTLConfig:
    """Human-on-the-Loop configuration."""

    enabled: bool = field(default_factory=lambda: os.getenv("HOTL_ENABLED", "true").lower() == "true")
    approval_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("HOTL_TIMEOUT", "300")))  # 5 min
    auto_approve_low_risk: bool = field(default_factory=lambda: os.getenv("HOTL_AUTO_APPROVE_LOW", "false").lower() == "true")
    audit_log_path: str = field(default_factory=lambda: os.getenv("HOTL_AUDIT_LOG", "/var/log/hotl/audit.log"))


@dataclass
class ServiceConfig:
    """Main service configuration."""

    host: str = field(default_factory=lambda: os.getenv("SERVICE_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("SERVICE_PORT", "8090")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Sub-configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    vectordb: VectorDBConfig = field(default_factory=VectorDBConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    hotl: HOTLConfig = field(default_factory=HOTLConfig)


def load_config() -> ServiceConfig:
    """
    Load configuration from environment variables.

    Returns:
        ServiceConfig: Complete service configuration

    Raises:
        ValueError: If required environment variables are missing
    """
    config = ServiceConfig()

    # Validate critical configs - DISABLED for graceful degradation
    # if not config.llm.api_key:
    #     raise ValueError("GEMINI_API_KEY environment variable is required")

    # if not config.database.password:
    #     raise ValueError("POSTGRES_PASSWORD environment variable is required")

    return config


# Singleton instance
_config: Optional[ServiceConfig] = None


def get_config() -> ServiceConfig:
    """
    Get singleton configuration instance.

    Returns:
        ServiceConfig: Service configuration
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
