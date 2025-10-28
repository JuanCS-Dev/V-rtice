# Sessão 01 · Thread B – Telemetria & Segurança

## Objetivo
Construir um inventário centralizado de telemetria e definir o plano Zero Trust para conexões internas da plataforma.

## Entregáveis da Sessão
1. `docs/observability/matriz-telemetria.md`
   - Lista completa de métricas (CLI, MAXIMUS, serviços satélites).
   - Identificação de origem, destino, protocolo, frequência, retenção.
   - Estados de instrumentação (existente, pendente, em validação).
2. `docs/security/zero-trust-plan.md`
   - Política de autenticação/autorizações inter-serviços.
  - Estratégia de rotacionamento de credenciais e certificados.
  - Plano de rollout e validação.

## Próximos Passos
1. Levantar fontes de métricas atuais (Prometheus, OTel, logs CLI, dashboards).
2. Mapear lacunas (missing metrics, cardinalidade, agregação).
3. Definir pipeline de coleta/ingestão (tempo real vs batch).
4. Alinhar com DevSecOps a matriz de confiança e mecanismos de rotação.

## Dependências
- Acesso aos painéis Grafana do MAXIMUS.
- Configurações OTel do vcli-go.
- Documentação de serviços satélites (HSAS, governance, etc.).
- Suporte da equipe de segurança para adequações.

## Observações
- Telemetria deve respeitar princípios de mínima exposição (no PII).
- Rotas de dados devem incluir traço/correlação (X-Trace-Id).
- Plano Zero Trust deve ser incremental para não interromper serviços legados.
