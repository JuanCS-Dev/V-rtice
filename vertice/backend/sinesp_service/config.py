from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SINESP_API_BASE_URL: str = (
        "https://wdapi2.sinesp.gov.br"  # API oficial do SINESP Cidadão
    )
    SINESP_API_KEY: str = "your_sinesp_api_key"  # Default, should be overridden by .env
    RATE_LIMIT_PER_MINUTE: int = 100
    AUTH_SERVICE_URL: str = (
        "http://auth_service:8003"  # Default for internal communication
    )


settings = Settings()
