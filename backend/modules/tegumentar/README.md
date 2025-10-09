# Tegumentar Module – Biomimetic Firewall

O módulo Tegumentar implementa a pele digital do MAXIMUS AI. Inspirado nas camadas epiderme/derme/hipoderme, fornece defesa adaptativa, reflexos de latência zero e integração cognitiva.

## Estrutura do Pacote

```
backend/modules/tegumentar
├── config.py                 # Pydantic settings (Redis, Kafka, Postgres, etc.)
├── orchestrator.py           # Ponto de entrada para MAXIMUS
├── epiderme/                 # Filtro stateless + eBPF reflex arc
├── derme/                    # Stateful inspection, DPI híbrido, Células de Langerhans
├── hipoderme/                # Permeabilidade adaptativa, SOAR, interface MMEI
└── resources/
    ├── cache/blocked_ips.txt # Cache local de reputação (gerenciado automaticamente)
    ├── ml/baseline_dataset.csv
    ├── playbooks/            # Playbooks SOAR (ex.: critical_intrusion.yaml)
    └── signatures/           # Regras YAML (ex.: web_attacks.yaml)
```

## Dependências Externas

- Linux com suporte a **eBPF/XDP** (`clang`, `libbcc`/`python3-bcc`, `ip`).
- `nftables` para filtragem stateless.
- Redis, Kafka e PostgreSQL (TimescaleDB recomendado).
- `tc` (Traffic Control) para throttling adaptativo.

## Configuração

Variáveis com prefixo `TEGUMENTAR_` podem sobrescrever os defaults definidos em `config.py`. Arquivos gerados em runtime
(cache de reputação e modelos) são gravados em `~/.cache/tegumentar/` por padrão.
Exemplos de overrides:

```bash
export TEGUMENTAR_REDIS_URL=redis://redis.internal:6379/5
export TEGUMENTAR_KAFKA_BOOTSTRAP_SERVERS=kafka.internal:9092
export TEGUMENTAR_POSTGRES_DSN=postgresql+asyncpg://tegumentar:secret@db/tegumentar
export TEGUMENTAR_SIGNATURE_DIRECTORY=/opt/tegumentar/signatures
export TEGUMENTAR_SOAR_PLAYBOOKS_PATH=/opt/tegumentar/playbooks
```

## Inicialização Programática

```python
from backend.modules.tegumentar import TegumentarModule
from backend.modules.tegumentar.derme import FlowObservation

module = TegumentarModule()

async def boot():
    await module.startup(interface="eth0")

asyncio.run(boot())
```

O orchestrator expõe um `FastAPI` via `module.fastapi_app()` com rotas:

- `POST /api/tegumentar/posture` → ajusta permeabilidade (`LOCKDOWN`, `HARDENED`, `BALANCED`, `EXPLORE`)
- `GET /api/tegumentar/status` → estado e qualia atuais
- `POST /api/tegumentar/wound-healing` → executa playbooks

## Fluxo Operacional

1. **Epiderme**: sincroniza blocklists reais, aplica rate limiting distribuído e acopla `xdp_reflex_firewall` ao dispositivo de rede. Eventos reflexos são enviados ao Kafka (`tegumentar.reflex`).
2. **Derme**: mantém estado de conexões em PostgreSQL, executa DPI híbrido (assinaturas + Isolation Forest). Anomalias fortes viram antígenos publicados em `tegumentar.langerhans`.
3. **Hipoderme**: controla a permeabilidade (nftables + SDN), dispara playbooks SOAR (`critical_intrusion.yaml`) e publica vetor de qualia para o MMEI.

## Treinamento do Modelo de Anomalia

Se `anomaly_detector.joblib` não existir, o módulo treina automaticamente usando `baseline_dataset.csv`. Para treinar com dataset personalizado:

```bash
python -m backend.modules.tegumentar.derme.ml.train --dataset /data/flows.csv --output /etc/tegumentar/models/anomaly_detector.joblib
```

(script detalhado em `derme/ml/train.py`).

## Observabilidade

- Métricas Prometheus expostas em `/metrics` (`TEGUMENTAR_PROMETHEUS_METRICS_PORT`).
- Contadores e histogramas: reflexos, antígenos, validações do Linfonodo e vacinações.
- Eventos de reflexo e antígenos enviados via Kafka.
- Sessões e antígenos persistidos em PostgreSQL.

## Segurança

- `NO MOCK`: rotas executam comandos reais (`nft`, `tc`, `systemctl`) e interagem com serviços MAXIMUS.
- `QUALITY-FIRST`: validações rigorosas, conexões seguras (TLS nos endpoints SDN/MMEI recomendados).
- Documentação fenomenológica: vetor de qualia descreve “pressão”, “temperatura” e “dor” derivadas dos fluxos de rede para integração com o sistema sensorial.

## Próximos Passos

- Adicionar testes de caos (Gremlin/Litmus) focados em DDoS e perda de Kafka.
- Integrar métricas ao Grafana e alarmes ao Alertmanager.
- Publicar novos playbooks assinados para cenários setoriais (finanças, ICS, saúde).
