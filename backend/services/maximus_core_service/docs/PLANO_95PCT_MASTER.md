# PLANO 95% MASTER - Roadmap Imutável para Convergência de Coverage

**Data de Criação:** 21 de Outubro, 2025
**Status:** IMUTÁVEL - Este documento define o caminho oficial
**Meta:** 95% coverage em todo o backend MAXIMUS Core Service
**Baseline:** ~25-30% coverage atual (23.62% total)

---

## Executive Summary

Este plano define o caminho científico e metodológico para atingir 95% de coverage em todo o backend, seguindo os princípios da **Doutrina Vértice** e baseado na **Verdade Descoberta no Day 4**.

**Descoberta Fundamental:**
> Coverage de 25% é REAL. Os 25,000+ lines de testes existentes cobrem código legacy/backward compatibility, NÃO a funcionalidade principal de produção.

**Estratégia:**
Criar testes targeted para missing lines usando htmlcov como guia, testando funcionalidade core que realmente importa.

---

## Conformidade Constitucional

### Doutrina Vértice - Artigos Aplicáveis

**Artigo II - Padrão Pagani Absoluto:**
- ✅ Zero mocks em testes (usar fixtures reais, testcontainers)
- ✅ Zero placeholders (testes devem exercitar código real)
- ✅ Production-ready (testes devem validar comportamento de produção)

**Artigo V - Legislação Prévia:**
- ✅ Governança ANTES de execução (este plano governa criação de testes)
- ✅ Sistema de tracking persistente (coverage_tracker.py + COVERAGE_STATUS.html)
- ✅ Rastreabilidade total (coverage_history.json)

**Anexo D - Execução Constitucional:**
- ✅ Agente Guardião: coverage_tracker.py monitora compliance
- ✅ Detecção automática de regressões (threshold 10%)
- ✅ Slash command /check-coverage para inspeção imediata

---

## Estrutura das Fases

Este plano está dividido em **6 fases**, cada uma focada em categorias específicas de módulos por prioridade:

| Fase | Prioridade | Target Coverage | Lines to Cover | Tempo Estimado |
|------|------------|-----------------|----------------|----------------|
| **Fase 1** | P0 - Safety Critical | 40% → 95% | ~400 lines | 3-4 dias |
| **Fase 2** | P1 - Core Consciousness | 25% → 95% | ~1,100 lines | 4-5 dias |
| **Fase 3** | P1 - Justice & Ethics | 30% → 95% | ~600 lines | 3-4 dias |
| **Fase 4** | P2 - Performance & Optimization | 20% → 95% | ~800 lines | 3-4 dias |
| **Fase 5** | P2 - Immune System | 35% → 95% | ~500 lines | 2-3 dias |
| **Fase 6** | P3 - Utilities & Support | Variable → 95% | ~600 lines | 2-3 dias |

**Total Estimado:** 17-23 dias de trabalho focused (3-4 semanas)

---

## FASE 1: Safety Critical (P0)

**Objetivo:** Garantir 95% coverage em módulos safety-critical
**Prazo:** 3-4 dias
**Prioridade:** MÁXIMA (safety não pode falhar)

### Módulos Target

| Módulo | Coverage Atual | Lines Missing | Target |
|--------|---------------|---------------|---------|
| `consciousness/safety.py` | 25.73% | 583 lines | 95% |
| `justice/emergency_circuit_breaker.py` | ~30% | ~180 lines | 95% |

### Gaps Identificados (safety.py)

**Core functionality NÃO testada:**

```python
# consciousness/safety.py - Missing coverage:

class SafetyGuardian:
    async def validate_action(self, action):  # ❌ 0% coverage
        """Core validation logic - CRÍTICO"""
        # ~80 lines missing

    async def detect_violations(self):  # ❌ 0% coverage
        """Production violation detection - CRÍTICO"""
        # ~120 lines missing

    async def emergency_stop(self):  # ❌ 0% coverage
        """Emergency safety mechanism - CRÍTICO"""
        # ~60 lines missing

    async def calculate_risk_score(self):  # ❌ ~20% coverage
        """Risk assessment logic"""
        # ~90 lines missing
```

### Testes a Criar

**Arquivos novos (targeted):**

