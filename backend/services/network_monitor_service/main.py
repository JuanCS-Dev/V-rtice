# backend/services/network_monitor_service/main.py

"""
Network Monitor Service - Vértice
Migração e adaptação do net_monitor.py do Batman do Cerrado
Monitoramento assíncrono de rede com detecção de comportamentos suspeitos em tempo real
"""

import asyncio
import json
import re
import subprocess
import sys
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Deque

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# --- Modelos de Dados ---

class NetworkAlert(BaseModel):
    timestamp: datetime
    target: str
    alert_type: str
    severity: str  # info, medium, high, critical
    description: str
    details: Dict[str, Any]
    source: str = "network_monitor"

class NetworkStats(BaseModel):
    active_connections: int
    listening_ports: int
    unique_ips: int
    total_alerts: int
    alerts_by_severity: Dict[str, int]
    uptime_seconds: int

class MonitorConfig(BaseModel):
    window_seconds: int = Field(default=12, description="Janela de tempo para análise")
    spike_threshold: int = Field(default=30, description="Threshold para pico de conexões")
    syn_recv_threshold: int = Field(default=60, description="Threshold para SYN flood")
    portscan_ports_threshold: int = Field(default=15, description="Threshold para port scan")
    persistent_scan_threshold: int = Field(default=3, description="Threshold para scan persistente")
    debounce_seconds: int = Field(default=20, description="Debounce para evitar spam")

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: int
    monitoring_active: bool
    ss_available: bool

# --- Regex e Helpers ---
ADDR_RE = re.compile(r"(.+?):(\*|\d+)$")

def parse_addr(addr: str) -> Tuple[str, str]:
    """Extrai IP/host e porta de uma string 'addr:port'."""
    match = ADDR_RE.search(addr.strip())
    return (match.group(1), match.group(2)) if match else (addr, "")

# --- Controle de Flood/Ruído ---
class FindingDeduplicator:
    """Deduplicador e debounce para findings, para evitar floods de alertas repetidos."""
    def __init__(self, debounce_seconds: int = 20):
        self.last_finding: Dict[str, float] = defaultdict(float)
        self.debounce_seconds = debounce_seconds

    def should_emit(self, key: str) -> bool:
        now = time.time()
        if now - self.last_finding[key] < self.debounce_seconds:
            return False
        self.last_finding[key] = now
        return True

