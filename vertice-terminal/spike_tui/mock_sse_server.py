"""
Mock SSE Server para Spike TUI - Ethical Governance Workspace

Este servidor simula o backend enviando eventos de governança ética via SSE.
Implementação production-ready para validação de arquitetura.

Endpoints:
    GET /stream/ethical-events - SSE stream de eventos
    GET /spike/health - Health check
    POST /spike/trigger-high-risk - Força evento crítico
    POST /spike/trigger-batch - Força múltiplos eventos
"""

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mock SSE Server - Ethical Governance",
    description="Spike técnico para validação de arquitetura TUI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event templates para simulação
EVENT_TEMPLATES: List[Dict] = [
    {
        "action_type": "port_scan",
        "target": "192.168.1.0/24",
        "risk_level": "medium",
        "ethical_concern": "Scan não autorizado em rede corporativa interna",
        "recommended_action": "require_approval",
        "context": "Descoberta de serviços em rede de produção"
    },
    {
        "action_type": "exploit_attempt",
        "target": "vulnerable-host.internal",
        "risk_level": "high",
        "ethical_concern": "Tentativa de exploração sem autorização explícita do proprietário",
        "recommended_action": "block",
        "context": "Vulnerabilidade crítica detectada (CVE-2024-1234)"
    },
    {
        "action_type": "credential_extraction",
        "target": "database-server-01",
        "risk_level": "critical",
        "ethical_concern": "Extração de credenciais sensíveis sem aprovação de segurança",
        "recommended_action": "block",
        "context": "Tentativa de dump de passwords do sistema"
    },
    {
        "action_type": "network_enumeration",
        "target": "10.0.0.0/8",
        "risk_level": "low",
        "ethical_concern": "Enumeração passiva de rede autorizada",
        "recommended_action": "log_only",
        "context": "Mapeamento de topologia de rede para documentação"
    },
    {
        "action_type": "social_engineering",
        "target": "admin@company.com",
        "risk_level": "high",
        "ethical_concern": "Teste de phishing sem consentimento prévio do alvo",
        "recommended_action": "require_approval",
        "context": "Campanha de conscientização de segurança"
    },
    {
        "action_type": "ddos_test",
        "target": "loadbalancer-prod.company.com",
        "risk_level": "critical",
        "ethical_concern": "Teste de stress em sistema de produção sem janela de manutenção",
        "recommended_action": "block",
        "context": "Validação de capacidade de infraestrutura"
    },
    {
        "action_type": "data_exfiltration",
        "target": "customer-database",
        "risk_level": "critical",
        "ethical_concern": "Tentativa de exfiltração de dados de clientes",
        "recommended_action": "block",
        "context": "Teste de DLP (Data Loss Prevention)"
    },
    {
        "action_type": "privilege_escalation",
        "target": "linux-server-42",
        "risk_level": "high",
        "ethical_concern": "Tentativa de elevação de privilégios em sistema crítico",
        "recommended_action": "require_approval",
        "context": "Validação de controles de acesso"
    }
]

# Contadores globais para IDs únicos
event_counter = 0
active_connections = 0


async def generate_ethical_events() -> AsyncGenerator[str, None]:
    """
    Gera eventos de governança ética para streaming SSE.

    Yields:
        str: Eventos formatados no padrão SSE (data: {...})
    """
    global event_counter, active_connections
    active_connections += 1
    logger.info(f"Nova conexão SSE estabelecida. Total: {active_connections}")

    try:
        while True:
            # Intervalo aleatório entre eventos (2-6 segundos)
            await asyncio.sleep(random.uniform(2.0, 6.0))

            # Seleciona template aleatório
            template = random.choice(EVENT_TEMPLATES).copy()

            # Adiciona metadados únicos
            event_counter += 1
            event_id = f"evt_{event_counter:04d}"

            event_data = {
                "id": event_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": template["action_type"],
                "target": template["target"],
                "risk_level": template["risk_level"],
                "ethical_concern": template["ethical_concern"],
                "recommended_action": template["recommended_action"],
                "context": template["context"],
                "agent_id": f"agent-{random.randint(1, 5):02d}",
                "confidence_score": round(random.uniform(0.7, 0.99), 2)
            }

            # Formato SSE: "data: {json}\n\n"
            sse_message = f"data: {json.dumps(event_data)}\n\n"

            logger.debug(f"Enviando evento: {event_id} ({event_data['risk_level']})")
            yield sse_message

    except asyncio.CancelledError:
        logger.info("Conexão SSE cancelada pelo cliente")
        raise
    finally:
        active_connections -= 1
        logger.info(f"Conexão SSE encerrada. Total: {active_connections}")


@app.get("/stream/ethical-events")
async def stream_ethical_events() -> StreamingResponse:
    """
    Endpoint principal de SSE para eventos de governança ética.

    Returns:
        StreamingResponse: Stream contínuo de eventos SSE
    """
    return StreamingResponse(
        generate_ethical_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx compatibility
            "Connection": "keep-alive"
        }
    )


@app.get("/spike/health")
async def spike_health() -> Dict:
    """
    Health check endpoint para validação do spike.

    Returns:
        Dict: Status do servidor e estatísticas
    """
    return {
        "status": "healthy",
        "spike": True,
        "active_connections": active_connections,
        "events_sent": event_counter,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/spike/trigger-high-risk")
async def trigger_high_risk_event() -> Dict:
    """
    Endpoint de controle para forçar evento de alto risco.
    Útil para testes de validação do spike.

    Returns:
        Dict: Confirmação de evento disparado
    """
    global event_counter
    event_counter += 1

    high_risk_event = {
        "id": f"evt_{event_counter:04d}_forced",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_type": "forced_critical_test",
        "target": "critical-system.test",
        "risk_level": "critical",
        "ethical_concern": "Evento de teste forçado para validação do spike",
        "recommended_action": "require_approval",
        "context": "Teste manual via API de controle",
        "agent_id": "agent-test",
        "confidence_score": 1.0
    }

    logger.info(f"Evento crítico forçado: {high_risk_event['id']}")

    return {
        "status": "triggered",
        "event": high_risk_event
    }


@app.post("/spike/trigger-batch")
async def trigger_batch_events(count: int = 5) -> Dict:
    """
    Dispara múltiplos eventos rapidamente para teste de carga.

    Args:
        count: Número de eventos a disparar (default: 5, max: 20)

    Returns:
        Dict: Confirmação de batch disparado
    """
    global event_counter

    # Limita batch para evitar sobrecarga
    count = min(count, 20)

    batch_ids = []
    for _ in range(count):
        event_counter += 1
        batch_ids.append(f"evt_{event_counter:04d}")

    logger.info(f"Batch de {count} eventos disparados: {batch_ids}")

    return {
        "status": "triggered",
        "count": count,
        "event_ids": batch_ids
    }


@app.get("/")
async def root() -> Dict:
    """
    Endpoint raiz com informações do servidor.

    Returns:
        Dict: Informações básicas e links úteis
    """
    return {
        "name": "Mock SSE Server - Ethical Governance",
        "version": "1.0.0",
        "spike": True,
        "endpoints": {
            "sse_stream": "/stream/ethical-events",
            "health": "/spike/health",
            "trigger_high_risk": "/spike/trigger-high-risk (POST)",
            "trigger_batch": "/spike/trigger-batch?count=5 (POST)"
        },
        "active_connections": active_connections,
        "events_sent": event_counter
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando Mock SSE Server para spike TUI...")
    logger.info("Acesse http://localhost:8001 para info")
    logger.info("Stream SSE: http://localhost:8001/stream/ethical-events")

    uvicorn.run(
        "mock_sse_server:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
