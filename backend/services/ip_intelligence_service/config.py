
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Manages application configuration using Pydantic."""
    DATABASE_URL: str = "sqlite+aiosqlite:///./ip_intel.db"
    CACHE_TTL_SECONDS: int = 86400  # 24 hours

    # External API URLs
    IP_API_URL: str = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,query"
    IPINFO_URL: str = "https://ipinfo.io/{ip}/json"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