# --- Motor de Detecção Assíncrono ---
class NetworkDetector:
    """Motor de detecção assíncrono para comportamentos suspeitos em conexões de rede."""
    
    def __init__(self, config: MonitorConfig):
        self.config = config
        self.dedup = FindingDeduplicator(config.debounce_seconds)
        
        # Estado do detector
        self.last_listen_check: Dict[str, Any] = {}
        self.first_seen: Set[str] = set()
        self.ip_buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self.port_buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self.scan_buckets: Dict[str, Deque[Tuple[float, str]]] = defaultdict(deque)
        self.syn_recv_buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self.persistent_scan_cache: Dict[str, List[float]] = defaultdict(list)
        
        # Estatísticas
        self.stats = {
            "total_alerts": 0,
            "alerts_by_severity": {"info": 0, "medium": 0, "high": 0, "critical": 0},
            "start_time": time.time()
        }
        
        # Filas para WebSocket
        self.alert_queues: List[asyncio.Queue] = []

    async def run_ss(self, args: List[str]) -> str:
        """Executa 'ss' (socket stat) de forma assíncrona."""
        cmd = ["ss", "-H", "-n"] + args
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5)
            return stdout.decode('utf-8', errors='ignore')
        except (asyncio.TimeoutError, FileNotFoundError):
            return ""

    async def emit_alert(self, alert: NetworkAlert):
        """Emite um alerta para todas as conexões WebSocket ativas."""
        self.stats["total_alerts"] += 1
        self.stats["alerts_by_severity"][alert.severity] += 1
        
        # Adiciona à fila de todos os clientes WebSocket
        for queue in self.alert_queues:
            try:
                await queue.put(alert)
            except:
                pass  # Cliente desconectado

    async def check_new_listens(self):
        """Detecta novas portas abertas/listen."""
        output = await self.run_ss(["-ltup"])
        current_listens = {}
        
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            proto, _, _, local_addr, _ = parts[0], parts[1], parts[2], parts[3], parts[4]
            _, port = parse_addr(local_addr)
            key = f"{proto}:{port}"
            current_listens[key] = line

        for key, data in current_listens.items():
            if key not in self.last_listen_check and self.dedup.should_emit(f"listen:{key}"):
                alert = NetworkAlert(
                    timestamp=datetime.now(),
                    target="localhost",
                    alert_type="new_listen",
                    severity="medium",
                    description=f"Nova porta em escuta detectada: {key}",
                    details={"raw_ss_line": data, "service": key}
                )
                await self.emit_alert(alert)
                
        self.last_listen_check = current_listens

    async def check_connections(self):
        """
        Detecta:
        - Primeiro contato de IP
        - Picos de conexões ("connection spike")
        - Varredura de portas (port scan)
        - SYN flood/SYN_RECV spikes
        - Escaneamento persistente
        """
        output = await self.run_ss(["-taup"])
        now = time.time()
        time_limit = now - self.config.window_seconds

        # Limpa buckets de eventos antigos
        for bucket in [self.ip_buckets, self.port_buckets]:
            for key in list(bucket):
                while bucket[key] and bucket[key][0] < time_limit:
                    bucket[key].popleft()
        
        for key in list(self.scan_buckets):
            while self.scan_buckets[key] and self.scan_buckets[key][0][0] < time_limit:
                self.scan_buckets[key].popleft()
        
        for key in list(self.syn_recv_buckets):
            while self.syn_recv_buckets[key] and self.syn_recv_buckets[key][0] < time_limit:
                self.syn_recv_buckets[key].popleft()

        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue
            proto, state, _, local_addr, peer_addr, _ = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]

            # Detecta SYN_RECV (SYN flood)
            if state == "SYN-RECV":
                rip, _ = parse_addr(peer_addr)
                if rip and rip != "0.0.0.0":
                    self.syn_recv_buckets[rip].append(now)
                    if len(self.syn_recv_buckets[rip]) >= self.config.syn_recv_threshold and self.dedup.should_emit(f"synrecv:{rip}"):
                        alert = NetworkAlert(
                            timestamp=datetime.now(),
                            target=rip,
                            alert_type="syn_flood",
                            severity="critical",
                            description=f"Possível SYN flood detectado do IP {rip}",
                            details={
                                "count": len(self.syn_recv_buckets[rip]),
                                "window_sec": self.config.window_seconds,
                                "attack_type": "ddos"
                            }
                        )
                        await self.emit_alert(alert)
                continue

            if state == "LISTEN":
                continue

            rip, rport = parse_addr(peer_addr)
            _, lport = parse_addr(local_addr)
            if rip == "0.0.0.0" or not rip:
                continue

            # Primeiro contato de IP externo
            if rip not in self.first_seen and self.dedup.should_emit(f"first_seen:{rip}"):
                self.first_seen.add(rip)
                alert = NetworkAlert(
                    timestamp=datetime.now(),
                    target=rip,
                    alert_type="first_contact",
                    severity="info",
                    description=f"Primeiro contato detectado do IP {rip}",
                    details={
                        "remote_port": rport,
                        "local_port": lport,
                        "protocol": proto
                    }
                )
                await self.emit_alert(alert)

            # Pico de conexões abertas vindas do IP
            self.ip_buckets[rip].append(now)
            port_key = f"{proto}:{lport}"
            self.port_buckets[port_key].append(now)
            
            if len(self.ip_buckets[rip]) >= self.config.spike_threshold and self.dedup.should_emit(f"spike:{rip}"):
                alert = NetworkAlert(
                    timestamp=datetime.now(),
                    target=rip,
                    alert_type="connection_spike",
                    severity="high",
                    description=f"Pico de conexões detectado do IP {rip}",
                    details={
                        "count": len(self.ip_buckets[rip]),
                        "window_sec": self.config.window_seconds,
                        "attack_type": "potential_ddos"
                    }
                )
                await self.emit_alert(alert)

            # Varredura de portas
            self.scan_buckets[rip].append((now, lport))
            unique_ports = {port for _, port in self.scan_buckets[rip]}
            
            if len(unique_ports) >= self.config.portscan_ports_threshold and self.dedup.should_emit(f"portscan:{rip}"):
                alert = NetworkAlert(
                    timestamp=datetime.now(),
                    target=rip,
                    alert_type="port_scan",
                    severity="critical",
                    description=f"Varredura de portas detectada do IP {rip}",
                    details={
                        "ports_hit": sorted(list(unique_ports))[:20],
                        "port_count": len(unique_ports),
                        "attack_type": "reconnaissance"
                    }
                )
                await self.emit_alert(alert)
                
                # Armazena para detecção de scan persistente
                self.persistent_scan_cache[rip].append(now)

            # Detecção de escaneamento persistente
            times = self.persistent_scan_cache[rip]
            self.persistent_scan_cache[rip] = [t for t in times if t > now - 600]  # Últimos 10 min
            
            if len(self.persistent_scan_cache[rip]) >= self.config.persistent_scan_threshold and self.dedup.should_emit(f"persistent_scan:{rip}"):
                alert = NetworkAlert(
                    timestamp=datetime.now(),
                    target=rip,
                    alert_type="persistent_portscan",
                    severity="critical",
                    description=f"Varredura persistente detectada do IP {rip}",
                    details={
                        "scan_count": len(self.persistent_scan_cache[rip]),
                        "period_min": 10,
                        "attack_type": "advanced_reconnaissance"
                    }
                )
                await self.emit_alert(alert)

    async def get_stats(self) -> NetworkStats:
        """Retorna estatísticas atuais do monitor."""
        # Conta conexões ativas e portas em escuta
        connections_output = await self.run_ss(["-taup"])
        listen_output = await self.run_ss(["-ltup"])
        
        active_connections = len([line for line in connections_output.splitlines() if line.strip()])
        listening_ports = len([line for line in listen_output.splitlines() if line.strip()])
        unique_ips = len(self.first_seen)
        
        return NetworkStats(
            active_connections=active_connections,
            listening_ports=listening_ports,
            unique_ips=unique_ips,
            total_alerts=self.stats["total_alerts"],
            alerts_by_severity=self.stats["alerts_by_severity"],
            uptime_seconds=int(time.time() - self.stats["start_time"])
        )

    async def monitor_loop(self, interval: float = 2.0):
        """Loop principal do monitor."""
        while True:
            try:
                await asyncio.gather(
                    self.check_new_listens(),
                    self.check_connections()
                )
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Erro no loop de monitoramento: {e}")
                await asyncio.sleep(interval)

