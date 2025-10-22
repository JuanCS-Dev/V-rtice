# PLANO DE BATALHA: RESSURREIÇÃO 100% - BACKEND VÉRTICE-MAXIMUS

**Versão:** 1.0  
**Data:** 2025-10-19  
**Status Atual:** 65% funcional → Objetivo: 100% Soberania Absoluta  
**Tempo Estimado:** 4-6 horas  
**Autoridade:** Arquiteto-Chefe (Soberano)

---

## FASE I: ANÁLISE FORENSE PROFUNDA

### 1. BLOQUEADOR: 11 Serviços com Build Falhado (13.1% do total)

#### 1.1 Causa-Raiz: Build Context Inválido

**Serviços afetados:**
- `eureka-confirmation`
- `maximus-eureka` 
- `maximus-oraculo`
- `oraculo-threat-sentinel`
- `offensive_gateway`
- `offensive_tools_service`
- `wargaming-crisol`
- `web_attack_service`
- `hitl-patch-service`
- `hpc-service`
- `hpc_service` (duplicado)

**Diagnóstico técnico:**

**Tipo A - Context Mismatch (4 serviços):**
- `eureka-confirmation`: build context `./backend/services` + dockerfile `maximus_eureka/Dockerfile`
- `maximus-eureka`: build context `./backend` + dockerfile `services/maximus_eureka/Dockerfile`
- `oraculo-threat-sentinel`: build context `./backend/services` + dockerfile `maximus_oraculo/Dockerfile`
- `maximus-oraculo`: build context correto, mas Dockerfile pode ter path issues

**Problema:** Docker compose define build context em um diretório, mas o Dockerfile referencia paths relativos que assumem outro context. Quando o Dockerfile usa `COPY services/X`, mas o context é `./backend/services`, o path resulta em `./backend/services/services/X` (não existe).

**Tipo B - Parent Directory Access (2 serviços):**
- `offensive_tools_service`: Dockerfile linha 15: `COPY ../../security /app/security`
- `offensive_gateway`: Similar issue

**Problema:** Docker build context não permite acessar diretórios pai (`../`). O Dockerfile tenta copiar `../../security`, mas isso viola a sandbox do build context. Erro: `"/security": not found`

**Tipo C - Missing/Duplicated Services (2 serviços):**
- `hpc-service` vs `hpc_service`: Naming inconsistency (hyphen vs underscore)
- `hitl-patch-service`: Não existe no filesystem como diretório standalone

**Problema:** Docker compose referencia serviço que não tem diretório correspondente ou usa naming errado.

---

### 2. BLOQUEADOR: 52 Serviços Unhealthy (78.8% dos containers com healthcheck)

#### 2.1 Causa-Raiz: Healthcheck Timeout/Misconfiguration

**Diagnóstico técnico:**

**Evidência empírica:**
- Teste manual: `docker compose exec domain_service curl -s http://localhost:8014/health` → `{"status":"healthy"}` ✅
- Status Docker: `unhealthy` ❌
- Healthcheck config: `HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8014/health || exit 1`

**Problema identificado:**
1. **Curl não instalado em imagens slim:** Muitos Dockerfiles usam `python:3.11-slim` como base, que NÃO inclui `curl` por padrão. Healthcheck tenta executar `curl`, falha com "command not found", retorna exit code != 0, Docker marca como unhealthy.

2. **Start period insuficiente:** Serviços FastAPI/Uvicorn levam 5-15s para inicializar completamente (import de dependências, conexão DB, etc). Healthcheck default `--start-period` é muito curto, marca como unhealthy antes do serviço estar pronto.

3. **Timeout muito agressivo:** `--timeout=10s` pode ser insuficiente para serviços que fazem validações complexas no healthcheck (ex: verificar conexão Redis + DB).

**Confirmação:** 
- Serviços respondem corretamente quando testados manualmente
- Logs não mostram crashes ou erros de runtime
- Issue é puramente de healthcheck configuration

---

### 3. BLOQUEADOR: API Gateway Contract Mismatch (Workflows E2E 0% funcionais via gateway)

#### 3.1 Causa-Raiz: Divergência Arquitetural entre Gateway e Microserviços

**Diagnóstico técnico:**

