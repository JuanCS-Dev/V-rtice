"""Active Immune Core Service - Configuration

PRODUCTION-READY configuration using Pydantic Settings.
All settings loaded from environment variables with sensible defaults.
"""

import logging
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Active Immune Core Service configuration"""

    # ==================== SERVICE ====================
    service_name: str = Field(default="active_immune_core", description="Service name")
    service_port: int = Field(default=8200, ge=1024, le=65535, description="Service port")
    host: str = Field(default="0.0.0.0", description="Bind host")
    log_level: str = Field(default="INFO", description="Log level")
    debug: bool = Field(default=False, description="Debug mode")

    # ==================== KAFKA (CYTOKINES) ====================
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers (comma-separated)",
    )
    kafka_cytokine_topic_prefix: str = Field(
        default="immunis.cytokines",
        description="Topic prefix for cytokines",
    )
    kafka_consumer_group_prefix: str = Field(
        default="active_immune",
        description="Consumer group prefix",
    )
    kafka_acks: str = Field(
        default="all",
        description="Producer acks (all, 1, 0)",
    )
    kafka_compression: str = Field(
        default="gzip",
        description="Message compression (gzip, snappy, lz4, zstd)",
    )
    kafka_max_batch_size: int = Field(
        default=16384,
        ge=1024,
        description="Producer max batch size (bytes)",
    )

    # ==================== REDIS (HORMONES + STATE) ====================
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
    )
    redis_agent_state_ttl: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="Agent state TTL in Redis (seconds)",
    )
    redis_max_connections: int = Field(
        default=50,
        ge=10,
        le=1000,
        description="Redis connection pool max size",
    )

    # ==================== POSTGRESQL (MEMORY) ====================
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, ge=1024, le=65535, description="PostgreSQL port")
    postgres_db: str = Field(default="immunis_memory", description="Database name")
    postgres_user: str = Field(default="postgres", description="Database user")
    postgres_password: str = Field(default="postgres", description="Database password")
    postgres_pool_size: int = Field(
        default=10,
        ge=5,
        le=100,
        description="Connection pool size",
    )

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ==================== EXTERNAL SERVICES ====================
    rte_service_url: str = Field(
        default="http://localhost:8002",
        description="RTE Service URL (network operations)",
    )
    ip_intel_service_url: str = Field(
        default="http://localhost:8001",
        description="IP Intelligence Service URL",
    )
    ethical_ai_url: str = Field(
        default="http://localhost:8612",
        description="Ethical AI Audit Service URL",
    )
    memory_service_url: str = Field(
        default="http://localhost:8019",
        description="Memory Consolidation Service URL",
    )
    adaptive_immunity_url: str = Field(
        default="http://localhost:8020",
        description="Adaptive Immunity Service URL",
    )
    treg_service_url: str = Field(
        default="http://localhost:8018",
        description="Regulatory T-Cells Service URL",
    )

    # External service timeouts
    external_service_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="External service request timeout (seconds)",
    )

    # ==================== HOMEOSTASIS ====================
    baseline_active_percentage: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Baseline active agent percentage (Vigilância state)",
    )
    max_agent_lifespan_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Maximum agent lifespan (hours)",
    )
    energy_decay_rate_per_minute: float = Field(
        default=0.5,
        ge=0.1,
        le=10.0,
        description="Energy decay rate per minute",
    )

    # Temperature thresholds (Celsius)
    temp_repouso: float = Field(default=37.0, ge=36.0, le=37.5, description="Repouso temperature")
    temp_vigilancia: float = Field(default=37.5, ge=37.0, le=38.0, description="Vigilância temperature")
    temp_atencao: float = Field(default=38.0, ge=37.5, le=39.0, description="Atenção temperature")
    temp_inflamacao: float = Field(default=39.0, ge=38.0, le=42.0, description="Inflamação temperature")

    # ==================== CLONING ====================
    max_clones_per_threat: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum clones per threat",
    )
    clone_mutation_rate: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Somatic hypermutation rate (0-1)",
    )
    min_detections_for_cloning: int = Field(
        default=5,
        ge=2,
        le=20,
        description="Minimum detections to trigger cloning",
    )

    # ==================== AGENT LIMITS ====================
    max_total_agents: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum total agents (resource limit)",
    )
    max_agents_per_lymphnode: int = Field(
        default=200,
        ge=10,
        le=1000,
        description="Maximum agents per lymphnode",
    )

    # ==================== OBSERVABILITY ====================
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    structured_logging: bool = Field(default=True, description="Use structured JSON logging")
    tracing_enabled: bool = Field(default=False, description="Enable OpenTelemetry tracing")

    # ==================== SECURITY ====================
    ethical_ai_validation_enabled: bool = Field(
        default=True,
        description="Enable Ethical AI validation (NEVER disable in production)",
    )
    api_key: Optional[str] = Field(default=None, description="API key for authentication")

    # ==================== MODEL CONFIG ====================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="ACTIVE_IMMUNE_",
        extra="ignore",  # Ignore extra env vars
    )

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @validator("kafka_acks")
    def validate_kafka_acks(cls, v: str) -> str:
        """Validate Kafka acks"""
        valid_acks = ["all", "1", "0"]
        if v not in valid_acks:
            raise ValueError(f"Invalid Kafka acks: {v}. Must be one of {valid_acks}")
        return v

    def configure_logging(self) -> None:
        """Configure application logging"""
        numeric_level = getattr(logging, self.log_level)

        if self.structured_logging:
            # Structured logging for production
            import structlog

            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer(),
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
        else:
            # Simple logging for development
            logging.basicConfig(
                level=numeric_level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )


# Global settings instance
settings = Settings()
