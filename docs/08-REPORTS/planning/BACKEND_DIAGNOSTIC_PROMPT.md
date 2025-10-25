# PROMPT DE DIAGNÓSTICO SISTEMÁTICO - BACKEND VÉRTICE

## CONTEXTO
O backend do projeto Vértice possui 110+ microserviços distribuídos em Docker Compose. O objetivo é realizar uma verificação sistemática profunda e criar um plano de ação cirúrgico para deixar o ambiente operacional (status UP).

---

## FASE 1: AUDITORIA SISTEMÁTICA

### 1.1 MAPEAMENTO DE DEPENDÊNCIAS
**Objetivo:** Entender a topologia de serviços e ordem de inicialização crítica.

**Ações:**
```bash
# Extrair grafo de dependências do docker-compose.yml
cd /home/juan/vertice-dev
grep -A 10 "depends_on:" docker-compose.yml > backend_dependencies.txt

# Identificar serviços sem dependências (Tier 0 - fundação)
awk '/^  [a-z_-]+:/{service=$1} /depends_on:/{skip=1} !skip && service{print service; service=""}' docker-compose.yml

# Mapear redes e volumes compartilhados
grep -E "networks:|volumes:" docker-compose.yml | sort | uniq -c
```

**Checklist:**
- [ ] Tier 0 identificados (redis, postgres, qdrant, kafka, etc)
- [ ] Tier 1 identificados (serviços core sem LLM)
- [ ] Tier 2 identificados (serviços com IA/LLM)
- [ ] Tier 3+ identificados (orquestradores e serviços compostos)

---

### 1.2 CONFLITOS DE INFRAESTRUTURA
**Objetivo:** Detectar colisões de portas, redes, volumes e nomes.

**Ações:**
```bash
# Conflitos de porta HOST
awk '/ports:/{flag=1; next} flag && /- "[0-9]+:[0-9]+"/{print} flag && /^[^ ]/{flag=0}' docker-compose.yml | \
  sed 's/.*"\([0-9]*\):.*/\1/' | sort | uniq -d

# Conflitos de nome de serviço (hífen vs underscore)
grep -oP '^  [a-z_-]+:' docker-compose.yml | sed 's/://g' | \
  awk '{gsub(/-/,"_"); print}' | sort | uniq -d

# Redes externas não criadas
grep -A 1 "external: true" docker-compose.yml

# Volumes órfãos (referenciados mas não declarados)
comm -23 \
  <(grep -oP 'volumes:.*\K[a-z_-]+(?=:)' docker-compose.yml | sort -u) \
  <(awk '/^volumes:/,/^[^ ]/' docker-compose.yml | grep -oP '^  [a-z_-]+:' | sed 's/://g' | sort -u)
```

**Checklist:**
- [ ] Duplicação de portas HOST resolvida
- [ ] Inconsistências de nome (service_name vs service-name) mapeadas
- [ ] Redes externas criadas ou marcadas como driver: bridge
- [ ] Volumes órfãos corrigidos

---

### 1.3 INTEGRIDADE DE DOCKERFILES
**Objetivo:** Validar que todos os serviços têm Dockerfile funcional.

**Ações:**
```bash
# Listar serviços com build context
awk '/^  [a-z_-]+:/{service=$1} /build:/{print service}' docker-compose.yml | sed 's/://g' > services_with_build.txt

# Validar existência de Dockerfile
while read svc; do
  path=$(awk -v s="$svc:" '$0 ~ s{flag=1; next} flag && /context:/{print $2; exit}' docker-compose.yml)
  if [ -z "$path" ]; then
    path=$(awk -v s="$svc:" '$0 ~ s{flag=1; next} flag && /build:/{getline; print $1; exit}' docker-compose.yml)
  fi
  [ ! -f "$path/Dockerfile" ] && echo "MISSING: $svc -> $path/Dockerfile"
done < services_with_build.txt

# Verificar multi-stage builds quebrados
find backend/services -name Dockerfile -exec grep -l "FROM.*AS.*builder" {} \; | \
  xargs -I{} sh -c 'grep -q "FROM.*builder" {} || echo "BROKEN MULTI-STAGE: {}"'
```

**Checklist:**
- [ ] Todos os Dockerfiles existem
- [ ] Multi-stage builds funcionais
- [ ] Base images válidas (não deprecated)

---

