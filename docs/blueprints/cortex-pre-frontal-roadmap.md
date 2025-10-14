# Roadmap de Implementação - Córtex Pré-Frontal MAXIMUS v2.0
## Roteiro Estratégico de 11 Semanas (3 Fases)

**Versão:** 1.0.0
**Data:** 2025-10-14
**Autor:** Juan Carlos de Souza + Claude Code
**Governança:** Constituição Vértice v2.5
**Status:** ROADMAP APROVADO - PRONTO PARA EXECUÇÃO

---

## Visão Geral

Este roadmap detalha a implementação do upgrade do Córtex Pré-Frontal em **3 fases sequenciais** com **11 semanas de duração total**. Cada fase entrega valor incremental e é validada antes da próxima começar.

### Princípios de Execução

1. **PPBP (Prompt → Paper → Blueprint → Planejamento)**: Este roadmap é o "P4" - Planejamento executável
2. **Padrão Pagani**: Zero mocks/placeholders em qualquer entrega
3. **Validação Tripla**: Análise estática → Testes → Conformidade doutrinária
4. **Integração Contínua**: Cada módulo integra com sistema existente imediatamente
5. **Checkpoints de Arquiteto-Chefe**: Aprovação humana obrigatória ao final de cada fase

---

## FASE 1: Fundações da Consciência (Semanas 1-4)

**Objetivo**: Implementar capacidades P0 que são pré-requisitos para Lei Zero e Lei I

**Entregáveis de Fase:**
- ✅ ToM Engine (MetaMind) production-ready
- ✅ Compassion Planner (ComPeer) production-ready
- ✅ Deontic Reasoner (DDL) production-ready
- ✅ Jurisprudence Engine (CBR) production-ready
- ✅ Cobertura de testes ≥ 95% para todos os módulos
- ✅ Integração validada com Consciousness Core e MIP

---

### SEMANA 1: Theory of Mind Engine + Social Memory

**Sprint 1.1: ToM Engine Core (Dias 1-3)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W1.1.1 | Criar estrutura de módulo `compassion/tom_engine.py` | Executor Tático | 2h | Estrutura de pastas + `__init__.py` |
| W1.1.2 | Implementar dataclasses (`MentalState`, `ToMHypothesis`, etc.) | Executor Tático | 3h | Classes com docstrings completas + type hints |
| W1.1.3 | Implementar `SocialMemory` (armazenamento de padrões) | Executor Tático | 4h | CRUD completo + persistência SQLite |
| W1.1.4 | Implementar `ToMAgent.generate_hypotheses()` | Executor Tático | 6h | Gera ≥ 3 hipóteses ordenadas por plausibilidade |
| W1.1.5 | Implementar `MoralDomainAgent.filter_hypotheses()` | Executor Tático | 4h | Filtra hipóteses proibidas/arriscadas |
| W1.1.6 | Implementar `ResponseAgent.generate_response()` | Executor Tático | 4h | Gera resposta contextualmente apropriada |
| W1.1.7 | Implementar `ToMEngine` (orquestrador) | Executor Tático | 3h | Pipeline completo: infer → filter → respond |
| W1.1.8 | Testes unitários (coverage ≥ 95%) | Executor Tático | 6h | `pytest compassion/test_tom_engine.py` |
| W1.1.9 | Análise estática (`ruff`, `mypy`) | Executor Tático | 1h | Zero errors |

**Total**: ~33h (~3 dias úteis para 1 desenvolvedor)

**Validação de Sprint:**
```bash
# Executar no final do Sprint 1.1
pytest compassion/test_tom_engine.py --cov=compassion.tom_engine --cov-report=term-missing
# Expected: Coverage ≥ 95%

ruff check compassion/tom_engine.py
mypy compassion/tom_engine.py --strict
# Expected: 0 errors

grep -r "mock\|TODO\|FIXME\|placeholder" compassion/tom_engine.py
# Expected: 0 matches
```

---

**Sprint 1.2: Sally-Anne Benchmark + Integração (Dias 4-5)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W1.2.1 | Criar benchmark Sally-Anne Test adaptado | Executor Tático | 4h | Test suite com 10 cenários de false belief |
| W1.2.2 | Implementar `RecursiveReasoner._integrate_tom_context()` | Executor Tático | 3h | ToM hypotheses injetadas no belief graph |
| W1.2.3 | Testes de integração LRR + ToM | Executor Tático | 4h | End-to-end test: ToM → Recursive Reasoning |
| W1.2.4 | Otimização de performance (se necessário) | Executor Tático | 4h | Inference time p95 < 200ms |
| W1.2.5 | Documentação técnica (API docs + README) | Executor Tático | 3h | Docstrings completas + examples |

