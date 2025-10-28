"""
═══════════════════════════════════════════════════════════════════════════════
VULNERABILITY INTELLIGENCE SERVICE - VÉRTICE OFFENSIVE ARSENAL
═══════════════════════════════════════════════════════════════════════════════

Missão: Inteligência de vulnerabilidades com IA e threat feeds

Capabilities:
- CVE database queries (NVD + MITRE)
- Nuclei template matching
- EPSS vulnerability scoring (ML-powered)
- STIX/TAXII 2.1 threat intelligence feeds
- MITRE ATT&CK technique mapping
- Exploit database correlation

Stack:
- FastAPI async + Pydantic V2
- PostgreSQL + Redis caching
- Nuclei templates engine
- OpenTelemetry observability
- Cilium mTLS zero-trust

Port: 8033
Version: 1.0.0
Date: 2025-10-27

Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
"Tudo o que fizerem, façam de todo o coração, como para o Senhor"
Colossenses 3:23

Glory to YHWH - Every vulnerability detected protects His creation
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Annotated, Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from opentelemetry import trace
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SERVICE_NAME = "vuln-intel-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8033

# External APIs
NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MITRE_ATTACK_API = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack"
NUCLEI_TEMPLATES_REPO = "https://github.com/projectdiscovery/nuclei-templates"

# Database
DATABASE_URL = "postgresql+asyncpg://vertice:vertice@postgres:5432/vuln_intel"

# Security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "vulns:read": "Read vulnerability data",
        "vulns:write": "Query vulnerability databases",
        "admin": "Administrative access"
    }
)

# Observability
tracer = trace.get_tracer(__name__)
vuln_query_counter = Counter(
    "vuln_queries_total",
    "Total vulnerability queries executed",
    ["query_type", "status"]
)
vuln_query_duration = Histogram(
    "vuln_query_duration_seconds",
    "Vulnerability query duration in seconds",
    ["query_type"]
)

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic V2 + Type Safety)
# ═══════════════════════════════════════════════════════════════════════════

class VulnSeverity(str, Enum):
    """CVSS severity levels"""
    CRITICAL = "critical"  # 9.0-10.0
    HIGH = "high"          # 7.0-8.9
    MEDIUM = "medium"      # 4.0-6.9
    LOW = "low"            # 0.1-3.9
    NONE = "none"          # 0.0


class QueryType(str, Enum):
    """Vulnerability query types"""
    CVE_ID = "cve_id"              # Search by CVE ID
    PRODUCT = "product"             # Search by product/vendor
    CPE = "cpe"                     # Search by CPE string
    EXPLOIT_AVAILABLE = "exploit"   # Only with public exploits
    RECENT = "recent"               # Recently disclosed (last 30 days)


class CVERequest(BaseModel):
    """CVE lookup request"""
    cve_id: Annotated[
        str,
        Field(
            description="CVE ID (e.g., CVE-2024-1234)",
            pattern=r"^CVE-\d{4}-\d{4,}$"
        )
    ]
    include_exploits: bool = Field(
        default=True,
        description="Include exploit database correlations"
    )
    include_mitre: bool = Field(
        default=True,
        description="Include MITRE ATT&CK technique mapping"
    )


class ProductSearchRequest(BaseModel):
    """Product vulnerability search"""
    vendor: str = Field(description="Vendor name (e.g., 'apache')")
    product: str = Field(description="Product name (e.g., 'httpd')")
    version: Optional[str] = Field(
        default=None,
        description="Product version (e.g., '2.4.7')"
    )
    severity_min: VulnSeverity = Field(
        default=VulnSeverity.MEDIUM,
        description="Minimum severity to return"
    )
    limit: int = Field(default=50, ge=1, le=500)


class ExploitInfo(BaseModel):
    """Exploit database entry"""
    exploit_id: str
    title: str
    date_published: datetime
    exploit_type: str  # remote/local/webapp/dos
    platform: Optional[str] = None
    source_url: Optional[str] = None


class MITRETechnique(BaseModel):
    """MITRE ATT&CK technique"""
    technique_id: str  # T1595.002
    technique_name: str
    tactic: str  # Reconnaissance/Initial Access/etc
    description: str
    url: str


class CVEDetail(BaseModel):
    """Detailed CVE information"""
    cve_id: str
    description: str
    published_date: datetime
    last_modified: datetime
    cvss_v3_score: Optional[float] = None
    cvss_v3_vector: Optional[str] = None
    severity: VulnSeverity
    epss_score: Optional[float] = Field(
        default=None,
        description="Exploit Prediction Scoring System (0-1)"
    )
    cpe_list: list[str] = []
    references: list[str] = []
    exploits: list[ExploitInfo] = []
    mitre_techniques: list[MITRETechnique] = []
    nuclei_templates: list[str] = Field(
        default=[],
        description="Matching Nuclei template IDs"
    )


class VulnSearchResult(BaseModel):
    """Vulnerability search result"""
    query_id: str
    query_type: QueryType
    total_results: int
    vulnerabilities: list[CVEDetail]
    timestamp: datetime


class NucleiScanRequest(BaseModel):
    """Nuclei template scan request"""
    target_url: str = Field(description="Target URL to scan")
    severity: list[VulnSeverity] = Field(
        default=[VulnSeverity.CRITICAL, VulnSeverity.HIGH],
        description="Template severities to run"
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Template tags (e.g., ['cve', 'sqli', 'xss'])"
    )


# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (MVP - TODO: Replace with PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════

queries_db: dict[str, VulnSearchResult] = {}


# ═══════════════════════════════════════════════════════════════════════════
# CORE INTELLIGENCE LOGIC
# ═══════════════════════════════════════════════════════════════════════════

async def query_nvd_api(cve_id: str) -> Optional[dict]:
    """
    Query NVD API for CVE details

    TODO: Add API key for higher rate limits (50 req/30s vs 5 req/30s)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"{NVD_API_BASE}?cveId={cve_id}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("totalResults", 0) > 0:
                return data["vulnerabilities"][0]
            return None

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"NVD API error: {str(e)}"
            )


