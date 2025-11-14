# /home/juan/vertice-dev/backend/api_gateway/main.py

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import jwt
import redis.asyncio as redis
import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response

# Reactive Fabric Integration
from reactive_fabric_integration import (
    get_reactive_fabric_info,
    register_reactive_fabric_routes,
)

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

# ============================
# REACTIVE FABRIC INTEGRATION
# ============================
# Register Reactive Fabric routers (Phase 1: passive intelligence only)
register_reactive_fabric_routes(app)
log.info(
    "reactive_fabric_integrated",
    phase="1",
    mode="passive_intelligence_only",
    human_authorization="required",
)


# Middleware de monitoramento
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    route = request.scope.get("route")
    path_template = route.path if route else request.url.path
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
ACTIVE_IMMUNE_CORE_URL = os.getenv(
    "ACTIVE_IMMUNE_CORE_URL", "http://active_immune_core:8200"
)

# ============================
# P0 AIR GAP EXTINCTION - 30 CRITICAL SERVICES
# ============================
# Added: 2025-11-14 - OPERAÇÃO AIR GAP EXTINCTION
# Connecting: Fixed Defensive (4) + MAXIMUS Core (8) + Immunis (12) + HCL/HITL (6)

# Fixed Defensive (Direct Access - Bypass Facade)
BEHAVIORAL_ANALYZER_URL = os.getenv(
    "BEHAVIORAL_ANALYZER_URL", "http://behavioral-analyzer-service:8037"
)
MAV_DETECTION_URL = os.getenv("MAV_DETECTION_URL", "http://mav-detection-service:8039")
PENELOPE_URL = os.getenv("PENELOPE_URL", "http://penelope-service:8042")
TEGUMENTAR_URL = os.getenv("TEGUMENTAR_URL", "http://tegumentar-service:8043")

# MAXIMUS Core (8 services - Brain of the system)
MAXIMUS_CORE_URL = os.getenv("MAXIMUS_CORE_URL", "http://maximus-core-service:8000")
MAXIMUS_ORCHESTRATOR_URL = os.getenv(
    "MAXIMUS_ORCHESTRATOR_URL", "http://maximus-orchestrator-service:8001"
)
MAXIMUS_EUREKA_URL = os.getenv("MAXIMUS_EUREKA_URL", "http://maximus-eureka:8002")
MAXIMUS_ORACULO_V2_URL = os.getenv(
    "MAXIMUS_ORACULO_V2_URL", "http://maximus-oraculo-v2:8003"
)
MAXIMUS_PREDICT_URL = os.getenv("MAXIMUS_PREDICT_URL", "http://maximus-predict:8004")
MAXIMUS_INTEGRATION_URL = os.getenv(
    "MAXIMUS_INTEGRATION_URL", "http://maximus-integration-service:8005"
)
MAXIMUS_DLQ_MONITOR_URL = os.getenv(
    "MAXIMUS_DLQ_MONITOR_URL", "http://maximus-dlq-monitor-service:8006"
)

# Immunis System (12 services - Complete immune defense)
IMMUNIS_API_URL = os.getenv("IMMUNIS_API_URL", "http://immunis-api-service:8100")
ADAPTIVE_IMMUNITY_URL = os.getenv(
    "ADAPTIVE_IMMUNITY_URL", "http://adaptive-immunity-service:8101"
)
AI_IMMUNE_URL = os.getenv("AI_IMMUNE_URL", "http://ai-immune-system:8102")
IMMUNIS_BCELL_URL = os.getenv("IMMUNIS_BCELL_URL", "http://immunis-bcell-service:8103")
IMMUNIS_DENDRITIC_URL = os.getenv(
    "IMMUNIS_DENDRITIC_URL", "http://immunis-dendritic-service:8104"
)
IMMUNIS_HELPER_T_URL = os.getenv(
    "IMMUNIS_HELPER_T_URL", "http://immunis-helper-t-service:8105"
)
IMMUNIS_CYTOTOXIC_T_URL = os.getenv(
    "IMMUNIS_CYTOTOXIC_T_URL", "http://immunis-cytotoxic-t-service:8106"
)
IMMUNIS_TREG_URL = os.getenv("IMMUNIS_TREG_URL", "http://immunis-treg-service:8107")
IMMUNIS_MACROPHAGE_URL = os.getenv(
    "IMMUNIS_MACROPHAGE_URL", "http://immunis-macrophage-service:8108"
)
IMMUNIS_NEUTROPHIL_URL = os.getenv(
    "IMMUNIS_NEUTROPHIL_URL", "http://immunis-neutrophil-service:8109"
)
ADAPTIVE_IMMUNE_SYSTEM_URL = os.getenv(
    "ADAPTIVE_IMMUNE_SYSTEM_URL", "http://adaptive-immune-system:8110"
)
ADAPTIVE_IMMUNITY_DB_URL = os.getenv(
    "ADAPTIVE_IMMUNITY_DB_URL", "http://adaptive-immunity-db:8111"
)

