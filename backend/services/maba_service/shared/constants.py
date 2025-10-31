"""
Vértice Platform - Centralized Constants

This module contains all system-wide constants used across the 67+ microservices.
Centralizing constants prevents magic strings/numbers and ensures consistency.

Usage:
    from shared.constants import ServicePorts, APIEndpoints

    app = FastAPI()
    uvicorn.run(app, host="0.0.0.0", port=ServicePorts.MAXIMUS_CORE)

Author: Vértice Platform Team
Version: 1.0.0
"""

from typing import Final

# ============================================================================
# SERVICE PORTS - All 67+ Microservices
# ============================================================================


class ServicePorts:
    """Service port assignments for all Vértice microservices.

    Port Range Allocation:
        8000-8099: Core & Intelligence Services
        8100-8199: Cognitive & Neural Services
        8200-8299: Data & Storage Services
        8300-8399: Offensive Security Arsenal
        8400-8499: Infrastructure Services
        9000+: Monitoring & Observability
    """

    # Core Services (8000-8019)
    API_GATEWAY: Final[int] = 8000
    MAXIMUS_CORE: Final[int] = 8001
    IP_INTELLIGENCE: Final[int] = 8002
    THREAT_INTEL: Final[int] = 8003
    FILE_ANALYSIS: Final[int] = 8004
    MALWARE_ANALYSIS: Final[int] = 8007
    BEHAVIORAL_ANALYSIS: Final[int] = 8009
    FORENSICS: Final[int] = 8010
    OSINT: Final[int] = 8012
    PREDICTIVE_HUNTING: Final[int] = 8013
    CONTEXT_ANALYZER: Final[int] = 8014
    IMMUNIS_API: Final[int] = 8015
    SIEM_INTEGRATION: Final[int] = 8016
    INCIDENT_RESPONSE: Final[int] = 8017
    AUTONOMOUS_INVESTIGATION: Final[int] = 8018
    NARRATIVE_FILTER: Final[int] = 8019

    # Memory & Learning (8020-8029)
    MEMORY_CONSOLIDATION: Final[int] = 8020
    ADAPTIVE_LEARNING: Final[int] = 8021
    PATTERN_RECOGNITION: Final[int] = 8024
    STRATEGIC_PLANNING: Final[int] = 8026

    # Offensive Arsenal (8027-8037)
    NETWORK_RECON: Final[int] = 8028
    WEB_ATTACK: Final[int] = 8032
    C2_ORCHESTRATION: Final[int] = 8033
    BAS: Final[int] = 8034  # Breach and Attack Simulation
    SOCIAL_ENGINEERING: Final[int] = 8035
    PHISHING_SIM: Final[int] = 8036
    VULN_SCANNER: Final[int] = 8037

    # Data Services (8040-8059)
    NEO4J_SERVICE: Final[int] = 8042
    SERIEMA_GRAPH: Final[int] = 8045
    TATACA_INGESTION: Final[int] = 8051

    # Cognitive Services (8080-8089)
    VISUAL_CORTEX: Final[int] = 8080
    AUDITORY_CORTEX: Final[int] = 8081
    SOMATOSENSORY: Final[int] = 8082
    CHEMICAL_SENSING: Final[int] = 8083
    VESTIBULAR: Final[int] = 8084

    # HCL Services (Homeostatic Control Loop) (8090-8094)
    HCL_MONITOR: Final[int] = 8090
    HCL_ANALYZER: Final[int] = 8091
    HCL_PLANNER: Final[int] = 8092
    HCL_EXECUTOR: Final[int] = 8093
    HCL_KB: Final[int] = 8094  # Knowledge Base

    # Immunis Machina Services (8095-8105)
    IMMUNIS_MACROPHAGE: Final[int] = 8095
    IMMUNIS_NEUTROPHIL: Final[int] = 8096
    IMMUNIS_NK_CELL: Final[int] = 8097
    IMMUNIS_BCELL: Final[int] = 8098
    IMMUNIS_CYTOTOXIC_T: Final[int] = 8099
    IMMUNIS_HELPER_T: Final[int] = 8100
    IMMUNIS_DENDRITIC: Final[int] = 8101

    # Maximus Advanced Services (8150-8159)
    MAXIMUS_ORACULO: Final[int] = 8152  # Code oracle
    MAXIMUS_EUREKA: Final[int] = 8153  # Pattern discovery
    MAXIMUS_PREDICT: Final[int] = 8154

    # Neuromodulation Services (8160-8169)
    NEUROMODULATION: Final[int] = 8160
    DOPAMINE_CORE: Final[int] = 8161
    SEROTONIN_CORE: Final[int] = 8162
    NORADRENALINE_CORE: Final[int] = 8163

    # Specialized Services
    AUTH_SERVICE: Final[int] = 8612
    DIGITAL_THALAMUS: Final[int] = 8070
    PREFRONTAL_CORTEX: Final[int] = 8071
    HOMEOSTATIC_REGULATION: Final[int] = 8072
    REFLEX_TRIAGE: Final[int] = 8073
    AI_IMMUNE: Final[int] = 8074
    CLOUD_COORDINATOR: Final[int] = 8075

    # Infrastructure (9000+)
    PROMETHEUS: Final[int] = 9090
    GRAFANA: Final[int] = 3000
    KAFKA: Final[int] = 9092
    ZOOKEEPER: Final[int] = 2181
    NEO4J_BOLT: Final[int] = 7687
    NEO4J_HTTP: Final[int] = 7474
    POSTGRES: Final[int] = 5432
    REDIS: Final[int] = 6379
    QDRANT: Final[int] = 6333


