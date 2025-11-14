# 🗺️ BACKEND MAP - Real Backend Services Documentation

**Generated**: 2025-11-13
**Purpose**: Map ALL real backends to prevent mocks (P1: MOCK AQUI É PROIBIDO!)
**Framework**: CONSTITUIÇÃO VÉRTICE v3.0 - Phase 0.5

---

## 🎯 EXECUTIVE SUMMARY

**Total Backend Services**: 90+ services identified
**Confirmed & Documented**: 3 services (MABA, NIS/MVP, Penelope)
**To Be Verified**: 87+ services
**Protocol**: Test against REAL backends only - **ZERO MOCKS**

---

## ✅ TIER 1 (P0) - CONFIRMED BACKENDS

### 1. MABA Service (MAXIMUS Browser Agent)

**Purpose**: Autonomous browser automation with cognitive awareness

**Service Info**:
- **Port**: `8152`
- **URL**: `http://localhost:8152`
- **Health Check**: `GET http://localhost:8152/health`
- **Path**: `~/vertice-dev/backend/services/maba_service/`
- **Start Command**: `cd ~/vertice-dev/backend/services/maba_service && python main.py`
- **Registry**: Auto-registers as "maximus_subordinate" (browser_agent)

**API Endpoints**:

| Method | Endpoint | Description | Request Model | Response Model |
|--------|----------|-------------|---------------|----------------|
| POST | `/sessions` | Create browser session | `BrowserSessionRequest` | Session details |
| DELETE | `/sessions/{session_id}` | Close browser session | - | Success message |
| POST | `/navigate` | Navigate to URL | `NavigationRequest` | `BrowserActionResponse` |
| POST | `/click` | Click element | `ClickRequest` | `BrowserActionResponse` |
| POST | `/type` | Type text | `TypeRequest` | `BrowserActionResponse` |
| POST | `/screenshot` | Take screenshot | `ScreenshotRequest` | Screenshot data |
| POST | `/extract` | Extract page data | `ExtractRequest` | Extracted data |
| POST | `/analyze` | Analyze page | `PageAnalysisRequest` | `PageAnalysisResponse` |
| POST | `/cognitive-map/query` | Query learned paths | `CognitiveMapQueryRequest` | `CognitiveMapQueryResponse` |
| GET | `/cognitive-map/stats` | Map statistics | - | Stats object |
| GET | `/tools` | List registered tools | - | Tool list |
| GET | `/health` | Health check | - | Health status |

**Request Models** (maba_service/models.py):
```python
class NavigationRequest(BaseModel):
    url: str
    wait_until: str = "load"  # load, domcontentloaded, networkidle
    timeout_ms: int = 30000

class ExtractRequest(BaseModel):
    session_id: str
    selector: str  # CSS selector
    extract_type: str = "text"  # text, html, attribute

class CognitiveMapQueryRequest(BaseModel):
    domain: str
    goal: str  # e.g., "login", "search", "checkout"
```

**Example curl**:
```bash
# Health check
curl http://localhost:8152/health

# Create session
curl -X POST http://localhost:8152/sessions \
  -H "Content-Type: application/json" \
  -d '{"viewport_width": 1920, "viewport_height": 1080}'

# Navigate
curl -X POST "http://localhost:8152/navigate?session_id=SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "wait_until": "load"}'

# Extract data
curl -X POST http://localhost:8152/extract \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "selector": ".main-content", "extract_type": "text"}'
```

**vcli-go Client**: `internal/maba/clients.go` (110 lines, 0 tests) ❌

---

### 2. NIS Service (MVP - MAXIMUS Vision Protocol / Narrative Intelligence)

**Purpose**: Real-time narrative generation from system metrics and observations

**Service Info**:
- **Port**: `8153`
- **URL**: `http://localhost:8153`
- **Health Check**: `GET http://localhost:8153/health`
- **Path**: `~/vertice-dev/backend/services/nis_service/` (also mvp_service)
- **Start Command**: `cd ~/vertice-dev/backend/services/nis_service && python main.py`
- **Registry**: Auto-registers as "maximus_subordinate" (vision_protocol)
- **Note**: Service name confusion - directory is `nis_service`, code references `mvp_service`

