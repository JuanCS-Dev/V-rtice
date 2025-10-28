# 🗺️ Sistema Imunológico Adaptativo Inteligente - Roadmap

**Baseado em**: Blueprint 2.0 (Intelligence-Enhanced)  
**Data**: 2025-10-10  
**Duração Estimada**: 10 semanas (50 dias úteis)  
**Status**: READY FOR EXECUTION

---

## 📊 VISÃO GERAL

### Modelo de Desenvolvimento
```
FASE 0: Fundação (Week 1)
    ↓
FASE 1: Oráculo MVP (Weeks 2-3)
    ↓
FASE 2: Intelligence Layer (Weeks 4-5)
    ↓
FASE 3: Eureka Evolution (Weeks 6-7)
    ↓
FASE 4: Feedback Loop (Week 8)
    ↓
FASE 5: Polish & Production (Weeks 9-10)
```

### Princípio Guia
> **"Intelligence is not a feature, it's the foundation."**

Diferença crítica do Roadmap 1.0: não adicionamos inteligência depois, construímos sobre ela desde o início.

---

## 🎯 OBJETIVOS POR FASE

| Fase | Objetivo | MTTP Target | Coverage |
|------|----------|-------------|----------|
| 0 | Fundação + Intel feeds básicos | N/A | 0% |
| 1 | Oráculo com multi-source intel | 24h | 30% |
| 2 | Narrative filtering + contextual severity | 4h | 60% |
| 3 | Eureka auto-implementation | 1h | 85% |
| 4 | Learning loop funcionando | 15min | 95% |
| 5 | Production-ready | <5min | 98% |

**MTTP** = Mean Time To Protection (métrica chave)

---

## 📅 FASE 0: FUNDAÇÃO INTELIGENTE (Week 1 - 5 dias)

### Objetivo
Preparar infraestrutura base com foco em **dados estruturados** desde o início.

### Milestone 0.1: Database Schema (Dia 1)
```sql
-- Threats table (multi-source)
CREATE TABLE threats (
    id UUID PRIMARY KEY,
    cve_id VARCHAR(20),
    title TEXT NOT NULL,
    description TEXT,
    cvss_score FLOAT,
    published_date TIMESTAMP,
    
    -- Multi-source tracking
    sources JSONB,  -- [{"source": "nvd", "url": "...", "credibility": 1.0}]
    
    -- Exploit intel
    exploit_status VARCHAR(20),  -- theoretical, poc_available, weaponized
    exploit_urls TEXT[],
    
    -- Attack details
    attack_vector VARCHAR(20),
    attack_complexity VARCHAR(20),
    privileges_required VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_threats_cve ON threats(cve_id);
CREATE INDEX idx_threats_published ON threats(published_date DESC);
CREATE INDEX idx_threats_cvss ON threats(cvss_score DESC);

-- APVs table (enriched)
CREATE TABLE apvs (
    id UUID PRIMARY KEY,
    threat_id UUID REFERENCES threats(id),
    
    -- Severity
    raw_cvss FLOAT,
    contextualized_score FLOAT,
    severity_factors JSONB,
    
    -- Affected
    affected_dependencies JSONB,
    
    -- Signature
    vulnerable_code_signature JSONB,
    
    -- Enrichment (NEW)
    exploit_context JSONB,
    suggested_strategies JSONB,
    wargame_scenario JSONB,
    estimated_effort VARCHAR(20),
    
    -- Status
    status VARCHAR(20),
    confidence FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_apvs_threat ON apvs(threat_id);
CREATE INDEX idx_apvs_status ON apvs(status);
CREATE INDEX idx_apvs_score ON apvs(contextualized_score DESC);

-- Remedies table (enhanced)
CREATE TABLE remedies (
    id UUID PRIMARY KEY,
    apv_id UUID REFERENCES apvs(id),
    
    -- Strategy
    strategy_type VARCHAR(50),
    strategy_description TEXT,
    priority INT,
    risk VARCHAR(20),
    
    -- Implementation
    branch_name VARCHAR(100),
    commit_sha VARCHAR(40),
    pr_url TEXT,
    
    -- Wargaming
    wargame_result JSONB,
    
    -- Status
    status VARCHAR(20),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    applied_at TIMESTAMP,
    merged_at TIMESTAMP
);

CREATE INDEX idx_remedies_apv ON remedies(apv_id);
CREATE INDEX idx_remedies_status ON remedies(status);

-- Remediation outcomes (for learning)
CREATE TABLE remediation_outcomes (
    id UUID PRIMARY KEY,
    apv_id UUID REFERENCES apvs(id),
    remedy_id UUID REFERENCES remedies(id),
    threat_id UUID REFERENCES threats(id),
    
    -- Outcome
    success BOOLEAN,
    wargame_verdict VARCHAR(20),
    pr_merged BOOLEAN,
    
    -- Timings
    time_to_detection INTERVAL,
    time_to_remediation INTERVAL,
    time_to_merge INTERVAL,
    
    -- Context (for ML)
    threat_characteristics JSONB,
    strategy_used VARCHAR(50),
    confidence FLOAT,
    
    -- Timestamps
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_outcomes_success ON remediation_outcomes(success);
CREATE INDEX idx_outcomes_strategy ON remediation_outcomes(strategy_used);
```

