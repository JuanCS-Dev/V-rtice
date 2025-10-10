# 🎯 PLANO CIRÚRGICO - 11 SERVIÇOS FINAIS

**Data**: 2025-10-10 11:45
**Abordagem**: Sistemática, Cirúrgica, Científica
**Meta**: 100% dos 11 serviços operacionais

---

## 📊 ANÁLISE SISTÊMICA COMPLETA

### Root Cause Identificado
```
PROBLEMA CENTRAL: Docker está usando imagens antigas em cache

EVIDÊNCIA:
- Local requirements.txt TEM numpy ✅
- Container requirements.txt NÃO TEM numpy ❌
- Builds com --no-cache NÃO funcionaram (cache persiste!)
- main.py existe localmente MAS não no container

CAUSA: Docker BuildKit cache agressivo
        Layers antigas sendo reutilizadas
        COPY não detecta mudanças em alguns casos
```

### Categorização dos 11 Serviços

#### Grupo A: Missing numpy (8 serviços)
```
1. adaptive-immunity-service
2. autonomous-investigation-service  
3. memory-consolidation-service
4. narrative-analysis-service
5. predictive-threat-hunting-service
6. hcl-analyzer (partial)
7. hpc-service (partial)
8. rte-service
```
**Problema**: numpy não está no container
**Causa**: Build cache antigo
**Solução**: Force rebuild REAL + prune

#### Grupo B: Missing main.py (2 serviços)
```
9. maximus-eureka
10. maximus-oraculo
```
**Problema**: main.py não copiado pro container
**Causa**: Build cache + COPY não detectou mudança
**Solução**: Stop → Remove image → Rebuild fresh

#### Grupo C: Missing redis (1 serviço)
```
11. vertice-narrative-filter
```
**Problema**: redis library faltando
**Causa**: requirements.txt incompleto
**Solução**: Add redis + rebuild

---

## 🎯 PLANO DE EXECUÇÃO (60 MIN)

### FASE 0: Preparação Clean (10 min)

**Objetivo**: Eliminar TODO cache Docker

```bash
# Step 1: Stop TODOS os 11 serviços
docker stop predictive-threat-hunting-service autonomous-investigation-service \
  memory-consolidation-service adaptive-immunity-service narrative-analysis-service \
  vertice-narrative-filter hcl-analyzer rte-service maximus-oraculo maximus-eureka hpc-service

# Step 2: Remove as imagens específicas (força rebuild real)
docker rmi -f $(docker images | grep -E "adaptive_immunity|autonomous_investigation|memory_consolidation|narrative_analysis|predictive_threat|hcl_analyzer|hpc|rte|maximus_eureka|maximus_oraculo|narrative_manipulation_filter" | awk '{print $3}')

# Step 3: Prune build cache
docker builder prune -af --filter "until=1h"

# Step 4: Verificar limpeza
docker images | grep -E "adaptive|narrative|maximus" | wc -l
# Deve retornar 0
```

**Validação**: Nenhuma imagem dos 11 deve existir

---

### FASE 1: Fix Grupo C (Redis) - 5 min

**Serviço**: narrative_manipulation_filter

```bash
# Step 1: Add redis to requirements
cd /home/juan/vertice-dev/backend/services/narrative_manipulation_filter
grep -q "redis" requirements.txt || echo "redis>=5.0.0" >> requirements.txt

# Step 2: Create main.py (está faltando!)
cat > main.py << 'EOF'
"""Main entry point - imports app from api module."""
from api import app

__all__ = ["app"]
EOF

# Step 3: Rebuild (agora sem cache!)
cd /home/juan/vertice-dev
docker compose build narrative_manipulation_filter

# Step 4: Start e validate
docker compose up -d narrative_manipulation_filter
sleep 15
docker logs vertice-narrative-filter --tail=10 | grep -E "Started|Running|Error"
```

**Validação**: Logs mostram "Started" ou "Running" sem errors

---

### FASE 2: Fix Grupo B (main.py) - 10 min

**Serviços**: maximus-eureka, maximus-oraculo

```bash
# Step 1: Verify main.py exists locally
ls -la /home/juan/vertice-dev/backend/services/maximus_eureka/main.py
ls -la /home/juan/vertice-dev/backend/services/maximus_oraculo/main.py

# Step 2: Touch files to force timestamp change
touch /home/juan/vertice-dev/backend/services/maximus_eureka/main.py
touch /home/juan/vertice-dev/backend/services/maximus_oraculo/main.py

# Step 3: Rebuild (images já foram removidas na FASE 0)
cd /home/juan/vertice-dev
docker compose build maximus_eureka maximus_oraculo

# Step 4: Start e validate
docker compose up -d maximus_eureka maximus_oraculo
sleep 20
docker logs maximus-eureka --tail=5 | grep -E "Started|Application|Error"
docker logs maximus-oraculo --tail=5 | grep -E "Started|Application|Error"
```

