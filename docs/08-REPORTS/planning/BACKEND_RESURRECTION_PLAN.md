# 🔄 BACKEND RESURRECTION PLAN
**Status:** CRITICAL - Sistema inoperante  
**Objetivo:** Build funcional com 100% dos serviços UP  
**Data:** 2025-10-18 02:24 UTC  

---

## 📊 DIAGNÓSTICO EXECUTIVO

### Causa Raiz
Durante migração de imports relativos → absolutos (commits `66626e21` até `bc1d3abf` em 2025-10-17), foi introduzido um **padrão anti-arquitetural de imports cross-service** via `sys.path` hacks.

**Sintoma crítico:**
```python
# Em maximus_eureka/orchestration/eureka_orchestrator.py:48
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "maximus_oraculo"))
from models.apv import APV  # ❌ QUEBRA: cross-service dependency no runtime
```

### Escopo do Dano
- **Arquivos afetados:** 15 arquivos em `maximus_eureka` + pattern replicado em outros serviços
- **Serviços down:** 85 de 87 (apenas postgres/redis UP)
- **Commits ontem:** 49 (alta velocidade de mudanças = alto risco de regressão)
- **Arquitetura:** 90 pyproject.toml (cada serviço é um pacote Python isolado)
- **Duplicação:** APV model existe em 3 lugares (eureka: 440L, oraculo: 440L idêntico, adaptive_immune: 230L)

### Estado Atual Build
```
✅ vertice-postgres    UP 21min
✅ vertice-redis       UP 21min
❌ maximus-eureka      Exited (1) - ModuleNotFoundError: models.apv
❌ 85 outros serviços  Exited (0/127) - nunca iniciados
```

---

## 🎯 ESTRATÉGIA DE RESSURREIÇÃO

### Princípios Arquiteturais (Constituição Vértice)
1. **Zero Trust:** Cada serviço é um contexto isolado (não deve importar código de outro serviço)
2. **Padrão Pagani:** Zero mocks/TODOs, 99%+ testes passando
3. **Anti-Verbosidade:** Execução silenciosa, reportar apenas bloqueadores
4. **Legislação Prévia:** Definir doutrina de imports ANTES de executar fix

---

## 📋 PLANO DE AÇÃO (5 FASES)

### **FASE 1: DOUTRINA DE IMPORTS** ⏱ 5min
**Objetivo:** Estabelecer padrão constitucional de imports entre serviços

#### Decisão Arquitetural: Shared Models via `backend.shared`
```python
# ✅ PADRÃO APROVADO
# Em backend/shared/models/apv.py (fonte única da verdade)
from pydantic import BaseModel

class APV(BaseModel):
    """Atomic Patchable Vulnerability - Shared model"""
    # ... implementação canônica

# ✅ USO EM SERVIÇOS
# Em maximus_eureka/orchestration/eureka_orchestrator.py
from backend.shared.models.apv import APV  # Import absoluto do shared

# ✅ PYTHONPATH em Dockerfile
ENV PYTHONPATH="/app:/app/backend:${PYTHONPATH}"
```

**Alternativa rejeitada:** `sys.path` hacks (violação Zero Trust)

**Output:** `IMPORT_DOCTRINE.md` + atualização Constituição Anexo F

---

### **FASE 2: CONSOLIDAÇÃO APV** ⏱ 10min
**Objetivo:** Unificar 3 implementações de APV em 1 fonte canônica

#### Steps:
1. **Análise de diferenças:**
   ```bash
   diff backend/services/maximus_eureka/models/apv.py \
        backend/services/maximus_oraculo/models/apv.py
   # Output: idênticos (440 linhas)
   
   diff backend/services/adaptive_immune_system/models/apv.py \
        backend/services/maximus_oraculo/models/apv.py
   # Output: verificar se 230L é subset ou versão divergente
   ```

2. **Migração:**
   ```bash
   # Se idênticos: mover versão canônica
   mv backend/services/maximus_oraculo/models/apv.py \
      backend/shared/models/apv.py
   
   # Criar symlinks de compatibilidade temporária (se necessário para testes legados)
   ln -s ../../../shared/models/apv.py \
         backend/services/maximus_eureka/models/apv.py
   ```

3. **Validação:**
   ```bash
   python -c "from backend.shared.models.apv import APV; print('✅ Import OK')"
   pytest backend/shared/tests/models/test_apv.py -v
   ```

**Bloqueadores potenciais:**
- Se APV de `adaptive_immune_system` diverge → criar `APVLegacy` em shared ou migrar schema

**Output:** `backend/shared/models/apv.py` consolidado + testes migrando

---

### **FASE 3: FIX IMPORTS MASSIVO** ⏱ 20min
**Objetivo:** Substituir 100% dos imports quebrados por padrão canônico

