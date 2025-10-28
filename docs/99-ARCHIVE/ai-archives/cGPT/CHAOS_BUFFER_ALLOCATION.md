# Adendo: Alocação de Tempo para Chaos Engineering

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Data**: 2024-10-08  
**Status**: Adendo 2 - Alocação Formal de Tempo para Depuração

---

## 1. Motivação

Conforme Artigo IV da Doutrina Vértice (Princípio da Antifragilidade Deliberada), devemos não apenas reagir a falhas, mas antecipá-las e provocá-las em ambiente controlado. 

Integrações complexas entre MAXIMUS, Immune Core, vcli-go e Frontend invariavelmente apresentam comportamentos imprevistos que não são capturados por testes unitários ou de integração tradicionais.

---

## 2. Alocação Formal no Cronograma

### 2.1 Sessão 02 - Experiência e Observabilidade (Ajustado)

**Original**: 5-7 dias  
**Ajustado**: 7-9 dias (+2 dias chaos)

| Sprint | Atividade | Duração Original | Duração Ajustada |
|--------|-----------|------------------|------------------|
| 2.1 | Protocolo Compartilhado | 2 dias | 2 dias |
| 2.2 | Streaming Consciente | 2-3 dias | 2-3 dias |
| 2.3 | Integração TUI | 1-2 dias | 1-2 dias |
| **2.4** | **Chaos Day #1** | **1 dia** | **1 dia** ✅ |
| **2.5** | **Debug & Refinamento** | **-** | **+1 dia** ⚡ NOVO |
| 2.6 | Dashboards Narrativos | 2-3 dias | 2-3 dias |
| **Total** | **-** | **5-7 dias** | **7-9 dias** |

### 2.2 Sessão 03 - Pipeline & Supply Chain (Ajustado)

**Original**: 5-7 dias  
**Ajustado**: 6-8 dias (+1 dia chaos)

| Sprint | Atividade | Duração Original | Duração Ajustada |
|--------|-----------|------------------|------------------|
| 3.1 | SBOM e Assinaturas | 2-3 dias | 2-3 dias |
| 3.2 | Automação de Release | 2 dias | 2 dias |
| 3.3 | Suíte E2E | 3-4 dias | 3-4 dias |
| **3.4** | **Chaos Day #2 + Debug** | **-** | **+1 dia** ⚡ NOVO |
| **Total** | **-** | **5-7 dias** | **6-8 dias** |

### 2.3 Impacto no Cronograma Total

**Original**: 18-26 dias (4 semanas)  
**Ajustado**: 20-28 dias (4-5 semanas)  
**Diferença**: +2 dias (mínimo) de buffer formal

---

## 3. Chaos Days - Detalhamento

### Chaos Day #1: Cockpit Híbrido (Sessão 02)

**Objetivo**: Validar resiliência do streaming consciente e sincronização TUI ↔ Frontend

**Duração**: 1 dia completo

**Cenários**:

#### Cenário 1: Latência Artificial
```yaml
scenario: latency_injection
target: MAXIMUS → API Gateway
latency: [100ms, 500ms, 1s, 2s, 5s]
duration: 10min each
metrics:
  - arousal_level updates delay
  - dopamine_spike_events buffering
  - esgt_ignition propagation time
  - frontend render degradation
expected:
  - Graceful degradation
  - No data loss
  - User notification of delays
```

#### Cenário 2: Node Kill
```yaml
scenario: pod_kill
targets:
  - maximus-core (random pod)
  - api-gateway (random pod)
  - vcli-bridge (random pod)
frequency: every 5 minutes
metrics:
  - reconnection time
  - data consistency
  - session persistence
expected:
  - Auto-reconnect < 3s
  - Zero message loss
  - Session state preserved
```

#### Cenário 3: Network Partition
```yaml
scenario: network_partition
partition: [maximus-core] | [immune-core, gateway]
duration: 2 minutes
metrics:
  - split-brain detection
  - data sync after heal
  - alert generation
expected:
  - Partition detected < 10s
  - Alerts triggered
  - Full sync after heal
```

