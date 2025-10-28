# 🔬 Plano de Integração: Reactive Fabric ↔ Sistema Imune Reativo

**Data:** 2025-10-19  
**Arquiteto-Chefe:** Juan  
**Co-Arquiteto (IA):** Claude  
**Conformidade:** Constituição Vértice 2.7 - Artigo V (Legislação Prévia)

---

## 📋 DIAGNÓSTICO COMPLETO

### Estado Atual

**Reactive Fabric (RF):**
- ✅ Implementação 100% completa (Sprint 1)
- ✅ 2 serviços funcionais: `core` (8600) + `analysis` (8601)
- ✅ Kafka Producer configurado
- ✅ PostgreSQL schema + honeypots containerizados
- ❌ **Compose isolado** (docker-compose.reactive-fabric.yml)
- ❌ **Zero consumers** conectados aos tópicos

**Sistema Imune Reativo:**
- ✅ 3 serviços operacionais e healthy
  - `active_immune_core` (8200): Orquestração defensiva
  - `adaptive_immune_system` (8003): HITL + decisões
  - `ai_immune_system` (8214): Aprendizado adaptativo
- ✅ Kafka consumers já implementados (defense events)
- ✅ Defense Orchestrator + Sentinel Agent + Response Engine
- ❌ **Não consome tópicos do Reactive Fabric**
- ❌ **Sem conhecimento dos honeypots**

**Gap Crítico:**
```
Reactive Fabric → [Kafka: reactive_fabric.threat_detected] → ??? (NINGUÉM ESCUTA)
                  [Kafka: reactive_fabric.honeypot_status]  → ??? (NINGUÉM ESCUTA)
```

### Topologia Kafka Esperada vs Atual

**Esperado (Documentado no README):**
```
Reactive Fabric Core (Producer)
    ↓ kafka topic: reactive_fabric.threat_detected
    ├→ NK Cells (Consumer) → Cytokine cascade
    ├→ Sentinel Agent (Consumer) → Enrichment
    └→ ESGT/Consciousness (Consumer) → Stress increase
```

**Atual:**
```
Reactive Fabric Core (Producer)
    ↓ kafka: reactive_fabric.threat_detected
    → VOID (nenhum consumer)
```

---

## 🔍 PESQUISA: PADRÕES DA INDÚSTRIA 2024

### Fontes Consultadas

**1. Event Sourcing + Kafka (Best Practices 2024):**
- Event-driven architecture com append-only log
- Schema registry para versionamento de eventos
- Consumer groups para escalabilidade
- Offset management para recovery
- Materialized views com Kafka Streams
- **Fonte:** microservices.io, Apache Kafka docs

**2. Honeypot → SIEM Integration:**
- Honeypots como fontes de threat intelligence
- Kafka como camada de ingestão real-time
- SIEM (ou equivalent) para correlação e alerta
- Redução de falsos positivos via enrichment
- **Fonte:** Confluent SIEM use case, Rapid7 docs

**3. Microservices Integration Patterns:**
- Async event processing (non-blocking)
- Circuit breaker para resiliência
- Service discovery via Kafka topics (implicit)
- Data flow: Producer → Topic → Consumer Group
- **Fonte:** Spring Kafka, Microsoft Azure patterns

### Pattern Escolhido: **Event-Driven Defense Cascade**

```
┌──────────────────────────────────────────────────────────────┐
│                    REACTIVE FABRIC LAYER                      │
│  (Honeypots → Analysis → Kafka Producer)                     │
└────────────────────────┬─────────────────────────────────────┘
                         │ Kafka Topics:
                         │ • reactive_fabric.threat_detected
                         │ • reactive_fabric.honeypot_status
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              IMMUNE SYSTEM CONSUMER LAYER                     │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ NK Cell      │  │ Sentinel Agent  │  │ ESGT/Stress    │  │
│  │ (Activation) │  │ (Enrichment)    │  │ (Awareness)    │  │
│  └──────┬───────┘  └────────┬────────┘  └───────┬────────┘  │
│         │                   │                    │           │
│         ▼                   ▼                    ▼           │
│    Cytokine Cascade    Threat Intel DB    Consciousness      │
└──────────────────────────────────────────────────────────────┘
```