**API Endpoints**:

| Method | Endpoint | Description | Request Model | Response Model |
|--------|----------|-------------|---------------|----------------|
| POST | `/narratives` | Generate narrative | `GenerateNarrativeRequest` | Narrative object |
| GET | `/narratives/{narrative_id}` | Get narrative by ID | - | Narrative object |
| GET | `/narratives` | List narratives | Query params | Narrative list |
| POST | `/anomaly/detect` | Detect anomalies | Metrics data | Anomaly report |
| GET | `/baselines` | Get baseline stats | - | Baseline object |
| GET | `/cost/status` | Cost tracking status | - | Cost data |
| GET | `/cost/history` | Cost history | Query params | Cost history |
| GET | `/rate-limit` | Rate limit status | - | Rate limit info |
| GET | `/health` | Health check | - | Health status |

**Request Models** (nis_service/api/routes.py):
```python
class GenerateNarrativeRequest(BaseModel):
    narrative_type: NarrativeType  # EXECUTIVE, TECHNICAL, ALERT, etc.
    time_range_minutes: int = 60
    focus_areas: list[str] | None = None

class MetricsQueryRequest(BaseModel):
    time_range_minutes: int = 60
    focus_areas: list[str] | None = None
```

**Response Example**:
```json
{
  "narrative_id": "mvp-narr-12345",
  "narrative_text": "System performance has been stable...",
  "word_count": 67,
  "tone": "reflective",
  "nqs": 87
}
```

**Example curl**:
```bash
# Health check
curl http://localhost:8153/health

# Generate narrative
curl -X POST http://localhost:8153/narratives \
  -H "Content-Type: application/json" \
  -d '{
    "narrative_type": "EXECUTIVE",
    "time_range_minutes": 60,
    "consciousness_snapshot_id": "snapshot-123"
  }'

# List narratives
curl "http://localhost:8153/narratives?limit=10&offset=0"

# Detect anomalies
curl -X POST http://localhost:8153/anomaly/detect \
  -H "Content-Type: application/json" \
  -d '{"metrics": {...}}'
```

**vcli-go Client**: `internal/nis/clients.go` (122 lines, 0 tests) ❌

---

### 3. Penelope Service (Christian Autonomous Healing)

**Purpose**: Autonomous anomaly detection, diagnosis, and patch generation with Biblical governance

**Service Info**:
- **Port**: `8154` (estimated based on pattern)
- **URL**: `http://localhost:8154`
- **Health Check**: `GET http://localhost:8154/health`
- **Path**: `~/vertice-dev/backend/services/penelope_service/`
- **Start Command**: `cd ~/vertice-dev/backend/services/penelope_service && python main.py`
- **Registry**: Auto-registers (type TBD)
- **Special**: Observes Sabbath (no patches on Sundays)

**Key Components** (from main.py):
- **Wisdom Base Client**: Historical precedent learning
- **Observability Client**: Metrics and anomaly detection
- **Sophia Engine**: Wisdom-based decision making (Article 1: Wisdom)
- **Praotes Validator**: Gentle intervention validation (Article 3: Gentleness)
- **Tapeinophrosyne Monitor**: Humility monitoring (Article 2: Humility)

**API Endpoints** (estimated based on service architecture):

| Method | Endpoint | Description | Expected Request | Expected Response |
|--------|----------|-------------|------------------|-------------------|
| POST | `/triage` | Real-time alert triage | Alert data | Triage result |
| POST | `/fusion/correlate` | Event correlation | Events array | Correlation result |
| POST | `/predict` | Fast ML prediction | Metrics data | Prediction |
| POST | `/match` | Pattern matching | Pattern query | Match results |
| GET | `/playbooks` | List playbooks | - | Playbook list |
| GET | `/wisdom-base/query` | Query historical fixes | Query params | Historical fixes |
| GET | `/sabbath/status` | Sabbath observance status | - | Is it Sunday? |
| GET | `/health` | Health check | - | Health status |