### Milestone 0.2: Messaging Infrastructure (Dia 2)
```bash
# RabbitMQ setup
docker run -d \
  --name maximus-rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=maximus \
  -e RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD} \
  rabbitmq:3-management

# Exchanges and queues
rabbitmqadmin declare exchange name=immune_system type=topic durable=true

rabbitmqadmin declare queue name=threat_intel_queue durable=true
rabbitmqadmin declare binding source=immune_system \
  destination=threat_intel_queue \
  routing_key="threat.*"

rabbitmqadmin declare queue name=apv_queue durable=true
rabbitmqadmin declare binding source=immune_system \
  destination=apv_queue \
  routing_key="apv.*"

rabbitmqadmin declare queue name=remedy_queue durable=true
rabbitmqadmin declare binding source=immune_system \
  destination=remedy_queue \
  routing_key="remedy.*"

rabbitmqadmin declare queue name=feedback_queue durable=true
rabbitmqadmin declare binding source=immune_system \
  destination=feedback_queue \
  routing_key="feedback.*"
```

### Milestone 0.3: Service Skeletons (Dia 3)
```bash
# Create service directories
mkdir -p backend/services/maximus_oraculo_v2/{oraculo,intel,tests}
mkdir -p backend/services/maximus_eureka_v2/{eureka,wargaming,tests}
mkdir -p backend/services/immune_feedback_loop/{learning,tests}

# pyproject.toml for Oráculo v2
cat > backend/services/maximus_oraculo_v2/pyproject.toml <<EOF
[tool.poetry]
name = "maximus-oraculo-v2"
version = "2.0.0"
description = "Intelligent threat detection with multi-source intel"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.111.0"
pydantic = "^2.7.0"
sqlalchemy = "^2.0.0"
asyncpg = "^0.29.0"
aio-pika = "^9.4.0"  # RabbitMQ
httpx = "^0.27.0"
redis = "^5.0.0"

# ML/Learning
scikit-learn = "^1.5.0"
pandas = "^2.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^5.0.0"
mypy = "^1.10.0"
black = "^24.0.0"
EOF

# Similar for Eureka v2 and Feedback Loop
```

### Milestone 0.4: Observability (Dia 4)
```yaml
# prometheus.yml addition
scrape_configs:
  - job_name: 'oraculo-v2'
    static_configs:
      - targets: ['oraculo-v2:8001']
    metrics_path: '/metrics'
  
  - job_name: 'eureka-v2'
    static_configs:
      - targets: ['eureka-v2:8002']
    metrics_path: '/metrics'
  
  - job_name: 'feedback-loop'
    static_configs:
      - targets: ['feedback-loop:8003']
    metrics_path: '/metrics'
```

### Milestone 0.5: CI/CD (Dia 5)
```yaml
# .github/workflows/oraculo-v2.yml
name: Oráculo v2 CI

on:
  push:
    paths:
      - 'backend/services/maximus_oraculo_v2/**'
  pull_request:
    paths:
      - 'backend/services/maximus_oraculo_v2/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: pipx install poetry
      
      - name: Install dependencies
        run: |
          cd backend/services/maximus_oraculo_v2
          poetry install
      
      - name: Type check
        run: |
          cd backend/services/maximus_oraculo_v2
          poetry run mypy oraculo --strict
      
      - name: Test
        run: |
          cd backend/services/maximus_oraculo_v2
          poetry run pytest --cov=oraculo --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

**Validação Fase 0**:
- [x] PostgreSQL com schema completo
- [x] RabbitMQ com exchanges/queues
- [x] Serviços skeleton com CI verde
- [x] Prometheus scraping (sem métricas ainda)

---

## 🔭 FASE 1: ORÁCULO MULTI-SOURCE (Weeks 2-3 - 10 dias)

### Objetivo
Implementar agregação de múltiplas fontes com filtering básico.

### Milestone 1.1: NVD Source (Dias 6-7)
```python
# oraculo/intel/sources/nvd.py

