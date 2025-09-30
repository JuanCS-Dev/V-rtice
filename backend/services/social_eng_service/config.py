from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import EmailStr

class Settings(BaseSettings):
    APP_BASE_URL: str = "http://localhost:8011"
    DATABASE_URL: str = "sqlite+aiosqlite:///./social_eng.db"

    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_SENDER_EMAIL: EmailStr = "noreply@vertice.com"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
