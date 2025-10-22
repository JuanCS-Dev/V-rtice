---
description: Check coverage status and review master plan
---

# Coverage Status Check - Sistema Persistente de Tracking

Vou executar uma verificação completa do status de coverage e plano 95%.

## Passo 1: Ler Status Atual

Vou abrir e analisar o dashboard de coverage:

- Read `docs/COVERAGE_STATUS.html`
- Read `docs/coverage_history.json`
- Read `docs/PLANO_95PCT_MASTER.md`

## Passo 2: Analisar Situação

Vou apresentar:

1. **Coverage atual**: % total e por módulo
2. **Tendência**: Comparação com snapshots anteriores
3. **Regressões detectadas**: Se houver drops ≥10%
4. **Fase atual do plano**: Qual módulo devemos testar hoje
5. **Próximos passos**: Ações específicas recomendadas

## Passo 3: Verificar Conformidade Constitucional

Vou validar conformidade com Doutrina Vértice:

- ✅ Artigo II (Padrão Pagani): Zero mocks nos testes
- ✅ Artigo V (Legislação Prévia): Tracking persistente ativo
- ✅ Anexo D (Execução Constitucional): Agente Guardião funcionando

## Passo 4: Recomendar Ação Imediata

Com base no PLANO_95PCT_MASTER.md e coverage atual, vou recomendar:

- Módulo a testar hoje
- Missing lines específicas (via htmlcov)
- Testes a criar (targeted)
- Tempo estimado

---

**Filosofia:**

> "Ao abrir Claude Code, SEMPRE execute /retomar para saber onde estamos e para onde vamos."

> "Tracking persistente elimina o problema: 'TODO DIA O QUE TAVA 100% VAI PRA 20%'"

— PLANO 95% MASTER, Padrão Pagani Absoluto