# ============================================================================
# API ENDPOINTS - Common Patterns
# ============================================================================


class APIEndpoints:
    """Standard API endpoint patterns across services."""

    # Health & Status
    HEALTH: Final[str] = "/health"
    READY: Final[str] = "/ready"
    METRICS: Final[str] = "/metrics"

    # Documentation
    DOCS: Final[str] = "/docs"
    REDOC: Final[str] = "/redoc"
    OPENAPI: Final[str] = "/openapi.json"

    # Common CRUD
    LIST: Final[str] = "/"
    CREATE: Final[str] = "/"
    GET_BY_ID: Final[str] = "/{id}"
    UPDATE: Final[str] = "/{id}"
    DELETE: Final[str] = "/{id}"

    # Analysis Endpoints
    ANALYZE: Final[str] = "/analyze"
    SCAN: Final[str] = "/scan"
    QUERY: Final[str] = "/query"
    SEARCH: Final[str] = "/search"

    # Threat Intelligence
    THREAT_LOOKUP: Final[str] = "/threat/{indicator}"
    IOC_SEARCH: Final[str] = "/ioc/search"
    ENRICH: Final[str] = "/enrich"


# ============================================================================
# RESPONSE CODES - Standardized Error/Success Codes
# ============================================================================


class ResponseCodes:
    """Standardized response codes for API responses."""

    # Success Codes
    SUCCESS: Final[str] = "SUCCESS"
    CREATED: Final[str] = "CREATED"
    UPDATED: Final[str] = "UPDATED"
    DELETED: Final[str] = "DELETED"

    # Error Codes - Validation
    VALIDATION_ERROR: Final[str] = "VALIDATION_ERROR"
    INVALID_INPUT: Final[str] = "INVALID_INPUT"
    MISSING_FIELD: Final[str] = "MISSING_FIELD"
    INVALID_FORMAT: Final[str] = "INVALID_FORMAT"

    # Error Codes - Authentication/Authorization
    UNAUTHORIZED: Final[str] = "UNAUTHORIZED"
    FORBIDDEN: Final[str] = "FORBIDDEN"
    TOKEN_EXPIRED: Final[str] = "TOKEN_EXPIRED"
    INVALID_CREDENTIALS: Final[str] = "INVALID_CREDENTIALS"

    # Error Codes - Resources
    NOT_FOUND: Final[str] = "NOT_FOUND"
    ALREADY_EXISTS: Final[str] = "ALREADY_EXISTS"
    CONFLICT: Final[str] = "CONFLICT"

    # Error Codes - Server
    INTERNAL_ERROR: Final[str] = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE: Final[str] = "SERVICE_UNAVAILABLE"
    TIMEOUT: Final[str] = "TIMEOUT"
    DATABASE_ERROR: Final[str] = "DATABASE_ERROR"
    EXTERNAL_API_ERROR: Final[str] = "EXTERNAL_API_ERROR"

    # Error Codes - Business Logic
    INSUFFICIENT_PRIVILEGES: Final[str] = "INSUFFICIENT_PRIVILEGES"
    QUOTA_EXCEEDED: Final[str] = "QUOTA_EXCEEDED"
    RATE_LIMIT_EXCEEDED: Final[str] = "RATE_LIMIT_EXCEEDED"


# ============================================================================
# THREAT LEVELS - Standardized Severity Classification
# ============================================================================


class ThreatLevels:
    """Threat severity levels following NIST 800-61 guidelines."""

    CRITICAL: Final[str] = "CRITICAL"  # Immediate action required
    HIGH: Final[str] = "HIGH"  # Urgent response needed
    MEDIUM: Final[str] = "MEDIUM"  # Response within 24h
    LOW: Final[str] = "LOW"  # Routine handling
    INFO: Final[str] = "INFO"  # Informational only

    # Numeric scores for sorting/filtering
    SCORES: Final[dict] = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1}


# ============================================================================
# SERVICE STATUS - Health Check States
# ============================================================================


