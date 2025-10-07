# /home/juan/vertice-dev/backend/api_gateway/main.py

from datetime import datetime
import json
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
import jwt
from prometheus_client import Counter, generate_latest, Histogram
from pydantic import BaseModel
import redis.asyncio as redis
from slowapi import _rate_limit_exceeded_handler, Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response
import structlog

# Configuração de logs estruturados
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

# Métricas Prometheus
REQUESTS_TOTAL = Counter(
    "api_requests_total",
    "Total de pedidos recebidos",
    ["method", "path", "status_code"],
)
RESPONSE_TIME = Histogram(
    "api_response_time_seconds", "Tempo de resposta dos pedidos", ["method", "path"]
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title="Projeto VÉRTICE - API Gateway",
    description="Ponto de entrada unificado com cache, rate limiting, observability, cyber security e OSINT completo.",
    version="3.3.1",  # Version bump para correção do Redis
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de monitoramento
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    path_template = (
        request.scope.get("route").path
        if request.scope.get("route")
        else request.url.path
    )
    method = request.method
    status_code = response.status_code

    REQUESTS_TOTAL.labels(
        method=method, path=path_template, status_code=status_code
    ).inc()
    RESPONSE_TIME.labels(method=method, path=path_template).observe(process_time)

    log.info(
        "request_processed",
        method=method,
        path=request.url.path,
        status_code=status_code,
        process_time=round(process_time, 4),
    )

    return response


# ============================
# URLs DOS SERVIÇOS INTERNOS
# ============================
SINESP_SERVICE_URL = os.getenv("SINESP_SERVICE_URL", "http://sinesp_service:80")
CYBER_SERVICE_URL = os.getenv("CYBER_SERVICE_URL", "http://cyber_service:80")
DOMAIN_SERVICE_URL = os.getenv("DOMAIN_SERVICE_URL", "http://domain_service:80")
IP_INTEL_SERVICE_URL = os.getenv(
    "IP_INTEL_SERVICE_URL", "http://ip_intelligence_service:80"
)
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://nmap_service:80")
NETWORK_MONITOR_SERVICE_URL = os.getenv(
    "NETWORK_MONITOR_SERVICE_URL", "http://network_monitor_service:80"
)
VULN_SCANNER_SERVICE_URL = os.getenv(
    "VULN_SCANNER_SERVICE_URL", "http://vuln_scanner_service:80"
)
SOCIAL_ENG_SERVICE_URL = os.getenv(
    "SOCIAL_ENG_SERVICE_URL", "http://social_eng_service:80"
)
# New NSA-Grade Services
THREAT_INTEL_SERVICE_URL = os.getenv(
    "THREAT_INTEL_SERVICE_URL", "http://threat_intel_service:80"
)
MALWARE_ANALYSIS_SERVICE_URL = os.getenv(
    "MALWARE_ANALYSIS_SERVICE_URL", "http://malware_analysis_service:80"
)
SSL_MONITOR_SERVICE_URL = os.getenv(
    "SSL_MONITOR_SERVICE_URL", "http://ssl_monitor_service:80"
)
AURORA_ORCHESTRATOR_URL = os.getenv(
    "AURORA_ORCHESTRATOR_URL", "http://aurora_orchestrator_service:80"
)
OSINT_SERVICE_URL = os.getenv("OSINT_SERVICE_URL", "http://osint-service:80")
GOOGLE_OSINT_SERVICE_URL = os.getenv(
    "GOOGLE_OSINT_SERVICE_URL", "http://localhost:8013"
)
AURORA_PREDICT_URL = os.getenv("AURORA_PREDICT_URL", "http://aurora_predict:80")
ATLAS_SERVICE_URL = os.getenv("ATLAS_SERVICE_URL", "http://atlas_service:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:80")
VULN_SCANNER_SERVICE_URL = os.getenv(
    "VULN_SCANNER_SERVICE_URL", "http://vuln_scanner_service:80"
)
SOCIAL_ENG_SERVICE_URL = os.getenv(
    "SOCIAL_ENG_SERVICE_URL", "http://social_eng_service:80"
)
AI_AGENT_SERVICE_URL = os.getenv("AI_AGENT_SERVICE_URL", "http://ai_agent_service:80")
ACTIVE_IMMUNE_CORE_URL = os.getenv("ACTIVE_IMMUNE_CORE_URL", "http://active_immune_core:8200")

# Authentication configuration
JWT_SECRET = os.getenv("JWT_SECRET", "vertice-super-secret-key-2024")
security = HTTPBearer()

# ============================
# CONEXÃO COM REDIS (CORRIGIDA)
# ============================
REDIS_URL = "redis://redis:6379/0"
redis_client = None

try:
    redis_client = redis.from_url(
        REDIS_URL, decode_responses=True, socket_connect_timeout=5
    )
    log.info("Redis client configured successfully.")
except Exception as e:
    log.error(
        "Could not configure Redis client",
        error=str(e),
        detail="API Gateway will operate without cache.",
    )
    redis_client = None


# ============================
# MODELOS PYDANTIC
# ============================
class OccurrenceInput(BaseModel):
    lat: float
    lng: float
    intensity: float
    timestamp: datetime
    tipo: str


class PredictionInput(BaseModel):
    occurrences: List[OccurrenceInput]


class ClusterOutput(BaseModel):
    center_lat: float
    center_lng: float
    num_points: int
    risk_level: str


class PredictionOutput(BaseModel):
    hotspots: List[ClusterOutput]


class AutomatedInvestigationRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    image_url: Optional[str] = None


# ============================
# AUTHENTICATION FUNCTIONS
# ============================


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Verify JWT token and return user info"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_permission(permission: str):
    """Dependency factory to require specific permission"""

    def permission_dependency(user: Dict[str, Any] = Depends(verify_token)):
        if permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required. Available: {user.get('permissions', [])}",
            )
        return user

    return permission_dependency


