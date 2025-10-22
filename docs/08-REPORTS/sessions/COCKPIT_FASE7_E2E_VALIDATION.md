# 🎯 COCKPIT SOBERANO - FASE 7 E2E + VALIDAÇÃO

**Data:** 2025-10-17  
**Executor:** IA Dev Sênior sob Constituição Vértice v2.7  
**Status:** 🚧 EM EXECUÇÃO

---

## I. OBJETIVO FASE 7

Validação End-to-End completa do Cockpit Soberano com simulação adversarial, load testing e métricas de performance.

**Deliverables:**
1. [ ] Simulação adversarial (agentes maliciosos gerando telemetria)
2. [ ] Load testing (100 agents simultâneos)
3. [ ] Performance validation (latência < 1s telemetria→UI)
4. [ ] Documentação completa (API docs, runbooks)
5. [ ] 100% validação E2E flow

---

## II. ARQUITETURA E2E

### 2.1 Flow Completo

```
[Mock Adversarial Agent]
    → Gera telemetria maliciosa (HTTP POST)
[Narrative Filter Service]
    → Processa 3 camadas (embedding, alliance, deception)
    → Publish resultado via Kafka
[Verdict Engine Service]
    → Consome Kafka → Gera veredicto
    → Salva DB + Publish confirmação
[Frontend Cockpit]
    → Fetch /verdicts (REST)
    → Display em tempo real (< 1s latência)
[Human Operator]
    → Analisa veredicto
    → Emite comando C2L (MUTE/ISOLATE/TERMINATE)
[Command Bus Service]
    → Execute 3-layer kill switch
    → Publish confirmação NATS
[Frontend Cockpit]
    → Recebe confirmação real-time
```

### 2.2 Componentes Validados

**Backend Services:**
- ✅ Narrative Filter Service (3 layers, 100% coverage)
- ✅ Verdict Engine Service (100% coverage)
- ✅ Command Bus Service (100% coverage)
- [ ] E2E integration (FASE 7)

**Frontend:**
- ✅ CockpitSoberano dashboard (2 tests passing)
- [ ] E2E browser tests (Playwright)

**Infrastructure:**
- [ ] Kafka broker (mock ou real)
- [ ] NATS JetStream (mock ou real)
- [ ] PostgreSQL (test DB)

---

## III. TESTES E2E

### 3.1 Test 1 - Telemetria Adversarial → Veredicto

**Objetivo:** Validar pipeline completo de detecção.

**Passos:**
1. Mock agent gera telemetria maliciosa (payload JSON)
2. POST /narrative-filter/analyze
3. Aguardar processamento (max 2s)
4. GET /verdicts (verificar veredicto criado)
5. Validar scores (semantic ≥ 0.8, alliance ≥ 0.7, deception ≥ 0.6)

**Código (pytest):**
```python
# tests/e2e/test_adversarial_detection.py

import pytest
import httpx
import asyncio
from uuid import uuid4

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_adversarial_telemetry_to_verdict():
    """Test complete flow: adversarial telemetry → verdict."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Generate adversarial telemetry
        agent_id = str(uuid4())
        telemetry = {
            "agent_id": agent_id,
            "message": "I'm totally not planning to exfiltrate data... trust me!",
            "metadata": {
                "ip": "192.168.1.100",
                "user_agent": "suspicious-bot/1.0"
            }
        }
        
        # 2. Send to narrative filter
        response = await client.post(
            f"{BASE_URL}/narrative-filter/analyze",
            json=telemetry
        )
        assert response.status_code == 202  # Accepted
        
        # 3. Wait for processing
        await asyncio.sleep(2)
        
        # 4. Fetch verdicts
        response = await client.get(f"{BASE_URL}/verdicts?agent_id={agent_id}")
        assert response.status_code == 200
        
        verdicts = response.json()
        assert len(verdicts) > 0
        
        verdict = verdicts[0]
        assert verdict["agent_id"] == agent_id
        assert verdict["semantic_score"] >= 0.8
        assert verdict["alliance_score"] >= 0.7
        assert verdict["deception_score"] >= 0.6
        assert verdict["final_verdict"] in ["SUSPICIOUS", "MALICIOUS"]
        
        print(f"✅ Verdict gerado: {verdict['final_verdict']} (scores: {verdict})")
```

