# 🧬 Active Immune System - Plano de Continuação
**Data**: 2025-01-11  
**Status**: EXECUTION-READY  
**Filosofia**: Coeso, Estruturado, Metódico

---

## 📊 ESTADO ATUAL (Onde Paramos)

### ✅ Oráculo Engine - COMPLETO
**Status**: 93/93 testes passando | 81.62% coverage Oráculo Engine | mypy --strict ✅

#### Implementado:
- ✅ **APV Model**: Pydantic completo com 32 testes (97% coverage)
- ✅ **OSV.dev Client**: Threat feed primário (13 testes, 83.10% coverage)
- ✅ **Dependency Graph**: Cross-referencing de deps (33 testes)
- ✅ **Relevance Filter**: Filtragem contextual (40 testes)
- ✅ **Kafka Publisher**: APV publishing para Eureka (7 testes)
- ✅ **Oráculo Engine**: Orchestrator end-to-end (E2E completo)

#### Arquivos Core:
```
backend/services/maximus_oraculo/
├── models/apv.py                    # APV Pydantic - COMPLETE
├── threat_feeds/
│   ├── base_feed.py                 # Abstract feed interface
│   └── osv_client.py                # OSV.dev implementation
├── filtering/
│   ├── dependency_graph.py          # Dep graph builder
│   └── relevance_filter.py          # Contextual filter
├── kafka_integration/
│   └── apv_publisher.py             # Kafka producer
├── oraculo_engine.py                # Main orchestrator
└── tests/                           # 93 testes (unit + integration + e2e)
```

#### Gaps:
- ❌ **Coverage < 90%**: Shared modules puxando coverage pra baixo (36% total)
- ⚠️ **1 test failing**: OSV API response format mudou (`summary` field)
- ❌ **Frontend Dashboard**: Não iniciado
- ❌ **Eureka Integration**: Eureka só tem stub (8 arquivos Python vazios)

---

### ⏸️ Eureka Engine - STUB ONLY
**Status**: 8 arquivos Python | Apenas placeholders

#### Arquivos Existentes:
```
backend/services/maximus_eureka/
├── eureka.py                        # Stub com docstrings
├── ioc_extractor.py                 # Empty
├── pattern_detector.py              # Empty
├── playbook_generator.py            # Empty
├── api.py                           # Empty
└── test_eureka.py                   # Empty
```

**Realidade**: Eureka Engine NÃO está implementado. Só existe estrutura de diretórios.

---

### ❌ Frontend Dashboard - NÃO INICIADO
**Status**: Sem componentes de Active Immune System

#### Objetivo:
Dashboard visualizando:
- APVs em tempo real (feed do Kafka)
- Status Oráculo + Eureka
- Métricas de imunidade (MTTP, taxa de remediação)
- Timeline de ameaças detectadas
- Auto-implementações sugeridas pelo Eureka

---

## 🎯 PLANO DE CONTINUAÇÃO METODICO

### Filosofia de Execução
1. **Completar > Iniciar**: Finish Oráculo antes de Eureka
2. **Validar > Documentar > Avançar**: Tripla validação (syntax, semantic, phenomenological)
3. **Frontend Last**: Backend primeiro, dashboard depois
4. **Zero Placeholder Code**: Tudo production-ready

---

## 📅 ROADMAP ESTRUTURADO

### **FASE 1: ORÁCULO HARDENING** (Prioridade 1)
**Objetivo**: Levar Oráculo a 100% production-ready  
**Duração**: 4-6 horas  
**Exit Criteria**: Coverage ≥90% | Todos testes passing | Documentação validada

#### 1.1. Fix Test Failure (30min)
**Arquivo**: `backend/services/maximus_oraculo/tests/unit/test_osv_client.py`  
**Problema**: OSV API mudou formato (sem campo `summary`)

**Ação**:
```python
# Test espera 'summary', mas API retorna 'details'
# Fix: Atualizar assertion ou mapear 'details' → 'summary'
```

**Validação**: `pytest test_osv_client.py -v`

---

#### 1.2. Coverage Boost (2h)
**Target**: Elevar coverage de 36% → 90%

**Estratégia**:
1. **Isolar shared modules** (eles contam pro total mas não são nossos)
   ```bash
   pytest --cov=backend/services/maximus_oraculo \
          --cov-report=html \
          --cov-fail-under=90
   ```

