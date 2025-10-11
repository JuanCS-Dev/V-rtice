# 🚀 SPRINT 2: REMEDIAÇÃO EUREKA - Plano de Implementação

**Data Início**: 2025-10-11  
**Timeline**: 10 dias úteis (2 semanas)  
**Status**: 🟢 **EM EXECUÇÃO**  
**Branch**: `feature/sprint-2-remediation-eureka`

---

## 📊 ANÁLISE DE STATUS ATUAL

### ✅ Já Implementado (Sprint 1)

**Backend Base**:
- ✅ DependencyUpgradeStrategy (base implementation)
- ✅ CodePatchLLMStrategy (base implementation)
- ✅ Git Integration (GitOperations, PRCreator, SafetyChecks)
- ✅ LLM Clients (ClaudeClient, base prompts)
- ✅ 103/104 tests passing (99%)

**Estrutura**:
```
backend/services/maximus_eureka/
├── strategies/
│   ├── base_strategy.py           ✅
│   ├── dependency_upgrade.py      ✅
│   ├── code_patch_llm.py          ✅
│   └── strategy_selector.py       ✅
├── git_integration/
│   ├── git_operations.py          ✅
│   ├── pr_creator.py              ✅
│   └── safety_checks.py           ✅
├── llm/
│   ├── base_client.py             ✅
│   ├── claude_client.py           ✅
│   └── prompt_templates.py        ✅
└── tests/                         ✅ 103 passing
```

---

## 🎯 ENTREGÁVEIS SPRINT 2 (NOVOS)

### 1. LLM Breaking Changes Analyzer ⏳

**Objetivo**: Analisar diffs de versões e detectar breaking changes.

**Implementação**:
```python
# backend/services/maximus_eureka/llm/breaking_changes_analyzer.py

class BreakingChangesAnalyzer:
    """
    Analyze version diffs to detect breaking changes using LLM.
    
    Uses Gemini 2.5 Pro (cost-effective) to analyze:
    - API signature changes
    - Behavior modifications
    - Deprecations
    - Required migrations
    """
    
    async def analyze_diff(
        self,
        package: str,
        from_version: str,
        to_version: str,
        diff_content: str
    ) -> BreakingChangesReport:
        """Analyze diff and generate report"""
```

**Tasks**:
- [ ] Criar `breaking_changes_analyzer.py`
- [ ] Implementar prompts para análise de diff
- [ ] Integrar com Gemini 2.5 Pro API
- [ ] Estruturar `BreakingChangesReport` model
- [ ] Unit tests (≥90% coverage)
- [ ] Integration test com diff real

**Estimativa**: 4 horas

---

### 2. Few-Shot Database Setup ⏳

**Objetivo**: Database SQLite com exemplos de fixes para few-shot learning.

**Schema**:
```sql
CREATE TABLE vulnerability_fixes (
    id INTEGER PRIMARY KEY,
    cwe_id TEXT NOT NULL,
    cve_id TEXT,
    language TEXT NOT NULL,
    vulnerable_code TEXT NOT NULL,
    fixed_code TEXT NOT NULL,
    explanation TEXT NOT NULL,
    difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cwe ON vulnerability_fixes(cwe_id);
CREATE INDEX idx_language ON vulnerability_fixes(language);
```

**Seeding Inicial** (50+ exemplos):
```python
# Exemplo 1: CWE-295 (TLS Certificate Validation)
{
    "cwe_id": "CWE-295",
    "language": "python",
    "vulnerable_code": "requests.get(url, verify=False)",
    "fixed_code": "requests.get(url, verify=True)",
    "explanation": "Enable TLS certificate validation to prevent MITM attacks",
    "difficulty": "easy"
}

# Exemplo 2: CWE-89 (SQL Injection)
{
    "cwe_id": "CWE-89",
    "language": "python",
    "vulnerable_code": "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
    "fixed_code": "cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))",
    "explanation": "Use parameterized queries to prevent SQL injection",
    "difficulty": "easy"
}

# ... 48+ more examples
```

**Tasks**:
- [ ] Criar database schema (`data/few_shot_examples.db`)
- [ ] Implementar `FewShotDatabase` manager
- [ ] Curar 50+ exemplos (CWE top 25)
- [ ] Script de seeding
- [ ] Query interface (get_examples_by_cwe)
- [ ] Unit tests

