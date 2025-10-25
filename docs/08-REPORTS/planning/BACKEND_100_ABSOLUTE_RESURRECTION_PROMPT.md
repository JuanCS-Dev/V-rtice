# BACKEND 100% ABSOLUTE RESURRECTION - PROMPT DE ANÁLISE E CORREÇÃO TOTAL

## CONTEXTO CRÍTICO

O backend do sistema Vértice-MAXIMUS está "respirando por aparelhos". Necessita-se uma **ressurreição arquitetural completa**, não apenas fazer os containers subirem, mas garantir que **CADA COMPONENTE, CADA ENDPOINT, CADA INTEGRAÇÃO** esteja **100% FUNCIONAL, TESTADO E VALIDADO**.

---

## OBJETIVO DA MISSÃO

**Transformar o backend de um estado vegetativo para um estado de excelência operacional absoluta (100%).**

### Critérios de Sucesso (100% Absoluto):

1. ✅ **Todos os serviços up e healthy** (não apenas "running")
2. ✅ **Todos os healthchecks passando** (200 OK com métricas reais)
3. ✅ **Todas as integrações funcionando** (DB, Redis, RabbitMQ, etc.)
4. ✅ **Todos os endpoints respondendo corretamente** (não apenas 404/500)
5. ✅ **Todos os workflows E2E funcionais** (do input ao output completo)
6. ✅ **Zero mocks em produção** (Padrão Pagani - Artigo II)
7. ✅ **Zero TODOs/FIXMEs em código crítico**
8. ✅ **Coverage de testes ≥95%** (unitários + integração)
9. ✅ **Zero warnings críticos** (mypy, ruff, security scanners)
10. ✅ **Documentação de APIs atualizada** (OpenAPI/Swagger funcional)

---

## FASE 1: DIAGNÓSTICO PROFUNDO (Análise Forense)

### 1.1 Análise de Containers e Orquestração

**Objetivo:** Mapear o estado real de TODOS os containers backend.

**Tarefas:**
```bash
# 1. Status detalhado de TODOS os containers backend
docker-compose ps --all
docker ps -a --filter "name=vertice" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Logs de TODOS os serviços (últimas 1000 linhas)
for service in $(docker-compose config --services | grep -E "(api|worker|scheduler|osint|nlp|maximus|c2l)"); do
  echo "=== $service ===" >> backend_logs_full.txt
  docker-compose logs --tail=1000 "$service" >> backend_logs_full.txt 2>&1
done

# 3. Healthchecks individuais (curl interno)
docker-compose exec -T api-gateway curl -s http://localhost:8000/health || echo "FAIL: api-gateway"
docker-compose exec -T osint-deep-search curl -s http://localhost:8001/health || echo "FAIL: osint"
docker-compose exec -T nlp-parser curl -s http://localhost:8002/health || echo "FAIL: nlp"
# ... repetir para TODOS os serviços

# 4. Análise de dependências entre containers
docker-compose config | grep -A 5 "depends_on"
```

**Deliverable:** `DIAGNÓSTICO_CONTAINERS.json` com:
- Estado de cada container (up/down/restarting/unhealthy)
- Motivo de falha (se aplicável)
- Última reinicialização
- Uso de recursos (CPU/RAM)

---

### 1.2 Análise de Código-Fonte (Auditoria Arquitetural)

**Objetivo:** Identificar TODAS as violações de qualidade e gaps funcionais.

**Tarefas:**
```bash
# 1. Mapeamento de estrutura de módulos
find backend -type f -name "*.py" | grep -E "(main|app|__init__|routes|api)" > backend_structure_map.txt

# 2. Scan de violações do Padrão Pagani
echo "=== MOCKS PROIBIDOS ===" > backend_violations.txt
grep -r "mock\|TODO\|FIXME\|placeholder\|stub" backend/ --include="*.py" >> backend_violations.txt

# 3. Scan de type hints faltantes
echo "=== TYPE HINTS MISSING ===" >> backend_violations.txt
find backend -name "*.py" -exec grep -L "from typing import" {} \; >> backend_violations.txt

# 4. Análise de imports quebrados
cd backend && python -c "
import ast
import sys
from pathlib import Path

broken = []
for pyfile in Path('.').rglob('*.py'):
    try:
        ast.parse(pyfile.read_text())
    except SyntaxError as e:
        broken.append(f'{pyfile}: {e}')

print('\n'.join(broken))
" > ../backend_syntax_errors.txt

# 5. Scan de segurança
bandit -r backend/ -f json -o backend_security_scan.json

# 6. Análise de complexidade ciclomática
radon cc backend/ -a -j > backend_complexity.json
```

