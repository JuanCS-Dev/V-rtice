# 🛠️ PLANO DE IMPLEMENTAÇÃO - Sistema Imunológico Adaptativo

**Data**: 2025-10-10  
**Status**: 🟢 **PLANO APROVADO - INÍCIO IMEDIATO**  
**Metodologia**: TDD + Incremental + Production-First  
**Tooling**: Python 3.11+, FastAPI, Kafka, K8s, ast-grep, LLMs

---

## 🎯 FILOSOFIA DE IMPLEMENTAÇÃO

### Princípios MAXIMUS
1. ❌ **NO MOCK** - Implementações reais desde Sprint 1
2. ❌ **NO PLACEHOLDER** - Zero `pass` ou `NotImplementedError` em main paths
3. ✅ **TDD Rigoroso** - Teste antes de implementação
4. ✅ **Type Hints 100%** - mypy --strict passing
5. ✅ **Production-Ready** - Cada merge é deployável
6. ✅ **Documentação Histórica** - Commits serão estudados em 2050

### Abordagem Incremental
Cada sprint entrega **funcionalidade end-to-end testável**, não componentes isolados. MVP Sprint 1 já permite CVE→APV→Confirmação completo.

---

## 📦 ESTRUTURA DE DIRETÓRIOS

```
backend/services/
├── maximus_oraculo/                # Refatoração do existente
│   ├── oraculo.py                  # Core engine (REFACTOR)
│   ├── threat_feeds/               # NOVO
│   │   ├── osv_client.py          # Cliente OSV.dev
│   │   ├── nvd_client.py          # Cliente NVD backup
│   │   └── docker_security.py     # Docker CVEs
│   ├── enrichment/                 # NOVO
│   │   ├── cvss_normalizer.py     # CVSS scoring
│   │   ├── cwe_extractor.py       # CWE mapping
│   │   └── signature_generator.py # ast-grep patterns
│   ├── filtering/                  # NOVO
│   │   ├── dependency_graph.py    # Grafo de deps
│   │   └── relevance_filter.py    # Filtro contextual
│   ├── models/                     # NOVO
│   │   ├── apv.py                 # APV Pydantic model
│   │   └── enriched_vuln.py       # EnrichedVulnerability
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── maximus_eureka/                 # Refatoração do existente
│   ├── eureka.py                   # Core engine (REFACTOR)
│   ├── consumers/                  # NOVO
│   │   └── apv_consumer.py        # Kafka APV consumer
│   ├── confirmation/               # NOVO
│   │   ├── ast_grep_engine.py     # Wrapper ast-grep
│   │   └── vulnerability_confirmer.py
│   ├── strategies/                 # NOVO
│   │   ├── dependency_upgrade.py  # Strategy 1
│   │   ├── code_patch_llm.py      # Strategy 2 (APPATCH)
│   │   └── coagulation_integrator.py  # Strategy 3
│   ├── llm/                        # NOVO
│   │   ├── claude_client.py       # Anthropic Claude
│   │   ├── openai_client.py       # GPT-4
│   │   ├── gemini_client.py       # Google Gemini
│   │   └── prompt_templates.py    # APPATCH prompts
│   ├── git_integration/            # NOVO
│   │   ├── branch_manager.py      # Git operations
│   │   └── patch_applicator.py    # Secure patch apply
│   └── tests/
│
├── adaptive_immunity_wargaming/    # NOVO SERVICE
│   ├── api.py
│   ├── provisioner/
│   │   ├── k8s_namespace.py       # Ephemeral envs
│   │   └── iac_validator.py       # Template security
│   ├── testing/
│   │   ├── regression_runner.py   # Pytest executor
│   │   └── two_phase_validator.py # Baseline + Patched
│   ├── attack_simulation/
│   │   ├── framework.py           # Core framework
│   │   ├── modules/
│   │   │   ├── http_attack.py     # HTTP exploits
│   │   │   ├── network_attack.py  # Scapy-based
│   │   │   └── custom_exploits.py # Scriptable
│   │   └── payload_generators.py
│   └── tests/
│
├── adaptive_immunity_hitl/         # NOVO SERVICE
│   ├── api.py
│   ├── pr_generation/
│   │   ├── github_client.py       # PyGithub wrapper
│   │   ├── template_engine.py     # Jinja2 Markdown
│   │   └── artifact_bundler.py    # Collects logs/reports
│   ├── dashboards/
│   │   └── api_endpoints.py       # Frontend API
│   └── tests/
│
└── shared/                         # Shared utilities
    ├── kafka_utils.py
    ├── redis_utils.py
    └── audit_logger.py
```

