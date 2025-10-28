# Inventário de Pipelines – Release Liturgia

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

| Componente | Localização | Workflow atual | Observações | Próximas ações |
|------------|-------------|----------------|-------------|----------------|
| CLI (vcli-go) | `vcli-go/` | templates `.github/workflows/templates/service-ci*.yml` (build/test) | Sem SBOM, sem assinatura, release manual via `make release`. | Adicionar job `release-liturgia` com `syft`, `grype`, `cosign`. |
| Frontend | `frontend/` | N/A (build local com npm) | Necessita workflow `frontend-release.yml` (build, bundle, SBOM, upload). | Criar pipeline nova com `npm install/build`, `syft`, `cosign`. |
| MAXIMUS Core | `backend/services/maximus_core_service/` + sub-serviços | Rodado via scripts `make` individuais | Fragmentado; sem centralização de release. | Planejar pipeline monolítica `maximus-release.yml` (docker build, SBOM, cosign). |
| Services (REST) | `backend/services/*` | Alguns usam templates `service-ci`, mas sem release final | Necessário checklist e release artefato docker. | Reusar job `release-liturgia` com matrix por serviço crítico. |
| Observabilidade / Docs | `docs/`, `monitoring/` | Sem workflow | Requer pipeline para publicar dashboards/relatórios. | Integrar com `performance-benchmarks.yml` e nova etapa release. |

## Ferramentas/Secrets Necessários
- `SYFT_VERSION`, `GRYPE_VERSION` (ou container oficial). 
- `COSIGN_KEY`, `COSIGN_PASSWORD`, `REKOR_URL`.
- Registry destino (GitHub Container Registry). 

## Próximos Passos
1. Prototipar `scripts/generate-sbom.sh` usando `syft` (docker).  
2. Definir formato de release notes (template markdown).  
3. Criar `release-liturgia.yml` consumindo este inventário.