class ServiceStatus:
    """Service health status values."""

    HEALTHY: Final[str] = "healthy"
    UNHEALTHY: Final[str] = "unhealthy"
    DEGRADED: Final[str] = "degraded"
    STARTING: Final[str] = "starting"
    STOPPING: Final[str] = "stopping"
    UNKNOWN: Final[str] = "unknown"


# ============================================================================
# MALWARE CLASSIFICATION - MITRE ATT&CK Aligned
# ============================================================================


class MalwareTypes:
    """Malware classification following MITRE ATT&CK."""

    RANSOMWARE: Final[str] = "ransomware"
    TROJAN: Final[str] = "trojan"
    WORM: Final[str] = "worm"
    VIRUS: Final[str] = "virus"
    ROOTKIT: Final[str] = "rootkit"
    SPYWARE: Final[str] = "spyware"
    ADWARE: Final[str] = "adware"
    BOTNET: Final[str] = "botnet"
    RAT: Final[str] = "rat"  # Remote Access Trojan
    KEYLOGGER: Final[str] = "keylogger"
    CRYPTOMINER: Final[str] = "cryptominer"
    BACKDOOR: Final[str] = "backdoor"
    DROPPER: Final[str] = "dropper"
    DOWNLOADER: Final[str] = "downloader"
    EXPLOIT_KIT: Final[str] = "exploit_kit"
    PUP: Final[str] = "pup"  # Potentially Unwanted Program


# ============================================================================
# ATTACK TECHNIQUES - MITRE ATT&CK Tactics
# ============================================================================


class AttackTactics:
    """MITRE ATT&CK tactics."""

    RECONNAISSANCE: Final[str] = "reconnaissance"
    RESOURCE_DEVELOPMENT: Final[str] = "resource_development"
    INITIAL_ACCESS: Final[str] = "initial_access"
    EXECUTION: Final[str] = "execution"
    PERSISTENCE: Final[str] = "persistence"
    PRIVILEGE_ESCALATION: Final[str] = "privilege_escalation"
    DEFENSE_EVASION: Final[str] = "defense_evasion"
    CREDENTIAL_ACCESS: Final[str] = "credential_access"
    DISCOVERY: Final[str] = "discovery"
    LATERAL_MOVEMENT: Final[str] = "lateral_movement"
    COLLECTION: Final[str] = "collection"
    COMMAND_AND_CONTROL: Final[str] = "command_and_control"
    EXFILTRATION: Final[str] = "exfiltration"
    IMPACT: Final[str] = "impact"


# ============================================================================
# NETWORK PROTOCOLS
# ============================================================================


class NetworkProtocols:
    """Common network protocols for scanning/analysis."""

    TCP: Final[str] = "tcp"
    UDP: Final[str] = "udp"
    ICMP: Final[str] = "icmp"
    HTTP: Final[str] = "http"
    HTTPS: Final[str] = "https"
    DNS: Final[str] = "dns"
    FTP: Final[str] = "ftp"
    SSH: Final[str] = "ssh"
    TELNET: Final[str] = "telnet"
    SMTP: Final[str] = "smtp"
    POP3: Final[str] = "pop3"
    IMAP: Final[str] = "imap"
    SMB: Final[str] = "smb"
    RDP: Final[str] = "rdp"
    SNMP: Final[str] = "snmp"


# ============================================================================
# TIME CONSTANTS
# ============================================================================


class TimeConstants:
    """Time-related constants in seconds."""

    SECOND: Final[int] = 1
    MINUTE: Final[int] = 60
    HOUR: Final[int] = 3600
    DAY: Final[int] = 86400
    WEEK: Final[int] = 604800

    # Timeouts
    DEFAULT_TIMEOUT: Final[int] = 30
    LONG_RUNNING_TIMEOUT: Final[int] = 300
    HTTP_TIMEOUT: Final[int] = 10
    DATABASE_TIMEOUT: Final[int] = 5

    # Cache TTLs
    CACHE_SHORT: Final[int] = 300  # 5 minutes
    CACHE_MEDIUM: Final[int] = 3600  # 1 hour
    CACHE_LONG: Final[int] = 86400  # 1 day

    # Retry delays
    RETRY_INITIAL: Final[int] = 1
    RETRY_MAX: Final[int] = 60


# ============================================================================
# DATABASE CONSTANTS
# ============================================================================


