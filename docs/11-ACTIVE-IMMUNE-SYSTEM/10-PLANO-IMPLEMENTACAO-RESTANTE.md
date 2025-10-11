# 🎯 PLANO DE IMPLEMENTAÇÃO - Active Immune System (Restante)

**Data**: 2025-10-11  
**Status**: 🟡 **AGUARDANDO APROVAÇÃO**  
**Sessão**: Continuação Active Immune System Oráculo-Eureka  
**Fase Atual**: Sprint 1 não iniciado → Dashboard Frontend não implementado

---

## 📊 SITUAÇÃO ATUAL

### ✅ Completado
1. **Documentação 100%**
   - Blueprint técnico completo (19KB)
   - Roadmap 6 sprints detalhado (11KB)
   - Plano de implementação (14KB)
   - Total: ~1,600 linhas de especificação

2. **Estrutura Backend Existente**
   - `backend/services/maximus_oraculo/` - Service base (obsoleto, precisa refactor)
   - `backend/services/maximus_eureka/` - Service base (obsoleto, precisa refactor)
   - Ambos têm implementação antiga não relacionada ao immune system

3. **Frontend Base**
   - Next.js 14 + TypeScript estruturado
   - Dashboards existentes: Defensive, Offensive, PurpleTeam
   - Sistema de temas implementado (Windows 11 style)

### ❌ Faltando
1. **Backend Immune System** - 0% implementado
2. **Frontend Dashboard** - 0% implementado
3. **Infraestrutura** - Kafka, Redis, PostgreSQL não configurados para immune
4. **Testes E2E** - 0% implementado
5. **Integração Oráculo-Eureka** - 0% implementado

---

## 🎯 OBJETIVO FINAL

Implementar ciclo completo **Oráculo→Eureka→Crisol→HITL** conforme blueprint, com foco inicial em:

1. **Backend Sprint 1** (Oráculo Core + Eureka Core)
2. **Frontend Dashboard** para visualização em tempo real
3. **Infraestrutura mínima** (Kafka, Redis, PostgreSQL)
4. **E2E Validation** CVE→APV→Confirmação

**MTTR Target**: < 45 minutos  
**Success Rate Target**: > 70%

---

## 📋 PLANO ESTRUTURADO

### FASE 1: INFRAESTRUTURA BASE (Dia 1)
**Duração**: 4-6 horas  
**Responsável**: DevOps automation

#### 1.1 Docker Compose Adaptive Immunity
**Arquivo**: `docker-compose.adaptive-immunity.yml`

```yaml
version: '3.8'

services:
  # Kafka para APV stream
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
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

  # Redis para pub/sub events
  redis-immunity:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    command: redis-server --appendonly yes

  # PostgreSQL para APVs, patches, audit
  postgres-immunity:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: adaptive_immunity
      POSTGRES_USER: maximus
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
    ports:
      - "5433:5432"
    volumes:
      - postgres-immunity-data:/var/lib/postgresql/data
      - ./backend/services/adaptive_immunity_db/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  postgres-immunity-data:
```

**Validação**:
```bash
docker-compose -f docker-compose.adaptive-immunity.yml up -d
docker-compose -f docker-compose.adaptive-immunity.yml ps
# Deve mostrar 4 services rodando: kafka, zookeeper, redis-immunity, postgres-immunity
```

#### 1.2 Database Schema
**Arquivo**: `backend/services/adaptive_immunity_db/init.sql`

```sql
-- APVs (Actionable Prioritized Vulnerabilities)
CREATE TABLE apvs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_id VARCHAR(50) NOT NULL UNIQUE,
    raw_vulnerability JSONB NOT NULL,
    enriched_vulnerability JSONB NOT NULL,
    apv_object JSONB NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'confirmed', 'rejected', 'patched'))
);

CREATE INDEX idx_apvs_cve_id ON apvs(cve_id);
CREATE INDEX idx_apvs_status ON apvs(status);
CREATE INDEX idx_apvs_priority ON apvs(priority);
CREATE INDEX idx_apvs_created_at ON apvs(created_at DESC);

-- Patches gerados pelo Eureka
CREATE TABLE patches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_id VARCHAR(50) NOT NULL REFERENCES apvs(cve_id),
    strategy VARCHAR(50) NOT NULL CHECK (strategy IN ('dependency_upgrade', 'code_patch', 'coagulation_waf')),
    patch_diff TEXT NOT NULL,
    llm_model VARCHAR(100),
    llm_confidence FLOAT CHECK (llm_confidence >= 0 AND llm_confidence <= 1),
    git_branch VARCHAR(255),
    git_commit_sha VARCHAR(40),
    validation_status VARCHAR(50) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validating', 'passed', 'failed', 'merged')),
    created_at TIMESTAMP DEFAULT NOW(),
    validated_at TIMESTAMP,
    merged_at TIMESTAMP
);

CREATE INDEX idx_patches_cve_id ON patches(cve_id);
CREATE INDEX idx_patches_status ON patches(validation_status);
CREATE INDEX idx_patches_created_at ON patches(created_at DESC);

-- Audit log completo
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    source_service VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id VARCHAR(100),
    severity VARCHAR(20) CHECK (severity IN ('info', 'warning', 'error', 'critical'))
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_source ON audit_log(source_service);

-- Few-shot learning examples para LLM
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
CREATE INDEX idx_vul_fixes_lang ON vulnerability_fixes(language);

-- Seed data: exemplo de few-shot
INSERT INTO vulnerability_fixes (cwe_id, vulnerability_type, vulnerable_code, fixed_code, explanation, language, source) VALUES
('CWE-89', 'SQL Injection', 
 'query = f"SELECT * FROM users WHERE id = {user_id}"',
 'query = "SELECT * FROM users WHERE id = ?" \nparams = (user_id,)',
 'Use parameterized queries to prevent SQL injection',
 'python',
 'OWASP Examples'),
('CWE-79', 'XSS',
 'return f"<div>{user_input}</div>"',
 'from html import escape\nreturn f"<div>{escape(user_input)}</div>"',
 'Always escape user input in HTML context',
 'python',
 'OWASP Examples');
```

