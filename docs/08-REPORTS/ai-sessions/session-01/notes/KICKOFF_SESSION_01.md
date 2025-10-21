# Sessão 01 – Kick-off Multi-Thread

**Data**: (preencher)  
**Participantes**: (nomes e funções)  
**Objetivo**: dar início à Sessão 1 do programa cGPT, alinhando threads A/B e confirmando escopo, dependências e entregáveis da semana.

---

## 1. Revisão da Doutrina e Blueprint
- Confirmado alinhamento com **Doutrina Vértice** (Regra de Ouro, Legislação Prévia, Antifragilidade).
- Blueprint `MULTI_THREAD_EXECUTION_BLUEPRINT.md` validado como referência oficial.
- Roadmap semanal `EXECUTION_ROADMAP.md` aceito.

## 2. Escopo da Sessão 01
### Thread A – Interface Charter
- Levantar todos os endpoints e contratos existentes (vcli-go, MAXIMUS, serviços satélites).
- Construir **Interface Charter v0.1** (OpenAPI/Protobuf).
- Preparar lint automático (Spectral/Buf) integrado à CI.
- Entregável: `docs/contracts/interface-charter.yaml` (ou equivalente) + scripts de lint.

### Thread B – Telemetria & Segurança
- Inventariar pontos de observabilidade (CLI OTel, Prometheus, frontend).
- Definir plano de Zero Trust intra-serviços (certs, tokens, rotacionamento).
- Entregáveis: `docs/observability/matriz-telemetria.md` + `docs/security/zero-trust-plan.md`.

## 3. Dependências e Recursos
- Times envolvidos: Core Engineering, DevSecOps, Observability.
- Acessos necessários: repositórios MAXIMUS, vcli-go, painéis Grafana, pipelines CI/CD.
- Ferramentas: Spectral/Buf, OpenAPI Generator, Grafana export, Vault/Sealed Secrets (a confirmar).

## 4. Riscos Iniciais
- Mapeamento incompleto de contratos legados→ mitigar com workshop rápido com responsáveis de cada serviço.
- Falta de tempo DevSecOps para rotacionamento de credenciais → agendar slot dedicado na semana.
- Volume de documentação → utilizar templates reutilizáveis (ver sessão 5).

## 5. Ações Imediatas
1. Criar scaffolding dos artefatos (templates para Charter, matriz de telemetria, plano de segurança).
2. Agendar entrevistas técnicas com donos de serviços e operadores.
3. Preparar pipelines locais para lint de OpenAPI/Buf.

## 6. Próximo Checkpoint
- **Sexta-feira (horário)** – review dos artefatos v0.1, decisão sobre ajustes e riscos.

---
*Documento inicial – atualizar com decisões, participantes e datas assim que a sessão ocorrer.*