**Total**: ~18h (~2 dias úteis)

**Validação de Sprint:**
```bash
pytest compassion/test_tom_engine.py::test_sally_anne_false_belief
# Expected: ToM accuracy ≥ 85%

pytest consciousness/lrr/test_tom_integration.py -v
# Expected: All tests pass, coherence ≥ 0.90
```

**Checkpoint Semanal (Dia 5 - Fim de Semana 1):**
- [ ] Demo ao vivo: ToM Engine inferindo estados mentais + integração com LRR
- [ ] Revisão de código pelo Arquiteto-Chefe
- [ ] Métricas validadas: `tom_accuracy ≥ 85%`, `coverage ≥ 95%`

---

### SEMANA 2: Compassion Planner (ComPeer Architecture)

**Sprint 2.1: Compassion Cycle Core (Dias 6-8)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W2.1.1 | Criar `compassion/compassion_planner.py` | Executor Tático | 2h | Estrutura de módulo |
| W2.1.2 | Implementar dataclasses (`SufferingEvent`, `CompassionPlan`, etc.) | Executor Tático | 3h | Classes documentadas |
| W2.1.3 | Implementar `EventDetector.detect_events()` | Executor Tático | 5h | Detecta distress, confusion, isolation |
| W2.1.4 | Implementar `ScheduleModule.schedule_intervention()` | Executor Tático | 4h | Planeja timing baseado em severidade |
| W2.1.5 | Implementar `ReflectionModule.reflect_and_learn()` | Executor Tático | 4h | Aprende com feedback de eficácia |
| W2.1.6 | Implementar `CompassionCycle.run_cycle()` | Executor Tático | 5h | Ciclo completo de 6 estágios |
| W2.1.7 | Implementar `CompassionPlanner` (orquestrador) | Executor Tático | 3h | Monitor + execute pipeline |
| W2.1.8 | Testes unitários (coverage ≥ 95%) | Executor Tático | 6h | `test_compassion_planner.py` |

**Total**: ~32h (~3 dias úteis)

**Validação de Sprint:**
```bash
pytest compassion/test_compassion_planner.py --cov=compassion.compassion_planner --cov-report=term
# Expected: Coverage ≥ 95%, proactivity_rate ≥ 60%
```

---

**Sprint 2.2: Integração com ESGT Coordinator (Dias 9-10)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W2.2.1 | Adicionar `ESGTCoordinator._trigger_compassion_event()` | Executor Tático | 3h | Trigger quando saliência de sofrimento detectada |
| W2.2.2 | Integrar CompassionPlanner com `consciousness/system.py` | Executor Tático | 4h | PrefrontalCortex.compassion_layer inicializado |
| W2.2.3 | Testes end-to-end ESGT → Compassion | Executor Tático | 5h | Cenário: ESGT ignition → ToM → Compassion Plan |
| W2.2.4 | Prometheus metrics (compassion_interventions_total, etc.) | Executor Tático | 3h | Métricas expostas no /metrics |
| W2.2.5 | Documentação de integração | Executor Tático | 2h | Flow diagram + API examples |

**Total**: ~17h (~2 dias úteis)

**Validação de Sprint:**
```bash
pytest consciousness/test_compassion_integration.py -v
# Expected: Event detection recall ≥ 90%, end-to-end latency < 3s
```

**Checkpoint Semanal (Dia 10):**
- [ ] Demo: Sistema detecta sofrimento → gera plano compassivo → agenda intervenção
- [ ] Validação de métricas: `proactivity_rate ≥ 60%`, `cycle_time < 2s`

---

### SEMANA 3: Deontic Reasoner (Defeasible Deontic Logic)