---

## 🔧 SETUP INICIAL (Pré-Sprint 1)

### 1. Dependências Python

```bash
# backend/services/maximus_oraculo/requirements.txt
aiohttp==3.9.1              # HTTP async client
httpx==0.25.2               # Alternative HTTP client
pydantic==2.5.0             # Data validation
kafka-python==2.0.2         # Kafka client
redis==5.0.1                # Redis client
tomli==2.0.1                # TOML parser (backport)
# tomllib built-in Python 3.11+

# LLM clients
anthropic==0.8.0            # Claude
openai==1.6.0               # GPT-4
google-generativeai==0.3.0  # Gemini

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx[test]==0.25.2         # Mock HTTP
```

### 2. Infraestrutura (Docker Compose)

```yaml
# docker-compose.adaptive-immunity.yml
version: '3.8'

services:
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    ports:
      - "2181:2181"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: maximus_adaptive_immunity
      POSTGRES_USER: maximus
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  oraculo:
    build: ./backend/services/maximus_oraculo
    environment:
      OSV_API_URL: https://api.osv.dev/v1
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      REDIS_URL: redis://redis:6379
      POSTGRES_DSN: postgresql://maximus:${POSTGRES_PASSWORD}@postgres:5432/maximus_adaptive_immunity
    depends_on:
      - kafka
      - redis
      - postgres

  eureka:
    build: ./backend/services/maximus_eureka
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      REDIS_URL: redis://redis:6379
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      GIT_REPO_PATH: /opt/maximus/repo
    volumes:
      - maximus-repo:/opt/maximus/repo:ro
    depends_on:
      - kafka
      - oraculo

volumes:
  maximus-repo:
```

### 3. Database Schema

```sql
-- init.sql

CREATE TABLE apvs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_id VARCHAR(50) NOT NULL UNIQUE,
    raw_vulnerability JSONB NOT NULL,
    enriched_vulnerability JSONB NOT NULL,
    apv_object JSONB NOT NULL,
    priority VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending'
);

CREATE INDEX idx_apvs_cve_id ON apvs(cve_id);
CREATE INDEX idx_apvs_status ON apvs(status);
CREATE INDEX idx_apvs_priority ON apvs(priority);
CREATE INDEX idx_apvs_created_at ON apvs(created_at DESC);

CREATE TABLE patches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_id VARCHAR(50) NOT NULL REFERENCES apvs(cve_id),
    strategy VARCHAR(50) NOT NULL,
    patch_diff TEXT NOT NULL,
    llm_model VARCHAR(100),
    llm_confidence FLOAT,
    git_branch VARCHAR(255),
    git_commit_sha VARCHAR(40),
    validation_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    validated_at TIMESTAMP,
    merged_at TIMESTAMP
);

CREATE INDEX idx_patches_cve_id ON patches(cve_id);
CREATE INDEX idx_patches_status ON patches(validation_status);

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    source_service VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id VARCHAR(100)
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_log(event_type);

-- Few-shot examples database
CREATE TABLE vulnerability_fixes (
    id SERIAL PRIMARY KEY,
    cwe_id VARCHAR(20) NOT NULL,
    vulnerability_type VARCHAR(100),
    vulnerable_code TEXT NOT NULL,
    fixed_code TEXT NOT NULL,
    explanation TEXT,
    language VARCHAR(50) DEFAULT 'python',
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vul_fixes_cwe ON vulnerability_fixes(cwe_id);
```

---

