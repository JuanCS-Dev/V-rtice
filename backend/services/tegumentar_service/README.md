# Tegumentar Service

FastAPI gateway para expor o Módulo Tegumentar do MAXIMUS AI. O serviço inicia
o firewall biomimético, acopla o arco reflexo XDP à interface especificada e
disponibiliza as rotas `/api/tegumentar/*` para controle cognitivo, postura e
playbooks de cicatrização.

## Pré-requisitos

- Kernel Linux com suporte a eBPF/XDP.
- Permissões para executar `nft`, `tc`, `ip link` e carregar programas eBPF.
- Redis, Kafka e PostgreSQL acessíveis conforme configurado em variáveis de
  ambiente `TEGUMENTAR_*`.

## Execução Local

```bash
cd backend/services/tegumentar_service
python -m backend.services.tegumentar_service.main
```

Variáveis chave (ver `.env.example`):

- `TEGUMENTAR_SERVICE_INTERFACE`: interface de rede (ex.: `eth0`).
- `TEGUMENTAR_REDIS_URL`, `TEGUMENTAR_KAFKA_BOOTSTRAP_SERVERS`,
  `TEGUMENTAR_POSTGRES_DSN`: apontam para infra real.

## Docker

```bash
docker build -t tegumentar-service .
docker run --rm --net=host --privileged \
  -e TEGUMENTAR_SERVICE_INTERFACE=eth0 \
  -e TEGUMENTAR_REDIS_URL=redis://localhost:6379/0 \
  -e TEGUMENTAR_KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
  -e TEGUMENTAR_POSTGRES_DSN=postgresql+asyncpg://tegumentar:tegumentar@localhost:5432/tegumentar \
  tegumentar-service
```

> O contêiner precisa de modo privilegiado ou capabilities específicas para
> anexar o programa XDP.

## API

A aplicação exposta em `app.py` reutiliza o FastAPI do módulo Tegumentar.
Rotas principais:

- `POST /api/tegumentar/posture` – ajusta permeabilidade (`LOCKDOWN`, `HARDENED`,
  `BALANCED`, `EXPLORE`).
- `GET /api/tegumentar/status` – estado atual, vetor de qualia e interface.
- `GET /api/tegumentar/qualia` – snapshot sensorial para MMEI.
- `POST /api/tegumentar/wound-healing` – executa playbook SOAR definido em
  `resources/playbooks/`.

## Observabilidade

O módulo expõe métricas Prometheus na porta configurada por
`TEGUMENTAR_PROMETHEUS_METRICS_PORT`. Grafana/Alertmanager podem consumir as
contagens de reflexos, bloqueios, anomalias e cicatrizações para dashboards e
alertas.

## Segurança

- Código 100% funcional: interage com nftables, eBPF, Redis, Kafka e PostgreSQL.
- Sem mocks nem placeholders. Falhas de dependência resultam em erro explícito.
- Recomenda-se rodar testes de carga DDoS/zero-day em staging antes de produção.