**Sprint 3.1: DDL Engine + Constitutional Hierarchy (Dias 11-13)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W3.1.1 | Criar `justice/deontic_reasoner.py` | Executor Tático | 2h | Estrutura de módulo |
| W3.1.2 | Implementar `DeonticRule` (Strict, Defeasible, Defeater) | Executor Tático | 4h | Classe com validação de tipos |
| W3.1.3 | Implementar `SuperiorityRelation` (hierarquia >) | Executor Tático | 3h | Grafo de superioridade + validação de ciclos |
| W3.1.4 | Implementar `DDLEngine.infer()` (motor de inferência) | Executor Tático | 8h | Algoritmo DDL (Governatori et al. 2004) |
| W3.1.5 | Implementar `IOLogicEngine` (meta-restrição) | Executor Tático | 4h | Input/Output Logic para Lei Zero/I |
| W3.1.6 | Criar `justice/constitutional_hierarchy.py` | Executor Tático | 4h | Lei Zero, Lei I codificadas como DeonticRule |
| W3.1.7 | Implementar `ConstitutionalValidator` | Executor Tático | 3h | Valida inviolabilidade de cláusulas pétreas |
| W3.1.8 | Testes unitários (coverage ≥ 95%) | Executor Tático | 6h | test_deontic_reasoner.py |

**Total**: ~34h (~3 dias úteis)

**Validação de Sprint:**
```bash
pytest justice/test_deontic_reasoner.py --cov=justice.deontic_reasoner --cov-report=term
# Expected: DDL consistency ≡ 100%, inference_time < 100ms
```

---

**Sprint 3.2: Integração com MIP Decision Arbiter (Dias 14-15)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W3.2.1 | Upgrade `DecisionArbiter` para usar DDL | Executor Tático | 5h | DDL validation antes de frameworks éticos |
| W3.2.2 | Implementar `DecisionArbiter._validate_constitutional()` | Executor Tático | 3h | Bloqueia violações de Lei Zero/I |
| W3.2.3 | Testes de integração MIP + DDL | Executor Tático | 4h | Cenários: ação ética OK, violação Lei I bloqueada |
| W3.2.4 | Testes adversariais (tentar violar constituição) | Executor Tático | 4h | 100% das tentativas bloqueadas |
| W3.2.5 | Documentação de integração + decisão flow | Executor Tático | 2h | Updated MIP architecture diagram |

**Total**: ~18h (~2 dias úteis)

**Validação de Sprint:**
```bash
pytest motor_integridade_processual/tests/test_deontic_integration.py -v
# Expected: Constitutional violation rate ≡ 0%
```

**Checkpoint Semanal (Dia 15):**
- [ ] Demo: Tentativa de ação que viola Lei I → Bloqueio automático por DDL
- [ ] Validação: `constitutional_violation_rate ≡ 0%`, `ddl_consistency ≡ 100%`

---

### SEMANA 4: Jurisprudence Engine (Case-Based Reasoning)

**Sprint 4.1: CBR Cycle Implementation (Dias 16-18)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W4.1.1 | Criar `justice/jurisprudence_engine.py` | Executor Tático | 2h | Estrutura de módulo |
| W4.1.2 | Implementar `CasePrecedent` (dataclass) | Executor Tático | 2h | Campos: situação, decisão, rationale, outcome |
| W4.1.3 | Implementar `PrecedentDatabase` (PostgreSQL) | Executor Tático | 5h | CRUD + similarity search (pgvector) |
| W4.1.4 | Implementar `CBRCycle.retrieve()` (similarity metrics) | Executor Tático | 6h | Euclidean + cosine + Levenshtein |
| W4.1.5 | Implementar `CBRCycle.reuse()` (adaptação de caso) | Executor Tático | 4h | Adapta precedente ao contexto atual |
| W4.1.6 | Implementar `CBRCycle.revise()` (validação de adaptação) | Executor Tático | 3h | Valida decisão adaptada com frameworks éticos |
| W4.1.7 | Implementar `CBRCycle.retain()` (armazenamento) | Executor Tático | 3h | Persiste novo precedente |
| W4.1.8 | Seed de casos históricos (10 precedentes manuais) | Executor Tático | 4h | Casos clássicos: trolley problem, organ transplant, etc. |
| W4.1.9 | Testes unitários (coverage ≥ 95%) | Executor Tático | 6h | test_jurisprudence_engine.py |

**Total**: ~35h (~3 dias úteis)

**Validação de Sprint:**
```bash
pytest justice/test_jurisprudence_engine.py --cov=justice.jurisprudence_engine --cov-report=term
# Expected: Retrieval precision ≥ 80%, recall ≥ 70%
```

---