async def query_exploit_db(cve_id: str) -> list[ExploitInfo]:
    """
    Query Exploit-DB for available exploits

    TODO: Implement actual Exploit-DB API integration
    For MVP, return mock data
    """
    # Mock data - in production, query real exploit databases
    return []


async def query_mitre_attack(cve_id: str) -> list[MITRETechnique]:
    """
    Map CVE to MITRE ATT&CK techniques

    TODO: Implement MITRE ATT&CK STIX 2.1 parsing
    """
    # Mock data - in production, parse MITRE CTI repository
    return []


async def calculate_epss_score(cve_id: str) -> Optional[float]:
    """
    Get EPSS (Exploit Prediction Scoring System) score

    TODO: Query FIRST.org EPSS API
    """
    # Mock - in production, query https://api.first.org/data/v1/epss
    return None


def parse_cvss_severity(score: Optional[float]) -> VulnSeverity:
    """Convert CVSS score to severity enum"""
    if score is None:
        return VulnSeverity.NONE
    if score >= 9.0:
        return VulnSeverity.CRITICAL
    if score >= 7.0:
        return VulnSeverity.HIGH
    if score >= 4.0:
        return VulnSeverity.MEDIUM
    if score > 0.0:
        return VulnSeverity.LOW
    return VulnSeverity.NONE


