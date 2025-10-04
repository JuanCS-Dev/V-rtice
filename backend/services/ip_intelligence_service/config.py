"""IP Intelligence Service - Configuration.

This module defines the configuration model for the IP Intelligence service,
loading settings from environment variables using Pydantic's BaseSettings.
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Manages application configuration using Pydantic.

    Attributes:
        DATABASE_URL (str): The connection string for the SQLite database.
        CACHE_TTL_SECONDS (int): The time-to-live for cached IP analysis results.
        IP_API_URL (str): The URL template for the ip-api.com GeoIP service.
        IPINFO_URL (str): The URL template for the ipinfo.io GeoIP service.
    """
    DATABASE_URL: str = "sqlite+aiosqlite:///./ip_intel.db"
    CACHE_TTL_SECONDS: int = 86400  # 24 hours

    # External API URLs
    IP_API_URL: str = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,query"
    IPINFO_URL: str = "https://ipinfo.io/{ip}/json"

    class Config:
        """Pydantic configuration settings."""
        env_file = ".env"
        extra = "ignore"

settings = Settings()