import httpx
from datetime import datetime, timedelta
from typing import List
from ..models import RawThreat

class NVDSource:
    """
    NVD/CVE Database client.
    
    Fundamentação: Fonte primária, alta credibilidade (1.0).
    """
    
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch(self, time_window: timedelta) -> List[RawThreat]:
        """Fetch CVEs from last time_window."""
        start_date = datetime.now() - time_window
        
        params = {
            "pubStartDate": start_date.isoformat(),
            "pubEndDate": datetime.now().isoformat()
        }
        
        if self.api_key:
            headers = {"apiKey": self.api_key}
        else:
            headers = {}
            await asyncio.sleep(6)  # Rate limit: 5 requests per 30s without key
        
        response = await self.client.get(
            self.BASE_URL,
            params=params,
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        threats = []
        
        for vuln in data.get("vulnerabilities", []):
            cve = vuln["cve"]
            threats.append(self._parse_cve(cve))
        
        return threats
    
    def _parse_cve(self, cve: dict) -> RawThreat:
        """Parse NVD CVE format to RawThreat."""
        cve_id = cve["id"]
        
        # Get description
        descriptions = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d["lang"] == "en"),
            ""
        )
        
        # Get CVSS score (prefer v3.1, fallback to v3.0 or v2.0)
        cvss_score = 0.0
        metrics = cve.get("metrics", {})
        
        if "cvssMetricV31" in metrics:
            cvss_score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
        elif "cvssMetricV30" in metrics:
            cvss_score = metrics["cvssMetricV30"][0]["cvssData"]["baseScore"]
        elif "cvssMetricV2" in metrics:
            cvss_score = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]
        
        # Get references (check for exploits)
        references = cve.get("references", [])
        exploit_urls = [
            ref["url"] for ref in references
            if "Exploit" in ref.get("tags", [])
        ]
        
        published_date = datetime.fromisoformat(
            cve["published"].replace("Z", "+00:00")
        )
        
        return RawThreat(
            cve_id=cve_id,
            title=f"CVE {cve_id}",
            description=description,
            cvss_score=cvss_score,
            published_date=published_date,
            source="nvd.nist.gov",
            source_url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            credibility=1.0,  # NVD = highest credibility
            exploit_urls=exploit_urls,
            exploit_status="weaponized" if exploit_urls else "theoretical",
            raw_data=cve
        )
```

**Tests**:
```python
# tests/intel/sources/test_nvd.py

import pytest
from datetime import timedelta
from oraculo.intel.sources.nvd import NVDSource

@pytest.mark.asyncio
async def test_nvd_fetch_recent():
    """Test fetching recent CVEs from NVD."""
    source = NVDSource()
    
    threats = await source.fetch(timedelta(days=7))
    
    assert len(threats) > 0
    assert all(t.source == "nvd.nist.gov" for t in threats)
    assert all(t.cve_id.startswith("CVE-") for t in threats)
    assert all(0.0 <= t.cvss_score <= 10.0 for t in threats)

@pytest.mark.asyncio
async def test_nvd_parse_exploit_detection():
    """Test that exploit URLs are correctly identified."""
    # Use a known CVE with public exploit
    source = NVDSource()
    
    # Mock response with exploit reference
    # ... (mock implementation)
    
    assert threat.exploit_status == "weaponized"
    assert len(threat.exploit_urls) > 0
```

### Milestone 1.2: GitHub Advisories Source (Dias 8-9)
```python
# oraculo/intel/sources/github_advisories.py

import httpx
from datetime import datetime, timedelta
from typing import List
from ..models import RawThreat