**Deliverable:** `DIAGNÓSTICO_CODIGO.json` com:
- Violações do Padrão Pagani (mocks/TODOs)
- Erros de sintaxe/imports
- Funções sem type hints
- Vulnerabilidades de segurança
- Código com complexidade >10 (refactor necessário)

---

### 1.3 Análise de Testes (Coverage Real)

**Objetivo:** Obter coverage REAL de TODOS os módulos backend.

**Tarefas:**
```bash
# 1. Coverage absoluto (todos os módulos backend)
pytest backend/tests/ \
  --cov=backend \
  --cov-report=json:coverage_backend_absolute.json \
  --cov-report=html:htmlcov_backend \
  --cov-report=term-missing \
  -v --tb=short \
  > backend_test_results.txt 2>&1

# 2. Análise de testes faltantes
coverage json --omit="*/tests/*,*/migrations/*" -o coverage_gaps.json

# 3. Testes quebrados (que estão sendo skipped)
grep -r "@pytest.mark.skip\|@unittest.skip" backend/tests/ > backend_skipped_tests.txt

# 4. Scan de assertions fracas (que não validam nada)
grep -r "assert True\|pass  # TODO" backend/tests/ > backend_weak_tests.txt
```

**Deliverable:** `DIAGNÓSTICO_TESTES.json` com:
- Coverage atual por módulo (%)
- Módulos com coverage <95%
- Testes skipped com justificativa
- Testes sem assertions (inúteis)
- Gap de testes críticos (ex: auth, payments, OSINT workflows)

---

### 1.4 Análise de Integrações (Conectividade Real)

**Objetivo:** Validar que TODAS as dependências externas estão funcionais.

**Tarefas:**
```bash
# 1. PostgreSQL - Validação de schemas
docker-compose exec -T postgres psql -U vertice -d vertice_db -c "\dt" > db_tables.txt
docker-compose exec -T postgres psql -U vertice -d vertice_db -c "SELECT count(*) FROM pg_stat_activity;" > db_connections.txt

# 2. Redis - Validação de conexão
docker-compose exec -T redis redis-cli PING
docker-compose exec -T redis redis-cli INFO stats > redis_stats.txt

# 3. RabbitMQ - Validação de queues
curl -u guest:guest http://localhost:15672/api/queues > rabbitmq_queues.json

# 4. MinIO/S3 - Validação de buckets
docker-compose exec -T minio mc ls local/ > minio_buckets.txt

# 5. Elasticsearch - Validação de índices
curl -s http://localhost:9200/_cat/indices?v > elasticsearch_indices.txt

# 6. Prometheus/Grafana - Validação de métricas
curl -s http://localhost:9090/api/v1/targets > prometheus_targets.json
```

**Deliverable:** `DIAGNÓSTICO_INTEGRACOES.json` com:
- Status de cada dependência (PostgreSQL, Redis, RabbitMQ, etc.)
- Conectividade (pode conectar? latência?)
- Dados de teste presentes (seeders funcionaram?)
- Permissões corretas (usuários, roles, ACLs)

---

### 1.5 Análise de Endpoints (API Real)

**Objetivo:** Testar TODOS os endpoints e validar responses.

**Tarefas:**
```bash
# 1. Extração de TODAS as rotas
cd backend && python -c "
from fastapi.routing import APIRoute
from importlib import import_module

# Importar todos os apps FastAPI
apps = ['api_gateway', 'osint_service', 'nlp_service', 'maximus_service']
routes = []

for app_name in apps:
    try:
        app = import_module(f'{app_name}.main').app
        for route in app.routes:
            if isinstance(route, APIRoute):
                routes.append(f'{app_name}: {route.methods} {route.path}')
    except Exception as e:
        print(f'ERROR loading {app_name}: {e}')

print('\n'.join(routes))
" > ../backend_all_routes.txt

# 2. Teste automatizado de TODOS os endpoints
# (usando arquivo de rotas gerado acima)
while read route; do
  method=$(echo $route | awk '{print $2}')
  path=$(echo $route | awk '{print $3}')
  service=$(echo $route | awk -F: '{print $1}')
  
  # Testar endpoint
  response=$(curl -s -X $method "http://localhost:8000$path" -w "\n%{http_code}")
  echo "$service $method $path: $response" >> backend_endpoint_tests.txt
done < backend_all_routes.txt

# 3. Validação de OpenAPI/Swagger
curl -s http://localhost:8000/docs > /dev/null && echo "Swagger OK" || echo "Swagger FAIL"
curl -s http://localhost:8000/openapi.json | jq . > backend_openapi_spec.json
```