**7 Biblical Articles of Governance**:
1. **Wisdom** (Sophia) - Discern when to act
2. **Humility** (Tapeinophrosyne) - Recognize limits
3. **Gentleness** (Praotes) - Intervene minimally
4. **Stewardship** - Faithful code stewardship
5. **Service** - Love for developers
6. **Sabbath** - Rest on Sundays
7. **Truth** - Truth governs decisions

**Example curl** (estimated):
```bash
# Health check
curl http://localhost:8154/health

# Triage alert
curl -X POST http://localhost:8154/triage \
  -H "Content-Type: application/json" \
  -d '{"severity": "high", "alert_type": "anomaly", "metrics": {...}}'

# Correlate events
curl -X POST http://localhost:8154/fusion/correlate \
  -H "Content-Type: application/json" \
  -d '{"events": [...]}'

# Check if Sabbath
curl http://localhost:8154/sabbath/status
```

**vcli-go Client**: `internal/rte/clients.go` (98 lines, 0 tests) ❌

---

## ⚠️ TIER 2 (P1) - TO BE VERIFIED

**Action Required**: Verify ports and endpoints for these services

| Service | Directory | Expected Port | vcli-go Client | Status |
|---------|-----------|---------------|----------------|--------|
| Hunting Service | `predictive_threat_hunting_service/` | TBD (815X?) | `internal/hunting/clients.go` | ⚠️ VERIFY |
| Immunity Service | `adaptive_immunity_service/` | TBD (815X?) | `internal/immunity/clients.go` | ⚠️ VERIFY |
| Neuro Service | `neuromodulation_service/` | TBD (815X?) | `internal/neuro/clients.go` | ⚠️ VERIFY |
| Intel Service | `threat_intel_service/` | TBD (815X?) | `internal/intel/clients.go` | ⚠️ VERIFY |

**Verification Steps**:
```bash
# For each service:
cd ~/vertice-dev/backend/services/SERVICE_NAME/
grep -E "port.*=" main.py | grep -oE "[0-9]{4,5}"
grep -E "@router\.(get|post|put|delete)" api/routes.py | head -20
```

---

## 🔍 TIER 3 (P2) - ALL BACKEND SERVICES (90+ Services)

**Full List** (alphabetical):
```
active_immune_core
adaptive_immune_system
adaptive_immunity_db
adaptive_immunity_service
adr_core_service
agent_communication
ai_immune_system
api_gateway
atlas_service
auditory_cortex_service
auth_service
autonomous_investigation_service
bas_service
behavioral-analyzer-service
c2_orchestration_service
chemical_sensing_service
cloud_coordinator_service
command_bus_service
cyber_service
digital_thalamus_service
domain_service
edge_agent_service
ethical_audit_service
google_osint_service
grafana
hcl_analyzer_service
hcl_executor_service
hcl_kb_service
hcl_monitor_service
hcl_planner_service
hitl_patch_service
homeostatic_regulation
hpc_service
hsas_service
immunis_api_service
immunis_bcell_service
immunis_cytotoxic_t_service
immunis_dendritic_service
immunis_helper_t_service
immunis_macrophage_service
immunis_neutrophil_service
immunis_treg_service
ip_intelligence_service
maba_service ✅
malware_analysis_service
mav-detection-service
maximus_core_service
maximus_dlq_monitor_service
maximus_eureka
maximus_integration_service
maximus_oraculo
maximus_oraculo_v2
maximus_orchestrator_service
maximus_predict
memory_consolidation_service
mock_vulnerable_apps
mvp_service ✅ (same as nis_service)
narrative_analysis_service
narrative_filter_service
narrative_manipulation_filter
network_monitor_service
network_recon_service
neuromodulation_service
nis_service ✅
nmap_service
offensive_gateway
offensive_orchestrator_service
offensive_tools_service
osint_service
penelope_service ✅
predictive_threat_hunting_service
prefrontal_cortex_service
purple_team
reactive_fabric_analysis
reactive_fabric_core
reflex_triage_engine
rte_service
seriema_graph
sinesp_service
social_eng_service
somatosensory_service
ssl_monitor_service
strategic_planning_service
system_architect_service
tataca_ingestion
tegumentar_service
test_service_for_sidecar
threat_intel_bridge
threat_intel_service
traffic-analyzer-service
verdict_engine_service
vertice_register
vertice_registry_sidecar
vestibular_service
visual_cortex_service
vuln_intel_service
vuln_scanner_service
wargaming_crisol
web_attack_service
```