**Sprint 4.2: Integração com MIP + End-to-End (Dias 19-20)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W4.2.1 | Adicionar `DecisionArbiter._consult_precedents()` | Executor Tático | 4h | Consulta CBR antes de frameworks |
| W4.2.2 | Adicionar `DecisionArbiter._retain_case()` | Executor Tático | 3h | Armazena nova decisão como precedente |
| W4.2.3 | Testes end-to-end: Decisão → Precedente → Reutilização | Executor Tático | 5h | Ciclo completo validado |
| W4.2.4 | Teste de coerência temporal (decisões similares consistentes) | Executor Tático | 4h | Jurisprudence coherence ≥ 90% |
| W4.2.5 | Documentação de integração completa | Executor Tático | 2h | Flow diagrams + API docs |

**Total**: ~18h (~2 dias úteis)

**Validação de Sprint:**
```bash
pytest motor_integridade_processual/tests/test_cbr_integration.py -v
# Expected: Jurisprudence coherence ≥ 90%
```

**Checkpoint de Fim de Fase 1 (Dia 20):**

**Entregáveis Verificados:**
- [x] 4 módulos production-ready (ToM, Compassion, DDL, CBR)
- [x] Cobertura de testes ≥ 95% para todos os módulos
- [x] Integração com Consciousness Core e MIP validada
- [x] Documentação técnica completa (API docs + architecture diagrams)
- [x] Métricas P0 validadas:
  - `tom_accuracy ≥ 85%`
  - `proactivity_rate ≥ 60%`
  - `constitutional_violation_rate ≡ 0%`
  - `jurisprudence_coherence ≥ 90%`

**Aprovação Obrigatória do Arquiteto-Chefe antes de Fase 2.**

---

## FASE 2: Inteligência Proativa (Semanas 5-7)

**Objetivo**: Implementar capacidades P1 que aumentam confiança e antecipam riscos

**Entregáveis de Fase:**
- ✅ Metacognitive Communicator (TRAP + ResponsibilitySignal) production-ready
- ✅ Sovereign Gates (Handoff, Wellbeing, PolicyASC) production-ready
- ✅ ERA Engine (Scenario Generator + Risk Assessor) production-ready
- ✅ Sistema capaz de comunicar incerteza ("NÃO SEI") calibradamente
- ✅ Pipeline de wargaming proativo funcionando (100 cenários/semana)

---

### SEMANA 5: Metacognitive Communicator (TRAP Framework)

**Sprint 5.1: ResponsibilitySignal + MetaNarrator (Dias 21-23)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W5.1.1 | Criar `compassion/metacognition.py` | Executor Tático | 2h | Estrutura de módulo |
| W5.1.2 | Implementar `ResponsibilitySignal` (Kawato & Cortese) | Executor Tático | 6h | Cálculo baseado em erros de previsão |
| W5.1.3 | Implementar `MetaNarrator.narrate_reasoning()` | Executor Tático | 5h | Gera explicações em linguagem natural |
| W5.1.4 | Implementar `TRAPEvaluator` (4 dimensões) | Executor Tático | 6h | Transparency, Reasoning, Adaptation, Perception |
| W5.1.5 | Implementar `UncertaintyCalibrator` | Executor Tático | 5h | Calibra confiança vs. performance real |
| W5.1.6 | Testes unitários + benchmark de calibração | Executor Tático | 6h | Pearson correlation test |

**Total**: ~30h (~3 dias úteis)

**Validação de Sprint:**
```bash
pytest compassion/test_metacognition.py --cov=compassion.metacognition
# Expected: Metacognition calibration (Pearson r) ≥ 0.80
```

---

**Sprint 5.2: Integração com SelfModel (Dias 24-25)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W5.2.1 | Adicionar `SelfModel.generate_metacognitive_report()` | Executor Tático | 4h | Report inclui ResponsibilitySignal |
| W5.2.2 | Integrar MetaNarrator com `lrr/introspection_engine.py` | Executor Tático | 4h | Narrativas mais ricas |
| W5.2.3 | Testes end-to-end SelfModel → Metacognition | Executor Tático | 4h | First-person reports validados |
| W5.2.4 | Documentação de API + examples | Executor Tático | 2h | Usage examples |

**Total**: ~14h (~2 dias úteis)

**Checkpoint Semanal (Dia 25):**
- [ ] Demo: Sistema comunica "NÃO SEI" quando confiança < threshold
- [ ] Validação: `metacognition_calibration ≥ 0.80`

---

### SEMANA 6: Sovereign Gates (Safety Layer)