# Optional auth - allows both authenticated and unauthenticated access
async def optional_auth(
    authorization: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Optional authentication - returns user info if token is provided and valid"""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        return None


# ============================
# FUNÇÃO AUXILIAR PARA PROXY
# ============================
async def proxy_request(
    request: Request,
    service_url: str,
    endpoint: str,
    service_name: str,
    timeout: float = 30.0,
    is_text_body: bool = False,
) -> Any:
    async with httpx.AsyncClient() as client:
        try:
            headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in ["host", "content-length"]
            }

            content = None
            if request.method in ["POST", "PUT", "PATCH"]:
                if is_text_body:
                    content = await request.body()
                    headers["content-type"] = "text/plain"
                else:
                    try:
                        content = await request.json()
                    except json.JSONDecodeError:
                        log.warning("proxy_request_empty_body")
                        content = {}

            response = await client.request(
                method=request.method,
                url=f"{service_url}{endpoint}",
                json=content if not is_text_body and content is not None else None,
                content=content if is_text_body and content is not None else None,
                params=dict(request.query_params),
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()

            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text

        except httpx.RequestError as exc:
            log.error(f"{service_name}_proxy_error", error=str(exc))
            raise HTTPException(
                status_code=503, detail=f"Erro de comunicação com {service_name}: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            log.error(
                f"{service_name}_http_error",
                status=exc.response.status_code,
                detail=exc.response.text,
            )
            detail = (
                exc.response.json().get("detail", exc.response.text)
                if "application/json" in exc.response.headers.get("content-type", "")
                else exc.response.text
            )
            raise HTTPException(status_code=exc.response.status_code, detail=detail)


# ============================
# ENDPOINTS
# ============================
@app.get("/", tags=["Root"])
async def read_root():
    return {"status": "API Gateway is running!"}


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Aggregated health check for API Gateway and key services.

    Checks:
    - API Gateway status
    - Active Immune Core status
    - Redis connectivity
    """
    health_status = {
        "status": "healthy",
        "message": "API Gateway is operational.",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api_gateway": "healthy",
            "redis": "unknown",
            "active_immune_core": "unknown",
        }
    }

    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = "degraded"
            log.warning("redis_health_check_failed", error=str(e))
    else:
        health_status["services"]["redis"] = "unavailable"

    # Check Active Immune Core
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ACTIVE_IMMUNE_CORE_URL}/health",
                timeout=5.0
            )
            if response.status_code == 200:
                health_status["services"]["active_immune_core"] = "healthy"
            else:
                health_status["services"]["active_immune_core"] = "degraded"
    except Exception as e:
        health_status["services"]["active_immune_core"] = "unavailable"
        log.warning("active_immune_core_health_check_failed", error=str(e))

    # Determine overall status
    service_statuses = list(health_status["services"].values())
    if all(s == "healthy" for s in service_statuses):
        health_status["status"] = "healthy"
    elif any(s == "unavailable" for s in service_statuses):
        health_status["status"] = "degraded"

    return health_status


