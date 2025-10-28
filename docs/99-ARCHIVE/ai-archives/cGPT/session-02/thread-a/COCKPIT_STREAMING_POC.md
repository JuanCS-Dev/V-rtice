# Thread A · Cockpit Híbrido – Protótipo de Streaming Consciente

## 1. Objetivo
Permitir que o TUI (Bubble Tea) e o frontend React recebam, em tempo real, métricas de consciência do MAXIMUS (arousal, dopamina, ESGT, violações) através de um protocolo unificado.

## 2. Arquitetura Proposta
```
MAXIMUS Core (gRPC stream) ──┐
                             │
Gateway Streaming Bridge ────┼──> SSE/WebSocket → Frontend React (React Query)
                             │
                             └──> gRPC ↔ CLI vcli-go (Bubble Tea TUI)
```

- **MAXIMUS** publica métricas através de gRPC streams (`ConsciousnessStream`).
- **Streaming Bridge** (novo serviço leve) converte gRPC → HTTP SSE e WebSocket.
- **CLI** continua consumindo gRPC diretamente (latência mínima).
- **Frontend** consome SSE/WebSocket encapsulado (auto-reconnect, fallback).

## 3. Contrato de Payload
```json
{
  "timestamp": "2025-10-08T14:35:12Z",
  "eventType": "neuromodulation.dopamine.spike",
  "metrics": {
    "dopamine_level": 0.82,
    "arousal": 0.67,
    "coherence": 0.91
  },
  "context": {
    "skill": "threat_intel_correlation",
    "trigger": "HSAS::Alert#12345"
  },
  "severity": "medium"
}
```

- Suporta adicionando `safety.kill_switch.triggered`, `skill.learning.update`, etc.
- `severity` mapeia para níveis visuais (verde, amarelo, vermelho).
- `context` fornece narrativa (relacionar a dashboards e logs).

## 4. Protocolo SSE/WebSocket
- **Endpoint SSE**: `GET /stream/consciousness/sse` (headers: `Authorization`, `X-Trace-Id`).
- **Endpoint WebSocket**: `GET /stream/consciousness/ws`.
- Reconnect exponencial (1s, 2s, 4s… até 30s).
- Compressão (gzip) habilitada para SSE.
- Mensagens send-only; acknowledgements via gRPC se necessário (para CLI).

## 5. Integração no Frontend
- Hook React Query customizado (`useConsciousnessStream`) com fallback a polling.
- Zustand store para manter estado atual (último evento, histórico curto).
- Visualizações:
  - **Timeline** (sparklines) para dopamina/arousal.
  - **Widget de Safety** muda cor se severity >= HIGH.
  - **Narrativas**: componentes que exibem `context` em linguagem natural.

## 6. Integração no TUI
- Bubble Tea: novo “widget” com event loop assíncrono recebendo gRPC stream.
- Buffer de eventos (limite 100) + filtros por severity.
- Comando `/stream pause|resume` controlando ingestão.

## 7. Autenticação & Segurança
- Tokens JWT para SSE/WebSocket (validação por Gateway).
- gRPC utiliza mTLS (SPIFFE IDs).
- Todos os eventos propagam `trace_id` para correlação com logs/dashboard.

## 8. Métricas & Observabilidade
- Métricas do bridge:
  - `stream.connected_clients`
  - `stream.messages_delivered_total`
  - `stream.delivery_latency_ms`
- Logs estruturados por evento (JSON).

## 9. Próximas Ações
1. Implementar serviço bridge (PoC) e validar latência < 500 ms.
2. Ajustar frontend (React Query hook + componentes).
3. Atualizar CLI com comando `/stream` e UI real-time.
4. Documentar fallback (em caso de streaming indisponível).