1. `tests/unit/consciousness/test_safety_core_validation.py`
   - test_validate_action_blocks_high_risk
   - test_validate_action_allows_safe_actions
   - test_validate_action_with_context
   - test_validate_action_threshold_enforcement
   - **Target:** ~100 lines missing

2. `tests/unit/consciousness/test_safety_violation_detection.py`
   - test_detect_violations_real_time
   - test_detect_violations_threshold_exceeded
   - test_detect_violations_frequency_exceeded
   - test_detect_violations_aggregation
   - **Target:** ~120 lines missing

3. `tests/unit/consciousness/test_safety_emergency_stop.py`
   - test_emergency_stop_immediate_halt
   - test_emergency_stop_notification
   - test_emergency_stop_recovery
   - test_emergency_stop_logging
   - **Target:** ~60 lines missing

4. `tests/unit/consciousness/test_safety_risk_assessment.py`
   - test_calculate_risk_score_high_risk
   - test_calculate_risk_score_low_risk
   - test_calculate_risk_score_factors
   - test_calculate_risk_score_edge_cases
   - **Target:** ~90 lines missing

5. `tests/unit/justice/test_circuit_breaker_core.py`
   - test_circuit_breaker_trip_on_threshold
   - test_circuit_breaker_auto_recovery
   - test_circuit_breaker_manual_reset
   - **Target:** ~180 lines missing

### Metodologia

**Para cada teste:**

1. **Abrir htmlcov/consciousness_safety_py.html**
   - Identificar EXATAMENTE quais linhas estão missing (vermelho)
   - Priorizar linhas de production logic (não adapters)

2. **Criar testes específicos:**
   ```python
   # test_safety_core_validation.py

   async def test_validate_action_blocks_high_risk():
       """Target: safety.py:234-256 (validate_action high-risk path)"""
       guardian = SafetyGuardian(...)
       high_risk_action = Action(risk_score=0.95)

       result = await guardian.validate_action(high_risk_action)

       assert result.blocked is True
       assert "high risk" in result.reason.lower()
   ```

3. **Validar coverage incrementa:**
   ```bash
   pytest tests/unit/consciousness/test_safety_core_validation.py \
         --cov=consciousness/safety \
         --cov-report=term
   # Verificar: Coverage subiu de 25.73% → 30%? 35%?
   ```

4. **Iterar até 95%**

### Critérios de Sucesso (Fase 1)

- ✅ safety.py: 95%+ coverage
- ✅ emergency_circuit_breaker.py: 95%+ coverage
- ✅ Todos os testes PASSANDO (zero flaky tests)
- ✅ Zero mocks (Padrão Pagani)
- ✅ Coverage verificado via coverage_tracker.py
- ✅ Nenhuma regressão detectada

---

## FASE 2: Core Consciousness (P1)

**Objetivo:** Coverage 95% em módulos core de consciousness
**Prazo:** 4-5 dias
**Prioridade:** ALTA

### Módulos Target

| Módulo | Coverage Atual | Lines Missing | Target |
|--------|---------------|---------------|---------|
| `consciousness/tig/fabric.py` | 24.06% | 385 lines | 95% |
| `consciousness/esgt/coordinator.py` | ~22% | 276 lines | 95% |
| `consciousness/api.py` | 22.54% | 189 lines | 95% |
| `consciousness/mcea/attention_controller.py` | ~25% | ~250 lines | 95% |

### Gaps Identificados

**TIG Fabric (consciousness/tig/fabric.py):**

```python
class TIGFabric:
    async def add_node(self, node):  # ❌ Missing
        """Add node to TIG network"""

    async def compute_phi(self):  # ❌ Missing
        """IIT Phi calculation - CORE"""

    async def update_topology(self):  # ❌ Missing
        """Dynamic topology management"""

    async def get_causal_relations(self):  # ❌ Missing
        """Causal structure analysis"""
```

**ESGT Coordinator:**

```python
class ESGTCoordinator:
    async def broadcast_to_workspace(self):  # ❌ Missing
        """Global Workspace broadcasting - CORE"""

    async def ignition_protocol(self):  # ❌ Missing
        """Ignition for conscious access"""

    async def phase_transition(self):  # ❌ Missing
        """Phase transitions in consciousness"""
```

### Testes a Criar