@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    return Response(generate_latest(), media_type="text/plain")


# === CORREÇÃO: ROTAS ESPECÍFICAS PRIMEIRO ===
@app.get("/veiculos/{placa}", tags=["SINESP"])
@limiter.limit("30/minute")
async def consultar_placa_proxy(request: Request, placa: str):
    """Proxy para consulta de placas no SINESP Service com cache."""
    cache_key = f"placa:{placa.upper()}"

    if redis_client:
        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                log.info("cache_hit", placa=placa.upper())
                return json.loads(cached_data)
        except Exception as e:
            log.error("redis_get_error", error=str(e), detail="Continuando sem cache.")
    else:
        log.warning(
            "redis_unavailable", detail="Redis client not connected. Skipping cache."
        )

    log.info("cache_miss", placa=placa.upper())
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SINESP_SERVICE_URL}/veiculos/{placa}")
            response.raise_for_status()
            vehicle_data = response.json()
            if redis_client:
                try:
                    await redis_client.setex(cache_key, 3600, json.dumps(vehicle_data))
                except Exception as e:
                    log.error("redis_save_error", error=str(e))
            return vehicle_data
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Erro de comunicação com o serviço SINESP: {exc}",
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=exc.response.json().get("detail", exc.response.text),
            )


@app.get("/ocorrencias/tipos", tags=["SINESP"])
@limiter.limit("10/minute")
async def get_ocorrencia_tipos_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=SINESP_SERVICE_URL,
        endpoint=f"/ocorrencias/tipos",
        service_name="sinesp-service",
    )


@app.get("/ocorrencias/heatmap", tags=["SINESP"])
@limiter.limit("10/minute")
async def get_heatmap_data_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=SINESP_SERVICE_URL,
        endpoint=f"/ocorrencias/heatmap",
        service_name="sinesp-service",
    )


# ============================================


@app.api_route(
    "/atlas/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Atlas GIS"],
)
@limiter.limit("60/minute")
async def atlas_proxy(request: Request, full_path: str):
    endpoint = f"/{full_path}"
    log.info("Proxying request to Atlas GIS service", endpoint=endpoint)
    is_text = full_path == "query/" and request.method == "POST"
    return await proxy_request(
        request=request,
        service_url=ATLAS_SERVICE_URL,
        endpoint=endpoint,
        service_name="atlas-gis-service",
        is_text_body=is_text,
    )


# ============================
# ROTAS CYBER SERVICE
# ============================
@app.post("/cyber/network-scan", tags=["Cyber Security"])
@limiter.limit("5/minute")
async def cyber_network_scan_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/cyber/network-scan",
        service_name="cyber-service",
        timeout=60.0,
    )


@app.get("/cyber/port-analysis", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_port_analysis_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/cyber/port-analysis",
        service_name="cyber-service",
    )


@app.get("/cyber/file-integrity", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_file_integrity_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/cyber/file-integrity",
        service_name="cyber-service",
    )


@app.get("/cyber/process-analysis", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_process_analysis_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/cyber/process-analysis",
        service_name="cyber-service",
    )


@app.get("/cyber/certificate-check", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_certificate_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/cyber/certificate-check",
        service_name="cyber-service",
    )


@app.get("/cyber/security-config", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_security_config_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/cyber/security-config",
        service_name="cyber-service",
    )


@app.get("/cyber/security-logs", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_security_logs_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/cyber/security-logs",
        service_name="cyber-service",
    )


@app.get("/cyber/health", tags=["Cyber Security"])
async def cyber_health_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=CYBER_SERVICE_URL,
        endpoint="/",
        service_name="cyber-service",
    )


# ============================
# ROTAS NMAP SERVICE
# ============================
@app.post("/api/nmap/scan", tags=["Network Scanning"])
@limiter.limit("3/minute")
async def nmap_scan_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=NMAP_SERVICE_URL,
        endpoint="/scan",
        service_name="nmap-service",
        timeout=180.0,
    )


@app.get("/api/nmap/profiles", tags=["Network Scanning"])
@limiter.limit("30/minute")
async def nmap_profiles_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=NMAP_SERVICE_URL,
        endpoint="/profiles",
        service_name="nmap-service",
    )


@app.get("/nmap/health", tags=["Network Scanning"])
async def nmap_health_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=NMAP_SERVICE_URL,
        endpoint="/",
        service_name="nmap-service",
    )