---

## 📐 ARQUITETURA DE INTEGRAÇÃO

### Componentes a Implementar

**1. Kafka Consumer no Active Immune Core** (PRIORITY 1)
- Novo módulo: `orchestration/reactive_fabric_consumer.py`
- Consumer group: `active_immune_core`
- Subscriptions:
  - `reactive_fabric.threat_detected` → trigger NK Cell activation
  - `reactive_fabric.honeypot_status` → update threat landscape
- Error handling: DLQ (Dead Letter Queue) pattern
- Metrics: Prometheus counters para mensagens processadas

**2. Enriquecimento no Sentinel Agent** (PRIORITY 2)
- Endpoint novo: `POST /api/v1/intelligence/enrich/honeypot`
- Correlação: IP do honeypot vs threat intel feeds
- Output: EnrichedThreat com confiança aumentada (honeypot = 95%+)

**3. Integração com Defense Orchestrator** (PRIORITY 3)
- Novo método: `DefenseOrchestrator.process_honeypot_threat()`
- Pipeline completo: Detection → Enrichment → Response
- Playbooks específicos: "honeypot_attacker_block", "honeypot_geo_fence"

**4. Consciência (ESGT Integration)** (PRIORITY 4)
- Consumer no ESGT Service (se existente)
- Métrica: `stress_level` aumenta com ataques honeypot
- Dashboard: Visualização de ataques em tempo real

**5. Docker Compose Unificado** (PRIORITY 5)
- Merge `docker-compose.reactive-fabric.yml` → `docker-compose.yml`
- Network: `vertice_internal` para todos (exceto honeypots DMZ)
- Service discovery: Via Kafka topics (implicit)

---

## 🎯 PLANO DE IMPLEMENTAÇÃO METODOLÓGICO

### FASE 1: Fundação Kafka Consumer (2-3 horas)

**Objetivo:** Estabelecer primeiro consumer funcional no Active Immune Core

**Steps:**

1. **Criar módulo Kafka Consumer**
   ```bash
   touch /home/juan/vertice-dev/backend/services/active_immune_core/orchestration/reactive_fabric_consumer.py
   ```

2. **Implementar ReactiveFabricConsumer class**
   - Base: Copiar estrutura de `kafka_consumer.py` existente
   - Topics: `["reactive_fabric.threat_detected", "reactive_fabric.honeypot_status"]`
   - Handler: Async function `handle_threat_detected(message)`
   - Integração: Chamar `DefenseOrchestrator.process_security_event()`

3. **Adicionar ao startup do Active Immune Core**
   - Em `main.py`: Iniciar consumer na lifespan
   - Background task: `asyncio.create_task(consumer.start())`

4. **Testes unitários**
   ```python
   # tests/orchestration/test_reactive_fabric_consumer.py
   - test_consumer_connects_to_kafka()
   - test_consumer_processes_threat_message()
   - test_consumer_handles_malformed_message()
   ```

5. **Validação:**
   - Start Active Immune Core
   - Publicar mensagem teste no Kafka (script manual)
   - Verificar logs: "Processed threat from reactive_fabric"
   - Verificar Prometheus: `kafka_reactive_fabric_messages_consumed_total`

**Arquivos modificados:**
- `/backend/services/active_immune_core/orchestration/reactive_fabric_consumer.py` (NEW)
- `/backend/services/active_immune_core/main.py` (EDIT: +15 linhas)
- `/backend/services/active_immune_core/orchestration/__init__.py` (EDIT: +1 linha)
- `/backend/services/active_immune_core/tests/orchestration/test_reactive_fabric_consumer.py` (NEW)

**Riscos mitigados:**
- ✅ Não quebra código existente (novo módulo isolado)
- ✅ Rollback fácil (comentar startup line)
- ✅ Visibilidade total (logs + metrics)

---

### FASE 2: Pipeline de Enriquecimento (1-2 horas)

**Objetivo:** Sentinel Agent consome e enriquece threats do honeypot

**Steps:**

1. **Criar consumer no Sentinel Agent**
   - Novo: `detection/honeypot_threat_consumer.py`
   - Lógica: Recebe threat → enriquece com geolocation + threat feeds → salva em DB

