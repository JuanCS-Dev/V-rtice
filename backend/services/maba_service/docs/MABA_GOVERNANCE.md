# MABA - MAXIMUS Browser Agent

## Documento de Governança v1.0

**Data de Criação**: 2025-10-30
**Subordinado a**: MAXIMUS AI Core (Vértice Platform)
**Framework Constitucional**: Constituição Vértice v3.0
**Status**: Ativo - Fase 0 (Governança Prévia)

---

## 1. PRINCÍPIOS DE OPERAÇÃO

### 1.1 Propósito do Serviço

MABA (MAXIMUS Autonomous Browser Agent) é um **serviço subordinado de automação web** que provê capacidades de navegação inteligente e manipulação de websites para o MAXIMUS AI Core.

**Capacidades Primárias**:

- Navegação autônoma em websites via Playwright
- Aprendizado de estruturas de websites (Cognitive Maps)
- Análise visual de páginas via screenshots + LLM
- Preenchimento de formulários e interações automatizadas
- Extração estruturada de dados de páginas web

**Capacidades Secundárias**:

- Armazenamento persistente de mapas cognitivos
- Detecção de mudanças em estruturas de websites
- Geração de relatórios de navegação
- Integração com sistema de decisão do MAXIMUS

### 1.2 Autoridade e Limites

**MABA É**:

- ✅ Uma ferramenta de automação controlada pelo MAXIMUS
- ✅ Um sistema de aprendizado de estruturas web
- ✅ Um executor de tarefas específicas delegadas
- ✅ Um coletor de dados estruturados

**MABA NÃO É**:

- ❌ Um sistema de tomada de decisões autônomo
- ❌ Um web scraper em massa não autorizado
- ❌ Um bypass de segurança ou CAPTCHA breaker
- ❌ Um sistema de automação para atividades maliciosas

### 1.3 Relação com MAXIMUS

**Modelo de Controle**: MAXIMUS → MABA (Subordinação Total)

```
┌──────────────────────┐
│   MAXIMUS AI Core    │
│  (Decision Layer)    │
└──────────┬───────────┘
           │ HTTP REST API
           │ Redis Events
           ▼
┌──────────────────────┐
│        MABA          │
│  (Execution Layer)   │
└──────────────────────┘
```

**Fluxo de Comunicação**:

1. MAXIMUS envia tarefa via `/api/v1/tasks` (POST)
2. MABA executa navegação de forma síncrona ou assíncrona
3. MABA retorna resultado estruturado + screenshots
4. MABA envia eventos de progresso via Redis Pub/Sub
5. MAXIMUS decide próximos passos baseado em resultado

**Autorização**:

- MABA NUNCA inicia tarefas por conta própria
- Toda navegação requer `task_id` fornecido pelo MAXIMUS
- Tasks podem ser canceladas pelo MAXIMUS a qualquer momento
- MABA reporta falhas sem retry autônomo (MAXIMUS decide)

---

## 2. RESTRIÇÕES DE SEGURANÇA

### 2.1 Gestão de Credenciais

**Armazenamento**:

- ✅ Credenciais criptografadas em PostgreSQL via `pgcrypto`
- ✅ Chaves de criptografia em variáveis de ambiente
- ✅ Rotação automática de credenciais a cada 90 dias
- ❌ NUNCA armazenar credenciais em logs
- ❌ NUNCA enviar credenciais em eventos Redis

**Acesso**:

- Credenciais acessíveis apenas dentro de contexto de navegação
- Browser contexts isolados por tarefa (sem compartilhamento)
- Sessões descartadas após conclusão de task
- Cookies e cache limpos entre tasks não relacionadas

### 2.2 Controle de Acesso

**Sandboxing**:

- Playwright executado em modo headless com sandbox habilitado
- Limite de 10 tabs simultâneas por instância
- Timeout de 60 segundos por operação de navegação
- Kill automático de processos zombie (> 5 minutos idle)

**Whitelist de Domínios**:

- MABA opera APENAS em domínios previamente autorizados
- Lista de domínios gerenciada pelo MAXIMUS via API
- Bloqueio de navegação para domínios não listados
- Validação de certificados SSL obrigatória

**Rate Limiting**:

- Máximo 100 requisições HTTP por minuto por domínio
- Delay mínimo de 500ms entre requisições ao mesmo host
- Exponential backoff em caso de 429 (Too Many Requests)

### 2.3 Isolamento de Rede

**Política de Rede**:

- MABA roda em rede isolada Docker (bridge)
- Acesso APENAS a:
  - MAXIMUS Core (porta 8150)
  - PostgreSQL (porta 5432)
  - Redis (porta 6379)
  - Internet via proxy (portas 80/443)