**Evidência forense:**
1. **Código do Gateway no repo:** `/backend/services/api_gateway/main.py` tem 319 linhas, 16 rotas simples, NÃO inclui rotas OSINT
2. **Código do Gateway no container:** Inspeção runtime mostra 151 rotas, incluindo 13 OSINT-related
3. **Conclusão:** Container foi buildado com código DIFERENTE do que está no repo atual

**Contract divergence identificada:**

| Componente | Esperado pelo Gateway | Real no Microserviço | Status |
|------------|----------------------|---------------------|--------|
| google_osint_service | `/api/search/basic` | `/query_osint` | ❌ MISMATCH |
| domain_service | `/api/domain/analyze` | endpoint desconhecido | ⚠️ NÃO VALIDADO |
| Porta google_osint | 8031 (env var) | 8016 (Dockerfile CMD) | ✅ CORRIGIDO |
| Porta domain | 80 (env var) | 8014 (Dockerfile CMD) | ✅ CORRIGIDO |

**Problema fundamental:**
1. **Versioning ausente:** Não há controle de versão de contratos API entre gateway e microserviços
2. **No schema validation:** Nenhum OpenAPI spec centralizado ou validação automática de contratos
3. **Build desacoplado:** API Gateway foi buildado em momento diferente dos microserviços, usando código-fonte que já divergiu

**Impacto:** Workflows E2E falham porque o Gateway chama endpoints que não existem ou com schemas incompatíveis.

---

### 4. BLOQUEADOR: Coverage 0% (Pytest não instrumenta código)

#### 4.1 Causa-Raiz: Pytest-cov Configuration para Monorepo

**Diagnóstico técnico:**

**Análise de configuração:**
```ini
# /backend/pytest.ini
[pytest]
pythonpath = services/active_immune_core services/api_gateway services libs/...
testpaths = libs/vertice_core/tests libs/vertice_api/tests services
```

**Problema identificado:**
1. **Coverage source path não especificado:** Comando executado foi `pytest --cov=services`, mas pytest-cov não sabe qual é o source root real dos arquivos a instrumentar
2. **Monorepo structure confusion:** Testes estão em `services/*/tests/`, código em `services/*/`, mas coverage não mapeia corretamente a relação
3. **Import paths mismatch:** Código usa absolute imports (`from services.X import Y`), mas coverage tracking usa relative paths

**Evidência:**
- 347 testes passam ✅
- Coverage report: 181,218 statements, 0 covered (0.00%)
- Pytest executa testes corretamente, mas coverage.py não intercepta as execuções

**Causa-raiz canônica:** Em monorepos com múltiplos packages, `pytest-cov` requer configuração explícita de `source` parameter ou `[run] source` em `.coveragerc` para saber qual código instrumentar.

---

### 5. BLOQUEADOR ADICIONAL: Discrepância Compose vs Filesystem (8 serviços órfãos)

#### 5.1 Causa-Raiz: Serviços não Orquestrados

**Diagnóstico:**
- Docker compose: 95 serviços definidos
- Filesystem: 87 diretórios em `/backend/services/`
- Delta: 8 serviços definidos no compose SEM diretório correspondente

**Serviços fantasma identificados:**
- `eureka-confirmation` (aponta para `maximus_eureka`)
- `maximus-eureka` (conflict com `maximus_eureka`)
- `oraculo-threat-sentinel` (aponta para `maximus_oraculo`)
- Outros com naming inconsistency (hyphen vs underscore)

**Problema:** Docker compose tem definições duplicadas ou malformadas que referenciam serviços que não existem ou conflitam com serviços reais.

---

## FASE II: INTELIGÊNCIA DE FONTES ABERTAS (OSINT)

### 1. Solução para Build Context Issues

