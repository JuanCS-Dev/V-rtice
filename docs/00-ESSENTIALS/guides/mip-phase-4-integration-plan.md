# MIP FASE 4 - INTEGRATION & DEPLOYMENT
## Motor de Integridade Processual - Integração Completa

**Autor**: GitHub Copilot CLI  
**Data**: 2025-10-14  
**Versão**: 1.0  
**Lei Governante**: Constituição Vértice v2.6  
**Padrão**: PAGANI ABSOLUTO - 100% ou nada

---

## 📊 STATUS ATUAL (Baseline Completo)

### ✅ FASE 1-3 CONCLUÍDAS (100%)

**MÉTRICAS ATUAIS:**
- ✅ **190 testes** (100% passando)
- ✅ **7/7 módulos éticos** com ≥95% coverage
- ✅ **1 módulo** com 100% coverage perfeito
- ✅ **~7,600 LOC** production code
- ✅ **~3,800 LOC** comprehensive tests
- ✅ **Total:** 9,276 LOC (production-ready)

**COVERAGE POR MÓDULO:**
1. knowledge_models.py: 100.0% ✅
2. models.py: 99.4% ✅
3. principialism.py: 98.2% ✅
4. resolver.py: 97.6% ✅
5. utilitarian.py: 96.7% ✅
6. kantian.py: 95.9% ✅
7. virtue_ethics.py: 95.4% ✅

**COMPONENTES PRONTOS:**
- ✅ 4 Frameworks Éticos (Kantian, Utilitarian, Virtue, Principialism)
- ✅ Conflict Resolver (multi-framework orchestration)
- ✅ Core Engine (ProcessIntegrityEngine)
- ✅ Knowledge Base (Neo4j integration ready)
- ✅ Data Models (comprehensive)
- ✅ FastAPI skeleton (api.py - 577 LOC)
- ✅ Config management

---

## 🎯 FASE 4: INTEGRATION & DEPLOYMENT

**Objetivo**: Integrar MIP ao MAXIMUS ecosystem, deploy em Docker, e habilitar operação production.

**Duração Estimada**: 2-3 dias  
**LOC Estimado**: ~1,500 LOC  
**Prioridade**: CRÍTICA

---

## 📋 TASK-010: FastAPI Service Completion

**Duração**: 6-8 horas  
**LOC Estimado**: 300  
**Status**: 🟡 50% (skeleton existe, falta completar)

### Análise do Estado Atual

**Arquivo**: `backend/consciousness/mip/api.py` (577 LOC)

**O que está implementado:**
- ✅ Pydantic request/response models
- ✅ Estrutura básica de endpoints
- ✅ CORS middleware
- ✅ Logging setup
- ✅ Settings management
- ✅ Health check endpoint

**O que falta:**
- ❌ Lifespan management (startup/shutdown)
- ❌ Neo4j connection pooling
- ❌ KnowledgeBase initialization
- ❌ Error handling middleware
- ❌ Request validation
- ❌ Response caching
- ❌ Rate limiting
- ❌ Authentication/Authorization (se necessário)

### Entregáveis

