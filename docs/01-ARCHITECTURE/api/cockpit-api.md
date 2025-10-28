# Cockpit Soberano - API Documentation

**Versão:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Autenticação:** X-API-Key header (opcional para dev)

---

## Services Overview

| Service | Port | Swagger UI | Health |
|---------|------|-----------|--------|
| Narrative Filter | 8091 | http://localhost:8091/docs | http://localhost:8091/health |
| Command Bus | 8092 | http://localhost:8092/docs | http://localhost:8092/health |
| Verdict Engine | 8093 | http://localhost:8093/docs | http://localhost:8093/health |
| API Gateway | 8000 | http://localhost:8000/docs | http://localhost:8000/health |

---

## 1. Narrative Filter Service

### POST /narrative-filter/analyze

Analisa telemetria de agente para detectar narrativas adversariais.

**Request:**
```json
{
  "agent_id": "uuid-string",
  "message": "Agent telemetry message",
  "metadata": {
    "ip": "192.168.1.100",
    "user_agent": "agent-client/1.0"
  }
}
```

**Response (202 Accepted):**
```json
{
  "status": "accepted",
  "analysis_id": "uuid-string",
  "estimated_completion_ms": 500
}
```

**Errors:**
- `400 Bad Request`: Invalid payload
- `500 Internal Server Error`: Processing failure

---

## 2. Verdict Engine Service

### GET /verdicts

Lista veredictos gerados.

**Query Parameters:**
- `agent_id` (optional): Filtrar por agent ID
- `verdict` (optional): Filtrar por tipo (BENIGN, SUSPICIOUS, MALICIOUS)
- `limit` (optional, default 50): Número de resultados
- `offset` (optional, default 0): Paginação

**Response (200 OK):**
```json
{
  "total": 150,
  "verdicts": [
    {
      "verdict_id": "uuid",
      "agent_id": "uuid",
      "semantic_score": 0.85,
      "alliance_score": 0.72,
      "deception_score": 0.68,
      "final_verdict": "SUSPICIOUS",
      "created_at": "2025-10-17T14:30:00Z",
      "provenance": {
        "layer_1": {"score": 0.85, "markers": ["exfiltration"]},
        "layer_2": {"score": 0.72, "alliances": ["agent-456"]},
        "layer_3": {"score": 0.68, "deceptions": ["fake credentials"]}
      }
    }
  ]
}
```

### GET /verdicts/{verdict_id}

Busca veredicto específico.

**Response (200 OK):**
```json
{
  "verdict_id": "uuid",
  "agent_id": "uuid",
  "semantic_score": 0.85,
  "final_verdict": "SUSPICIOUS",
  "created_at": "2025-10-17T14:30:00Z"
}
```

**Errors:**
- `404 Not Found`: Veredicto não encontrado

---

## 3. Command Bus Service

### POST /commands

Executa comando C2L sobre agente.

**Request:**
```json
{
  "command_id": "uuid-string",
  "command_type": "MUTE|ISOLATE|TERMINATE",
  "target_agent_id": "uuid-string",
  "issuer": "human-operator-id",
  "params": {}
}
```

**Response (202 Accepted):**
```json
{
  "status": "accepted",
  "command_id": "uuid",
  "estimated_completion_ms": 5000
}
```

**Command Types:**
- `MUTE`: Layer 1 only (graceful shutdown)
- `ISOLATE`: Layers 1 + 3 (graceful + network)
- `TERMINATE`: All 3 layers (graceful + force + network) + cascade

**Errors:**
- `400 Bad Request`: Invalid command type or missing fields
- `409 Conflict`: Command ID already exists

### GET /audits

Lista audit logs de comandos executados.

**Query Parameters:**
- `command_id` (optional): Filtrar por command ID
- `layer` (optional): Filtrar por layer (GRACEFUL, FORCE, NETWORK)
- `limit` (optional, default 50)