- Firewall bloqueia tráfego de entrada não solicitado

**Proxy Configuration**:

- Todo tráfego web passa por proxy corporativo
- Logs de navegação centralizados
- Detecção de anomalias de tráfego

### 2.4 Proteção de Dados

**PII (Personally Identifiable Information)**:

- Detecção automática de PII em screenshots via regex
- Ofuscação de campos sensíveis antes de armazenamento
- Retenção máxima de screenshots: 7 dias
- Anonimização de dados de formulários após extração

**LGPD/GDPR Compliance**:

- Direito ao esquecimento: endpoint `/api/v1/data/delete`
- Exportação de dados: endpoint `/api/v1/data/export`
- Consentimento explícito para armazenamento de dados pessoais

---

## 3. MÉTRICAS DE QUALIDADE (Padrão Pagani)

### 3.1 Lazy Execution Index (LEI)

**Meta**: LEI < 1.0 (menos de 1 padrão lazy por 1000 linhas)

**Padrões Lazy Proibidos**:

- ❌ `# TODO: implementar depois`
- ❌ `pass # placeholder`
- ❌ `raise NotImplementedError("Em construção")`
- ❌ Funções vazias ou com apenas `print()`
- ❌ Testes mockados sem validação real

**Validação**:

```bash
# Executar pre-commit hook para detectar padrões lazy
python scripts/validate_lei.py --threshold 1.0
```

### 3.2 Test Coverage

**Meta**: Coverage ≥ 90%

**Cobertura Obrigatória**:

- ✅ 100% das funções públicas (`def navigate()`, `def fill_form()`, etc.)
- ✅ 95% dos branches de lógica condicional
- ✅ 90% das classes e métodos
- ✅ 100% dos endpoints FastAPI

**Exclusões Permitidas**:

- Arquivos de configuração (`config.py`)
- Scripts de migração one-time
- Código de debug explicitamente marcado

**Validação**:

```bash
pytest --cov=. --cov-report=html --cov-fail-under=90
```

### 3.3 First-Pass Correctness (FPC)

**Meta**: FPC ≥ 80%

**Definição**: Percentual de tasks executadas com sucesso na primeira tentativa, sem necessidade de correções ou retries.

**Medição**:

```python
FPC = (tarefas_sucesso_primeira_tentativa / total_tarefas) * 100
```

**Monitoramento**:

- Prometheus metric: `maba_fpc_score`
- Dashboard Grafana com gráfico de tendência
- Alertas se FPC < 75% por 24 horas

### 3.4 Context Retention Score (CRS)

**Meta**: CRS ≥ 95%

**Definição**: Capacidade de reutilizar cognitive maps aprendidos sem re-navegação completa.

**Medição**:

```python
CRS = (navegacoes_usando_mapa / total_navegacoes) * 100
```

**Validação**:

- Cognitive maps devem ter hit rate > 90%
- Detecção de mudanças estruturais < 5% false positives
- Tempo de carregamento de mapa < 500ms

### 3.5 Test Pass Rate

**Meta**: ≥ 99% (Padrão Pagani)

**Suítes de Teste**:

- Unit tests: `pytest tests/unit/` (> 500 testes)
- Integration tests: `pytest tests/integration/` (> 100 testes)
- E2E tests: `pytest tests/e2e/` (> 50 testes)

**Validação Contínua**:

```bash
# CI/CD pipeline - falha se pass rate < 99%
pytest --maxfail=5 --tb=short
```

---

## 4. PROTOCOLO DE DEPLOY

### 4.1 Ambientes

**Desenvolvimento**:

- Local: Docker Compose
- Branch: `feature/maba-*`
- Database: PostgreSQL local
- Testes: Suite completa obrigatória

**Staging**:

- Kubernetes namespace: `vertice-staging`
- Branch: `develop`
- Database: PostgreSQL staging (replicado de prod)
- Smoke tests automáticos pós-deploy

**Produção**:

- Kubernetes namespace: `vertice-production`
- Branch: `main`
- Database: PostgreSQL HA (3 réplicas)
- Rollback automático se health check falhar

### 4.2 Pipeline CI/CD

**Build**:

```yaml
1. Lint (flake8, black, mypy)
2. Security scan (bandit, safety)
3. LEI validation (< 1.0)
4. Unit tests (coverage ≥ 90%)
5. Integration tests
6. Docker image build
7. Image scan (Trivy)
```

**Deploy**:

