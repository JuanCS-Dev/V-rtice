"""Configuration schema for the Tegumentar firewall module.

The configuration centralises all tunables so the three layers (epiderme,
derme, hipoderme) can share consistent parameters. Settings are loaded from
environment variables using Pydantic.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings


class TegumentarSettings(BaseSettings):
    """Pydantic settings for the Tegumentar module."""

    environment: str = Field(
        "production", pattern=r"^(development|staging|production)$"
    )

    # === Epiderme ===
    nft_binary: str = Field("/usr/sbin/nft", description="Path to nftables binary.")
    nft_table_name: str = Field("tegumentar_epiderme", min_length=1, max_length=64)
    nft_chain_name: str = Field("edge_filter", min_length=1, max_length=64)
    reputation_refresh_interval: PositiveInt = Field(
        900, description="Seconds between IP reputation synchronisations."
    )
    ip_reputation_sources: list[HttpUrl] = Field(
        default=[
            "https://lists.blocklist.de/lists/all.txt",
            "https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
        ],
        description="External PAMP feeds consumed by the epiderme layer.",
    )
    redis_url: str = Field(
        "redis://localhost:6379/0",
        description="Redis instance used for distributed rate limiting and cache.",
    )
    reputation_cache_path: str = Field(
        str(Path.home() / ".cache" / "tegumentar" / "blocked_ips.txt"),
        description="Local cache of merged reputation feeds.",
    )
    rate_limit_capacity: PositiveInt = Field(
        10000, description="Token bucket capacity per source IP."
    )
    rate_limit_refill_per_second: PositiveInt = Field(
        500, description="Tokens refilled every second per source IP."
    )

    # === Derme ===
    postgres_dsn: str = Field(
        "postgresql://tegumentar:tegumentar@localhost:5432/tegumentar",
        description="Timescale/PostgreSQL DSN for session state and analytics.",
    )
    kafka_bootstrap_servers: str = Field(
        "localhost:9092", description="Kafka cluster for Langerhans broadcasts."
    )
    reflex_topic: str = Field(
        "tegumentar.reflex",
        description="Kafka topic receiving reflex arc immediate alerts.",
    )
    langerhans_topic: str = Field(
        "tegumentar.langerhans",
        description="Kafka topic for distribution of newly learned threat signatures.",
    )
    lymphnode_endpoint: HttpUrl = Field(
        "http://localhost:8021",
        description="Endpoint do Linfonodo Digital (Immunis API).",
    )
    lymphnode_api_key: str | None = Field(
        default=None,
        description="Token opcional para autenticação no Linfonodo (Bearer).",
    )
    anomaly_model_path: str = Field(
        str(
            Path.home() / ".cache" / "tegumentar" / "models" / "anomaly_detector.joblib"
        ),
        description="Path to the trained anomaly detection model.",
    )
    signature_directory: str = Field(
        str(Path(__file__).resolve().parent / "resources" / "signatures"),
        description="Directory containing YAML signatures.",
    )

    # === Hipoderme ===
    mmei_endpoint: HttpUrl = Field(
        "http://localhost:8600/api/mmei/v1",
        description="Endpoint for communicating posture and qualia with MAXIMUS.",
    )
    sdnc_endpoint: HttpUrl | None = Field(
        "http://localhost:8181/restconf",
        description="Software defined network controller endpoint for permeability actions.",
    )
    soar_playbooks_path: str = Field(
        str(Path(__file__).resolve().parent / "resources" / "playbooks"),
        description="Directory with YAML playbooks executed during wound healing.",
    )

    prometheus_metrics_port: PositiveInt = Field(
        9815, description="Port where tegumentar metrics are exposed."
    )

    class Config:
        env_prefix = "TEGUMENTAR_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore env vars that don't match schema

    @field_validator("ip_reputation_sources", mode="before")
    def _split_reputation_sources(cls, value: object) -> object:
        if isinstance(value, str):
            return [source.strip() for source in value.split(",") if source.strip()]
        return value


@lru_cache
def get_settings() -> TegumentarSettings:
    """Cached accessor to avoid reparsing environment variables."""

    return TegumentarSettings()


__all__ = ["TegumentarSettings", "get_settings"]
