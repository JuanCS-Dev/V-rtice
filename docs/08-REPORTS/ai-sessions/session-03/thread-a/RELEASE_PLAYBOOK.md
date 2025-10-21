# Release Playbook – Liturgia Vêtice

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## 1. Preparação
1. Verificar branch `main` limpo e atualizado.  
2. Validar que `COSIGN_*` e `BENCH_TARGET_*` estão configurados.  
3. Executar `make test` / `npm test` localmente para sanity check (opcional).

## 2. Execução (GitHub Actions)
1. `release-liturgia.yml` – selecionar componente (`vcli-go`, `frontend`, `maximus`, `docs`).  
2. `frontend-release.yml` – pipeline dedicada (quando necessário).  
3. Registrar outputs (artefatos SBOM, vuln, release-notes.md) baixando-os dos artefatos da action.

## 3. Pós-Execução
1. Preencher `docs/cGPT/session-03/thread-a/RELEASE_CHECKLIST.md` com links dos artefatos.  
2. Caso necessário, gerar release notes locais:
   ```bash
   python scripts/release/generate-release-notes.py \
     --component vcli-go \
     --sbom artifacts/vcli-go/sbom-vcli-go.json \
     --vuln artifacts/vcli-go/vuln-vcli-go.json \
     --template docs/cGPT/session-03/thread-a/RELEASE_NOTES_TEMPLATE.md \
     --output release-notes-vcli-go.md
   ```
3. Anexar SBOM, vulnerabilidade, release notes ao repositório (ou à página de release).

## 4. Auditoria
- Checklist assinado por QA, Segurança e Arquiteto.  
- Logs das actions armazenados por 90 dias.  
- SBOM/vuln guardados em `artifacts/<component>`.

## 5. Contingência
- Falha no SBOM → rodar scripts manualmente (`scripts/release/`).  
- Falha no cosign → revogar chave e emitir nova.  
- Vulnerabilidades críticas → abrir incident response antes do release.

## 6. Próximas melhorias
- Integrar release notes automáticas à action.  
- Publicar artefatos em registry S3/GH Releases.  
- Adicionar verificação de dependências bloqueadas (policy).
