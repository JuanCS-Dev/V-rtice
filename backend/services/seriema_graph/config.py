"""Seriema Graph Service - Configuration.

Simple configuration module for the Seriema Graph service.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Seriema Graph service settings."""

    # Service configuration
    SERVICE_NAME: str = Field(default="seriema_graph", env="SERVICE_NAME")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8029, env="PORT")

    # Neo4j configuration
    NEO4J_URI: str = Field(default="bolt://neo4j:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="neo4j123", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="neo4j", env="NEO4J_DATABASE")
    NEO4J_MAX_POOL_SIZE: int = Field(default=50, env="NEO4J_MAX_POOL_SIZE")

    # API configuration
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