# --- FastAPI App ---
app = FastAPI(
    title="Network Monitor Service",
    description="Serviço de monitoramento de rede em tempo real - Vértice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global do detector
detector_config = MonitorConfig()
detector = NetworkDetector(detector_config)
monitor_task = None

# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check do serviço."""
    # Verifica se o comando 'ss' está disponível
    try:
        process = await asyncio.create_subprocess_exec(
            "ss", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        ss_available = process.returncode == 0
    except FileNotFoundError:
        ss_available = False
    
    return HealthResponse(
        status="healthy" if ss_available else "degraded",
        uptime_seconds=int(time.time() - detector.stats["start_time"]),
        monitoring_active=monitor_task is not None and not monitor_task.done(),
        ss_available=ss_available
    )

@app.get("/stats", response_model=NetworkStats)
async def get_network_stats():
    """Retorna estatísticas atuais do monitor de rede."""
    return await detector.get_stats()

@app.get("/config", response_model=MonitorConfig)
async def get_monitor_config():
    """Retorna a configuração atual do monitor."""
    return detector.config

@app.put("/config", response_model=MonitorConfig)
async def update_monitor_config(config: MonitorConfig):
    """Atualiza a configuração do monitor."""
    detector.config = config
    detector.dedup.debounce_seconds = config.debounce_seconds
    return config

@app.post("/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Inicia o monitoramento de rede."""
    global monitor_task
    
    if monitor_task is not None and not monitor_task.done():
        raise HTTPException(status_code=400, detail="Monitoramento já está ativo")
    
    # Verifica se ss está disponível
    try:
        process = await asyncio.create_subprocess_exec(
            "ss", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail="Comando 'ss' não disponível")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Comando 'ss' não encontrado")
    
    monitor_task = asyncio.create_task(detector.monitor_loop())
    return {"message": "Monitoramento iniciado", "status": "active"}

@app.post("/stop")
async def stop_monitoring():
    """Para o monitoramento de rede."""
    global monitor_task
    
    if monitor_task is None or monitor_task.done():
        raise HTTPException(status_code=400, detail="Monitoramento não está ativo")
    
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    
    return {"message": "Monitoramento parado", "status": "stopped"}

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket para streaming de alertas em tempo real."""
    await websocket.accept()
    
    # Cria fila para este cliente
    client_queue = asyncio.Queue()
    detector.alert_queues.append(client_queue)
    
    try:
        while True:
            # Aguarda novos alertas
            alert = await client_queue.get()
            await websocket.send_text(alert.model_dump_json())
    except WebSocketDisconnect:
        pass
    finally:
        # Remove a fila quando cliente desconecta
        if client_queue in detector.alert_queues:
            detector.alert_queues.remove(client_queue)

@app.on_event("startup")
async def startup_event():
    """Inicializa o serviço."""
    print("🚀 Network Monitor Service iniciado")
    print("📡 Pronto para detectar ameaças de rede em tempo real")

@app.on_event("shutdown")
async def shutdown_event():
    """Finaliza o serviço."""
    global monitor_task
    if monitor_task and not monitor_task.done():
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
    print("🛑 Network Monitor Service finalizado")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        access_log=True
    )
