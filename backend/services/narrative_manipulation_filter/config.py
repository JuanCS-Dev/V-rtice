"""Cognitive Defense System - Centralized Configuration.

All system configuration managed through Pydantic Settings with environment
variable support. Provides type safety, validation, and default values.
"""

from datetime import timedelta
from typing import Any, Dict, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration for Cognitive Defense System."""

    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================
    SERVICE_NAME: str = "narrative_manipulation_filter"
    SERVICE_VERSION: str = "2.0.0"
    SERVICE_PORT: int = Field(8030, env="SERVICE_PORT")
    SERVICE_HOST: str = Field("0.0.0.0", env="SERVICE_HOST")
    WORKERS: int = Field(4, env="WORKERS")
    DEBUG: bool = Field(False, env="DEBUG")

    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    POSTGRES_HOST: str = Field("postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("postgres", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("aurora", env="POSTGRES_DB")

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Database pool settings
    DB_POOL_SIZE: int = Field(20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(10, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(30, env="DB_POOL_TIMEOUT")
    DB_ECHO: bool = Field(False, env="DB_ECHO")
    POSTGRES_AUTO_CREATE_TABLES: bool = Field(True, env="POSTGRES_AUTO_CREATE_TABLES")

    # ============================================================================
    # REDIS CONFIGURATION
    # ============================================================================
    REDIS_HOST: str = Field("redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_MAX_CONNECTIONS: int = Field(50, env="REDIS_MAX_CONNECTIONS")

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Cache TTL strategies (in seconds)
    CACHE_TTL_NEWSGUARD: int = Field(604800, env="CACHE_TTL_NEWSGUARD")  # 7 days
    CACHE_TTL_FACTCHECK: int = Field(2592000, env="CACHE_TTL_FACTCHECK")  # 30 days
    CACHE_TTL_ANALYSIS: int = Field(604800, env="CACHE_TTL_ANALYSIS")  # 7 days
    CACHE_TTL_REPUTATION: int = Field(86400, env="CACHE_TTL_REPUTATION")  # 1 day
    CACHE_TTL_SESSION: int = Field(3600, env="CACHE_TTL_SESSION")  # 1 hour

    # ============================================================================
    # KAFKA CONFIGURATION
    # ============================================================================
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        "hcl-kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_CLIENT_ID: str = Field("cognitive_defense", env="KAFKA_CLIENT_ID")
    KAFKA_GROUP_ID: str = Field("cognitive_defense_group", env="KAFKA_GROUP_ID")
    KAFKA_AUTO_OFFSET_RESET: str = Field("earliest", env="KAFKA_AUTO_OFFSET_RESET")
    KAFKA_ENABLE_AUTO_COMMIT: bool = Field(True, env="KAFKA_ENABLE_AUTO_COMMIT")
    KAFKA_MAX_POLL_RECORDS: int = Field(500, env="KAFKA_MAX_POLL_RECORDS")

    # Kafka topics
    KAFKA_TOPIC_RAW_TEXT: str = "raw_text"
    KAFKA_TOPIC_PROCESSED_TEXT: str = "processed_text"
    KAFKA_TOPIC_CLAIMS_TO_VERIFY: str = "claims_to_verify"
    KAFKA_TOPIC_VERIFICATION_RESULTS: str = "verification_results"
    KAFKA_TOPIC_ANALYSIS_RESULTS: str = "analysis_results"
    KAFKA_TOPIC_ERRORS: str = "verification_errors"

    # ============================================================================
    # SERIEMA GRAPH CONFIGURATION
    # ============================================================================
    SERIEMA_URL: str = Field("http://localhost:7474", env="SERIEMA_URL")
    SERIEMA_USER: str = Field("neo4j", env="SERIEMA_USER")
    SERIEMA_PASSWORD: str = Field("password", env="SERIEMA_PASSWORD")

    # ============================================================================
    # EXTERNAL API KEYS
    # ============================================================================
    NEWSGUARD_API_KEY: Optional[str] = Field(None, env="NEWSGUARD_API_KEY")
    NEWSGUARD_API_URL: str = Field(
        "https://api.newsguardtech.com/v1", env="NEWSGUARD_API_URL"
    )

    GOOGLE_FACTCHECK_API_KEY: Optional[str] = Field(
        None, env="GOOGLE_FACTCHECK_API_KEY"
    )
    GOOGLE_FACTCHECK_API_URL: str = "https://factchecktools.googleapis.com/v1alpha1"

    CLAIMBUSTER_API_URL: str = "https://idir.uta.edu/claimbuster/api/v2"

    DBPEDIA_SPOTLIGHT_URL: str = "https://api.dbpedia-spotlight.org/pt/annotate"
    WIKIDATA_SPARQL_URL: str = "https://query.wikidata.org/sparql"
    DBPEDIA_SPARQL_URL: str = "https://dbpedia.org/sparql"

    GEMINI_API_KEY: str = Field(
        "", env="GEMINI_API_KEY"
    )  # Optional - can be empty for health checks
    GEMINI_MODEL: str = Field("gemini-2.0-flash-exp", env="GEMINI_MODEL")

    # ============================================================================
    # MODEL CONFIGURATION
    # ============================================================================
    MODEL_DIR: str = Field("./models", env="MODEL_DIR")

    # Model paths
    BERTIMBAU_EMOTIONS_PATH: str = Field(
        "./models/bertimbau-emotions", env="BERTIMBAU_EMOTIONS_PATH"
    )
    ROBERTA_PROPAGANDA_PATH: str = Field(
        "./models/roberta-pt-propaganda", env="ROBERTA_PROPAGANDA_PATH"
    )
    BERT_FALLACIES_PATH: str = Field(
        "./models/bert-fallacies", env="BERT_FALLACIES_PATH"
    )
    ROBERTA_CIALDINI_PATH: str = Field(
        "./models/roberta-cialdini", env="ROBERTA_CIALDINI_PATH"
    )
    BERT_COBAIT_PATH: str = Field("./models/bert-cobait", env="BERT_COBAIT_PATH")

    # Model serving configuration
    MODEL_BATCH_SIZE: int = Field(32, env="MODEL_BATCH_SIZE")
    MODEL_MAX_LENGTH: int = Field(512, env="MODEL_MAX_LENGTH")
    MODEL_DEVICE: str = Field("cpu", env="MODEL_DEVICE")  # "cpu" or "cuda"
    USE_QUANTIZATION: bool = Field(True, env="USE_QUANTIZATION")

    # ============================================================================
    # ANALYSIS THRESHOLDS
    # ============================================================================
    # Check-worthiness threshold (ClaimBuster)
    CHECK_WORTHINESS_THRESHOLD: float = Field(0.5, env="CHECK_WORTHINESS_THRESHOLD")

    # Source credibility thresholds
    CREDIBILITY_THRESHOLD_HIGH: float = Field(0.7, env="CREDIBILITY_THRESHOLD_HIGH")
    CREDIBILITY_THRESHOLD_LOW: float = Field(0.3, env="CREDIBILITY_THRESHOLD_LOW")

    # Manipulation score thresholds
    MANIPULATION_THRESHOLD_HIGH: float = Field(0.7, env="MANIPULATION_THRESHOLD_HIGH")
    MANIPULATION_THRESHOLD_MODERATE: float = Field(
        0.4, env="MANIPULATION_THRESHOLD_MODERATE"
    )
    MANIPULATION_THRESHOLD_LOW: float = Field(0.2, env="MANIPULATION_THRESHOLD_LOW")

    # Emotional manipulation thresholds
    EMOTIONAL_SCORE_THRESHOLD: float = Field(0.6, env="EMOTIONAL_SCORE_THRESHOLD")

    # Fallacy detection threshold
    FALLACY_CONFIDENCE_THRESHOLD: float = Field(0.7, env="FALLACY_CONFIDENCE_THRESHOLD")

    # Fact-check similarity threshold
    FACTCHECK_SIMILARITY_THRESHOLD: float = Field(
        0.85, env="FACTCHECK_SIMILARITY_THRESHOLD"
    )

    # Domain similarity threshold (for hopping detection)
    DOMAIN_SIMILARITY_THRESHOLD: float = Field(0.85, env="DOMAIN_SIMILARITY_THRESHOLD")

    # ============================================================================
    # SCORING WEIGHTS
    # ============================================================================
    # Module weights for final manipulation score
    WEIGHT_CREDIBILITY: float = Field(0.25, env="WEIGHT_CREDIBILITY")
    WEIGHT_EMOTIONAL: float = Field(0.25, env="WEIGHT_EMOTIONAL")
    WEIGHT_LOGICAL: float = Field(0.20, env="WEIGHT_LOGICAL")
    WEIGHT_REALITY: float = Field(0.30, env="WEIGHT_REALITY")

    # Source credibility scoring weights
    WEIGHT_NEWSGUARD: float = Field(0.7, env="WEIGHT_NEWSGUARD")
    WEIGHT_HISTORICAL: float = Field(0.3, env="WEIGHT_HISTORICAL")

    @field_validator(
        "WEIGHT_CREDIBILITY", "WEIGHT_EMOTIONAL", "WEIGHT_LOGICAL", "WEIGHT_REALITY"
    )
    @classmethod
    def validate_weights(cls, v: float) -> float:
        """Ensure weights are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(f"Weight must be between 0 and 1, got {v}")
        return v

    # ============================================================================
    # PERFORMANCE CONFIGURATION
    # ============================================================================
    MAX_WORKERS: int = Field(10, env="MAX_WORKERS")
    MAX_CONTENT_LENGTH: int = Field(10000, env="MAX_CONTENT_LENGTH")
    REQUEST_TIMEOUT: int = Field(30, env="REQUEST_TIMEOUT")  # seconds

    # Batching configuration
    BATCH_WAIT_TIME_MS: int = Field(100, env="BATCH_WAIT_TIME_MS")
    BATCH_SIZE: int = Field(32, env="BATCH_SIZE")

    # Queue sizes
    TIER2_QUEUE_SIZE: int = Field(1000, env="TIER2_QUEUE_SIZE")
    BATCH_QUEUE_SIZE: int = Field(500, env="BATCH_QUEUE_SIZE")

    # ============================================================================
    # ADVERSARIAL DEFENSE CONFIGURATION
    # ============================================================================
    ENABLE_ADVERSARIAL_DEFENSE: bool = Field(True, env="ENABLE_ADVERSARIAL_DEFENSE")
    RANDOMIZED_SMOOTHING_SIGMA: float = Field(0.1, env="RANDOMIZED_SMOOTHING_SIGMA")
    RANDOMIZED_SMOOTHING_SAMPLES: int = Field(100, env="RANDOMIZED_SMOOTHING_SAMPLES")

    # ============================================================================
    # MLOPS CONFIGURATION
    # ============================================================================
    ENABLE_MLOPS: bool = Field(False, env="ENABLE_MLOPS")
    MLFLOW_TRACKING_URI: Optional[str] = Field(None, env="MLFLOW_TRACKING_URI")
    MODEL_REGISTRY_URI: Optional[str] = Field(None, env="MODEL_REGISTRY_URI")

    # Retraining triggers
    RETRAINING_SCHEDULE_DAYS: int = Field(7, env="RETRAINING_SCHEDULE_DAYS")
    DRIFT_CONFIDENCE_THRESHOLD: float = Field(0.7, env="DRIFT_CONFIDENCE_THRESHOLD")
    DRIFT_LATENCY_THRESHOLD_MS: int = Field(1000, env="DRIFT_LATENCY_THRESHOLD_MS")
    DRIFT_ERROR_RATE_THRESHOLD: float = Field(0.05, env="DRIFT_ERROR_RATE_THRESHOLD")

    # ============================================================================
    # MONITORING & LOGGING
    # ============================================================================
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("json", env="LOG_FORMAT")  # "json" or "text"

    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9090, env="METRICS_PORT")

    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================
    ENABLE_MODULE_CREDIBILITY: bool = Field(True, env="ENABLE_MODULE_CREDIBILITY")
    ENABLE_MODULE_EMOTIONAL: bool = Field(True, env="ENABLE_MODULE_EMOTIONAL")
    ENABLE_MODULE_LOGICAL: bool = Field(True, env="ENABLE_MODULE_LOGICAL")
    ENABLE_MODULE_REALITY: bool = Field(True, env="ENABLE_MODULE_REALITY")

    ENABLE_TIER2_VERIFICATION: bool = Field(True, env="ENABLE_TIER2_VERIFICATION")
    ENABLE_MEME_ANALYSIS: bool = Field(
        False, env="ENABLE_MEME_ANALYSIS"
    )  # Disabled by default (heavy)

    ENABLE_ARGUMENTATION_GRAPHS: bool = Field(True, env="ENABLE_ARGUMENTATION_GRAPHS")
    ENABLE_DOMAIN_FINGERPRINTING: bool = Field(True, env="ENABLE_DOMAIN_FINGERPRINTING")

    # ============================================================================
    # DEVELOPMENT & TESTING
    # ============================================================================
    TESTING_MODE: bool = Field(False, env="TESTING_MODE")
    MOCK_EXTERNAL_APIS: bool = Field(False, env="MOCK_EXTERNAL_APIS")
    SEED: int = Field(42, env="SEED")  # For reproducibility

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"

    def get_cache_ttl(self, category: str) -> int:
        """Get TTL in seconds for a cache category.

        Args:
            category: Cache category ("newsguard", "factcheck", "analysis", "reputation", "session")

        Returns:
            TTL in seconds

        Raises:
            ValueError: If category is unknown
        """
        ttl_map = {
            "newsguard": self.CACHE_TTL_NEWSGUARD,
            "factcheck": self.CACHE_TTL_FACTCHECK,
            "analysis": self.CACHE_TTL_ANALYSIS,
            "reputation": self.CACHE_TTL_REPUTATION,
            "session": self.CACHE_TTL_SESSION,
        }

        if category not in ttl_map:
            raise ValueError(f"Unknown cache category: {category}")

        return ttl_map[category]

    def get_kafka_topics(self) -> Dict[str, str]:
        """Get all Kafka topic names as a dictionary.

        Returns:
            Dictionary mapping topic names to their values
        """
        return {
            "raw_text": self.KAFKA_TOPIC_RAW_TEXT,
            "processed_text": self.KAFKA_TOPIC_PROCESSED_TEXT,
            "claims_to_verify": self.KAFKA_TOPIC_CLAIMS_TO_VERIFY,
            "verification_results": self.KAFKA_TOPIC_VERIFICATION_RESULTS,
            "analysis_results": self.KAFKA_TOPIC_ANALYSIS_RESULTS,
            "errors": self.KAFKA_TOPIC_ERRORS,
        }

    def validate_configuration(self) -> bool:
        """Validate critical configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate weights sum to approximately 1.0
        total_weight = (
            self.WEIGHT_CREDIBILITY
            + self.WEIGHT_EMOTIONAL
            + self.WEIGHT_LOGICAL
            + self.WEIGHT_REALITY
        )

        if not 0.99 <= total_weight <= 1.01:
            raise ValueError(
                f"Module weights must sum to 1.0, got {total_weight}. "
                f"Check WEIGHT_CREDIBILITY, WEIGHT_EMOTIONAL, WEIGHT_LOGICAL, WEIGHT_REALITY"
            )

        # Validate Gemini API key is present (commented for health check compatibility)
        # if not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "your-api-key-here":
        #     raise ValueError(
        #         "GEMINI_API_KEY must be set in environment variables or .env file"
        #     )

        return True

    def get_info(self) -> Dict[str, Any]:
        """Get configuration summary (safe for logging).

        Returns:
            Dictionary with non-sensitive configuration info
        """
        return {
            "service": {
                "name": self.SERVICE_NAME,
                "version": self.SERVICE_VERSION,
                "port": self.SERVICE_PORT,
                "workers": self.WORKERS,
            },
            "database": {
                "host": self.POSTGRES_HOST,
                "port": self.POSTGRES_PORT,
                "database": self.POSTGRES_DB,
            },
            "redis": {
                "host": self.REDIS_HOST,
                "port": self.REDIS_PORT,
                "db": self.REDIS_DB,
            },
            "kafka": {
                "bootstrap_servers": self.KAFKA_BOOTSTRAP_SERVERS,
                "topics": self.get_kafka_topics(),
            },
            "modules_enabled": {
                "credibility": self.ENABLE_MODULE_CREDIBILITY,
                "emotional": self.ENABLE_MODULE_EMOTIONAL,
                "logical": self.ENABLE_MODULE_LOGICAL,
                "reality": self.ENABLE_MODULE_REALITY,
            },
            "features": {
                "tier2_verification": self.ENABLE_TIER2_VERIFICATION,
                "meme_analysis": self.ENABLE_MEME_ANALYSIS,
                "argumentation_graphs": self.ENABLE_ARGUMENTATION_GRAPHS,
                "domain_fingerprinting": self.ENABLE_DOMAIN_FINGERPRINTING,
                "adversarial_defense": self.ENABLE_ADVERSARIAL_DEFENSE,
            },
            "thresholds": {
                "check_worthiness": self.CHECK_WORTHINESS_THRESHOLD,
                "manipulation_high": self.MANIPULATION_THRESHOLD_HIGH,
                "manipulation_moderate": self.MANIPULATION_THRESHOLD_MODERATE,
                "credibility_high": self.CREDIBILITY_THRESHOLD_HIGH,
                "credibility_low": self.CREDIBILITY_THRESHOLD_LOW,
            },
            "weights": {
                "credibility": self.WEIGHT_CREDIBILITY,
                "emotional": self.WEIGHT_EMOTIONAL,
                "logical": self.WEIGHT_LOGICAL,
                "reality": self.WEIGHT_REALITY,
            },
        }


# Global settings instance
settings = Settings()

# Validate on import
settings.validate_configuration()


def get_settings() -> Settings:
    """
    Return singleton settings instance.

    This function provides a consistent interface for dependency injection
    and is compatible with FastAPI's Depends() pattern.

    Returns:
        Settings: Global configuration singleton instance

    Example:
        ```python
        from fastapi import Depends
        from config import get_settings

        @app.get("/info")
        def info(settings: Settings = Depends(get_settings)):
            return {"environment": settings.ENVIRONMENT}
        ```
    """
    return settings
