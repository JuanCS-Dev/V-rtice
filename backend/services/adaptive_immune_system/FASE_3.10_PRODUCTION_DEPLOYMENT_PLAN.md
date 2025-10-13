# FASE 3.10 - Production Deployment Plan

**Status**: 📋 **PLANEJAMENTO**
**Data**: 2025-10-13
**Objetivo**: Preparar Adaptive Immune System para produção com Docker, configurações, monitoramento e documentação

---

## 📋 Contexto

### O Que Já Está Completo (FASE 3.1-3.9)

✅ **Backend Completo**:
- Wargaming Engine (2,223 LOC)
- HITL Backend API (1,634 LOC)
- WebSocket Real-time (854 LOC)
- Modelos Pydantic
- Decision Engine
- Mock API funcionando (PID 2026174)

✅ **Frontend Completo**:
- HITL Console React (1,395 LOC)
- WebSocket Hook (288 LOC)
- Integrado no AdminDashboard
- Design system completo

✅ **Validação**:
- 17/17 testes WebSocket passando
- Conformidade 100% com "Regra de Ouro"
- Conformidade 100% com FRONTEND_MANIFESTO
- Documentação completa (3,503+ linhas)

### O Que Falta (FASE 3.10)

❌ **Deployment Infrastructure**:
- Dockerfile para Adaptive Immune System
- docker-compose.yml integration
- Environment variables production-ready
- Health checks e readiness probes

❌ **Configuração**:
- Production settings (vs development)
- Secrets management
- Database migrations
- RabbitMQ queues setup

❌ **Monitoramento**:
- Prometheus metrics
- Logging estruturado
- Health endpoints
- Status dashboard

❌ **Documentação Operacional**:
- Deployment guide
- Troubleshooting guide
- Runbook

---

## 🎯 Objetivos da FASE 3.10

### Objetivo 1: Containerização
Criar Dockerfile e docker-compose para executar Adaptive Immune System em produção

### Objetivo 2: Configuração Production-Ready
Separar configurações de dev/prod, gerenciar secrets, preparar database

### Objetivo 3: Observabilidade
Adicionar métricas, logs estruturados, health checks

### Objetivo 4: Integração com Infraestrutura Existente
Integrar com docker-compose.yml principal do Vértice

### Objetivo 5: Documentação Operacional
Criar guias para deploy, troubleshooting e manutenção

---

## 🏗️ Arquitetura de Deploy

```
┌─────────────────────────────────────────────────────────────┐
│                     VERTICE INFRASTRUCTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Docker Compose (docker-compose.yml)                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Gateway (8000)                                    │ │
│  │  - Routes to all services                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                      │                                       │
│                      │ routes to                             │
│                      ▼                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Adaptive Immune System (8003)           [NEW]        │ │
│  │  ├─ HITL API (FastAPI)                                │ │
│  │  ├─ WebSocket Server                                  │ │
│  │  ├─ Wargaming Engine                                  │ │
│  │  └─ Decision Engine                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│          │          │          │          │                  │
│          ▼          ▼          ▼          ▼                  │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  ┌────────────┐     │
│  │PostgreSQL│  │RabbitMQ │  │ Redis  │  │Prometheus  │     │
│  │ (5432)  │  │ (5672)  │  │ (6379) │  │   (9090)   │     │
│  └─────────┘  └─────────┘  └────────┘  └────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Tasks - Milestone 3.10.1: Dockerização

### Task 1: Criar Dockerfile

**Arquivo**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/hitl/health || exit 1

# Run application
CMD ["uvicorn", "hitl.api.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

**Critérios de Aceitação**:
- [ ] Dockerfile válido
- [ ] Build sem erros
- [ ] Health check funcional
- [ ] Image < 500MB

---

### Task 2: Criar requirements.txt

**Arquivo**: `requirements.txt`

```txt
# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# WebSocket
websockets==12.0
python-socketio==5.10.0

# Database
asyncpg==0.29.0
sqlalchemy==2.0.23
alembic==1.13.0

# Message Queue
aio-pika==9.3.1