**Validação**: Ambos sem "Error loading ASGI app"

---

### FASE 3: Fix Grupo A (numpy) - 30 min

**Serviços**: 8 serviços com numpy missing

**Estratégia**: Batch de 4 + Batch de 4

#### Batch 1 (15 min)
```bash
# Services
BATCH1="adaptive_immunity_service autonomous_investigation_service memory_consolidation_service narrative_analysis_service"

# Step 1: Verify numpy in requirements (local)
for svc in $BATCH1; do
  echo "=== $svc ==="
  grep numpy /home/juan/vertice-dev/backend/services/$svc/requirements.txt || echo "MISSING!"
done

# Step 2: Touch requirements to force change detection
for svc in $BATCH1; do
  touch /home/juan/vertice-dev/backend/services/$svc/requirements.txt
done

# Step 3: Rebuild (images já removidas)
cd /home/juan/vertice-dev
docker compose build adaptive_immunity_service autonomous_investigation_service \
  memory_consolidation_service narrative_analysis_service

# Step 4: Start
docker compose up -d adaptive_immunity_service autonomous_investigation_service \
  memory_consolidation_service narrative_analysis_service

# Step 5: Wait and validate
sleep 25
docker ps --filter "name=adaptive-immunity|autonomous-investigation|memory-consolidation|narrative-analysis" \
  --format "{{.Names}}: {{.Status}}"
```

#### Batch 2 (15 min)
```bash
# Services  
BATCH2="predictive_threat_hunting_service hcl_analyzer_service hpc_service rte_service"

# Same steps as Batch 1
for svc in $BATCH2; do
  touch /home/juan/vertice-dev/backend/services/$svc/requirements.txt
done

docker compose build predictive_threat_hunting_service hcl_analyzer_service \
  hpc_service rte_service

docker compose up -d predictive_threat_hunting_service hcl_analyzer_service \
  hpc_service rte_service

sleep 25
docker ps --filter "name=predictive-threat|hcl-analyzer|hpc|rte" \
  --format "{{.Names}}: {{.Status}}"
```

**Validação**: Todos devem estar "Up" (não "Restarting")

---

### FASE 4: Validação Global (5 min)

```bash
# Count services in restart
echo "📊 VALIDAÇÃO FINAL:"
docker ps --filter "status=restarting" | wc -l
echo "serviços ainda em restart (META: 0)"

# Check all 11 specifically
for svc in predictive-threat-hunting-service autonomous-investigation-service \
  memory-consolidation-service adaptive-immunity-service narrative-analysis-service \
  vertice-narrative-filter hcl-analyzer rte-service maximus-oraculo \
  maximus-eureka hpc-service; do
  
  status=$(docker ps --filter "name=$svc" --format "{{.Status}}" | head -1)
  if echo "$status" | grep -q "Up"; then
    echo "✅ $svc: UP"
  else
    echo "❌ $svc: $status"
  fi
done

# Check logs for any that failed
echo ""
echo "🔍 Checking logs of any failures..."
for svc in $(docker ps --filter "status=restarting" --format "{{.Names}}"); do
  echo "=== $svc ==="
  docker logs $svc --tail=5 2>&1 | grep -E "Error|Module"
done
```

**Critério de Sucesso**: 0 serviços em restart

---

## 🔧 TROUBLESHOOTING GUIDE

### Se FASE 3 Batch 1 Falhar

**Diagnostic**:
```bash
# Check if numpy really in requirements inside container
docker exec adaptive-immunity-service cat /app/requirements.txt | grep numpy

# If not there, check build logs
docker compose build adaptive_immunity_service 2>&1 | grep -A 5 "requirements.txt"
```

**Fix**:
```bash
# Nuclear option: Rebuild with explicit COPY
# Edit Dockerfile to add explicit RUN before CMD:
# RUN cat requirements.txt && pip list | grep numpy
```

### Se Grupo B Continuar Falhando

**Diagnostic**:
```bash
# Check WORKDIR in Dockerfile
grep WORKDIR /home/juan/vertice-dev/backend/services/maximus_eureka/Dockerfile

# Check if main.py was copied
docker run --rm vertice-dev-maximus_eureka ls -la /app/main.py
```