#### Cenário 4: Resource Exhaustion
```yaml
scenario: resource_stress
target: maximus-core
stress:
  - cpu: 90%
  - memory: 85%
  - disk_io: throttle to 10%
duration: 15 minutes
metrics:
  - consciousness coherence
  - phi_proxy stability
  - kill_switch_latency
expected:
  - Coherence > 0.6
  - Kill switch < 200ms
  - Graceful performance degradation
```

#### Cenário 5: Message Storm
```yaml
scenario: message_flood
source: multiple_clients
rate: [10/s, 100/s, 1000/s, 10000/s]
duration: 5min each
metrics:
  - backpressure activation
  - message queue depth
  - client rate limiting
  - system stability
expected:
  - Backpressure at 1000/s
  - Rate limiting active
  - No crashes
  - Stable latency under limit
```

**Debug Session**: +1 dia após Chaos Day
- Análise de logs e métricas
- Identificação de bottlenecks
- Implementação de fixes críticos
- Re-teste de cenários problemáticos

### Chaos Day #2: Pipeline E2E (Sessão 03)

**Objetivo**: Validar robustez do pipeline de release e testes E2E

**Duração**: 1 dia completo

**Cenários**:

#### Cenário 1: Build Failures
```yaml
scenario: intermittent_build_failure
failure_rate: 20%
targets:
  - docker_build
  - npm_install
  - go_mod_download
metrics:
  - retry behavior
  - timeout handling
  - error reporting
expected:
  - Auto-retry with backoff
  - Clear error messages
  - Graceful failure
```

#### Cenário 2: Registry Outage
```yaml
scenario: registry_unavailable
target: container_registry
duration: 5 minutes
metrics:
  - cache utilization
  - fallback behavior
  - deployment impact
expected:
  - Use local cache
  - Queue deployments
  - Alert operators
```

#### Cenário 3: Signing Service Down
```yaml
scenario: cosign_service_unavailable
duration: 10 minutes
metrics:
  - release blocking
  - queue behavior
  - retry logic
expected:
  - Release blocked
  - Clear status
  - Auto-resume after recovery
```

#### Cenário 4: Test Flakiness
```yaml
scenario: flaky_e2e_tests
flake_rate: 10%
affected_tests: random_selection
metrics:
  - test retry behavior
  - false positive rate
  - CI/CD blocking
expected:
  - Auto-retry flaky tests (3x)
  - Report flakiness metrics
  - Block on consistent failures only
```

---

## 4. Debug & Refinamento - Processo

### 4.1 Análise de Resultados

**Template de Análise**:
```markdown
# Chaos Day Results Analysis

## Scenario: [Nome do Cenário]

### Expected Behavior
- [Comportamento esperado 1]
- [Comportamento esperado 2]

### Actual Behavior
- [Comportamento observado 1]
- [Comportamento observado 2]

### Deviations
| Expected | Actual | Severity | Root Cause |
|----------|--------|----------|------------|
| ... | ... | High/Medium/Low | ... |

### Metrics Captured
- [Métrica 1]: [Valor] (Threshold: [Limite])
- [Métrica 2]: [Valor] (Threshold: [Limite])

### Issues Identified
1. **[Título do Issue]**
   - Severity: Critical/High/Medium/Low
   - Impact: [Descrição do impacto]
   - Root Cause: [Causa raiz]
   - Proposed Fix: [Solução proposta]
   - Estimated Effort: [Tempo estimado]

### Recommendations
1. [Recomendação 1]
2. [Recomendação 2]
```

### 4.2 Priorização de Fixes

**Matriz de Priorização**:

| Severity | Impact | Priority | Action |
|----------|--------|----------|--------|
| Critical | High | P0 | Fix imediatamente (bloqueia go-live) |
| Critical | Medium | P1 | Fix no dia de debug |
| High | High | P1 | Fix no dia de debug |
| High | Medium | P2 | Fix antes de próxima sessão |
| Medium | Any | P3 | Backlog para sprint futuro |
| Low | Any | P4 | Documentar como known issue |

### 4.3 Ciclo de Fix