**Fonte:** [Stack Overflow - Include files outside Docker build context](https://stackoverflow.com/questions/27068596/how-to-include-files-outside-of-dockers-build-context)

**Best practice identificada:**
1. **Ajustar build context para parent directory:** Mudar `context: ./backend/services/X` para `context: ./backend` e ajustar Dockerfile paths
2. **Usar multistage builds:** Copiar dependências compartilhadas em stage separado
3. **Consolidar shared code:** Mover `/security` para dentro do service directory ou usar Docker named volumes

**Solução canônica para Vértice:**
- **Opção A (Preferencial):** Mudar todos os build contexts para `./backend` e ajustar Dockerfiles para usar paths relativos corretos
- **Opção B:** Mover código compartilhado (`/security`) para um package pip instalável via `requirements.txt`

---

### 2. Solução para Healthcheck Failures

**Fontes:** 
- [Docker Status Unhealthy Fix](https://last9.io/blog/docker-status-unhealthy-how-to-fix-it/)
- [Fixing Unhealthy Containers](https://www.khueapps.com/blog/article/how-to-fix-healthcheck-failed-and-unhealthy-containers)

**Best practices identificadas:**
1. **Install curl in slim images:** Adicionar `RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*` nos Dockerfiles
2. **Increase start-period:** Usar `--start-period=60s` para serviços Python que importam muitas dependências
3. **Use python for healthcheck:** Substituir `curl` por `python -c "import httpx; httpx.get('http://localhost:PORT/health')"` (httpx já está instalado)
4. **Debug with docker inspect:** `docker inspect --format "{{json .State.Health}}" container_name` mostra logs de healthcheck

**Solução canônica para Vértice:**
- **Preferencial:** Usar `python -c` com httpx (já disponível em todos os serviços FastAPI)
- **Aumentar start-period:** `--start-period=60s` (vs atual 30s)
- **Aumentar timeout:** `--timeout=15s` (vs atual 10s)

---

### 3. Solução para API Gateway Contract Mismatch

**Fontes:**
- [Microsoft - Microservice API Versioning](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/maintain-microservice-apis)
- [Microservices Versioning Best Practices](https://www.opslevel.com/resources/the-ultimate-guide-to-microservices-versioning-best-practices)
- [OpenAPI Shared Schemas](https://stackoverflow.com/questions/71583589/openapi-spec-what-is-the-best-practice-that-multiple-microservices-use-the-sam)

**Best practices identificadas:**
1. **Contract-first development:** Definir OpenAPI spec ANTES de implementar gateway e microserviços
2. **Centralized schema registry:** Usar repositório Git separado para schemas OpenAPI, versionados com semantic versioning
3. **Automated validation:** Implementar CI step que valida se gateway e microserviços estão compatíveis com schema central
4. **API versioning in URL:** `/api/v1/osint/scan` vs `/api/v2/osint/scan`
5. **Gateway adapter pattern:** Se rebuild não é viável, criar adapter layer no gateway que traduz requests para formato esperado pelos microserviços

**Solução canônica para Vértice:**
- **Curto prazo (Tactical):** Rebuild API Gateway com código atual do repo
- **Médio prazo (Strategic):** Implementar OpenAPI schema validation + adapter pattern
- **Longo prazo:** Migrar para contract-first development com schema registry

---

### 4. Solução para Pytest Coverage 0%

**Fontes:**
- [Pytest Coverage Monorepo](https://pytest-with-eric.com/coverage/poetry-test-coverage/)
- [GitHub Issue - Coverage 0%](https://github.com/pytest-dev/pytest-cov/issues/641)

**Best practices identificadas:**
1. **Explicit source paths:** Usar `pytest --cov-source=backend/services --cov-report=...`
2. **Create .coveragerc:** Definir `[run] source = services` explicitamente
3. **Use relative_files = True:** Para monorepos, ajuda coverage.py mapear imports corretamente
4. **Combine coverage from multiple runs:** Se testes estão distribuídos, usar `coverage combine`

**Solução canônica para Vértice:**
```ini
# .coveragerc
[run]
source = services
relative_files = True
omit = 
    */tests/*
    */__pycache__/*
    */venv/*
```

Executar: `pytest --cov --cov-config=.coveragerc --cov-report=json`

---

## FASE III: PLANO DE BATALHA - EXECUÇÃO SISTEMÁTICA

### TRACK 1: BUILDS FALHADOS (Prioridade MÁXIMA)
**Objetivo:** 84/84 serviços buildados (100%)  
**Tempo estimado:** 90min

#### STEP 1.1: Corrigir Build Context (Serviços Tipo A)
**Duração:** 30min

**Ação:**
```bash
# Analisar conflitos de context atual
grep -A 3 "eureka-confirmation:\|maximus-eureka:\|oraculo-threat-sentinel:" docker-compose.yml

# Corrigir para context unificado
# Editar docker-compose.yml:
# - eureka-confirmation: context: ./backend, dockerfile: services/maximus_eureka/Dockerfile
# - maximus-eureka: REMOVER (duplicado)
# - oraculo-threat-sentinel: REMOVER (duplicado)
# - maximus-oraculo: verificar se context já está correto
```

**Validação:**
```bash
docker compose build eureka-confirmation --no-cache 2>&1 | tee /tmp/build_eureka.log
# Critério sucesso: "Successfully built" sem erros de path
```

---

#### STEP 1.2: Corrigir Parent Directory Access (Serviços Tipo B)
**Duração:** 45min

**Opção A - Ajustar Build Context (PREFERENCIAL):**
```bash
# Editar docker-compose.yml para offensive_tools_service e offensive_gateway:
# build:
#   context: ./backend  # Muda de ./backend/services/X para ./backend
#   dockerfile: services/offensive_tools_service/Dockerfile

# Editar Dockerfiles:
# Linha 15: COPY ../../security /app/security
# PARA:   COPY security /app/security
```

**Opção B - Mover Código Compartilhado:**
```bash
# Se Option A não resolver:
cp -r backend/security backend/services/offensive_tools_service/
cp -r backend/security backend/services/offensive_gateway/

# Editar Dockerfiles:
# COPY ../../security /app/security
# PARA: COPY security /app/security
```

**Validação:**
```bash
docker compose build offensive_tools_service offensive_gateway --no-cache --parallel
# Critério sucesso: ambos buildados sem erro "not found"
```

---

#### STEP 1.3: Resolver Serviços Duplicados/Missing (Tipo C)
**Duração:** 15min

**Ação:**
```bash
# 1. Remover duplicados do docker-compose.yml
# - maximus-eureka (duplicado de maximus_eureka)
# - oraculo-threat-sentinel (duplicado de maximus_oraculo)
# - hpc-service (duplicado de hpc_service)

# 2. Verificar se hitl-patch-service deve existir
ls -la backend/services/ | grep hitl
# Se não existir: REMOVER do docker-compose.yml
# Se existir: criar Dockerfile e requirements.txt
```

**Validação:**
```bash
docker compose config --services | wc -l
# Critério sucesso: número alinhado com filesystem (87 ou menos)
```

---

#### STEP 1.4: Rebuild Massivo
**Duração:** 20min

**Ação:**
```bash
# Build dos 11 serviços corrigidos
cat > /tmp/rebuild_list.txt << 'EOF'
eureka-confirmation
offensive_gateway
offensive_tools_service
wargaming-crisol
web_attack_service
maximus-oraculo
hpc_service
EOF

cat /tmp/rebuild_list.txt | xargs docker compose build --parallel --no-cache
```

**Validação:**
```bash
docker images | grep vertice-dev | wc -l
# Critério sucesso: >= 84 (100% dos serviços)

# Listar falhas remanescentes
docker images | grep vertice-dev > /tmp/built_images.txt
docker compose config --services > /tmp/compose_services.txt
comm -23 <(sort /tmp/compose_services.txt) <(grep vertice-dev /tmp/built_images.txt | sed 's/.*vertice-dev-//' | sed 's/ .*//' | sort)
# Critério sucesso: output vazio (0 falhas)
```

---

### TRACK 2: HEALTHCHECKS (Prioridade ALTA)
**Objetivo:** 66/66 healthchecks passing (100%)  
**Tempo estimado:** 60min

#### STEP 2.1: Criar Dockerfile Healthcheck Template
**Duração:** 15min

**Ação:**
```bash
cat > /tmp/healthcheck_fix_template.txt << 'EOF'
# ANTES:
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:PORT/health || exit 1

# DEPOIS:
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
  CMD python -c "import httpx; exit(0 if httpx.get('http://localhost:PORT/health', timeout=5).status_code == 200 else 1)" || exit 1
EOF
```

**Justificativa:**
- Remove dependência de `curl` (não instalado em slim images)
- Usa `httpx` (já presente em todos os serviços FastAPI)
- Aumenta `start-period` para 60s (serviços Python são lentos para importar)
- Aumenta `timeout` para 15s
- Adiciona `retries=3` para tolerância a falhas transitórias

---

#### STEP 2.2: Aplicar Fix aos Top 20 Serviços Unhealthy
**Duração:** 30min

**Ação:**
```bash
# Gerar lista dos 20 serviços mais críticos (unhealthy)
docker compose ps --format "{{.Service}} {{.Health}}" | grep unhealthy | head -20 > /tmp/unhealthy_top20.txt

# Para cada serviço, editar Dockerfile
for service in $(cat /tmp/unhealthy_top20.txt | awk '{print $1}'); do
  dockerfile=$(find backend/services -name Dockerfile -path "*/${service//-/_}/*" 2>/dev/null | head -1)
  if [ -f "$dockerfile" ]; then
    echo "Fixing: $dockerfile"
    # Backup
    cp "$dockerfile" "${dockerfile}.backup"
    
    # Substituir healthcheck
    sed -i 's/HEALTHCHECK --interval=30s --timeout=10s CMD curl.*/HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \\\n  CMD python -c "import httpx; exit(0 if httpx.get('\''http:\/\/localhost:PORT\/health'\'', timeout=5).status_code == 200 else 1)" || exit 1/' "$dockerfile"
    
    # Ajustar PORT (extrair do CMD uvicorn)
    port=$(grep "CMD.*uvicorn.*--port" "$dockerfile" | grep -oP '(?<=--port )\d+')
    if [ ! -z "$port" ]; then
      sed -i "s/PORT/$port/g" "$dockerfile"
    fi
  fi
done
```

**Validação:**
```bash
# Rebuild serviços corrigidos
cat /tmp/unhealthy_top20.txt | awk '{print $1}' | xargs docker compose build --parallel

# Restart para aplicar novos healthchecks
cat /tmp/unhealthy_top20.txt | awk '{print $1}' | xargs docker compose up -d --force-recreate

# Aguardar start-period (60s)
sleep 70

# Contar healthchecks passing
docker compose ps --format "{{.Health}}" | grep -c "healthy"
# Critério sucesso: >= 20 (de 14 baseline)
```

---

#### STEP 2.3: Aplicar Fix aos Serviços Remanescentes
**Duração:** 15min

**Ação:**
```bash
# Aplicar mesmo fix aos 32 serviços restantes unhealthy
docker compose ps --format "{{.Service}} {{.Health}}" | grep unhealthy | tail -32 > /tmp/unhealthy_remaining.txt

# Repetir loop do STEP 2.2 para estes serviços
# (código idêntico, apenas muda input file)
```

**Validação:**
```bash
# Após rebuild e restart
docker compose ps --format "{{.Health}}" | grep -c "healthy"
# Critério sucesso: >= 60/66 (90%+)

# Identificar os 6 que ainda falharem para análise manual
docker compose ps --format "{{.Service}} {{.Health}}" | grep unhealthy > /tmp/final_unhealthy.txt
```

---

### TRACK 3: API GATEWAY CONTRACT (Prioridade ALTA)
**Objetivo:** Workflows E2E 6/6 funcionais  
**Tempo estimado:** 90min

#### STEP 3.1: Rebuild API Gateway com Código Atual
**Duração:** 20min

**Ação:**
```bash
# Forçar rebuild do API Gateway (sem cache)
docker compose build api_gateway --no-cache

# Restart
docker compose up -d api_gateway --force-recreate

# Aguardar inicialização
sleep 10

# Verificar código-fonte no container
docker compose exec api_gateway ls -la /app/main.py
docker compose exec api_gateway wc -l /app/main.py
# Critério: deve ter 319 linhas (código atual do repo)
```

**Validação:**
```bash
# Verificar rotas após rebuild
docker compose exec api_gateway python3 -c "
import sys; sys.path.insert(0, '/app')
from main import app
print(f'Total routes: {len([r for r in app.routes if hasattr(r, \"path\")])}')
"
# Critério sucesso: número de rotas compatível com código repo (16 rotas, não 151)
```

---

#### STEP 3.2: Identificar e Documentar Contratos Reais dos Microserviços
**Duração:** 30min

**Ação:**
```bash
# Extrair OpenAPI specs de todos os serviços OSINT
services="google_osint_service domain_service ip_intelligence_service network_recon_service"

for svc in $services; do
  port=$(docker compose port $svc 8000 2>/dev/null || echo "unknown")
  if [ "$port" != "unknown" ]; then
    echo "=== $svc ===" >> /tmp/osint_contracts.txt
    docker compose exec -T $svc curl -s http://localhost:$(docker compose exec -T $svc printenv | grep PORT | cut -d= -f2 | head -1)/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Endpoints:')
for path in data.get('paths', {}).keys():
    print(f'  {path}')
" >> /tmp/osint_contracts.txt
    echo "" >> /tmp/osint_contracts.txt
  fi
done

cat /tmp/osint_contracts.txt
```

**Output esperado:**
```
=== google_osint_service ===
Endpoints:
  /health
  /query_osint

=== domain_service ===
Endpoints:
  /health
  /analyze_domain
...
```

---

#### STEP 3.3: Implementar Adapter Pattern no API Gateway
**Duração:** 40min

**Ação:**
```python
# Editar /backend/services/api_gateway/main.py
# Adicionar adapter functions ANTES das rotas proxy

# Exemplo para google_osint:
@app.post("/api/google/search/basic")
async def google_search_adapter(request: Request):
    """Adapter: traduz request gateway → microserviço."""
    body = await request.json()
    
    # Transform: gateway format → service format
    adapted_body = {
        "query": body.get("query"),
        "search_type": "web",  # default
        "limit": body.get("num_results", 10)
    }
    
    # Proxy para endpoint REAL do serviço
    service_url = os.getenv("GOOGLE_OSINT_SERVICE_URL", "http://google_osint_service:8016")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_url}/query_osint",
            json=adapted_body,
            timeout=180.0
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)

# Repetir para domain_service, ip_intelligence_service, etc.
```

**Validação:**
```bash
# Rebuild gateway com adapters
docker compose build api_gateway
docker compose up -d api_gateway --force-recreate

# Testar workflow OSINT E2E
curl -X POST http://localhost:8000/api/google/search/basic \
  -H 'Content-Type: application/json' \
  -d '{"query":"vertice security","num_results":3}' \
  -s | python3 -m json.tool

# Critério sucesso: resposta com results[], não erro 404 ou 503
```

---

### TRACK 4: TEST COVERAGE (Prioridade MÉDIA)
**Objetivo:** Coverage >70% (target 95%)  
**Tempo estimado:** 45min

#### STEP 4.1: Criar .coveragerc
**Duração:** 10min

**Ação:**
```bash
cat > /home/juan/vertice-dev/backend/.coveragerc << 'EOF'
[run]
source = services
relative_files = True
omit = 
    */tests/*
    */__pycache__/*
    */.venv/*
    */venv/*
    */site-packages/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = ../htmlcov
EOF
```

---

#### STEP 4.2: Re-executar Pytest com Coverage Corrigido
**Duração:** 15min

**Ação:**
```bash
cd /home/juan/vertice-dev/backend

# Executar com config corrigido
pytest tests/ \
  --cov \
  --cov-config=.coveragerc \
  --cov-report=json:../coverage_backend_100.json \
  --cov-report=term-missing \
  --cov-report=html \
  -v
```

**Validação:**
```bash
# Analisar coverage
python3 -c "
import json
with open('../coverage_backend_100.json') as f:
    data = json.load(f)
    cov = data['totals']['percent_covered']
    print(f'Coverage: {cov:.2f}%')
    print(f'Covered: {data[\"totals\"][\"covered_lines\"]}/{data[\"totals\"][\"num_statements\"]} lines')
"

# Critério sucesso: coverage > 10% (provando que instrumentação funciona)
# Target ideal: >= 70%
```

---

#### STEP 4.3: Identificar Gaps de Coverage
**Duração:** 20min

**Ação:**
```bash
# Gerar relatório por módulo
python3 -c "
import json
with open('../coverage_backend_100.json') as f:
    data = json.load(f)
    files = data.get('files', {})
    
    print('Top 10 módulos SEM coverage:')
    uncovered = [(f, d['summary']['percent_covered']) for f, d in files.items() if d['summary']['percent_covered'] < 50]
    for f, cov in sorted(uncovered, key=lambda x: x[1])[:10]:
        print(f'{cov:5.1f}% - {f}')
" > /tmp/coverage_gaps.txt

cat /tmp/coverage_gaps.txt
```

**Output esperado:**
Lista de serviços que precisam de mais testes unitários.

---

### TRACK 5: VALIDAÇÃO FINAL E CERTIFICAÇÃO (Prioridade MÁXIMA)
**Objetivo:** Certificar 100% Soberania Absoluta  
**Tempo estimado:** 60min

#### STEP 5.1: Validação de Builds
**Duração:** 10min

**Ação:**
```bash
# Contar imagens
total_images=$(docker images | grep vertice-dev | wc -l)
total_services=$(docker compose config --services | wc -l)

echo "Images: $total_images / $total_services"
echo "Percentage: $(($total_images * 100 / $total_services))%"

# Listar falhas
comm -23 \
  <(docker compose config --services | sort) \
  <(docker images | grep vertice-dev | awk '{print $1}' | sed 's/vertice-dev-//' | sort) \
  > /tmp/final_build_failures.txt

cat /tmp/final_build_failures.txt
```

**Critério sucesso:** 84/84 images (100%) ou justificativa para cada falha remanescente.

---

#### STEP 5.2: Validação de Healthchecks
**Duração:** 15min

**Ação:**
```bash
# Restart ALL para garantir healthchecks limpos
docker compose down
docker compose up -d

# Aguardar start-period máximo
sleep 90

# Contar healthchecks
total_containers=$(docker compose ps --format "{{.Service}}" | wc -l)
healthy_count=$(docker compose ps --format "{{.Health}}" | grep -c "healthy" || echo 0)
unhealthy_count=$(docker compose ps --format "{{.Health}}" | grep -c "unhealthy" || echo 0)

echo "Containers: $total_containers"
echo "Healthy: $healthy_count"
echo "Unhealthy: $unhealthy_count"
echo "Percentage healthy: $(($healthy_count * 100 / ($healthy_count + $unhealthy_count)))%"

# Gerar relatório final
docker compose ps --format "{{.Service}} {{.State}} {{.Health}}" > /tmp/final_healthcheck_status.txt
```

**Critério sucesso:** >= 85% healthy (target: 100%)

---

#### STEP 5.3: Validação de Workflows E2E
**Duração:** 20min

**Ação:**
```bash
# Workflow 1: OSINT Deep Search
curl -X POST http://localhost:8000/api/google/search/basic \
  -H 'Content-Type: application/json' \
  -d '{"query":"cybersecurity frameworks","num_results":5}' \
  -s -w "\nStatus: %{http_code}\n" | tee /tmp/workflow_osint.txt

# Workflow 2: Domain Analysis
curl -X POST http://localhost:8000/api/domain/analyze \
  -H 'Content-Type: application/json' \
  -d '{"domain":"example.com"}' \
  -s -w "\nStatus: %{http_code}\n" | tee /tmp/workflow_domain.txt

# Workflow 3: IP Intelligence
curl -X POST http://localhost:8000/api/ip/analyze \
  -H 'Content-Type: application/json' \
  -d '{"ip":"8.8.8.8"}' \
  -s -w "\nStatus: %{http_code}\n" | tee /tmp/workflow_ip.txt

# Workflow 4: Auth (register + login)
curl -X POST http://localhost:8006/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"test_user","email":"test@vertice.com","password":"test123"}' \
  -s -w "\nStatus: %{http_code}\n" | tee /tmp/workflow_auth_register.txt

curl -X POST http://localhost:8006/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"test_user","password":"test123"}' \
  -s -w "\nStatus: %{http_code}\n" | tee /tmp/workflow_auth_login.txt

# Análise de resultados
grep "Status: 20" /tmp/workflow_*.txt | wc -l
# Critério sucesso: >= 4/6 workflows retornando 200/201
```

---

#### STEP 5.4: Validação de Coverage
**Duração:** 5min

**Ação:**
```bash
python3 -c "
import json
with open('/home/juan/vertice-dev/coverage_backend_100.json') as f:
    cov = json.load(f)['totals']['percent_covered']
    print(f'Coverage: {cov:.2f}%')
    if cov >= 70:
        print('✅ PASS: Coverage >= 70%')
    elif cov >= 50:
        print('⚠️  WARN: Coverage >= 50% (target: 70%)')
    else:
        print('❌ FAIL: Coverage < 50%')
"
```

---

#### STEP 5.5: Geração do Relatório de Certificação 100%
**Duração:** 10min

**Ação:**
```bash
cat > /home/juan/vertice-dev/CERTIFICACAO_100_ABSOLUTA.md << 'EOF'
# CERTIFICAÇÃO 100% ABSOLUTA - BACKEND VÉRTICE-MAXIMUS

**Data:** $(date -I)
**Executor:** Célula Híbrida Humano-IA
**Tempo Total:** [PREENCHER]

## MÉTRICAS FINAIS

### Builds Docker
- **Total:** [X]/84 (XX.X%)
- **Status:** [PASS/FAIL]

### Containers Ativos
- **Total:** [X]/87 (XX.X%)
- **Healthy:** [X]/[Y] (XX.X%)
- **Status:** [PASS/FAIL]

### Workflows E2E
- **Funcionais:** [X]/6 (XX.X%)
- **Status:** [PASS/FAIL]

### Test Coverage
- **Cobertura:** XX.XX%
- **Testes Passing:** 347/347
- **Status:** [PASS/FAIL]

### Padrão Pagani
- **Violations:** [X]
- **Status:** [PASS/FAIL]

## CERTIFICAÇÃO

Estado do sistema: **[SOBERANO/NÃO-SOBERANO]**

Justificativa: [PREENCHER]

---
**Assinatura Digital:** [HASH DO ESTADO FINAL]
EOF

# Preencher métricas automaticamente
# (comandos similares aos validation steps acima)
```

---

## RESUMO EXECUTIVO DO PLANO

### Ordem de Execução (Caminho Crítico)
1. **TRACK 1** (Builds) → Desbloqueia TRACK 2 e 3
2. **TRACK 2** (Healthchecks) → Pode rodar em paralelo com TRACK 3
3. **TRACK 3** (API Gateway) → Depende de TRACK 1
4. **TRACK 4** (Coverage) → Independente, pode rodar em paralelo
5. **TRACK 5** (Validação) → Final, depende de todos

### Tempo Total Estimado
- **TRACK 1:** 90min
- **TRACK 2:** 60min (paralelo com TRACK 3)
- **TRACK 3:** 90min (paralelo com TRACK 2)
- **TRACK 4:** 45min (paralelo com qualquer)
- **TRACK 5:** 60min
- **TOTAL:** ~4-5 horas (com paralelização) ou 5.5-6.5h (sequencial)

### Critérios de Certificação 100%
| Métrica | Target | Mínimo Aceitável |
|---------|--------|------------------|
| Builds Docker | 84/84 (100%) | 80/84 (95%) |
| Containers Healthy | 87/87 (100%) | 74/87 (85%) |
| Workflows E2E | 6/6 (100%) | 5/6 (83%) |
| Test Coverage | >95% | >70% |
| Padrão Pagani Violations | 0 | ≤3 (não críticas) |

### Desvios Permitidos
- **Builds:** Até 4 serviços podem falhar SE forem marcados como deprecated/experimental
- **Healthchecks:** Até 13 serviços unhealthy SE responderem corretamente quando testados manualmente
- **Coverage:** Mínimo 70% aceitável SE todos os testes críticos passarem

---

## CONCLUSÃO

Este plano de batalha é a codificação sistemática do caminho de 65% → 100% Soberania Absoluta. Cada step é atômico, validável e reversível. Não há "best effort" - apenas execução disciplinada do protocolo.

A Glória se manifestará através da nossa adesão inflexível ao método.

**Status:** PRONTO PARA EXECUÇÃO  
**Aprovação Requerida:** Arquiteto-Chefe

---
**Versão:** 1.0  
**Changelog:** 2025-10-19 - Gênese do plano (FASE I + II + III completas)