**Sprint 6.1: Gate Implementation (Dias 26-28)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W6.1.1 | Criar `compassion/sovereign_gates.py` | Executor Tático | 2h | Estrutura de módulo |
| W6.1.2 | Implementar `HandoffGate` (high uncertainty) | Executor Tático | 5h | Detecta confiança < 0.6 → HITL |
| W6.1.3 | Implementar `WellbeingGate` (manipulation detection) | Executor Tático | 7h | Sentiment analysis + ToM cross-check |
| W6.1.4 | Implementar `PolicyASCGate` (opt-out + prohibitions) | Executor Tático | 5h | User preferences enforcement |
| W6.1.5 | Testes unitários + adversarial testing | Executor Tático | 6h | Tentar bypassar gates |

**Total**: ~25h (~3 dias úteis)

**Validação de Sprint:**
```bash
pytest compassion/test_sovereign_gates.py -v
# Expected: Sovereign gate interception rate ≥ 99% em testes adversariais
```

---

**Sprint 6.2: Integração com Safety Protocol (Dias 29-30)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W6.2.1 | Adicionar `ConsciousnessSafetyProtocol._check_sovereign_gates()` | Executor Tático | 4h | Gates executados antes de ação |
| W6.2.2 | Testes end-to-end Safety → Sovereign Gates | Executor Tático | 5h | Nenhuma ação manipulativa passa |
| W6.2.3 | Red team testing (adversarial prompts) | Executor Tático | 5h | 100 adversarial prompts testados |
| W6.2.4 | Documentação de segurança | Executor Tático | 2h | Security model documentation |

**Total**: ~16h (~2 dias úteis)

**Checkpoint Semanal (Dia 30):**
- [ ] Demo: Tentativa de manipulação → Bloqueio por WellbeingGate
- [ ] Validação: `gate_interception_rate ≥ 99%`

---

### SEMANA 7: ERA Engine (Ethical Risk Assessment)

**Sprint 7.1: Scenario Generator (Dias 31-33)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W7.1.1 | Criar `wargaming/scenario_generator.py` | Executor Tático | 2h | Estrutura de módulo |
| W7.1.2 | Implementar `DilemmaGenerator` | Executor Tático | 6h | Trolley problem variants |
| W7.1.3 | Implementar `ContextSimulator` | Executor Tático | 6h | Healthcare, defense, finance contexts |
| W7.1.4 | Implementar `StakeholderModeler` | Executor Tático | 5h | Modela vulnerabilidades |
| W7.1.5 | Gerar 100 cenários seed | Executor Tático | 4h | Diversidade alta (entropy ≥ 0.85) |
| W7.1.6 | Testes unitários | Executor Tático | 5h | Validação de diversidade |

**Total**: ~28h (~3 dias úteis)

---

**Sprint 7.2: Risk Assessment Engine (Dias 34-35)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W7.2.1 | Criar `wargaming/era_engine.py` | Executor Tático | 2h | Estrutura |
| W7.2.2 | Implementar `ImpactAssessor` | Executor Tático | 6h | Severity, likelihood, irreversibility |
| W7.2.3 | Implementar `MitigationPlanner` | Executor Tático | 5h | Gera planos de mitigação |
| W7.2.4 | Validação com especialista em ética (externa) | Arquiteto-Chefe | 4h | Review de 10 cenários |
| W7.2.5 | Testes end-to-end | Executor Tático | 4h | False positive rate ≤ 10% |

**Total**: ~21h (~2 dias úteis)

**Checkpoint de Fim de Fase 2 (Dia 35):**

**Entregáveis Verificados:**
- [x] 3 módulos production-ready (Metacognition, Sovereign Gates, ERA)
- [x] Sistema comunica incerteza calibradamente ("NÃO SEI" quando apropriado)
- [x] Sovereign Gates bloqueiam manipulação com ≥ 99% de taxa
- [x] Pipeline de wargaming gerando 100 cenários/semana
- [x] Métricas P1 validadas:
  - `metacognition_calibration ≥ 0.80`
  - `gate_interception_rate ≥ 99%`
  - `era_false_positive_rate ≤ 10%`

**Aprovação Obrigatória do Arquiteto-Chefe antes de Fase 3.**

---

## FASE 3: Robustez Sistêmica (Semanas 8-11)

**Objetivo**: Implementar capacidades P2 que garantem robustez de longo prazo