# ============================
# ROTAS DOMAIN SERVICE
# ============================
@app.post("/api/domain/analyze", tags=["Domain Intelligence"])
@limiter.limit("10/minute")
async def domain_analyze_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=DOMAIN_SERVICE_URL,
        endpoint="/analyze",
        service_name="domain-service",
        timeout=60.0,
    )


@app.get("/domain/health", tags=["Domain Intelligence"])
async def domain_health_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=DOMAIN_SERVICE_URL,
        endpoint="/",
        service_name="domain-service",
    )


# ============================
# ROTAS IP INTELLIGENCE SERVICE
# ============================
@app.post("/api/ip/analyze", tags=["IP Intelligence"])
@limiter.limit("15/minute")
async def ip_analyze_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=IP_INTEL_SERVICE_URL,
        endpoint="/analyze",
        service_name="ip-intelligence-service",
        timeout=60.0,
    )


@app.get("/api/ip/my-ip", tags=["IP Intelligence"])
@limiter.limit("10/minute")
async def ip_my_ip_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=IP_INTEL_SERVICE_URL,
        endpoint="/my-ip",
        service_name="ip-intelligence-service",
        timeout=30.0,
    )


@app.post("/api/ip/analyze-my-ip", tags=["IP Intelligence"])
@limiter.limit("10/minute")
async def ip_analyze_my_ip_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=IP_INTEL_SERVICE_URL,
        endpoint="/analyze-my-ip",
        service_name="ip-intelligence-service",
        timeout=60.0,
    )


@app.get("/ip/health", tags=["IP Intelligence"])
async def ip_health_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=IP_INTEL_SERVICE_URL,
        endpoint="/",
        service_name="ip-intelligence-service",
    )


# ============================
# ROTAS NETWORK MONITOR SERVICE
# ============================
@app.get("/api/network/monitor", tags=["Network Monitoring"])
@limiter.limit("20/minute")
async def network_monitor_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=NETWORK_MONITOR_SERVICE_URL,
        endpoint="/stats",
        service_name="network-monitor-service",
    )


@app.get("/network/health", tags=["Network Monitoring"])
async def network_health_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=NETWORK_MONITOR_SERVICE_URL,
        endpoint="/",
        service_name="network-monitor-service",
    )


# ============================
# ROTAS OSINT SERVICE
# ============================
@app.post("/api/investigate/auto", tags=["OSINT"])
@limiter.limit("2/minute")
async def automated_investigation(
    request: Request, investigation_request: AutomatedInvestigationRequest
):
    if not any(
        [
            investigation_request.username,
            investigation_request.email,
            investigation_request.phone,
            investigation_request.name,
            investigation_request.image_url,
        ]
    ):
        raise HTTPException(
            status_code=400, detail="Pelo menos um identificador deve ser fornecido."
        )
    log.info("Proxying automated investigation request to OSINT service")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OSINT_SERVICE_URL}/api/investigate/auto",
            json=jsonable_encoder(investigation_request),
            timeout=300.0,
        )
        response.raise_for_status()
        return response.json()


@app.post("/api/username/search", tags=["OSINT"])
@limiter.limit("10/minute")
async def search_username_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/api/username/search",
        service_name="osint-service",
        timeout=120.0,
    )


@app.post("/api/email/analyze", tags=["OSINT"])
@limiter.limit("10/minute")
async def analyze_email_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/api/email/analyze",
        service_name="osint-service",
        timeout=120.0,
    )


@app.post("/api/phone/analyze", tags=["OSINT"])
@limiter.limit("10/minute")
async def analyze_phone_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/api/phone/analyze",
        service_name="osint-service",
        timeout=120.0,
    )


@app.post("/api/social/profile", tags=["OSINT"])
@limiter.limit("5/minute")
async def get_social_profile_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/api/social/profile",
        service_name="osint-service",
        timeout=180.0,
    )


@app.post("/api/image/analyze", tags=["OSINT"])
@limiter.limit("3/minute")
async def analyze_image_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/api/image/analyze",
        service_name="osint-service",
        timeout=300.0,
    )


@app.post("/api/search/comprehensive", tags=["OSINT"])
@limiter.limit("5/minute")
async def comprehensive_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/api/search/comprehensive",
        service_name="osint-service",
        timeout=240.0,
    )


@app.get("/api/osint/stats", tags=["OSINT"])
@limiter.limit("30/minute")
async def get_osint_stats_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/api/stats",
        service_name="osint-service",
    )


