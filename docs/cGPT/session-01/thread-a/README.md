# Sessão 01 · Thread A – Interface Charter

## Objetivo
Consolidar em um único repositório os contratos de comunicação entre:
- **vcli-go** (CLI & bridge)
- **MAXIMUS Core** (REST/gRPC expostos via API Gateway)
- **Serviços satélites** (HSAS, governance, etc.)

## Artefatos Gerados
- `docs/contracts/interface-charter.yaml` – rascunho inicial OpenAPI 3.1 com endpoints prioritários.
- `docs/contracts/INVENTARIO_ENDPOINTS.md` – inventário completo de rotas FastAPI por serviço.
- `docs/cGPT/session-01/thread-a/lint/spectral.yaml` – configuração preliminar para lint (a criar).
- Script de verificação (`scripts/lint-interface.sh`) – planejar integração em CI.

## Próximas Ações
1. **Inventário completo de endpoints** (CLI ↔ MAXIMUS ↔ serviços):
   - Mapear gRPC protos existentes (MAXIMUS).
   - Mapear comandos REST expostos pelo gateway.
   - Validar contratos de streaming (SSE/WebSocket).
2. **Refinar interface-charter.yaml**:
   - Adicionar todos os paths/operations com descrições confiáveis.
   - Modelar schemas específicos de cada serviço (HSAS, Governance, Analytics).
   - Documentar headers de segurança e versionamento (x-trace-id, etc.).
3. **Automação de lint**:
   - Definir regras Spectral (nomenclatura, versionamento, description).
   - Integrar lint na pipeline (GitHub Actions / CI interno).
4. **Documentação de migração**:
   - Guia para serviços adotarem o charter como fonte da verdade.
   - Plano de versionamento semântico (v1alpha, v1beta, etc.).

## Dependências
- Protobuf/gRPC definitions do MAXIMUS Core.
- Equipe de DevSecOps para revisar políticas de autenticação/Zero Trust.
- Operadores do CLI para validar fluxo real de comandos.

## Observações
- Todo novo endpoint deve ser registrado aqui antes de entrar em produção.
- Manter compatibilidade com clientes existentes (estratégia de depreciação gradual).
- Garantir que os nomes dos eventos respeitem a taxonomia do MAXIMUS (ESGT, neuromodulação, safety).
