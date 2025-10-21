# PLANO DE CORREÇÃO SEGURA - Sem Quebrar Backend

**Data:** 2025-10-18T04:02:00Z  
**Status:** 🎯 ESTRATÉGIA DEFENSIVA

---

## PROBLEMAS IDENTIFICADOS

### Categoria A: EXITED (1 serviço)
```
maximus-eureka (porta 8153)
├─ Erro: "Attribute 'app' not found in module 'main'"
└─ Impacto: BAIXO (serviço discovery, não crítico)
```

### Categoria B: UNHEALTHY (15+ serviços)
```
Serviços com healthcheck falhando:
- maximus_integration_service
- network_monitor_service
- memory_consolidation_service
- narrative_analysis_service
- adaptive_immune_system
- adr_core_service
- ai_immune_system
- atlas_service
- auth_service
- cyber_service
- etc...
```

**Impacto:** MÉDIO (serviços rodando, mas healthcheck falhando)

---

## ESTRATÉGIA DE CORREÇÃO

### PRINCÍPIO: "Primum non nocere" (primeiro, não causar dano)

**Regras de engajamento:**
1. ✅ Sempre validar API Gateway antes e depois de CADA fix
2. ✅ Corrigir um serviço por vez
3. ✅ Se algo quebrar, rollback imediato
4. ✅ Nunca tocar em serviços HEALTHY
5. ✅ Criar backup antes de cada mudança

---

## FASE 1: CORREÇÕES NÃO INVASIVAS (0% risco)

### Fix 1: maximus-eureka (EXITED)
**Problema:** Missing 'app' in main.py  
**Solução:** Verificar e corrigir import/export

**Passos seguros:**
```bash
# 1. Ver estrutura do serviço
ls -la backend/services/maximus_eureka_service/

# 2. Verificar main.py
cat backend/services/maximus_eureka_service/main.py | grep -E "^app|def app"

# 3. Se necessário, adicionar export correto
# (apenas se arquivo existe e está correto)

# 4. Rebuild isolado (não afeta outros)
docker compose build maximus-eureka

# 5. Start isolado
docker compose up -d maximus-eureka

# 6. VALIDAR API GATEWAY
curl http://localhost:8000/health
```

**Rollback:** `docker compose stop maximus-eureka` (não afeta nada)

### Fix 2: Healthchecks falhando
**Problema:** Healthcheck endpoints não respondendo  
**Solução:** Investigar causa-raiz SEM modificar código

**Passos seguros:**
```bash
# 1. Verificar se serviço está REALMENTE rodando
docker compose logs atlas_service --tail=20

# 2. Testar healthcheck manualmente
docker compose exec atlas_service curl -f http://localhost:8109/health || echo "Failed"

# 3. Se falhar, ver porquê
docker compose exec atlas_service ps aux | grep python

# 4. Decisão:
#    - Se serviço OK mas healthcheck ruim → comentar healthcheck
#    - Se serviço quebrado → investigar logs
```

**Rollback:** Nenhum código modificado, apenas diagnóstico

---

## FASE 2: CORREÇÕES MODERADAS (5% risco)

### Fix 3: Ajustar healthchecks muito agressivos

**Problema:** Healthcheck com timeout muito curto  
**Solução:** Aumentar timeout/interval no docker-compose.yml

**Exemplo:**
```yaml
# ANTES (muito agressivo)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8109/health"]
  interval: 10s
  timeout: 5s
  retries: 3

# DEPOIS (mais tolerante)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8109/health"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 60s  # Dá tempo para o serviço iniciar
```

**Impacto:** BAIXO (só afeta quando container reinicia)

**Validação:**
```bash
# Restart apenas o serviço modificado
docker compose up -d atlas_service

# Aguardar 60s
sleep 60

# Verificar health
docker compose ps atlas_service

# VALIDAR API GATEWAY
curl http://localhost:8000/health
```

---

## FASE 3: CORREÇÕES INVASIVAS (10% risco) - APENAS SE NECESSÁRIO

### Fix 4: Corrigir código de serviços quebrados