@app.get("/api/osint/health", tags=["OSINT"])
async def osint_health_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint=f"/health",
        service_name="osint-service",
    )


# ============================
# GOOGLE OSINT ENDPOINTS
# ============================
@app.post("/api/google/search/basic", tags=["Google OSINT"])
@limiter.limit("5/minute")
async def google_basic_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/api/search/basic",
        service_name="google-osint-service",
        timeout=180.0,
    )


@app.post("/api/google/search/advanced", tags=["Google OSINT"])
@limiter.limit("3/minute")
async def google_advanced_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/api/search/advanced",
        service_name="google-osint-service",
        timeout=300.0,
    )


@app.post("/api/google/search/documents", tags=["Google OSINT"])
@limiter.limit("5/minute")
async def google_documents_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/api/search/documents",
        service_name="google-osint-service",
        timeout=240.0,
    )


@app.post("/api/google/search/images", tags=["Google OSINT"])
@limiter.limit("5/minute")
async def google_images_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/api/search/images",
        service_name="google-osint-service",
        timeout=180.0,
    )


@app.post("/api/google/search/social", tags=["Google OSINT"])
@limiter.limit("5/minute")
async def google_social_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/api/search/social",
        service_name="google-osint-service",
        timeout=180.0,
    )


@app.get("/api/google/dorks/patterns", tags=["Google OSINT"])
@limiter.limit("30/minute")
async def google_dork_patterns_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/api/dorks/patterns",
        service_name="google-osint-service",
    )


@app.get("/api/google/stats", tags=["Google OSINT"])
@limiter.limit("30/minute")
async def google_osint_stats_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/api/stats",
        service_name="google-osint-service",
    )


@app.get("/api/google/health", tags=["Google OSINT"])
async def google_osint_health_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint=f"/health",
        service_name="google-osint-service",
    )


@app.post(
    "/predict/crime-hotspots", response_model=PredictionOutput, tags=["Prediction"]
)
@limiter.limit("5/minute")
async def predict_crime_hotspots_proxy(request: Request, data: PredictionInput):
    log.info("Proxying crime hotspot prediction request to Aurora service")
    try:
        # Extrai os parâmetros de sensibilidade do payload da requisição
        body = await request.json()
        payload = {
            "occurrences": body.get("occurrences", []),
            "eps_km": body.get("eps_km"),
            "min_samples": body.get("min_samples"),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AURORA_PREDICT_URL}/predict/crime-hotspots",
                json=payload,
                timeout=90.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        log.error("aurora_predict_proxy_error", error=str(exc))
        raise HTTPException(
            status_code=503,
            detail=f"Erro de comunicação com o serviço de predição: {exc}",
        )
    except httpx.HTTPStatusError as exc:
        log.error(
            "aurora_predict_http_error",
            status=exc.response.status_code,
            detail=exc.response.json().get("detail", exc.response.text),
        )
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.json().get("detail", exc.response.text),
        )


# ============================
# AUTHENTICATION ROUTES
# ============================


@app.post("/auth/google", tags=["Authentication"])
@limiter.limit("10/minute")
async def authenticate_with_google(request: Request):
    """Proxy for Google OAuth authentication"""
    return await proxy_request(
        request=request,
        service_url=AUTH_SERVICE_URL,
        endpoint="/auth/google",
        service_name="auth-service",
    )