#### Arquivos alvo (maximus_eureka):
```
orchestration/eureka_orchestrator.py
confirmation/vulnerability_confirmer.py
consumers/apv_consumer.py
strategies/strategy_selector.py
strategies/base_strategy.py
strategies/code_patch_llm.py
eureka_models/patch.py
models/confirmation/__init__.py
+ 7 arquivos de testes
```

#### Pattern de substituição:
```python
# ❌ BEFORE (remover)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "maximus_oraculo"))
from models.apv import APV

# ✅ AFTER
from backend.shared.models.apv import APV
```

#### Automação:
```bash
# Script de migração em lote
cat > /tmp/fix_imports.sh << 'EOF'
#!/bin/bash
FILES=$(find backend/services/maximus_eureka -name "*.py" -type f)

for file in $FILES; do
    # Remover sys.path hacks
    sed -i '/sys.path.insert.*maximus_oraculo/d' "$file"
    
    # Substituir import
    sed -i 's|^from models\.apv import|from backend.shared.models.apv import|g' "$file"
    
    # Limpar imports de sys/Path não usados
    ruff check --fix --select F401,F811 "$file"
done

echo "✅ Fix aplicado em $(echo "$FILES" | wc -l) arquivos"
EOF

chmod +x /tmp/fix_imports.sh
bash /tmp/fix_imports.sh
```

**Validação:**
```bash
# Garantir zero sys.path hacks remanescentes
grep -r "sys.path.insert.*oraculo" backend/services/maximus_eureka/
# Output esperado: vazio

# Ruff full check
ruff check backend/services/maximus_eureka/ --select F,E
# Target: 0 F401, 0 F811, < 50 outros erros
```

**Output:** 15 arquivos corrigidos, 0 sys.path hacks

---

### **FASE 4: INFRA DOCKER** ⏱ 15min
**Objetivo:** Configurar PYTHONPATH e build context corretos

#### 4.1 Dockerfile eureka
```dockerfile
# backend/services/maximus_eureka/Dockerfile
FROM vertice/python311-uv:latest AS builder
# ... (manter)

FROM python:3.11-slim
# ... (manter setup inicial)

WORKDIR /app

# ✅ CRITICAL: Copiar backend inteiro (não só serviço)
COPY --chown=appuser:appuser ../../backend /app/backend
COPY --chown=appuser:appuser . /app/backend/services/maximus_eureka

# ✅ PYTHONPATH para imports absolutos
ENV PYTHONPATH="/app:${PYTHONPATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser
WORKDIR /app/backend/services/maximus_eureka

HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8036/health || exit 1

EXPOSE 8036
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8036"]
```

#### 4.2 docker-compose.yml ajuste
```yaml
maximus-eureka:
  build:
    context: ./backend  # ✅ Build context = backend (não serviço individual)
    dockerfile: services/maximus_eureka/Dockerfile
  container_name: maximus-eureka
  environment:
    PYTHONPATH: "/app:/app/backend"  # ✅ Redundância segura
  # ... (manter resto)
```

#### 4.3 Build test
```bash
docker compose build maximus-eureka
# Verificar:
# - COPY sem erros de path
# - Image size razoável (< 500MB)

docker compose up -d maximus-eureka
docker logs maximus-eureka --tail 50
# Esperado: "Application startup complete" (não ModuleNotFoundError)
```

**Bloqueadores potenciais:**
- Build context change pode afetar outros 86 serviços → validar 3-5 serviços representativos primeiro

**Output:** maximus-eureka container healthy

---

### **FASE 5: VALIDAÇÃO SISTÊMICA** ⏱ 30min
**Objetivo:** 100% serviços UP, build verde

#### 5.1 Replicar fix em serviços críticos
**Ordem de prioridade:**
1. `maximus_oraculo` (produtor de APVs)
2. `adaptive_immune_system` (consumidor de APVs)
3. `maximus_core_service` (orchestrador central)
4. Top 10 serviços por dependências (via analysis de imports)

**Para cada serviço:**
```bash
# Template
SERVICE=maximus_oraculo
cd backend/services/$SERVICE

# 1. Fix imports (reuse script Fase 3)
grep -r "sys.path.insert" . | cut -d: -f1 | sort -u  # Identify targets
# Apply fix_imports.sh pattern

# 2. Update Dockerfile (reuse pattern Fase 4)
# 3. Test build
docker compose build $SERVICE
docker compose up -d $SERVICE

# 4. Health check
timeout 60 bash -c "until curl -sf http://localhost:PORT/health; do sleep 2; done"
echo "✅ $SERVICE is healthy"
```

#### 5.2 Build completo
```bash
# Stop tudo
docker compose down

# Build from scratch (paralelo)
docker compose build --parallel

# Up staged (infra → core → services)
docker compose up -d postgres redis qdrant
sleep 10

docker compose up -d maximus-core-service api-gateway
sleep 15

docker compose up -d  # Resto dos serviços
```