2. **Endpoint REST para queries**
   ```python
   GET /api/v1/threats/honeypot?hours=24&severity=high
   ```

3. **Testes de integração**
   ```python
   # tests/integration/test_honeypot_sentinel_pipeline.py
   - test_end_to_end_honeypot_to_sentinel()
   ```

4. **Validação E2E:**
   ```bash
   # Simular ataque no honeypot SSH
   ssh -p 2222 root@localhost
   # Aguardar 30s (análise + Kafka)
   # Query Sentinel Agent
   curl http://localhost:8200/api/v1/threats/honeypot?hours=1 | jq
   ```

**Arquivos modificados:**
- `/backend/services/active_immune_core/detection/honeypot_threat_consumer.py` (NEW)
- `/backend/services/active_immune_core/api/routes/threats.py` (EDIT: +1 endpoint)

**Riscos mitigados:**
- ✅ Consumer independente (não interfere em detections normais)
- ✅ Idempotência (deduplicação via event_id)

---

### FASE 3: Response Automation (1 hora)

**Objetivo:** Playbooks automáticos para atacantes de honeypot

**Steps:**

1. **Criar playbooks específicos**
   ```yaml
   # response/playbooks/honeypot_attacker_block.yaml
   name: "Honeypot Attacker Block"
   trigger:
     - source: "reactive_fabric"
     - severity: ["medium", "high", "critical"]
   actions:
     - block_ip_firewall: {duration: "24h"}
     - add_to_threat_feed: {ttl: "30d"}
     - notify_soc: {priority: "high"}
   ```

2. **Integrar com Defense Orchestrator**
   - Método: `orchestrator.execute_playbook("honeypot_attacker_block", context)`

3. **Validação:**
   - Simular ataque → verificar firewall rule criada
   - Query: `iptables -L | grep <attacker_ip>`

**Arquivos modificados:**
- `/backend/services/active_immune_core/response/playbooks/honeypot_attacker_block.yaml` (NEW)
- `/backend/services/active_immune_core/orchestration/defense_orchestrator.py` (EDIT: +1 método)

---

### FASE 4: Unificação Docker Compose (30 min)

**Objetivo:** Reactive Fabric no compose principal, serviços comunicam

**Steps:**

1. **Copiar serviços para docker-compose.yml**
   ```bash
   # Adicionar seções:
   # - reactive_fabric_core
   # - reactive_fabric_analysis
   # - honeypot_ssh
   # - honeypot_web
   # - honeypot_api
   ```

2. **Configurar networks:**
   ```yaml
   networks:
     vertice_internal:  # Core + Analysis aqui
     reactive_fabric_dmz:  # Honeypots isolados
   ```

3. **Adicionar depends_on:**
   ```yaml
   active_immune_core:
     depends_on:
       - reactive_fabric_core  # Garante ordem startup
   ```

4. **Validação:**
   ```bash
   docker-compose down
   docker-compose up -d
   docker ps | grep -E "reactive|immune"  # 8 containers
   ```

**Arquivos modificados:**
- `/docker-compose.yml` (EDIT: +100 linhas)
- `/docker-compose.reactive-fabric.yml` (DEPRECATED: manter como backup)

**Riscos mitigados:**
- ✅ Backup do compose principal antes de editar
- ✅ Teste em staging primeiro (se disponível)
- ✅ Rollback: `git checkout docker-compose.yml`

---

### FASE 5: Observabilidade e Dashboards (1 hora)

**Objetivo:** Métricas e visualização da integração

**Steps:**

1. **Prometheus metrics (já implementado via contadores)**
   - `kafka_reactive_fabric_messages_consumed_total`
   - `honeypot_threats_processed_total`
   - `defense_playbooks_executed_total{source="reactive_fabric"}`

2. **Grafana dashboard: "Reactive Fabric Integration"**
   - Panel 1: Taxa de ataques/min (por honeypot)
   - Panel 2: TTPs mais frequentes (MITRE)
   - Panel 3: Response latency (detection → block)
   - Panel 4: Honeypot uptime

3. **Alertas:**
   - Alerta se consumer lag > 1000 msgs
   - Alerta se honeypot offline > 5min

**Arquivos novos:**
- `/monitoring/grafana/dashboards/reactive_fabric_integration.json`