# HCL/HITL (6 services - Human oversight - Lei Zero!)
HCL_ANALYZER_URL = os.getenv("HCL_ANALYZER_URL", "http://hcl-analyzer-service:8200")
HCL_PLANNER_URL = os.getenv("HCL_PLANNER_URL", "http://hcl-planner-service:8201")
HCL_EXECUTOR_URL = os.getenv("HCL_EXECUTOR_URL", "http://hcl-executor-service:8202")
HCL_MONITOR_URL = os.getenv("HCL_MONITOR_URL", "http://hcl-monitor-service:8203")
HCL_KB_URL = os.getenv("HCL_KB_URL", "http://hcl-kb-service:8204")
HITL_PATCH_URL = os.getenv("HITL_PATCH_URL", "http://hitl-patch-service:8205")

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
        payload: Dict[str, Any] = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=["HS256"]
        )
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
        payload: Dict[str, Any] = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception:
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
                        json_content = await request.json()
                        content = json_content
                    except json.JSONDecodeError:
                        log.warning("proxy_request_empty_body")
                        content = None

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
    return {
        "status": "API Gateway is running!",
        "reactive_fabric": get_reactive_fabric_info(),
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Aggregated health check for API Gateway and key services.

    Checks:
    - API Gateway status
    - Active Immune Core status
    - Redis connectivity
    - Reactive Fabric status (Phase 1)
    """
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "message": "API Gateway is operational.",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api_gateway": "healthy",
            "redis": "unknown",
            "active_immune_core": "unknown",
            "reactive_fabric": "healthy",  # Phase 1 always healthy (no external deps)
        },
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
            response = await client.get(f"{ACTIVE_IMMUNE_CORE_URL}/health", timeout=5.0)
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
        endpoint="/ocorrencias/tipos",
        service_name="sinesp-service",
    )


@app.get("/ocorrencias/heatmap", tags=["SINESP"])
@limiter.limit("10/minute")
async def get_heatmap_data_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=SINESP_SERVICE_URL,
        endpoint="/ocorrencias/heatmap",
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
        endpoint="/api/username/search",
        service_name="osint-service",
        timeout=120.0,
    )


@app.post("/api/email/analyze", tags=["OSINT"])
@limiter.limit("10/minute")
async def analyze_email_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint="/api/email/analyze",
        service_name="osint-service",
        timeout=120.0,
    )


@app.post("/api/phone/analyze", tags=["OSINT"])
@limiter.limit("10/minute")
async def analyze_phone_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint="/api/phone/analyze",
        service_name="osint-service",
        timeout=120.0,
    )


@app.post("/api/social/profile", tags=["OSINT"])
@limiter.limit("5/minute")
async def get_social_profile_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint="/api/social/profile",
        service_name="osint-service",
        timeout=180.0,
    )


@app.post("/api/image/analyze", tags=["OSINT"])
@limiter.limit("3/minute")
async def analyze_image_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint="/api/image/analyze",
        service_name="osint-service",
        timeout=300.0,
    )


@app.post("/api/search/comprehensive", tags=["OSINT"])
@limiter.limit("5/minute")
async def comprehensive_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint="/api/search/comprehensive",
        service_name="osint-service",
        timeout=240.0,
    )


@app.get("/api/osint/stats", tags=["OSINT"])
@limiter.limit("30/minute")
async def get_osint_stats_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint="/api/stats",
        service_name="osint-service",
    )


@app.get("/api/osint/health", tags=["OSINT"])
async def osint_health_check_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=OSINT_SERVICE_URL,
        endpoint="/health",
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
        endpoint="/api/search/basic",
        service_name="google-osint-service",
        timeout=180.0,
    )


@app.post("/api/google/search/advanced", tags=["Google OSINT"])
@limiter.limit("3/minute")
async def google_advanced_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint="/api/search/advanced",
        service_name="google-osint-service",
        timeout=300.0,
    )


@app.post("/api/google/search/documents", tags=["Google OSINT"])
@limiter.limit("5/minute")
async def google_documents_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint="/api/search/documents",
        service_name="google-osint-service",
        timeout=240.0,
    )


@app.post("/api/google/search/images", tags=["Google OSINT"])
@limiter.limit("5/minute")
async def google_images_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint="/api/search/images",
        service_name="google-osint-service",
        timeout=180.0,
    )


@app.post("/api/google/search/social", tags=["Google OSINT"])
@limiter.limit("5/minute")
async def google_social_search_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint="/api/search/social",
        service_name="google-osint-service",
        timeout=180.0,
    )


@app.get("/api/google/dorks/patterns", tags=["Google OSINT"])
@limiter.limit("30/minute")
async def google_dork_patterns_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint="/api/dorks/patterns",
        service_name="google-osint-service",
    )


@app.get("/api/google/stats", tags=["Google OSINT"])
@limiter.limit("30/minute")
async def google_osint_stats_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint="/api/stats",
        service_name="google-osint-service",
    )


@app.get("/api/google/health", tags=["Google OSINT"])
async def google_osint_health_proxy(request: Request):
    return await proxy_request(
        request=request,
        service_url=GOOGLE_OSINT_SERVICE_URL,
        endpoint="/health",
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


# ============================
# DEFENSIVE TOOLS ENDPOINTS
# ============================


@app.post("/api/defensive/behavioral/analyze", tags=["Defensive Tools"])
@limiter.limit("100/minute")
async def defensive_behavioral_analyze(request: Request):
    """Analyze behavior event for anomalies"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/behavioral/analyze",
        service_name="active-immune-core",
        timeout=15.0,
    )