@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(user: Dict[str, Any] = Depends(verify_token)):
    """Get current user information"""
    return {
        "authenticated": True,
        "user": {
            "id": user["sub"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
        },
        "permissions": user.get("permissions", []),
    }


@app.post("/auth/logout", tags=["Authentication"])
async def logout(request: Request, user: Dict[str, Any] = Depends(verify_token)):
    """Logout user"""
    return await proxy_request(
        request=request,
        service_url=AUTH_SERVICE_URL,
        endpoint="/auth/logout",
        service_name="auth-service",
    )


@app.get("/auth/verify-token", tags=["Authentication"])
async def verify_token_route(user: Dict[str, Any] = Depends(verify_token)):
    """Verify token validity"""
    return {
        "valid": True,
        "user_id": user["sub"],
        "permissions": user.get("permissions", []),
    }


# ============================
# PROTECTED ROUTES EXAMPLES
# ============================


@app.get("/protected/admin", tags=["Protected"])
async def admin_only(user: Dict[str, Any] = Depends(require_permission("admin"))):
    """Admin only endpoint"""
    return {"message": "Admin access granted", "user": user["email"]}


@app.get("/protected/offensive", tags=["Protected"])
async def offensive_tools_access(
    user: Dict[str, Any] = Depends(require_permission("offensive")),
):
    """Offensive tools access"""
    return {"message": "Offensive tools access granted", "user": user["email"]}


@app.get("/protected/analyst", tags=["Protected"])
async def analyst_access(user: Dict[str, Any] = Depends(require_permission("write"))):
    """Analyst access"""
    return {"message": "Analyst access granted", "user": user["email"]}


# ============================
# VULNERABILITY SCANNER ROUTES
# ============================
@app.post("/api/vuln-scanner/scan", tags=["Offensive Security"])
async def vulnerability_scan(
    request: Request, user: Dict[str, Any] = Depends(require_permission("offensive"))
):
    """Perform vulnerability scan - requires offensive permission"""
    return await proxy_request(
        request, VULN_SCANNER_SERVICE_URL, "/scan", "Vulnerability Scanner"
    )


@app.get("/api/vuln-scanner/scan/{scan_id}", tags=["Offensive Security"])
async def get_scan_result(
    scan_id: str, user: Dict[str, Any] = Depends(require_permission("offensive"))
):
    """Get vulnerability scan results - requires offensive permission"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{VULN_SCANNER_SERVICE_URL}/scan/{scan_id}")
        return response.json()


@app.post("/api/vuln-scanner/exploit", tags=["Offensive Security"])
async def exploit_vulnerability(
    request: Request, user: Dict[str, Any] = Depends(require_permission("offensive"))
):
    """Exploit vulnerability - requires offensive permission"""
    return await proxy_request(
        request, VULN_SCANNER_SERVICE_URL, "/exploit", "Vulnerability Scanner"
    )


@app.get("/api/vuln-scanner/exploits", tags=["Offensive Security"])
async def list_exploits(
    user: Dict[str, Any] = Depends(require_permission("offensive")),
):
    """List available exploits - requires offensive permission"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{VULN_SCANNER_SERVICE_URL}/exploits")
        return response.json()


@app.get("/vuln-scanner/health", tags=["Offensive Security"])
async def vuln_scanner_health():
    """Health check for vulnerability scanner service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{VULN_SCANNER_SERVICE_URL}/health")
        return response.json()


# ============================
# SOCIAL ENGINEERING ROUTES
# ============================
@app.post("/api/social-eng/campaign", tags=["Offensive Security"])
async def create_phishing_campaign(
    request: Request, user: Dict[str, Any] = Depends(require_permission("offensive"))
):
    """Create phishing campaign - requires offensive permission"""
    return await proxy_request(
        request, SOCIAL_ENG_SERVICE_URL, "/campaign", "Social Engineering"
    )


@app.get("/api/social-eng/campaign/{campaign_id}", tags=["Offensive Security"])
async def get_campaign_status(
    campaign_id: str, user: Dict[str, Any] = Depends(require_permission("offensive"))
):
    """Get campaign status - requires offensive permission"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SOCIAL_ENG_SERVICE_URL}/campaign/{campaign_id}")
        return response.json()


@app.post("/api/social-eng/awareness", tags=["Offensive Security"])
async def create_awareness_training(
    request: Request, user: Dict[str, Any] = Depends(require_permission("offensive"))
):
    """Create awareness training - requires offensive permission"""
    return await proxy_request(
        request, SOCIAL_ENG_SERVICE_URL, "/awareness", "Social Engineering"
    )


@app.get("/api/social-eng/templates", tags=["Offensive Security"])
async def list_templates(
    user: Dict[str, Any] = Depends(require_permission("offensive")),
):
    """List phishing templates - requires offensive permission"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SOCIAL_ENG_SERVICE_URL}/templates")
        return response.json()


@app.get("/api/social-eng/analytics/{campaign_id}", tags=["Offensive Security"])
async def get_campaign_analytics(
    campaign_id: str, user: Dict[str, Any] = Depends(require_permission("offensive"))
):
    """Get campaign analytics - requires offensive permission"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SOCIAL_ENG_SERVICE_URL}/analytics/{campaign_id}")
        return response.json()