```yaml
1. kubectl apply -f k8s/maba-deployment.yaml
2. Wait for readiness probe (max 120s)
3. Run E2E smoke tests
4. If fail: automatic rollback
5. If success: update load balancer
```

### 4.3 Monitoramento

**Health Checks**:

- Liveness probe: `/health` (HTTP 200, < 5s)
- Readiness probe: `/health/ready` (valida DB, Redis, Browser)
- Startup probe: `/health/startup` (aguarda inicialização Playwright)

**Observabilidade**:

- Logs: Centralizados em Loki
- Metrics: Prometheus (scrape interval: 15s)
- Traces: Jaeger (amostragem: 10%)
- Dashboards: Grafana (MABA Overview, Performance, Errors)

**Alertas**:

- Error rate > 5%: Página time on-call
- Latency p95 > 10s: Aviso Slack
- Health check falha 3x: Restart automático
- LEI > 1.0 em PR: Bloqueia merge

### 4.4 Rollback

**Triggers Automáticos**:

- Health check falha por > 2 minutos
- Error rate > 10% por > 5 minutos
- Crash loop detectado (> 3 restarts em 10 min)

**Procedimento**:

```bash
# Rollback automático via Kubernetes
kubectl rollout undo deployment/maba -n vertice-production

# Rollback manual de database (se necessário)
psql -f migrations/rollback/012_maba_rollback.sql
```

### 4.5 Autorização de Deploy

**Desenvolvimento → Staging**:

- ✅ Aprovação: Lead Developer
- ✅ Checklist: Testes passando + LEI < 1.0

**Staging → Produção**:

- ✅ Aprovação: Arquiteto-Chefe (Juan)
- ✅ Checklist:
  - [ ] Smoke tests em staging executados com sucesso
  - [ ] Coverage ≥ 90%
  - [ ] LEI < 1.0 validado
  - [ ] Documentação atualizada
  - [ ] Changelog atualizado
  - [ ] Plano de rollback documentado
  - [ ] Time de on-call notificado

---

## 5. INTEGRAÇÃO COM MAXIMUS

### 5.1 Endpoints REST API

**Base URL**: `http://maba:8152/api/v1`

#### 5.1.1 POST /tasks - Criar Tarefa de Navegação

**Request**:

```json
{
  "task_type": "navigate",
  "url": "https://example.com",
  "actions": [
    { "type": "click", "selector": "#login-button" },
    { "type": "fill", "selector": "#username", "value": "user@example.com" },
    { "type": "submit", "selector": "#login-form" }
  ],
  "extract": {
    "title": "h1.page-title",
    "content": "div.main-content"
  },
  "screenshot": true,
  "timeout": 30000
}
```

**Response**:

```json
{
  "task_id": "maba-task-7f3d9a2b",
  "status": "queued",
  "created_at": "2025-10-30T14:23:45Z",
  "estimated_duration": 15000
}
```

#### 5.1.2 GET /tasks/{task_id} - Status da Tarefa

**Response**:

```json
{
  "task_id": "maba-task-7f3d9a2b",
  "status": "completed",
  "result": {
    "extracted_data": {
      "title": "Welcome to Example",
      "content": "Lorem ipsum..."
    },
    "screenshot_url": "/screenshots/7f3d9a2b.png",
    "cognitive_map_id": "cm-example-com-login"
  },
  "metrics": {
    "duration_ms": 12340,
    "requests_made": 8,
    "cognitive_map_used": true
  }
}
```

#### 5.1.3 POST /cognitive-maps/learn - Aprender Estrutura

**Request**:

```json
{
  "domain": "example.com",
  "entry_point": "/dashboard",
  "depth": 2,
  "extract_navigation": true
}
```

**Response**:

```json
{
  "cognitive_map_id": "cm-example-dashboard-v1",
  "nodes_discovered": 47,
  "edges_mapped": 132,
  "confidence_score": 0.92
}
```

#### 5.1.4 DELETE /tasks/{task_id} - Cancelar Tarefa

**Response**:

```json
{
  "task_id": "maba-task-7f3d9a2b",
  "status": "cancelled",
  "message": "Task cancelled by MAXIMUS"
}
```

### 5.2 Eventos Redis Pub/Sub

**Channel**: `maximus:maba:events`

**Evento: Task Started**:

```json
{
  "event": "task.started",
  "task_id": "maba-task-7f3d9a2b",
  "timestamp": "2025-10-30T14:23:46Z"
}
```

**Evento: Navigation Progress**:

```json
{
  "event": "navigation.progress",
  "task_id": "maba-task-7f3d9a2b",
  "current_url": "https://example.com/dashboard",
  "action_completed": "click #login-button",
  "progress_percent": 40
}
```

