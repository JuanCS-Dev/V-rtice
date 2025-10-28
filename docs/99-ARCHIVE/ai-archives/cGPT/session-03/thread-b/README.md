# Thread B – Testes Integrados Cruzados

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## Objetivo
Criar uma suíte E2E que valide CLI ↔ MAXIMUS ↔ Frontend antes de cada release:
- Cenários críticos (chat, kill switch, streaming, dashboards).
- Matriz legacy (safety v1) x toolchain moderna uv.
- Relatórios automatizados anexados aos releases.

## Situação Atual
| Área | Estado | Observações |
|------|--------|-------------|
| CLI ↔ MAXIMUS | Scripts manuais (`vcli-go/internal/...`) | Sem execução automática. |
| MAXIMUS API | Testes unitários/extensivos no repositório | Necessário orquestração multi-serviço. |
| Frontend | Testes Vitest | Não cobre integração real. |

## Próximos Passos
1. Mapear cenários mínimos (ver planilha abaixo).
2. Escolher framework (pytest + docker-compose, k6, etc).
3. Implementar orquestrador (`tests/e2e/run-tests.sh`).
4. Exportar relatórios (junit/html) + dashboards.

## Cenários Alvo (Rascunho)
| Código | Descrição | Métricas | Estado |
|--------|-----------|----------|--------|
| E2E-CLI-STREAM | CLI inicia stream, recebe métricas <500ms | latência, reconexão | 🔄 |
| E2E-FRONT-DASH | Frontend consome streaming e atualiza dashboard | p95 render <300ms | 🔄 |
| E2E-KILL-SWITCH | Gatilho de violação gera incident report + HSAS | tempo <1s | 🔄 |
| E2E-LEGACY-SAFETY | Suite legado (safety_py) com uv toolchain | all tests pass | 🔄 |

## Documentos Associados
- `E2E_TEST_PLAN.md` (planejamento detalhado).
- `E2E_RUNBOOK.md` (execução manual).
- Scripts/relatórios a definir.

## Artefatos Matriz
- `tests/e2e/matrix/matrix.csv` – status por cenário.
- `tests/e2e/matrix/legacy-uv-notes.md` – diferenças legacy/uv.