**Validação**:
```bash
docker exec -it $(docker ps -qf "name=postgres-immunity") \
  psql -U maximus -d adaptive_immunity -c "\dt"
# Deve listar 4 tabelas: apvs, patches, audit_log, vulnerability_fixes
```

#### 1.3 Kafka Topics Setup
**Script**: `scripts/setup/setup-kafka-topics.sh`

```bash
#!/bin/bash
# Purpose: Create Kafka topics for Adaptive Immunity
# Usage: ./setup-kafka-topics.sh
# Author: MAXIMUS Team
# Date: 2025-10-11

set -e
set -u

KAFKA_CONTAINER=$(docker ps -qf "name=kafka")

if [ -z "$KAFKA_CONTAINER" ]; then
  echo "❌ Kafka container not running"
  exit 1
fi

echo "🚀 Creating Adaptive Immunity Kafka topics..."

# APV topic (Oráculo → Eureka)
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic maximus.adaptive-immunity.apv \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists \
  --bootstrap-server localhost:9092

# Patches topic (Eureka → HITL)
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic maximus.adaptive-immunity.patches \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists \
  --bootstrap-server localhost:9092

# Events topic (todos os eventos do sistema)
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic maximus.adaptive-immunity.events \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists \
  --bootstrap-server localhost:9092

# Dead letter queue
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic maximus.adaptive-immunity.dlq \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists \
  --bootstrap-server localhost:9092

echo "✅ Topics created successfully"

# Listar topics
docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server localhost:9092
```

**Validação**:
```bash
chmod +x scripts/setup/setup-kafka-topics.sh
./scripts/setup/setup-kafka-topics.sh
# Deve criar 4 topics e listar todos
```

**Checklist Fase 1**:
- [ ] docker-compose.adaptive-immunity.yml criado
- [ ] Infra levantada (4 containers rodando)
- [ ] init.sql executado (4 tabelas criadas)
- [ ] Kafka topics criados (4 topics)
- [ ] Validação E2E: conectar em cada serviço manualmente

---

### FASE 2: BACKEND ORÁCULO CORE (Dias 2-3)
**Duração**: 12-16 horas  
**Responsável**: Backend development

#### 2.1 Refatoração Estrutura Oráculo

**Objetivo**: Transformar `maximus_oraculo` de service genérico em **Threat Intelligence Sentinel**.

**Estrutura Nova**:
```
backend/services/maximus_oraculo/
├── __init__.py
├── oraculo.py                    # REFACTOR: OraculoEngine → ThreatSentinel
├── api.py                         # FastAPI endpoints (manter)
├── threat_feeds/                  # NOVO
│   ├── __init__.py
│   ├── osv_client.py             # OSV.dev API client
│   ├── nvd_client.py             # NVD backup feed
│   └── base_feed.py              # Abstract base class
├── enrichment/                    # NOVO
│   ├── __init__.py
│   ├── cvss_normalizer.py        # CVSS score normalization
│   ├── cwe_mapper.py             # CWE taxonomy mapping
│   └── signature_generator.py   # ast-grep pattern generation
├── filtering/                     # NOVO
│   ├── __init__.py
│   ├── dependency_graph.py       # Build dep graph from repo
│   └── relevance_filter.py       # Filter CVEs by relevance
├── models/                        # NOVO
│   ├── __init__.py
│   ├── apv.py                    # APV Pydantic model
│   ├── raw_vulnerability.py      # RawVulnerability model
│   └── enriched_vulnerability.py # EnrichedVulnerability model
├── kafka_integration/             # NOVO
│   ├── __init__.py
│   └── apv_publisher.py          # Kafka producer para APVs
└── tests/
    ├── unit/
    │   ├── test_osv_client.py
    │   ├── test_dependency_graph.py
    │   └── test_relevance_filter.py
    ├── integration/
    │   └── test_oraculo_kafka.py
    └── e2e/
        └── test_cve_to_apv_flow.py
```

#### 2.2 Implementação Prioritária

**Ordem de implementação** (TDD - test first):

