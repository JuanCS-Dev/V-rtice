# Cockpit Soberano - Roadmap de Implementação (25 Dias)

**Versão:** 1.0.0 | **Data:** 2025-10-17  
**Executor:** Dev Sênior configurado conforme Constituição Vértice

---

## ESTRUTURA

**Metodologia:** Incremental e validável  
**Commitment:** Zero mocks, zero TODOs, código nível produção  
**Cobertura:** ≥ 95% | **Latency p95:** <1s (telemetry→UI)

### FASES

1. **Fundação (Dias 1-5):** NATS, PostgreSQL, Kafka, Microsserviços skeleton
2. **Filtro Camada 1 (Dias 6-8):** Semantic Processor + Kafka integration
3. **Filtro Camada 2 (Dias 9-12):** Strategic Game Modeler (inconsistências, alianças, engano)
4. **Filtro Camada 3 + Veredictos (Dias 13-15):** Truth Synthesizer + Verdict Engine
5. **Frontend (Dias 16-20):** React UI + WebSocket
6. **Comando C2L + Kill Switch (Dias 21-23):** Command Bus + 3-layer termination
7. **E2E + Validação (Dias 24-25):** Testes integrados + Simulação adversarial

---

## FASE 1 - FUNDAÇÃO (DIAS 1-5)

### Dia 1: Infraestrutura
- NATS JetStream (subjects: sovereign.commands, sovereign.confirmations)
- PostgreSQL schemas (verdicts, c2l_commands, semantic_representations, etc.)
- Kafka topics (agent-communications, semantic-events, strategic-patterns)
- **Validação:** Health checks, smoke tests

### Dia 2: Microsserviços Skeleton
-  (port 8090)
-  (port 8091)
-  (port 8092)
- **Validação:** Health endpoints OK, testes unitários 100% coverage

### Dia 3: CI/CD + Observabilidade
- GitHub Actions workflow (lint, typecheck, test, coverage)
- Prometheus metrics (semantic_events_processed, processing_latency, etc.)
- Structured logging (JSON)
- **Validação:** CI passa, metrics expostas

### Dias 4-5: Modelos + Repositories
- Pydantic models (SemanticRepresentation, Verdict, C2LCommand)
- SQLAlchemy models + pgvector
- Repositories com CRUD completo
- **Validação:** Testes de integração DB, coverage > 95%

---

## FASE 2 - FILTRO CAMADA 1 (DIAS 6-8)

### Dia 6: Semantic Processor Core
- Embedding generation (sentence-transformers/all-MiniLM-L6-v2)
- Intent classification (COOPERATIVE, COMPETITIVE, NEUTRAL, AMBIGUOUS)
- **Validação:** Embedding 768-dim, intent accuracy > 90%

### Dia 7: Kafka Integration
- TelemetryConsumer (topic: agent-communications)
- Flow: Kafka → Processamento → DB → Kafka (semantic-events)
- **Validação:** E2E flow funcionando

### Dia 8: Performance Tuning
- Batch processing (32 msgs/batch)
- Load testing
- **Validação:** Throughput > 100 msgs/sec, latency < 50ms (p95)

---

## FASE 3 - FILTRO CAMADA 2 (DIAS 9-12)

### Dia 9: Strategic Game Modeler Setup
- Core class structure
- **Deliverable:** Skeleton Camada 2

### Dia 10: Detecção de Inconsistências
- Semantic divergence calculation (cosine distance)
- Comparação declarações atuais vs. histórico
- **Validação:** Detecta contradições com divergence > 0.7

### Dia 11: Mapeamento de Alianças
- Interaction graph (NetworkX)
- Mutual information calculation
- **Validação:** Detecta aliança em < 10 interações

### Dia 12: Detecção de Engano + Integration
- Deception markers (qualificadores, negações duplas, etc.)
- StrategicConsumer (Kafka: semantic-events → strategic-patterns)
- **Validação:** Coverage Camada 2 > 95%

---

## FASE 4 - CAMADA 3 + VEREDICTOS (DIAS 13-15)

### Dia 13: Truth Synthesizer
- Agregação de padrões → Executive summary
- Priorização por severity
- **Deliverable:** Resumos executivos concisos

### Dias 14-15: Verdict Engine
- Tradução summary → Verdict estruturado
- Severity mapping (confidence + impact)
- WebSocket publisher (canal: verdict-stream)
- **Validação:** Latency < 500ms, push funcionando

---

## FASE 5 - FRONTEND (DIAS 16-20)

### Dia 16: Estrutura Base
- Componente raiz CockpitSoberano.jsx
- SovereignHeader
- Routing entre views
- **Deliverable:** Skeleton UI

### Dia 17: VerdictPanel
- VerdictCard (severity colors, confidence bar)
- VerdictTimeline
- useVerdictStream hook (WebSocket)
- **Validação:** Renderiza veredictos real-time

### Dia 18: RelationshipGraph
- Visualização de grafo de agentes (D3.js ou Cytoscape)
- Nodes (agentes), Edges (alianças)
- **Validação:** Grafo interativo atualiza em real-time

### Dia 19: CommandConsole
- CommandBuilder (dropdown: MUTE, ISOLATE, TERMINATE)
- useCommandBus hook (envio de comandos)
- **Validação:** Envio de comando → Receipt

### Dia 20: ProvenanceViewer + Polish
- Visualização de evidence_chain
- Accessibility (WCAG 2.1 AA)
- Testes React (Jest + React Testing Library)
- **Validação:** Cobertura UI > 80%, a11y compliance

---

## FASE 6 - COMANDO C2L + KILL SWITCH (DIAS 21-23)

### Dia 21: Barramento de Comando
- SovereignCommandBus (NATS integration)
- C2LCommand models
- Subscriber na camada de governança
- **Validação:** Comando publicado → Confirmação recebida < 2s

### Dia 22: Kill Switch Multi-Camadas
- Layer 1: Graceful shutdown + credential revocation
- Layer 2: Container/pod destruction (Kubernetes API)
- Layer 3: Network isolation (firewall rules)
- Cascade terminate logic
- **Validação:** Terminação SEMPRE sucede, mesmo com falhas

### Dia 23: Integration Testing
- Test: Veredicto → Comando → Execução → Confirmação
- Test: Kill switch cascade reliability
- **Validação:** Flow completo E2E < 5s

---

## FASE 7 - VALIDAÇÃO FINAL (DIAS 24-25)

### Dia 24: Testes E2E Completos
- Simulação de conluio (2 agentes, 10 trocas)
- Veredicto gerado → UI → Comando → Mitigação
- Load test (100 agentes simultâneos)
- **Validação:** Todas as métricas SLA atingidas

### Dia 25: Simulação Adversarial + Documentação
- Red team test: Agentes tentam enganar o sistema
- Blue team test: Cockpit detecta e mitiga
- Documentação final (API docs, runbooks, troubleshooting)
- **Deliverable:** Sistema 100% operacional, documentado, testado

---

## MÉTRICAS DE SUCESSO



---

**STATUS:** ROADMAP APROVADO  
**PRÓXIMO:** Plano de Ação Detalhado (anti-burro, passo-a-passo)
