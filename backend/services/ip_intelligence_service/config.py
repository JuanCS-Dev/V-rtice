"""Maximus IP Intelligence Service - Configuration Module.

This module handles the configuration settings for the IP Intelligence Service.
It provides a centralized place to define and manage parameters such as API keys
for external IP intelligence providers, caching settings, logging levels, and
other operational settings.

By externalizing configuration, this module allows for flexible deployment and
management of the IP Intelligence Service without requiring code changes.
It supports loading configurations from environment variables, files, or other
sources, ensuring adaptability across different environments.
"""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Maximus IP Intelligence Service.

    Settings are loaded from environment variables or a .env file.
    """

    app_name: str = "Maximus IP Intelligence Service"
    external_ip_api_key: str = os.getenv(
        "EXTERNAL_IP_API_KEY", "your_external_ip_api_key"
    )
    cache_ttl_seconds: int = os.getenv("CACHE_TTL_SECONDS", 3600)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Returns a singleton instance of the Settings.

    Returns:
        Settings: The configuration settings for the IP Intelligence service.
    """
    return Settings()
