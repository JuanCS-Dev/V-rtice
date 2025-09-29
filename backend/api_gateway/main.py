# /home/juan/vertice-dev/backend/api_gateway/main.py

import httpx
import redis.asyncio as redis
import os
import json
import time
import structlog
import jwt
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
from pydantic import BaseModel

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

# Métricas Prometheus
REQUESTS_TOTAL = Counter("api_requests_total", "Total de pedidos recebidos", ["method", "path", "status_code"])
RESPONSE_TIME = Histogram("api_response_time_seconds", "Tempo de resposta dos pedidos", ["method", "path"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title="Projeto VÉRTICE - API Gateway",
    description="Ponto de entrada unificado com cache, rate limiting, observability, cyber security e OSINT completo.",
    version="3.3.1" # Version bump para correção do Redis
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
origins = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Middleware de monitoramento
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    path_template = request.scope.get("route").path if request.scope.get("route") else request.url.path
    method = request.method
    status_code = response.status_code
    
    REQUESTS_TOTAL.labels(method=method, path=path_template, status_code=status_code).inc()
    RESPONSE_TIME.labels(method=method, path=path_template).observe(process_time)
    
    log.info("request_processed",
             method=method,
             path=request.url.path,
             status_code=status_code,
             process_time=round(process_time, 4))
    
    return response

# ============================
# URLs DOS SERVIÇOS INTERNOS
# ============================
SINESP_SERVICE_URL = os.getenv("SINESP_SERVICE_URL", "http://sinesp_service:80")
CYBER_SERVICE_URL = os.getenv("CYBER_SERVICE_URL", "http://cyber_service:80")
DOMAIN_SERVICE_URL = os.getenv("DOMAIN_SERVICE_URL", "http://domain_service:80")
IP_INTEL_SERVICE_URL = os.getenv("IP_INTEL_SERVICE_URL", "http://ip_intelligence_service:80")
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://nmap_service:80")
NETWORK_MONITOR_SERVICE_URL = os.getenv("NETWORK_MONITOR_SERVICE_URL", "http://network_monitor_service:80")
OSINT_SERVICE_URL = os.getenv("OSINT_SERVICE_URL", "http://osint-service:80")
AURORA_PREDICT_URL = os.getenv("AURORA_PREDICT_URL", "http://aurora_predict:80")
ATLAS_SERVICE_URL = os.getenv("ATLAS_SERVICE_URL", "http://atlas_service:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:80")

# Authentication configuration
JWT_SECRET = os.getenv("JWT_SECRET", "vertice-super-secret-key-2024")
security = HTTPBearer()

# ============================
# CONEXÃO COM REDIS (CORRIGIDA)
# ============================
REDIS_URL = "redis://redis:6379/0"
redis_client = None

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=5)
    log.info("Redis client configured successfully.")
except Exception as e:
    log.error("Could not configure Redis client", error=str(e), detail="API Gateway will operate without cache.")
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

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
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
                detail=f"Permission '{permission}' required. Available: {user.get('permissions', [])}"
            )
        return user
    return permission_dependency