**Deliverable:** `DIAGNÓSTICO_ENDPOINTS.json` com:
- Lista completa de endpoints por serviço
- Status de cada endpoint (200, 404, 500, timeout, etc.)
- Endpoints não documentados
- Endpoints que retornam mocks/placeholders
- Endpoints sem autenticação (security gap)

---

### 1.6 Análise de Workflows E2E (Fluxos Completos)

**Objetivo:** Validar que workflows críticos funcionam de ponta a ponta.

**Workflows Críticos:**
1. **OSINT Deep Search:** Input (target) → Reconnaissance → Analysis → Report
2. **NLP Parser:** Input (text) → Tokenization → Entity Recognition → Output
3. **MAXIMUS Decision:** Input (context) → AI Model → Decision → Action
4. **C2L (Command to Log):** Input (command) → Validation → Execution → Log
5. **Authentication:** Register → Login → JWT → Protected Route
6. **File Upload:** Upload → Storage (MinIO) → Metadata (PostgreSQL) → Retrieval

**Tarefas:**
```bash
# Para cada workflow, criar um script de teste E2E
# Exemplo: OSINT Deep Search
curl -X POST http://localhost:8000/api/v1/osint/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "depth": 2}' \
  > osint_workflow_test.json

# Validar response
jq '.status, .results, .errors' osint_workflow_test.json
```

**Deliverable:** `DIAGNÓSTICO_WORKFLOWS.json` com:
- Status de cada workflow crítico (funcional/parcial/quebrado)
- Etapa onde falha (se aplicável)
- Erro específico e stacktrace
- Dados de entrada e saída (para debugging)

---

## FASE 2: CATEGORIZAÇÃO DE PROBLEMAS (Triagem Estratégica)

Com base nos 6 diagnósticos acima, categorizar TODOS os problemas encontrados em:

### Categoria A: **BLOQUEADORES CRÍTICOS** (Impedem funcionamento básico)
- Exemplos: Container não sobe, DB inacessível, import quebrado

### Categoria B: **FALHAS FUNCIONAIS** (Funcionalidade não entrega valor)
- Exemplos: Endpoint retorna 500, workflow E2E quebrado

### Categoria C: **DÍVIDAS TÉCNICAS** (Funciona, mas viola Padrão Pagani)
- Exemplos: TODOs, mocks, coverage <95%

### Categoria D: **GAPS DE SEGURANÇA** (Vulnerabilidades)
- Exemplos: Auth bypassada, SQL injection, secrets hardcoded

### Categoria E: **GAPS DE OBSERVABILIDADE** (Funciona, mas não sabemos o estado)
- Exemplos: Logs ausentes, métricas não coletadas, healthcheck fake

**Deliverable:** `PROBLEMAS_CATEGORIZADOS.json` com:
```json
{
  "categoria_a_bloqueadores": [
    {
      "id": "BLOQ-001",
      "modulo": "osint-deep-search",
      "descricao": "Container reinicia infinitamente",
      "causa_raiz": "ImportError: elasticsearch module",
      "impacto": "OSINT completamente inoperante"
    }
  ],
  "categoria_b_funcionais": [...],
  "categoria_c_dividas": [...],
  "categoria_d_seguranca": [...],
  "categoria_e_observabilidade": [...]
}
```

---

## FASE 3: PLANO DE CORREÇÃO 100% (Blueprint de Execução)

### 3.1 Estrutura do Plano

Para CADA problema categorizado, criar:

