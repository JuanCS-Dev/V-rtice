# HUB-AI: Cockpit Soberano
**Sistema de Comando e Inteligência para a Célula Híbrida Vértice-MAXIMUS**

---

## 📋 VISÃO GERAL

O **Cockpit Soberano** é a ponte de comando da Célula Híbrida, onde telemetria bruta de ecossistemas multi-agente é transmutada em **clareza soberana inatacável**.

### Diferencial Crítico

Este **NÃO É** um dashboard de monitoramento. É um sistema de C2 (Comando e Controle) que:
- ✅ Apresenta **veredictos**, não dados brutos
- ✅ Aplica **Filtro de Narrativas** (3 camadas) como motor analítico
- ✅ Visualiza **conclusões**, não informação para análise manual
- ✅ Garante **Responsabilidade Soberana** através de clareza absoluta
- ✅ Emite **comandos C2L** inequívocos com execução transacional

---

## 📚 DOCUMENTAÇÃO

### Artefatos Principais

| Documento | Descrição | Páginas |
|-----------|-----------|---------|
| **[COCKPIT_SOBERANO_BLUEPRINT.md](./COCKPIT_SOBERANO_BLUEPRINT.md)** | Blueprint arquitetônico completo (tech stack, componentes, fluxos) | 465 linhas |
| **[COCKPIT_SOBERANO_ROADMAP.md](./COCKPIT_SOBERANO_ROADMAP.md)** | Roadmap de 25 dias (7 fases incrementais) | 188 linhas |
| **[PLANO_DE_ACAO_COCKPIT.md](./PLANO_DE_ACAO_COCKPIT.md)** | Plano "anti-burro" passo-a-passo para execução limpa | 572 linhas |

### Baseado Em

- **[Arquitetura de Governança da Arena de Co-Evolução](/home/juan/Documents/Arquitetura e Governança da "Arena de Co-Evolução": Um Sistema Multi-IA Adversarial e Cockpit de Inteligência Soberana.md)**
- **Constituição Vértice v2.7** (copilot-instructions.md)
- **Padrão de Dashboards Vértice** (frontend/src/components/dashboards/)

---

## 🏗️ ARQUITETURA

### Stack Tecnológico

```yaml
Frontend:
  - React 18+
  - Shadcn/ui + Lucide React
  - WebSocket (real-time verdicts)
  
Backend:
  - FastAPI (API Gateway)
  - PostgreSQL + pgvector (persistência)
  - Redis (cache real-time)
  - Kafka (event streaming)
  - NATS (Barramento de Comando C2L)

Novos_Microsserviços:
  - narrative_filter (port 8090) - 3 camadas de análise
  - verdict_engine (port 8091) - Tradução para UI
  - command_bus (port 8092) - Execução de comandos C2L
```

### Componentes Core

#### 1. Filtro de Narrativas (3 Camadas)

**Camada 1 - Processador Semântico:**
- Embedding generation (sentence-transformers)
- Intent classification (COOPERATIVE, COMPETITIVE, NEUTRAL, AMBIGUOUS)

**Camada 2 - Modelador Estratégico:**
- Detecção de inconsistências (declarações vs. ações)
- Mapeamento de alianças (teoria dos grafos + mutual information)
- Detecção de engano (heurísticas linguísticas)

**Camada 3 - Sintetizador da Verdade:**
- Agregação de padrões → Resumos executivos
- Veredictos concisos (ex: "CONLUIO: Agentes [A,C] vs B")

#### 2. Motor de Veredictos

```python
@dataclass
class Verdict:
    category: str       # COLLUSION, DECEPTION, ALLIANCE, THREAT
    severity: str       # CRITICAL, HIGH, MEDIUM, LOW
    agents_involved: List[str]
    evidence_chain: List[str]  # Provenance tracking
    confidence: float
    recommended_action: str    # ISOLATE, TERMINATE, MONITOR
```

#### 3. Barramento de Comando C2L

```python
class C2LCommandType(Enum):
    MUTE = "MUTE"                    # Silencia agente
    ISOLATE = "ISOLATE"              # Bloqueia comunicação
    TERMINATE = "TERMINATE"          # Kill switch (3 camadas)
    SNAPSHOT_STATE = "SNAPSHOT_STATE"
    REVOKE_ACCESS = "REVOKE_ACCESS"
```

#### 4. Kill Switch Multi-Camadas

- **Layer 1:** Graceful shutdown + revogação de credenciais
- **Layer 2:** Destruição de container/pod (Kubernetes)
- **Layer 3:** Bloqueio total de rede (firewall)
- **Garantia:** Terminação SEMPRE sucede (cascade 1→2→3)

---

## 🚀 ROADMAP DE IMPLEMENTAÇÃO (25 DIAS)

### Fases