## 📝 SPRINT 1 IMPLEMENTATION CHECKLIST

### Dia 1-2: Oráculo - Threat Feeds

**Arquivo**: `backend/services/maximus_oraculo/threat_feeds/osv_client.py`

```python
"""OSV.dev API client com retry logic e rate limiting."""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class OSVClient:
    """
    Cliente para OSV.dev API.
    
    Docs: https://ossf.github.io/osv-schema/
    Rate limit: Sem limite oficial, mas respeitar 100 req/min
    \"\"\"
    
    BASE_URL = "https://api.osv.dev/v1"
    
    def __init__(self, rate_limit: int = 100):
        self.rate_limit = rate_limit  # requests per minute
        self._request_times: List[datetime] = []
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def _rate_limit_wait(self):
        \"\"\"Implementa rate limiting baseado em janela deslizante\"\"\"
        now = datetime.now()
        # Remove requests mais antigos que 1 minuto
        self._request_times = [t for t in self._request_times if now - t < timedelta(minutes=1)]
        
        if len(self._request_times) >= self.rate_limit:
            # Aguarda até o request mais antigo "expirar"
            oldest = self._request_times[0]
            wait_time = 60 - (now - oldest).seconds
            if wait_time > 0:
                logger.info(f"Rate limit atingido, aguardando {wait_time}s")
                await asyncio.sleep(wait_time)
        
        self._request_times.append(now)
    
    async def query_package(
        self,
        package_name: str,
        ecosystem: str = "PyPI"
    ) -> List[Dict]:
        \"\"\"
        Query vulnerabilities para um package específico.
        
        Args:
            package_name: Nome do package (ex: 'requests')
            ecosystem: Ecossistema (PyPI, npm, Go, etc)
            
        Returns:
            Lista de vulnerabilidades
        \"\"\"
        await self._rate_limit_wait()
        
        url = f"{self.BASE_URL}/query"
        payload = {
            "package": {
                "name": package_name,
                "ecosystem": ecosystem
            }
        }
        
        for attempt in range(3):  # Retry logic
            try:
                async with self._session.post(url, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data.get('vulns', [])
            except aiohttp.ClientError as e:
                logger.warning(f"Tentativa {attempt + 1} falhou: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def get_vulnerability(self, vuln_id: str) -> Optional[Dict]:
        \"\"\"Obtém detalhes de uma vulnerabilidade específica por ID\"\"\"
        await self._rate_limit_wait()
        
        url = f"{self.BASE_URL}/vulns/{vuln_id}"
        
        async with self._session.get(url) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            return await resp.json()
```

**Testes** (`tests/unit/test_osv_client.py`):

```python
import pytest
from unittest.mock import AsyncMock, patch
from threat_feeds.osv_client import OSVClient

@pytest.mark.asyncio
async def test_osv_client_query_package(respx_mock):
    \"\"\"Test query de package com mock HTTP\"\"\"
    respx_mock.post("https://api.osv.dev/v1/query").mock(
        return_value=httpx.Response(200, json={
            "vulns": [{
                "id": "GHSA-xxxx-xxxx-xxxx",
                "summary": "Test vulnerability"
            }]
        })
    )
    
    async with OSVClient() as client:
        vulns = await client.query_package("requests", "PyPI")
        
    assert len(vulns) == 1
    assert vulns[0]['id'] == "GHSA-xxxx-xxxx-xxxx"

@pytest.mark.asyncio
async def test_osv_client_rate_limiting():
    \"\"\"Test rate limiting funciona\"\"\"
    client = OSVClient(rate_limit=5)
    
    start = time.time()
    
    # Faz 10 requests (deve aguardar após 5)
    for _ in range(10):
        await client._rate_limit_wait()
    
    elapsed = time.time() - start
    
    # Deve ter aguardado pelo menos ~60s para os últimos 5
    assert elapsed >= 55  # Margem de erro
```

---

_(Plano continua com implementação detalhada de cada módulo Sprint 1, depois Sprint 2-6...)_

**✅ Plano de Implementação iniciado - estrutura completa documentada.**