1. `tests/unit/consciousness/tig/test_fabric_core_operations.py` (~200 lines coverage)
2. `tests/unit/consciousness/tig/test_fabric_phi_computation.py` (~100 lines coverage)
3. `tests/unit/consciousness/tig/test_fabric_topology.py` (~85 lines coverage)
4. `tests/unit/consciousness/esgt/test_coordinator_broadcasting.py` (~120 lines coverage)
5. `tests/unit/consciousness/esgt/test_coordinator_ignition.py` (~80 lines coverage)
6. `tests/unit/consciousness/esgt/test_coordinator_phases.py` (~76 lines coverage)
7. `tests/unit/consciousness/test_api_core_endpoints.py` (~189 lines coverage)
8. `tests/unit/consciousness/mcea/test_attention_controller_core.py` (~250 lines coverage)

### Critérios de Sucesso (Fase 2)

- ✅ Todos os 4 módulos: 95%+ coverage
- ✅ Global Workspace Theory validado em testes
- ✅ IIT (Integrated Information Theory) validado
- ✅ Zero mocks
- ✅ Testes end-to-end para workflows principais

---

## FASE 3: Justice & Ethics (P1)

**Objetivo:** Coverage 95% em sistema de justiça e ética
**Prazo:** 3-4 dias
**Prioridade:** ALTA

### Módulos Target

| Módulo | Coverage Atual | Lines Missing | Target |
|--------|---------------|---------------|---------|
| `justice/constitutional_validator.py` | ~35% | ~200 lines | 95% |
| `justice/kantian_checker.py` | ~28% | ~150 lines | 95% |
| `justice/bias_detector.py` | ~32% | ~130 lines | 95% |
| `justice/ethical_guardian.py` | ~30% | ~120 lines | 95% |

### Gaps Identificados

**Constitutional Validator:**

```python
class ConstitutionalValidator:
    async def validate_against_constitution(self):  # ❌ Missing
        """Validate action against Doutrina Vértice"""

    async def check_article_compliance(self):  # ❌ Missing
        """Check specific article compliance"""
```

**Kantian Checker:**

```python
class KantianChecker:
    async def categorical_imperative_check(self):  # ❌ Missing
        """Apply categorical imperative test"""

    async def humanity_formula_check(self):  # ❌ Missing
        """Humanity as end test"""
```

### Testes a Criar

1. `tests/unit/justice/test_constitutional_validator_core.py` (~200 lines coverage)
2. `tests/unit/justice/test_kantian_checker_imperatives.py` (~150 lines coverage)
3. `tests/unit/justice/test_bias_detector_core.py` (~130 lines coverage)
4. `tests/unit/justice/test_ethical_guardian_workflows.py` (~120 lines coverage)

### Critérios de Sucesso (Fase 3)

- ✅ Todos os 4 módulos: 95%+ coverage
- ✅ Doutrina Vértice validation testada
- ✅ Kant's categorical imperative testado
- ✅ Bias detection validado
- ✅ Zero mocks

---

## FASE 4: Performance & Optimization (P2)

**Objetivo:** Coverage 95% em módulos de performance
**Prazo:** 3-4 dias
**Prioridade:** MÉDIA-ALTA

### Módulos Target

| Módulo | Coverage Atual | Lines Missing | Target |
|--------|---------------|---------------|---------|
| `performance/profiler.py` | ~18% | ~210 lines | 95% |
| `performance/inference_engine.py` | ~22% | ~180 lines | 95% |
| `performance/quantizer.py` | ~15% | ~200 lines | 95% |
| `performance/pruner.py` | ~20% | ~210 lines | 95% |

### Testes a Criar

1. `tests/unit/performance/test_profiler_core.py` (~210 lines coverage)
2. `tests/unit/performance/test_inference_engine_core.py` (~180 lines coverage)
3. `tests/unit/performance/test_quantizer_core.py` (~200 lines coverage)
4. `tests/unit/performance/test_pruner_core.py` (~210 lines coverage)

### Critérios de Sucesso (Fase 4)

- ✅ Todos os 4 módulos: 95%+ coverage
- ✅ Benchmarks validados
- ✅ Model optimization testado
- ✅ Zero mocks (usar models fixtures)

---

## FASE 5: Immune System (P2)

