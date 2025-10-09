# Testes de Performance – MAXIMUS Consciousness

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

Este diretório contém a suíte oficial de benchmarks do Adendo 3 (Benchmarks de Latência) descrito no `copilot_session.md`. O objetivo é medir continuamente os tempos de resposta dos principais canais do cockpit consciente (REST, WebSocket, gRPC) e garantir os targets < 500 ms p95.

```
tests/performance/
├── config/                # Configurações de cenários
├── ghz/                   # Benchmarks gRPC
├── hey/                   # Benchmarks REST (hey)
├── k6/                    # Benchmarks WebSocket/Streaming (k6)
├── reports/               # Relatórios gerados automaticamente
├── docker-compose.bench.yml
└── run-benchmarks.sh      # Orquestrador principal
```

## Pré-requisitos
- Docker / Docker Compose
- Node.js 20+ (para k6 via xk6-websockets, opcional quando usando Docker)
- Go (para ghz) – já provisionado no container de benchmark
- Ferramentas `hey`, `k6`, `ghz` (instaladas automaticamente via Docker)

## Cenários Disponíveis
Os cenários estão descritos em `config/scenarios.yaml` e cobrem:
- **baseline** – carga leve (1 → 10 usuários)
- **stress** – carga elevada sustentada
- **spike** – picos repentinos
- **soak** – testes longos (1h)

## Execução
```bash
# Executar todos os benchmarks
./tests/performance/run-benchmarks.sh

# Executar somente REST
./tests/performance/run-benchmarks.sh --rest

# Executar com cenário customizado
SCENARIO=stress ./tests/performance/run-benchmarks.sh
```

Os relatórios serão gerados em `tests/performance/reports/` (JSON) e sumarizados em Markdown em `docs/performance/MAXIMUS_LATENCY_BENCHMARKS.md`.

## Integração CI/CD
O workflow `.github/workflows/performance-benchmarks.yml` executa esta suíte manualmente (`workflow_dispatch`) ou conforme agendamento. Certifique-se de exportar as variáveis de ambiente:
- `BENCH_TARGET_BASE_URL`
- `BENCH_TARGET_WS_URL`
- `BENCH_TARGET_GRPC_ADDR`

## Referências
- [BENCHMARKING_GUIDE.md](../../docs/performance/BENCHMARKING_GUIDE.md)
- [MAXIMUS_LATENCY_BENCHMARKS.md](../../docs/performance/MAXIMUS_LATENCY_BENCHMARKS.md)
