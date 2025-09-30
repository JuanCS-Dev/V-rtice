
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Manages application configuration using Pydantic."""
    DATABASE_URL: str = "sqlite+aiosqlite:///./vuln_scanner.db"
    APP_VERSION: str = "2.0.0"
    APP_TITLE: str = "Vulnerability Scanner Service"
    APP_DESCRIPTION: str = "Serviço de scanner de vulnerabilidades ofensivo - Projeto Vértice"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
