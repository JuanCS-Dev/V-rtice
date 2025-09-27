# /home/juan/vertice-dev/backend/api_gateway/main.py

import httpx
import redis.asyncio as redis
import os
import json
import time
import structlog
import websockets
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
from pydantic import BaseModel

log = structlog.get_logger()
REQUESTS_TOTAL = Counter("api_requests_total", "Total de pedidos recebidos", ["method", "path", "status_code"])
RESPONSE_TIME = Histogram("api_response_time_seconds", "Tempo de resposta dos pedidos", ["method", "path"])
limiter = Limiter(key_func=get_remote_address)

app = FastAPI( 
    title="Projeto VÉRTICE - API Gateway", 
    description="Ponto de entrada unificado com cache, rate limiting, observability e cyber security.", 
    version="2.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["http://localhost:5173"]
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=origins, 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

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
    log.info( 
        "request_processed", 
        method=method, 
        path=request.url.path, 
        status_code=status_code, 
        process_time=round(process_time, 4)
    )
    return response

# URLs dos serviços
SINESP_SERVICE_URL = os.getenv("SINESP_SERVICE_URL", "http://sinesp_service:8001")
CYBER_SERVICE_URL = os.getenv("CYBER_SERVICE_URL", "http://cyber_service:8002")
DOMAIN_SERVICE_URL = os.getenv("DOMAIN_SERVICE_URL", "http://domain_service:8003")
IP_INTELLIGENCE_SERVICE_URL = os.getenv("IP_INTELLIGENCE_SERVICE_URL", "http://ip_intelligence_service:8004")
NETWORK_MONITOR_SERVICE_URL = os.getenv("NETWORK_MONITOR_SERVICE_URL", "http://network_monitor_service:8005")
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://nmap_service:8006")

REDIS_URL = "redis://redis:6379"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
CACHE_EXPIRATION_SECONDS = 3600

# Modelos para requests
class NetworkScanRequest(BaseModel):
    target: str
    profile: str = "self-check"

class DomainAnalysisRequest(BaseModel):
    domain: str

class IPAnalysisRequest(BaseModel):
    ip: str

class NetworkMonitorConfigRequest(BaseModel):
    window_seconds: int = 12
    spike_threshold: int = 30
    syn_recv_threshold: int = 60
    portscan_ports_threshold: int = 15
    persistent_scan_threshold: int = 3
    debounce_seconds: int = 20

class NmapScanRequest(BaseModel):
    target: str
    profile: str = "quick"
    custom_args: Optional[str] = None

@app.get("/metrics", tags=["Monitoring"])
def get_metrics(): 
    return Response(generate_latest(), media_type="text/plain")

@app.get("/", tags=["Root"])
async def read_root(): 
    return {"status": "API Gateway is running with Cyber Security!"}

# --- ENDPOINTS IP INTELLIGENCE ---

@app.post("/ip/analyze", tags=["IP Intelligence"])
@limiter.limit("5/minute")
async def ip_analyze(request: Request, ip_request: IPAnalysisRequest):
    """Proxy para análise completa de IP"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{IP_INTELLIGENCE_SERVICE_URL}/analyze",
                json=ip_request.dict(),
                timeout=60  # Timeout maior para análise completa
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503, 
                detail=f"Erro de comunicação com o serviço de análise de IP: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=exc.response.json().get("detail", exc.response.text)
            )

@app.get("/ip/health", tags=["IP Intelligence"])
@limiter.limit("10/minute")
async def ip_health(request: Request):
    """Health check do IP Intelligence Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{IP_INTELLIGENCE_SERVICE_URL}/", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de IP: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

# --- ENDPOINTS DOMAIN ANALYSIS ---

@app.post("/domain/analyze", tags=["Domain Analysis"])
@limiter.limit("3/minute")
async def domain_analyze(request: Request, domain_request: DomainAnalysisRequest):
    """Proxy para análise completa de domínio"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DOMAIN_SERVICE_URL}/analyze",
                json=domain_request.dict(),
                timeout=45
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503, 
                detail=f"Erro de comunicação com o serviço de análise de domínio: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=exc.response.json().get("detail", exc.response.text)
            )

@app.get("/domain/health", tags=["Domain Analysis"])
@limiter.limit("10/minute")
async def domain_health(request: Request):
    """Health check do Domain Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DOMAIN_SERVICE_URL}/", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de domínio: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

# --- ENDPOINTS NETWORK MONITOR ---

@app.get("/network-monitor/health", tags=["Network Monitor"])
@limiter.limit("10/minute")
async def network_monitor_health(request: Request):
    """Health check do Network Monitor Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NETWORK_MONITOR_SERVICE_URL}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de network monitor: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/network-monitor/stats", tags=["Network Monitor"])
@limiter.limit("5/minute")
async def network_monitor_stats(request: Request):
    """Proxy para estatísticas do monitor de rede"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NETWORK_MONITOR_SERVICE_URL}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de network monitor: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/network-monitor/config", tags=["Network Monitor"])
@limiter.limit("5/minute")
async def network_monitor_get_config(request: Request):
    """Proxy para configuração do monitor"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NETWORK_MONITOR_SERVICE_URL}/config", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de network monitor: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.put("/network-monitor/config", tags=["Network Monitor"])
@limiter.limit("2/minute")
async def network_monitor_update_config(request: Request, config_request: NetworkMonitorConfigRequest):
    """Proxy para atualizar configuração do monitor"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{NETWORK_MONITOR_SERVICE_URL}/config",
                json=config_request.dict(),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503, 
                detail=f"Erro de comunicação com o serviço de network monitor: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=exc.response.json().get("detail", exc.response.text)
            )

