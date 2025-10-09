# Scripts de Release Liturgia

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

| Script | Descrição |
|--------|-----------|
| `generate-sbom.sh` | Gera SBOM (Syft local ou container). |
| `vulnerability-scan.sh` | Executa Grype em SBOM ou alvo direto. |
| `sign-artifact.sh` | Assina artefato com cosign (opcional attestation). |
| `generate-release-notes.py` | Produz release notes Markdown a partir de SBOM/vuln. |

## Uso Local
```bash
# SBOM
./scripts/release/generate-sbom.sh frontend sbom.json

# Scan
./scripts/release/vulnerability-scan.sh sbom.json vuln.json

# Assinatura
COSIGN_PASSWORD=... COSIGN_KEY=... ./scripts/release/sign-artifact.sh frontend --attest sbom.json
```
