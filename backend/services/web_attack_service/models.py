# ============================================================================
# WEB APPLICATION ATTACK SERVICE - Data Models
# AI-Powered Web Security Testing: Burp Suite + OWASP ZAP
# ============================================================================

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class AttackEngine(str, Enum):
    """Attack engine type"""

    BURP_SUITE = "burp_suite"
    OWASP_ZAP = "owasp_zap"
    BOTH = "both"


class ScanType(str, Enum):
    """Web scan type"""

    PASSIVE = "passive"
    ACTIVE = "active"
    SPIDER = "spider"
    AJAX_SPIDER = "ajax_spider"
    API_SCAN = "api_scan"
    AUTHENTICATED = "authenticated"


class VulnerabilityType(str, Enum):
    """OWASP Top 10 vulnerability types"""

    SQLI = "sql_injection"
    XSS = "cross_site_scripting"
    BROKEN_AUTH = "broken_authentication"
    SENSITIVE_DATA = "sensitive_data_exposure"
    XXE = "xml_external_entities"
    BROKEN_ACCESS = "broken_access_control"
    SECURITY_MISCONFIG = "security_misconfiguration"
    XSS_STORED = "stored_xss"
    INSECURE_DESERIAL = "insecure_deserialization"
    VULN_COMPONENTS = "vulnerable_components"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    SSRF = "server_side_request_forgery"
    CSRF = "cross_site_request_forgery"
    IDOR = "insecure_direct_object_reference"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    LDAP_INJECTION = "ldap_injection"
    NOSQL_INJECTION = "nosql_injection"


class AIProvider(str, Enum):
    """AI provider for Co-Pilot"""

    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    AUTO = "auto"  # Fallback logic


