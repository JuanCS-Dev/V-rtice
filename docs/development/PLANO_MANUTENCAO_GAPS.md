# 🔧 PLANO DE MANUTENÇÃO - ELIMINAÇÃO DE GAPS

**Data**: 2025-10-26  
**Objetivo**: Eliminar gaps detectados SEM adicionar features  
**Restrições**: Zero custos adicionais, zero quebra de código existente  
**Escopo**: APENAS manutenção corretiva

---

## 📋 GAPS IDENTIFICADOS

### ✅ GAPS JÁ RESOLVIDOS (não tocar)
- Frontend → Backend integration (100% funcional)
- API Gateway routing (operacional)
- LoadBalancer único (arquitetura correta)

### ❌ GAPS CRÍTICOS ATIVOS

| ID | Gap | Impacto | Causa Raiz |
|----|-----|---------|------------|
| **GAP-1** | hitl-patch-service CrashLoop | HITL Dashboard DOWN | PostgreSQL connection failure |
| **GAP-2** | command-bus-service CrashLoop | Command routing degradado | A investigar |
| **GAP-3** | agent-communication CrashLoop | Inter-agent sync degradado | A investigar |
| **GAP-4** | 11 pods em CrashLoop | Funcionalidades parciais | Variadas |

---

## 🎯 METODOLOGIA DE FIX

### Princípios
1. **Diagnóstico antes de ação**: Logs → Causa-raiz → Fix cirúrgico
2. **Um gap por vez**: Fix → Validação → Próximo
3. **Zero impacto**: Não mexer em código funcional
4. **Rollback rápido**: Cada fix deve ser reversível

### Ordem de Execução
1. GAP-1 (CRÍTICO) - HITL service
2. GAP-2 (ALTO) - Command Bus
3. GAP-3 (ALTO) - Agent Communication
4. GAP-4 (MÉDIO) - Demais pods (priorizar por impacto)

---

## 📝 PLANO DE EXECUÇÃO DETALHADO

---

## GAP-1: hitl-patch-service (CRÍTICO)

### Diagnóstico
```bash
# 1. Verificar logs do pod
kubectl logs -n vertice -l app=hitl-patch-service --tail=100

# 2. Verificar secret PostgreSQL
kubectl get secret -n vertice vertice-core-secrets -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d

# 3. Testar conexão PostgreSQL direta
kubectl exec -n vertice postgres-0 -- psql -U vertice -d vertice -c "SELECT 1"

# 4. Verificar env vars do deployment
kubectl get deployment -n vertice hitl-patch-service -o yaml | grep -A 20 "env:"
```

### Possíveis Causas
1. Secret `POSTGRES_PASSWORD` incorreto/corrompido
2. PostgreSQL host/port incorreto (DNS resolution)
3. Database `vertice` não existe
4. User `vertice` sem permissões

### Fix Candidato 1: Validar Secret
```bash
# Se password incorreto:
kubectl get secret -n vertice vertice-core-secrets -o yaml
# Comparar com postgres-0 actual password
kubectl exec -n vertice postgres-0 -- env | grep POSTGRES_PASSWORD
# Se divergir: atualizar secret
```

### Fix Candidato 2: Validar Database
```bash
# Verificar se DB existe
kubectl exec -n vertice postgres-0 -- psql -U postgres -c "\l" | grep vertice
# Se não existir: criar
kubectl exec -n vertice postgres-0 -- psql -U postgres -c "CREATE DATABASE vertice;"
```

### Fix Candidato 3: Validar User
```bash
# Verificar user
kubectl exec -n vertice postgres-0 -- psql -U postgres -c "\du" | grep vertice
# Se não existir: criar
kubectl exec -n vertice postgres-0 -- psql -U postgres -c "CREATE USER vertice WITH PASSWORD 'XXX';"
kubectl exec -n vertice postgres-0 -- psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE vertice TO vertice;"
```

### Ação de Fix
```bash
# Após identificar causa-raiz:
# 1. Aplicar fix específico
# 2. Forçar restart do deployment
kubectl rollout restart deployment/hitl-patch-service -n vertice

# 3. Monitorar restart
kubectl rollout status deployment/hitl-patch-service -n vertice

# 4. Verificar logs
kubectl logs -n vertice -l app=hitl-patch-service --tail=50 -f
```

### Validação de Sucesso
```bash
# Pod deve estar Running
kubectl get pods -n vertice -l app=hitl-patch-service

# Service deve responder
kubectl exec -n vertice -l app=api-gateway -- curl -s http://hitl-patch-service:8027/health
```

### Rollback (se falhar)
```bash
# Não necessário - apenas restart não quebra nada
# Se secret foi alterado e causou problemas:
kubectl apply -f k8s/secrets/vertice-core-secrets.yaml.backup
kubectl rollout restart deployment/hitl-patch-service -n vertice
```

---

## GAP-2: command-bus-service (ALTO)

