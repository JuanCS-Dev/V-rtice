"""Service configuration for Tegumentar Service."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from backend.modules.tegumentar import TegumentarModule, TegumentarSettings, get_settings


class TegumentarServiceSettings(BaseSettings):
    interface: str = Field(..., min_length=1, description="Network interface to attach the XDP reflex arc.")
    host: str = Field("0.0.0.0", description="API bind host.")
    port: int = Field(8085, ge=1, le=65535, description="API bind port.")

    class Config:
        env_prefix = "TEGUMENTAR_SERVICE_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_service_settings() -> TegumentarServiceSettings:
    return TegumentarServiceSettings()


@lru_cache()
def get_module(settings: Optional[TegumentarSettings] = None) -> TegumentarModule:
    module_settings = settings or get_settings()
    return TegumentarModule(module_settings)


__all__ = ["TegumentarServiceSettings", "get_service_settings", "get_module"]
