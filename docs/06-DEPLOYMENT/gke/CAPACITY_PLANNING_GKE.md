# Capacity Planning - Cluster GKE Vértice

**Data**: 2025-10-25

---

## AUDIT COMPLETO - RECURSOS ATUAIS

### Deployments (pods ativos)

| Service | Replicas | Mem Request | Mem Limit | CPU Request | CPU Limit |
|---------|----------|-------------|-----------|-------------|-----------|
| active-immune-core | 1 | 512Mi | 1Gi | 500m | 1000m |
| adaptive-immune-system | 1 | 512Mi | 1Gi | 500m | 1000m |
| ai-immune-system | 1 | 512Mi | 1Gi | 500m | 1000m |
| api-gateway | 2 | 512Mi | 1Gi | 500m | 1000m |
| auth-service | 2 | 256Mi | 512Mi | 250m | 500m |
| immunis-api-service | 1 | 512Mi | 1Gi | 500m | 1000m |
| maximus-core-service | 1 | 2Gi | 4Gi | 1000m | 2000m |
| maximus-eureka | 1 | 1Gi | 2Gi | 500m | 1000m |
| maximus-oraculo | 1 | 1Gi | 2Gi | 500m | 1000m |
| maximus-orchestrator | 1 | 1Gi | 2Gi | 500m | 1000m |
| maximus-predict | 1 | 1Gi | 2Gi | 500m | 1000m |
| redis | 1 | 256Mi | 512Mi | 250m | 500m |

### StatefulSets

| Service | Containers | Mem Request | Mem Limit | CPU Request | CPU Limit |
|---------|------------|-------------|-----------|-------------|-----------|
| kafka | kafka | 1Gi | 2Gi | 500m | 1000m |
| kafka | zookeeper | 256Mi | 512Mi | 250m | 500m |
| postgres | postgres | 512Mi | 1Gi | 500m | 1000m |

---

## CÁLCULOS TOTAIS

### Memory Requests (garantido pelo scheduler)
```
Deployments:
- active-immune-core:        512Mi
- adaptive-immune-system:    512Mi
- ai-immune-system:          512Mi
- api-gateway (x2):         1024Mi
- auth-service (x2):         512Mi
- immunis-api-service:       512Mi
- maximus-core:             2048Mi
- maximus-eureka:           1024Mi
- maximus-oraculo:          1024Mi
- maximus-orchestrator:     1024Mi
- maximus-predict:          1024Mi
- redis:                     256Mi

StatefulSets:
- kafka:                    1024Mi
- zookeeper:                 256Mi
- postgres:                  512Mi

TOTAL REQUESTS: ~11.3 GB
```

### Memory Limits (máximo que pode usar)
```
Deployments:
- active-immune-core:        1Gi
- adaptive-immune-system:    1Gi
- ai-immune-system:          1Gi
- api-gateway (x2):          2Gi
- auth-service (x2):         1Gi
- immunis-api-service:       1Gi
- maximus-core:              4Gi
- maximus-eureka:            2Gi
- maximus-oraculo:           2Gi
- maximus-orchestrator:      2Gi
- maximus-predict:           2Gi
- redis:                   512Mi

StatefulSets:
- kafka:                     2Gi
- zookeeper:               512Mi
- postgres:                  1Gi

TOTAL LIMITS: ~24.5 GB
```

### Cluster Capacity
```
Total allocatable: 3 nodes × 12.6GB = 37.8 GB
Total requests:    11.3 GB (30% utilization)
Total limits:      24.5 GB (65% utilization)
```

---

## ANÁLISE DE PROBLEMAS

### ❌ Problema 1: Memory Request vs Limit Gap
**Violação de Best Practice do Google**: "Set the same amount of memory for request and limit"

Gaps identificados:
- maximus-core: 2Gi request, 4Gi limit (2x gap) ⚠️ CRÍTICO
- MAXIMUS services: 1Gi request, 2Gi limit (2x gap)
- Immune system: 512Mi request, 1Gi limit (2x gap)
- api-gateway: 512Mi request, 1Gi limit (2x gap)

**Consequência**: 
- Scheduler vê 11.3GB de uso
- Real pode ser até 24.5GB
- Overcommit perigoso!

### ❌ Problema 2: Workers Múltiplos em Containers Pequenos
Confirmado: `active-immune-core` usa `workers=4` com apenas 1Gi de limit.

Cada worker uvicorn:
- Carrega app completo na memória
- 4 workers = ~4x uso de memória
- Com 1Gi limit = ~250MB por worker (MUITO APERTADO)

