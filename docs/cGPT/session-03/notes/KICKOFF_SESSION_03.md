# Sessão 03 – Kick-off (Pipeline & Supply Chain)

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

**Data**: (preencher)  
**Participantes**: (nomes/papéis)  
**Objetivo**: Garantir cadeia de releases confiável e suite de testes cruzados CLI ↔ MAXIMUS ↔ Frontend.

---

## 1. Revisão de Contexto
- Sessão 01: Contratos + telemetria.
- Sessão 02: Cockpit & dashboards.
- Sessão 03 foca em **pipeline/SBOM/assinaturas** e **testes integrados**.
- Regra de Ouro → releases só com checks completos.

## 2. Escopo por Thread

### Thread A – Release Liturgia
- Geração de SBOM (CLI, frontend, MAXIMUS).
- Assinatura de artefatos (cosign) + attestation (Rekor).
- Checklist de release (Regra de Ouro + Doutrina).
- Automação (workflows CI/CD).

### Thread B – Testes Integrados Cruzados
- Orquestração de cenários E2E (CLI → MAXIMUS → Frontend).
- Matriz legacy uv (safety v1 + uv toolchain).
- Relatório de conformidade (latência, kill switch, streaming).

## 3. Dependências
- Acesso: build pipelines (GitHub Actions, etc.), registries, cluster staging.
- Equipes: DevOps, SRE, Security, Frontend/CLI/Backend.
- Ferramentas: cosign, syft/grype, pytest, k6 (opcional).

## 4. Riscos
- Rotinas de assinatura precisam ser integradas sem quebrar fluxo atual.
- Complexidade de testes E2E (ambiente deve estar estável).
- Coleta de resultados (logs/artefatos) deve ser persistida.

## 5. Ações Imediatas
1. Inventário de pipelines existentes e lacunas.
2. Definir formato de checklist (Regra de Ouro + Doutrina).
3. Identificar cenários críticos para E2E (Chat, kill switch, streaming).

## 6. Checkpoint
- Sexta (horário): review dos workflows atualizados e E2E rodando.

---
*Atualizar com decisões e owner de cada tarefa.*
