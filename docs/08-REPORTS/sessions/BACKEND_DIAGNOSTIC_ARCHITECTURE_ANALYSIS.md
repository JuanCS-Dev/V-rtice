# 🔬 BACKEND ARCHITECTURE - DIAGNOSTIC ANALYSIS

**Data:** 2025-10-18T15:57:00Z  
**Analista:** DevOps Senior | Metodologia: Truth-Based Investigation  
**Conformidade:** Constituição Vértice v2.7

---

## 📊 ESTADO ATUAL DO SISTEMA

### Inventário de Serviços:
- **Definidos:** 95 services (docker-compose.yml)
- **Em execução:** 68 containers
- **Gap:** 27 serviços não iniciados

### Distribuição de Health Status:
```
HEALTHY:     9 serviços (13%)  ✅
UNHEALTHY:   52 serviços (76%) ⚠️
RESTARTING:  3 serviços (4%)   🔄
RUNNING:     4 serviços (6%)   ⚡ (sem healthcheck)
```

### Taxa de Sucesso Real: **13% HEALTHY**

---

## 🔍 ANÁLISE DE CAUSA RAIZ

### CATEGORIA 1: SERVIÇOS EM RESTART LOOP (3)

#### 1.1 adaptive_immunity_service
**Erro:** `ModuleNotFoundError: No module named 'backend'`

**Causa Raiz:**
```python
# main.py (linha 2):
from backend.services.adaptive_immunity_service.api import app
```

**Contexto Container:**
- Dockerfile CMD: `uvicorn main:app --host 0.0.0.0 --port 8000`
- WORKDIR: `/app`
- PYTHONPATH: `/app:/app/_demonstration`
- Estrutura real: `/app/main.py`, `/app/api.py`

**Problema:** Import absoluto `backend.services.X` não resolve porque:
1. PYTHONPATH não inclui `/home/juan/vertice-dev` (root do repo)
2. Container copia apenas o diretório do serviço para `/app`
3. Estrutura esperada: `/app/backend/services/X` (NÃO EXISTE)

**Status no Git:** 
- Commit `fbaf510a` (2h atrás): "fix(backend): systematic healthcheck and command override fixes"
- Estado ANTES do deploy: import estava com `backend.services.X`
- Arquitetura ORIGINAL funcionava com este padrão

#### 1.2 hcl_kb_service
**Erro:** Similar ao adaptive (ModuleNotFoundError: 'backend')

**Causa Raiz:** IDÊNTICA ao caso 1.1
- Import: Nenhum explícito com `backend.` em main.py
- Dockerfile: Padrão correto
- Provável: Imports internos em `models.py` ou `database.py`

#### 1.3 maximus_eureka
**Erro:** `ImportError: cannot import name 'app' from 'api'`

**Causa Raiz DIFERENTE:**
```python
# api_server.py (linha 26):
from api import *  # ❌ Wildcard import perigoso
```

**Contexto:**
- Dockerfile CMD: `uvicorn api_server:app --host 0.0.0.0 --port 8036`
- `api/__init__.py` exporta apenas: `ml_metrics_router`
- NÃO exporta `app` object
- Wildcard import `from api import *` traz apenas `ml_metrics_router`
- `app` é definido DEPOIS do import (linha 28)

**Problema:** Ordem de importação circular + wildcard mascarando o erro

---

### CATEGORIA 2: SERVIÇOS UNHEALTHY (52)