```json
{
  "id": "BLOQ-001",
  "categoria": "A",
  "prioridade": 1,
  "modulo": "osint-deep-search",
  "problema": "Container reinicia infinitamente",
  "causa_raiz": "ImportError: elasticsearch module",
  "solucao": {
    "tipo": "dependency_fix",
    "arquivos_afetados": [
      "backend/osint-deep-search/requirements.txt",
      "backend/osint-deep-search/Dockerfile"
    ],
    "steps": [
      {
        "step": 1,
        "acao": "Adicionar 'elasticsearch==8.10.0' ao requirements.txt",
        "comando": "echo 'elasticsearch==8.10.0' >> backend/osint-deep-search/requirements.txt"
      },
      {
        "step": 2,
        "acao": "Rebuild do container",
        "comando": "docker-compose build osint-deep-search"
      },
      {
        "step": 3,
        "acao": "Restart e validação",
        "comando": "docker-compose up -d osint-deep-search && sleep 10 && docker-compose logs osint-deep-search --tail=50"
      }
    ],
    "validacao": {
      "tipo": "healthcheck",
      "comando": "curl -f http://localhost:8001/health",
      "criterio_sucesso": "http_code == 200 && response.status == 'healthy'"
    },
    "testes": [
      "pytest backend/tests/integration/test_osint_service.py -v"
    ],
    "rollback": {
      "comando": "git checkout backend/osint-deep-search/requirements.txt && docker-compose build osint-deep-search"
    }
  },
  "tempo_estimado": "15min",
  "dependencias": []
}
```

### 3.2 Ordem de Execução (Grafo de Dependências)

**PRIORIDADE 1: Bloqueadores Críticos (Categoria A)**
- Ordem: Infraestrutura → Dependências → Imports → Containers

**PRIORIDADE 2: Falhas Funcionais (Categoria B)**
- Ordem: Endpoints básicos → Integrações → Workflows E2E

**PRIORIDADE 3: Dívidas Técnicas (Categoria C)**
- Ordem: Remover mocks → Adicionar testes → Elevar coverage

**PRIORIDADE 4: Segurança (Categoria D)**
- Executar em PARALELO com Prioridade 1-3 (não bloqueia, mas crítico)

**PRIORIDADE 5: Observabilidade (Categoria E)**
- Última (sistema já funcional, agora adicionar telemetria)

### 3.3 Checkpoints de Validação

Após cada 20% do plano executado:
1. **Validar estado:** Rodar TODOS os diagnósticos novamente
2. **Comparar métricas:** Coverage, healthchecks, endpoints
3. **Commit atômico:** `git commit -m "BACKEND-FIX: [módulo] - [problema corrigido]"`
4. **Snapshot de estado:** `docker-compose ps > checkpoint_X.txt`

---

## FASE 4: EXECUÇÃO SISTEMÁTICA (Operação Cirúrgica)

### 4.1 Protocolo de Execução

Para CADA item do plano:

```bash
# 1. Anunciar item
echo "=== EXECUTANDO: [ID] - [Descrição] ==="

# 2. Executar steps
[executar steps sequencialmente]

# 3. Validar
[rodar comando de validação]

# 4. Se FALHOU:
   - Executar rollback
   - Logar erro em FAILED_FIXES.json
   - Marcar para análise manual
   - CONTINUAR com próximo item

# 5. Se PASSOU:
   - Logar sucesso em SUCCESSFUL_FIXES.json
   - Commit atômico
   - CONTINUAR com próximo item
```

### 4.2 Modo de Falha Seguro

- **NUNCA parar execução por 1 falha** (exceto se categoria A e bloqueia tudo)
- **Isolar falhas:** Um módulo quebrado não pode impedir correção de outros
- **Log forensics:** Capturar TUDO (stdout, stderr, exit codes, core dumps)

---

## FASE 5: VALIDAÇÃO 100% ABSOLUTA (Certificação Final)

### 5.1 Bateria de Testes Completa

```bash
# 1. Todos os containers UP e HEALTHY
docker-compose ps | grep -c "Up (healthy)" == [número total de serviços backend]

# 2. Todos os healthchecks PASSING
for service in $(docker-compose config --services | grep backend); do
  docker-compose exec -T $service curl -f http://localhost:[porta]/health || exit 1
done

# 3. Todos os endpoints RESPONDENDO
python scripts/test_all_endpoints.py --fail-fast

# 4. Todos os workflows E2E FUNCIONAIS
pytest backend/tests/e2e/ -v --tb=short

# 5. Coverage ≥95%
pytest --cov=backend --cov-fail-under=95

# 6. Zero violações Padrão Pagani
! grep -r "mock\|TODO\|FIXME" backend/ --include="*.py" --exclude-dir=tests

# 7. Zero warnings críticos
mypy backend/ --strict --no-error-summary | grep -c "error" == 0
ruff check backend/ | grep -c "error" == 0

# 8. Docs atualizadas
curl -f http://localhost:8000/docs > /dev/null

# 9. Performance baseline
ab -n 1000 -c 10 http://localhost:8000/health | grep "Requests per second"

# 10. Security scan PASSING
bandit -r backend/ -ll | grep -c "Issue" == 0
```