# HTTP Client
aiohttp==3.9.1
httpx==0.25.2

# GitHub API
PyGithub==2.1.1

# Utilities
python-dotenv==1.0.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Monitoring
prometheus-client==0.19.0

# Logging
structlog==23.2.0
```

**Critérios de Aceitação**:
- [ ] Todas dependências listadas
- [ ] Versões fixadas
- [ ] Compatíveis entre si
- [ ] pip install sem conflitos

---

### Task 3: Integrar no docker-compose.yml

**Arquivo**: `/home/juan/vertice-dev/docker-compose.yml` (adicionar)

```yaml
  # ============================
  # ADAPTIVE IMMUNE SYSTEM
  # ============================
  adaptive_immune_system:
    build: ./backend/services/adaptive_immune_system
    container_name: vertice-adaptive-immune
    ports:
      - "8003:8003"
    volumes:
      - ./backend/services/adaptive_immune_system:/app
    command: uvicorn hitl.api.main:app --host 0.0.0.0 --port 8003 --reload
    environment:
      # Database
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/adaptive_immune
      # RabbitMQ
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      # GitHub
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_REPO_OWNER=${GITHUB_REPO_OWNER}
      - GITHUB_REPO_NAME=${GITHUB_REPO_NAME}
      # Redis
      - REDIS_URL=redis://redis:6379/0
      # Observability
      - LOG_LEVEL=info
      - PROMETHEUS_ENABLED=true
      # CORS
      - CORS_ORIGINS=http://localhost:5173,http://localhost:3000
    depends_on:
      - postgres
      - rabbitmq
      - redis
    networks:
      - maximus-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/hitl/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Critérios de Aceitação**:
- [ ] Service configurado corretamente
- [ ] Dependências especificadas
- [ ] Environment variables completas
- [ ] Health check definido
- [ ] Integrado com rede existente

---

## 📦 Tasks - Milestone 3.10.2: Configuração

### Task 4: Criar Settings Management

**Arquivo**: `hitl/config.py`

```python
"""Configuration management with Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Adaptive Immune System - HITL API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8003

    # Database
    database_url: str

    # RabbitMQ
    rabbitmq_url: str

    # GitHub
    github_token: str
    github_repo_owner: str
    github_repo_name: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Observability
    log_level: str = "info"
    prometheus_enabled: bool = True

    # Feature Flags
    websocket_enabled: bool = True
    wargaming_enabled: bool = True


settings = Settings()
```

**Critérios de Aceitação**:
- [ ] Pydantic Settings implementado
- [ ] Lê variáveis de .env
- [ ] Validação de tipos
- [ ] Defaults seguros

---

### Task 5: Criar .env.example

**Arquivo**: `.env.example`

```bash
# Adaptive Immune System - Environment Variables
# ===============================================

# Application
APP_NAME="Adaptive Immune System - HITL API"
APP_VERSION="1.0.0"
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8003

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/adaptive_immune

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# GitHub
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO_OWNER=your-org
GITHUB_REPO_NAME=your-repo

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Observability
LOG_LEVEL=info
PROMETHEUS_ENABLED=true

# Feature Flags
WEBSOCKET_ENABLED=true
WARGAMING_ENABLED=true
```

**Critérios de Aceitação**:
- [ ] Todas variáveis documentadas
- [ ] Valores de exemplo seguros
- [ ] Comentários explicativos

---

### Task 6: Criar Database Migrations

**Arquivo**: `alembic.ini` + `alembic/versions/001_initial.py`