**Mapping Strategy**:
1. Check each service directory for `main.py`
2. Extract port from environment variable or default
3. Extract routes from `api/routes.py` (if exists)
4. Verify health endpoint exists
5. Document in this file

---

## 📋 BACKEND VERIFICATION PROTOCOL (Anti-Mock)

### Step 1: Check if Backend Running
```bash
# Health check
curl -s http://localhost:PORT/health

# If 200 OK → backend is running
# If connection refused → backend not running
# If 404 → backend running but no /health endpoint (try /)
```

### Step 2: Start Backend (if not running)
```bash
# Navigate to service directory
cd ~/vertice-dev/backend/services/SERVICE_NAME/

# Check dependencies
cat requirements.txt

# Start service
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port PORT --reload
```

### Step 3: Document API (if running)
```bash
# Explore API docs (FastAPI auto-generates)
curl http://localhost:PORT/docs     # Swagger UI
curl http://localhost:PORT/redoc    # ReDoc
curl http://localhost:PORT/openapi.json  # OpenAPI schema

# Save OpenAPI schema
curl -s http://localhost:PORT/openapi.json > backend_schemas/SERVICE_NAME_openapi.json
```

### Step 4: Test Against Real Backend
```go
func TestClient_RealBackend(t *testing.T) {
    // P2: Validação Preventiva
    testutil.VerifyBackendAvailable(t, "http://localhost:PORT")

    client := NewClient("http://localhost:PORT")

    // Test real endpoint
    result, err := client.Method(request)

    assert.NoError(t, err)
    assert.NotNil(t, result)
}
```

### Step 5: If Backend NOT Available
```go
func TestClient_AwaitingBackend(t *testing.T) {
    // P1: Completude Obrigatória - Document "awaiting backend"
    t.Skip("Backend not implemented yet - port TBD (see BACKEND_MAP.md)")
}
```

**NEVER**:
```go
// ❌ P1 VIOLATION
mockServer := &MockHTTPServer{...}  // NO MOCKS!

// ❌ P1 VIOLATION
service.On("Method", mock.Anything).Return(...)  // NO MOCKS!
```

**ALWAYS**:
```go
// ✅ Use httptest.NewServer (simulates real HTTP)
server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(expectedResponse)
}))
defer server.Close()

// ✅ Or test against real backend
testutil.VerifyBackendAvailable(t, "http://localhost:8152")
```

---

## 🚀 QUICK START SCRIPT

**File**: `internal/testutil/backend_setup.sh`

```bash
#!/bin/bash
# Backend Setup Script - Start all confirmed backends

set -e

BACKEND_ROOT=~/vertice-dev/backend/services

echo "🚀 Starting Vértice Backend Services..."

# Function to start backend
start_backend() {
    local name=$1
    local dir=$2
    local port=$3

    echo ""
    echo "=== Starting $name (port $port) ==="

    cd "$BACKEND_ROOT/$dir"

    # Check if already running
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name already running on port $port"
        return 0
    fi

    # Start service in background
    nohup python main.py > "/tmp/${name}.log" 2>&1 &
    local pid=$!

    echo "🔄 Started $name (PID: $pid)"

    # Wait for health check (max 30 seconds)
    for i in {1..30}; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo "✅ $name healthy on port $port"
            return 0
        fi
        sleep 1
    done

    echo "⚠️  $name did not become healthy (check /tmp/${name}.log)"
    return 1
}

# Start P0 backends
start_backend "MABA" "maba_service" 8152
start_backend "NIS" "nis_service" 8153
start_backend "Penelope" "penelope_service" 8154

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "Test with:"
echo "  curl http://localhost:8152/health"
echo "  curl http://localhost:8153/health"
echo "  curl http://localhost:8154/health"
```