### Diagnóstico
```bash
# 1. Logs do pod
kubectl logs -n vertice -l app=command-bus-service --tail=100

# 2. Verificar deployment
kubectl describe deployment -n vertice command-bus-service

# 3. Verificar dependências (Redis, Kafka, etc)
kubectl get pods -n vertice -l app=redis
kubectl get pods -n vertice -l app=kafka
```

### Possíveis Causas
1. Redis/Kafka connection failure
2. Missing environment variable
3. Port conflict
4. Resource limits too low

### Ação de Fix
```bash
# Aguardar análise de logs para definir fix específico
# NÃO fazer alterações antes de diagnóstico completo
```

### Validação de Sucesso
```bash
kubectl get pods -n vertice -l app=command-bus-service
# Status: Running, Ready: 1/1
```

---

## GAP-3: agent-communication (ALTO)

### Diagnóstico
```bash
# 1. Logs do pod
kubectl logs -n vertice -l app=agent-communication --tail=100

# 2. Verificar deployment
kubectl describe deployment -n vertice agent-communication
```

### Ação de Fix
```bash
# Aguardar análise de logs para definir fix específico
```

### Validação de Sucesso
```bash
kubectl get pods -n vertice -l app=agent-communication
# Status: Running
```

---

## GAP-4: Demais Pods CrashLoop (11 pods)

### Priorização

| Pod | Prioridade | Justificativa | Dashboard Afetado |
|-----|------------|---------------|-------------------|
| verdict-engine-service | ALTA | Cockpit Soberano crítico | Cockpit |
| hcl-kb-service | MÉDIA | HCL workflows afetados | N/A |
| threat-intel-bridge | MÉDIA | Intel aggregation degradada | N/A |
| memory-consolidation-service | BAIXA | Funcionalidade background | N/A |
| narrative-filter-service | BAIXA | Redundância existe | Cockpit |
| offensive-orchestrator-service | BAIXA | Não usado em prod | Offensive |
| offensive-tools-service (2x) | BAIXA | Redundância | Offensive |
| purple-team | BAIXA | Apenas em wargames | Purple Team |
| tegumentar-service (2x) | BAIXA | Sensory layer opcional | N/A |
| vertice-register | MÉDIA | Service registry backup | N/A |

### Estratégia
1. **ALTA**: Fix após GAP-1/2/3
2. **MÉDIA**: Fix apenas se tempo permitir
3. **BAIXA**: Documentar, não fix (não impactam dashboards principais)

### Metodologia por Pod
```bash
# Para cada pod:
# 1. kubectl logs -n vertice -l app=<pod-name> --tail=100
# 2. Identificar causa-raiz
# 3. Se fix simples (secret, env var): aplicar
# 4. Se fix complexo (código, arquitetura): documentar como KNOWN ISSUE
```

---

## 🚫 O QUE NÃO FAZER

### ❌ PROIBIDO
- Adicionar novos services/deployments
- Modificar código de aplicação (exceto config/env vars)
- Aumentar resources (CPU/Memory) sem justificativa técnica
- Alterar arquitetura de rede (LoadBalancer, Ingress)
- Tocar em pods que estão Running (api-gateway, maximus-core, etc)
- Fazer "melhorias" ou "otimizações"
- Adicionar monitoring/logging novo

### ✅ PERMITIDO
- Corrigir secrets corrompidos
- Ajustar env vars incorretas
- Criar databases/users missing
- Restart de deployments
- Ajustar probes (liveness/readiness) se timeout incorreto
- Corrigir typos em configs

---

## 📊 MÉTRICAS DE SUCESSO

### Targets

| Métrica | Atual | Target | Crítico |
|---------|-------|--------|---------|
| Pods Running | 85/99 (85.9%) | 92/99 (93%) | 90/99 (91%) |
| Dashboards Funcionais | 5/7 (71%) | 7/7 (100%) | 6/7 (86%) |
| CrashLoop Pods | 14 | 7 | 8 |
| Health Score | 87% | 93% | 91% |

### Definição de Sucesso Mínimo (Crítico)
- ✅ HITL Dashboard UP
- ✅ Command-Bus operational
- ✅ Agent-Communication operational
- ✅ ≥6 dashboards 100% funcionais
- ✅ ≥91% pods Running

### Definição de Sucesso Ideal (Target)
- ✅ Todos os dashboards funcionais
- ✅ ≤7 pods CrashLoop (apenas prioridade BAIXA)
- ✅ ≥93% Health Score

---

## 🔄 PROCESSO DE EXECUÇÃO

### Fase 1: Preparação (15min)
```bash
# 1. Backup de secrets atuais
kubectl get secret -n vertice vertice-core-secrets -o yaml > /tmp/secrets-backup.yaml

# 2. Documentar estado atual
kubectl get pods -n vertice > /tmp/pods-before.txt

# 3. Validar acesso kubectl
kubectl cluster-info
```