# Optional auth - allows both authenticated and unauthenticated access
async def optional_auth(authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
async def proxy_request(request: Request, service_url: str, endpoint: str,
                       service_name: str, timeout: float = 30.0, is_text_body: bool = False) -> Any:
    async with httpx.AsyncClient() as client:
        try:
            headers = {key: value for key, value in request.headers.items() if key.lower() not in ['host', 'content-length']}
            
            content = None
            if request.method in ["POST", "PUT", "PATCH"]:
                if is_text_body:
                    content = await request.body()
                    headers['content-type'] = 'text/plain'
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
                timeout=timeout
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text

        except httpx.RequestError as exc:
            log.error(f"{service_name}_proxy_error", error=str(exc))
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com {service_name}: {exc}")
        except httpx.HTTPStatusError as exc:
            log.error(f"{service_name}_http_error", status=exc.response.status_code, detail=exc.response.text)
            detail = exc.response.json().get("detail", exc.response.text) if "application/json" in exc.response.headers.get("content-type", "") else exc.response.text
            raise HTTPException(status_code=exc.response.status_code, detail=detail)


# ============================
# ENDPOINTS
# ============================
@app.get("/", tags=["Root"])
async def read_root():
    return {"status": "API Gateway is running!"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

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
        log.warning("redis_unavailable", detail="Redis client not connected. Skipping cache.")

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
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço SINESP: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/ocorrencias/tipos", tags=["SINESP"])
@limiter.limit("10/minute")
async def get_ocorrencia_tipos_proxy(request: Request):
    return await proxy_request(request=request, service_url=SINESP_SERVICE_URL, endpoint=f"/ocorrencias/tipos", service_name="sinesp-service")

@app.get("/ocorrencias/heatmap", tags=["SINESP"])
@limiter.limit("10/minute")
async def get_heatmap_data_proxy(request: Request):
    return await proxy_request(request=request, service_url=SINESP_SERVICE_URL, endpoint=f"/ocorrencias/heatmap", service_name="sinesp-service")
# ============================================

@app.api_route("/atlas/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Atlas GIS"])
@limiter.limit("60/minute")
async def atlas_proxy(request: Request, full_path: str):
    endpoint = f"/{full_path}"
    log.info("Proxying request to Atlas GIS service", endpoint=endpoint)
    is_text = full_path == "query/" and request.method == "POST"
    return await proxy_request(
        request=request, service_url=ATLAS_SERVICE_URL, endpoint=endpoint,
        service_name="atlas-gis-service", is_text_body=is_text
    )

# ============================
# ROTAS CYBER SERVICE
# ============================
@app.post("/cyber/network-scan", tags=["Cyber Security"])
@limiter.limit("5/minute")
async def cyber_network_scan_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/cyber/network-scan", service_name="cyber-service", timeout=60.0)

@app.get("/cyber/port-analysis", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_port_analysis_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/cyber/port-analysis", service_name="cyber-service")

@app.get("/cyber/file-integrity", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_file_integrity_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/cyber/file-integrity", service_name="cyber-service")

@app.get("/cyber/process-analysis", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_process_analysis_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/cyber/process-analysis", service_name="cyber-service")

@app.get("/cyber/certificate-check", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_certificate_check_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/cyber/certificate-check", service_name="cyber-service")

@app.get("/cyber/security-config", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_security_config_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/cyber/security-config", service_name="cyber-service")

@app.get("/cyber/security-logs", tags=["Cyber Security"])
@limiter.limit("10/minute")
async def cyber_security_logs_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/cyber/security-logs", service_name="cyber-service")

@app.get("/cyber/health", tags=["Cyber Security"])
async def cyber_health_check_proxy(request: Request):
    return await proxy_request(request=request, service_url=CYBER_SERVICE_URL, endpoint="/", service_name="cyber-service")

# ============================
# ROTAS NMAP SERVICE
# ============================
@app.post("/api/nmap/scan", tags=["Network Scanning"])
@limiter.limit("3/minute")
async def nmap_scan_proxy(request: Request):
    return await proxy_request(request=request, service_url=NMAP_SERVICE_URL, endpoint="/scan", service_name="nmap-service", timeout=180.0)

@app.get("/api/nmap/profiles", tags=["Network Scanning"])
@limiter.limit("30/minute")
async def nmap_profiles_proxy(request: Request):
    return await proxy_request(request=request, service_url=NMAP_SERVICE_URL, endpoint="/profiles", service_name="nmap-service")

@app.get("/nmap/health", tags=["Network Scanning"])
async def nmap_health_check_proxy(request: Request):
    return await proxy_request(request=request, service_url=NMAP_SERVICE_URL, endpoint="/", service_name="nmap-service")

# ============================
# ROTAS DOMAIN SERVICE
# ============================
@app.post("/api/domain/analyze", tags=["Domain Intelligence"])
@limiter.limit("10/minute")
async def domain_analyze_proxy(request: Request):
    return await proxy_request(request=request, service_url=DOMAIN_SERVICE_URL, endpoint="/analyze", service_name="domain-service", timeout=60.0)

@app.get("/domain/health", tags=["Domain Intelligence"])
async def domain_health_check_proxy(request: Request):
    return await proxy_request(request=request, service_url=DOMAIN_SERVICE_URL, endpoint="/", service_name="domain-service")

# ============================
# ROTAS IP INTELLIGENCE SERVICE
# ============================
@app.post("/api/ip/analyze", tags=["IP Intelligence"])
@limiter.limit("15/minute")
async def ip_analyze_proxy(request: Request):
    return await proxy_request(request=request, service_url=IP_INTEL_SERVICE_URL, endpoint="/analyze", service_name="ip-intelligence-service", timeout=60.0)

@app.get("/ip/health", tags=["IP Intelligence"])
async def ip_health_check_proxy(request: Request):
    return await proxy_request(request=request, service_url=IP_INTEL_SERVICE_URL, endpoint="/", service_name="ip-intelligence-service")

# ============================
# ROTAS NETWORK MONITOR SERVICE
# ============================
@app.get("/api/network/monitor", tags=["Network Monitoring"])
@limiter.limit("20/minute")
async def network_monitor_proxy(request: Request):
    return await proxy_request(request=request, service_url=NETWORK_MONITOR_SERVICE_URL, endpoint="/stats", service_name="network-monitor-service")

@app.get("/network/health", tags=["Network Monitoring"])
async def network_health_check_proxy(request: Request):
    return await proxy_request(request=request, service_url=NETWORK_MONITOR_SERVICE_URL, endpoint="/", service_name="network-monitor-service")

# ============================
# ROTAS OSINT SERVICE
# ============================
@app.post("/api/investigate/auto", tags=["OSINT"])
@limiter.limit("2/minute")
async def automated_investigation(request: Request, investigation_request: AutomatedInvestigationRequest):
    if not any([investigation_request.username, investigation_request.email, investigation_request.phone, investigation_request.name, investigation_request.image_url]):
        raise HTTPException(status_code=400, detail="Pelo menos um identificador deve ser fornecido.")
    log.info("Proxying automated investigation request to OSINT service")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{OSINT_SERVICE_URL}/api/investigate/auto", json=jsonable_encoder(investigation_request), timeout=300.0)
        response.raise_for_status()
        return response.json()

@app.post("/api/username/search", tags=["OSINT"])
@limiter.limit("10/minute")
async def search_username_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/api/username/search", service_name="osint-service", timeout=120.0)

@app.post("/api/email/analyze", tags=["OSINT"])
@limiter.limit("10/minute")
async def analyze_email_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/api/email/analyze", service_name="osint-service", timeout=120.0)

@app.post("/api/phone/analyze", tags=["OSINT"])
@limiter.limit("10/minute")
async def analyze_phone_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/api/phone/analyze", service_name="osint-service", timeout=120.0)

@app.post("/api/social/profile", tags=["OSINT"])
@limiter.limit("5/minute")
async def get_social_profile_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/api/social/profile", service_name="osint-service", timeout=180.0)

@app.post("/api/image/analyze", tags=["OSINT"])
@limiter.limit("3/minute")
async def analyze_image_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/api/image/analyze", service_name="osint-service", timeout=300.0)

@app.post("/api/search/comprehensive", tags=["OSINT"])
@limiter.limit("5/minute")
async def comprehensive_search_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/api/search/comprehensive", service_name="osint-service", timeout=240.0)

@app.get("/api/osint/stats", tags=["OSINT"])
@limiter.limit("30/minute")
async def get_osint_stats_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/api/stats", service_name="osint-service")

@app.get("/api/osint/health", tags=["OSINT"])
async def osint_health_check_proxy(request: Request):
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint=f"/health", service_name="osint-service")

@app.post("/predict/crime-hotspots", response_model=PredictionOutput, tags=["Prediction"])
@limiter.limit("5/minute")
async def predict_crime_hotspots_proxy(request: Request, data: PredictionInput):
    log.info("Proxying crime hotspot prediction request to Aurora service")
    try:
        # Extrai os parâmetros de sensibilidade do payload da requisição
        body = await request.json()
        payload = {
            "occurrences": body.get("occurrences", []),
            "eps_km": body.get("eps_km"),
            "min_samples": body.get("min_samples")
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AURORA_PREDICT_URL}/predict/crime-hotspots",
                json=payload,
                timeout=90.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        log.error("aurora_predict_proxy_error", error=str(exc))
        raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de predição: {exc}")
    except httpx.HTTPStatusError as exc:
        log.error("aurora_predict_http_error", status=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

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
        service_name="auth-service"
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
        "permissions": user.get("permissions", [])
    }

@app.post("/auth/logout", tags=["Authentication"])
async def logout(request: Request, user: Dict[str, Any] = Depends(verify_token)):
    """Logout user"""
    return await proxy_request(
        request=request,
        service_url=AUTH_SERVICE_URL,
        endpoint="/auth/logout",
        service_name="auth-service"
    )

@app.get("/auth/verify-token", tags=["Authentication"])
async def verify_token_route(user: Dict[str, Any] = Depends(verify_token)):
    """Verify token validity"""
    return {
        "valid": True,
        "user_id": user["sub"],
        "permissions": user.get("permissions", [])
    }

# ============================
# PROTECTED ROUTES EXAMPLES
# ============================

@app.get("/protected/admin", tags=["Protected"])
async def admin_only(user: Dict[str, Any] = Depends(require_permission("admin"))):
    """Admin only endpoint"""
    return {"message": "Admin access granted", "user": user["email"]}

@app.get("/protected/offensive", tags=["Protected"])
async def offensive_tools_access(user: Dict[str, Any] = Depends(require_permission("offensive"))):
    """Offensive tools access"""
    return {"message": "Offensive tools access granted", "user": user["email"]}

@app.get("/protected/analyst", tags=["Protected"])
async def analyst_access(user: Dict[str, Any] = Depends(require_permission("write"))):
    """Analyst access"""
    return {"message": "Analyst access granted", "user": user["email"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