### 1.4 CONSISTÊNCIA DE VARIÁVEIS DE AMBIENTE
**Objetivo:** Garantir que URLs de serviço e configurações estão corretas.

**Ações:**
```bash
# Extrair todas as env vars de URL de serviço
grep -oP '_SERVICE_URL=.*' docker-compose.yml | sort | uniq > service_urls.txt

# Detectar URLs usando porta do HOST em vez do CONTAINER
grep -E 'http://[a-z_-]+:[8-9][0-9]{3}' docker-compose.yml | \
  grep -v "localhost" | grep -v "127.0.0.1"

# Validar que service names nas URLs existem no compose
awk -F'[/:]' '/SERVICE_URL=http:\/\//{print $4}' docker-compose.yml | sort -u | \
  while read sname; do
    grep -q "^  ${sname}:" docker-compose.yml || echo "SERVICE NOT FOUND: $sname"
  done

# Verificar inconsistências de nomeação (hífen vs underscore em URLs)
grep -oP 'SERVICE_URL=http://\K[^:]+' docker-compose.yml | \
  sed 'h; s/_/-/g; x; s/-/_/g; G' | paste - - | awk '$1 != $2'
```

**Checklist:**
- [ ] URLs internas usam service_name:container_port
- [ ] Sem referências a localhost/127.0.0.1 em env vars internas
- [ ] Nomeação consistente (definir padrão: hífen ou underscore)
- [ ] API_KEYs e secrets não hardcoded

---

### 1.5 HEALTHCHECKS E STARTUP ORDER
**Objetivo:** Garantir que depends_on + healthcheck funcionem corretamente.

**Ações:**
```bash
# Serviços sem healthcheck
comm -23 \
  <(grep -oP '^  [a-z_-]+:' docker-compose.yml | sed 's/://g' | sort) \
  <(awk '/healthcheck:/{ for(i=1; i<=10; i++) {getline; if(/^  [a-z_-]+:/) break; if(/test:/) {print prev}}} {prev=$0}' docker-compose.yml | grep -oP '^  \K[a-z_-]+' | sort)

# Healthchecks usando porta errada (host vs container)
grep -A 5 "healthcheck:" docker-compose.yml | grep -E "localhost:[8-9][0-9]{3}" | \
  grep -vE ":(8000|8007|8013|8014|8015|8016)" # Portas conhecidas do container

# Depends_on sem condition (não espera healthcheck)
awk '/depends_on:/{flag=1; svc=prev} flag && /^  [a-z_-]+:$/ && !/condition:/{print svc ": missing condition for", $1} flag && /^[^ ]/{flag=0} {prev=$0}' docker-compose.yml
```

**Checklist:**
- [ ] Serviços críticos têm healthcheck
- [ ] Healthchecks usam porta do container
- [ ] depends_on com condition: service_healthy onde necessário

---

### 1.6 VALIDAÇÃO DE REQUIREMENTS
**Objetivo:** Detectar dependências Python quebradas ou faltantes.

**Ações:**
```bash
# Verificar requirements.txt em cada serviço
find backend/services -name requirements.txt -exec sh -c '
  echo "=== {} ==="
  pip-compile --dry-run --quiet {} 2>&1 | grep -i "error\|conflict" || echo "OK"
' \;

# Detectar versões pinadas conflitantes entre serviços
find backend/services -name requirements.txt -exec grep -h "==" {} \; | \
  sort | uniq -d | awk -F'==' '{print $1}' | \
  while read pkg; do
    echo "Package: $pkg"
    find backend/services -name requirements.txt -exec grep "^$pkg==" {} +
    echo ""
  done

# Verificar se shared libs estão no PYTHONPATH
grep -r "from backend.shared" backend/services --include="*.py" | \
  cut -d: -f1 | sort -u | \
  while read file; do
    dir=$(dirname "$file")
    grep -q "PYTHONPATH.*backend" "$dir/../Dockerfile" || \
      echo "MISSING PYTHONPATH: $file"
  done
```

**Checklist:**
- [ ] Sem conflitos de versão de dependências
- [ ] Shared libs acessíveis (PYTHONPATH correto)
- [ ] Sem imports de módulos inexistentes

---

## FASE 2: PLANO DE AÇÃO CIRÚRGICO

### 2.1 PRIORIZAÇÃO DE FIXES
**Critério de severidade:**
1. **BLOCKER (P0):** Impede qualquer serviço de subir
   - Conflitos de porta
   - Redes externas ausentes
   - Dockerfiles inexistentes

