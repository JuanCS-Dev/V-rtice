"""Maximus BAS Service - Configuration Module.

This module handles the configuration settings for the Breach and Attack
Simulation (BAS) service. It provides a centralized place to define and manage
parameters such as API keys for external services, simulation thresholds,
logging levels, and other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the BAS service without requiring code changes. It supports
loading configurations from environment variables, files, or other sources,
ensuring adaptability across different environments.
"""

import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus BAS Service.

    Settings are loaded from environment variables or a .env file.
    """

    app_name: str = "Maximus BAS Service"
    bas_api_key: str = os.getenv("BAS_API_KEY", "default_bas_key")
    simulation_timeout_seconds: int = os.getenv("SIMULATION_TIMEOUT_SECONDS", 300)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the BAS service.
    """
    return Settings()