**Evento: Task Completed**:

```json
{
  "event": "task.completed",
  "task_id": "maba-task-7f3d9a2b",
  "status": "success",
  "result_available": true
}
```

**Evento: Task Failed**:

```json
{
  "event": "task.failed",
  "task_id": "maba-task-7f3d9a2b",
  "error": "TimeoutError: Navigation timeout exceeded 30s",
  "retry_suggested": false
}
```

### 5.3 Dependências de MAXIMUS

**Requeridos**:

- ✅ MAXIMUS Core Health Check: `/health` retorna 200
- ✅ PostgreSQL disponível (MAXIMUS compartilha database)
- ✅ Redis disponível (MAXIMUS compartilha instância)

**Opcionais**:

- ⚠️ MAXIMUS Decision Framework (para aprovação de tasks arriscadas)
- ⚠️ MAXIMUS Consciousness System (para logging enriquecido)

**Inicialização**:

```python
# MABA aguarda MAXIMUS estar healthy antes de aceitar tasks
async def startup():
    while not await maximus_client.is_healthy():
        logger.info("Waiting for MAXIMUS Core...")
        await asyncio.sleep(5)
    logger.info("MAXIMUS Core available - MABA ready")
```

### 5.4 Service Discovery

**Registro no Vértice Service Registry**:

```python
await auto_register_service(
    service_name="maba",
    port=8152,
    health_endpoint="/health",
    metadata={
        "category": "maximus_subordinate",
        "type": "browser_agent",
        "version": "1.0.0",
        "capabilities": [
            "web_navigation",
            "form_filling",
            "data_extraction",
            "cognitive_mapping"
        ]
    }
)
```

**Heartbeat**:

- Intervalo: 30 segundos
- Timeout: 90 segundos (3 falhas consecutivas = considerado down)

---

## 6. TAREFAS INICIAIS (MVP)

### 6.1 Task 1: DNS Management (Hostinger)

**Objetivo**: Automatizar gestão de registros DNS no painel Hostinger

**Capacidades**:

- Login automático em Hostinger
- Navegação até painel DNS
- Adicionar/editar/remover registros A, CNAME, MX, TXT
- Validação de propagação DNS

**Cognitive Map**: `cm-hostinger-dns-v1`

**Endpoints**:

- `POST /tasks/dns/create`
- `PUT /tasks/dns/update`
- `DELETE /tasks/dns/delete`

### 6.2 Task 2: Google Workspace Admin

**Objetivo**: Gestão de usuários e grupos no Google Workspace

**Capacidades**:

- Criar/desativar usuários
- Gerenciar grupos e membros
- Configurar políticas de senha
- Gerar relatórios de uso

**Cognitive Map**: `cm-google-admin-v1`

**Autenticação**: OAuth 2.0 (credenciais gerenciadas por MAXIMUS)

### 6.3 Task 3: Form Filling (Generic)

**Objetivo**: Sistema genérico de preenchimento de formulários web

**Capacidades**:

- Detecção automática de campos (nome, email, telefone, etc.)
- Preenchimento baseado em schema fornecido
- Validação de campos obrigatórios
- Submit e captura de resposta

**Cognitive Map**: Dinâmico (aprende estrutura de cada formulário)

### 6.4 Task 4: Search & Extract

**Objetivo**: Busca em websites e extração estruturada de dados

**Capacidades**:

- Busca em Google, Bing, DuckDuckGo
- Extração de títulos, snippets, URLs
- Follow-up em links selecionados
- Estruturação de dados em JSON

**Cognitive Map**: `cm-search-engines-v1`

### 6.5 Task 5: Data Extraction (E-commerce)

**Objetivo**: Extração de dados de produtos em sites de e-commerce

**Capacidades**:

- Navegação em categorias
- Extração de nome, preço, imagens, descrição
- Comparação de preços entre sites
- Detecção de promoções

**Cognitive Map**: Um por site (ex: `cm-amazon-products-v1`)

---

## 7. PROTOCOLOS CONSTITUCIONAIS

### 7.1 Detecção de Violações

**REGRA DE OURO**: Zero placeholders, zero mocks, 100% production-ready

**Validação Automática**:

```python
# Pre-commit hook
def validate_regra_de_ouro(diff):
    forbidden_patterns = [
        r"# TODO",
        r"# FIXME",
        r"pass\s*#\s*placeholder",
        r"raise NotImplementedError",
        r"\.mock\(\)",
        r"Mock\(\)"
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, diff):
            raise ConstitutionalViolation(f"REGRA DE OURO violada: {pattern}")
```