2. **CRITICAL (P1):** Impede serviços core de funcionar
   - URLs internas incorretas
   - Dependências circulares
   - Healthchecks quebrados

3. **MAJOR (P2):** Degrada funcionalidade
   - Serviços secundários com erro
   - Timeouts excessivos
   - Logs de erro contínuos

4. **MINOR (P3):** Melhorias técnicas
   - Duplicação de código
   - Nomenclatura inconsistente
   - Otimizações de performance

---

### 2.2 TEMPLATE DE FIX (por issue)

```markdown
## FIX-XXX: [Título descritivo]

**Severidade:** P0/P1/P2/P3
**Componentes afetados:** [lista de serviços]
**Root cause:** [explicação técnica em 1-2 linhas]

### Mudanças necessárias:
```diff
# docker-compose.yml (linha XXX)
- ports: "8151:8036"
+ ports: "8153:8036"

# backend/api_gateway/main.py (linha YYY)
- OSINT_SERVICE_URL = "http://localhost:8007"
+ OSINT_SERVICE_URL = "http://osint-service:8007"
```

### Validação:
```bash
# Comando para testar
docker compose up -d [service_name]
curl http://localhost:8000/health
```

### Rollback (se necessário):
```bash
git checkout HEAD -- docker-compose.yml
docker compose restart api_gateway
```
```

---

### 2.3 ORDEM DE EXECUÇÃO DOS FIXES

**Fase 0 - Infraestrutura (BLOCKER)**
1. Criar redes externas faltantes
2. Resolver conflitos de porta HOST
3. Declarar volumes órfãos

**Fase 1 - Tier 0 Services (CRITICAL)**
1. Corrigir Dockerfiles de redis, postgres, qdrant
2. Validar healthchecks de bancos de dados
3. Subir e validar estabilidade: `docker compose up -d redis postgres qdrant`

**Fase 2 - Tier 1 Services (CRITICAL)**
1. Corrigir URLs internas no API Gateway
2. Normalizar service names (escolher hífen ou underscore)
3. Subir serviços core: `docker compose up -d api_gateway sinesp_service domain_service ip_intelligence_service nmap_service`

**Fase 3 - Tier 2+ Services (MAJOR)**
1. Corrigir dependências de IA (GEMINI_API_KEY, etc)
2. Validar integrações entre serviços (OSINT, MAXIMUS, etc)
3. Subir gradualmente: threat_intel → malware_analysis → maximus_core

**Fase 4 - Validação E2E (MAJOR)**
1. Smoke tests em endpoints críticos
2. Verificar logs de erro nos containers
3. Monitorar métricas do Prometheus

---

## FASE 3: AUTOMAÇÃO DE VALIDAÇÃO

### 3.1 SCRIPT DE HEALTH CHECK AUTOMÁTICO

```bash
#!/bin/bash
# backend/scripts/health_check_all.sh

set -e

SERVICES=(
  "api_gateway:8000:/health"
  "sinesp_service:80:/"
  "domain_service:80:/"
  "ip_intelligence_service:80:/"
  "nmap_service:80:/"
  "threat_intel_service:8013:/health"
  "malware_analysis_service:8014:/health"
  "maximus_core_service:8100:/health"
)

echo "=== BACKEND HEALTH CHECK ==="
for entry in "${SERVICES[@]}"; do
  IFS=':' read -r service port endpoint <<< "$entry"
  echo -n "Checking $service... "
  
  if docker compose ps "$service" | grep -q "Up"; then
    if curl -sf "http://localhost:$port$endpoint" > /dev/null; then
      echo "✅ HEALTHY"
    else
      echo "❌ UNHEALTHY (endpoint not responding)"
    fi
  else
    echo "❌ DOWN"
  fi
done
```

### 3.2 SMOKE TEST SUITE

```python
# backend/tests/smoke_test.py
import httpx
import pytest

BASE_URL = "http://localhost:8000"

@pytest.mark.parametrize("endpoint", [
    "/health",
    "/api/google/health",
    "/api/osint/health",
    "/cyber/health",
    "/threat-intel/health",
])
def test_service_health(endpoint):
    response = httpx.get(f"{BASE_URL}{endpoint}", timeout=10)
    assert response.status_code == 200
    assert "healthy" in response.text.lower() or "status" in response.json()

def test_api_gateway_reactive_fabric():
    response = httpx.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "reactive_fabric" in data
```