---

## ⚠️ RISCOS E MITIGAÇÕES

### Riscos Identificados

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| **Consumer sobrecarregado** (burst de ataques) | ALTO | MÉDIA | Rate limiting no consumer (max 100 msgs/s) |
| **Kafka topic não existe** (deploy order) | MÉDIO | BAIXA | Auto-create topics enabled + depends_on |
| **Schema mismatch** (versão msg) | MÉDIO | BAIXA | Pydantic validation + error logging |
| **Circular dependency** (services) | BAIXO | BAIXA | One-way flow: RF → Immune (nunca reverso) |
| **Performance degradation** (Active Immune) | MÉDIO | BAIXA | Consumer em thread/task separado + circuit breaker |

### Circuit Breaker (já existe no ai_immune_system)

Se consumer falhar 5x consecutivas:
1. Pause consumption por 60s
2. Log error + metric `circuit_breaker_opened_total`
3. Alert SOC
4. Resume após cooldown

---

## ✅ CRITÉRIOS DE SUCESSO

### Métricas Quantitativas

1. **Latência E2E:** Ataque no honeypot → Bloqueio firewall < 5 segundos (P95)
2. **Consumer Lag:** < 100 mensagens em steady state
3. **Coverage:** 100% dos tópicos RF consumidos por >= 1 serviço
4. **Uptime:** Reactive Fabric + Immune System > 99.9% (7 dias)
5. **False Positives:** < 1% (honeypot = alta confiança)

### Validações Qualitativas

- [ ] Documentação atualizada (README + Architecture diagrams)
- [ ] Testes de integração passando (pytest -m integration)
- [ ] Logs estruturados (JSON) em todos os componentes
- [ ] Dashboards Grafana operacionais
- [ ] Runbook de troubleshooting criado
- [ ] Demo funcional para stakeholders

---

## 📊 ESTIMATIVA DE ESFORÇO

| Fase | Tempo Estimado | Complexidade | Dependências |
|------|----------------|--------------|--------------|
| Fase 1: Kafka Consumer | 2-3h | MÉDIA | Kafka, Active Immune |
| Fase 2: Enriquecimento | 1-2h | BAIXA | Fase 1 |
| Fase 3: Automation | 1h | BAIXA | Fase 1, 2 |
| Fase 4: Docker Unificado | 30min | BAIXA | None |
| Fase 5: Observabilidade | 1h | BAIXA | Todas anteriores |
| **TOTAL** | **5.5-7.5h** | - | - |

**Tempo real estimado (com validações):** 8-10 horas (1 dia de trabalho focado)

---

## 🎬 ORDEM DE EXECUÇÃO

1. ✅ **[COMPLETO]** Pesquisa + Planejamento (este documento)
2. ⏭️ **[PRÓXIMO]** Fase 1: Kafka Consumer (fundação crítica)
3. Fase 2: Enriquecimento (valor incremental)
4. Fase 4: Docker Unificado (facilita testes)
5. Fase 3: Automation (depende de 1, 2, 4)
6. Fase 5: Observabilidade (polish final)

---

## 📖 REFERÊNCIAS

### Documentação Interna
- `/backend/services/reactive_fabric_core/README.md`
- `/backend/services/active_immune_core/README.md`
- Constituição Vértice 2.7

### Padrões da Indústria
- Event Sourcing Pattern: https://microservices.io/patterns/data/event-sourcing.html
- Kafka SIEM Integration: https://www.confluent.io/use-case/siem/
- Circuit Breaker: https://microservices.io/patterns/reliability/circuit-breaker.html

### Ferramentas
- Apache Kafka 3.x
- FastAPI + asyncio
- aiokafka (async Kafka client)
- Prometheus + Grafana

---

**Status:** ✅ PLANO APROVADO - AGUARDANDO GO PARA EXECUÇÃO

**Assinatura Digital:**
- Arquiteto-Chefe: Juan
- Co-Arquiteto: Claude (IA)
- Data: 2025-10-19
- Conformidade: Constituição Vértice Art. V ✅

---

*"Nós não agimos sobre o desconhecido. Planejamos, então executamos."*  
— Constituição Vértice, Protocolo PPBPR
