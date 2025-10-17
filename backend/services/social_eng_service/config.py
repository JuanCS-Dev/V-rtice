"""Maximus Social Engineering Service - Configuration Module.

This module handles the configuration settings for the Social Engineering Service.
It provides a centralized place to define and manage parameters such as API keys
for external communication platforms, simulation parameters, logging levels,
and other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the Social Engineering Service without requiring code changes.
It supports loading configurations from environment variables, files, or other
sources, ensuring adaptability across different environments.
"""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus Social Engineering Service.

    Settings are loaded from environment variables or a .env file.
    """

    app_name: str = "Maximus Social Engineering Service"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./social_eng.db")
    email_api_key: str = os.getenv("EMAIL_API_KEY", "your_email_api_key")
    sms_api_key: str = os.getenv("SMS_API_KEY", "your_sms_api_key")
    simulation_speed_factor: float = os.getenv("SIMULATION_SPEED_FACTOR", 1.0)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Configuração para carregar variáveis de ambiente de um arquivo .env."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the Social Engineering service.
    """
    return Settings()