### 5.2 Certificado de 100% Absoluto

Se TODOS os 10 testes acima passarem:

```json
{
  "certificacao": "BACKEND 100% ABSOLUTO",
  "timestamp": "2025-10-18T22:00:00Z",
  "metricas": {
    "containers_healthy": "X/X (100%)",
    "healthchecks_passing": "X/X (100%)",
    "endpoints_ok": "X/X (100%)",
    "workflows_functional": "X/X (100%)",
    "test_coverage": "98.5%",
    "padrão_pagani_violations": 0,
    "type_errors": 0,
    "security_issues": 0
  },
  "status": "OPERACIONAL PLENO",
  "observacoes": "Backend ressuscitado com sucesso. Todos os sistemas funcionais."
}
```

---

## DELIVERABLES FINAIS

1. **`DIAGNÓSTICO_COMPLETO.json`** - Consolidação de todas as análises da Fase 1
2. **`PROBLEMAS_CATEGORIZADOS.json`** - Triagem estratégica (Fase 2)
3. **`PLANO_CORRECAO_100.json`** - Blueprint detalhado de execução (Fase 3)
4. **`RELATORIO_EXECUCAO.json`** - Log de TODAS as correções aplicadas (Fase 4)
5. **`CERTIFICACAO_100_ABSOLUTO.json`** - Métricas finais e certificado (Fase 5)
6. **`BACKEND_100_COMPLETE.md`** - Documentação narrativa do processo completo

---

## FILOSOFIA DE EXECUÇÃO (Lembretes Constitucionais)

### ⚖️ Artigo I, Cláusula 3.1: Adesão Inflexível ao Plano
- Seguir o plano gerado com precisão cirúrgica
- Desvios SOMENTE com aprovação explícita do Arquiteto-Chefe

### 🎯 Artigo II: Padrão Pagani
- Zero mocks/TODOs em código de produção
- 99% dos testes devem passar (mínimo)

### 🔒 Artigo III: Zero Trust
- Todo código gerado é "não confiável" até validado
- Validação tripla obrigatória (estática, testes, conformidade)

### 💪 Artigo IV: Antifragilidade
- Sistema deve ser resiliente a falhas parciais
- Cada correção deve fortalecer o sistema, não apenas "tampar buraco"

### 📋 Artigo V: Legislação Prévia
- Nenhuma funcionalidade nova sem governança definida

### 🚫 Artigo VI: Anti-Verbosidade
- Executar steps silenciosamente
- Reportar APENAS: progresso (25/50/75/100%), bloqueadores, desvios críticos

---

## MODO DE OPERAÇÃO RECOMENDADO

**Sugestão:** Usar modo **Plan Mode** para gerar o plano completo (Fases 1-3) sem executar.
Após revisão e aprovação do Arquiteto-Chefe, executar em modo **Execute Mode**.

**Comando de invocação:**
```
@executor-tático-backend: Execute o diagnóstico completo e geração de plano conforme BACKEND_100_ABSOLUTE_RESURRECTION_PROMPT.md - Fases 1, 2 e 3. NÃO execute correções ainda. Deliverable: PLANO_CORRECAO_100.json
```

Após aprovação:
```
@executor-tático-backend: Execute o PLANO_CORRECAO_100.json - Fase 4. Report progresso a cada 25%. Deliverable: RELATORIO_EXECUCAO.json
```

---

**FIM DO PROMPT DE ANÁLISE E CORREÇÃO 100% ABSOLUTA DO BACKEND**

**Versão:** 1.0
**Autor:** Arquiteto-Chefe
**Objetivo:** Ressurreição completa do backend Vértice-MAXIMUS
**Critério de Sucesso:** 100% absoluto em funcionalidade, qualidade e conformidade constitucional