#### 1. Lifespan Management
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação."""
    # Startup
    logger.info("🚀 MIP Service Starting...")
    
    # Initialize Neo4j
    app.state.kb_repo = KnowledgeBaseRepository(settings.NEO4J_URI)
    await app.state.kb_repo.connect()
    
    # Initialize Core Engine
    app.state.engine = ProcessIntegrityEngine()
    
    # Initialize services
    app.state.audit_service = AuditTrailService(app.state.kb_repo)
    app.state.query_service = PrincipleQueryService(app.state.kb_repo)
    
    logger.info("✅ MIP Service Ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 MIP Service Shutting Down...")
    await app.state.kb_repo.close()
    logger.info("✅ Shutdown Complete")
```

#### 2. Complete Endpoints

**Endpoints a completar:**

1. **POST `/evaluate`** - Avaliar ActionPlan
   - Request validation
   - Engine evaluation
   - Persistence no Neo4j
   - Response formatting
   - Error handling

2. **GET `/principles`** - Listar princípios
   - Query from KnowledgeBase
   - Filter by level/domain
   - Pagination
   - Cache response

3. **GET `/principles/{id}`** - Detalhe de princípio
   - Fetch principle
   - Include hierarchy
   - Include related decisions

4. **GET `/decisions`** - Histórico de decisões
   - Query audit trail
   - Filter by status/date
   - Pagination
   - Sort options

5. **GET `/decisions/{id}`** - Detalhe de decisão
   - Fetch decision
   - Include framework scores
   - Include conflicts
   - Include resolution

6. **GET `/audit-trail`** - Full audit trail
   - Complete history
   - Export options (JSON/CSV)
   - Date range filtering

7. **GET `/health`** - Health check (já existe)
   - Status check
   - Neo4j connectivity
   - Engine readiness

8. **GET `/metrics`** - Prometheus metrics
   - Evaluation counts
   - Decision status distribution
   - Framework usage stats
   - Response times

#### 3. Error Handling Middleware

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": time.time(),
        }
    )
```

#### 4. Request Validation

- Pydantic models completos para todos endpoints
- Custom validators
- Error messages claros

### Critérios de Aceitação

- [ ] Todos 8 endpoints funcionais
- [ ] Lifespan startup/shutdown correto
- [ ] Neo4j connection pool funciona
- [ ] Todos requests validados
- [ ] Error handling robusto
- [ ] Health check retorna 200 OK
- [ ] OpenAPI docs em `/docs` completas
- [ ] Response times < 100ms (exceto evaluate)
- [ ] Logs estruturados

### Comando de Validação

```bash
# 1. Start service
cd /home/juan/vertice-dev
docker-compose -f docker-compose.mip.yml up -d

# 2. Health check
curl http://localhost:8100/health
# Expected: {"status": "healthy", "neo4j": "connected"}

# 3. List principles
curl http://localhost:8100/principles
# Expected: [{"id": "...", "name": "Non-Maleficence", ...}]

# 4. Evaluate plan
curl -X POST http://localhost:8100/evaluate \
  -H "Content-Type: application/json" \
  -d @backend/consciousness/mip/examples/test_plan.json
# Expected: {"status": "approved", "overall_score": 0.85, ...}

# 5. Get decision
DECISION_ID=$(curl http://localhost:8100/decisions | jq -r '.[0].id')
curl http://localhost:8100/decisions/$DECISION_ID
# Expected: Full decision object

# 6. OpenAPI docs
curl http://localhost:8100/docs
# Expected: HTML documentation page
```

---

## 📋 TASK-011: Docker Compose Integration

**Duração**: 2-3 horas  
**LOC Estimado**: 150 (YAML + Dockerfile)  
**Status**: 🟡 30% (arquivo existe, falta completar)

### Análise do Estado Atual

**Arquivo**: `docker-compose.mip.yml` (já existe no root)

**O que está implementado:**
- ✅ Estrutura básica
- ✅ Neo4j service configurado

**O que falta:**
- ❌ MIP service definition completa
- ❌ Dockerfile otimizado
- ❌ Environment variables
- ❌ Volume mounts
- ❌ Health checks
- ❌ Network configuration
- ❌ Resource limits

### Entregáveis

#### 1. Dockerfile Otimizado

**Arquivo**: `backend/consciousness/mip/Dockerfile`

```dockerfile
FROM python:3.11-slim

# Metadata
LABEL maintainer="Juan Carlos de Souza"
LABEL project="MAXIMUS - MIP Service"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mip && chown -R mip:mip /app
USER mip

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8100/health || exit 1

# Expose port
EXPOSE 8100

# Run application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8100", "--log-level", "info"]
```

#### 2. Docker Compose Complete

**Arquivo**: `docker-compose.mip.yml` (atualizar)

```yaml
version: '3.8'

services:
  # Neo4j Database
  neo4j:
    image: neo4j:5.13.0
    container_name: mip-neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/vertice-mip-2024
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=1G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - ./backend/consciousness/mip/scripts/init_db.cypher:/init.cypher
    networks:
      - mip-network
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "vertice-mip-2024", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped

  # MIP Service
  mip:
    build:
      context: ./backend/consciousness/mip
      dockerfile: Dockerfile
    container_name: mip-service
    ports:
      - "8100:8100"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=vertice-mip-2024
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
    volumes:
      - ./backend/consciousness/mip:/app:ro
      - mip_logs:/app/logs
    networks:
      - mip-network
    depends_on:
      neo4j:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

networks:
  mip-network:
    driver: bridge

volumes:
  neo4j_data:
  neo4j_logs:
  mip_logs:
```

#### 3. Environment Variables

**Arquivo**: `.env.mip` (criar)

```bash
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=vertice-mip-2024

# MIP Configuration
MIP_PORT=8100
MIP_HOST=0.0.0.0
LOG_LEVEL=INFO
ENVIRONMENT=production

# Frameworks Configuration
KANTIAN_WEIGHT=1.0
UTILITARIAN_WEIGHT=1.0
VIRTUE_WEIGHT=1.0
PRINCIPIALISM_WEIGHT=1.0

# Resolution Configuration
CONFLICT_THRESHOLD=0.3
ESCALATION_THRESHOLD=0.5
HITL_REQUIRED=true

# Performance
CACHE_TTL=3600
MAX_WORKERS=4
REQUEST_TIMEOUT=30
```

### Critérios de Aceitação

- [ ] `docker-compose -f docker-compose.mip.yml up -d` funciona
- [ ] Ambos services (neo4j + mip) healthy
- [ ] Services comunicam via network
- [ ] Data persiste em volumes
- [ ] Health checks passam
- [ ] Resource limits aplicados
- [ ] Logs acessíveis
- [ ] Rebuild rápido (< 2min)

### Comando de Validação

```bash
# 1. Build and start
docker-compose -f docker-compose.mip.yml up -d --build

# 2. Check status
docker-compose -f docker-compose.mip.yml ps
# Expected: All services "healthy"

# 3. Check logs
docker-compose -f docker-compose.mip.yml logs -f mip

# 4. Test connectivity
docker exec mip-service curl http://localhost:8100/health
# Expected: {"status": "healthy"}

# 5. Test Neo4j connectivity
docker exec mip-neo4j cypher-shell -u neo4j -p vertice-mip-2024 "RETURN 1"
# Expected: 1

# 6. Stop
docker-compose -f docker-compose.mip.yml down
```

---

## 📋 TASK-012: MAXIMUS Integration

**Duração**: 4-5 horas  
**LOC Estimado**: 400  
**Status**: ❌ 0% (não iniciado)

### Objetivo

Criar client library em `maximus_core_service` para consumir MIP API.

### Entregáveis

#### 1. MIP Client Library

**Arquivo**: `backend/services/maximus_core_service/mip_client.py`

```python
"""
MIP Client Library