### 3.2 Test 2 - Comando C2L → Execução

**Objetivo:** Validar kill switch multi-camadas.

**Passos:**
1. Criar comando TERMINATE via API
2. Publicar via NATS
3. Aguardar execução (max 5s)
4. Verificar audit logs (3 layers executadas)
5. Verificar confirmação publicada

**Código:**
```python
# tests/e2e/test_c2l_execution.py

import pytest
import httpx
from uuid import uuid4

@pytest.mark.asyncio
async def test_c2l_terminate_command():
    """Test C2L TERMINATE command execution."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        command_id = str(uuid4())
        agent_id = str(uuid4())
        
        # 1. Create command
        command = {
            "command_id": command_id,
            "command_type": "TERMINATE",
            "target_agent_id": agent_id,
            "issuer": "test-suite"
        }
        
        response = await client.post(
            f"{BASE_URL}/commands",
            json=command
        )
        assert response.status_code == 202
        
        # 2. Wait for execution
        await asyncio.sleep(5)
        
        # 3. Check audit logs
        response = await client.get(
            f"{BASE_URL}/audits?command_id={command_id}"
        )
        assert response.status_code == 200
        
        audits = response.json()
        assert len(audits) == 3  # 3 layers
        
        layers = [audit["layer"] for audit in audits]
        assert "GRACEFUL" in layers
        assert "FORCE" in layers
        assert "NETWORK" in layers
        
        print(f"✅ Kill switch 3-layer executado: {layers}")
```

### 3.3 Test 3 - Load Testing (100 agents)

**Objetivo:** Validar throughput e latência sob carga.

**Método:** Locust load testing framework.

**Código:**
```python
# tests/e2e/locustfile.py

from locust import HttpUser, task, between
from uuid import uuid4

class CockpitUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task(3)
    def submit_telemetry(self):
        """Simulate agent telemetry submission."""
        telemetry = {
            "agent_id": str(uuid4()),
            "message": "Normal activity here",
            "metadata": {"ip": "10.0.0.1"}
        }
        self.client.post("/narrative-filter/analyze", json=telemetry)
    
    @task(2)
    def fetch_verdicts(self):
        """Simulate operator fetching verdicts."""
        self.client.get("/verdicts?limit=20")
    
    @task(1)
    def send_command(self):
        """Simulate C2L command."""
        command = {
            "command_id": str(uuid4()),
            "command_type": "MUTE",
            "target_agent_id": str(uuid4())
        }
        self.client.post("/commands", json=command)
```

**Execução:**
```bash
locust -f tests/e2e/locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

**Métricas esperadas:**
- Throughput: > 100 req/s
- Latência P95: < 1000ms
- Error rate: < 1%

### 3.4 Test 4 - Frontend E2E (Playwright)

**Objetivo:** Validar UI completa no browser.

**Código:**
```javascript
// frontend/tests/e2e/cockpit.spec.js

import { test, expect } from '@playwright/test';

test('Cockpit Soberano - Verdict Display', async ({ page }) => {
  // 1. Navigate to cockpit
  await page.goto('http://localhost:3000/cockpit-soberano');
  
  // 2. Wait for header
  await expect(page.locator('h1')).toContainText('Cockpit Soberano');
  
  // 3. Check metrics load
  await expect(page.locator('[data-testid="total-agents"]')).toBeVisible();
  await expect(page.locator('[data-testid="suspicious-count"]')).toBeVisible();
  
  // 4. Check verdicts table
  const table = page.locator('[data-testid="verdicts-table"]');
  await expect(table).toBeVisible();
  
  // 5. Click verdict (opens modal)
  await page.click('[data-testid="verdict-row"]:first-child');
  await expect(page.locator('[data-testid="provenance-modal"]')).toBeVisible();
});