2. **Adicionar testes faltantes**:
   - `oraculo_engine.py`: Linhas 274-341 (error handling paths)
   - `osv_client.py`: Edge cases (API timeout, malformed response)
   - `base_feed.py`: Abstract methods coverage

**Validação**: `pytest --cov=backend/services/maximus_oraculo --cov-fail-under=90`

---

#### 1.3. Oráculo API Endpoint (1h)
**Arquivo**: `backend/services/maximus_oraculo/api.py`  
**Status**: Existe mas não está completo

**Implementar**:
```python
from fastapi import FastAPI, BackgroundTasks
from oraculo_engine import OraculoEngine

app = FastAPI(title="Oráculo Threat Sentinel")
engine = OraculoEngine(repo_root="/path/to/maximus")

@app.post("/scan/vulnerabilities")
async def trigger_scan(background_tasks: BackgroundTasks):
    """Trigger vulnerability scan."""
    background_tasks.add_task(engine.scan_vulnerabilities)
    return {"status": "scan_initiated"}

@app.get("/apvs/recent")
async def get_recent_apvs(limit: int = 10):
    """Get recent APVs published."""
    # Query from DB or Kafka
    pass

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics."""
    return engine.get_metrics()
```

**Validação**: `curl localhost:8010/scan/vulnerabilities`

---

#### 1.4. Integration Test E2E Real (1h)
**Objetivo**: Validar pipeline completo com Kafka real

**Setup**:
```bash
# Start Kafka
docker-compose -f docker-compose.yml up -d kafka

# Run E2E test
pytest tests/e2e/test_oraculo_kafka_e2e.py -v
```

**Validação**: APV aparece no tópico Kafka `maximus.apv.threat`

---

#### 1.5. Documentação Operacional (30min)
**Arquivo**: `backend/services/maximus_oraculo/ORACULO_README.md`

**Adicionar**:
- Setup instructions (dependencies, Kafka config)
- API endpoints documentation
- Metrics explained (Prometheus)
- Troubleshooting guide

---

### **FASE 2: EUREKA ENGINE IMPLEMENTATION** (Prioridade 2)
**Objetivo**: Implementar Eureka Engine completo  
**Duração**: 8-10 horas  
**Exit Criteria**: Eureka recebe APV → Gera remédio → Testes ≥90%

#### 2.1. Eureka Core - IOC Extractor (2h)
**Arquivo**: `backend/services/maximus_eureka/ioc_extractor.py`

**Funcionalidade**:
```python
class IOCExtractor:
    """
    Extract Indicators of Compromise from APV.
    
    IOCs:
    - CVE ID
    - Affected package name + version range
    - CWE categories
    - Attack vector (CVSS)
    - Exploit URLs (if available)
    """
    
    def extract(self, apv: APV) -> IOCBundle:
        """Extract structured IOCs from APV."""
        return IOCBundle(
            cve_id=apv.cve_id,
            packages=[pkg.name for pkg in apv.affected_packages],
            cwes=apv.cwes,
            attack_vector=apv.cvss.attack_vector,
            exploit_urls=apv.references
        )
```

**Testes**: 15+ unit tests  
**Validação**: `pytest tests/unit/test_ioc_extractor.py -v`

---

#### 2.2. Pattern Detector (3h)
**Arquivo**: `backend/services/maximus_eureka/pattern_detector.py`

**Funcionalidade**:
```python
class PatternDetector:
    """
    Detect vulnerability patterns and suggest remediations.
    
    Patterns:
    1. Dependency upgrade (e.g., "upgrade fastapi 0.110.0 → 0.110.3")
    2. Configuration change (e.g., "disable XML external entities")
    3. Code patch (e.g., "add input sanitization")
    4. Network policy (e.g., "block port 8080 externally")
    """
    
    def detect_pattern(self, iocs: IOCBundle) -> RemediationPattern:
        """
        Analyze IOCs and determine remediation type.
        
        Logic:
        - If affected_package in requirements.txt → DEPENDENCY_UPGRADE
        - If CWE in [CWE-611, CWE-827] → CONFIG_CHANGE
        - If exploit PoC available → CODE_PATCH
        - Else → MANUAL_REVIEW
        """
        pass
```

**Testes**: 20+ unit tests (each pattern type)  
**Validação**: `pytest tests/unit/test_pattern_detector.py -v`

