# Guia de Benchmarking – MAXIMUS Consciousness

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## 1. Objetivo
Estabelecer o procedimento oficial para executar e analisar os benchmarks de latência definidos no Adendo 3. O foco é validar que todos os canais (REST, WebSocket, gRPC) operem com **p95 < 500 ms** antes do rollout do streaming consciente.

## 2. Preparação do Ambiente
1. `docker compose -f tests/performance/docker-compose.bench.yml up -d`
2. Exportar variáveis de ambiente:
   ```bash
   export BENCH_TARGET_BASE_URL="https://staging.vertice.local"
   export BENCH_TARGET_WS_URL="wss://staging.vertice.local/stream/consciousness/ws"
   export BENCH_TARGET_GRPC_ADDR="staging.vertice.local:50051"
   ```
3. Opcional: `pip install yq` para executar os scripts localmente sem Docker.

## 3. Execução
```bash
# Rodar todo o suite (baseline)
./tests/performance/run-benchmarks.sh

# Rodar cenário stress somente REST
SCENARIO=stress ./tests/performance/run-benchmarks.sh --rest
```

Os resultados são armazenados em `tests/performance/reports/` e integrados automaticamente a `docs/performance/MAXIMUS_LATENCY_BENCHMARKS.md`.

## 4. Métricas Monitoradas
| Canal | Métrica | Ferramenta |
|-------|---------|------------|
| REST | p50, p95, throughput, error rate | hey |
| WebSocket | message latency, throughput, reconnects | k6 |
| gRPC | latency, rps, errors | ghz |

## 5. Targets
- REST: p95 < 300 ms, error rate < 1%
- WebSocket: message latency < 500 ms (p95), reconnect < 2%
- gRPC: p95 < 400 ms

## 6. Integração Grafana
Os dados exportados podem ser enviados para Prometheus/Grafana utilizando o dashboard `performance_latency_overview.json`. Ajuste as jobs de scrape para incluir os artefatos gerados.

## 7. CI/CD
O workflow `.github/workflows/performance-benchmarks.yml` executa os testes sob demanda (`workflow_dispatch`) ou semanalmente. Configurar secrets:
- `BENCH_TARGET_BASE_URL`
- `BENCH_TARGET_WS_URL`
- `BENCH_TARGET_GRPC_ADDR`

## 8. Troubleshooting
- Conferir se o ambiente alvo está acessível.
- Validar autenticação se endpoints exigirem tokens (exportar headers via `hey` com `-H`).
- Para WebSocket, certificar-se de que o bridge está emitindo timestamps para cálculo da latência.

## 9. Próximos Passos
- Automatizar publicação de resultados em Grafana (Prometheus Pushgateway).
- Adicionar cenários de degradação (latência artificial).
- Expandir benchmarks para interações CLI (command latency).