**Estimativa**: 6 horas (curation = 3h, implementação = 3h)

---

### 3. Coagulation Integration (WAF Rules) ⏳

**Objetivo**: Criar regras WAF temporárias enquanto patch está em andamento.

**Implementação**:
```python
# backend/services/maximus_eureka/integrations/coagulation_client.py

class CoagulationClient:
    """
    Create temporary WAF rules via RTE service.
    
    Integrates with RTE Service (port 8002) to deploy firewall rules
    that block attack vectors while patch is being validated.
    
    Rules auto-expire after 24h or PR merge (whichever comes first).
    """
    
    async def create_temporary_rule(
        self,
        apv: APV,
        attack_vector: str,
        duration: timedelta = timedelta(hours=24)
    ) -> CoagulationRule:
        """
        Generate and deploy WAF rule.
        
        Example vectors:
        - SQL Injection: Block patterns like ' OR '1'='1
        - XSS: Block <script> tags
        - Path Traversal: Block ../ patterns
        - Command Injection: Block shell metacharacters
        """
```

**Attack Vector Templates**:
```python
TEMPLATES = {
    "CWE-89": {  # SQL Injection
        "pattern": r"(\bOR\b|\bAND\b|--|;|'|\"|\/\*|\*\/)",
        "action": "block",
        "message": "Potential SQL injection blocked"
    },
    "CWE-79": {  # XSS
        "pattern": r"<script|javascript:|onerror=|onload=",
        "action": "block",
        "message": "Potential XSS attack blocked"
    },
    "CWE-78": {  # Command Injection
        "pattern": r"[;&|`$()]",
        "action": "block",
        "message": "Potential command injection blocked"
    },
    # ... more templates
}
```

**RTE Integration**:
```python
# POST to RTE service
async def deploy_rule(self, rule: Dict) -> str:
    """Deploy rule to RTE service"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://rte-service:8002/api/v1/rules",
            json={
                "pattern": rule["pattern"],
                "action": rule["action"],
                "ttl_seconds": rule["ttl"],
                "source": "maximus_eureka",
                "metadata": {
                    "apv_id": rule["apv_id"],
                    "cve_id": rule["cve_id"]
                }
            }
        )
        return response.json()["rule_id"]
```

**Tasks**:
- [ ] Criar `integrations/coagulation_client.py`
- [ ] Implementar templates para CWE Top 10
- [ ] RTE API client (httpx)
- [ ] TTL management (auto-expire)
- [ ] Metrics (rules_created, rules_expired)
- [ ] Unit tests (mock RTE)
- [ ] Integration test (real RTE)

**Estimativa**: 5 horas

---

### 4. LLM Cost Tracking ⏳

**Objetivo**: Monitorar custos de LLM por patch para budget control.

**Implementação**:
```python
# backend/services/maximus_eureka/tracking/llm_cost_tracker.py

class LLMCostTracker:
    """
    Track LLM API costs per patch generation.
    
    Monitors:
    - Token usage (input/output)
    - Model pricing (Claude/GPT-4/Gemini)
    - Cost per patch
    - Monthly budget alerts
    
    Metrics exported to Prometheus:
    - llm_tokens_total{model, type}
    - llm_cost_usd_total{model}
    - llm_cost_per_patch_usd{strategy}
    """
    
    # Pricing (as of 2025-10)
    PRICING = {
        "claude-3-7-sonnet": {"input": 0.003, "output": 0.015},  # per 1K tokens
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gemini-2-5-pro": {"input": 0.00125, "output": 0.005}
    }
    
    async def track_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Dict
    ) -> CostRecord:
        """Record LLM usage and calculate cost"""
```

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'type']  # type = input/output
)

llm_cost_usd_total = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['model']
)

llm_cost_per_patch_usd = Histogram(
    'llm_cost_per_patch_usd',
    'Cost per patch generation',
    ['strategy'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)
```

**Budget Alerts**:
```python
async def check_budget(self):
    """Check if monthly budget exceeded"""
    monthly_cost = await self.get_monthly_cost()
    
    if monthly_cost > BUDGET_WARNING_THRESHOLD:
        await self.send_alert(
            level="warning",
            message=f"LLM cost ${monthly_cost:.2f} exceeds warning threshold"
        )
    
    if monthly_cost > BUDGET_HARD_LIMIT:
        await self.send_alert(
            level="critical",
            message=f"LLM cost ${monthly_cost:.2f} exceeds hard limit! Throttling."
        )
        await self.enable_throttling()
```

**Tasks**:
- [ ] Criar `tracking/llm_cost_tracker.py`
- [ ] Implementar cost calculation (tokens → USD)
- [ ] Prometheus metrics export
- [ ] Budget alert system (Slack/email)
- [ ] Monthly report generator
- [ ] Unit tests
- [ ] Dashboard Grafana (cost over time)

**Estimativa**: 4 horas

---

### 5. Enhanced Integration & E2E Tests ⏳

**Objetivo**: Testes end-to-end completos para Sprint 2.

**Cenários**:
```python
# tests/integration/test_sprint2_e2e.py

async def test_e2e_dependency_upgrade_with_breaking_changes():
    """
    E2E: CVE → Dependency Upgrade → Breaking Changes Analysis → PR
    
    Flow:
    1. APV com fix disponível (requests 2.28.0 → 2.31.0)
    2. DependencyUpgradeStrategy triggered
    3. Breaking changes analyzer consulta LLM
    4. Patch gerado com migration guide
    5. Git branch criado
    6. PR criado com breaking changes doc
    """
    
async def test_e2e_code_patch_llm_with_few_shot():
    """
    E2E: CVE → Code Patch LLM → Few-shot Examples → PR
    
    Flow:
    1. APV sem fix disponível (zero-day)
    2. CodePatchLLMStrategy triggered
    3. Few-shot examples recuperados (CWE match)
    4. LLM gera patch com context
    5. Syntax validation (ast.parse)
    6. Git branch criado
    7. PR criado com confidence score
    """

async def test_e2e_coagulation_waf_rule():
    """
    E2E: CVE → Coagulation Rule → Temporary WAF → Auto-Expire
    
    Flow:
    1. APV com attack vector (SQL Injection)
    2. CoagulationClient triggered
    3. WAF rule gerado (block SQL patterns)
    4. Rule deployed to RTE
    5. Monitoring: rule_active=true
    6. Wait 24h OR PR merge
    7. Rule auto-expires
    8. Monitoring: rule_active=false
    """

async def test_e2e_llm_cost_tracking():
    """
    E2E: Patch Generation → Cost Tracking → Budget Alert
    
    Flow:
    1. 20 patches gerados (mix strategies)
    2. Cost tracker records all requests
    3. Total cost calculated: $15.80
    4. Metrics exported to Prometheus
    5. Monthly cost dashboard updated
    6. No budget alert (under $50 threshold)
    """
```

**Tasks**:
- [ ] Implementar 4 cenários E2E
- [ ] Mock external services (LLM, RTE, GitHub)
- [ ] Fixtures para CVEs variados
- [ ] Assertions completas (patch quality, cost, timing)
- [ ] CI integration (run on PR)

**Estimativa**: 6 horas

---

## 📅 CRONOGRAMA DETALHADO

### Semana 1 (Dias 1-5)

**Dia 1-2: Breaking Changes Analyzer + Few-Shot DB**
- [ ] Implementar `breaking_changes_analyzer.py` (4h)
- [ ] Setup few-shot database (3h)
- [ ] Curar 50+ exemplos (3h)
- [ ] Unit tests (2h)

**Dia 3-4: Coagulation Integration**
- [ ] Implementar `coagulation_client.py` (3h)
- [ ] Templates WAF (CWE Top 10) (2h)
- [ ] RTE integration (2h)
- [ ] Unit + Integration tests (2h)

**Dia 5: LLM Cost Tracking**
- [ ] Implementar `llm_cost_tracker.py` (3h)
- [ ] Prometheus metrics (1h)
- [ ] Budget alerts (1h)
- [ ] Unit tests (1h)

### Semana 2 (Dias 6-10)

**Dia 6-8: E2E Tests**
- [ ] Cenário 1: Dependency Upgrade (2h)
- [ ] Cenário 2: Code Patch LLM (2h)
- [ ] Cenário 3: Coagulation (2h)
- [ ] Cenário 4: Cost Tracking (1h)
- [ ] CI integration (1h)

**Dia 9: Integration & Bug Fixes**
- [ ] Integrar componentes novos (3h)
- [ ] Fix bugs descobertos em testes (3h)
- [ ] Ajustes de performance (2h)

**Dia 10: Documentation & Validation**
- [ ] API documentation (Swagger) (2h)
- [ ] Runbook operacional (2h)
- [ ] Final validation (2h)
- [ ] Sprint 2 report (2h)

---

## 🎯 CRITÉRIOS DE SUCESSO

### Técnicos
- [ ] Breaking changes analyzer functional (accuracy ≥80%)
- [ ] Few-shot database ≥50 exemplos (CWE Top 25)
- [ ] Coagulation rules ≥3 attack vectors (SQL, XSS, RCE)
- [ ] LLM cost tracking operational (<$1/patch average)
- [ ] All unit tests passing (coverage ≥85%)
- [ ] 4 E2E scenarios passing

### Funcionais
- [ ] Dependency upgrade com breaking changes analysis
- [ ] Code patch LLM usa few-shot examples
- [ ] WAF rules deployed automaticamente
- [ ] Cost metrics visíveis em Grafana

### Performance
- [ ] Breaking changes analysis <30s (p95)
- [ ] Few-shot query <100ms
- [ ] Coagulation rule deployment <5s
- [ ] Cost calculation <10ms

---

## 🛠️ SETUP INICIAL

### 1. Branch Setup
```bash
cd /home/juan/vertice-dev
git checkout feature/sprint-2-remediation-eureka
git pull origin main  # Merge latest changes
```

### 2. Estrutura de Diretórios
```bash
cd backend/services/maximus_eureka

# Criar diretórios novos
mkdir -p llm/breaking_changes
mkdir -p data/few_shot_examples
mkdir -p integrations
mkdir -p tracking
mkdir -p tests/integration/sprint2

# Criar arquivos iniciais
touch llm/breaking_changes_analyzer.py
touch data/few_shot_database.py
touch integrations/coagulation_client.py
touch tracking/llm_cost_tracker.py
```

### 3. Dependencies
```bash
# Adicionar ao pyproject.toml
poetry add google-generativeai  # Gemini API
poetry add httpx                # Async HTTP
poetry add prometheus-client    # Metrics
```

### 4. Environment Variables
```bash
# .env
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
RTE_SERVICE_URL=http://rte-service:8002
LLM_BUDGET_MONTHLY=50.00  # USD
```

---

## 📊 MÉTRICAS DE PROGRESSO

### Daily Checklist

**Dia 1** ⏳:
- [ ] Breaking changes analyzer skeleton
- [ ] Gemini API integration
- [ ] Few-shot database schema

**Dia 2** ⏳:
- [ ] Few-shot seeding script (50+ examples)
- [ ] Breaking changes prompts
- [ ] Unit tests analyzer

**Dia 3** ⏳:
- [ ] Coagulation client skeleton
- [ ] WAF templates (SQL, XSS, RCE)
- [ ] RTE API client

**Dia 4** ⏳:
- [ ] Coagulation TTL management
- [ ] Integration test (mock RTE)
- [ ] Unit tests coagulation

**Dia 5** ⏳:
- [ ] LLM cost tracker implementation
- [ ] Prometheus metrics
- [ ] Budget alerts

**Dia 6-8** ⏳:
- [ ] 4 E2E scenarios
- [ ] CI integration

**Dia 9** ⏳:
- [ ] Integration final
- [ ] Bug fixes

**Dia 10** ⏳:
- [ ] Documentation
- [ ] Sprint 2 complete report

---

## 🚀 PRIMEIRO PASSO

```bash
# 1. Validar ambiente
cd /home/juan/vertice-dev/backend/services/maximus_eureka
pytest tests/ -v  # Confirmar 103/104 passing

# 2. Criar estrutura Sprint 2
mkdir -p llm/breaking_changes data integrations tracking tests/integration/sprint2

# 3. Iniciar Breaking Changes Analyzer
touch llm/breaking_changes_analyzer.py

# 4. Configurar API keys
echo "Configurar GEMINI_API_KEY no .env"
```

---

**Status**: 🟢 PRONTO PARA EXECUÇÃO  
**Primeira Task**: Implementar Breaking Changes Analyzer  
**Estimativa Total**: 40-50 horas (2 semanas)

🤖 _"Sprint 2 Day 1 - Building intelligent remediation. Glory to YHWH."_
