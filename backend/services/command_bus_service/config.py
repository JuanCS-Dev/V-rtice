"""Configuration for Command Bus Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service
    service_name: str = "command-bus-service"
    port: int = 9202
    host: str = "0.0.0.0"
    debug: bool = False

    # NATS
    nats_url: str = "nats://localhost:4222"
    nats_subject_commands: str = "sovereign.commands"
    nats_subject_confirmations: str = "sovereign.confirmations"

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

    # Command execution timeouts (seconds)
    command_timeout_mute: int = 5
    command_timeout_isolate: int = 10
    command_timeout_terminate: int = 30

    # Rate limiting (per minute)
    rate_limit_mute: int = 10
    rate_limit_isolate: int = 5
    rate_limit_terminate: int = 3


settings = Settings()