Cliente HTTP para comunicar com Motor de Integridade Processual.
Usado por MAXIMUS Core para validação ética de ações.

Autor: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.6
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


@dataclass
class MIPConfig:
    """Configuração do cliente MIP."""
    base_url: str = "http://mip:8100"
    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff: float = 1.0


class MIPClientError(Exception):
    """Erro base do cliente MIP."""
    pass


class MIPConnectionError(MIPClientError):
    """Erro de conexão com MIP."""
    pass


class MIPValidationError(MIPClientError):
    """Erro de validação de request."""
    pass


class MIPEvaluationError(MIPClientError):
    """Erro durante avaliação ética."""
    pass


class MIPClient:
    """
    Cliente HTTP para MIP Service.
    
    Fornece interface simplificada para validação ética de ActionPlans.
    Implementa retry logic, circuit breaker, e graceful degradation.
    
    Examples:
        >>> mip = MIPClient("http://mip:8100")
        >>> verdict = await mip.evaluate(action_plan)
        >>> if verdict.status == "approved":
        >>>     await execute_action(action_plan)
    """
    
    def __init__(self, config: Optional[MIPConfig] = None):
        """
        Inicializar cliente MIP.
        
        Args:
            config: Configuração do cliente (usa defaults se None)
        """
        self.config = config or MIPConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )
        logger.info(f"MIP Client initialized: {self.config.base_url}")
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def close(self):
        """Fechar conexões."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.ConnectError),
    )
    async def health_check(self) -> bool:
        """
        Verificar saúde do serviço MIP.
        
        Returns:
            True se serviço está saudável, False caso contrário.
        
        Raises:
            MIPConnectionError: Se não conseguir conectar após retries.
        """
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except httpx.ConnectError as e:
            logger.error(f"MIP health check failed: {e}")
            raise MIPConnectionError(f"Cannot connect to MIP: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.ConnectError),
    )
    async def evaluate(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avaliar ActionPlan eticamente.
        
        Args:
            action_plan: ActionPlan a ser avaliado.
        
        Returns:
            EthicalVerdict com resultado da avaliação.
        
        Raises:
            MIPValidationError: Se action_plan é inválido.
            MIPEvaluationError: Se avaliação falha.
            MIPConnectionError: Se não conseguir conectar.
        """
        try:
            response = await self.client.post(
                "/evaluate",
                json={"plan": action_plan},
            )
            
            if response.status_code == 422:
                raise MIPValidationError(f"Invalid action plan: {response.json()}")
            
            if response.status_code != 200:
                raise MIPEvaluationError(f"Evaluation failed: {response.text}")
            
            return response.json()
            
        except httpx.ConnectError as e:
            logger.error(f"MIP evaluation failed: {e}")
            raise MIPConnectionError(f"Cannot connect to MIP: {e}")
        except httpx.TimeoutException as e:
            logger.error(f"MIP evaluation timeout: {e}")
            raise MIPEvaluationError(f"Evaluation timeout: {e}")
    
    async def get_principles(
        self,
        level: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Listar princípios éticos.
        
        Args:
            level: Filtrar por nível (constitutional/statutory/policy).
            domain: Filtrar por domínio.
        
        Returns:
            Lista de princípios.
        
        Raises:
            MIPConnectionError: Se não conseguir conectar.
        """
        params = {}
        if level:
            params["level"] = level
        if domain:
            params["domain"] = domain
        
        response = await self.client.get("/principles", params=params)
        
        if response.status_code != 200:
            raise MIPEvaluationError(f"Failed to get principles: {response.text}")
        
        return response.json()
    
    async def get_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Obter detalhes de uma decisão.
        
        Args:
            decision_id: ID da decisão.
        
        Returns:
            Decisão completa.
        
        Raises:
            MIPConnectionError: Se não conseguir conectar.
        """
        response = await self.client.get(f"/decisions/{decision_id}")
        
        if response.status_code == 404:
            raise MIPEvaluationError(f"Decision not found: {decision_id}")
        
        if response.status_code != 200:
            raise MIPEvaluationError(f"Failed to get decision: {response.text}")
        
        return response.json()
    
    async def get_audit_trail(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Obter audit trail de decisões.
        
        Args:
            limit: Número máximo de decisões.
            offset: Offset para paginação.
        
        Returns:
            Lista de decisões.
        
        Raises:
            MIPConnectionError: Se não conseguir conectar.
        """
        params = {"limit": limit, "offset": offset}
        response = await self.client.get("/audit-trail", params=params)
        
        if response.status_code != 200:
            raise MIPEvaluationError(f"Failed to get audit trail: {response.text}")
        
        return response.json()
```

#### 2. Integration Tests

**Arquivo**: `backend/services/maximus_core_service/tests/test_mip_client.py`

```python
"""
MIP Client Integration Tests

Testes E2E para cliente MIP.

Autor: Juan Carlos de Souza
"""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from ..mip_client import MIPClient, MIPConfig, MIPConnectionError, MIPValidationError


@pytest.fixture
def mip_client():
    """Fixture para cliente MIP."""
    config = MIPConfig(base_url="http://localhost:8100")
    return MIPClient(config)


@pytest.mark.asyncio
async def test_health_check_success(mip_client):
    """Test health check bem-sucedido."""
    with patch.object(mip_client.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = await mip_client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_failure(mip_client):
    """Test health check com falha de conexão."""
    with patch.object(mip_client.client, 'get') as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        
        with pytest.raises(MIPConnectionError):
            await mip_client.health_check()


@pytest.mark.asyncio
async def test_evaluate_success(mip_client):
    """Test avaliação bem-sucedida."""
    action_plan = {
        "name": "Test Plan",
        "category": "defensive",
        "steps": [],
    }
    
    with patch.object(mip_client.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "approved",
            "overall_score": 0.85,
        }
        mock_post.return_value = mock_response
        
        verdict = await mip_client.evaluate(action_plan)
        assert verdict["status"] == "approved"
        assert verdict["overall_score"] == 0.85


@pytest.mark.asyncio
async def test_evaluate_invalid_plan(mip_client):
    """Test avaliação com plano inválido."""
    invalid_plan = {}
    
    with patch.object(mip_client.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "Validation error"}
        mock_post.return_value = mock_response
        
        with pytest.raises(MIPValidationError):
            await mip_client.evaluate(invalid_plan)


# ... mais testes
```

#### 3. Integration em MAXIMUS Core

**Arquivo**: `backend/services/maximus_core_service/decision_engine.py`

Adicionar integração:

```python
from .mip_client import MIPClient, MIPConnectionError

class MAXIMUSDecisionEngine:
    def __init__(self):
        self.mip_client = MIPClient()
    
    async def evaluate_action(self, action_plan: Dict) -> bool:
        """
        Avaliar ação proposta eticamente.
        
        Args:
            action_plan: Plano de ação a executar.
        
        Returns:
            True se aprovado, False se rejeitado.
        """
        try:
            # Verificar se MIP está disponível
            if not await self.mip_client.health_check():
                logger.warning("MIP unavailable, using fallback logic")
                return self._fallback_evaluation(action_plan)
            
            # Avaliar com MIP
            verdict = await self.mip_client.evaluate(action_plan)
            
            # Log resultado
            logger.info(f"MIP Verdict: {verdict['status']} (score: {verdict['overall_score']})")
            
            # Decisão baseada em status e score
            if verdict["status"] == "approved":
                return True
            elif verdict["status"] == "conditionally_approved":
                # Verificar condições
                return await self._check_conditions(verdict["conditions"])
            else:
                logger.warning(f"Action rejected by MIP: {verdict['rejection_reason']}")
                return False
                
        except MIPConnectionError:
            logger.error("MIP connection error, using fallback")
            return self._fallback_evaluation(action_plan)
    
    def _fallback_evaluation(self, action_plan: Dict) -> bool:
        """Lógica de fallback se MIP indisponível."""
        # Lógica simples e conservadora
        if action_plan.get("category") == "offensive":
            return False  # Rejeitar ações ofensivas por segurança
        return True
```

### Critérios de Aceitação

- [ ] MIPClient implementado completo
- [ ] Retry logic funcionando (3 tentativas)
- [ ] Graceful degradation se MIP offline
- [ ] Integration tests passando (≥10 tests)
- [ ] MAXIMUS pode chamar MIP via client
- [ ] Fallback logic funciona
- [ ] Logs estruturados
- [ ] Type hints 100%
- [ ] Docstrings completas

### Comando de Validação

```bash
# 1. Run MIP service
docker-compose -f docker-compose.mip.yml up -d

# 2. Run integration tests
pytest backend/services/maximus_core_service/tests/test_mip_client.py -v
# Expected: 100% pass

# 3. Test MAXIMUS integration
# (via MAXIMUS test suite)
pytest backend/services/maximus_core_service/tests/test_decision_engine.py -v -k "test_mip_integration"
# Expected: Pass

# 4. Test fallback
# Stop MIP, verify MAXIMUS ainda funciona
docker-compose -f docker-compose.mip.yml stop mip
# MAXIMUS should use fallback logic
```

---

## 📋 TASK-013: Integration Tests E2E

**Duração**: 3-4 horas  
**LOC Estimado**: 500  
**Status**: ❌ 0% (não iniciado)

### Objetivo

Testes end-to-end completos do fluxo MAXIMUS → MIP → Neo4j.

### Entregáveis

#### 1. E2E Test Suite

**Arquivo**: `tests/integration/test_mip_e2e.py`

```python
"""
MIP End-to-End Integration Tests

Testes completos do fluxo MAXIMUS → MIP → Neo4j.

Autor: Juan Carlos de Souza
"""

import pytest
import asyncio
from uuid import uuid4
from typing import AsyncGenerator

from backend.services.maximus_core_service.mip_client import MIPClient
from backend.consciousness.mip.infrastructure.knowledge_base import KnowledgeBaseRepository


@pytest.fixture(scope="module")
async def neo4j_repo() -> AsyncGenerator[KnowledgeBaseRepository, None]:
    """Fixture para repository Neo4j."""
    repo = KnowledgeBaseRepository("bolt://localhost:7687")
    await repo.connect()
    yield repo
    await repo.close()


@pytest.fixture(scope="module")
async def mip_client() -> AsyncGenerator[MIPClient, None]:
    """Fixture para cliente MIP."""
    client = MIPClient()
    
    # Wait for service to be ready
    max_retries = 10
    for i in range(max_retries):
        try:
            if await client.health_check():
                break
        except:
            if i == max_retries - 1:
                pytest.fail("MIP service not available")
            await asyncio.sleep(2)
    
    yield client
    await client.close()


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_complete_evaluation_flow(mip_client, neo4j_repo):
    """
    Test fluxo completo de avaliação.
    
    1. MAXIMUS cria ActionPlan
    2. MIP avalia via API
    3. Decisão persistida no Neo4j
    4. Query retorna decisão
    """
    # 1. Create action plan
    action_plan = {
        "id": str(uuid4()),
        "name": "E2E Test Plan",
        "description": "Testing complete flow",
        "category": "defensive",
        "steps": [{
            "sequence_number": 1,
            "description": "Block malicious IP",
            "action_type": "defensive",
            "respects_autonomy": True,
            "treats_as_means_only": False,
        }],
        "stakeholders": [{
            "id": "users",
            "type": "human_group",
            "name": "System Users",
            "interests": ["security", "privacy"],
            "benefits": ["protection"],
            "harms": [],
        }],
    }
    
    # 2. Evaluate via MIP API
    verdict = await mip_client.evaluate(action_plan)
    
    # 3. Verify verdict
    assert verdict["status"] in ["approved", "conditionally_approved"]
    assert verdict["overall_score"] > 0.0
    assert "decision_id" in verdict
    
    decision_id = verdict["decision_id"]
    
    # 4. Wait for persistence (async)
    await asyncio.sleep(1)
    
    # 5. Query Neo4j directly
    decision = await neo4j_repo.get_decision(decision_id)
    
    # 6. Verify persisted data
    assert decision is not None
    assert decision.action_plan_name == action_plan["name"]
    assert decision.status == verdict["status"]
    assert decision.overall_score == verdict["overall_score"]
    
    # 7. Query via MIP API
    api_decision = await mip_client.get_decision(decision_id)
    
    # 8. Verify consistency
    assert api_decision["id"] == decision_id
    assert api_decision["status"] == verdict["status"]


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_principle_hierarchy_query(mip_client, neo4j_repo):
    """Test query de hierarquia de princípios."""
    # 1. Get principles from API
    principles = await mip_client.get_principles()
    
    # 2. Verify structure
    assert len(principles) > 0
    
    # 3. Check hierarchy levels
    levels = {p["level"] for p in principles}
    assert "constitutional" in levels
    
    # 4. Query directly from Neo4j
    neo4j_principles = await neo4j_repo.get_all_principles()
    
    # 5. Verify consistency
    assert len(principles) == len(neo4j_principles)


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_audit_trail_completeness(mip_client):
    """Test completude do audit trail."""
    # 1. Evaluate multiple plans
    plans = [
        create_test_plan("Plan 1", "defensive"),
        create_test_plan("Plan 2", "offensive"),
        create_test_plan("Plan 3", "reconnaissance"),
    ]
    
    decision_ids = []
    for plan in plans:
        verdict = await mip_client.evaluate(plan)
        decision_ids.append(verdict["decision_id"])
    
    # 2. Wait for persistence
    await asyncio.sleep(2)
    
    # 3. Get audit trail
    audit_trail = await mip_client.get_audit_trail(limit=10)
    
    # 4. Verify all decisions present
    trail_ids = {d["id"] for d in audit_trail}
    for decision_id in decision_ids:
        assert decision_id in trail_ids


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_concurrent_evaluations(mip_client):
    """Test avaliações concorrentes."""
    # Create 10 plans
    plans = [create_test_plan(f"Concurrent Plan {i}", "defensive") for i in range(10)]
    
    # Evaluate concurrently
    tasks = [mip_client.evaluate(plan) for plan in plans]
    verdicts = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    assert len(verdicts) == 10
    assert all(v["status"] in ["approved", "conditionally_approved"] for v in verdicts)
    
    # Verify unique decision IDs
    decision_ids = [v["decision_id"] for v in verdicts]
    assert len(set(decision_ids)) == 10


def create_test_plan(name: str, category: str) -> dict:
    """Helper para criar plano de teste."""
    return {
        "id": str(uuid4()),
        "name": name,
        "description": f"Testing {category}",
        "category": category,
        "steps": [{
            "sequence_number": 1,
            "description": "Test action",
            "action_type": category,
            "respects_autonomy": True,
            "treats_as_means_only": False,
        }],
        "stakeholders": [],
    }
```

#### 2. Performance Tests

**Arquivo**: `tests/integration/test_mip_performance.py`

```python
"""MIP Performance Tests."""

import pytest
import asyncio
import time
from statistics import mean, stdev

from backend.services.maximus_core_service.mip_client import MIPClient


@pytest.mark.asyncio
@pytest.mark.performance
async def test_evaluation_latency():
    """Test latência de avaliação."""
    client = MIPClient()
    
    # Warm-up
    for _ in range(5):
        await client.evaluate(create_simple_plan())
    
    # Measure
    latencies = []
    for _ in range(100):
        start = time.time()
        await client.evaluate(create_simple_plan())
        latency = (time.time() - start) * 1000  # ms
        latencies.append(latency)
    
    # Analyze
    avg_latency = mean(latencies)
    std_latency = stdev(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    
    print(f"\nLatency Stats:")
    print(f"  Average: {avg_latency:.2f}ms")
    print(f"  StdDev:  {std_latency:.2f}ms")
    print(f"  P95:     {p95_latency:.2f}ms")
    
    # Assertions
    assert avg_latency < 100, f"Average latency too high: {avg_latency}ms"
    assert p95_latency < 200, f"P95 latency too high: {p95_latency}ms"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_throughput():
    """Test throughput (requests/second)."""
    client = MIPClient()
    
    num_requests = 100
    start = time.time()
    
    tasks = [client.evaluate(create_simple_plan()) for _ in range(num_requests)]
    await asyncio.gather(*tasks)
    
    duration = time.time() - start
    throughput = num_requests / duration
    
    print(f"\nThroughput: {throughput:.2f} req/s")
    
    assert throughput > 10, f"Throughput too low: {throughput} req/s"


def create_simple_plan():
    """Helper para criar plano simples."""
    return {
        "name": "Simple Plan",
        "category": "defensive",
        "steps": [],
        "stakeholders": [],
    }
```

### Critérios de Aceitação

- [ ] E2E tests implementados (≥5 scenarios)
- [ ] Performance tests implementados (≥2 tests)
- [ ] Todos testes passando
- [ ] Coverage do fluxo completo
- [ ] Latência média < 100ms
- [ ] P95 latency < 200ms
- [ ] Throughput > 10 req/s
- [ ] Concurrent requests funcionam
- [ ] Neo4j persistence verificada

### Comando de Validação

```bash
# 1. Start all services
docker-compose -f docker-compose.mip.yml up -d

# 2. Run E2E tests
pytest tests/integration/test_mip_e2e.py -v -m e2e
# Expected: 100% pass

# 3. Run performance tests
pytest tests/integration/test_mip_performance.py -v -m performance
# Expected: Pass with metrics

# 4. Check Neo4j data
docker exec mip-neo4j cypher-shell -u neo4j -p vertice-mip-2024 \
  "MATCH (d:Decision) RETURN count(d)"
# Expected: ≥10 decisions
```

---

## 📋 TASK-014: Documentation & Deployment Guide

**Duração**: 2-3 horas  
**LOC Estimado**: N/A (documentation)  
**Status**: ❌ 0% (não iniciado)

### Objetivo

Documentação completa para deploy e uso do MIP em produção.

### Entregáveis

#### 1. Deployment Guide

**Arquivo**: `docs/guides/mip-deployment-guide.md`

Conteúdo:
- Prerequisites
- Installation steps
- Configuration
- Docker setup
- Health checks
- Monitoring
- Troubleshooting
- Rollback procedures

#### 2. API Documentation

**Arquivo**: `docs/architecture/mip/api-reference.md`

Conteúdo:
- All endpoints
- Request/response schemas
- Error codes
- Rate limiting
- Authentication
- Examples

#### 3. Integration Guide

**Arquivo**: `docs/guides/mip-integration-guide.md`

Conteúdo:
- How to integrate with MAXIMUS
- Client library usage
- Error handling
- Best practices
- Code examples

#### 4. Operations Manual

**Arquivo**: `docs/guides/mip-operations-manual.md`

Conteúdo:
- Day-to-day operations
- Monitoring dashboards
- Alert handling
- Backup/restore
- Scaling procedures
- Performance tuning

### Critérios de Aceitação

- [ ] Todas documentações criadas
- [ ] Examples testados e funcionando
- [ ] Diagramas claros
- [ ] Troubleshooting abrangente
- [ ] Reviewed e aprovado

---

## 📊 SUMMARY & TIMELINE

### Timeline Otimista (2 dias)

**Dia 1 (8 horas):**
- TASK-010: FastAPI Completion (6h)
- TASK-011: Docker Complete (2h)

**Dia 2 (8 horas):**
- TASK-012: MAXIMUS Integration (4h)
- TASK-013: E2E Tests (3h)
- TASK-014: Documentation (1h)

### Timeline Realista (3 dias)

**Dia 1 (8 horas):**
- TASK-010: FastAPI Completion (8h)

**Dia 2 (8 horas):**
- TASK-011: Docker Complete (3h)
- TASK-012: MAXIMUS Integration (5h)

**Dia 3 (8 horas):**
- TASK-013: E2E Tests (5h)
- TASK-014: Documentation (3h)

### Estimativa Total

| Task | Duração | LOC | Prioridade |
|------|---------|-----|------------|
| TASK-010 | 6-8h | 300 | CRÍTICA |
| TASK-011 | 2-3h | 150 | CRÍTICA |
| TASK-012 | 4-5h | 400 | CRÍTICA |
| TASK-013 | 3-4h | 500 | ALTA |
| TASK-014 | 2-3h | N/A | ALTA |
| **TOTAL** | **17-23h** | **~1,350** | - |

---

## 🎯 PRÓXIMO PASSO IMEDIATO

**Iniciar**: TASK-010 (FastAPI Service Completion)

**Razão**:
- Critical path
- Dependency para todas outras tasks
- Demonstrável imediatamente
- Unlock E2E testing

**Comando para começar:**
```bash
cd /home/juan/vertice-dev/backend/consciousness/mip
code api.py  # Abrir e completar endpoints
```

---

## ✅ VALIDAÇÃO FINAL (Fase 4 Completa)

Checklist para considerar FASE 4 concluída:

- [ ] ✅ TASK-010: API 8 endpoints funcionais
- [ ] ✅ TASK-011: Docker compose up funciona
- [ ] ✅ TASK-012: MAXIMUS pode chamar MIP
- [ ] ✅ TASK-013: E2E tests 100% pass
- [ ] ✅ TASK-014: Docs completas

**Comando de Validação Final:**
```bash
# Full stack test
cd /home/juan/vertice-dev

# 1. Build and start
docker-compose -f docker-compose.mip.yml up -d --build

# 2. Health checks
curl http://localhost:8100/health

# 3. Run all tests
pytest backend/consciousness/mip/tests/ -v --cov
pytest tests/integration/test_mip_e2e.py -v
pytest backend/services/maximus_core_service/tests/test_mip_client.py -v

# 4. Performance test
pytest tests/integration/test_mip_performance.py -v

# Expected: ALL GREEN ✅
```

---

**Assinado**: GitHub Copilot CLI  
**Arquiteto**: Juan Carlos de Souza (MAXIMUS Project)  
**Data**: 2025-10-14  
**Versão**: 1.0  

**Status**: PRONTO PARA EXECUÇÃO  
**Padrão**: PAGANI 100% CUMPRIDO

🚀 **LET'S BUILD SOMETHING LEGENDARY!** 🚀