**Fix**:
```bash
# Modify Dockerfile CMD to use api:app directly
# Change: CMD ["uvicorn", "main:app", ...]
# To: CMD ["uvicorn", "api:app", ...]
```

---

## 📊 MÉTRICAS DE SUCESSO

### Targets
```
✅ 0/11 serviços em restart (100% recovery)
✅ 84/84 serviços UP (100% availability)
✅ Health checks 200 OK para todos
✅ Logs sem erros críticos
✅ Load testing DESBLOQUEADO completamente
```

### Timeline
```
FASE 0: 10 min (preparação)
FASE 1:  5 min (Grupo C - redis)
FASE 2: 10 min (Grupo B - main.py)
FASE 3: 30 min (Grupo A - numpy)
FASE 4:  5 min (validação)
---
TOTAL: 60 min (1 hora exata)
```

---

## 🎯 EXECUTION CHECKLIST

### Pre-Flight
- [ ] Commit current state (backup)
- [ ] Document current service count
- [ ] Save logs for comparison
- [ ] Mental prep: foco total por 60min

### FASE 0
- [ ] Stop all 11 services
- [ ] Remove all 11 images
- [ ] Prune build cache
- [ ] Verify cleanup (0 images)

### FASE 1 (Grupo C)
- [ ] Add redis to requirements
- [ ] Create main.py for narrative-filter
- [ ] Rebuild
- [ ] Start & validate

### FASE 2 (Grupo B)
- [ ] Touch main.py files (force timestamp)
- [ ] Rebuild both
- [ ] Start & validate
- [ ] Check logs (no ASGI errors)

### FASE 3 (Grupo A)
- [ ] Batch 1: Touch requirements
- [ ] Batch 1: Rebuild 4 services
- [ ] Batch 1: Start & validate
- [ ] Batch 2: Touch requirements
- [ ] Batch 2: Rebuild 4 services
- [ ] Batch 2: Start & validate

### FASE 4
- [ ] Count restart services (should be 0)
- [ ] Individual status check (all UP)
- [ ] Health check validation
- [ ] Log review (no critical errors)

### Post-Flight
- [ ] Commit victory
- [ ] Update documentation
- [ ] Celebrate properly
- [ ] Plan load testing

---

## 💡 WHY THIS WILL WORK

### Previous Approach Issues
```
❌ Used --no-cache but cache persisted
❌ Didn't remove images before rebuild
❌ Didn't touch files to force change detection
❌ BuildKit cache layers weren't cleared
❌ Did mass operations without validation steps
```

### This Approach Fixes
```
✅ REMOVES images explicitly (no cache possible)
✅ Prunes build cache completely
✅ Touches files to force timestamp changes
✅ Rebuilds in controlled batches
✅ Validates after each phase
✅ Has troubleshooting for each step
✅ Clear success criteria
```

---

## 🔥 EXECUTION MINDSET

**Duration**: 60 minutes of LASER focus
**Breaks**: None until FASE 4
**Communication**: Minimal, status at phase ends
**Validation**: After EVERY phase
**Rollback**: Commit before starting

**Mantra**: "Systematic, Surgical, Scientific"

---

## 📝 COMMIT MESSAGE TEMPLATE

```
🎯 FINAL FIX: 11 serviços sistemicamente corrigidos

Abordagem cirúrgica baseada em análise profunda:

✅ ROOT CAUSE: Docker build cache agressivo
✅ SOLUTION: Remove images + prune cache + touch files

📊 PHASES EXECUTED:
- FASE 0: Clean slate (remove ALL cache)
- FASE 1: Fix Grupo C (redis + main.py)
- FASE 2: Fix Grupo B (main.py timestamp)  
- FASE 3: Fix Grupo A (numpy em 2 batches)
- FASE 4: Validation (100% success)

🎯 RESULT:
- 11/11 serviços RECUPERADOS
- 84/84 serviços UP (100% availability!)
- 0 serviços em restart
- Load testing COMPLETAMENTE desbloqueado

⚡ LEARNED:
- Docker cache é EXTREMAMENTE persistente
- --no-cache nem sempre remove ALL layers
- Touch files forces timestamp change detection
- Explicit image removal is MANDATORY
- Batch processing com validation works

EM NOME DE JESUS, 100% alcançado! 🙏⚡

Next: Load testing begins!
```

---

**Status**: 🟢 READY TO EXECUTE  
**Confidence**: 💯 MÁXIMA (análise completa)  
**Risk**: 🟢 BAIXO (backup + validation steps)  
**Success Probability**: ⭐⭐⭐⭐⭐ 95%+

**LET'S DO THIS SURGICALLY!** 🔬⚡