#### 5.3 Métricas de sucesso
```bash
# Contar serviços UP
TOTAL=$(docker compose config --services | wc -l)
UP=$(docker compose ps --filter "status=running" --format json | jq -s length)
echo "Status: $UP / $TOTAL UP"

# Target: >= 85% UP (75/87)
# Aceitável: 90% (78/87) = bloqueadores documentados em 9 serviços

# Health checks
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -v "Up (healthy)"
# Target: < 10 serviços sem health check OK
```

#### 5.4 Testes de integração
```bash
# Smoke tests nos endpoints críticos
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8151/health  # Maximus Eureka

# Se kafka UP: testar pipeline APV
# (fora de escopo se infra message broker down)
```

**Output:** Relatório de serviços (UP/DOWN/BLOCKED), logs de falhas

---

## 🚨 CONTINGÊNCIAS

### Se Fase 3 revelar imports cruzados além de APV
**Ação:** Pause e mapeie TODAS as dependências shared:
```bash
# Descobrir todos os imports cross-service
for service in backend/services/*/; do
    echo "=== $(basename $service) ==="
    grep -rh "^from " "$service" | grep -v "^from \." | sort -u
done > /tmp/all_imports.txt

# Identificar imports entre services
grep "backend.services" /tmp/all_imports.txt
```

Criar `backend/shared/models/` para cada model compartilhado ANTES de continuar Fase 3.

### Se Dockerfile context change quebrar 50%+ dos builds
**Rollback plan:**
```bash
git stash  # Salvar mudanças Fase 4
git checkout bc1d3abf~1  # Commit antes do absolute imports massacre

# Reverter apenas imports, manter testes/cobertura
git checkout HEAD -- backend/services/*/tests/
```

**Alternative approach:** Usar `pip install -e` nos Dockerfiles:
```dockerfile
# Em cada Dockerfile
COPY --from=builder /opt/venv /opt/venv
COPY backend/shared /app/backend/shared
RUN pip install -e /app/backend/shared  # Instala shared como package
```

### Se APV models divergirem (adaptive_immune_system ≠ oraculo)
**Schema migration:**
1. Manter ambos models em shared: `APV` (v2) e `APVLegacy` (v1)
2. Adicionar adapter:
   ```python
   # backend/shared/models/apv_adapter.py
   def migrate_v1_to_v2(apv_v1: APVLegacy) -> APV:
       """Migra APV v1 (230L) → v2 (440L)"""
       return APV(
           id=apv_v1.id,
           # ... field mapping
       )
   ```
3. Deprecation timeline: APVLegacy removal em Sprint +2

---

## 📏 MÉTRICAS DE VALIDAÇÃO

### Build Success Criteria
- [ ] `docker compose build` completa sem erros (exit 0)
- [ ] ≥ 75/87 serviços com status `Up (healthy)` após 5min
- [ ] 0 erros de `ModuleNotFoundError` em logs

### Code Quality (Padrão Pagani)
- [ ] `ruff check backend/services/maximus_eureka/ --select F` → 0 erros
- [ ] `mypy backend/services/maximus_eureka/ --strict` → 0 erros
- [ ] `pytest backend/services/maximus_eureka/tests/ -v` → 99%+ passing
- [ ] `grep -r "sys.path.insert\|TODO\|FIXME" backend/services/maximus_eureka/` → 0 matches

### Regression Prevention
- [ ] Coverage mantida ou aumentada: `pytest --cov=backend/services/maximus_eureka --cov-report=json`
- [ ] Benchmarks de imports: `python -m timeit "from backend.shared.models.apv import APV"` < 50ms

---

## ⏱ TIMELINE ESTIMADO

| Fase | Duração | Risco | Bloqueador Crítico? |
|------|---------|-------|---------------------|
| 1. Doutrina | 5min | Baixo | Não |
| 2. Consolidação APV | 10min | Médio | Sim (se schemas divergem) |
| 3. Fix Imports | 20min | Baixo | Não (automável) |
| 4. Infra Docker | 15min | Alto | Sim (context change) |
| 5. Validação | 30min | Médio | Não |
| **TOTAL** | **80min** | - | 2 checkpoints críticos |

**Checkpoint 1:** Fim Fase 2 - Se APV diverge, pause para schema analysis  
**Checkpoint 2:** Fim Fase 4 - Se < 60% builds sucesso, rollback e pivô para pip install approach

---

## 🎯 OUTPUTS FINAIS

1. **IMPORT_DOCTRINE.md** - Anexo à Constituição
2. **backend/shared/models/apv.py** - Fonte única APV
3. **BACKEND_RESURRECTION_REPORT.md** - Métricas finais
4. **docker-compose.yml** + 87 Dockerfiles atualizados
5. **Backend funcional:** ≥75 serviços UP, health checks green

---

**Próximo passo:** Aprovação do Arquiteto-Chefe para iniciar Fase 1.
