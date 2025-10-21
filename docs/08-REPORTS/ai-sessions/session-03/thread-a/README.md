# Thread A – Release Liturgia

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## Objetivo
Definir o rito de release confiável para toda a plataforma Vértice:
- SBOM para cada artefato (CLI, Frontend, MAXIMUS).
- Assinatura e attestation (cosign + Rekor).
- Checklist Regra de Ouro automatizado em CI.
- Documentação de release para auditoria (Doutrina Vértice).

## Situação Atual
| Artefato | Pipeline atual | Gaps identificados |
|----------|----------------|--------------------|
| vcli-go (Go) | Usa templates `.github/workflows/templates/service-ci*.yml` | Sem SBOM, sem assinatura, sem checklist |
| Frontend (React) | Scripts locais; sem workflow formal | Build sem SBOM, sem assinatura |
| MAXIMUS services | Pipelines individuais (não versionadas) | Falta SBOM e assinatura; releases manuais |
| Observability/Docs | Nenhuma rotina formal | N/A |

## Próximos Passos
1. Inventariar pipelines existentes (Go, frontend, python) e registrar no plano.
2. Decidir ferramenta SBOM (syft/grype) e pontos de integração.
3. Definir estrutura de checklist (Regra de Ouro + Doutrina).
4. Criar workflow `release-liturgia.yml` consolidando passos.

## Documentos Associados
- `RELEASE_LITURGIA_PLAN.md` – plano detalhado e checklist.
- Future: `RELEASE_PLAYBOOK.md`, `RELEASE_CHECKLIST.md`.

## Referências
- Multi-Thread Blueprint Sessão 03.
- Documentação cosign/Rekor.
- Guidelines Doutrina Vértice Artigo VIII.