@app.get("/social-eng/health", tags=["Offensive Security"])
async def social_eng_health():
    """Health check for social engineering service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SOCIAL_ENG_SERVICE_URL}/health")
        return response.json()


# ============================
# NSA-GRADE SERVICES - AURORA AI
# ============================


@app.post("/api/threat-intel/check", tags=["Threat Intelligence"])
@limiter.limit("30/minute")
async def threat_intel_check(request: Request):
    """Threat Intelligence Aggregator - checks multiple sources"""
    return await proxy_request(
        request=request,
        service_url=THREAT_INTEL_SERVICE_URL,
        endpoint="/api/threat-intel/check",
        service_name="threat-intel-service",
        timeout=30.0,
    )


@app.get("/threat-intel/health", tags=["Threat Intelligence"])
async def threat_intel_health():
    """Health check for threat intelligence service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{THREAT_INTEL_SERVICE_URL}/health")
        return response.json()


@app.post("/api/malware/analyze-file", tags=["Malware Analysis"])
@limiter.limit("10/minute")
async def malware_analyze_file(request: Request):
    """Malware Analysis - analyze uploaded file"""
    return await proxy_request(
        request=request,
        service_url=MALWARE_ANALYSIS_SERVICE_URL,
        endpoint="/api/malware/analyze-file",
        service_name="malware-analysis-service",
        timeout=60.0,
    )


@app.post("/api/malware/analyze-hash", tags=["Malware Analysis"])
@limiter.limit("30/minute")
async def malware_analyze_hash(request: Request):
    """Malware Analysis - analyze hash"""
    return await proxy_request(
        request=request,
        service_url=MALWARE_ANALYSIS_SERVICE_URL,
        endpoint="/api/malware/analyze-hash",
        service_name="malware-analysis-service",
        timeout=30.0,
    )


@app.post("/api/malware/analyze-url", tags=["Malware Analysis"])
@limiter.limit("30/minute")
async def malware_analyze_url(request: Request):
    """Malware Analysis - analyze URL"""
    return await proxy_request(
        request=request,
        service_url=MALWARE_ANALYSIS_SERVICE_URL,
        endpoint="/api/malware/analyze-url",
        service_name="malware-analysis-service",
        timeout=30.0,
    )


@app.get("/malware/health", tags=["Malware Analysis"])
async def malware_health():
    """Health check for malware analysis service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MALWARE_ANALYSIS_SERVICE_URL}/health")
        return response.json()


@app.post("/api/ssl/check", tags=["SSL/TLS Monitor"])
@limiter.limit("30/minute")
async def ssl_check(request: Request):
    """SSL/TLS Monitor - comprehensive certificate analysis"""
    return await proxy_request(
        request=request,
        service_url=SSL_MONITOR_SERVICE_URL,
        endpoint="/api/ssl/check",
        service_name="ssl-monitor-service",
        timeout=30.0,
    )


@app.get("/ssl/health", tags=["SSL/TLS Monitor"])
async def ssl_health():
    """Health check for SSL monitor service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SSL_MONITOR_SERVICE_URL}/health")
        return response.json()


@app.post("/api/aurora/investigate", tags=["Aurora Orchestrator"])
@limiter.limit("10/minute")
async def aurora_investigate(request: Request):
    """Aurora Orchestrator - autonomous investigation"""
    return await proxy_request(
        request=request,
        service_url=AURORA_ORCHESTRATOR_URL,
        endpoint="/api/aurora/investigate",
        service_name="aurora-orchestrator",
        timeout=300.0,
    )


@app.get("/api/aurora/investigation/{investigation_id}", tags=["Aurora Orchestrator"])
@limiter.limit("60/minute")
async def aurora_get_investigation(request: Request, investigation_id: str):
    """Aurora Orchestrator - get investigation status"""
    return await proxy_request(
        request=request,
        service_url=AURORA_ORCHESTRATOR_URL,
        endpoint=f"/api/aurora/investigation/{investigation_id}",
        service_name="aurora-orchestrator",
        timeout=10.0,
    )


@app.get("/api/aurora/services", tags=["Aurora Orchestrator"])
@limiter.limit("30/minute")
async def aurora_list_services(request: Request):
    """Aurora Orchestrator - list all services"""
    return await proxy_request(
        request=request,
        service_url=AURORA_ORCHESTRATOR_URL,
        endpoint="/api/aurora/services",
        service_name="aurora-orchestrator",
        timeout=10.0,
    )