class Severity(str, Enum):
    """Finding severity"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================================================
# BURP SUITE MODELS
# ============================================================================


class BurpScanConfig(BaseModel):
    """Burp Suite scan configuration"""

    scan_type: ScanType = ScanType.ACTIVE
    crawl_depth: int = Field(default=3, ge=1, le=10)
    max_crawl_time: int = Field(default=600, description="Seconds")

    # Audit configuration
    audit_checks: List[VulnerabilityType] = Field(
        default=[
            VulnerabilityType.SQLI,
            VulnerabilityType.XSS,
            VulnerabilityType.SSRF,
            VulnerabilityType.XXE,
        ]
    )

    # Performance
    thread_count: int = Field(default=10, ge=1, le=50)
    throttle_ms: int = Field(default=0, ge=0, le=5000)


class BurpScanRequest(BaseModel):
    """Burp Suite scan request"""

    target_url: HttpUrl
    config: BurpScanConfig = BurpScanConfig()

    # Authentication
    auth_type: Optional[str] = Field(default=None, description="basic, bearer, cookie")
    auth_credentials: Optional[Dict[str, str]] = None

    # Session handling
    session_cookies: Optional[Dict[str, str]] = None
    custom_headers: Optional[Dict[str, str]] = None

    # AI Co-Pilot
    enable_ai_copilot: bool = Field(default=True)
    ai_provider: AIProvider = AIProvider.AUTO


class BurpVulnerability(BaseModel):
    """Burp Suite vulnerability finding"""

    issue_type: str
    issue_name: str
    severity: Severity
    confidence: str  # certain, firm, tentative

    # Location
    url: str
    path: str
    method: str
    parameter: Optional[str] = None

    # Evidence
    request: str
    response: str
    evidence: Optional[str] = None

    # AI-generated insights
    ai_analysis: Optional[Dict] = Field(default=None, description="AI Co-Pilot analysis")
    ai_recommendations: Optional[List[str]] = None

    timestamp: datetime


class BurpScanResult(BaseModel):
    """Burp Suite scan result"""

    scan_id: str
    target_url: str
    scan_type: ScanType

    vulnerabilities_found: int
    findings: List[BurpVulnerability]

    # Statistics
    requests_made: int
    pages_crawled: int
    scan_duration: float

    timestamp: datetime


# ============================================================================
# OWASP ZAP MODELS
# ============================================================================


class ZAPScanPolicy(BaseModel):
    """ZAP scan policy"""

    policy_name: str = Field(default="API-Security", description="Scan policy name")

    # Attack strength
    attack_strength: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, INSANE")
    alert_threshold: str = Field(default="MEDIUM", description="OFF, LOW, MEDIUM, HIGH")

    # Scan rules
    enabled_scanners: List[int] = Field(default=[], description="Scanner IDs (empty = all)")


class ZAPScanRequest(BaseModel):
    """OWASP ZAP scan request"""

    target_url: HttpUrl
    scan_type: ScanType = ScanType.ACTIVE
    policy: ZAPScanPolicy = ZAPScanPolicy()

    # Context
    context_name: Optional[str] = "default"
    include_in_context: Optional[List[str]] = None  # URL patterns
    exclude_from_context: Optional[List[str]] = None

    # Authentication
    auth_method: Optional[str] = None  # form, script, json, http
    login_url: Optional[HttpUrl] = None
    username: Optional[str] = None
    password: Optional[str] = None

    # Advanced
    max_children: int = Field(default=0, description="Max child nodes (0=unlimited)")
    recurse: bool = Field(default=True)
    subtree_only: bool = Field(default=False)


class ZAPAlert(BaseModel):
    """ZAP alert/vulnerability"""

    alert_id: int
    plugin_id: int
    alert_name: str
    risk: Severity
    confidence: str  # High, Medium, Low, Falsepositive

    # Location
    url: str
    method: str
    param: Optional[str] = None
    attack: Optional[str] = None
    evidence: Optional[str] = None

    # Details
    description: str
    solution: str
    reference: str
    cwe_id: Optional[int] = None
    wasc_id: Optional[int] = None

    timestamp: datetime


class ZAPScanResult(BaseModel):
    """ZAP scan result"""

    scan_id: str
    target_url: str
    scan_type: ScanType

    alerts_count: int
    alerts: List[ZAPAlert]

    # Statistics
    urls_found: int
    scan_duration: float

    timestamp: datetime


# ============================================================================
# AI CO-PILOT MODELS
# ============================================================================


class AICoPilotRequest(BaseModel):
    """AI Co-Pilot analysis request"""

    vulnerability_context: Dict[str, Any]
    request_structure: Dict[str, Any]
    attack_type: VulnerabilityType

    # AI settings
    provider: AIProvider = AIProvider.AUTO
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)


class AIGeneratedPayload(BaseModel):
    """AI-generated attack payload"""

    payload: str
    payload_type: VulnerabilityType
    explanation: str
    risk_level: Severity

    # Validation
    prefrontal_cortex_approved: bool = Field(default=False)
    destructiveness_score: float = Field(default=0.0, ge=0.0, le=1.0)


class AICoPilotResponse(BaseModel):
    """AI Co-Pilot response"""

    analysis: str
    attack_vectors: List[AIGeneratedPayload]
    recommendations: List[str]

    # Metadata
    provider_used: AIProvider
    tokens_used: int
    confidence: float
    timestamp: datetime


# ============================================================================
# SMART FUZZING MODELS
# ============================================================================


class FuzzingTarget(BaseModel):
    """Fuzzing target specification"""

    url: HttpUrl
    method: str = Field(default="POST", description="GET, POST, PUT, DELETE, etc")

    # Parameters to fuzz
    query_params: Optional[Dict[str, str]] = None
    body_params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None

    # Fuzzing points
    fuzz_points: List[str] = Field(..., description="Parameter names to fuzz")


class FuzzingStrategy(str, Enum):
    """Fuzzing strategy"""

    MUTATION = "mutation"  # Mutate existing values
    GENERATION = "generation"  # Generate new values
    DICTIONARY = "dictionary"  # Use wordlists
    AI_POWERED = "ai_powered"  # AI-generated payloads


class FuzzingConfig(BaseModel):
    """Fuzzing configuration"""

    strategy: FuzzingStrategy = FuzzingStrategy.AI_POWERED
    max_iterations: int = Field(default=1000, ge=1, le=10000)

    # AI fuzzing
    ai_provider: AIProvider = AIProvider.AUTO
    context_aware: bool = Field(default=True, description="Use AI for context-aware fuzzing")

    # Performance
    concurrent_requests: int = Field(default=10, ge=1, le=100)
    delay_ms: int = Field(default=100, ge=0, le=5000)


class FuzzingRequest(BaseModel):
    """Smart fuzzing request"""

    target: FuzzingTarget
    config: FuzzingConfig = FuzzingConfig()

    # Vulnerability focus
    target_vulns: List[VulnerabilityType] = Field(default=[VulnerabilityType.SQLI, VulnerabilityType.XSS])


class FuzzingResult(BaseModel):
    """Fuzzing result"""

    fuzzing_id: str
    target_url: str

    # Results
    total_requests: int
    anomalies_found: int
    vulnerabilities: List[Dict[str, Any]]

    # AI insights
    ai_analysis: Optional[str] = None

    duration: float
    timestamp: datetime


# ============================================================================
# UNIFIED WEB ATTACK MODELS
# ============================================================================


class UnifiedWebAttackRequest(BaseModel):
    """Unified web application attack request"""

    target_url: HttpUrl

    # Engine selection
    engines: List[AttackEngine] = Field(default=[AttackEngine.BURP_SUITE])

    # Scan configuration
    scan_types: List[ScanType] = Field(default=[ScanType.ACTIVE])

    # Authentication
    auth_type: Optional[str] = None
    auth_credentials: Optional[Dict[str, str]] = None

    # AI Co-Pilot
    enable_ai_copilot: bool = Field(default=True)
    ai_provider: AIProvider = AIProvider.AUTO

    # Fuzzing
    enable_fuzzing: bool = Field(default=True)
    fuzzing_targets: Optional[List[FuzzingTarget]] = None

    # ASA Integration
    enable_asa_integration: bool = Field(default=True)


class UnifiedVulnerability(BaseModel):
    """Unified vulnerability finding"""

    vuln_id: str
    source_engine: AttackEngine

    vuln_type: VulnerabilityType
    severity: Severity
    confidence: str

    # Location
    url: str
    method: str
    parameter: Optional[str] = None

    # Evidence
    request: Optional[str] = None
    response: Optional[str] = None
    payload: Optional[str] = None

    # AI insights
    ai_analysis: Optional[Dict] = None
    ai_remediation: Optional[str] = None

    # ASA validation
    prefrontal_cortex_validated: bool = Field(default=False)
    auditory_cortex_analysis: Optional[Dict] = None

    timestamp: datetime


class UnifiedWebAttackResult(BaseModel):
    """Unified web attack result"""

    scan_id: str
    target_url: str
    engines_used: List[AttackEngine]

    # Results
    total_vulnerabilities: int
    vulnerabilities_by_severity: Dict[str, int]
    findings: List[UnifiedVulnerability]

    # Engine-specific results
    burp_result: Optional[BurpScanResult] = None
    zap_result: Optional[ZAPScanResult] = None
    fuzzing_result: Optional[FuzzingResult] = None

    # AI Co-Pilot summary
    ai_executive_summary: Optional[str] = None
    ai_recommendations: Optional[List[str]] = None

    # Timing
    total_duration: float
    timestamp: datetime


# ============================================================================
# ASA INTEGRATION MODELS
# ============================================================================


class PrefrontalCortexRequest(BaseModel):
    """Prefrontal Cortex impulse inhibition request"""

    action: str = "web_attack"
    payload: Dict[str, Any]
    destructiveness_score: float


class PrefrontalCortexResponse(BaseModel):
    """Prefrontal Cortex response"""

    approved: bool
    reasoning: str
    alternative_action: Optional[str] = None


class AuditoryCortexRequest(BaseModel):
    """Auditory Cortex C2 beacon detection request"""

    http_traffic: Dict[str, Any]
    request_pattern: str


class AuditoryCortexResponse(BaseModel):
    """Auditory Cortex response"""

    c2_detected: bool
    beacon_type: Optional[str] = None
    confidence: float
    threat_level: str