**Evidência**: Logs mostram "Child process died" - OOMKilled individual do worker

### ✅ Problema 3: Kafka RESOLVIDO
- Era KAFKA_PORT env var do Kubernetes
- Fix aplicado: unset das variáveis conflitantes
- Status: 2/2 Running estável

---

## PROPOSTA DE FIX DEFINITIVO

### Estratégia: Equalizar Requests e Limits (Google Best Practice)

#### Opção A: Conservative (Usar Limits Atuais)
Elevar requests para igualar limits:
- Total requests: 24.5 GB
- Total limits: 24.5 GB
- Utilização: 65% do cluster

**Vantagem**: Sem surpresas, sem OOMKilled
**Desvantagem**: 65% do cluster usado, pouco headroom

#### Opção B: Aggressive (Usar Requests Atuais + Padding)
Reduzir limits para próximo dos requests (com margem de segurança):
- Total requests: 13.5 GB (requests atuais + 20%)
- Total limits: 13.5 GB
- Utilização: 36% do cluster

**Vantagem**: Muito headroom, pode escalar muito mais
**Desvantagem**: Se apps realmente precisam dos limits atuais, vão OOMKill

#### Opção C: Balanced (Meio Termo)
Equalizar no ponto médio + reduzir workers:
- Reduzir workers para 1 em TODOS os serviços
- Requests = Limits = média entre request e limit atuais
- Total: ~18 GB (48% do cluster)

**Vantagem**: Balanceado, menos workers = menos memória real
**Desvantagem**: Requer rebuild de alguns serviços

---

## RECOMENDAÇÃO FINAL

### Fase 1: IMEDIATO (sem rebuild)
1. **Equalizar Requests e Limits** (Opção A conservative)
   - Elevar todos os requests para igualar os limits
   - Sem OOMKilled surprises
   - Deixa cluster em 65% utilization (aceitável)

2. **Escalar DOWN o Sistema Imune temporariamente**
   - Liberar 4GB de limits imediatamente
   - Baixa cluster para ~54% utilization
   - Dá espaço para resto do sistema respirar

### Fase 2: CÓDIGO (rebuild necessário)
1. **Reduzir workers para 1** em:
   - active-immune-core (run.py: workers=4 → 1)
   - Qualquer outro serviço com workers > 1

2. **Rebuild e redeploy** com workers=1
   - Reduz uso real de memória em ~50-75%
   - Permite baixar limits mantendo estabilidade

3. **Re-equalizar** requests/limits com valores menores
   - Target: 12-15GB total (30-40% utilization)
   - Headroom de 60-70% para crescimento

### Fase 3: SCALE UP (quando precisar mais pods)
- Com 60-70% de headroom, cluster aguenta:
  - Dobrar número de pods atuais
  - Ou adicionar novos serviços (RSS, etc)

---

## IMPLEMENTAÇÃO

### Passo 1: Escalar DOWN immune system
```bash
kubectl scale deployment active-immune-core --replicas=0 -n vertice
kubectl scale deployment adaptive-immune-system --replicas=0 -n vertice
kubectl scale deployment ai-immune-system --replicas=0 -n vertice
kubectl scale deployment immunis-api-service --replicas=0 -n vertice
```

### Passo 2: Equalizar Requests e Limits (MAXIMUS + Core Services)
Criar patches para cada deployment elevando requests para igualar limits.

### Passo 3: Fix Workers (Código)
Editar `backend/services/active_immune_core/run.py`:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8200, workers=1)  # was 4
```

### Passo 4: Rebuild e Redeploy
- Build novas imagens
- Push para Artifact Registry
- Update deployments com novas imagens

### Passo 5: Scale UP com configs otimizadas
- Reduzir limits para ~512-768Mi (agora com 1 worker)
- Equalizar requests = limits
- Scale up immune system

---

## VALIDAÇÃO COM USUÁRIO

**Perguntas para decisão**:

1. **Estratégia imediata**: Opção A (conservative, requests = limits atuais)?
   - Pro: Sem OOMKilled, funciona agora
   - Con: 65% do cluster usado

2. **Sistema Imune**: Escalar para 0 temporariamente enquanto otimizamos?
   - Libera 4GB imediatamente
   - Permite resto do sistema estabilizar

3. **Rebuild obrigatório**: OK fazer rebuild para reduzir workers?
   - Necessário para fix definitivo
   - Reduz uso real de memória em 50-75%

4. **Adicionar nodes**: Preferência é otimizar OU escalar cluster?
   - Otimizar: mais trabalho, mas custo $0
   - Escalar: adicionar 1-2 nodes (custo $$$)