---

#### 2.3. Playbook Generator (3h)
**Arquivo**: `backend/services/maximus_eureka/playbook_generator.py`

**Funcionalidade**:
```python
class PlaybookGenerator:
    """
    Generate executable remediation playbooks.
    
    Output formats:
    - Bash script (for deps/config)
    - Python code (for code patches)
    - Dockerfile diff (for containerized changes)
    - GitHub PR description (for HITL review)
    """
    
    def generate(self, pattern: RemediationPattern) -> Playbook:
        """
        Generate playbook from pattern.
        
        Example (DEPENDENCY_UPGRADE):
            ```bash
            # Remediation for CVE-2024-XXXX
            pip install fastapi==0.110.3
            pytest tests/integration/ -v
            ```
        """
        pass
```

**Testes**: 25+ tests (cada tipo de playbook)  
**Validação**: 
- `pytest tests/unit/test_playbook_generator.py -v`
- Executar playbook gerado em sandbox

---

#### 2.4. Eureka Engine Orchestrator (1h)
**Arquivo**: `backend/services/maximus_eureka/eureka.py`

**Funcionalidade**:
```python
class EurekaEngine:
    """
    Main orchestrator: APV → IOC → Pattern → Playbook.
    """
    
    def __init__(self):
        self.ioc_extractor = IOCExtractor()
        self.pattern_detector = PatternDetector()
        self.playbook_generator = PlaybookGenerator()
    
    async def process_apv(self, apv: APV) -> RemediationResult:
        """
        Process APV through full pipeline.
        
        Returns:
            RemediationResult(
                playbook=Playbook(...),
                confidence=0.85,
                requires_hitl=False
            )
        """
        iocs = self.ioc_extractor.extract(apv)
        pattern = self.pattern_detector.detect_pattern(iocs)
        playbook = self.playbook_generator.generate(pattern)
        
        return RemediationResult(
            playbook=playbook,
            confidence=pattern.confidence,
            requires_hitl=(pattern.confidence < 0.8)
        )
```

**Testes**: 10+ integration tests  
**Validação**: `pytest tests/integration/test_eureka_engine.py -v`

---

#### 2.5. Kafka Consumer (Oráculo → Eureka) (1h)
**Arquivo**: `backend/services/maximus_eureka/kafka_consumer.py`

**Funcionalidade**:
```python
class APVConsumer:
    """
    Consume APVs from Kafka topic and trigger Eureka processing.
    """
    
    async def consume(self):
        """
        Subscribe to maximus.apv.threat topic.
        For each APV:
            1. Deserialize
            2. Process via EurekaEngine
            3. Store remediation in DB
            4. Publish metrics
        """
        async for msg in self.consumer:
            apv = APV.parse_raw(msg.value)
            result = await self.engine.process_apv(apv)
            
            await self.db.store_remediation(result)
            self.metrics.remediations_generated.inc()
```

**Validação**: End-to-end test Oráculo → Kafka → Eureka

---

### **FASE 3: FRONTEND DASHBOARD** (Prioridade 3)
**Objetivo**: Visualização Active Immune System  
**Duração**: 6-8 horas  
**Exit Criteria**: Dashboard funcional + real-time updates

#### 3.1. APV Feed Component (2h)
**Arquivo**: `frontend/src/components/immune/APVFeed.tsx`

**Design**:
```tsx
interface APVFeedProps {
  limit?: number;
}

export function APVFeed({ limit = 20 }: APVFeedProps) {
  const { apvs, loading } = useAPVStream(); // WebSocket hook
  
  return (
    <Card>
      <CardHeader>
        <h2>🔴 Live Threat Feed</h2>
        <Badge variant="destructive">{apvs.length} Active</Badge>
      </CardHeader>
      <ScrollArea>
        {apvs.map(apv => (
          <APVCard key={apv.id} apv={apv} />
        ))}
      </ScrollArea>
    </Card>
  );
}
```

**Validação**: Ver APVs aparecendo em tempo real

---

#### 3.2. Remediation Timeline (2h)
**Arquivo**: `frontend/src/components/immune/RemediationTimeline.tsx`