@app.get("/aurora/health", tags=["Aurora Orchestrator"])
async def aurora_health():
    """Health check for Aurora orchestrator"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AURORA_ORCHESTRATOR_URL}/health")
        return response.json()


# ========================================
# AI AGENT ROUTES - THE BRAIN 🧠
# ========================================


@app.get("/api/ai/", tags=["AI Agent"])
async def ai_agent_info():
    """Get AI Agent service info"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AI_AGENT_SERVICE_URL}/")
        return response.json()


@app.get("/api/ai/tools", tags=["AI Agent"])
async def ai_agent_list_tools(request: Request):
    """List all tools available to the AI"""
    return await proxy_request(
        request=request,
        service_url=AI_AGENT_SERVICE_URL,
        endpoint="/tools",
        service_name="ai-agent",
        timeout=10.0,
    )


@app.post("/api/ai/chat", tags=["AI Agent"])
@limiter.limit("10/minute")
async def ai_agent_chat(request: Request):
    """
    Chat conversacional com AI Agent
    A AI tem acesso maestro a TODOS os serviços via tool calling
    """
    return await proxy_request(
        request=request,
        service_url=AI_AGENT_SERVICE_URL,
        endpoint="/chat",
        service_name="ai-agent",
        timeout=120.0,
    )


@app.get("/ai/health", tags=["AI Agent"])
async def ai_agent_health():
    """Health check for AI Agent"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AI_AGENT_SERVICE_URL}/health")
        return response.json()


# ========================================
# ACTIVE IMMUNE CORE ROUTES - IMMUNIS 🦠
# ========================================


@app.get("/api/immune/health", tags=["Active Immune Core"])
async def immune_health_check(request: Request):
    """Health check for Active Immune Core"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/health",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/stats", tags=["Active Immune Core"])
@limiter.limit("30/minute")
async def immune_get_stats(request: Request):
    """Get Active Immune Core statistics"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/stats",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/agents", tags=["Active Immune Core"])
@limiter.limit("30/minute")
async def immune_list_agents(request: Request):
    """List all immune agents"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/agents",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/agents/{agent_id}", tags=["Active Immune Core"])
@limiter.limit("60/minute")
async def immune_get_agent(request: Request, agent_id: str):
    """Get specific agent details"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint=f"/api/agents/{agent_id}",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.post("/api/immune/threats/detect", tags=["Active Immune Core"])
@limiter.limit("20/minute")
async def immune_detect_threat(request: Request):
    """Submit threat for detection and response"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/threats/detect",
        service_name="active-immune-core",
        timeout=30.0,
    )


@app.get("/api/immune/threats", tags=["Active Immune Core"])
@limiter.limit("30/minute")
async def immune_list_threats(request: Request):
    """List detected threats"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/threats",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/threats/{threat_id}", tags=["Active Immune Core"])
@limiter.limit("60/minute")
async def immune_get_threat(request: Request, threat_id: str):
    """Get specific threat details"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint=f"/api/threats/{threat_id}",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/lymphnodes", tags=["Active Immune Core"])
@limiter.limit("30/minute")
async def immune_list_lymphnodes(request: Request):
    """List all lymphnodes (coordination points)"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/lymphnodes",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/lymphnodes/{lymphnode_id}", tags=["Active Immune Core"])
@limiter.limit("60/minute")
async def immune_get_lymphnode(request: Request, lymphnode_id: str):
    """Get specific lymphnode details"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint=f"/api/lymphnodes/{lymphnode_id}",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/memory/antibodies", tags=["Active Immune Core"])
@limiter.limit("30/minute")
async def immune_list_antibodies(request: Request):
    """List known antibodies (threat signatures)"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/memory/antibodies",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/memory/search", tags=["Active Immune Core"])
@limiter.limit("30/minute")
async def immune_search_memory(request: Request):
    """Search immune memory for similar threats"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/memory/search",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/homeostasis", tags=["Active Immune Core"])
@limiter.limit("30/minute")
async def immune_homeostasis_status(request: Request):
    """Get homeostatic control status"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/homeostasis",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.post("/api/immune/homeostasis/adjust", tags=["Active Immune Core"])
@limiter.limit("10/minute")
async def immune_adjust_homeostasis(request: Request):
    """Manually adjust homeostatic parameters"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/homeostasis/adjust",
        service_name="active-immune-core",
        timeout=10.0,
    )


@app.get("/api/immune/metrics", tags=["Active Immune Core"])
@limiter.limit("60/minute")
async def immune_get_metrics(request: Request):
    """Get Prometheus metrics from Active Immune Core"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/metrics",
        service_name="active-immune-core",
        timeout=10.0,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