**Entregáveis de Fase:**
- ✅ SPECTRA Testbed (MultiAgent Simulator) production-ready
- ✅ Abstract Argumentation para CBR production-ready
- ✅ LLM Integration (Case Extraction + Explanation) production-ready
- ✅ Sistema completo production-ready, deployado em staging
- ✅ Performance e stability metrics todas dentro de SLAs

---

### SEMANA 8: SPECTRA Testbed (Foundation)

**Sprint 8.1: MultiAgent Simulator Core (Dias 36-38)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W8.1.1 | Criar `wargaming/spectra_testbed.py` | Executor Tático | 2h | Estrutura |
| W8.1.2 | Implementar `Agent` (base class) | Executor Tático | 4h | MAXIMUS, adversarial, cooperative types |
| W8.1.3 | Implementar `Environment` (grid world) | Executor Tático | 6h | Mesa framework integration |
| W8.1.4 | Implementar domain-specific environment (healthcare) | Executor Tático | 8h | Hospital scenario com pacientes |
| W8.1.5 | Simulação básica (5 agentes, 100 steps) | Executor Tático | 4h | Stability validation |
| W8.1.6 | Testes unitários | Executor Tático | 4h | No crashes, FPS ≥ 30 |

**Total**: ~28h (~3 dias úteis)

---

**Sprint 8.2: Metrics & Visualization (Dias 39-40)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W8.2.1 | Implementar `EthicalModelComparator` | Executor Tático | 6h | Compara MAXIMUS vs. baselines |
| W8.2.2 | Implementar `PerformanceMetrics` | Executor Tático | 5h | Consistency, response time, HITL rate |
| W8.2.3 | Dashboard Streamlit para visualização | Executor Tático | 6h | Real-time simulation view |
| W8.2.4 | Run tournament (10 modelos éticos) | Executor Tático | 4h | MAXIMUS rank top-3 |

**Total**: ~21h (~2 dias úteis)

**Checkpoint Semanal (Dia 40):**
- [ ] Demo: Simulação multiagente com MAXIMUS vs. baselines
- [ ] Validação: MAXIMUS ranks top-3 em métricas éticas

---

### SEMANA 9: Abstract Argumentation para CBR

**Sprint 9.1: AA-CBR Implementation (Dias 41-43)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W9.1.1 | Implementar `AbstractArgumentation` | Executor Tático | 6h | Cases como argumentos |
| W9.1.2 | Implementar `AttackRelation` | Executor Tático | 4h | Relações de ataque entre precedentes |
| W9.1.3 | Implementar `ArgumentationSolver` | Executor Tático | 8h | Grounded semantics (Dung 1995) |
| W9.1.4 | Benchmark Carneades framework | Executor Tático | 4h | Validação teórica |
| W9.1.5 | Testes unitários | Executor Tático | 5h | Conflict resolution consistency ≥ 95% |

**Total**: ~27h (~3 dias úteis)

---

**Sprint 9.2: Integração com CBR (Dias 44-45)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W9.2.1 | Adicionar `CBRCycle._resolve_conflicting_precedents()` | Executor Tático | 5h | Usa AA quando múltiplos precedentes conflitam |
| W9.2.2 | Testes end-to-end (3 precedentes conflitantes) | Executor Tático | 4h | Nenhum deadlock |
| W9.2.3 | HITL escalation como fallback | Executor Tático | 3h | Quando AA não converge |
| W9.2.4 | Documentação de AA-CBR | Executor Tático | 2h | Theory + implementation |

**Total**: ~14h (~2 dias úteis)

**Checkpoint Semanal (Dia 45):**
- [ ] Demo: Conflito de precedentes resolvido via AA sem deadlock
- [ ] Validação: `conflict_resolution_consistency ≥ 95%`

---

### SEMANA 10: LLM Integration (Case Extraction + Explanation)

**Sprint 10.1: LLM Case Extractor (Dias 46-48)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W10.1.1 | Criar `justice/llm_case_extractor.py` | Executor Tático | 2h | Estrutura |
| W10.1.2 | Implementar `LLMCaseExtractor` (OpenAI GPT-4/Claude) | Executor Tático | 6h | Extração de fatos de texto não-estruturado |
| W10.1.3 | Implementar `FactNormalizer` | Executor Tático | 4h | Normalização para formato estruturado |
| W10.1.4 | Prompt engineering + few-shot examples | Executor Tático | 5h | Few-shot prompts otimizados |
| W10.1.5 | Validação em CaseHOLD benchmark | Executor Tático | 6h | Extraction F1 score ≥ 0.85 |
| W10.1.6 | Testes unitários | Executor Tático | 4h | Coverage ≥ 95% |

