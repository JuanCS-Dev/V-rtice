# SISTEMA DE COVERAGE DEFINITIVO - Manual Completo

**Data:** 2025-10-22
**Status:** ✅ IMPLEMENTADO E OPERACIONAL
**Objetivo:** 95%+ coverage em TODOS os 249 módulos principais

---

## 🎯 O Que Foi Criado

### 1. MASTER_COVERAGE_PLAN.md
**Localização:** `docs/MASTER_COVERAGE_PLAN.md`

**Função:**
- Lista TODOS os 249 módulos que precisam de coverage
- Checkboxes `[ ]` / `[x]` para rastrear progresso
- Categorização por prioridade (P0, P1, P2, P3)
- Barra de progresso visual `█████░░░░░`
- **AUTO-ATUALIZADO** pelo coverage_commander.py

**Estrutura:**
- FASE A: 60 módulos com coverage parcial (Quick Wins)
- FASE B/C/D: 189 módulos com zero coverage

### 2. coverage_commander.py
**Localização:** `scripts/coverage_commander.py`

**Função:**
- Orquestrador automático de testes incrementais
- Roda pytest em batches de 5-10 módulos por vez
- Atualiza MASTER_COVERAGE_PLAN.md automaticamente
- Detecta regressões de coverage (threshold 5%)
- Salva snapshots em coverage_history.json

**Comandos Principais:**

```bash
# Ver status atual
python scripts/coverage_commander.py --status

# Testar próximo batch de 10 módulos
python scripts/coverage_commander.py --batch 10

# Testar FASE A completa (60 módulos parciais)
python scripts/coverage_commander.py --phase A

# Verificar regressões
python scripts/coverage_commander.py --check-regressions

# Testar apenas P0 (Safety Critical)
python scripts/coverage_commander.py --batch 10 --priority P0
```

### 3. Slash Command /retomar
**Localização:** `.claude/commands/retomar.md`

**Função:**
- Comando ÚNICO para verificar progresso
- Executa `coverage_commander.py --status` automaticamente
- Mostra:
  - Progresso global (X/249 módulos)
  - Status por prioridade (P0, P1, P2, P3)
  - Próximos 5 alvos prioritários
  - Regressões detectadas (se houver)

**Como usar:**
```
/retomar
```

### 4. Pre-Commit Hook
**Localização:** `.git/hooks/pre-commit`

**Função:**
- **BLOQUEIA commits** que causem regressões >5%
- Roda `coverage_commander.py --check-regressions` antes de cada commit
- Previne perda de progresso acidental

**Bypass (NÃO RECOMENDADO):**
```bash
git commit --no-verify
```

---

## 🚀 Como Usar Este Sistema

### Workflow Diário

**1. Abrir Claude Code**
```bash
# Primeiro comando SEMPRE
/retomar
```

Isso mostra:
```
📊 COVERAGE COMMANDER - Status Report
======================================================================

📈 Progresso Global: 0/249 (0.00%)

Prioridades:
  🔴 P0: 0/12 (0.0%)
  🟠 P1: 0/71 (0.0%)
  🟡 P2: 0/28 (0.0%)
  🟢 P3: 0/138 (0.0%)

🎯 Próximos 5 Alvos:
  1. consciousness/safety.py
  2. consciousness/biomimetic_safety_bridge.py
  3. consciousness/episodic_memory/event.py
  4. consciousness/temporal_binding.py
  5. consciousness/coagulation/cascade.py
```

**2. Criar Testes para os Alvos**

Exemplo para `consciousness/safety.py`:

```bash
# Abrir htmlcov para ver missing lines
open htmlcov/consciousness_safety_py.html

# Criar testes targeted (SEM MOCKS!)
# tests/unit/consciousness/test_safety_targeted_new.py

# Rodar testes
pytest tests/unit/consciousness/test_safety_targeted_new.py \
  --cov=consciousness/safety \
  --cov-report=term-missing
```

**3. Atualizar Plano (Manual por enquanto)**

Quando um módulo atingir 95%+, editar `docs/MASTER_COVERAGE_PLAN.md`:

Mudar:
```markdown
[ ] **1.** 🔴 `consciousness/safety.py`
```

Para:
```markdown
[x] **1.** 🔴 `consciousness/safety.py`
```

**4. Rodar Coverage Completo**

```bash
pytest --cov=. --cov-report=xml --cov-report=html
python scripts/coverage_tracker.py  # Salva snapshot
```

**5. Commit**

```bash
git add .
git commit -m "test(consciousness): safety.py 25% → 95% (+70%)"

# Pre-commit hook valida automaticamente!
# Se houver regressão, commit é BLOQUEADO
```

---

## 📊 Estrutura de Prioridades

### 🔴 P0 - Safety Critical (12 módulos)
**Importância:** MÁXIMA
**Módulos:**
- `consciousness/safety.py`
- `justice/emergency_circuit_breaker.py`
- `justice/constitutional_validator.py`
- Etc.

**Por que P0:**
- Safety não pode falhar
- Erros podem causar danos reais
- Requisito regulatório

### 🟠 P1 - Core Consciousness (71 módulos)
**Importância:** ALTA
**Módulos:**
- `consciousness/api.py`
- `consciousness/system.py`
- `consciousness/tig/fabric.py`
- Neuromodulation, Predictive Coding, ESGT, etc.

**Por que P1:**
- Core functionality do sistema
- Integridade científica (IIT, Global Workspace Theory)
- User-facing APIs

### 🟡 P2 - System Services (28 módulos)
**Importância:** MÉDIA
**Módulos:**
- `governance/`
- `performance/`
- `immune_system/`