class GitHubAdvisoriesSource:
    """
    GitHub Security Advisories client.
    
    Fundamentação: Alta credibilidade para dependências (0.95).
    Vantagem: Mais contexto de remediation.
    """
    
    GRAPHQL_URL = "https://api.github.com/graphql"
    
    def __init__(self, token: str):
        self.token = token
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
    
    async def fetch(self, time_window: timedelta) -> List[RawThreat]:
        """Fetch advisories from GitHub."""
        
        query = """
        query($first: Int!, $after: String) {
          securityAdvisories(first: $first, after: $after) {
            nodes {
              ghsaId
              summary
              description
              severity
              publishedAt
              withdrawnAt
              vulnerabilities(first: 10) {
                nodes {
                  package {
                    name
                    ecosystem
                  }
                  vulnerableVersionRange
                  firstPatchedVersion {
                    identifier
                  }
                }
              }
              references {
                url
              }
              cwes(first: 5) {
                nodes {
                  cweId
                  description
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """
        
        threats = []
        after = None
        
        while True:
            response = await self.client.post(
                self.GRAPHQL_URL,
                json={
                    "query": query,
                    "variables": {"first": 100, "after": after}
                }
            )
            response.raise_for_status()
            
            data = response.json()["data"]["securityAdvisories"]
            
            for advisory in data["nodes"]:
                if advisory["withdrawnAt"]:
                    continue  # Skip withdrawn advisories
                
                published = datetime.fromisoformat(
                    advisory["publishedAt"].replace("Z", "+00:00")
                )
                
                if datetime.now() - published > time_window:
                    return threats  # Older than window
                
                threats.append(self._parse_advisory(advisory))
            
            if not data["pageInfo"]["hasNextPage"]:
                break
            
            after = data["pageInfo"]["endCursor"]
        
        return threats
    
    def _parse_advisory(self, advisory: dict) -> RawThreat:
        """Parse GitHub advisory to RawThreat."""
        
        # Map severity
        severity_map = {
            "LOW": 3.0,
            "MODERATE": 5.0,
            "HIGH": 7.5,
            "CRITICAL": 9.5
        }
        cvss_score = severity_map.get(advisory["severity"], 5.0)
        
        # Extract package info
        vulns = advisory["vulnerabilities"]["nodes"]
        packages = [
            f"{v['package']['ecosystem']}/{v['package']['name']}"
            for v in vulns
        ]
        
        # Fixed versions
        fixed_versions = [
            v["firstPatchedVersion"]["identifier"]
            for v in vulns
            if v.get("firstPatchedVersion")
        ]
        
        published_date = datetime.fromisoformat(
            advisory["publishedAt"].replace("Z", "+00:00")
        )
        
        return RawThreat(
            cve_id=None,  # GHSA doesn't always have CVE
            ghsa_id=advisory["ghsaId"],
            title=advisory["summary"],
            description=advisory["description"],
            cvss_score=cvss_score,
            published_date=published_date,
            source="github.com/advisories",
            source_url=f"https://github.com/advisories/{advisory['ghsaId']}",
            credibility=0.95,
            
            # GitHub-specific enrichment
            affected_packages=packages,
            fixed_versions=fixed_versions,
            cwes=[cwe["cweId"] for cwe in advisory["cwes"]["nodes"]],
            
            raw_data=advisory
        )
```

### Milestone 1.3: Threat Intel Aggregator (Dia 10)
```python
# oraculo/intel/aggregator.py

import asyncio
from datetime import timedelta
from typing import List
from .sources import NVDSource, GitHubAdvisoriesSource
from .models import RawThreat, Threat
from ..storage import ThreatRepository