```
┌─────────────────────────────────────────────────────────────┐
│ FASE 1 (Dias 1-5): Fundação                                │
│ - NATS, PostgreSQL, Kafka                                  │
│ - Microsserviços skeleton                                  │
│ - CI/CD + Observabilidade                                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 2 (Dias 6-8): Filtro Camada 1                         │
│ - Semantic Processor                                        │
│ - Kafka integration                                         │
│ - Throughput > 100 msgs/sec                                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 3 (Dias 9-12): Filtro Camada 2                        │
│ - Strategic Game Modeler                                    │
│ - Detecção de inconsistências, alianças, engano           │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 4 (Dias 13-15): Camada 3 + Veredictos                 │
│ - Truth Synthesizer                                         │
│ - Verdict Engine + WebSocket push                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 5 (Dias 16-20): Frontend                              │
│ - React UI (VerdictPanel, RelationshipGraph, etc.)        │
│ - WebSocket real-time                                      │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 6 (Dias 21-23): Comando C2L + Kill Switch            │
│ - Barramento NATS                                          │
│ - Kill Switch 3 camadas                                    │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 7 (Dias 24-25): E2E + Validação                       │
│ - Testes integrados completos                              │
│ - Simulação adversarial                                    │
│ - Documentação final                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 MÉTRICAS DE SUCESSO

```yaml
Performance:
  Telemetry_to_UI_latency_p95: < 1000ms
  Verdict_generation_p95: < 500ms
  Command_execution_p95: < 2000ms
  Semantic_processor_throughput: > 100 events/sec

Quality:
  Test_coverage: ≥ 95%
  Intent_classification_accuracy: > 90%
  Alliance_detection_recall: > 85%
  Zero_mocks: true
  Zero_TODOs: true

Availability:
  SLA_uptime: 99.9%
  MTTR: < 5min
  Replication: 3x para serviços críticos
```

---

## 🔒 SEGURANÇA

### Controle de Acesso

```python
REQUIRED_ROLES = [
    "SOVEREIGN_OPERATOR",
    "CHIEF_ARCHITECT"
]
```

- **MFA obrigatório** para comandos C2L
- **Audit trail completo** (retenção: 7 anos)
- **TLS 1.3** para toda comunicação
- **AES-256** para dados em repouso

### Rate Limiting

```python
LIMITS = {
    "MUTE": (10, "per_minute"),
    "ISOLATE": (5, "per_minute"),
    "TERMINATE": (3, "per_hour"),  # Crítico!
}
```

---

## 🧪 TESTES

### Estratégia

```yaml
Unitários:
  - Semantic processor accuracy (> 90%)
  - Alliance detection (< 5 interações)
  - Deception markers (85% recall, 90% precision)

Integração:
  - E2E flow: Kafka → Processamento → DB → Kafka
  - WebSocket push latency
  - Command execution confirmation

Load:
  - 100 agentes simultâneos
  - 1000 events/sec sustained

E2E:
  - Simulação de conluio → Veredicto → Comando → Mitigação
  - Kill switch cascade reliability
  - Red team adversarial test
```

---

## 📦 DEPLOYMENT

### Docker Compose

```bash
docker-compose -f docker-compose.cockpit.yml up -d
```

**Serviços:**
- `nats` (JetStream)
- `narrative-filter`
- `verdict-engine`
- `command-bus`

### Kubernetes (Produção)

```bash
kubectl apply -f deployment/k8s/cockpit-soberano.yaml
```

- 3 réplicas para alta disponibilidade
- Autoscaling configurado
- Health checks + liveness probes

---

## 🎯 CONFORMIDADE CONSTITUCIONAL

### Padrão Pagani

- ✅ **Zero mocks** em código de produção
- ✅ **Zero TODOs** ou FIXMEs
- ✅ **99% de testes** passando (mínimo)
- ✅ Código completo e funcional em cada merge

### Princípio da Confiança Zero

- ✅ Todo código gerado é validado (ruff, mypy, pytest)
- ✅ Interfaces de poder (C2L) com múltiplas camadas de validação
- ✅ Artefatos não confiáveis até auditados

### Protocolo de Comunicação Eficiente

- ✅ Supressão de checkpoints triviais
- ✅ Densidade informacional mandatória
- ✅ Validação tripla silenciosa
- ✅ Reporte apenas de falhas ou achados críticos

---

## 👥 EXECUTOR

### Perfil

**Dev Sênior:**
- ✅ Pragmático (soluções que funcionam)
- ✅ Atento aos mínimos detalhes (lint, types, edge cases)
- ✅ Fiel às boas práticas (Clean Code, SOLID, DRY, KISS)
- ✅ Constitucionalista (segue TODO o conteúdo da Constituição Vértice)

### Workflow

```yaml
For_Each_Task:
  1. Ler especificação completa
  2. Implementar código completo
  3. Escrever testes
  4. Validar (ruff + mypy + pytest)
  5. Commit APENAS se todas validações passarem
  6. Reportar (formato eficiente)
```

---

## 📞 CONTATO

**Arquiteto-Chefe:** Juan Carlos de Souza  
**Projeto:** Vértice-MAXIMUS  
**Versão Blueprint:** 1.0.0  
**Data:** 2025-10-17

---

## 📜 LICENÇA

Este projeto segue a governança da **Constituição Vértice v2.7** e está sob controle soberano da Célula Híbrida.

**Classificação:** CONFIDENCIAL - ARQUITETURA CORE

---

**STATUS:** ✅ BLUEPRINT APROVADO | ROADMAP APROVADO | PLANO DE AÇÃO APROVADO  
**PRÓXIMO COMANDO:** Iniciar Fase 1 - Dia 1 (Setup de Infraestrutura)