---

## FASE 4: DOCUMENTAÇÃO DE SAÍDA

### 4.1 RELATÓRIO DE EXECUÇÃO
Criar: `BACKEND_FIX_EXECUTION_REPORT.md`

**Estrutura:**
```markdown
# Backend Fix Execution Report

**Data:** [timestamp]
**Executor:** [nome/sistema]
**Status:** ✅ SUCCESS / ⚠️ PARTIAL / ❌ FAILED

## Fixes Aplicados
- [x] FIX-001: Conflito de porta 8151 (P0)
- [x] FIX-002: URL incorreta OSINT_SERVICE (P1)
- [ ] FIX-003: Healthcheck malware_analysis (P2) - PENDENTE

## Serviços Operacionais
- ✅ api_gateway (8000)
- ✅ redis (6379)
- ✅ postgres (5432)
- ⚠️ maximus_core_service (8100) - logs com warning
- ❌ offensive_gateway (8537) - dependência faltante

## Próximos Passos
1. Investigar warnings do maximus_core_service
2. Validar API_KEYs de serviços externos
3. Executar smoke tests completos
```

### 4.2 PLANO DE AÇÃO FINAL
Criar: `BACKEND_ACTION_PLAN.md`

**Formato:**
```markdown
# Plano de Ação - Backend Vértice

## P0 - BLOCKERS (executar AGORA)
1. [ ] Criar rede: `docker network create maximus-immunity-network`
2. [ ] Fix porta duplicada 8151: editar linha 930 do docker-compose.yml
3. [ ] Fix porta duplicada 5433: editar linha 2377 do docker-compose.yml

## P1 - CRITICAL (executar em 24h)
1. [ ] Normalizar URLs internas no api_gateway (10 ocorrências)
2. [ ] Adicionar healthcheck em 15 serviços core
3. [ ] Validar PYTHONPATH em Dockerfiles de serviços com shared libs

## P2 - MAJOR (executar em 1 semana)
1. [ ] Padronizar nomes: escolher hífen ou underscore
2. [ ] Migrar secrets hardcoded para .env
3. [ ] Implementar circuit breakers em chamadas de serviço

## P3 - MINOR (backlog)
1. [ ] Refatorar duplicação de código em Dockerfiles
2. [ ] Otimizar cache de layers Docker
3. [ ] Documentar topologia de serviços
```

---

## EXECUÇÃO DO PROMPT

**Comando para o Executor:**
```bash
# Executar diagnóstico completo
cd /home/juan/vertice-dev
bash backend/scripts/diagnostic_systematic.sh > BACKEND_DIAGNOSTIC_OUTPUT.txt 2>&1

# Gerar plano de ação
python backend/scripts/generate_action_plan.py --input BACKEND_DIAGNOSTIC_OUTPUT.txt --output BACKEND_ACTION_PLAN.md

# Executar fixes (modo dry-run primeiro)
python backend/scripts/apply_fixes.py --plan BACKEND_ACTION_PLAN.md --dry-run

# Aplicar fixes (real)
python backend/scripts/apply_fixes.py --plan BACKEND_ACTION_PLAN.md --execute --checkpoint-interval=5

# Validar
bash backend/scripts/health_check_all.sh
pytest backend/tests/smoke_test.py -v
```

---

## CRITÉRIOS DE SUCESSO

**Definição de "Backend UP":**
1. ✅ 90%+ dos serviços core em status `healthy`
2. ✅ API Gateway respondendo em http://localhost:8000/health
3. ✅ Smoke tests passando (>95%)
4. ✅ Logs sem erros críticos contínuos
5. ✅ Métricas Prometheus coletando dados

**SLA de disponibilidade:**
- Tier 0 (infra): 100% UP
- Tier 1 (core): 95% UP
- Tier 2+ (features): 80% UP

---

## NOTAS FINAIS

- **Princípio cirúrgico:** Modificar apenas o mínimo necessário
- **Validação contínua:** Após cada fix, validar que não quebrou outros serviços
- **Rollback preparado:** Ter git commit antes de cada batch de mudanças
- **Documentação obrigatória:** Cada fix deve ter entry no relatório

**Anexar ao final:**
- Lista completa de serviços (110+)
- Mapa de dependências (grafo)
- Inventário de portas (host:container)
- Checklist de validação por tier
