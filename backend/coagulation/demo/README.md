# 🩸 Multi-Agent Demo

Demonstração de 3 agentes plaquetários comunicando via P2P e detectando breaches coordenadamente.

## Pré-requisitos

```bash
# 1. NATS JetStream rodando
docker run -d --name nats-coagulation -p 4222:4222 -p 8222:8222 nats:2.10-alpine -js

# 2. Agent compilado
cd backend/coagulation
go build -o bin/platelet-agent ./platelet_agent/agent.go
```

## Executar Demo

```bash
./demo/multi_agent_demo.sh
```

## O que acontece

1. **3 agents iniciam** com thresholds diferentes:
   - `platelet-alpha`: 0.6 (mais sensível)
   - `platelet-beta`: 0.7 (moderado)
   - `platelet-gamma`: 0.8 (menos sensível)

2. **Monitoramento contínuo**: Cada agent monitora processos locais

3. **Detecção distribuída**: Agent detecta anomalia → ativa → emite sinal P2P

4. **Amplificação**: Peers recebem sinal → aumentam sensibilidade → ativam

5. **Cascata**: Severity ≥0.8 → Emite breach_detected → Trigger Factor VIIa

## Arquitetura Demonstrada

```
Agent Alpha (0.6)  ──┐
                     ├──> NATS (P2P signaling)
Agent Beta (0.7)   ──┤
                     │
Agent Gamma (0.8)  ──┘
```

## Verificar Comunicação

```bash
# Ver métricas
curl localhost:8222/varz

# Ver logs
docker logs nats-coagulation
```

## Biological Analogy

- **Resting State**: Agents circulam monitarando
- **Activation**: Threshold excedido (lesão detectada)
- **P2P Signaling**: ADP/TXA2 digital (NATS pub/sub)
- **Aggregation**: Convergência coordenada no breach
- **Cascade Trigger**: Factor VIIa activation (próxima fase)

---

**"As plaquetas circulam. A cascata se prepara."** 🩸
