"""
Offensive Security Configuration
================================

Configuration management for offensive security operations.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class ReconConfig(BaseModel):
    """Reconnaissance configuration."""
    
    max_threads: int = Field(default=10, ge=1, le=100)
    timeout: float = Field(default=5.0, ge=0.1, le=60.0)
    scan_common_ports: bool = True
    common_ports: List[int] = Field(
        default_factory=lambda: [
            21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 
            3306, 3389, 5432, 5900, 8080, 8443
        ]
    )
    scan_all_ports: bool = False
    dns_servers: List[str] = Field(
        default_factory=lambda: ["8.8.8.8", "1.1.1.1"]
    )
    user_agent: str = "MAXIMUS-Recon/1.0"
    
    @validator('max_threads')
    def validate_max_threads(cls, v: int) -> int:
        """Ensure reasonable thread count."""
        if v < 1 or v > 100:
            raise ValueError("max_threads must be between 1 and 100")
        return v


class ExploitConfig(BaseModel):
    """Exploitation configuration."""
    
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=2.0, ge=0.1, le=30.0)
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    verify_success: bool = True
    safe_mode: bool = True
    payload_encoding: str = "base64"
    shell_port: int = Field(default=4444, ge=1024, le=65535)
    
    @validator('safe_mode')
    def warn_safe_mode(cls, v: bool) -> bool:
        """Warn if safe mode disabled."""
        if not v:
            import warnings
            warnings.warn(
                "Safe mode disabled - destructive exploits enabled",
                UserWarning
            )
        return v


class PostExploitConfig(BaseModel):
    """Post-exploitation configuration."""
    
    persistence_methods: List[str] = Field(
        default_factory=lambda: ["cron", "systemd", "registry"]
    )
    exfiltration_chunk_size: int = Field(default=1048576, ge=1024)  # 1MB
    c2_interval: float = Field(default=60.0, ge=1.0, le=3600.0)
    encryption_enabled: bool = True
    stealth_mode: bool = True
    cleanup_on_exit: bool = True


class IntelligenceConfig(BaseModel):
    """Intelligence gathering configuration."""
    
    osint_sources: List[str] = Field(
        default_factory=lambda: [
            "shodan", "censys", "virustotal", "github"
        ]
    )
    threat_intel_feeds: List[str] = Field(
        default_factory=lambda: ["otx", "misp", "threatfox"]
    )
    credential_databases: List[str] = Field(
        default_factory=lambda: ["haveibeenpwned", "dehashed"]
    )
    max_results: int = Field(default=100, ge=1, le=1000)
    api_rate_limit: float = Field(default=1.0, ge=0.1)  # requests per second


class OffensiveConfig(BaseModel):
    """Master offensive security configuration."""
    
    reconnaissance: ReconConfig = Field(default_factory=ReconConfig)
    exploitation: ExploitConfig = Field(default_factory=ExploitConfig)
    post_exploitation: PostExploitConfig = Field(default_factory=PostExploitConfig)
    intelligence: IntelligenceConfig = Field(default_factory=IntelligenceConfig)
    
    log_level: str = Field(default="INFO")
    log_file: Optional[Path] = None
    output_dir: Path = Field(default=Path("./offensive_output"))
    enable_metrics: bool = True
    
    # Ethical boundaries
    require_authorization: bool = True
    whitelist_only: bool = False
    target_whitelist: List[str] = Field(default_factory=list)
    target_blacklist: List[str] = Field(default_factory=list)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
        validate_assignment = True
    
    @validator('output_dir')
    def create_output_dir(cls, v: Path) -> Path:
        """Create output directory if not exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('target_whitelist', 'target_blacklist')
    def validate_targets(cls, v: List[str]) -> List[str]:
        """Validate target lists."""
        from .utils import is_valid_ip
        for target in v:
            if not is_valid_ip(target) and '/' not in target:
                # Allow hostnames and CIDR
                pass
        return v


def load_config(config_path: Optional[Path] = None) -> OffensiveConfig:
    """
    Load offensive security configuration.
    
    Args:
        config_path: Path to configuration file (YAML/JSON)
        
    Returns:
        Loaded configuration
    """
    if config_path and config_path.exists():
        import yaml
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return OffensiveConfig(**data)
    return OffensiveConfig()


# Global configuration instance
_config: Optional[OffensiveConfig] = None


def get_config() -> OffensiveConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: OffensiveConfig) -> None:
    """Set global configuration instance."""
    global _config
    _config = config