class DatabaseNames:
    """Database names for different data stores."""

    # PostgreSQL Databases
    POSTGRES_MAIN: Final[str] = "vertice"
    POSTGRES_AUTH: Final[str] = "vertice_auth"
    POSTGRES_LOGS: Final[str] = "vertice_logs"

    # Neo4j Databases
    NEO4J_THREAT_GRAPH: Final[str] = "threat_graph"
    NEO4J_KNOWLEDGE_BASE: Final[str] = "knowledge_base"

    # Qdrant Collections
    QDRANT_EMBEDDINGS: Final[str] = "threat_embeddings"
    QDRANT_MEMORY: Final[str] = "maximus_memory"

    # Redis Keyspaces
    REDIS_CACHE: Final[int] = 0
    REDIS_SESSIONS: Final[int] = 1
    REDIS_PUBSUB: Final[int] = 2


# ============================================================================
# FILE EXTENSIONS - Supported File Types
# ============================================================================


class FileExtensions:
    """Supported file extensions for analysis."""

    # Executables
    PE: Final[list] = [".exe", ".dll", ".sys", ".scr"]
    ELF: Final[list] = [".elf", ".so", ".bin"]
    MACH_O: Final[list] = [".dylib", ".bundle"]

    # Scripts
    SCRIPTS: Final[list] = [".py", ".ps1", ".sh", ".bat", ".vbs", ".js"]

    # Documents
    OFFICE: Final[list] = [".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]
    PDF: Final[list] = [".pdf"]

    # Archives
    ARCHIVES: Final[list] = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"]

    # Web
    WEB: Final[list] = [".html", ".htm", ".php", ".asp", ".aspx", ".jsp"]


# ============================================================================
# REGEX PATTERNS - Common Validation Patterns
# ============================================================================


class RegexPatterns:
    """Common regex patterns for validation."""

    # Network
    IPV4: Final[str] = (
        r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    IPV6: Final[str] = r"^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|::1|::)$"
    DOMAIN: Final[str] = (
        r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )
    URL: Final[str] = r"^https?://[^\s/$.?#].[^\s]*$"
    EMAIL: Final[str] = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # Hashes
    MD5: Final[str] = r"^[a-fA-F0-9]{32}$"
    SHA1: Final[str] = r"^[a-fA-F0-9]{40}$"
    SHA256: Final[str] = r"^[a-fA-F0-9]{64}$"

    # CVE
    CVE: Final[str] = r"^CVE-\d{4}-\d{4,}$"


# ============================================================================
# SYSTEM LIMITS
# ============================================================================


class SystemLimits:
    """System-wide limits and quotas."""

    # Request Limits
    MAX_REQUEST_SIZE: Final[int] = 100_000_000  # 100MB
    MAX_FILE_UPLOAD: Final[int] = 500_000_000  # 500MB
    MAX_BATCH_SIZE: Final[int] = 1000

    # Rate Limits (per minute)
    RATE_LIMIT_DEFAULT: Final[int] = 100
    RATE_LIMIT_ANALYSIS: Final[int] = 10
    RATE_LIMIT_SCAN: Final[int] = 5

    # Pagination
    PAGE_SIZE_DEFAULT: Final[int] = 50
    PAGE_SIZE_MAX: Final[int] = 1000

    # String Lengths
    MAX_USERNAME_LENGTH: Final[int] = 64
    MAX_EMAIL_LENGTH: Final[int] = 254
    MAX_PASSWORD_LENGTH: Final[int] = 128
    MAX_QUERY_LENGTH: Final[int] = 10000


# ============================================================================
# LOG LEVELS - Following Python logging
# ============================================================================


class LogLevels:
    """Logging levels."""

    DEBUG: Final[str] = "DEBUG"
    INFO: Final[str] = "INFO"
    WARNING: Final[str] = "WARNING"
    ERROR: Final[str] = "ERROR"
    CRITICAL: Final[str] = "CRITICAL"


# ============================================================================
# ENVIRONMENT NAMES
# ============================================================================


class Environments:
    """Environment names."""

    DEVELOPMENT: Final[str] = "development"
    STAGING: Final[str] = "staging"
    PRODUCTION: Final[str] = "production"
    TESTING: Final[str] = "testing"


# ============================================================================
# USER ROLES - RBAC
# ============================================================================


class UserRoles:
    """User roles for Role-Based Access Control."""

    ADMIN: Final[str] = "admin"
    SOC_ANALYST: Final[str] = "soc_analyst"
    SECURITY_ENGINEER: Final[str] = "security_engineer"
    INCIDENT_RESPONDER: Final[str] = "incident_responder"
    THREAT_HUNTER: Final[str] = "threat_hunter"
    READ_ONLY: Final[str] = "read_only"


# Export all constants
__all__ = [
    "ServicePorts",
    "APIEndpoints",
    "ResponseCodes",
    "ThreatLevels",
    "ServiceStatus",
    "MalwareTypes",
    "AttackTactics",
    "NetworkProtocols",
    "TimeConstants",
    "DatabaseNames",
    "FileExtensions",
    "RegexPatterns",
    "SystemLimits",
    "LogLevels",
    "Environments",
    "UserRoles",
]
