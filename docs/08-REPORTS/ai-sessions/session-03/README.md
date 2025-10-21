# Sessão 03 – Release Liturgia & Testes Integrados

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## Objetivo
Garantir cadeia de release confiável (SBOM + assinaturas + checklist Doutrina) e uma suíte de testes integrados CLI ↔ MAXIMUS ↔ Frontend.

## Estrutura
```
session-03/
├── README.md
├── notes/
│   └── KICKOFF_SESSION_03.md
├── thread-a/   # Release Liturgia
└── thread-b/   # Testes Integrados Cruzados
```

## Status Inicial
| Thread | Status | Descrição |
|--------|--------|-----------|
| A – Release Liturgia | 🔄 Em execução | Inventário + scripts SBOM/cosign prontos |
| B – Testes Integrados | 🔄 Em execução | Cenários definidos, estrutura e2e criada |

## Entregáveis Esperados
- Workflow(s) CI/CD com geração de SBOM, cosign, attestation.
- Playbook e templates de release (`RELEASE_PLAYBOOK.md`, `RELEASE_NOTES_TEMPLATE.md`).
- Checklist Regra de Ouro automatizado (GitHub Actions / script).
- Suíte de testes integrados com relatórios (docs/cGPT/session-03/thread-b/...).
- Documentos de release (`docs/cGPT/session-03/thread-a/RELEASE_LITURGIA_PLAN.md`, etc.).
- Relatório de conformidade E2E.

## Referências
- `docs/cGPT/MULTI_THREAD_EXECUTION_BLUEPRINT.md`
- `.github/workflows/` (já existentes)
- `docs/performance/` (para reuso de pipeline)
