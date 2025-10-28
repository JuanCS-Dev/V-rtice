# Análise Sistêmica Completa - Cluster GKE Vértice

**Data**: 2025-10-25
**Objetivo**: Diagnosticar e resolver instabilidade do cluster com abordagem sistêmica

---

## 1. ESTADO ATUAL DO CLUSTER

### Nodes (3x e2-standard-4)
- **CPU por node**: 4 vCPUs (3920m allocatable)
- **Memory por node**: ~15GB total (~12.6GB allocatable)
- **Total cluster**: 12 vCPUs, ~38GB memory

### Node Utilization (CRÍTICO - OVERCOMMIT)
```
Node chh5: Memory limits  94% (11.9GB/12.6GB) - QUASE CHEIO
Node kcvb: Memory limits  96% (12.1GB/12.6GB) - QUASE CHEIO
Node kpdx: Memory limits 128% (16.6GB/12.6GB) - OVERCOMMITTED!!!
```

**PROBLEMA CRÍTICO**: Node kpdx está com 128% de memory limits alocados!
- Kubernetes permite agendar pods se REQUEST < capacity
- Mas se todos os pods usarem seu LIMIT, o node vai OOMKill

---

## 2. PODS OPERACIONAIS (11 pods 1/1 Running)

| Service | Replicas | Memory Request | Memory Limit | Workers |
|---------|----------|----------------|--------------|---------|
| api-gateway | 2 | ? | ? | ? |
| auth-service | 2 | ? | ? | ? |
| maximus-core-service | 1 | 2Gi | 4Gi | 1 |
| maximus-eureka | 1 | ? | 2Gi | ? |
| maximus-oraculo | 1 | ? | 2Gi | ? |
| maximus-orchestrator | 1 | ? | 2Gi | ? |
| maximus-predict | 1 | ? | 2Gi | ? |
| postgres | 1 | ? | ? | - |
| redis | 1 | ? | ? | - |
| kafka | 1 (2 containers) | 1Gi | 2Gi | - |

**Total conhecido**: ~18Gi em limits apenas nos MAXIMUS

---

## 3. PODS FALHANDO (4 pods - Sistema Imune)

| Service | Status | Restarts | Problema |
|---------|--------|----------|----------|
| active-immune-core | 0/1 Running | 2+ | Child process died |
| adaptive-immune-system | 0/1 Running | 2+ | ? |
| ai-immune-system | 0/1 Running | 2+ | ? |
| immunis-api-service | 0/1 Running | 3+ | Child process died |

**Root Cause Provável**:
- active-immune-core usa `workers=4` hardcoded (mesma issue do MAXIMUS)
- Cluster já está em OVERCOMMIT
- Pods tentam iniciar múltiplos workers, estouram memória, morrem

---

## 4. BEST PRACTICES DO GOOGLE (Pesquisa 2024)

### Memory Management
> **"Set the same amount of memory for the request and limit."**
> - Rationale: Memory cannot be compressed like CPU
> - Prevents OOMKilled surprises

### CPU Management  
> **"For the request, specify the minimum CPU needed, and set an unbounded CPU limit."**
> - Rationale: CPU can be throttled safely
> - Or set limits higher than requests

### Overcommit Warning
> **"When the sum of all container limits exceeds available machine resources, Kubernetes enters an overcommitted state"**
> - CPU: Throttled (safe)
> - Memory: OOMKilled (dangerous)

### CPU:Memory Ratio
> **"Most workloads work best in 1:4 vCPU to Memory ratio"**
> - 1 vCPU = 4GB RAM (default GKE)
> - Different workloads may need different ratios

---

## 5. DIAGNÓSTICO SISTÊMICO

### Problema 1: OVERCOMMIT Perigoso
- Node kpdx com 128% memory limits
- Se todos os pods usarem o limit: OOMKilled garantido
- Solução: Reduzir limits OU adicionar nodes

### Problema 2: Workers Excessivos
- MAXIMUS tinha 4 workers por serviço
- Sistema Imune tem 4 workers (active-immune-core confirmado)
- Cada worker = 1 cópia completa do app na memória
- Solução: 1 worker por pod em produção GKE

### Problema 3: Requests != Limits (anti-pattern)
- Google recomenda requests == limits para memória
- Nosso cluster provavelmente tem gaps grandes
- Scheduler agenda por REQUEST mas processo usa LIMIT
- Solução: Equalizar requests e limits

### Problema 4: Lack of Resource Visibility
- Não sabemos os requests/limits de vários serviços
- Impossível fazer capacity planning correto
- Solução: Auditar TODOS os deployments

---

## 6. PLANO DE AÇÃO DEFINITIVO

### Fase 1: AUDIT (Coleta de Dados)
1. Extrair requests/limits de TODOS os deployments
2. Calcular total de requests e limits
3. Identificar gaps (limits muito maiores que requests)
4. Listar todos os serviços com workers > 1

### Fase 2: STANDARDIZAÇÃO
1. Aplicar padrão Google: `requests.memory == limits.memory`
2. Reduzir workers para 1 em TODOS os serviços
3. Definir CPU:Memory ratio apropriado por tipo de serviço
4. Aplicar health check adequado (start-period >= tempo de init)

### Fase 3: CAPACITY PLANNING
1. Calcular memória total necessária
2. Decidir: otimizar pods OU adicionar nodes
3. Garantir headroom de 20% para spikes

### Fase 4: IMPLEMENTAÇÃO
1. Aplicar mudanças em ordem de dependência
2. Validar cada serviço antes de próximo
3. Monitorar metrics durante rollout

---

## 7. PRÓXIMOS PASSOS IMEDIATOS

1. [ ] Executar audit completo de recursos
2. [ ] Criar planilha de capacity planning
3. [ ] Propor configuração otimizada
4. [ ] Validar com usuário antes de aplicar
5. [ ] Implementar changes de forma controlada

---

**Documentação de Referência**:
- [GKE Resource Requests and Limits Best Practices](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-resource-requests-and-limits)
- [Troubleshoot OOM Events (Google)](https://cloud.google.com/kubernetes-engine/docs/troubleshooting/oom-events)
- [Troubleshoot CrashLoopBackOff (Google)](https://cloud.google.com/kubernetes-engine/docs/troubleshooting/crashloopbackoff-events)