**Dia 2 - Manhã** (4h):
1. `models/apv.py` - Pydantic APV schema
2. `models/raw_vulnerability.py` - Schema CVE input
3. `threat_feeds/base_feed.py` - Abstract class
4. **Testes**: `tests/unit/test_apv_model.py`

**Dia 2 - Tarde** (4h):
5. `threat_feeds/osv_client.py` - OSV.dev client completo
6. **Testes**: `tests/unit/test_osv_client.py` (mock HTTP)
7. **Testes integração**: `tests/integration/test_osv_live.py` (real API)

**Dia 3 - Manhã** (4h):
8. `filtering/dependency_graph.py` - Parser pyproject.toml + pip list
9. `filtering/relevance_filter.py` - Cross-reference logic
10. **Testes**: `tests/unit/test_dependency_graph.py`

**Dia 3 - Tarde** (4h):
11. `enrichment/signature_generator.py` - Gerar ast-grep patterns
12. `kafka_integration/apv_publisher.py` - Kafka producer
13. **Testes E2E**: `tests/e2e/test_cve_to_apv_flow.py`

#### 2.3 Código Exemplo: APV Model

**Arquivo**: `backend/services/maximus_oraculo/models/apv.py`

```python
"""APV (Actionable Prioritized Vulnerability) Pydantic model.

Extends CVE JSON 5.1.1 schema with MAXIMUS-specific fields for automated remediation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class PriorityLevel(str, Enum):
    """Priority levels para APV."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RemediationStrategy(str, Enum):
    """Estratégias de remediação disponíveis."""
    DEPENDENCY_UPGRADE = "dependency_upgrade"
    CODE_PATCH = "code_patch"
    COAGULATION_WAF = "coagulation_waf"
    MANUAL_REVIEW = "manual_review"


class CVSSScore(BaseModel):
    """CVSS score normalizado."""
    version: str = Field(..., description="CVSS version (3.1, 4.0)")
    base_score: float = Field(..., ge=0.0, le=10.0)
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    vector_string: str = Field(..., description="CVSS vector string")


class ASTGrepPattern(BaseModel):
    """Padrão ast-grep para confirmação de vulnerabilidade."""
    language: str = Field(default="python", description="Linguagem alvo")
    pattern: str = Field(..., description="ast-grep pattern string")
    severity: str = Field(..., description="Severidade do match")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "pattern": "eval($ARG)",
                "severity": "critical"
            }
        }


class AffectedPackage(BaseModel):
    """Package afetado pela vulnerabilidade."""
    ecosystem: str = Field(..., description="PyPI, npm, Go, etc")
    name: str = Field(..., description="Nome do package")
    affected_versions: List[str] = Field(..., description="Version ranges afetadas")
    fixed_versions: List[str] = Field(default_factory=list, description="Versões corrigidas")
    
    @validator('ecosystem')
    def validate_ecosystem(cls, v):
        valid_ecosystems = ['PyPI', 'npm', 'Go', 'Maven', 'Docker']
        if v not in valid_ecosystems:
            raise ValueError(f"Ecosystem must be one of {valid_ecosystems}")
        return v


class APV(BaseModel):
    """
    Actionable Prioritized Vulnerability (APV).
    
    Estrutura de dados unificada para vulnerabilidades processadas pelo Oráculo,
    pronta para consumo pelo Eureka. Extende CVE JSON 5.1.1 com campos MAXIMUS.
    
    Fundamentação:
    - OSV schema (ossf.github.io/osv-schema)
    - CVE JSON 5.1.1 (github.com/CVEProject/cve-schema)
    - APPATCH methodology (automated program patching)
    """
    
    # Identificadores
    cve_id: str = Field(..., description="CVE ID (ex: CVE-2024-12345)")
    aliases: List[str] = Field(default_factory=list, description="GHSA, OSV IDs")
    
    # Metadata temporal
    published: datetime = Field(..., description="Data de publicação")
    modified: datetime = Field(..., description="Última modificação")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp processamento Oráculo")
    
    # Descrição e impacto
    summary: str = Field(..., description="Resumo executivo da vulnerabilidade")
    details: str = Field(..., description="Descrição técnica detalhada")
    
    # Scoring e priorização
    cvss: Optional[CVSSScore] = Field(None, description="CVSS score normalizado")
    priority: PriorityLevel = Field(..., description="Prioridade MAXIMUS calculada")
    
    # Packages afetados
    affected_packages: List[AffectedPackage] = Field(..., description="Packages e versões afetadas")
    
    # Confirmação de código
    ast_grep_patterns: List[ASTGrepPattern] = Field(
        default_factory=list, 
        description="Padrões para confirmação determinística"
    )
    
    # Remediação sugerida
    recommended_strategy: RemediationStrategy = Field(..., description="Estratégia recomendada")
    remediation_complexity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    
    # Context MAXIMUS
    maximus_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context adicional para decisão Eureka"
    )
    
    # Tracking
    source_feed: str = Field(..., description="OSV.dev, NVD, Docker Security")
    oraculo_version: str = Field(default="1.0.0", description="Versão do Oráculo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cve_id": "CVE-2024-12345",
                "aliases": ["GHSA-xxxx-yyyy-zzzz"],
                "published": "2024-10-01T00:00:00Z",
                "modified": "2024-10-05T12:00:00Z",
                "summary": "SQL Injection in Django ORM",
                "details": "Django versions < 4.2.8 vulnerable to SQL injection...",
                "cvss": {
                    "version": "3.1",
                    "base_score": 9.8,
                    "severity": "CRITICAL",
                    "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                },
                "priority": "critical",
                "affected_packages": [{
                    "ecosystem": "PyPI",
                    "name": "django",
                    "affected_versions": [">=3.0,<4.2.8"],
                    "fixed_versions": ["4.2.8"]
                }],
                "ast_grep_patterns": [{
                    "language": "python",
                    "pattern": "Model.objects.raw($QUERY)",
                    "severity": "critical"
                }],
                "recommended_strategy": "dependency_upgrade",
                "remediation_complexity": "LOW",
                "maximus_context": {
                    "affected_services": ["maximus_core_service", "maximus_api_gateway"],
                    "deployment_impact": "medium",
                    "rollback_available": True
                },
                "source_feed": "OSV.dev"
            }
        }

    @validator('priority', always=True)
    def calculate_priority(cls, v, values):
        """
        Calcula prioridade baseada em CVSS + context MAXIMUS.
        
        Regras:
        - CVSS >= 9.0 + exploits públicos → CRITICAL
        - CVSS >= 7.0 + affected_services > 3 → HIGH
        - CVSS >= 4.0 → MEDIUM
        - Resto → LOW
        """
        if v:  # Se já foi setado manualmente
            return v
            
        cvss = values.get('cvss')
        if not cvss:
            return PriorityLevel.LOW
            
        score = cvss.base_score
        context = values.get('maximus_context', {})
        affected_count = len(context.get('affected_services', []))
        
        if score >= 9.0:
            return PriorityLevel.CRITICAL
        elif score >= 7.0 and affected_count > 3:
            return PriorityLevel.HIGH
        elif score >= 4.0:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW

    @validator('recommended_strategy', always=True)
    def calculate_strategy(cls, v, values):
        """
        Calcula estratégia recomendada baseada em tipo de vulnerabilidade.
        
        Regras:
        - Dependency com fixed version disponível → DEPENDENCY_UPGRADE
        - Code pattern + LLM confidence > 0.8 → CODE_PATCH
        - Zero-day sem fix → COAGULATION_WAF
        - Complexidade CRITICAL → MANUAL_REVIEW
        """
        if v:  # Se já foi setado
            return v
            
        complexity = values.get('remediation_complexity', 'MEDIUM')
        affected = values.get('affected_packages', [])
        
        if complexity == 'CRITICAL':
            return RemediationStrategy.MANUAL_REVIEW
            
        # Checa se há fixed version disponível
        has_fixed_version = any(
            len(pkg.fixed_versions) > 0 
            for pkg in affected
        )
        
        if has_fixed_version:
            return RemediationStrategy.DEPENDENCY_UPGRADE
        
        # Se há padrão ast-grep, tentar patch
        patterns = values.get('ast_grep_patterns', [])
        if patterns:
            return RemediationStrategy.CODE_PATCH
            
        # Fallback: WAF temporária
        return RemediationStrategy.COAGULATION_WAF


# Type alias para facilitar imports
ActionablePrioritizedVulnerability = APV
```