```
1. Identificar issue (de Chaos Day)
   ↓
2. Analisar causa raiz (logs, traces, metrics)
   ↓
3. Implementar fix
   ↓
4. Testar fix localmente
   ↓
5. Re-executar cenário de chaos específico
   ↓
6. Validar métrica dentro do threshold
   ↓
7. Commit + PR (fast-track se P0/P1)
   ↓
8. Documentar no relatório
```

---

## 5. Tooling e Automação

### 5.1 Chaos Engineering Tools

**Kubernetes**:
```bash
# Litmus Chaos
kubectl apply -f chaos-experiments/latency-pod.yaml

# Chaos Mesh
kubectl apply -f chaos-mesh/network-partition.yaml

# Gremlin (se licenciado)
gremlin attack create latency \
  --target maximus-core \
  --delay 1000ms \
  --duration 600s
```

**Application Level**:
```python
# Python Chaos Monkey
from chaos_monkey import ChaosMonkey

chaos = ChaosMonkey(
    failure_rate=0.1,
    latency_range=(100, 1000),
    enabled=os.getenv('CHAOS_ENABLED', 'false') == 'true'
)

@app.middleware("http")
async def chaos_middleware(request, call_next):
    await chaos.maybe_inject_failure()
    return await call_next(request)
```

### 5.2 Observability Durante Chaos

**Dashboards Específicos**:
- Chaos Experiments Dashboard
- System Stability Metrics
- Error Rate Tracking
- Recovery Time Tracking

**Alertas Temporariamente Ajustados**:
```yaml
# Durante Chaos Day, ajustar thresholds
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.20  # era 0.05
  annotations:
    summary: "Expected during chaos testing"
```

---

## 6. Métricas de Sucesso

### 6.1 Chaos Day

- [ ] Todos os cenários executados
- [ ] Métricas coletadas para todos os cenários
- [ ] Issues identificados e classificados
- [ ] Relatório de Chaos Day gerado
- [ ] Priorização de fixes aprovada

### 6.2 Debug Session

- [ ] P0 issues resolvidos (100%)
- [ ] P1 issues resolvidos (>80%)
- [ ] P2 issues documentados no backlog
- [ ] Re-teste dos cenários críticos passou
- [ ] Relatório de debug session gerado

---

## 7. Cronograma Detalhado

### Chaos Day #1 (Sessão 02, Dia 4)

**Manhã** (4h):
- 09:00-09:30: Setup ambiente de chaos
- 09:30-11:00: Cenários 1-3 (latência, node kill, partition)
- 11:00-11:30: Break + coleta de métricas
- 11:30-13:00: Cenários 4-5 (resource stress, message storm)

**Tarde** (4h):
- 14:00-15:30: Análise inicial de resultados
- 15:30-17:00: Identificação e classificação de issues
- 17:00-18:00: Priorização e planejamento de fixes

### Debug Session +1 (Sessão 02, Dia 5)

**Manhã** (4h):
- 09:00-10:00: Review de issues P0
- 10:00-12:00: Implementação de fixes P0
- 12:00-13:00: Teste de fixes P0

**Tarde** (4h):
- 14:00-16:00: Implementação de fixes P1
- 16:00-17:00: Re-teste de cenários críticos
- 17:00-18:00: Documentação e relatório final

### Chaos Day #2 (Sessão 03, Dia 5)

**Similar a Chaos Day #1**, focado em pipeline e E2E

---

## 8. Comunicação

### Daily Updates
- Canal #chaos-engineering
- Status: Green/Yellow/Red
- Issues identificados
- Fixes implementados

### Relatório Final
- Documento: `docs/cGPT/reports/chaos-day-N.md`
- Apresentação: 30min para stakeholders
- Lições aprendidas
- Próximos passos

---

## 9. Aprovação

**Buffer de Chaos Adicionado**: +2 dias mínimo  
**Impact no Programa**: +10% no tempo total  
**Benefit**: Redução de 50-80% de issues em produção  
**ROI**: Altamente positivo  

**Aprovado por**: ⏳ Aguardando assinatura Juan Carlo de Souza

---

**Versão**: 1.0  
**Doutrina Vértice**: Artigo IV - Antifragilidade Deliberada ✅