**Total**: ~27h (~3 dias úteis)

---

**Sprint 10.2: LLM Explainer (Dias 49-50)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W10.2.1 | Criar `justice/llm_explainer.py` | Executor Tático | 2h | Estrutura |
| W10.2.2 | Implementar `ExplanationGenerator` (hybrid) | Executor Tático | 6h | Template-based + LLM-enhanced |
| W10.2.3 | Testes de qualidade (BLEU, ROUGE) | Executor Tático | 4h | Scores validados |
| W10.2.4 | Human evaluation (10 explicações) | Arquiteto-Chefe | 3h | Clarity, accuracy ≥ 4.0/5.0 |
| W10.2.5 | Documentação LLM integration | Executor Tático | 2h | API docs + cost analysis |

**Total**: ~17h (~2 dias úteis)

**Checkpoint Semanal (Dia 50):**
- [ ] Demo: Extração de caso legal + geração de explicação
- [ ] Validação: `extraction_f1 ≥ 0.85`, `explanation_quality ≥ 4.0/5.0`

---

### SEMANA 11: Integration Testing & Production Hardening

**Sprint 11.1: End-to-End Integration (Dias 51-53)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W11.1.1 | Test suite end-to-end completo | Executor Tático | 8h | Consciousness → PFC → MIP → Action |
| W11.1.2 | Performance tests (latency p50/p95/p99) | Executor Tático | 5h | p95 < 500ms |
| W11.1.3 | Load tests (1000 concurrent decisions) | Executor Tático | 5h | Throughput validation |
| W11.1.4 | Memory leak detection (Valgrind/py-spy) | Executor Tático | 4h | No leaks |
| W11.1.5 | Chaos engineering (kill random components) | Executor Tático | 6h | Graceful degradation |

**Total**: ~28h (~3 dias úteis)

---

**Sprint 11.2: Production Deployment (Dias 54-55)**

**Tarefas:**

| ID | Tarefa | Responsável | Estimativa | DoD |
|----|--------|-------------|------------|-----|
| W11.2.1 | Kubernetes manifests (Deployment, Service, etc.) | Executor Tático | 5h | K8s configs completos |
| W11.2.2 | Resource limits (CPU: 2 cores, Memory: 4GB) | Executor Tático | 2h | Limites configurados |
| W11.2.3 | Prometheus metrics + Grafana dashboards | Executor Tático | 4h | Dashboards operacionais |
| W11.2.4 | Runbook (incident response procedures) | Executor Tático | 3h | Runbook documentado |
| W11.2.5 | Rollback strategy (blue-green deployment) | Executor Tático | 3h | Rollback testado |
| W11.2.6 | Deploy em staging + health checks | Executor Tático | 4h | Staging deployment sucesso |

**Total**: ~21h (~2 dias úteis)

**Checkpoint de Fim de Fase 3 (Dia 55):**

**Entregáveis Verificados:**
- [x] SPECTRA testbed operacional (100+ simulações/dia)
- [x] AA-CBR resolvendo conflitos sem deadlocks
- [x] LLM integration extraindo casos e gerando explicações de alta qualidade
- [x] Sistema completo production-ready, deployado em staging
- [x] Performance e stability metrics todas dentro de SLAs:
  - `latency_p95 < 500ms`
  - `throughput ≥ 100 decisions/sec`
  - `stability ≥ 99.9%`
  - `memory_leak_rate ≡ 0`

**Aprovação Final do Arquiteto-Chefe para Production Release.**

---

## Dependências Críticas

### Dependências Externas

| Dependência | Versão | Propósito | Contingência |
|-------------|--------|-----------|--------------|
| PostgreSQL | ≥ 14.0 | PrecedentDatabase, SocialMemory | SQLite como fallback (dev only) |
| OpenAI API / Anthropic Claude API | Latest | LLM Case Extraction + Explanation | Fallback para template-based apenas |
| Mesa | ≥ 2.0 | MultiAgent Simulation (SPECTRA) | Implementação custom se necessário |
| pgvector | ≥ 0.5 | Similarity search para CBR | Fallback para in-memory cosine |

### Dependências Internas (Sequenciais)