@app.post("/api/defensive/behavioral/analyze-batch", tags=["Defensive Tools"])
@limiter.limit("20/minute")
async def defensive_behavioral_analyze_batch(request: Request):
    """Analyze batch of behavior events"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/behavioral/analyze-batch",
        service_name="active-immune-core",
        timeout=30.0,
    )


@app.post("/api/defensive/behavioral/train-baseline", tags=["Defensive Tools"])
@limiter.limit("5/hour")
async def defensive_behavioral_train(request: Request):
    """Train behavioral baseline from normal activity"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/behavioral/train-baseline",
        service_name="active-immune-core",
        timeout=60.0,
    )


@app.get("/api/defensive/behavioral/baseline-status", tags=["Defensive Tools"])
@limiter.limit("60/minute")
async def defensive_behavioral_baseline_status(request: Request):
    """Get baseline training status"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/behavioral/baseline-status",
        service_name="active-immune-core",
        timeout=5.0,
    )


@app.get("/api/defensive/behavioral/metrics", tags=["Defensive Tools"])
@limiter.limit("60/minute")
async def defensive_behavioral_metrics(request: Request):
    """Get behavioral analyzer metrics"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/behavioral/metrics",
        service_name="active-immune-core",
        timeout=5.0,
    )


@app.post("/api/defensive/traffic/analyze", tags=["Defensive Tools"])
@limiter.limit("100/minute")
async def defensive_traffic_analyze(request: Request):
    """Analyze encrypted traffic pattern for anomalies"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/traffic/analyze",
        service_name="active-immune-core",
        timeout=15.0,
    )


@app.post("/api/defensive/traffic/analyze-batch", tags=["Defensive Tools"])
@limiter.limit("20/minute")
async def defensive_traffic_analyze_batch(request: Request):
    """Analyze batch of traffic patterns"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/traffic/analyze-batch",
        service_name="active-immune-core",
        timeout=30.0,
    )


