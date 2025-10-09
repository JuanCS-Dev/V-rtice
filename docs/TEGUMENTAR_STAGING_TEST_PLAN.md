# Plano de Testes em Staging – Módulo Tegumentar

**Objetivo:** validar ponta a ponta o ciclo reflexo → Linfonodo → vacinação em ambiente staging com infraestrutura real (XDP, Redis, Kafka, PostgreSQL, Immunis API).

## Pré-Requisitos
- Kernel Linux com suporte a XDP/eBPF (`CAP_BPF`, `CAP_NET_ADMIN`).
- Redis/Kafka/PostgreSQL acessíveis nas mesmas credenciais usadas em produção.
- Immunis API (`/threat_alert`, `/trigger_immune_response`) disponível e apontando para ambiente de homologação.
- Deploy do `tegumentar_service` com `/metrics` exposto e scrape configurado no Prometheus de staging.
- API Gateway configurado (`/stream/consciousness/{sse,ws}`) + API key ativa para SSE/WebSocket.

## Roteiro de Execução
1. **Baseline**
   - Aplicar `POST /api/tegumentar/posture` → `BALANCED` e validar resposta.
   - Coletar métricas iniciais (`curl http://<host>:9815/metrics`).

2. **Teste Reflexo → Linfonodo**
   - Injetar tráfego SQL injection (ex.: `tcpreplay` com payload `UNION SELECT`).
   - Verificar contadores: `tegumentar_reflex_events_total{signature_id="2"}` incrementado.
   - Confirmar registro do antígeno (`tegumentar_antigens_captured_total`).
   - Checar chamadas ao Linfonodo via logs (`tegumentar_lymphnode_validations_total{result="confirmed"}`).

3. **Vacinação**
   - Validar `tegumentar_vaccinations_total{result="success"}`.
   - Confirmar recebimento da imunização no Immunis (eventos `trigger_immune_response`).

4. **Observabilidade**
   - Exportar latências médias (`tegumentar_lymphnode_latency_seconds`) e anexar ao relatório.
   - Registrar métricas no Grafana (print/dashboard).

5. **Failover Controlado**
   - Simular indisponibilidade do Linfonodo (bloquear tráfego HTTP).
   - Repetir injeção; validar contadores `result="error"` e ausência de vacinação.
   - Restaurar Linfonodo e confirmar retentativas manuais (se aplicável).

## Entregáveis
- Relatório contendo:
  - Tabela de métricas antes/depois (reflexo, validações, vacinações, latência).
  - Logs relevantes (tegumentar + Immunis).
  - Incidentes/erros e tratamento.
- Atualização do `STATUS_TEGUMENTAR_IMPLEMENTATION.md` com resultados.