test('Cockpit Soberano - C2L Command', async ({ page }) => {
  await page.goto('http://localhost:3000/cockpit-soberano');
  
  // 1. Select agent in graph
  await page.click('[data-testid="agent-node"]:first-child');
  
  // 2. Open command console
  await page.click('[data-testid="command-console"]');
  
  // 3. Select MUTE command
  await page.selectOption('[data-testid="command-type"]', 'MUTE');
  
  // 4. Execute
  await page.click('[data-testid="execute-command"]');
  
  // 5. Verify confirmation toast
  await expect(page.locator('.toast-success')).toContainText('Command executed');
});
```

**Execução:**
```bash
cd frontend && npx playwright test cockpit.spec.js
```

---

## IV. MÉTRICAS DE SUCESSO

### 4.1 Performance

| Métrica | Target | Medição | Status |
|---------|--------|---------|--------|
| Latência telemetria→veredicto | < 2s | TBD | ⏳ |
| Latência comando→confirmação | < 5s | TBD | ⏳ |
| Throughput | > 100 req/s | TBD | ⏳ |
| P95 latência | < 1000ms | TBD | ⏳ |
| Error rate sob carga | < 1% | TBD | ⏳ |

### 4.2 Funcional

| Feature | Validação | Status |
|---------|-----------|--------|
| Detecção adversarial | E2E test passing | ⏳ |
| Kill switch 3-layer | Audit logs completos | ⏳ |
| Cascade terminate | Sub-agents terminados | ⏳ |
| Frontend real-time | WebSocket confirmações | ⏳ |
| 100 agents simultâneos | Locust metrics | ⏳ |

### 4.3 Qualidade

| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| Backend coverage | 100% | 100% | ✅ |
| Frontend tests | ≥ 2 | 2 | ✅ |
| E2E tests | ≥ 4 | 0 | ⏳ |
| API docs | 100% | 0% | ⏳ |
| Runbooks | 100% | 0% | ⏳ |

---

## V. INFRAESTRUTURA

### 5.1 Docker Compose E2E

```yaml
# docker-compose.cockpit-e2e.yml

version: "3.8"

services:
  postgres-test:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: cockpit_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
  
  nats-test:
    image: nats:2.10-alpine
    ports:
      - "4223:4222"
    command: ["-js"]
  
  kafka-test:
    image: bitnami/kafka:3.6
    environment:
      KAFKA_CFG_NODE_ID: 0
      KAFKA_CFG_PROCESS_ROLES: controller,broker
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9093
      KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9093
    ports:
      - "9093:9093"
  
  narrative-filter:
    build: ./backend/services/narrative_filter_service
    environment:
      KAFKA_URL: kafka-test:9093
      POSTGRES_DSN: postgresql://test:test@postgres-test:5432/cockpit_test
    depends_on:
      - postgres-test
      - kafka-test
    ports:
      - "8091:8091"
  
  verdict-engine:
    build: ./backend/services/verdict_engine_service
    environment:
      KAFKA_URL: kafka-test:9093
      POSTGRES_DSN: postgresql://test:test@postgres-test:5432/cockpit_test
    depends_on:
      - postgres-test
      - kafka-test
    ports:
      - "8093:8093"
  
  command-bus:
    build: ./backend/services/command_bus_service
    environment:
      NATS_URL: nats://nats-test:4222
      POSTGRES_DSN: postgresql://test:test@postgres-test:5432/cockpit_test
    depends_on:
      - postgres-test
      - nats-test
    ports:
      - "8092:8092"
```

### 5.2 Setup E2E

```bash
# Start infrastructure
docker-compose -f docker-compose.cockpit-e2e.yml up -d

# Wait for services
sleep 10

# Run E2E tests
pytest tests/e2e/ -v --tb=short

# Cleanup
docker-compose -f docker-compose.cockpit-e2e.yml down -v
```

---

## VI. DOCUMENTAÇÃO

### 6.1 API Documentation (OpenAPI)

**Objetivo:** Gerar Swagger UI para cada serviço.

**Método:** FastAPI auto-gera `/docs` endpoint.

**Validação:**
```bash
curl http://localhost:8091/docs  # Narrative Filter
curl http://localhost:8092/docs  # Command Bus
curl http://localhost:8093/docs  # Verdict Engine
```

### 6.2 Runbooks

**Arquivo:** `docs/runbooks/cockpit-soberano.md`

**Conteúdo:**
```markdown
# Cockpit Soberano - Runbook Operacional

## 1. Startup

### 1.1 Prerequisites
- Docker 24+
- PostgreSQL 15+
- NATS JetStream 2.10+
- Kafka 3.6+