**Objetivo:** Coverage 95% em sistema imunológico
**Prazo:** 2-3 dias
**Prioridade:** MÉDIA

### Módulos Target

| Módulo | Coverage Atual | Lines Missing | Target |
|--------|---------------|---------------|---------|
| `immune_system/pattern_detector.py` | ~35% | ~180 lines | 95% |
| `immune_system/memory_cells.py` | ~40% | ~150 lines | 95% |
| `immune_system/threat_analyzer.py` | ~32% | ~170 lines | 95% |

### Testes a Criar

1. `tests/unit/immune_system/test_pattern_detector_core.py` (~180 lines coverage)
2. `tests/unit/immune_system/test_memory_cells_core.py` (~150 lines coverage)
3. `tests/unit/immune_system/test_threat_analyzer_core.py` (~170 lines coverage)

### Critérios de Sucesso (Fase 5)

- ✅ Todos os 3 módulos: 95%+ coverage
- ✅ Threat detection validado
- ✅ Memory persistence testado
- ✅ Zero mocks

---

## FASE 6: Utilities & Support (P3)

**Objetivo:** Coverage 95% em módulos de suporte
**Prazo:** 2-3 dias
**Prioridade:** BAIXA-MÉDIA

### Módulos Target

Módulos diversos com <95% coverage:
- Config loaders
- Logging utilities
- Metrics collectors
- Helper functions

**Total estimado:** ~600 lines missing

### Testes a Criar

Será determinado após análise detalhada no início da fase.

### Critérios de Sucesso (Fase 6)

- ✅ Todos os módulos support: 95%+ coverage
- ✅ Edge cases testados
- ✅ Error handling validado

---

## Workflow Operacional

### Daily Workflow (A SEGUIR TODOS OS DIAS)

**Ao abrir Claude Code:**

1. **Executar slash command:**
   ```
   /check-coverage
   ```

2. **Revisar COVERAGE_STATUS.html:**
   - Check for regressions (🔴 alerts)
   - Identify today's target module
   - Review trend chart

3. **Abrir PLANO_95PCT_MASTER.md:**
   - Identify current phase
   - Select next module to test
   - Review gaps e testes a criar

4. **Criar testes targeted:**
   - Abrir htmlcov/{module}.html
   - Identificar missing lines (vermelho)
   - Criar testes específicos
   - Validar coverage incrementa

5. **Update snapshot:**
   ```bash
   pytest --cov=. --cov-report=xml --cov-report=html
   python scripts/coverage_tracker.py
   ```

6. **Commit progress:**
   ```bash
   git add .
   git commit -m "test(module): +15% coverage - tested core validation logic"
   ```

### Weekly Review

**Toda sexta-feira:**

1. Review coverage_history.json (7 days trend)
2. Validate no regressions occurred
3. Update estimates if needed
4. Plan next week's modules

---

## Detecção de Regressões

### Sistema Automático

**coverage_tracker.py detecta automaticamente:**

- ✅ Overall coverage drop ≥10%
- ✅ Per-module coverage drop ≥10%
- ✅ Total lines covered decreased
- ✅ New modules with 0% coverage

**Ação ao detectar regressão:**

1. 🚨 Alert mostrado em COVERAGE_STATUS.html
2. 🔍 Investigar causa (código novo não testado?)
3. 🛠️ Criar testes IMEDIATAMENTE para o gap
4. ✅ Validar coverage restaurado

---

## Métricas de Progresso

### KPIs por Fase

| Métrica | Baseline | Meta Final |
|---------|----------|------------|
| **Overall Coverage** | 23.62% | 95%+ |
| **Safety Coverage** | 25.73% | 95%+ |
| **Consciousness Coverage** | ~24% | 95%+ |
| **Justice Coverage** | ~31% | 95%+ |
| **Performance Coverage** | ~19% | 95%+ |
| **Immune Coverage** | ~36% | 95%+ |

### Tracking

Todos os dias:
```bash
python scripts/coverage_tracker.py
```

Dados salvos em:
- `docs/coverage_history.json` (append-only, imutável)
- `docs/COVERAGE_STATUS.html` (dashboard atualizado)

---

## Princípios Imutáveis

### O Que SEMPRE Fazer