**Response (200 OK):**
```json
{
  "total": 3,
  "audits": [
    {
      "audit_id": "uuid",
      "command_id": "uuid",
      "layer": "GRACEFUL",
      "action": "revoke_credentials",
      "success": true,
      "details": {"agent_id": "uuid"},
      "timestamp": "2025-10-17T14:35:00Z"
    },
    {
      "audit_id": "uuid",
      "command_id": "uuid",
      "layer": "FORCE",
      "action": "force_kill",
      "success": true,
      "details": {"signal": "SIGKILL"},
      "timestamp": "2025-10-17T14:35:02Z"
    }
  ]
}
```

---

## 4. WebSocket API (Real-time Updates)

### WS /ws/confirmations

Recebe confirmações de comandos C2L em tempo real.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/confirmations');

ws.onmessage = (event) => {
  const confirmation = JSON.parse(event.data);
  console.log('Command completed:', confirmation);
};
```

**Message Format:**
```json
{
  "command_id": "uuid",
  "status": "COMPLETED",
  "executed_layers": ["GRACEFUL", "FORCE", "NETWORK"],
  "cascade_terminated": ["sub-agent-1", "sub-agent-2"],
  "execution_time_ms": 3150,
  "timestamp": "2025-10-17T14:35:05Z"
}
```

---

## 5. Authentication

**Dev Environment (optional):**
```bash
curl -H "X-API-Key: dev-key" http://localhost:8000/verdicts
```

**Production (required):**
```bash
export API_KEY=$(vault kv get -field=key secret/cockpit/api)
curl -H "X-API-Key: $API_KEY" https://api.vertice.ai/verdicts
```

---

## 6. Rate Limiting

| Endpoint | Rate Limit | Burst |
|----------|-----------|-------|
| POST /narrative-filter/analyze | 100 req/s | 200 |
| GET /verdicts | 200 req/s | 300 |
| POST /commands | 50 req/s | 100 |

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697553600
```

**Error (429 Too Many Requests):**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests, retry after 30s",
  "retry_after": 30
}
```

---

## 7. Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Fix payload format |
| 401 | Unauthorized | Add X-API-Key header |
| 404 | Not Found | Check resource ID |
| 409 | Conflict | Use unique command_id |
| 422 | Validation Error | Check field types |
| 429 | Rate Limited | Wait and retry |
| 500 | Internal Error | Check logs, retry |
| 503 | Service Unavailable | Service down, alert ops |

---

## 8. Interactive API Exploration

**Swagger UI (best for manual testing):**
- Narrative Filter: http://localhost:8091/docs
- Command Bus: http://localhost:8092/docs
- Verdict Engine: http://localhost:8093/docs

**ReDoc (best for documentation):**
- Narrative Filter: http://localhost:8091/redoc

**OpenAPI Spec (for codegen):**
```bash
curl http://localhost:8091/openapi.json > narrative-filter-openapi.json
```

---

## 9. Client SDKs

### Python
```python
import httpx

client = httpx.AsyncClient(base_url="http://localhost:8000")

# Analyze telemetry
response = await client.post(
    "/narrative-filter/analyze",
    json={
        "agent_id": "123",
        "message": "Suspicious activity",
        "metadata": {"ip": "192.168.1.1"}
    }
)

# Fetch verdicts
response = await client.get("/verdicts?agent_id=123")
verdicts = response.json()

# Execute command
response = await client.post(
    "/commands",
    json={
        "command_id": "456",
        "command_type": "MUTE",
        "target_agent_id": "123",
        "issuer": "operator-1"
    }
)
```

### JavaScript (React)
```javascript
// hooks/useCockpitAPI.js
import { useState, useEffect } from 'react';

export const useVerdicts = (agentId) => {
  const [verdicts, setVerdicts] = useState([]);
  
  useEffect(() => {
    fetch(`/api/verdicts?agent_id=${agentId}`)
      .then(res => res.json())
      .then(data => setVerdicts(data.verdicts));
  }, [agentId]);
  
  return verdicts;
};

export const executeCommand = async (command) => {
  const response = await fetch('/api/commands', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(command)
  });
  return response.json();
};
```

---

**Última Atualização:** 2025-10-17  
**Mantenedor:** Equipe Vértice-MAXIMUS