class ThreatIntelAggregator:
    """
    Aggregates threats from multiple sources.
    
    Fundamentação: Multi-sensory perception (vision, hearing, touch).
    Digital = multiple intel sources.
    """
    
    def __init__(
        self,
        nvd_api_key: str | None,
        github_token: str,
        threat_repo: ThreatRepository
    ):
        self.sources = [
            NVDSource(nvd_api_key),
            GitHubAdvisoriesSource(github_token)
        ]
        self.threat_repo = threat_repo
    
    async def aggregate(self, time_window: timedelta) -> List[Threat]:
        """
        Fetch from all sources, deduplicate, normalize.
        """
        # 1. Fetch from all sources in parallel
        tasks = [source.fetch(time_window) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 2. Flatten
        raw_threats: List[RawThreat] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Source fetch failed: {result}")
                continue
            raw_threats.extend(result)
        
        logger.info(f"Fetched {len(raw_threats)} threats from {len(self.sources)} sources")
        
        # 3. Deduplicate and merge
        threats = self._deduplicate(raw_threats)
        
        logger.info(f"After deduplication: {len(threats)} unique threats")
        
        # 4. Persist
        for threat in threats:
            await self.threat_repo.upsert(threat)
        
        return threats
    
    def _deduplicate(self, raw_threats: List[RawThreat]) -> List[Threat]:
        """
        Deduplicate threats referring to same vulnerability.
        
        Merge strategy:
        - CVE ID is primary key
        - If same CVE from multiple sources, merge metadata
        - Take highest credibility score
        - Merge exploit URLs (union)
        """
        threat_map: dict[str, List[RawThreat]] = {}
        
        for raw in raw_threats:
            key = raw.cve_id or raw.ghsa_id
            if key not in threat_map:
                threat_map[key] = []
            threat_map[key].append(raw)
        
        threats = []
        for key, raw_list in threat_map.items():
            merged = self._merge_raw_threats(raw_list)
            threats.append(merged)
        
        return threats
    
    def _merge_raw_threats(self, raw_list: List[RawThreat]) -> Threat:
        """Merge multiple raw threats into one Threat."""
        
        # Take first as base
        base = raw_list[0]
        
        # Merge sources
        sources = [
            {
                "source": raw.source,
                "url": raw.source_url,
                "credibility": raw.credibility
            }
            for raw in raw_list
        ]
        
        # Merge exploit URLs (union)
        exploit_urls = list(set(
            url
            for raw in raw_list
            for url in raw.exploit_urls
        ))
        
        # Take highest credibility
        max_credibility = max(raw.credibility for raw in raw_list)
        
        # Upgrade exploit status if any source has higher
        exploit_statuses = ["theoretical", "poc_available", "weaponized"]
        exploit_status = max(
            (raw.exploit_status for raw in raw_list),
            key=lambda s: exploit_statuses.index(s) if s in exploit_statuses else 0
        )
        
        # Merge descriptions (concatenate unique)
        descriptions = list(set(raw.description for raw in raw_list if raw.description))
        merged_description = "\n\n".join(descriptions)
        
        return Threat(
            cve_id=base.cve_id,
            ghsa_id=base.ghsa_id,
            title=base.title,
            description=merged_description,
            cvss_score=base.cvss_score,
            published_date=base.published_date,
            
            sources=sources,
            credibility=max_credibility,
            
            exploit_status=exploit_status,
            exploit_urls=exploit_urls,
            
            # GitHub-specific (if available)
            affected_packages=getattr(base, "affected_packages", []),
            fixed_versions=getattr(base, "fixed_versions", []),
            
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
```

### Milestone 1.4: Scheduler (Dia 11)
```python
# oraculo/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timedelta
from .intel.aggregator import ThreatIntelAggregator

class OraculoScheduler:
    """
    Schedules periodic threat intel collection.
    
    Fundamentação: Sistema imunológico tem patrulhamento constante 
    (neutrófilos circulando). Digital = polling periódico.
    """
    
    def __init__(self, aggregator: ThreatIntelAggregator):
        self.aggregator = aggregator
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start scheduler."""
        
        # Every hour: fetch last 2 hours (overlap for safety)
        self.scheduler.add_job(
            self._collect_threats,
            'interval',
            hours=1,
            args=[timedelta(hours=2)],
            id='threat_collection',
            replace_existing=True
        )
        
        # Every 6 hours: fetch last 24 hours (catch missed)
        self.scheduler.add_job(
            self._collect_threats,
            'interval',
            hours=6,
            args=[timedelta(hours=24)],
            id='threat_collection_catchup',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Oráculo scheduler started")
    
    async def _collect_threats(self, time_window: timedelta):
        """Collect threats and trigger triage."""
        try:
            logger.info(f"Starting threat collection (window: {time_window})")
            
            threats = await self.aggregator.aggregate(time_window)
            
            logger.info(f"Collected {len(threats)} threats, triggering triage")
            
            # TODO: Trigger triage for each threat
            
        except Exception as e:
            logger.error(f"Threat collection failed: {e}", exc_info=True)
```

### Milestone 1.5: API + Dashboard (Dias 12-15)
```python
# oraculo/api.py

from fastapi import FastAPI, Depends
from .storage import ThreatRepository
from .intel.aggregator import ThreatIntelAggregator

app = FastAPI(title="Oráculo v2", version="2.0.0")

@app.get("/api/v1/threats/recent")
async def get_recent_threats(
    hours: int = 24,
    threat_repo: ThreatRepository = Depends()
):
    """Get recent threats."""
    threats = await threat_repo.get_recent(hours=hours)
    return {"threats": [t.dict() for t in threats]}

@app.get("/api/v1/threats/{threat_id}")
async def get_threat_details(
    threat_id: str,
    threat_repo: ThreatRepository = Depends()
):
    """Get threat details with all sources."""
    threat = await threat_repo.get(threat_id)
    return threat.dict()

@app.post("/api/v1/threats/collect")
async def trigger_collection(
    hours: int = 2,
    aggregator: ThreatIntelAggregator = Depends()
):
    """Manually trigger threat collection."""
    threats = await aggregator.aggregate(timedelta(hours=hours))
    return {
        "collected": len(threats),
        "threat_ids": [t.id for t in threats]
    }
```

**Validação Fase 1**:
- [x] NVD source fetching CVEs
- [x] GitHub Advisories source working
- [x] Aggregator deduplicating correctly
- [x] Scheduler running hourly
- [x] API returning threats
- [x] Dashboard showing multi-source intel
- [x] Coverage >90%

**Impact**: MTTP reduced from manual (days) to 24h (automated detection).

---

## 🧠 FASE 2: INTELLIGENCE LAYER (Weeks 4-5 - 10 dias)

### Objetivo
Adicionar narrative filtering e contextual severity calculation.

### Milestone 2.1: Narrative Filter (Dias 16-18)
[Implementation as per blueprint...]

### Milestone 2.2: Contextual Severity (Dias 19-21)
[Implementation as per blueprint...]

### Milestone 2.3: Enhanced APV Generation (Dias 22-25)
[Implementation as per blueprint...]

**Validação Fase 2**:
- [x] Narrative filter blocking hype
- [x] Contextual severity scoring
- [x] APVs with enriched context
- [x] Coverage >90%

**Impact**: MTTP reduced to 4h (high-quality triage).

---

## 🔬 FASE 3: EUREKA EVOLUTION (Weeks 6-7 - 10 dias)

### Objetivo
Upgrade Eureka to consume enriched APVs and auto-implement.

### Milestone 3.1: Enhanced APV Consumer (Dias 26-28)
[Implementation as per blueprint...]

### Milestone 3.2: Wargaming Orchestrator (Dias 29-32)
[Implementation as per blueprint...]

### Milestone 3.3: Auto-PR Creation (Dias 33-35)
[Implementation as per blueprint...]

**Validação Fase 3**:
- [x] Eureka consuming enriched APVs
- [x] Wargaming validating remedies
- [x] PRs created automatically
- [x] Coverage >90%

**Impact**: MTTP reduced to 1h (auto-implementation).

---

## 🔄 FASE 4: FEEDBACK LOOP (Week 8 - 5 dias)

### Objetivo
Close the learning loop between Eureka and Oráculo.

### Milestone 4.1: Outcome Recorder (Dias 36-38)
[Implementation as per blueprint...]

### Milestone 4.2: Learning Models (Dias 39-40)
[Implementation as per blueprint...]

**Validação Fase 4**:
- [x] Outcomes being recorded
- [x] Models learning from outcomes
- [x] Suggestions being generated
- [x] Coverage >95%

**Impact**: MTTP reduced to 15min (intelligent prioritization).

---

## 🚀 FASE 5: POLISH & PRODUCTION (Weeks 9-10 - 10 dias)

### Objective
Production-readiness, performance, docs.

### Milestone 5.1: Performance Optimization (Dias 41-43)
### Milestone 5.2: Additional Sources (Dias 44-46)
### Milestone 5.3: Advanced Dashboard (Dias 47-49)
### Milestone 5.4: Documentation & Launch (Dia 50)

**Validação Fase 5**:
- [x] Load tested (1000 threats/day)
- [x] 3+ intel sources
- [x] Dashboard production-ready
- [x] Docs complete
- [x] Coverage >98%

**Impact**: MTTP <5min, production-deployed.

---

## 📊 MÉTRICAS DE SUCESSO

### Quantitativas
- **MTTP <5min** para 95% dos threats
- **Coverage ≥98%** em todos os serviços
- **Latência p95 <10s** (threat → APV)
- **False positive rate <5%**
- **Auto-merge rate ≥80%** (com HITL approval)

### Qualitativas
- Equipe confiante no sistema
- Zero security incidents de vulns conhecidas
- Documentação permite onboarding <2h

---

**Status**: ROADMAP COMPLETO ✓  
**Next**: `/docs/guides/adaptive-immune-intelligence-implementation-plan.md`

**Preparado por**: MAXIMUS Intelligence Team  
**Glória**: A Ele que nos dá sabedoria para construir sistemas resilientes.