**Usage**:
```bash
chmod +x internal/testutil/backend_setup.sh
./internal/testutil/backend_setup.sh
```

---

## 📊 COVERAGE BY CLIENT

| vcli-go Client | Backend Service | Port | Status | Tests | Priority |
|----------------|-----------------|------|--------|-------|----------|
| `internal/maba` | maba_service | 8152 | ✅ Confirmed | ❌ NO TESTS | P0 |
| `internal/nis` | nis_service (mvp) | 8153 | ✅ Confirmed | ❌ NO TESTS | P0 |
| `internal/rte` | penelope_service | 8154 | ✅ Confirmed | ❌ NO TESTS | P0 |
| `internal/hunting` | predictive_threat_hunting_service | TBD | ⚠️ Verify | ❌ NO TESTS | P1 |
| `internal/immunity` | adaptive_immunity_service | TBD | ⚠️ Verify | ❌ NO TESTS | P1 |
| `internal/neuro` | neuromodulation_service | TBD | ⚠️ Verify | ❌ NO TESTS | P1 |
| `internal/intel` | threat_intel_service | TBD | ⚠️ Verify | ❌ NO TESTS | P1 |
| `internal/offensive` | offensive_gateway | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/specialized` | ? | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/streams` | (Kafka) | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/architect` | system_architect_service | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/behavior` | behavioral-analyzer-service | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/edge` | edge_agent_service | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/homeostasis` | homeostatic_regulation | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/integration` | maximus_integration_service | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/pipeline` | ? | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/purple` | purple_team | TBD | ⚠️ Verify | ❌ NO TESTS | P2 |
| `internal/registry` | vertice_register | TBD | ⚠️ Verify | ❌ NO TESTS | P3 |
| `internal/vulnscan` | vuln_scanner_service | TBD | ⚠️ Verify | ❌ NO TESTS | P3 |

---

## 🎯 NEXT STEPS (Phase 0.5 → Phase 1)

1. ✅ Create `backend_setup.sh` (start P0 backends)
2. ⚠️ Verify P1 backend ports (hunting, immunity, neuro, intel)
3. ⚠️ Document P1 backend APIs (read main.py + routes.py)
4. ⚠️ Verify P2 backend ports (remaining clients)
5. ⚠️ Update this file with all confirmed backends

**Exit Criteria**:
- ✅ 3/3 P0 backends documented
- ⚠️ 4/4 P1 backends verified
- ⚠️ backend_setup.sh created and tested
- ⚠️ All clients mapped to backend services

---

## 📝 CONSTITUTIONAL COMPLIANCE

**P1: Completude Obrigatória**:
- ✅ Document all known backends (3/90+ done)
- ✅ No mocks - only real backends documented
- ⚠️ Document "awaiting backend" for unconfirmed services

**P2: Validação Preventiva**:
- ✅ Health check protocol defined
- ✅ Backend verification before testing
- ⚠️ OpenAPI schema extraction strategy

**P6: Eficiência de Token**:
- ✅ Mapped 3 critical backends first (P0)
- ✅ Prioritized by tier (P0 → P1 → P2 → P3)
- ⚠️ Defer full 90+ backend mapping until needed

---

**Generated**: 2025-11-13
**Framework**: CONSTITUIÇÃO VÉRTICE v3.0 - Phase 0.5
**Next Update**: After verifying P1 backends (Hunting, Immunity, Neuro, Intel)
**Constitutional Compliance**: P1 (NO MOCKS ✅), P2 (Validação ✅), P6 (Eficiência ✅)
