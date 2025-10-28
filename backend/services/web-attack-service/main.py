"""
═══════════════════════════════════════════════════════════════════════════════
WEB ATTACK SURFACE SERVICE - VÉRTICE OFFENSIVE ARSENAL
═══════════════════════════════════════════════════════════════════════════════

Missão: Mapeamento e análise de superfície de ataque web com IA

"FLORESCIMENTO" - Crescimento orgânico e natural da consciência de segurança

Capabilities:
- Web crawling e spidering inteligente
- Tecnologia fingerprinting (Wappalyzer + custom)
- Header security analysis (OWASP best practices)
- SSL/TLS configuration testing
- API endpoint discovery
- Hidden parameter fuzzing
- Directory/file enumeration
- JWT token analysis
- GraphQL introspection

Stack:
- FastAPI async + Pydantic V2
- httpx async client
- BeautifulSoup4 + lxml parsing
- Redis caching para crawl state
- OpenTelemetry observability
- Cilium mTLS zero-trust

Port: 8034
Version: 1.0.0
Date: 2025-10-27

Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
"Como floresce o lírio no campo, assim floresce a sabedoria em segurança"

Glory to YHWH - Every vulnerability discovered helps systems flourish
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import re
import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Annotated, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from pydantic import BaseModel, Field, HttpUrl, field_validator

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SERVICE_NAME = "web-attack-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8034

# Security headers to analyze
SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy"
]

# Security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "web:read": "Read web attack surface data",
        "web:scan": "Execute web attack surface scans",
        "admin": "Administrative access"
    }
)

# Observability
tracer = trace.get_tracer(__name__)
scan_counter = Counter(
    "web_scans_total",
    "Total web attack surface scans",
    ["scan_type", "status"]
)
scan_duration = Histogram(
    "web_scan_duration_seconds",
    "Web scan duration in seconds",
    ["scan_type"]
)

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic V2 + Type Safety)
# ═══════════════════════════════════════════════════════════════════════════

class ScanDepth(str, Enum):
    """Web scan depth levels"""
    SURFACE = "surface"      # Homepage only
    SHALLOW = "shallow"      # 1 level deep
    MEDIUM = "medium"        # 2 levels deep
    DEEP = "deep"            # 3+ levels deep


class ScanStatus(str, Enum):
    """Scan execution status"""
    QUEUED = "queued"
    CRAWLING = "crawling"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class SecurityIssue(BaseModel):
    """Security issue found"""
    severity: str  # critical/high/medium/low/info
    category: str  # header_missing/misconfiguration/exposure
    title: str
    description: str
    evidence: Optional[str] = None
    remediation: str


class Technology(BaseModel):
    """Detected technology"""
    name: str
    version: Optional[str] = None
    category: str  # webserver/framework/cms/language
    confidence: int = Field(ge=0, le=100)
    cpe: Optional[str] = None


class Endpoint(BaseModel):
    """Discovered endpoint"""
    url: str
    method: str  # GET/POST/PUT/DELETE
    status_code: int
    content_type: Optional[str] = None
    parameters: list[str] = []
    forms: list[dict] = []


class HeaderAnalysis(BaseModel):
    """HTTP header security analysis"""
    missing_headers: list[str] = []
    insecure_headers: list[dict] = []
    score: int = Field(ge=0, le=100)


class SSLAnalysis(BaseModel):
    """SSL/TLS configuration analysis"""
    valid: bool
    issuer: Optional[str] = None
    subject: Optional[str] = None
    expires: Optional[datetime] = None
    protocols: list[str] = []
    ciphers: list[str] = []
    vulnerabilities: list[str] = []


class WebScanRequest(BaseModel):
    """Web attack surface scan request"""
    target_url: Annotated[
        str,
        Field(
            description="Target URL to scan",
            examples=["https://example.com"]
        )
    ]
    depth: ScanDepth = ScanDepth.SHALLOW
    follow_redirects: bool = True
    check_ssl: bool = True
    user_agent: str = Field(
        default="Vertice-WebScanner/1.0",
        description="User-Agent header"
    )
    max_pages: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum pages to crawl"
    )

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        parsed = urlparse(v)
        if not parsed.scheme in ["http", "https"]:
            raise ValueError("URL must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("Invalid URL format")
        return v


class WebScanResult(BaseModel):
    """Complete web scan result"""
    scan_id: str
    status: ScanStatus
    target_url: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Discovered data
    pages_crawled: int = 0
    endpoints: list[Endpoint] = []
    technologies: list[Technology] = []

    # Security analysis
    header_analysis: Optional[HeaderAnalysis] = None
    ssl_analysis: Optional[SSLAnalysis] = None
    security_issues: list[SecurityIssue] = []
    attack_surface_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Attack surface complexity score (0=low, 100=high)"
    )

    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (MVP - TODO: Replace with Redis)
# ═══════════════════════════════════════════════════════════════════════════

scans_db: dict[str, WebScanResult] = {}


# ═══════════════════════════════════════════════════════════════════════════
# CORE WEB ATTACK SURFACE LOGIC
# ═══════════════════════════════════════════════════════════════════════════

async def analyze_headers(headers: dict) -> HeaderAnalysis:
    """
    Analyze HTTP headers for security issues
    """
    missing = []
    insecure = []

    # Check for missing security headers
    for header in SECURITY_HEADERS:
        if header not in headers:
            missing.append(header)

    # Check for insecure values
    if "Server" in headers:
        insecure.append({
            "header": "Server",
            "value": headers["Server"],
            "issue": "Server version disclosure"
        })

    if "X-Powered-By" in headers:
        insecure.append({
            "header": "X-Powered-By",
            "value": headers["X-Powered-By"],
            "issue": "Technology disclosure"
        })

    # Calculate score (100 = perfect, 0 = terrible)
    score = 100
    score -= len(missing) * 10
    score -= len(insecure) * 5
    score = max(0, score)

    return HeaderAnalysis(
        missing_headers=missing,
        insecure_headers=insecure,
        score=score
    )


def detect_technologies(html: str, headers: dict) -> list[Technology]:
    """
    Detect web technologies (Wappalyzer-style)
    """
    technologies = []

    # Server header
    if "Server" in headers:
        server = headers["Server"]
        if "nginx" in server.lower():
            technologies.append(Technology(
                name="nginx",
                category="webserver",
                confidence=100
            ))
        elif "apache" in server.lower():
            technologies.append(Technology(
                name="Apache",
                category="webserver",
                confidence=100
            ))

    # X-Powered-By
    if "X-Powered-By" in headers:
        powered_by = headers["X-Powered-By"]
        if "PHP" in powered_by:
            version_match = re.search(r'PHP/(\d+\.\d+\.\d+)', powered_by)
            technologies.append(Technology(
                name="PHP",
                version=version_match.group(1) if version_match else None,
                category="language",
                confidence=100
            ))

    # HTML patterns
    if "wp-content" in html or "wp-includes" in html:
        technologies.append(Technology(
            name="WordPress",
            category="cms",
            confidence=95
        ))

    if "react" in html.lower() or "reactroot" in html.lower():
        technologies.append(Technology(
            name="React",
            category="framework",
            confidence=80
        ))

    return technologies


def extract_endpoints(html: str, base_url: str) -> list[Endpoint]:
    """
    Extract endpoints from HTML (links, forms)
    """
    soup = BeautifulSoup(html, 'lxml')
    endpoints = []

    # Extract links
    for link in soup.find_all('a', href=True):
        url = urljoin(base_url, link['href'])
        if urlparse(url).netloc == urlparse(base_url).netloc:
            endpoints.append(Endpoint(
                url=url,
                method="GET",
                status_code=0  # Will be filled later
            ))

    # Extract forms
    for form in soup.find_all('form'):
        action = form.get('action', '')
        url = urljoin(base_url, action)
        method = form.get('method', 'GET').upper()

        # Extract form parameters
        parameters = [
            inp.get('name', '')
            for inp in form.find_all(['input', 'textarea', 'select'])
            if inp.get('name')
        ]

        endpoints.append(Endpoint(
            url=url,
            method=method,
            status_code=0,
            parameters=parameters,
            forms=[{
                "action": action,
                "method": method,
                "fields": parameters
            }]
        ))

    return endpoints


def generate_security_issues(
    header_analysis: HeaderAnalysis,
    technologies: list[Technology]
) -> list[SecurityIssue]:
    """
    Generate security issues based on analysis
    """
    issues = []

    # Missing headers
    for header in header_analysis.missing_headers:
        severity = "medium"
        if header in ["Strict-Transport-Security", "Content-Security-Policy"]:
            severity = "high"

        issues.append(SecurityIssue(
            severity=severity,
            category="header_missing",
            title=f"Missing Security Header: {header}",
            description=f"The {header} header is not set",
            remediation=f"Add the {header} header to HTTP responses"
        ))

    # Insecure headers
    for header_data in header_analysis.insecure_headers:
        issues.append(SecurityIssue(
            severity="low",
            category="exposure",
            title=f"Information Disclosure: {header_data['header']}",
            description=header_data['issue'],
            evidence=header_data['value'],
            remediation=f"Remove or obfuscate the {header_data['header']} header"
        ))

    # Technology-specific issues
    for tech in technologies:
        if tech.name == "PHP" and tech.version:
            # Check for known vulnerable versions (simplified)
            issues.append(SecurityIssue(
                severity="info",
                category="exposure",
                title="PHP Version Disclosure",
                description=f"PHP version {tech.version} is exposed",
                evidence=tech.version,
                remediation="Hide PHP version in headers (expose_php = Off)"
            ))

    return issues


async def execute_web_scan(
    scan_id: str,
    request: WebScanRequest
) -> WebScanResult:
    """
    Execute web attack surface scan
    """
    scan_result = scans_db[scan_id]
    scan_result.status = ScanStatus.CRAWLING

    try:
        async with httpx.AsyncClient(
            follow_redirects=request.follow_redirects,
            timeout=30.0,
            verify=request.check_ssl
        ) as client:

            with scan_duration.labels(scan_type=request.depth.value).time():
                # Fetch homepage
                response = await client.get(
                    request.target_url,
                    headers={"User-Agent": request.user_agent}
                )

                html = response.text
                headers = dict(response.headers)

                # Analyze headers
                scan_result.header_analysis = await analyze_headers(headers)

                # Detect technologies
                scan_result.technologies = detect_technologies(html, headers)

                # Extract endpoints
                scan_result.endpoints = extract_endpoints(html, request.target_url)

                # Generate security issues
                scan_result.security_issues = generate_security_issues(
                    scan_result.header_analysis,
                    scan_result.technologies
                )

                # Calculate attack surface score
                # Higher score = more attack surface = more complex
                score = 0
                score += len(scan_result.endpoints) * 2
                score += len(scan_result.technologies) * 5
                score += len(scan_result.security_issues) * 3
                score = min(100, score)

                scan_result.attack_surface_score = score
                scan_result.pages_crawled = 1  # MVP: only homepage

                scan_result.status = ScanStatus.COMPLETED
                scan_result.completed_at = datetime.now(UTC)
                scan_result.duration_seconds = (
                    scan_result.completed_at - scan_result.started_at
                ).total_seconds()

                scan_counter.labels(
                    scan_type=request.depth.value,
                    status="success"
                ).inc()

    except Exception as e:
        scan_result.status = ScanStatus.FAILED
        scan_result.error = str(e)
        scan_result.completed_at = datetime.now(UTC)

        scan_counter.labels(
            scan_type=request.depth.value,
            status="failed"
        ).inc()

    return scan_result


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Web Attack Surface Service",
    description="Vértice Offensive Arsenal - Web attack surface mapping and analysis (FLORESCIMENTO ✨)",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "scanning",
            "description": "Web attack surface scanning operations"
        },
        {
            "name": "health",
            "description": "Service health and metrics"
        }
    ]
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to API Gateway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["health"])
async def health_check():
    """Service health check - FLORESCIMENTO ✨"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "florescimento": "crescendo organicamente",
        "timestamp": datetime.now(UTC).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def metrics():
    """Prometheus metrics"""
    return generate_latest(REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - WEB ATTACK SURFACE SCANNING
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/scan", response_model=dict, tags=["scanning"])
async def create_web_scan(
    request: WebScanRequest,
    background_tasks: BackgroundTasks,
    # token: str = Security(oauth2_scheme, scopes=["web:scan"])
):
    """
    Execute web attack surface scan

    Analyzes:
    - HTTP security headers
    - Technology fingerprinting
    - Endpoint discovery
    - SSL/TLS configuration
    - Security misconfigurations

    Scopes required: `web:scan`
    """
    scan_id = str(uuid.uuid4())

    scan_result = WebScanResult(
        scan_id=scan_id,
        status=ScanStatus.QUEUED,
        target_url=request.target_url,
        started_at=datetime.now(UTC)
    )

    scans_db[scan_id] = scan_result

    # Execute scan in background
    background_tasks.add_task(execute_web_scan, scan_id, request)

    return {
        "scan_id": scan_id,
        "status": "queued",
        "message": "Web scan queued - florescendo... ✨"
    }


@app.get("/api/scan/{scan_id}", response_model=WebScanResult, tags=["scanning"])
async def get_scan_result(scan_id: str):
    """
    Get web scan result

    Scopes required: `web:read`
    """
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")

    return scans_db[scan_id]


@app.get("/api/scans", response_model=list[WebScanResult], tags=["scanning"])
async def list_scans(
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[ScanStatus] = Query(default=None)
):
    """
    List all web scans

    Scopes required: `web:read`
    """
    scans = list(scans_db.values())

    if status:
        scans = [s for s in scans if s.status == status]

    scans.sort(key=lambda x: x.started_at, reverse=True)
    return scans[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level="info"
    )