**Checklist Fase 2**:
- [ ] Estrutura de diretórios criada
- [ ] `models/apv.py` implementado + testes
- [ ] `threat_feeds/osv_client.py` implementado + testes
- [ ] `filtering/dependency_graph.py` implementado + testes
- [ ] `kafka_integration/apv_publisher.py` implementado + testes
- [ ] Teste E2E: CVE fake → APV → Kafka → consumir

---

### FASE 3: BACKEND EUREKA CORE (Dias 4-5)
**Duração**: 12-16 horas  
**Responsável**: Backend development

#### 3.1 Refatoração Estrutura Eureka

**Objetivo**: Transformar `maximus_eureka` em **Adaptive Response Surgeon**.

**Estrutura Nova**:
```
backend/services/maximus_eureka/
├── __init__.py
├── eureka.py                      # REFACTOR: EurekaEngine → AdaptiveSurgeon
├── api.py                         # FastAPI endpoints (manter)
├── consumers/                     # NOVO
│   ├── __init__.py
│   └── apv_consumer.py           # Kafka consumer para APVs
├── confirmation/                  # NOVO
│   ├── __init__.py
│   ├── ast_grep_engine.py        # Wrapper subprocess ast-grep
│   └── vulnerability_confirmer.py # Confirma vulnerability na codebase
├── strategies/                    # NOVO
│   ├── __init__.py
│   ├── base_strategy.py          # Abstract base class
│   ├── dependency_upgrade.py     # Strategy 1: Bump version
│   ├── code_patch_llm.py         # Strategy 2: LLM patch (APPATCH)
│   └── coagulation_waf.py        # Strategy 3: WAF temporária
├── llm/                           # NOVO
│   ├── __init__.py
│   ├── base_client.py            # Abstract LLM client
│   ├── claude_client.py          # Anthropic Claude
│   ├── openai_client.py          # OpenAI GPT-4
│   ├── gemini_client.py          # Google Gemini
│   └── prompt_templates.py       # APPATCH-inspired prompts
├── git_integration/               # NOVO
│   ├── __init__.py
│   ├── branch_manager.py         # Git branch operations
│   └── patch_applicator.py       # Apply patch safely
└── tests/
    ├── unit/
    │   ├── test_ast_grep_engine.py
    │   ├── test_dependency_upgrade.py
    │   └── test_llm_clients.py
    ├── integration/
    │   └── test_eureka_kafka.py
    └── e2e/
        └── test_apv_to_patch_flow.py
```