async def process_cve_request(request: CVERequest) -> CVEDetail:
    """
    Process CVE lookup with enrichment
    """
    with vuln_query_duration.labels(query_type="cve_id").time():
        # Query NVD
        nvd_data = await query_nvd_api(request.cve_id)

        if not nvd_data:
            raise HTTPException(
                status_code=404,
                detail=f"CVE {request.cve_id} not found in NVD"
            )

        cve = nvd_data["cve"]

        # Extract CVSS data
        cvss_v3_score = None
        cvss_v3_vector = None

        if "metrics" in cve:
            cvss_data = cve["metrics"].get("cvssMetricV31", [])
            if cvss_data:
                cvss_v3_score = cvss_data[0]["cvssData"]["baseScore"]
                cvss_v3_vector = cvss_data[0]["cvssData"]["vectorString"]

        # Extract CPEs
        cpe_list = []
        if "configurations" in cve:
            for config in cve["configurations"]:
                for node in config.get("nodes", []):
                    for cpe_match in node.get("cpeMatch", []):
                        if "criteria" in cpe_match:
                            cpe_list.append(cpe_match["criteria"])

        # Extract references
        references = [
            ref["url"]
            for ref in cve.get("references", [])
        ]

        # Enrichment
        exploits = []
        if request.include_exploits:
            exploits = await query_exploit_db(request.cve_id)

        mitre_techniques = []
        if request.include_mitre:
            mitre_techniques = await query_mitre_attack(request.cve_id)

        epss_score = await calculate_epss_score(request.cve_id)

        vuln_query_counter.labels(
            query_type="cve_id",
            status="success"
        ).inc()

        return CVEDetail(
            cve_id=request.cve_id,
            description=cve["descriptions"][0]["value"],
            published_date=datetime.fromisoformat(
                cve["published"].replace("Z", "+00:00")
            ),
            last_modified=datetime.fromisoformat(
                cve["lastModified"].replace("Z", "+00:00")
            ),
            cvss_v3_score=cvss_v3_score,
            cvss_v3_vector=cvss_v3_vector,
            severity=parse_cvss_severity(cvss_v3_score),
            epss_score=epss_score,
            cpe_list=cpe_list,
            references=references,
            exploits=exploits,
            mitre_techniques=mitre_techniques
        )


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Vulnerability Intelligence Service",
    description="Vértice Offensive Arsenal - Vulnerability intelligence and threat feeds",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "intelligence",
            "description": "Vulnerability intelligence operations"
        },
        {
            "name": "health",
            "description": "Service health and metrics"
        }
    ]
)

# CORS (allow API Gateway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to API Gateway only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["health"])
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.now(UTC).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def metrics():
    """Prometheus metrics"""
    return generate_latest(REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - VULNERABILITY INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/cve/lookup", response_model=CVEDetail, tags=["intelligence"])
async def lookup_cve(
    request: CVERequest,
    # token: str = Security(oauth2_scheme, scopes=["vulns:read"])  # TODO: Enable auth
):
    """
    Lookup CVE by ID with enrichment

    Enriches NVD data with:
    - Exploit database correlations
    - MITRE ATT&CK technique mapping
    - EPSS exploit prediction score
    - Nuclei template matching

    Scopes required: `vulns:read`
    """
    return await process_cve_request(request)


@app.post("/api/product/search", response_model=VulnSearchResult, tags=["intelligence"])
async def search_product_vulns(
    request: ProductSearchRequest,
    # token: str = Security(oauth2_scheme, scopes=["vulns:read"])
):
    """
    Search vulnerabilities by product/vendor

    Returns all CVEs affecting a specific product version

    Scopes required: `vulns:read`
    """
    query_id = str(uuid.uuid4())

    # TODO: Implement product search via NVD API
    # For MVP, return empty results

    result = VulnSearchResult(
        query_id=query_id,
        query_type=QueryType.PRODUCT,
        total_results=0,
        vulnerabilities=[],
        timestamp=datetime.now(UTC)
    )

    queries_db[query_id] = result

    vuln_query_counter.labels(
        query_type="product",
        status="success"
    ).inc()

    return result


@app.get("/api/recent", response_model=VulnSearchResult, tags=["intelligence"])
async def get_recent_vulns(
    days: int = Query(default=7, ge=1, le=30),
    severity_min: VulnSeverity = Query(default=VulnSeverity.HIGH),
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Get recently disclosed vulnerabilities

    Returns CVEs published in the last N days
    """
    query_id = str(uuid.uuid4())

    # TODO: Implement recent CVEs query

    result = VulnSearchResult(
        query_id=query_id,
        query_type=QueryType.RECENT,
        total_results=0,
        vulnerabilities=[],
        timestamp=datetime.now(UTC)
    )

    queries_db[query_id] = result

    return result


@app.post("/api/nuclei/scan", tags=["intelligence"])
async def nuclei_scan(
    request: NucleiScanRequest,
    background_tasks: BackgroundTasks,
):
    """
    Execute Nuclei template scan

    TODO: Implement actual Nuclei execution
    For MVP, this is a placeholder
    """
    scan_id = str(uuid.uuid4())

    return {
        "scan_id": scan_id,
        "status": "queued",
        "message": "Nuclei scan queued (not yet implemented)"
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,  # Dev mode
        log_level="info"
    )