### Fase 2: GAP-1 (30min)
```bash
# Executar plano GAP-1 completo
# Checkpoint: HITL Dashboard deve estar UP
```

### Fase 3: GAP-2 (30min)
```bash
# Executar plano GAP-2 completo
# Checkpoint: Command-Bus operational
```

### Fase 4: GAP-3 (30min)
```bash
# Executar plano GAP-3 completo
# Checkpoint: Agent-Communication operational
```

### Fase 5: Validação Final (15min)
```bash
# 1. Verificar métricas de sucesso
kubectl get pods -n vertice --field-selector=status.phase=Running | wc -l

# 2. Testar dashboards manualmente
# - MAXIMUS ✅
# - OSINT ✅
# - HITL ✅ (novo)
# - Admin ✅
# - Consciousness ✅

# 3. Documentar resultado
echo "Pods Running: $(kubectl get pods -n vertice --field-selector=status.phase=Running | wc -l)/99" > /tmp/result.txt
```

### Fase 6: Documentação (15min)
```bash
# Atualizar DIAGNOSTIC_SUMMARY.md com novos números
# Criar MAINTENANCE_REPORT_2025-10-26.md
```

---

## ⏱️ TIMELINE ESTIMADO

| Fase | Duração | Horário (BRT) |
|------|---------|---------------|
| Preparação | 15min | 07:30-07:45 |
| GAP-1 Fix | 30min | 07:45-08:15 |
| GAP-2 Fix | 30min | 08:15-08:45 |
| GAP-3 Fix | 30min | 08:45-09:15 |
| Validação | 15min | 09:15-09:30 |
| Documentação | 15min | 09:30-09:45 |
| **TOTAL** | **2h15min** | - |

---

## 📝 CHECKLIST DE EXECUÇÃO

### Antes de Começar
- [ ] Backup de secrets criado
- [ ] Estado atual documentado
- [ ] Kubectl acesso validado
- [ ] Arquiteto-Chefe disponível para aprovações

### Durante Execução
- [ ] GAP-1: Logs analisados
- [ ] GAP-1: Causa-raiz identificada
- [ ] GAP-1: Fix aplicado
- [ ] GAP-1: Validação OK
- [ ] GAP-2: Logs analisados
- [ ] GAP-2: Causa-raiz identificada
- [ ] GAP-2: Fix aplicado
- [ ] GAP-2: Validação OK
- [ ] GAP-3: Logs analisados
- [ ] GAP-3: Causa-raiz identificada
- [ ] GAP-3: Fix aplicado
- [ ] GAP-3: Validação OK

### Após Execução
- [ ] Métricas de sucesso atingidas
- [ ] Todos os dashboards críticos testados
- [ ] Documentação atualizada
- [ ] Relatório de manutenção gerado

---

## 🆘 PLANO DE CONTINGÊNCIA

### Se GAP-1 não resolver após 30min
**AÇÃO**: Documentar como KNOWN ISSUE, prosseguir para GAP-2/3  
**RAZÃO**: Não bloquear outros fixes por 1 pod

### Se algum fix quebrar pod funcional
**AÇÃO**: Rollback imediato
```bash
kubectl rollout undo deployment/<deployment-name> -n vertice
```

### Se Health Score piorar
**AÇÃO**: STOP, rollback de todas as mudanças
```bash
kubectl apply -f /tmp/secrets-backup.yaml
kubectl rollout restart deployment -n vertice --all
```

---

## 📄 ENTREGÁVEIS

1. **MAINTENANCE_REPORT_2025-10-26.md**
   - Gaps resolvidos
   - Gaps não resolvidos (com justificativa)
   - Métricas antes/depois
   - Próximos passos (se houver)

2. **Secrets/Configs corrigidos** (se aplicável)
   - Backup do estado anterior
   - Diff das mudanças

3. **Lista de KNOWN ISSUES** (se houver)
   - Pods que não foram fixados
   - Razão técnica
   - Workaround (se existir)

---

## ✅ CRITÉRIO DE CONCLUSÃO

Manutenção é considerada **COMPLETA** quando:

1. **OBRIGATÓRIO**:
   - ✅ GAP-1 resolvido OU documentado como impossível com justificativa
   - ✅ GAP-2 resolvido OU documentado
   - ✅ GAP-3 resolvido OU documentado
   - ✅ Health Score ≥ 91%
   - ✅ Nenhum pod funcional foi quebrado
   - ✅ Relatório de manutenção gerado

2. **DESEJÁVEL** (não bloqueante):
   - 7/7 dashboards funcionais
   - ≤7 pods CrashLoop
   - Health Score ≥93%

---

**Aprovação necessária do Arquiteto-Chefe antes de iniciar Fase 2 (execução)**

---

**Versão**: 1.0  
**Status**: AGUARDANDO APROVAÇÃO  
**Próximo passo**: Aprovação do Arquiteto-Chefe → Início da Fase 1