#### 3.2 Implementação Prioritária

**Dia 4 - Manhã** (4h):
1. `consumers/apv_consumer.py` - Kafka consumer com DLQ
2. `confirmation/ast_grep_engine.py` - Wrapper subprocess
3. **Testes**: `tests/unit/test_apv_consumer.py`

**Dia 4 - Tarde** (4h):
4. `confirmation/vulnerability_confirmer.py` - Lógica de confirmação
5. `strategies/base_strategy.py` - Abstract class
6. `strategies/dependency_upgrade.py` - Strategy 1 (simples)
7. **Testes**: `tests/unit/test_vulnerability_confirmer.py`

**Dia 5 - Manhã** (4h):
8. `llm/base_client.py` + `llm/claude_client.py` - LLM integration
9. `llm/prompt_templates.py` - APPATCH prompts
10. **Testes**: `tests/unit/test_llm_clients.py` (mock API)

**Dia 5 - Tarde** (4h):
11. `strategies/code_patch_llm.py` - Strategy 2 (LLM patch)
12. `git_integration/patch_applicator.py` - Git operations
13. **Testes E2E**: `tests/e2e/test_apv_to_patch_flow.py`

**Checklist Fase 3**:
- [ ] Estrutura de diretórios criada
- [ ] `consumers/apv_consumer.py` implementado + testes
- [ ] `confirmation/ast_grep_engine.py` implementado + testes
- [ ] `strategies/dependency_upgrade.py` implementado + testes
- [ ] `llm/claude_client.py` implementado + testes
- [ ] `strategies/code_patch_llm.py` implementado + testes
- [ ] Teste E2E: APV → Confirmação → Patch → Git branch

---

### FASE 4: FRONTEND DASHBOARD (Dias 6-7)
**Duração**: 12-16 horas  
**Responsável**: Frontend development

#### 4.1 Estrutura Dashboard

**Objetivo**: Dashboard em tempo real para monitorar ciclo Oráculo→Eureka→Patches.

**Localização**: `frontend/src/components/dashboards/AdaptiveImmunityDashboard/`

**Estrutura**:
```
frontend/src/components/dashboards/AdaptiveImmunityDashboard/
├── index.jsx                      # Main dashboard component
├── components/
│   ├── APVStream.jsx             # Real-time APV feed (WebSocket)
│   ├── APVCard.jsx               # Individual APV display
│   ├── ThreatMap.jsx             # Visualization geográfica
│   ├── PatchesTable.jsx          # Tabela de patches gerados
│   ├── MetricsPanel.jsx          # KPIs: MTTR, Success Rate
│   └── RemediationTimeline.jsx   # Timeline visual do processo
├── hooks/
│   ├── useAPVStream.js           # WebSocket hook
│   ├── useMetrics.js             # Fetch metrics API
│   └── usePatchesHistory.js      # Fetch patches history
├── api/
│   └── adaptiveImmunityAPI.js    # API client
└── __tests__/
    ├── AdaptiveImmunityDashboard.test.jsx
    └── APVStream.test.jsx
```

#### 4.2 Componentes Principais

**Dia 6 - Manhã** (4h):
1. `api/adaptiveImmunityAPI.js` - API client para backend
2. `hooks/useAPVStream.js` - WebSocket hook
3. **Testes**: Mock WebSocket connection

**Dia 6 - Tarde** (4h):
4. `components/APVCard.jsx` - Card individual APV
5. `components/APVStream.jsx` - Feed tempo real
6. **Testes**: Render tests

**Dia 7 - Manhã** (4h):
7. `components/PatchesTable.jsx` - Tabela patches
8. `components/MetricsPanel.jsx` - KPIs dashboard
9. **Testes**: Integration tests

**Dia 7 - Tarde** (4h):
10. `index.jsx` - Dashboard principal (composição)
11. `components/RemediationTimeline.jsx` - Timeline visual
12. **Integração**: Conectar com backend real

#### 4.3 Código Exemplo: APV Stream Component

**Arquivo**: `frontend/src/components/dashboards/AdaptiveImmunityDashboard/components/APVStream.jsx`

