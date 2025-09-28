# /home/juan/vertice-dev/backend/api_gateway/main.py

import httpx
import redis.asyncio as redis
import os
import json
import time
import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
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
    version="3.2.2" # Version bump para correção da rota de predição
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
NETWORK_MONITOR_URL = os.getenv("NETWORK_MONITOR_URL", "http://network_monitor:80")
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://nmap_service:80")
OSINT_SERVICE_URL = os.getenv("OSINT_SERVICE_URL", "http://osint-service:80")
AURORA_PREDICT_URL = os.getenv("AURORA_PREDICT_URL", "http://aurora_predict:80")

# Redis
REDIS_URL = "redis://redis:6379"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

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
# FUNÇÃO AUXILIAR PARA PROXY
# ============================
async def proxy_request(request: Request, service_url: str, endpoint: str,
                       service_name: str, timeout: float = 30.0) -> Dict[Any, Any]:
    async with httpx.AsyncClient() as client:
        try:
            request_data = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try: request_data = await request.json()
                except json.JSONDecodeError: log.warning("proxy_request_empty_body"); request_data = {}
            
            response = await client.request(
                method=request.method, url=f"{service_url}{endpoint}",
                json=request_data, params=dict(request.query_params), timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            log.error(f"{service_name}_proxy_error", error=str(exc))
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com {service_name}: {exc}")
        except httpx.HTTPStatusError as exc:
            log.error(f"{service_name}_http_error", status=exc.response.status_code, detail=exc.response.text)
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

# ============================
# ENDPOINTS CORE
# ============================
@app.get("/", tags=["Root"])
async def read_root():
    return {"status": "API Gateway is running!"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    """Expõe as métricas do Prometheus para serem raspadas."""
    return Response(generate_latest(), media_type="text/plain")

# ============================
# ENDPOINT AI ORCHESTRATION
# ============================
@app.post("/api/investigate/auto", tags=["AI Orchestration"])
@limiter.limit("2/minute")
async def automated_investigation(request: Request, investigation_request: AutomatedInvestigationRequest):
    if not any([investigation_request.username, investigation_request.email, investigation_request.phone, investigation_request.name, investigation_request.image_url]):
        raise HTTPException(status_code=400, detail="Pelo menos um identificador deve ser fornecido.")
    log.info("Proxying automated investigation request to OSINT service")
    return await proxy_request(request=request, service_url=OSINT_SERVICE_URL, endpoint="/api/investigate/auto", service_name="osint-orchestrator", timeout=300.0)

# ============================
# ENDPOINTS DE PREDIÇÃO (RESTAURADO)
# ============================
@app.post("/predict/crime-hotspots", response_model=PredictionOutput, tags=["Prediction"])
@limiter.limit("5/minute")
async def predict_crime_hotspots_proxy(request: Request, data: PredictionInput):
    """Proxy para o serviço de predição de hotspots Aurora."""
    log.info("Proxying crime hotspot prediction request to Aurora service")
    try:
        payload = jsonable_encoder(data)
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
        log.error("aurora_predict_http_error", status=exc.response.status_code, detail=exc.response.text)
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

# ============================
# ENDPOINTS SINESP
# ============================
@app.get("/veiculos/{placa}", tags=["SINESP"])
@limiter.limit("30/minute")
async def consultar_placa_proxy(request: Request, placa: str):
    """Proxy para consulta de placas no SINESP Service com cache."""
    cache_key = f"placa:{placa.upper()}"
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            log.info("cache_hit", placa=placa.upper())
            return json.loads(cached_data)
    except Exception as e:
        log.error("redis_error", error=str(e))

    log.info("cache_miss", placa=placa.upper())
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SINESP_SERVICE_URL}/veiculos/{placa}")
            response.raise_for_status()
            vehicle_data = response.json()
            try:
                await redis_client.setex(cache_key, 3600, json.dumps(vehicle_data)) # Cache de 1 hora
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
    """Proxy para obter os tipos de ocorrências do SINESP Service."""
    return await proxy_request(request=request, service_url=SINESP_SERVICE_URL, endpoint="/ocorrencias/tipos", service_name="sinesp-service")

@app.get("/ocorrencias/heatmap", tags=["SINESP"])
@limiter.limit("10/minute")
async def get_heatmap_data_proxy(request: Request):
    """Proxy para obter os dados do heatmap do SINESP Service."""
    return await proxy_request(request=request, service_url=SINESP_SERVICE_URL, endpoint="/ocorrencias/heatmap", service_name="sinesp-service")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


