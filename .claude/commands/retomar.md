---
description: Check coverage status and review master plan
---

# Coverage Status Check - Sistema Auto-Rastreável

Vou executar verificação automática usando o **Coverage Commander**.

## Sistema Novo (2025-10-22)

Este comando agora usa:
- **MASTER_COVERAGE_PLAN.md**: 249 módulos com checkboxes auto-atualizáveis
- **coverage_commander.py**: Orquestrador automático de testes incrementais
- **coverage_history.json**: Histórico persistente (append-only)

## Passo 1: Executar Coverage Commander

```bash
cd backend/services/maximus_core_service
python scripts/coverage_commander.py --status
```

Isso mostra:
- ✅ Progresso global (X/249 módulos = Y%)
- ✅ Status por prioridade (P0, P1, P2, P3)
- ✅ Próximos 5 alvos prioritários
- ⚠️ Regressões detectadas (se houver)

## Passo 2: Mostrar Progresso Visual

Vou apresentar:

1. **Progresso**: Barra visual `█████░░░░░ 45/249 (18.07%)`
2. **Por Prioridade**:
   - 🔴 P0 Safety: X/12 (Y%)
   - 🟠 P1 Consciousness: X/71 (Y%)
   - 🟡 P2 System Services: X/28 (Y%)
   - 🟢 P3 Supporting: X/138 (Y%)
3. **Próximos Alvos**: Lista de 5 módulos para testar hoje
4. **Regressões**: Alertas se coverage caiu >5%

## Passo 3: Validar Conformidade Constitucional

- ✅ Artigo II (Padrão Pagani): Coverage_commander previne mocks
- ✅ Artigo V (Legislação Prévia): MASTER_COVERAGE_PLAN.md governa
- ✅ Anexo D (Execução Constitucional): Auto-update de checkboxes

## Passo 4: Recomendar Ação Imediata

Com base no MASTER_COVERAGE_PLAN.md:

**Para testar próximo batch (10 módulos):**
```bash
python scripts/coverage_commander.py --batch 10
```

**Para testar FASE A completa (60 módulos parciais):**
```bash
python scripts/coverage_commander.py --phase A
```

**Para verificar se há regressões:**
```bash
python scripts/coverage_commander.py --check-regressions
```

---

## Filosofia

> "Coverage Commander elimina o problema: 'TODO DIA O QUE TAVA 100% VAI PRA 20%'"

> "MASTER_COVERAGE_PLAN.md é a fonte da verdade. Sempre atualizado. Sempre persistente."

> "249 módulos. 1 objetivo. 95%+ em TUDO."

— PLANO DEFINITIVO 2025-10-22