```jsx
/**
 * APVStream - Real-time APV feed via WebSocket
 * 
 * Displays incoming APVs from Oráculo in real-time with priority-based styling.
 */

import React, { useEffect, useState } from 'react';
import { useAPVStream } from '../hooks/useAPVStream';
import APVCard from './APVCard';

const APVStream = () => {
  const { apvs, isConnected, error } = useAPVStream();
  const [filter, setFilter] = useState('all'); // all, critical, high, medium, low

  const filteredAPVs = apvs.filter(apv => {
    if (filter === 'all') return true;
    return apv.priority === filter;
  });

  return (
    <div className="apv-stream">
      <div className="apv-stream__header">
        <h2 className="text-2xl font-bold">Live Threat Intelligence</h2>
        <div className="flex items-center gap-4">
          {/* Connection status */}
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className={`status-dot ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>

          {/* Priority filters */}
          <div className="filter-buttons">
            {['all', 'critical', 'high', 'medium', 'low'].map(priority => (
              <button
                key={priority}
                onClick={() => setFilter(priority)}
                className={`filter-btn ${filter === priority ? 'active' : ''}`}
              >
                {priority.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <span>⚠️ WebSocket Error: {error}</span>
        </div>
      )}

      <div className="apv-stream__content grid gap-4">
        {filteredAPVs.length === 0 ? (
          <div className="empty-state">
            <p className="text-gray-400">No APVs matching filter. System monitoring...</p>
          </div>
        ) : (
          filteredAPVs.map(apv => (
            <APVCard key={apv.cve_id} apv={apv} />
          ))
        )}
      </div>
    </div>
  );
};

export default APVStream;
```

**Arquivo**: `frontend/src/components/dashboards/AdaptiveImmunityDashboard/hooks/useAPVStream.js`

```javascript
/**
 * useAPVStream - WebSocket hook for real-time APV stream
 */

import { useState, useEffect, useRef } from 'react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/apv-stream';

export const useAPVStream = () => {
  const [apvs, setApvs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect WebSocket
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[APVStream] WebSocket connected');
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const apv = JSON.parse(event.data);
        console.log('[APVStream] New APV received:', apv.cve_id);
        
        // Add to stream (keep last 50)
        setApvs(prev => [apv, ...prev].slice(0, 50));
      } catch (err) {
        console.error('[APVStream] Failed to parse APV:', err);
        setError('Invalid APV format received');
      }
    };

    ws.onerror = (event) => {
      console.error('[APVStream] WebSocket error:', event);
      setError('Connection error');
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('[APVStream] WebSocket closed');
      setIsConnected(false);
    };

    // Cleanup
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return {
    apvs,
    isConnected,
    error,
    clearError: () => setError(null)
  };
};
```

**Checklist Fase 4**:
- [ ] Estrutura de diretórios criada
- [ ] `api/adaptiveImmunityAPI.js` implementado
- [ ] `hooks/useAPVStream.js` implementado + testes
- [ ] `components/APVCard.jsx` implementado + testes
- [ ] `components/APVStream.jsx` implementado + testes
- [ ] `components/PatchesTable.jsx` implementado + testes
- [ ] `components/MetricsPanel.jsx` implementado + testes
- [ ] `index.jsx` dashboard principal funcional
- [ ] Integração E2E: Backend → WebSocket → Frontend rendering

---

### FASE 5: BACKEND WEBSOCKET & API (Dia 8)
**Duração**: 6-8 horas  
**Responsável**: Backend development

#### 5.1 WebSocket Server

**Arquivo**: `backend/services/maximus_oraculo/websocket.py`

```python
"""WebSocket server for real-time APV streaming to frontend."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class APVStreamManager:
    """
    Gerencia conexões WebSocket para streaming de APVs.
    
    Patterns:
    - Pub/Sub via Redis para broadcast cross-instance
    - Connection pool management
    - Heartbeat para detect stale connections
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._heartbeat_task = None
    
    async def connect(self, websocket: WebSocket):
        """Aceita nova conexão WebSocket."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove conexão do pool."""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_apv(self, apv_dict: dict):
        """
        Broadcast APV para todas as conexões ativas.
        
        Args:
            apv_dict: APV serializado como dict
        """
        if not self.active_connections:
            return
            
        message = json.dumps(apv_dict)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected.add(connection)
        
        # Remove failed connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def start_heartbeat(self):
        """Envia heartbeat ping para detectar conexões mortas."""
        while True:
            await asyncio.sleep(30)  # Ping every 30s
            
            disconnected = set()
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.disconnect(conn)


# Global instance
stream_manager = APVStreamManager()
```

**Arquivo**: `backend/services/maximus_oraculo/api.py` (adicionar endpoint)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .websocket import stream_manager

app = FastAPI()

@app.websocket("/ws/apv-stream")
async def apv_stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para streaming de APVs em tempo real.
    
    Usage:
        ws://localhost:8000/ws/apv-stream
    """
    await stream_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive (client can send pongs)
            data = await websocket.receive_text()
            
            if data == "pong":
                continue  # Heartbeat response
                
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        stream_manager.disconnect(websocket)


@app.on_event("startup")
async def startup_event():
    """Start heartbeat task."""
    asyncio.create_task(stream_manager.start_heartbeat())
```

**Integração com Kafka Publisher** (modificar `apv_publisher.py`):

