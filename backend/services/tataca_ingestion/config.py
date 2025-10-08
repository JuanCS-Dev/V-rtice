"""Tatacá Ingestion Service - Configuration.

Configuration management for the ETL pipeline that ingests data from multiple
sources into the Vertice platform.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Tatacá Ingestion service settings."""

    # Service configuration
    SERVICE_NAME: str = Field(default="tataca_ingestion", env="SERVICE_NAME")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8028, env="PORT")

    # PostgreSQL configuration (Aurora database)
    POSTGRES_HOST: str = Field(default="postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="aurora", env="POSTGRES_DB")

    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Neo4j configuration (via Seriema Graph service)
    SERIEMA_GRAPH_URL: str = Field(default="http://seriema_graph:8029", env="SERIEMA_GRAPH_URL")

    # SINESP API configuration
    SINESP_SERVICE_URL: str = Field(default="http://sinesp_service:8018", env="SINESP_SERVICE_URL")

    # Data sources configuration
    ENABLE_SINESP_CONNECTOR: bool = Field(default=True, env="ENABLE_SINESP_CONNECTOR")
    ENABLE_PRISIONAL_CONNECTOR: bool = Field(default=False, env="ENABLE_PRISIONAL_CONNECTOR")
    ENABLE_ANTECEDENTES_CONNECTOR: bool = Field(default=False, env="ENABLE_ANTECEDENTES_CONNECTOR")

    # External API keys (optional - for future integrations)
    PRISIONAL_API_KEY: Optional[str] = Field(default=None, env="PRISIONAL_API_KEY")
    ANTECEDENTES_API_KEY: Optional[str] = Field(default=None, env="ANTECEDENTES_API_KEY")

    # Scheduler configuration
    ENABLE_SCHEDULER: bool = Field(default=True, env="ENABLE_SCHEDULER")
    SCHEDULER_INTERVAL_MINUTES: int = Field(default=60, env="SCHEDULER_INTERVAL_MINUTES")

    # Job configuration
    MAX_CONCURRENT_JOBS: int = Field(default=3, env="MAX_CONCURRENT_JOBS")
    JOB_TIMEOUT_SECONDS: int = Field(default=300, env="JOB_TIMEOUT_SECONDS")
    RETRY_ATTEMPTS: int = Field(default=3, env="RETRY_ATTEMPTS")
    RETRY_DELAY_SECONDS: int = Field(default=5, env="RETRY_DELAY_SECONDS")

    # Batch processing
    BATCH_SIZE: int = Field(default=100, env="BATCH_SIZE")
    ENABLE_PARALLEL_PROCESSING: bool = Field(default=True, env="ENABLE_PARALLEL_PROCESSING")

    # Monitoring
    PROMETHEUS_PORT: int = Field(default=8029, env="PROMETHEUS_PORT")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")

    # CORS configuration
    CORS_ORIGINS: str = Field(default="*", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Return singleton settings instance.

    Returns:
        Settings: Global configuration singleton instance
    """
    return settings