**APENAS se serviço é crítico E está impedindo operação**

**Pré-requisitos:**
1. ✅ Backup do docker-compose.yml
2. ✅ API Gateway validado HEALTHY
3. ✅ Aprovação explícita do arquiteto

**Procedimento:**
```bash
# 1. Backup
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)

# 2. Fix código
# (apenas o mínimo necessário)

# 3. Build isolado
docker compose build <service>

# 4. Test em container temporário
docker compose run --rm <service> python -c "import main; print('OK')"

# 5. Se OK, deploy
docker compose up -d <service>

# 6. VALIDAR API GATEWAY
curl http://localhost:8000/health

# 7. Se quebrou, ROLLBACK IMEDIATO
docker compose down <service>
cp docker-compose.yml.backup.* docker-compose.yml
docker compose up -d
```

---

## O QUE NÃO FAZER

❌ **NUNCA:**
1. Modificar múltiplos serviços simultaneamente
2. Fazer `docker compose down` (para tudo)
3. Modificar serviços HEALTHY
4. Fazer rebuild de api_gateway sem backup
5. Modificar docker-compose.yml sem backup
6. Fazer mudanças "experimentais"

✅ **SEMPRE:**
1. Validar API Gateway após CADA mudança
2. Fazer backup antes de modificar
3. Corrigir um serviço por vez
4. Ter plano de rollback pronto
5. Documentar cada mudança

---

## PLANO DE EXECUÇÃO PROPOSTO

### Prioridade P0 (fazer primeiro)
1. ✅ Validar API Gateway está UP
2. ⏳ Fix maximus-eureka (baixo risco)
3. ⏳ Diagnóstico de 3 serviços unhealthy (atlas, auth, cyber)

### Prioridade P1 (se P0 OK)
4. ⏳ Ajustar healthchecks muito agressivos (5 serviços)
5. ⏳ Investigar logs de serviços unhealthy

### Prioridade P2 (opcional)
6. ⏳ Fix de serviços não críticos
7. ⏳ Otimização de healthchecks

---

## VALIDAÇÃO CONTÍNUA

Após CADA fix, executar:

```bash
# 1. API Gateway
curl -f http://localhost:8000/health || echo "❌ ROLLBACK!"

# 2. Serviços core
docker compose ps api_gateway redis postgres qdrant

# 3. Count de serviços UP
BEFORE=60
AFTER=$(docker compose ps --format "{{.Service}}" | wc -l)
if [ $AFTER -lt $BEFORE ]; then
  echo "❌ PERDEMOS SERVIÇOS! ROLLBACK!"
fi
```

---

## DECISÃO CONSERVADORA

**Opção 1 (SEGURA):** Deixar unhealthy mas rodando
- Serviços estão funcionando
- Apenas healthcheck falhando
- 0% risco de quebrar

**Opção 2 (MODERADA):** Ajustar apenas healthchecks
- Aumentar timeouts
- Baixo risco (~5%)
- Pode resolver maioria dos unhealthy

**Opção 3 (AGRESSIVA):** Fix de código
- Alto risco (~10%)
- Apenas se serviço é crítico
- Requer aprovação explícita

---

## RECOMENDAÇÃO FINAL

**Para AGORA (04:02h):**
1. ✅ Fix maximus-eureka (serviço único, baixo risco)
2. ✅ Diagnóstico de 3 unhealthy (apenas logs)
3. ✅ Documentar estado atual

**Para DEPOIS (quando tiver tempo):**
4. ⏳ Ajustar healthchecks (um por vez)
5. ⏳ Fix de código (apenas se necessário)

**Resultado esperado:**
- 60 serviços UP (mantido)
- 1 EXITED → RUNNING (maximus-eureka)
- 15 UNHEALTHY → diagnóstico completo
- API Gateway: 100% SAFE

---

**Status:** 🎯 PLANO PRONTO PARA EXECUÇÃO SEGURA  
**Risco:** MÍNIMO (abordagem conservadora)  
**Tempo estimado:** 15-20 minutos  