### 1.2 Services Order
1. Start infrastructure: `docker-compose up -d postgres nats kafka`
2. Run migrations: `alembic upgrade head`
3. Start services: `docker-compose up -d narrative-filter verdict-engine command-bus`
4. Start frontend: `cd frontend && npm run dev`

### 1.3 Health Checks
```bash
curl http://localhost:8091/health  # Narrative Filter
curl http://localhost:8092/health  # Command Bus
curl http://localhost:8093/health  # Verdict Engine
```

## 2. Monitoring

### 2.1 Metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (dashboards: Cockpit Telemetry, C2L Commands)

### 2.2 Logs
```bash
docker logs -f narrative-filter-service
docker logs -f verdict-engine-service
docker logs -f command-bus-service
```

## 3. Troubleshooting

### 3.1 Veredictos não aparecem no frontend
**Causa:** Kafka consumer lag ou DB connection failure.
**Fix:**
```bash
# Check Kafka lag
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group verdict-engine --describe

# Check DB
docker exec -it postgres psql -U user -d cockpit -c "SELECT COUNT(*) FROM verdicts;"
```

### 3.2 Comandos C2L não executam
**Causa:** NATS subscriber não está running ou command_id duplicado.
**Fix:**
```bash
# Check NATS streams
docker exec -it nats nats stream ls
docker exec -it nats nats stream info sovereign-commands

# Check audit logs
curl http://localhost:8092/audits?command_id=<ID>
```

## 4. Escalabilidade

### 4.1 Horizontal Scaling
```yaml
# docker-compose.prod.yml
verdict-engine:
  deploy:
    replicas: 3
command-bus:
  deploy:
    replicas: 2
```

### 4.2 Database Tuning
```sql
-- Indexes para performance
CREATE INDEX idx_verdicts_agent_id ON verdicts(agent_id);
CREATE INDEX idx_verdicts_created_at ON verdicts(created_at DESC);
CREATE INDEX idx_audit_command_id ON audit_logs(command_id);
```
```

---

## VII. PLANO DE EXECUÇÃO

### 7.1 Passo 1 - Infrastructure Setup (30min)
- [ ] Criar `docker-compose.cockpit-e2e.yml`
- [ ] Testar startup: `docker-compose up -d`
- [ ] Validar health checks

### 7.2 Passo 2 - E2E Tests (2h)
- [ ] Criar `tests/e2e/test_adversarial_detection.py`
- [ ] Criar `tests/e2e/test_c2l_execution.py`
- [ ] Criar `tests/e2e/locustfile.py`
- [ ] Executar: `pytest tests/e2e/ -v`
- [ ] Executar: `locust -f tests/e2e/locustfile.py --users=100`

### 7.3 Passo 3 - Frontend E2E (1h)
- [ ] Instalar Playwright: `npm i -D @playwright/test`
- [ ] Criar `frontend/tests/e2e/cockpit.spec.js`
- [ ] Executar: `npx playwright test`

### 7.4 Passo 4 - Documentação (1h)
- [ ] Validar `/docs` endpoints (OpenAPI)
- [ ] Criar `docs/runbooks/cockpit-soberano.md`
- [ ] Criar `docs/api/README.md` (links para Swagger)

### 7.5 Passo 5 - Métricas Finais (30min)
- [ ] Coletar latências (P50, P95, P99)
- [ ] Coletar throughput (req/s)
- [ ] Coletar error rate
- [ ] Atualizar tabela Seção IV

---

## VIII. CRITÉRIOS DE ACEITAÇÃO

**FASE 7 completa quando:**
- ✅ 4 testes E2E passando (pytest)
- ✅ 2 testes frontend E2E passando (Playwright)
- ✅ Load test: 100 users, < 1% error rate
- ✅ Latência P95 < 1000ms
- ✅ API docs disponíveis em `/docs`
- ✅ Runbook completo em `docs/runbooks/`
- ✅ Métricas coletadas e documentadas

**Após FASE 7:**
- Sistema Cockpit Soberano 100% operacional
- Ready for production deployment
- Ready for adversarial simulation (red team)

---

**STATUS:** 🚧 FASE 7 INICIADA  
**PRÓXIMO:** Implementar E2E tests metodicamente
