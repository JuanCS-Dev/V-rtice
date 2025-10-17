"""Configuration for Narrative Filter Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service
    service_name: str = "narrative-filter-service"
    port: int = 9200
    host: str = "0.0.0.0"
    debug: bool = False

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "narrative-filter-group"
    kafka_topic_input: str = "agent-communications"
    kafka_topic_semantic: str = "semantic-events"
    kafka_topic_strategic: str = "strategic-patterns"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "vertice_db"
    postgres_user: str = "vertice"
    postgres_password: str = "password"

    @property
    def postgres_dsn(self) -> str:
        """PostgreSQL connection string."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ML Models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Thresholds
    alliance_threshold: float = 0.75
    inconsistency_threshold: float = 0.7
    deception_threshold: float = 0.65
    confidence_threshold: float = 0.8
    critical_deception: float = 0.9
    critical_inconsistency: float = 0.9
    high_deception: float = 0.7
    high_inconsistency: float = 0.7


settings = Settings()