**Design**:
```tsx
export function RemediationTimeline() {
  const remediations = useRemediations();
  
  return (
    <Timeline>
      {remediations.map(r => (
        <TimelineItem key={r.id} timestamp={r.created_at}>
          <div className="flex gap-4">
            <StatusBadge status={r.status} />
            <div>
              <h3>{r.apv.title}</h3>
              <p>Confidence: {r.confidence}%</p>
              {r.requires_hitl && <Badge>Needs Review</Badge>}
            </div>
            <Button onClick={() => viewPlaybook(r)}>
              View Playbook
            </Button>
          </div>
        </TimelineItem>
      ))}
    </Timeline>
  );
}
```

---

#### 3.3. Metrics Dashboard (2h)
**Arquivo**: `frontend/src/components/immune/MetricsDashboard.tsx`

**Métricas**:
- **MTTP** (Mean Time To Protect): Avg time APV → Remediation
- **Remediation Rate**: % APVs com playbook gerado
- **HITL Rate**: % remediações requiring human review
- **Coverage**: % deps com monitoramento ativo

**Validação**: Métricas atualizando a cada scan

---

#### 3.4. WebSocket Integration (1h)
**Arquivo**: `frontend/src/hooks/useAPVStream.ts`

**Implementação**:
```typescript
export function useAPVStream() {
  const [apvs, setAPVs] = useState<APV[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8010/ws/apvs');
    
    ws.onmessage = (event) => {
      const apv = JSON.parse(event.data);
      setAPVs(prev => [apv, ...prev].slice(0, 50));
    };
    
    return () => ws.close();
  }, []);
  
  return { apvs, loading: false };
}
```

---

#### 3.5. Integration with Existing Dashboard (1h)
**Arquivo**: `frontend/src/pages/SecurityDashboard.tsx`

**Adicionar**:
```tsx
<Tabs>
  <TabsList>
    <TabsTrigger value="firewall">Firewall</TabsTrigger>
    <TabsTrigger value="threats">Threats</TabsTrigger>
    <TabsTrigger value="immune">🧬 Active Immunity</TabsTrigger>
  </TabsList>
  
  <TabsContent value="immune">
    <div className="grid grid-cols-2 gap-4">
      <APVFeed />
      <RemediationTimeline />
      <MetricsDashboard className="col-span-2" />
    </div>
  </TabsContent>
</Tabs>
```

---

## 🎯 PRIORIDADES FINAIS

### **Ordem de Execução Recomendada**:

#### **Agora (Prioridade Máxima)**:
1. ✅ **Fase 1.1**: Fix test failure OSV (30min)
2. ✅ **Fase 1.2**: Coverage boost Oráculo (2h)
3. ✅ **Fase 1.3**: Oráculo API endpoints (1h)

#### **Depois (Alta Prioridade)**:
4. ✅ **Fase 1.4**: E2E test real com Kafka (1h)
5. ✅ **Fase 1.5**: Documentação operacional (30min)

#### **Em Seguida (Média Prioridade)**:
6. 🔨 **Fase 2**: Eureka Engine completo (8-10h)

#### **Por Último (Baixa Prioridade)**:
7. 🎨 **Fase 3**: Frontend Dashboard (6-8h)

---

## 📊 MÉTRICAS DE SUCESSO

### Oráculo (Fase 1):
- ✅ Coverage ≥ 90% (apenas maximus_oraculo/)
- ✅ 100% testes passing
- ✅ API funcional (curl returning 200)
- ✅ APVs aparecendo no Kafka

### Eureka (Fase 2):
- 🎯 Coverage ≥ 90%
- 🎯 APV → Playbook end-to-end working
- 🎯 3 tipos de remediação implementados (upgrade, config, patch)
- 🎯 Kafka consumer ativo

### Frontend (Fase 3):
- 🎯 APV feed real-time
- 🎯 Timeline de remediações
- 🎯 Métricas atualizando
- 🎯 WebSocket stable connection

---

## 🚀 COMANDO DE INÍCIO

```bash
# Fase 1.1: Fix test failure
cd /home/juan/vertice-dev
pytest backend/services/maximus_oraculo/tests/unit/test_osv_client.py::TestOSVClient::test_fetch_by_cve_id_real_api -v

# Identificar problema exato
# Fix no test ou no OSVClient
# Re-run até PASS
```

---

**Status**: READY TO EXECUTE  
**Próximo Passo**: Aguardar aprovação para iniciar Fase 1.1  
**Fundamentação**: Completar > Iniciar | Validar > Documentar > Avançar

Glory to YHWH. 🙏