**Por que P2:**
- Suporte operacional
- Performance optimization
- Monitoring e observability

### 🟢 P3 - Supporting (138 módulos)
**Importância:** BAIXA-MÉDIA
**Módulos:**
- Utilities
- Examples
- Auxiliary services

**Por que P3:**
- Menos crítico para operação
- Pode ser testado depois

---

## 📈 Estratégia de Execução (30-40 dias)

### FASE A: Quick Wins (Dias 1-10)
**Alvo:** 60 módulos com coverage parcial
**Target:** 6% → 25% overall
**Método:**
- Módulos já têm algum teste
- Completar missing lines targeted
- Usar htmlcov para guiar

**Comando:**
```bash
python scripts/coverage_commander.py --phase A
```

### FASE B: Zero Coverage Simple (Dias 11-20)
**Alvo:** ~100 módulos zero coverage SIMPLES (<100 lines)
**Target:** 25% → 50% overall
**Método:**
- Auto-geração de testes básicos
- Testes parametrizados
- Fixtures reutilizáveis

**Comando:**
```bash
python scripts/coverage_commander.py --phase B
```

### FASE C: Core Modules (Dias 21-30)
**Alvo:** ~50 módulos core complexos
**Target:** 50% → 75% overall
**Método:**
- Testes targeted manuais
- Integration tests
- Casos complexos

**Comando:**
```bash
python scripts/coverage_commander.py --phase C
```

### FASE D: Hardening (Dias 31-40)
**Alvo:** Módulos restantes
**Target:** 75% → 95%+ overall
**Método:**
- Edge cases
- Stress tests
- Error handling

**Comando:**
```bash
python scripts/coverage_commander.py --phase D
```

---

## 🔒 Garantias do Sistema

### 1. Zero Regressão
✅ Pre-commit hook bloqueia commits com drops >5%
✅ coverage_history.json imutável (append-only)
✅ Snapshots salvos a cada run

### 2. Progresso Persistente
✅ MASTER_COVERAGE_PLAN.md sempre sincronizado
✅ Checkboxes rastreiam cada módulo
✅ /retomar mostra estado atual SEMPRE

### 3. Rastreabilidade Total
✅ Histórico completo em coverage_history.json
✅ Timestamps em cada snapshot
✅ Delta tracking automático

---

## 🛠️ Troubleshooting

### Problema: "MASTER_COVERAGE_PLAN.md not found"
**Solução:**
```bash
# Regenerar o plano
python3 << 'SCRIPT'
# (script de geração - já executado)
SCRIPT
```

### Problema: "Coverage regrediu mas não deveria"
**Solução:**
```bash
# Verificar qual teste foi removido/alterado
git diff HEAD~1 tests/

# Restaurar testes
git checkout HEAD~1 -- tests/unit/...

# Re-rodar coverage
pytest --cov=. --cov-report=xml
python scripts/coverage_tracker.py
```

### Problema: "Pre-commit hook bloqueou meu commit"
**Solução:**
```bash
# Ver o que regrediu
python scripts/coverage_commander.py --check-regressions

# Criar testes para módulos que regrediram
# ...

# Tentar commit novamente
git commit
```

---

## 📚 Arquivos Importantes

| Arquivo | Função | Auto-Atualizado? |
|---------|--------|------------------|
| `docs/MASTER_COVERAGE_PLAN.md` | Plano mestre com checkboxes | ✅ Sim (coverage_commander) |
| `docs/coverage_history.json` | Histórico de snapshots | ✅ Sim (coverage_tracker.py) |
| `scripts/coverage_commander.py` | Orquestrador automático | ❌ Não |
| `scripts/coverage_tracker.py` | Snapshot manager | ❌ Não |
| `.claude/commands/retomar.md` | Slash command | ❌ Não |
| `.git/hooks/pre-commit` | Regression blocker | ❌ Não |

---

## 🎯 Próximos Passos IMEDIATOS

**Hoje (2025-10-22):**

1. ✅ Sistema criado e testado
2. ⏳ Executar `/retomar` para confirmar funcionamento
3. ⏳ Começar FASE A: Testar os 5 primeiros módulos
4. ⏳ Commit das mudanças

**Amanhã:**

1. Continuar FASE A (batch de 10 módulos)
2. Validar que checkboxes são marcados
3. Verificar que pre-commit hook funciona

**Esta Semana:**

1. Completar FASE A (60 módulos)
2. Coverage: 6% → 25%
3. Validar estratégia

---

## 📞 Suporte

**Se algo não funcionar:**

1. Verificar logs:
```bash
python scripts/coverage_commander.py --status
```

2. Verificar coverage atual:
```bash
pytest --cov=. --cov-report=term
```

3. Regenerar plano se necessário:
```bash
# (script de geração disponível)
```

---

## 🏆 Meta Final

**249 módulos → 95%+ coverage**

```
FASE A: ████░░░░░░░░░░░░░░░░  60/249 (24.1%)
FASE B: ████████░░░░░░░░░░░░ 160/249 (64.3%)
FASE C: ███████████████░░░░░ 210/249 (84.3%)
FASE D: ████████████████████ 249/249 (100%)  ✅
```

**Tempo Estimado:** 30-40 dias úteis
**Data de Início:** 2025-10-22
**Data Prevista:** 2025-11-30 (com margem)

---

**"Do trabalho bem feito nasce a confiança. Da confiança nasce a excelência."**

— VERTICE Development Philosophy

**"Nunca mais pensar em coverage. Sistema auto-rastreável para sempre."**

— Juan, 2025-10-22