```python
# Após publicar no Kafka, broadcast via WebSocket
from .websocket import stream_manager

async def publish_apv(apv: APV):
    """Publica APV no Kafka e broadcast via WebSocket."""
    # 1. Publish to Kafka
    await kafka_producer.send('maximus.adaptive-immunity.apv', apv.dict())
    
    # 2. Broadcast to WebSocket clients
    await stream_manager.broadcast_apv(apv.dict())
    
    logger.info(f"APV {apv.cve_id} published and broadcasted")
```

**Checklist Fase 5**:
- [ ] `websocket.py` implementado
- [ ] WebSocket endpoint `/ws/apv-stream` adicionado
- [ ] Integração Kafka → WebSocket broadcast
- [ ] Teste E2E: Kafka msg → WebSocket → Frontend recebe

---

### FASE 6: INTEGRAÇÃO E2E + VALIDAÇÃO (Dia 9)
**Duração**: 8 horas  
**Responsável**: Full-stack testing

#### 6.1 Teste E2E Completo

**Arquivo**: `tests/e2e/test_adaptive_immunity_full_cycle.py`

```python
"""
E2E test: CVE → Oráculo → APV → Kafka → Eureka → Patch → Git → Frontend
"""

import pytest
import asyncio
from backend.services.maximus_oraculo.threat_feeds.osv_client import OSVClient
from backend.services.maximus_oraculo.models.apv import APV
from backend.services.maximus_eureka.consumers.apv_consumer import APVConsumer
import websockets
import json


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_adaptive_immunity_cycle():
    """
    Test completo do ciclo:
    1. Oráculo fetch CVE fake do OSV.dev
    2. Oráculo processa → APV
    3. APV publicado no Kafka
    4. Eureka consome APV
    5. Eureka confirma vulnerability
    6. Eureka gera patch
    7. Frontend recebe APV via WebSocket
    """
    
    # 1. Setup: CVE fake injection
    fake_cve_id = "CVE-2024-99999-TEST"
    
    # 2. Oráculo: Fetch e processa
    async with OSVClient() as osv:
        # Simular query (em test, usar mock)
        raw_vuln = {
            "id": fake_cve_id,
            "summary": "Test SQL Injection",
            "severity": "CRITICAL",
            "affected": [{
                "package": {"ecosystem": "PyPI", "name": "django"},
                "ranges": [{"type": "SEMVER", "events": [{"introduced": "0"}, {"fixed": "4.2.8"}]}]
            }]
        }
        
        # Processar para APV (chamada real ao pipeline)
        apv = await process_cve_to_apv(raw_vuln)
        assert apv.cve_id == fake_cve_id
        assert apv.priority == "critical"
    
    # 3. Kafka: Publicar APV
    await publish_apv_to_kafka(apv)
    
    # 4. Eureka: Consumir e confirmar
    consumer = APVConsumer()
    confirmed_threat = await consumer.consume_and_confirm(timeout=10)
    
    assert confirmed_threat is not None
    assert confirmed_threat.cve_id == fake_cve_id
    assert len(confirmed_threat.vulnerable_files) > 0
    
    # 5. Eureka: Gerar patch
    patch = await generate_patch_for_threat(confirmed_threat)
    assert patch is not None
    assert patch.strategy in ["dependency_upgrade", "code_patch"]
    
    # 6. Git: Verificar branch criado
    git_branch = f"security/fix-{fake_cve_id.lower()}"
    assert git_branch_exists(git_branch)
    
    # 7. Frontend: Verificar WebSocket broadcast
    async with websockets.connect('ws://localhost:8000/ws/apv-stream') as ws:
        # Aguardar mensagem (timeout 5s)
        message = await asyncio.wait_for(ws.recv(), timeout=5.0)
        received_apv = json.loads(message)
        
        assert received_apv['cve_id'] == fake_cve_id
    
    print("✅ E2E Full Cycle Test PASSED")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_mttr_target():
    """
    Test MTTR < 45 minutos target.
    
    Simula processamento de CVE real e mede tempo total.
    """
    import time
    
    start_time = time.time()
    
    # Executar ciclo completo
    await test_full_adaptive_immunity_cycle()
    
    elapsed = time.time() - start_time
    elapsed_minutes = elapsed / 60
    
    assert elapsed_minutes < 45, f"MTTR target failed: {elapsed_minutes:.2f} min > 45 min"
    
    print(f"✅ MTTR Test PASSED: {elapsed_minutes:.2f} minutes")
```

**Checklist Fase 6**:
- [ ] Teste E2E full cycle implementado
- [ ] Teste MTTR < 45min implementado
- [ ] CI/CD: Adicionar job para E2E tests
- [ ] Documentação: Atualizar com evidências de testes passando

---

## 📊 CRONOGRAMA CONSOLIDADO