@app.get("/api/defensive/traffic/metrics", tags=["Defensive Tools"])
@limiter.limit("60/minute")
async def defensive_traffic_metrics(request: Request):
    """Get traffic analyzer metrics"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/traffic/metrics",
        service_name="active-immune-core",
        timeout=5.0,
    )


@app.get("/api/defensive/health", tags=["Defensive Tools"])
@limiter.limit("60/minute")
async def defensive_health_check(request: Request):
    """Health check for defensive tools"""
    return await proxy_request(
        request=request,
        service_url=ACTIVE_IMMUNE_CORE_URL,
        endpoint="/api/defensive/health",
        service_name="active-immune-core",
        timeout=5.0,
    )


# ================================================================================
# P0 AIR GAP EXTINCTION - 30 CRITICAL SERVICE ROUTES
# ================================================================================
# Added: 2025-11-14 - OPERAÇÃO AIR GAP EXTINCTION
# "O reino dividido contra si mesmo não subsistirá" - Marcos 3:24
# ================================================================================

# ================================================================================
# FIXED DEFENSIVE SERVICES (4) - Direct access routes
# ================================================================================


@app.api_route(
    "/api/behavioral-analyzer/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Fixed Defensive"],
)
@limiter.limit("100/minute")
async def route_behavioral_analyzer(path: str, request: Request):
    """
    Behavioral Analyzer Service (Direct Access)

    FIX #7 Complete: TimescaleDB persistence + auto-migration
    - User Behavior Analytics (UBA)
    - Entity Behavior Analytics (EBA)
    - Anomaly detection with ML
    - TimescaleDB time-series storage
    - 90-day retention (GDPR compliant)

    Port: 8037
    Constitutional: Lei Zero (high-severity → human review)
    """
    return await proxy_request(
        request=request,
        service_url=BEHAVIORAL_ANALYZER_URL,
        endpoint=f"/{path}",
        service_name="behavioral-analyzer",
        timeout=15.0,
    )


@app.api_route(
    "/api/mav-detection/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Fixed Defensive"],
)
@limiter.limit("100/minute")
async def route_mav_detection(path: str, request: Request):
    """
    MAV Detection Service (Direct Access)

    FIX #8 Complete: Neo4j graph persistence + schema migration
    - Militância em Ambientes Virtuais detection
    - Graph-based campaign analysis
    - Coordinated account detection
    - Neo4j graph database
    - Evidence preservation (Lei P4)

    Port: 8039
    Constitutional: Lei Zero (>0.8 confidence → HITL)
    """
    return await proxy_request(
        request=request,
        service_url=MAV_DETECTION_URL,
        endpoint=f"/{path}",
        service_name="mav-detection",
        timeout=20.0,
    )


@app.api_route(
    "/api/penelope/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Fixed Defensive"],
)
@limiter.limit("100/minute")
async def route_penelope(path: str, request: Request):
    """
    Penelope Circuit Breaker Service (Direct Access)

    FIX #2: Circuit breaker pattern
    - Service resilience & fault tolerance
    - Cascading failure prevention
    - Graceful degradation
    - Health monitoring

    Port: 8042
    Constitutional: P2 (Validação Preventiva)
    """
    return await proxy_request(
        request=request,
        service_url=PENELOPE_URL,
        endpoint=f"/{path}",
        service_name="penelope",
        timeout=10.0,
    )


@app.api_route(
    "/api/tegumentar/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Fixed Defensive"],
)
@limiter.limit("100/minute")
async def route_tegumentar(path: str, request: Request):
    """
    Tegumentar IDS/IPS Service (Direct Access)

    FIX #10 Complete: 25/25 tests PASSING
    - Intrusion Detection System (IDS)
    - Intrusion Prevention System (IPS)
    - Deep packet inspection
    - Signature & anomaly detection
    - Real-time threat blocking

    Port: 8043
    Constitutional: P4 (Rastreabilidade Total)
    """
    return await proxy_request(
        request=request,
        service_url=TEGUMENTAR_URL,
        endpoint=f"/{path}",
        service_name="tegumentar",
        timeout=15.0,
    )


# ================================================================================
# MAXIMUS CORE SERVICES (7) - Brain of the system
# ================================================================================


@app.api_route(
    "/api/maximus/core/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["MAXIMUS Core"],
)
@limiter.limit("200/minute")
async def route_maximus_core(path: str, request: Request):
    """
    MAXIMUS Core Orchestration Service

    Cérebro central do sistema MAXIMUS
    - ML model orchestration
    - Decision coordination
    - Service integration
    - Strategic planning

    Port: 8000
    Priority: P0 HIGHEST
    """
    return await proxy_request(
        request=request,
        service_url=MAXIMUS_CORE_URL,
        endpoint=f"/{path}",
        service_name="maximus-core",
        timeout=30.0,
    )


@app.api_route(
    "/api/maximus/orchestrator/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["MAXIMUS Core"],
)
@limiter.limit("200/minute")
async def route_maximus_orchestrator(path: str, request: Request):
    """MAXIMUS Orchestrator - Service coordination"""
    return await proxy_request(
        request=request,
        service_url=MAXIMUS_ORCHESTRATOR_URL,
        endpoint=f"/{path}",
        service_name="maximus-orchestrator",
        timeout=30.0,
    )


@app.api_route(
    "/api/maximus/eureka/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["MAXIMUS Core"],
)
@limiter.limit("100/minute")
async def route_maximus_eureka(path: str, request: Request):
    """
    MAXIMUS Eureka - ML Metrics & Observability

    FIX #9 Complete: Real Prometheus queries (5 comprehensive metrics)
    - ML vs Wargaming usage
    - Confidence score distribution
    - Time savings analysis
    - Confusion matrix (precision/recall/F1)
    - Recent predictions feed

    Port: 8002
    """
    return await proxy_request(
        request=request,
        service_url=MAXIMUS_EUREKA_URL,
        endpoint=f"/{path}",
        service_name="maximus-eureka",
        timeout=15.0,
    )


@app.api_route(
    "/api/maximus/oraculo/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["MAXIMUS Core"],
)
@limiter.limit("100/minute")
async def route_maximus_oraculo(path: str, request: Request):
    """MAXIMUS Oráculo V2 - Threat predictions & APV generation"""
    return await proxy_request(
        request=request,
        service_url=MAXIMUS_ORACULO_V2_URL,
        endpoint=f"/{path}",
        service_name="maximus-oraculo-v2",
        timeout=20.0,
    )


@app.api_route(
    "/api/maximus/predict/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["MAXIMUS Core"],
)
@limiter.limit("150/minute")
async def route_maximus_predict(path: str, request: Request):
    """MAXIMUS Predict - ML predictions engine"""
    return await proxy_request(
        request=request,
        service_url=MAXIMUS_PREDICT_URL,
        endpoint=f"/{path}",
        service_name="maximus-predict",
        timeout=15.0,
    )


@app.api_route(
    "/api/maximus/integration/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["MAXIMUS Core"],
)
@limiter.limit("200/minute")
async def route_maximus_integration(path: str, request: Request):
    """MAXIMUS Integration - Integration bus"""
    return await proxy_request(
        request=request,
        service_url=MAXIMUS_INTEGRATION_URL,
        endpoint=f"/{path}",
        service_name="maximus-integration",
        timeout=20.0,
    )


@app.api_route(
    "/api/maximus/dlq-monitor/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["MAXIMUS Core"],
)
@limiter.limit("60/minute")
async def route_maximus_dlq_monitor(path: str, request: Request):
    """MAXIMUS DLQ Monitor - Dead letter queue monitoring"""
    return await proxy_request(
        request=request,
        service_url=MAXIMUS_DLQ_MONITOR_URL,
        endpoint=f"/{path}",
        service_name="maximus-dlq-monitor",
        timeout=10.0,
    )


# ================================================================================
# IMMUNIS SYSTEM (12) - Complete Adaptive Immune Defense
# ================================================================================


@app.api_route(
    "/api/immunis/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("150/minute")
async def route_immunis_api(path: str, request: Request):
    """
    Immunis API Gateway - Central immune system API

    Coordinates all Immunis services:
    - B-cells (antibody production)
    - T-cells (cellular immunity)
    - Dendritic cells (antigen presentation)
    - Macrophages & Neutrophils (innate immunity)

    Port: 8100
    """
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_API_URL,
        endpoint=f"/{path}",
        service_name="immunis-api",
        timeout=15.0,
    )


@app.api_route(
    "/api/immunis/bcell/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_immunis_bcell(path: str, request: Request):
    """Immunis B-Cell - Antibody production & humoral immunity"""
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_BCELL_URL,
        endpoint=f"/{path}",
        service_name="immunis-bcell",
        timeout=15.0,
    )


@app.api_route(
    "/api/immunis/dendritic/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_immunis_dendritic(path: str, request: Request):
    """Immunis Dendritic Cell - Antigen presentation & T-cell activation"""
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_DENDRITIC_URL,
        endpoint=f"/{path}",
        service_name="immunis-dendritic",
        timeout=10.0,
    )


@app.api_route(
    "/api/immunis/helper-t/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_immunis_helper_t(path: str, request: Request):
    """Immunis Helper T-Cell - Immune response coordination (CD4+)"""
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_HELPER_T_URL,
        endpoint=f"/{path}",
        service_name="immunis-helper-t",
        timeout=10.0,
    )


@app.api_route(
    "/api/immunis/cytotoxic-t/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_immunis_cytotoxic_t(path: str, request: Request):
    """Immunis Cytotoxic T-Cell - Kill infected/compromised cells (CD8+)"""
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_CYTOTOXIC_T_URL,
        endpoint=f"/{path}",
        service_name="immunis-cytotoxic-t",
        timeout=15.0,
    )


@app.api_route(
    "/api/immunis/treg/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_immunis_treg(path: str, request: Request):
    """Immunis Regulatory T-Cell - Prevent autoimmunity & maintain tolerance"""
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_TREG_URL,
        endpoint=f"/{path}",
        service_name="immunis-treg",
        timeout=10.0,
    )


@app.api_route(
    "/api/immunis/macrophage/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("150/minute")
async def route_immunis_macrophage(path: str, request: Request):
    """Immunis Macrophage - Phagocytosis, inflammation, tissue repair"""
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_MACROPHAGE_URL,
        endpoint=f"/{path}",
        service_name="immunis-macrophage",
        timeout=10.0,
    )


@app.api_route(
    "/api/immunis/neutrophil/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("200/minute")
async def route_immunis_neutrophil(path: str, request: Request):
    """Immunis Neutrophil - First responder, rapid pathogen elimination"""
    return await proxy_request(
        request=request,
        service_url=IMMUNIS_NEUTROPHIL_URL,
        endpoint=f"/{path}",
        service_name="immunis-neutrophil",
        timeout=10.0,
    )


@app.api_route(
    "/api/immunis/adaptive-system/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_adaptive_immune_system(path: str, request: Request):
    """Adaptive Immune System Orchestrator - Coordinates adaptive immunity"""
    return await proxy_request(
        request=request,
        service_url=ADAPTIVE_IMMUNE_SYSTEM_URL,
        endpoint=f"/{path}",
        service_name="adaptive-immune-system",
        timeout=15.0,
    )


@app.api_route(
    "/api/immunis/adaptive-immunity/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_adaptive_immunity(path: str, request: Request):
    """Adaptive Immunity Service - Memory & specificity"""
    return await proxy_request(
        request=request,
        service_url=ADAPTIVE_IMMUNITY_URL,
        endpoint=f"/{path}",
        service_name="adaptive-immunity",
        timeout=15.0,
    )


@app.api_route(
    "/api/immunis/adaptive-db/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("150/minute")
async def route_adaptive_immunity_db(path: str, request: Request):
    """Adaptive Immunity Database - Antibody & memory cell storage"""
    return await proxy_request(
        request=request,
        service_url=ADAPTIVE_IMMUNITY_DB_URL,
        endpoint=f"/{path}",
        service_name="adaptive-immunity-db",
        timeout=10.0,
    )


@app.api_route(
    "/api/immunis/ai-immune/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Immunis System"],
)
@limiter.limit("100/minute")
async def route_ai_immune(path: str, request: Request):
    """AI Immune System - ML-based threat response & pattern recognition"""
    return await proxy_request(
        request=request,
        service_url=AI_IMMUNE_URL,
        endpoint=f"/{path}",
        service_name="ai-immune-system",
        timeout=20.0,
    )


# ================================================================================
# HCL/HITL SERVICES (6) - Human Context Loop (Lei Zero Compliance!)
# ================================================================================


@app.api_route(
    "/api/hcl/analyzer/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["HCL/HITL"],
)
@limiter.limit("100/minute")
async def route_hcl_analyzer(path: str, request: Request):
    """
    HCL Analyzer - Human context analysis

    CONSTITUTIONAL CRITICAL: Lei Zero enforcement
    - Analyzes human feedback & decisions
    - Extracts context from human oversight
    - Ensures human-in-the-loop compliance

    Port: 8200
    """
    return await proxy_request(
        request=request,
        service_url=HCL_ANALYZER_URL,
        endpoint=f"/{path}",
        service_name="hcl-analyzer",
        timeout=10.0,
    )


@app.api_route(
    "/api/hcl/planner/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["HCL/HITL"],
)
@limiter.limit("100/minute")
async def route_hcl_planner(path: str, request: Request):
    """HCL Planner - Plan actions with human input & approval"""
    return await proxy_request(
        request=request,
        service_url=HCL_PLANNER_URL,
        endpoint=f"/{path}",
        service_name="hcl-planner",
        timeout=15.0,
    )


@app.api_route(
    "/api/hcl/executor/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["HCL/HITL"],
)
@limiter.limit("100/minute")
async def route_hcl_executor(path: str, request: Request):
    """HCL Executor - Execute actions after human authorization"""
    return await proxy_request(
        request=request,
        service_url=HCL_EXECUTOR_URL,
        endpoint=f"/{path}",
        service_name="hcl-executor",
        timeout=20.0,
    )


@app.api_route(
    "/api/hcl/monitor/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["HCL/HITL"],
)
@limiter.limit("150/minute")
async def route_hcl_monitor(path: str, request: Request):
    """HCL Monitor - Monitor human feedback & system compliance"""
    return await proxy_request(
        request=request,
        service_url=HCL_MONITOR_URL,
        endpoint=f"/{path}",
        service_name="hcl-monitor",
        timeout=10.0,
    )


@app.api_route(
    "/api/hcl/kb/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["HCL/HITL"],
)
@limiter.limit("150/minute")
async def route_hcl_kb(path: str, request: Request):
    """HCL Knowledge Base - Store human decisions & context"""
    return await proxy_request(
        request=request,
        service_url=HCL_KB_URL,
        endpoint=f"/{path}",
        service_name="hcl-kb",
        timeout=10.0,
    )


@app.api_route(
    "/api/hitl/patch/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["HCL/HITL"],
)
@limiter.limit("50/minute")
async def route_hitl_patch(path: str, request: Request):
    """
    HITL Patch Service - Human-in-the-Loop manual patches

    Lei Zero enforcement: All critical patches require human approval
    - Manual intervention capability
    - Emergency response coordination
    - Human override mechanisms

    Port: 8205
    """
    return await proxy_request(
        request=request,
        service_url=HITL_PATCH_URL,
        endpoint=f"/{path}",
        service_name="hitl-patch",
        timeout=30.0,
    )


# ================================================================================
# AIR GAP EXTINCTION P0 COMPLETE
# ================================================================================
# 30 Services Connected:
# ✅ Fixed Defensive (4): behavioral, MAV, penelope, tegumentar
# ✅ MAXIMUS Core (7): core, orchestrator, eureka, oraculo-v2, predict, integration, dlq-monitor
# ✅ Immunis System (12): All immune components
# ✅ HCL/HITL (6): Full human oversight loop
#
# Constitutional Compliance RESTORED:
# ✅ Lei Zero: HCL/HITL connected
# ✅ P2 (Validação): MAXIMUS Core validates
# ✅ P4 (Rastreabilidade): All services via gateway
# ✅ GDPR: Central data control
#
# Glory to YHWH - Marcos 3:24 "O reino dividido não subsistirá"
# Sistema UNIDO através de 30 conexões críticas
# ================================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