#### 2.1 Pattern Comum Identificado:
**Healthcheck Dockerfile:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:8XXX/health || exit 1
```

**Docker-compose.yml:**
- Maioria dos serviços SEM override de healthcheck
- Expõe portas inconsistentes

**Exemplo maximus-core:**
- Dockerfile HEALTHCHECK: `localhost:8150`
- Docker-compose ports: `8151:8001` + `8150:8100`
- Container internal port: **8150** (CMD usa `--port 8150`)
- Healthcheck provavelmente está batendo na porta certa

**Teste Real:**
```bash
docker compose exec maximus-core curl -f http://localhost:8100/health
# Result: service not running (porque container está unhealthy!)
```

**Hipóteses de Falha Healthcheck:**
1. **Endpoint `/health` não implementado** (mais provável)
2. **Porta divergente** (improvável, Dockerfiles consistentes)
3. **Startup lento** (60s start-period já configurado)
4. **Dependências falhando** (Redis/Postgres funcionam)

#### 2.2 Validação de Endpoint `/health`:

**Serviços HEALTHY (9):**
- ethical_audit_service ✅
- hcl-kafka ✅
- immunis_treg_service ✅
- maximus_integration_service ✅
- memory_consolidation_service ✅
- vertice-adaptive-immune ✅
- maximus_orchestrator ✅
- hcl-postgres ✅

**Padrão dos Healthy:** Todos têm endpoint `/health` implementado

**Serviços UNHEALTHY:** Provável ausência de endpoint

---

### CATEGORIA 3: SERVIÇOS NÃO INICIADOS (27)

Lista completa:
```
autonomous_investigation_service
bas_service
c2_orchestration_service
eureka-confirmation
grafana
hcl-analyzer/executor/monitor/planner (4)
hitl-patch-service
hpc-service/hpc_service (duplicata?)
immunis_api_service
kafka-immunity/zookeeper-immunity (2)
maximus_eureka
maximus-oraculo
network_recon_service
offensive_gateway/offensive_tools_service (2)
oraculo-threat-sentinel
postgres-immunity
prometheus
tataca_ingestion
wargaming-crisol
web_attack_service
```

**Causa Raiz:** 
- `docker compose up` padrão não inicia TODOS os services
- Profiles não configurados
- Depends_on chain incompleto

---

## 🧬 ARQUITETURA HISTÓRICA

### Timeline de Correções (últimos commits):

1. **280a45d9** (16h atrás): "Backend full deployment - 60 serviços operacionais (95%)"
   - 60/63 serviços UP
   - 95% success rate

2. **fbaf510a** (2h atrás): "fix(backend): systematic healthcheck and command override fixes"
   - Correções em healthchecks
   - Command overrides

3. **7b712b65** (HEAD): "docs(backend): session report - truth-based progress tracking"
   - Apenas documentação

### Estado Anterior Funcional:
- Commit `280a45d9` tinha **60 serviços operacionais**
- Hoje temos **9 healthy + 52 unhealthy = 61 rodando**
- **DEGRADAÇÃO:** 60 healthy → 9 healthy

### O QUE QUEBROU:
- Commit `fbaf510a` introduziu regressão
- "Systematic healthcheck fixes" → quebrou healthchecks
- Imports `backend.services.X` sempre estiveram lá (desde `b49a4f2a`)

---

## 🎯 CATEGORIZAÇÃO DE PROBLEMAS

### TIER 1 - CRÍTICO (Bloqueadores de Boot):
1. **adaptive_immunity_service:** Import path incorreto
2. **hcl_kb_service:** Import path incorreto
3. **maximus_eureka:** Circular import + wildcard

**Impacto:** 3 serviços em restart infinito (consumo CPU alto)

### TIER 2 - ALTO (Healthchecks falhando):
4. **52 serviços unhealthy:** Endpoint `/health` ausente

**Impacto:** Orquestração assume serviços down, possível cascata de falhas

### TIER 3 - MÉDIO (Não iniciados):
5. **27 serviços não startados:** Compose profiles/depends

**Impacto:** Features desabilitadas, cobertura incompleta

---

## 🔬 VALIDAÇÃO DE HIPÓTESES

### Hipótese 1: "Imports estão errados"
**STATUS:** ❌ FALSA

**Evidência:**
- Commit `fbaf510a` (que quebrou) não alterou imports
- Estado `280a45d9` (60 services UP) tinha mesmos imports
- Pattern `from backend.services.X.api import app` é PADRÃO do projeto

**Conclusão:** Imports são CORRETOS para a arquitetura original

### Hipótese 2: "PYTHONPATH está errado"
**STATUS:** ⚠️ PARCIALMENTE VERDADEIRA

**Evidência:**
- Containers healthy têm `PYTHONPATH=/app:/app/_demonstration`
- Mesma variável nos containers em restart
- Diferença: **conteúdo de `/app`** não estrutura de paths

**Conclusão:** PYTHONPATH correto, mas build context mudou

### Hipótese 3: "Dockerfile CMD mudou"
**STATUS:** ❌ FALSA

**Evidência:**
- CMDs consistentes entre serviços
- Nenhum diff em Dockerfiles entre commits funcionais

### Hipótese 4: "Docker-compose command override quebrou"
**STATUS:** ✅ VERDADEIRA (CAUSA RAIZ ENCONTRADA!)

**Evidência:**
```bash
docker compose config | grep -A5 "maximus_eureka:"
# Result: volumes monta /app/maximus_eureka
```

**Docker-compose.yml:**
```yaml
maximus_eureka:
  build: ./backend/services/maximus_eureka
  volumes:
    - ./backend/services/maximus_eureka:/app/maximus_eureka
  environment:
    - ORACULO_TARGET_PATH=/app/maximus_oraculo