1. ✅ Usar htmlcov para targeting preciso
2. ✅ Testar funcionalidade core (não legacy)
3. ✅ Zero mocks (Padrão Pagani)
4. ✅ Validar coverage incrementa ANTES de commit
5. ✅ Executar /check-coverage diariamente
6. ✅ Detectar e corrigir regressões imediatamente

### O Que NUNCA Fazer

1. ❌ Criar testes genéricos sem targeting
2. ❌ Usar mocks para facilitar (viola Padrão Pagani)
3. ❌ Commit sem validar coverage
4. ❌ Ignorar regressões
5. ❌ Testar legacy code ao invés de core functionality
6. ❌ Criar placeholders (viola Padrão Pagani)

---

## Timeline Consolidado

```
┌─────────────────────────────────────────────────────────────┐
│ SEMANA 1: Fase 1 (Safety) + Início Fase 2 (Consciousness)  │
├─────────────────────────────────────────────────────────────┤
│ Day 1-2: safety.py (583 lines) → 95%                       │
│ Day 3:   emergency_circuit_breaker.py (180 lines) → 95%    │
│ Day 4-5: tig/fabric.py (385 lines) → 50%+                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SEMANA 2: Fase 2 Complete (Consciousness)                  │
├─────────────────────────────────────────────────────────────┤
│ Day 6-7: tig/fabric.py complete → 95%                      │
│ Day 8-9: esgt/coordinator.py (276 lines) → 95%            │
│ Day 10:  api.py + mcea/attention_controller.py → 95%       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SEMANA 3: Fase 3 (Justice) + Fase 4 (Performance)          │
├─────────────────────────────────────────────────────────────┤
│ Day 11-13: Justice modules (600 lines total) → 95%         │
│ Day 14-15: Performance modules start (800 lines)            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SEMANA 4: Fase 4, 5, 6 Complete + Validação Final          │
├─────────────────────────────────────────────────────────────┤
│ Day 16-17: Performance complete → 95%                       │
│ Day 18-19: Immune System (500 lines) → 95%                 │
│ Day 20-21: Utilities (600 lines) → 95%                     │
│ Day 22-23: Validação final, regression check, docs         │
└─────────────────────────────────────────────────────────────┘
```

**Total:** 23 dias úteis (~4-5 semanas com buffer)

---

## Conformidade Final

### Checklist de Conclusão (95% Atingido)

**Requisitos técnicos:**
- [ ] Overall coverage ≥ 95%
- [ ] Todos os módulos P0 (Safety): 95%+
- [ ] Todos os módulos P1 (Consciousness, Justice): 95%+
- [ ] Todos os módulos P2 (Performance, Immune): 95%+
- [ ] Todos os módulos P3 (Utilities): 95%+
- [ ] Zero regressões detectadas
- [ ] Todos os testes PASSANDO

**Requisitos constitucionais (Doutrina Vértice):**
- [ ] Zero mocks (Artigo II - Padrão Pagani)
- [ ] Zero placeholders (Artigo II - Padrão Pagani)
- [ ] Sistema de tracking persistente (Artigo V - Legislação Prévia)
- [ ] Agente Guardião operacional (Anexo D - Execução Constitucional)
- [ ] Rastreabilidade total (coverage_history.json)

**Requisitos de documentação:**
- [ ] COVERAGE_STATUS.html atualizado
- [ ] coverage_history.json com histórico completo
- [ ] /check-coverage slash command funcional
- [ ] Relatório final de conclusão criado

---

## Conclusão

Este plano é IMUTÁVEL e define o caminho oficial para 95% coverage.

**Filosofia:**

> "Teste o que importa, não o que é fácil."
> — Padrão Pagani Absoluto

> "A verdade é mais valiosa que a ilusão de progresso."
> — Day 4 Truth Discovery

> "Governança antes de execução. Sempre."
> — Doutrina Vértice, Artigo V

---

**Próximo Passo Imediato:**

1. Generate initial coverage snapshot:
   ```bash
   pytest --cov=. --cov-report=xml --cov-report=html
   python scripts/coverage_tracker.py
   ```

2. Open dashboard:
   ```bash
   open docs/COVERAGE_STATUS.html
   ```

3. Begin Fase 1 - safety.py targeted testing

---

**"Do trabalho bem feito nasce a confiança. Da confiança nasce a excelência."**

— VERTICE Development Philosophy