```python
"""Initial schema for HITL decisions.

Revision ID: 001
Revises:
Create Date: 2025-10-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


def upgrade():
    """Create initial tables."""

    # APV Reviews table
    op.create_table(
        'apv_reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('apv_code', sa.String(50), nullable=False, unique=True),
        sa.Column('cve_id', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('package_name', sa.String(100), nullable=False),
        sa.Column('patch_strategy', sa.String(50)),
        sa.Column('wargame_verdict', sa.String(50)),
        sa.Column('wargame_confidence', sa.Float),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )

    # Decisions table
    op.create_table(
        'hitl_decisions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('apv_id', UUID(as_uuid=True), nullable=False),
        sa.Column('apv_code', sa.String(50), nullable=False),
        sa.Column('decision', sa.String(20), nullable=False),
        sa.Column('reviewer_name', sa.String(100), nullable=False),
        sa.Column('reviewer_email', sa.String(150)),
        sa.Column('action_taken', sa.String(50)),
        sa.Column('comments', sa.Text),
        sa.Column('confidence_override', sa.Float),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['apv_id'], ['apv_reviews.id']),
    )

    # Indexes
    op.create_index('ix_apv_reviews_status', 'apv_reviews', ['status'])
    op.create_index('ix_apv_reviews_severity', 'apv_reviews', ['severity'])
    op.create_index('ix_hitl_decisions_apv_id', 'hitl_decisions', ['apv_id'])


def downgrade():
    """Drop all tables."""
    op.drop_table('hitl_decisions')
    op.drop_table('apv_reviews')
```

**Critérios de Aceitação**:
- [ ] Alembic configurado
- [ ] Migration inicial criada
- [ ] Indexes otimizados
- [ ] Foreign keys corretas

---

## 📦 Tasks - Milestone 3.10.3: Observabilidade

### Task 7: Adicionar Prometheus Metrics

**Arquivo**: `hitl/monitoring/metrics.py`

```python
"""Prometheus metrics for HITL API."""

from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time


# Counters
http_requests_total = Counter(
    'hitl_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

decisions_total = Counter(
    'hitl_decisions_total',
    'Total HITL decisions made',
    ['decision_type', 'severity']
)

websocket_connections_total = Counter(
    'hitl_websocket_connections_total',
    'Total WebSocket connections'
)

websocket_messages_sent = Counter(
    'hitl_websocket_messages_sent',
    'Total WebSocket messages sent',
    ['channel', 'message_type']
)

# Gauges
active_apv_reviews = Gauge(
    'hitl_active_apv_reviews',
    'Number of APVs pending review'
)

websocket_connections_active = Gauge(
    'hitl_websocket_connections_active',
    'Number of active WebSocket connections'
)

# Histograms
http_request_duration = Histogram(
    'hitl_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

decision_processing_duration = Histogram(
    'hitl_decision_processing_duration_seconds',
    'Time to process HITL decision'
)


def track_request_metrics(endpoint: str):
    """Decorator to track request metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method='GET',
                    endpoint=endpoint,
                    status=status
                ).inc()
                http_request_duration.labels(
                    method='GET',
                    endpoint=endpoint
                ).observe(duration)
        return wrapper
    return decorator
```

**Critérios de Aceitação**:
- [ ] Métricas definidas
- [ ] Decorators implementados
- [ ] Labels apropriados
- [ ] Endpoint /metrics exposto

---

### Task 8: Adicionar Structured Logging

**Arquivo**: `hitl/monitoring/logging.py`

```python
"""Structured logging configuration."""

import structlog
import logging
import sys


def configure_logging(log_level: str = "info"):
    """Configure structured logging."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level.upper(),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


logger = structlog.get_logger()
```

**Critérios de Aceitação**:
- [ ] Logs estruturados (JSON em prod)
- [ ] Contexto enriquecido
- [ ] Log level configurável
- [ ] Correlation IDs

---

### Task 9: Health Checks Completos

**Arquivo**: `hitl/api/health.py`

```python
"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict
import asyncio


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    checks: Dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "checks": {
            "api": "ok"
        }
    }


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check (checks dependencies)."""
    checks = {}

    # Check database
    try:
        # TODO: Add actual DB check
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    # Check RabbitMQ
    try:
        # TODO: Add actual RabbitMQ check
        checks["rabbitmq"] = "ok"
    except Exception:
        checks["rabbitmq"] = "error"

    # Check Redis
    try:
        # TODO: Add actual Redis check
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    # Determine overall status
    all_ok = all(v == "ok" for v in checks.values())
    status_code = "ready" if all_ok else "not_ready"

    return {
        "status": status_code,
        "version": "1.0.0",
        "checks": checks
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check (simple ping)."""
    return {"status": "alive"}
```