@app.post("/network-monitor/start", tags=["Network Monitor"])
@limiter.limit("2/minute")
async def network_monitor_start(request: Request):
    """Proxy para iniciar monitoramento"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{NETWORK_MONITOR_SERVICE_URL}/start", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de network monitor: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.post("/network-monitor/stop", tags=["Network Monitor"])
@limiter.limit("2/minute")
async def network_monitor_stop(request: Request):
    """Proxy para parar monitoramento"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{NETWORK_MONITOR_SERVICE_URL}/stop", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de network monitor: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.websocket("/network-monitor/ws/alerts")
async def network_monitor_websocket_alerts(websocket: WebSocket):
    """WebSocket proxy para alertas do Network Monitor em tempo real"""
    await websocket.accept()
    
    try:
        ws_url = NETWORK_MONITOR_SERVICE_URL.replace("http://", "ws://") + "/ws/alerts"
        
        async with websockets.connect(ws_url) as backend_ws:
            async for message in backend_ws:
                await websocket.send_text(message)
                
    except WebSocketDisconnect:
        log.info("Cliente WebSocket desconectado")
    except Exception as e:
        log.error("Erro no WebSocket proxy", error=str(e))
        await websocket.close(code=1011, reason=f"Erro interno: {str(e)}")

# --- ENDPOINTS NMAP SERVICE ---

@app.get("/nmap/health", tags=["Nmap Scanner"])
@limiter.limit("10/minute")
async def nmap_health(request: Request):
    """Health check do Nmap Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NMAP_SERVICE_URL}/", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de nmap: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/nmap/profiles", tags=["Nmap Scanner"])
@limiter.limit("5/minute")
async def nmap_profiles(request: Request):
    """Proxy para perfis de scan disponíveis"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NMAP_SERVICE_URL}/profiles", timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de nmap: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.post("/nmap/scan", tags=["Nmap Scanner"])
@limiter.limit("1/minute")  # Limite muito restrito para scans
async def nmap_scan(request: Request, scan_request: NmapScanRequest):
    """Proxy para execução de scan Nmap"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NMAP_SERVICE_URL}/scan",
                json=scan_request.dict(),
                timeout=320  # Timeout maior para scans
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503, 
                detail=f"Erro de comunicação com o serviço de nmap: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=exc.response.json().get("detail", exc.response.text)
            )

# --- ENDPOINTS CYBER SECURITY ---

@app.post("/cyber/network-scan", tags=["Cyber Security"])
@limiter.limit("2/minute")  # Limite restrito para scans
async def cyber_network_scan(request: Request, scan_request: NetworkScanRequest):
    """Proxy para network scan do cyber service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CYBER_SERVICE_URL}/cyber/network-scan",
                json=scan_request.dict(),
                timeout=60  # Timeout maior para scans
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503, 
                detail=f"Erro de comunicação com o serviço cyber: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=exc.response.json().get("detail", exc.response.text)
            )

@app.get("/cyber/port-analysis", tags=["Cyber Security"])
@limiter.limit("5/minute")
async def cyber_port_analysis(request: Request):
    """Proxy para análise de portas"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CYBER_SERVICE_URL}/cyber/port-analysis", timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço cyber: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/cyber/file-integrity", tags=["Cyber Security"])
@limiter.limit("3/minute")
async def cyber_file_integrity(request: Request):
    """Proxy para verificação de integridade de arquivos"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CYBER_SERVICE_URL}/cyber/file-integrity", timeout=45)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço cyber: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/cyber/process-analysis", tags=["Cyber Security"])
@limiter.limit("5/minute")
async def cyber_process_analysis(request: Request):
    """Proxy para análise de processos"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CYBER_SERVICE_URL}/cyber/process-analysis", timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço cyber: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/cyber/certificate-check", tags=["Cyber Security"])
@limiter.limit("3/minute")
async def cyber_certificate_check(request: Request):
    """Proxy para verificação de certificados"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CYBER_SERVICE_URL}/cyber/certificate-check", timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço cyber: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/cyber/security-config", tags=["Cyber Security"])
@limiter.limit("5/minute")
async def cyber_security_config(request: Request):
    """Proxy para verificação de configurações de segurança"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CYBER_SERVICE_URL}/cyber/security-config", timeout=20)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço cyber: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/cyber/security-logs", tags=["Cyber Security"])
@limiter.limit("3/minute")
async def cyber_security_logs(request: Request):
    """Proxy para análise de logs de segurança"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CYBER_SERVICE_URL}/cyber/security-logs", timeout=25)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço cyber: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

# --- ENDPOINTS SINESP (EXISTENTES) ---

@app.get("/ocorrencias/heatmap", tags=["Heatmap"])
@limiter.limit("5/minute")
async def get_heatmap_data_proxy(request: Request):
    cache_key = "heatmap:data"
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            log.info("heatmap_cache_hit")
            return json.loads(cached_data)
    except Exception as e:
        log.error("redis_error_heatmap", error=str(e))

    log.info("heatmap_cache_miss")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SINESP_SERVICE_URL}/ocorrencias/heatmap")
            response.raise_for_status()
            heatmap_data = response.json()
            try:
                await redis_client.setex(cache_key, 3600, json.dumps(heatmap_data))
            except Exception as e:
                 log.error("redis_save_error_heatmap", error=str(e))
            return heatmap_data
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de ocorrências: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))

@app.get("/veiculos/{placa}", tags=["Consultas"])
@limiter.limit("10/minute")
async def consultar_placa_com_cache(request: Request, placa: str):
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
                await redis_client.setex(cache_key, CACHE_EXPIRATION_SECONDS, json.dumps(vehicle_data))
            except Exception as e:
                 log.error("redis_save_error", error=str(e))
            return vehicle_data
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação com o serviço de consulta: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", exc.response.text))