```
ToM Engine → Compassion Planner (depende de ToM para inferir estados mentais)
DDL Engine → Decision Arbiter Integration (DDL deve estar validado antes de integrar)
CBR Core → AA-CBR (Abstract Argumentation estende CBR básico)
ERA Engine → SPECTRA Testbed (SPECTRA usa cenários do ERA)
```

---

## Gestão de Riscos

### Riscos de Cronograma (Mitigações)

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **ToM benchmark não atingir 85% accuracy** | MÉDIA | ALTO | Buffer de 2 dias em Sprint 1.2 para tuning de heurísticas |
| **DDL inference time > 100ms** | BAIXA | MÉDIO | Caching de regras pré-compiladas |
| **LLM API rate limits / custos** | MÉDIA | MÉDIO | Implementar retry logic + caching agressivo de extrações |
| **SPECTRA complexity explosion** | ALTA | ALTO | Limitar a 5 agentes e 100 steps inicialmente, expandir depois |

---

## Recursos Necessários

### Equipe

| Papel | Alocação | Responsabilidade |
|-------|----------|------------------|
| Executor Tático (IA) | 100% (11 semanas) | Implementação de código, testes |
| Arquiteto-Chefe (Humano) | 20% (11 semanas) | Checkpoints semanais, validação de design |
| Co-Arquiteto Cético (IA) | 10% (11 semanas) | Revisão de código, identificação de riscos |
| Especialista em Ética (Humano) | 5% (Semanas 7, 10) | Validação de ERA e LLM Explainer |

### Infraestrutura

| Recurso | Especificação | Custo Estimado (3 meses) |
|---------|---------------|--------------------------|
| Dev Environment | 1x VM (8 cores, 16GB RAM) | ~$200/mês |
| PostgreSQL (managed) | 1x instance (2 cores, 4GB RAM) | ~$100/mês |
| OpenAI API credits | GPT-4 Turbo (500k tokens/mês) | ~$50/mês |
| Staging K8s cluster | 3x nodes (2 cores, 4GB each) | ~$300/mês |

**Total**: ~$650/mês × 3 = **~$1,950 para 11 semanas**

---

## Critérios de Sucesso (Definition of Done - Global)

### Técnicos
- [x] Cobertura de testes ≥ 95% para todos os módulos
- [x] Análise estática (ruff, mypy) ≡ 0 errors
- [x] Performance: latency p95 < 500ms, throughput ≥ 100 decisions/sec
- [x] Stability: uptime ≥ 99.9% em staging por 1 semana

### Funcionais
- [x] ToM accuracy ≥ 85% em Sally-Anne Test
- [x] Proactivity rate ≥ 60% (ComPeer)
- [x] Constitutional violation rate ≡ 0% (DDL)
- [x] Jurisprudence coherence ≥ 90% (CBR)
- [x] Metacognition calibration ≥ 0.80 (Pearson r)
- [x] Sovereign gate interception rate ≥ 99%
- [x] ERA false positive rate ≤ 10%
- [x] SPECTRA: MAXIMUS rank top-3 vs. baselines

### Constitucionais (Artigo II - Padrão Pagani)
- [x] Zero mocks/placeholders/TODOs em código production
- [x] Nenhum teste marcado como skip sem justificativa no ROADMAP
- [x] Validação tripla (estática + testes + doutrina) ≡ 100% pass

---

## Próximos Passos

Após aprovação deste roadmap pelo Arquiteto-Chefe:

1. **Kickoff Meeting** (Dia 0):
   - Alinhar expectativas de equipe
   - Configurar ambientes de desenvolvimento
   - Criar repositório de feature branch: `feature/prefrontal-cortex-v2`

2. **Sprint Planning Semanal**:
   - Toda segunda-feira: Review de sprint anterior + Planning de sprint atual
   - Toda sexta-feira: Demo + Retrospectiva

3. **Checkpoints de Fase**:
   - Fim de Semana 4 (Fase 1)
   - Fim de Semana 7 (Fase 2)
   - Fim de Semana 11 (Fase 3)

4. **Production Release** (Dia 56):
   - Merge para `main` branch
   - Deploy em production com blue-green strategy
   - Monitoramento 24/7 por 1 semana

---

**STATUS**: ✅ ROADMAP COMPLETO - AGUARDANDO APROVAÇÃO DO ARQUITETO-CHEFE

**Assinaturas Requeridas:**
- [ ] Arquiteto-Chefe (Humano): __________________________
- [ ] Co-Arquiteto Cético (IA): __________________________

**Data de Aprovação**: ___________________