**Critérios de Aceitação**:
- [ ] /health endpoint
- [ ] /health/ready endpoint (dependency checks)
- [ ] /health/live endpoint
- [ ] Responde em < 1s

---

## 📦 Tasks - Milestone 3.10.4: Documentação Operacional

### Task 10: Deployment Guide

**Arquivo**: `docs/DEPLOYMENT_GUIDE.md`

Conteúdo:
- Pre-requisites (Docker, docker-compose, credentials)
- Environment variables setup
- Database initialization
- Running with docker-compose
- Verifying deployment
- Rolling back
- Scaling considerations

**Critérios de Aceitação**:
- [ ] Passo-a-passo completo
- [ ] Screenshots/exemplos
- [ ] Troubleshooting comum
- [ ] Rollback procedure

---

### Task 11: Operational Runbook

**Arquivo**: `docs/OPERATIONAL_RUNBOOK.md`

Conteúdo:
- Service overview
- Architecture diagram
- Monitoring dashboards
- Common operations (restart, scale, logs)
- Incident response procedures
- Backup and recovery
- Disaster recovery

**Critérios de Aceitação**:
- [ ] Procedimentos claros
- [ ] Responsáveis definidos
- [ ] Escalation paths
- [ ] Contact information

---

## 📊 Cronograma

```
┌────────────────────────────────────────────────────────────┐
│  FASE 3.10 - PRODUCTION DEPLOYMENT                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Milestone 3.10.1: Dockerização          [2-3h]          │
│    ├─ Task 1: Dockerfile                                  │
│    ├─ Task 2: requirements.txt                            │
│    └─ Task 3: docker-compose integration                  │
│                                                            │
│  Milestone 3.10.2: Configuração          [1-2h]          │
│    ├─ Task 4: Settings management                         │
│    ├─ Task 5: .env.example                                │
│    └─ Task 6: Database migrations                         │
│                                                            │
│  Milestone 3.10.3: Observabilidade       [2-3h]          │
│    ├─ Task 7: Prometheus metrics                          │
│    ├─ Task 8: Structured logging                          │
│    └─ Task 9: Health checks                               │
│                                                            │
│  Milestone 3.10.4: Documentação          [1-2h]          │
│    ├─ Task 10: Deployment guide                           │
│    └─ Task 11: Operational runbook                        │
│                                                            │
│  TOTAL ESTIMADO:                         [6-10h]         │
└────────────────────────────────────────────────────────────┘
```

---

## ✅ Critérios de Sucesso - FASE 3.10

### Funcional
- [ ] Docker build bem-sucedido
- [ ] docker-compose up funciona
- [ ] API responde em http://localhost:8003
- [ ] Health checks retornam 200
- [ ] WebSocket conecta
- [ ] Database migrations executam

### Observabilidade
- [ ] Métricas expostas em /metrics
- [ ] Logs estruturados em JSON
- [ ] Health checks em 3 endpoints
- [ ] Todos os componentes monitorados

### Configuração
- [ ] Settings com Pydantic
- [ ] .env.example completo
- [ ] Secrets não commitados
- [ ] Configuração dev/prod separada

### Documentação
- [ ] Deployment guide completo
- [ ] Runbook operacional
- [ ] Troubleshooting guide
- [ ] Architecture diagram atualizado

---

## 🚀 Próximos Passos Após FASE 3.10

### FASE 3.11: Production Testing
- Load testing (100+ concurrent users)
- Chaos engineering (kill services, network issues)
- Security audit (OWASP Top 10)
- Performance profiling

### FASE 3.12: CI/CD Pipeline
- GitHub Actions workflows
- Automated testing
- Docker image building
- Automated deployment

### FASE 3.13: Monitoring & Alerting
- Grafana dashboards
- Alertmanager rules
- PagerDuty integration
- SLO/SLA monitoring

---

**Data de Criação**: 2025-10-13
**Autor**: Claude Code (Adaptive Immune System Team)
**Status**: 📋 READY TO IMPLEMENT
