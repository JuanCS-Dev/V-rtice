# Release Liturgia – Plano de Execução

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## 1. Objetivo
Institucionalizar o rito de release conforme Doutrina Vértice: todo artefato sai com SBOM, assinatura, checklist Regra de Ouro e documentação auditável.

## 2. Inventário Inicial
| Artefato | Repositório | Pipeline atual | Observações |
|----------|-------------|----------------|-------------|
| vcli-go | `vcli-go/` | Templates `.github/workflows/templates/service-ci*.yml` (build/test) | Sem SBOM/assinatura. Releases manuais. |
| Frontend | `frontend/` | scripts npm locais | Necessário workflow build + SBOM. |
| MAXIMUS Core | `backend/services/maximus_core_service/` | comandos make + scripts | Sem pipeline centralizada; múltiplos serviços. |
| Docs/Dashboards | `docs/`, `monitoring/` | nenhuma | produzir pacote estático. |

## 3. Checklist Regra de Ouro (proposta)
1. ✅ Testes unitários/integrados executados.
2. ✅ Lint/format + segurança (ruff, spectral, etc).
3. ✅ SBOM gerada (syft) e armazenada.
4. ✅ Vulnerability scan (grype/snyk) sem findings críticos.
5. ✅ Artefato assinado (cosign) + attestation (Rekor).
6. ✅ Checklist Doutrina aprovado (kill switch, ética, etc).
7. ✅ Release notes gerados automaticamente.

## 4. Entregáveis
- Workflow `release-liturgia.yml` (ou workflows específicos).
- Scripts (`scripts/generate-sbom.sh`, `scripts/cosign-sign.sh`, etc).
- Documentação `docs/cGPT/session-03/thread-a/RELEASE_PLAYBOOK.md`.
- Templates de checklist (`docs/cGPT/session-03/thread-a/RELEASE_CHECKLIST.md`).

## 5. Plano de Trabalho
1. **Semana 1** – Inventário + SBOM PoC (syft/grype).
2. **Semana 2** – Assinatura cosign + publicação em registry.
3. **Semana 3** – Checklist Regra de Ouro automatizado + release notes.
4. **Semana 4** – Documentação final + run piloto.

## 6. Dependências
- Acesso a registries (Docker, GitHub Releases).
- Chaves cosign e Rekor (guardar em secrets).
- Equipe de segurança (aprovação SBOM/vuln).

## 7. Métricas de Sucesso
- 100% dos releases passam por SBOM + assinatura.
- Checklist gerado e anexado ao release.
- Pipeline reproduzível com um comando.

## 8. Próximos Passos
- Identificar owners por artefato.
- Definir storage SBOM (artefatos + repo).
- Redigir `RELEASE_PLAYBOOK.md`.

## Scripts disponíveis
- `scripts/release/generate-sbom.sh`
- `scripts/release/vulnerability-scan.sh`
- `scripts/release/sign-artifact.sh`

## Workflows relacionados
- `.github/workflows/release-liturgia.yml` (multi componente)
- `.github/workflows/frontend-release.yml` (pipeline dedicada frontend)

## Scripts de suporte
- Consulte `scripts/release/README.md` para invocações locais.