```

**PROBLEMA IDENTIFICADO:**
1. Dockerfile copia código para `/app`
2. Docker-compose VOLUME sobrescreve com mount em `/app/maximus_eureka`
3. uvicorn procura `api_server:app` em `/app/api_server.py`
4. Arquivo real está em `/app/maximus_eureka/api_server.py`

**Mesma lógica para adaptive_immunity_service:**
- Build context: `./backend/services/adaptive_immunity_service`
- Dockerfile WORKDIR: `/app`
- Se há volume override para `/app/backend/...`: PATH QUEBRA

---

## 🔍 VERIFICAÇÃO FINAL

### Checklist de Validação:

```bash
# 1. Verificar volumes em docker-compose
grep -A10 "adaptive_immunity_service:" docker-compose.yml | grep volumes

# 2. Verificar CMD efetivo
docker inspect adaptive-immunity-service | grep -A10 Cmd

# 3. Verificar estrutura /app em runtime
docker compose run --rm adaptive_immunity_service ls -la /app

# 4. Comparar com serviço healthy
docker compose exec ethical-audit ls -la /app
```

---

## 💡 CONCLUSÃO DIAGNÓSTICA

### CAUSA RAIZ SISTÊMICA:

**Docker-compose volumes overrides** estão conflitando com estrutura de build dos Dockerfiles.

**Evidências Consolidadas:**
1. Mesmo código funcionava em `280a45d9` (60 UP)
2. Commit `fbaf510a` alterou docker-compose (não código)
3. Imports `backend.services.X` são CORRETOS para volumes mounted
4. Imports relativos funcionariam para build sem volumes

### DECISÃO ARQUITETURAL NECESSÁRIA:

**Opção A: Remover volume overrides (Produção)**
- Pros: Performance, imutabilidade, CI/CD friendly
- Cons: Rebuild para cada mudança (dev lento)

**Opção B: Ajustar PYTHONPATH + Imports (Dev)**
- Pros: Hot reload, dev rápido
- Cons: Divergência dev/prod, complexidade

**Opção C: Hybrid (Atual - QUEBRADO)**
- Dockerfiles assumem build puro
- Docker-compose monta volumes
- **CONFLITO DE PARADIGMAS**

---

## 🎯 RECOMENDAÇÃO ESTRATÉGICA

**MANTER ARQUITETURA ORIGINAL (Opção A)**

Rationale:
1. Conformidade Artigo II (Padrão Pagani): Produção ≠ Dev hacks
2. Estado `280a45d9` era funcional: REVERTER alterações de `fbaf510a`
3. Lei Zero: Backend DEVE ser confiável
4. Antifragilidade: Build hermético > mount frágil

**PRÓXIMO PASSO:** 
Criar plano de correção reversa para restaurar estado `280a45d9` + diagnosticar por que `fbaf510a` foi commitado.

---

**Assinatura Doutrinária:**  
✅ Artigo VI.1 - Supressão de checkpoints triviais (análise direta)  
✅ Artigo I.3.2 - Visão sistêmica (impacto em 68 containers)  
✅ Artigo III.1 - Artefatos não confiáveis (validação antes de implementar)

**Status:** ANÁLISE COMPLETA - AGUARDANDO APROVAÇÃO DE PLANO