**Agentes Guardiões**:

- `lei_guardian.py`: Valida LEI < 1.0 em todo commit
- `coverage_guardian.py`: Bloqueia merge se coverage < 90%
- `fpc_monitor.py`: Alerta se FPC < 80% em produção

### 7.2 Obrigação da Verdade

**Cenários de Declaração de Impossibilidade**:

1. **Website requer CAPTCHA humano**:

   ```json
   {
     "status": "impossible",
     "reason": "Site requer resolução de CAPTCHA humano - MABA não possui capacidade de bypass",
     "alternatives": [
       "Usar serviço de resolução de CAPTCHA",
       "Solicitar API oficial do site"
     ]
   }
   ```

2. **Website usa autenticação 2FA não automatizável**:

   ```json
   {
     "status": "impossible",
     "reason": "Site requer 2FA via SMS - MABA não tem acesso a telefone físico",
     "alternatives": ["Configurar backup codes", "Usar autenticação via API"]
   }
   ```

3. **Rate limit excedido e IP bloqueado**:
   ```json
   {
     "status": "blocked",
     "reason": "IP bloqueado por rate limit - impossível continuar sem espera de 24h",
     "alternatives": [
       "Aguardar desbloqueio",
       "Usar proxy rotativo",
       "Contatar suporte do site"
     ]
   }
   ```

### 7.3 Verify-Fix-Execute Loop

**Protocolo**: Máximo 2 iterações com diagnóstico obrigatório antes de cada correção

**Iteração 1 - Verificação**:

```python
async def execute_task(task_id):
    # 1. Validar inputs
    if not validate_task_inputs(task_id):
        return {"status": "invalid", "diagnosis": "URL inválida ou ações malformadas"}

    # 2. Executar
    result = await navigate_and_extract(task_id)

    # 3. Verificar resultado
    if result.success:
        return {"status": "success", "data": result.data}
    else:
        # Diagnóstico obrigatório antes de retry
        diagnosis = await diagnose_failure(result)
        return {"status": "failed", "diagnosis": diagnosis, "retry_possible": diagnosis.retry_possible}
```

**Iteração 2 - Correção**:

```python
async def retry_with_fix(task_id, diagnosis):
    # Aplicar correção baseada em diagnóstico
    if diagnosis.issue == "selector_not_found":
        # Tenta seletores alternativos
        result = await navigate_with_fallback_selectors(task_id)
    elif diagnosis.issue == "timeout":
        # Aumenta timeout e tenta novamente
        result = await navigate_with_extended_timeout(task_id)
    else:
        # Falha permanente - não tenta 3ª vez
        return {"status": "impossible", "reason": diagnosis.reason}
```

---

## 8. MÉTRICAS DE GOVERNANÇA

### 8.1 Dashboard de Conformidade

**URL**: `https://grafana.vertice.com/d/maba-governance`

**Painéis**:

- **LEI Score**: Gráfico de linha (últimos 30 dias)
- **Test Coverage**: Gauge (meta: ≥ 90%)
- **FPC Score**: Gráfico de área (meta: ≥ 80%)
- **CRS Score**: Gráfico de linha (meta: ≥ 95%)
- **Violações Constitucionais**: Contador (meta: 0)

### 8.2 Relatórios Semanais

**Destinatário**: Arquiteto-Chefe (Juan)

**Conteúdo**:

- Tasks executadas: Total, sucesso, falhas
- Cognitive maps criados/atualizados
- Violações detectadas e corrigidas
- Métricas de qualidade (LEI, FPC, CRS)
- Incidentes de segurança
- Melhorias propostas

### 8.3 Auditoria Trimestral

**Checklist**:

- [ ] Review de credenciais armazenadas
- [ ] Validação de whitelist de domínios
- [ ] Análise de logs de segurança
- [ ] Teste de disaster recovery
- [ ] Atualização de dependências críticas
- [ ] Review de permissões de acesso

---

## 9. CONTATO E RESPONSABILIDADES

**Arquiteto-Chefe**: Juan (Vértice Platform Team)
**On-Call**: Time de DevOps (rotação semanal)
**Escalation**: incidents@vertice.com

**SLA**:

- Produção down: Resposta em 15 minutos
- Bug crítico: Fix em 4 horas
- Feature request: Avaliação em 48 horas

---

**Documento aprovado por**: \***\*\*\*\*\***\_\***\*\*\*\*\*** (Arquiteto-Chefe)
**Data de aprovação**: \***\*\*\*\*\***\_\***\*\*\*\*\***
**Próxima revisão**: 2025-01-30 (Trimestral)