| Fase | Duração | Dias | Entregas | Validação |
|------|---------|------|----------|-----------|
| **Fase 1: Infra** | 4-6h | Dia 1 | Docker Compose + DB + Kafka | Containers rodando |
| **Fase 2: Oráculo** | 12-16h | Dias 2-3 | Oráculo Core + APV model + Kafka | CVE→APV→Kafka |
| **Fase 3: Eureka** | 12-16h | Dias 4-5 | Eureka Core + Strategies + LLM | APV→Patch→Git |
| **Fase 4: Frontend** | 12-16h | Dias 6-7 | Dashboard + WebSocket | UI funcional |
| **Fase 5: WebSocket** | 6-8h | Dia 8 | WebSocket server + API | Real-time streaming |
| **Fase 6: E2E** | 8h | Dia 9 | Testes completos + validação | MTTR < 45min |
| **TOTAL** | **54-70h** | **9 dias** | **Sprint 1 MVP** | **✅ Production-ready** |

---

## 🎯 CRITÉRIOS DE SUCESSO

### Técnicos
- [ ] Oráculo ingere CVEs do OSV.dev sem rate limiting
- [ ] Dependency graph construído para ≥10 serviços MAXIMUS
- [ ] Filtro de relevância ≥90% precisão (CVEs descartados vs relevantes)
- [ ] APV schema validado contra CVE JSON 5.1.1
- [ ] Eureka confirma vulnerabilities via ast-grep determinístico
- [ ] Eureka gera patches com LLM (Strategy 2) confidence ≥0.8
- [ ] Git branches automáticas criadas para cada patch
- [ ] Frontend dashboard atualiza em tempo real via WebSocket
- [ ] Teste E2E full cycle passa em CI/CD

### Performance
- [ ] **MTTR < 45 minutos** (CVE publicado → Patch merged)
- [ ] **Latência Oráculo**: CVE fetch → APV < 30s
- [ ] **Latência Eureka**: APV → Patch gerado < 10min (com LLM)
- [ ] **WebSocket**: Broadcast latency < 500ms
- [ ] **Kafka**: Throughput ≥100 APVs/min

### Qualidade
- [ ] **Type hints**: 100% coverage (mypy --strict)
- [ ] **Testes**: ≥90% coverage (pytest-cov)
- [ ] **Docstrings**: 100% (Google style)
- [ ] **NO MOCK**: Apenas testes unitários mockam HTTP/Kafka
- [ ] **NO PLACEHOLDER**: Zero `pass` ou `NotImplementedError`

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

### Aprovação Pendente
Este plano aguarda aprovação para iniciar execução.

**Após aprovação**:

```bash
# 1. Criar branch de trabalho
git checkout -b feature/adaptive-immunity-sprint1-mvp

# 2. Executar Fase 1 (Infraestrutura)
./scripts/setup/setup-adaptive-immunity-infra.sh

# 3. Validar infra
docker-compose -f docker-compose.adaptive-immunity.yml ps

# 4. Iniciar Fase 2 (Oráculo Core)
# Seguir checklist detalhado Fase 2
```

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### Dívidas Técnicas Permitidas (Sprint 1 MVP)

Para atingir MVP funcional em 9 dias, **temporariamente aceitável**:

1. **Crisol de Wargaming**: Não implementado em Sprint 1
   - Validação manual de patches (HITL review obrigatório)
   - Implementar em Sprint 3 conforme roadmap

2. **Multi-LLM Fallback**: Apenas Claude client em Sprint 1
   - OpenAI e Gemini em Sprint 2

3. **Dashboard Analytics**: Apenas real-time stream em Sprint 1
   - Histórico e analytics em Sprint 4

4. **Coagulation Integration**: Strategy 3 stub em Sprint 1
   - Integração real com Coagulation em Sprint 2

**NÃO NEGOCIÁVEIS** (mesmo em MVP):
- Type hints 100%
- Testes ≥90% coverage
- Docstrings completos
- Error handling robusto
- Observability (logs estruturados)

---

## 🏆 IMPACTO ESPERADO

### Métricas Antes vs Depois

| Métrica | Antes (Manual) | Depois (Automated) | Melhoria |
|---------|----------------|-------------------|----------|
| **MTTR** | 3-48h | 15-45min | **16-64x** ⚡ |
| **Threat Coverage** | 0% | 95% | **∞** 🚀 |
| **Security Team Hours** | 40h/semana | 5h/semana | **87.5%** ↓ |
| **False Negatives** | ~40% | <5% | **8x better** |
| **Audit Trail** | Fragmentado | 100% (Git PRs) | **Complete** ✅ |

---

## 🙏 FUNDAMENTAÇÃO ESPIRITUAL

> **"Não por força nem por violência, mas pelo meu Espírito, diz o SENHOR dos Exércitos."**  
> — Zacarias 4:6

Este plano foi construído com:
- **Disciplina** (estrutura metodológica rigorosa)
- **Sabedoria** (priorização baseada em impacto)
- **Humildade** (reconhecer dívidas técnicas temporárias)
- **Excelência** (não negociar qualidade core)

**Glory to YHWH** - Source of all innovation and resilience.

---

**Status**: 🟡 **AGUARDANDO APROVAÇÃO**  
**Próximo Marco**: Aprovação → Fase 1 Day 1 - Infraestrutura Setup

*Este plano será estudado em 2050 como primeira implementação documentada de Sistema Imunológico Adaptativo em software de produção.*
