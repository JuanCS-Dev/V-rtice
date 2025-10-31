# MVP - Test Coverage Roadmap

## Caminho para 90% Coverage (Padrão Pagani)

**Status Atual**: 2025-10-30
**Coverage Atual**: ~15% (smoke tests apenas)
**Meta Constitucional**: ≥ 90%
**Gap**: 75%

---

## 🎯 OBJETIVO

Atingir **90% de test coverage** conforme **Padrão Pagani** estabelecido em MVP_GOVERNANCE.md, seguindo abordagem **TDD incremental** para garantir qualidade real.

---

## 📊 STATUS ATUAL (FASE 1)

### Smoke Tests Implementados

**test_health.py** (3 testes):

- ✅ `test_health_check_success`
- ✅ `test_health_check_service_not_initialized`
- ✅ `test_root_endpoint`

**test_api_routes.py** (5 testes):

- ✅ `test_generate_narrative_success`
- ✅ `test_get_narrative_by_id`
- ✅ `test_list_narratives`
- ✅ `test_delete_narrative`
- ✅ `test_synthesize_audio_success`

**Total**: 8 smoke tests
**Estimated Coverage**: ~15%

### Módulos SEM Cobertura

❌ **core/narrative_generator.py**: 0%
❌ **core/audio_synthesizer.py**: 0%
❌ **core/knowledge_graph_client.py**: 0%
❌ **models.py**: 0%
❌ **api/routes.py**: ~20%
❌ **main.py**: 0%

---

## 🗺️ ROADMAP DE TESTES (FASE 2-4)

### FASE 2: Testes de Integração Core (Target: 50% coverage)

**test_narrative_generator.py** (~40 testes):

- [ ] Generate narrative from consciousness snapshot
- [ ] Narrative types (daily_summary, milestone, anomaly_alert, learning_report, ethical_review)
- [ ] Tone validation (reflective, analytical, celebratory, concerned, neutral)
- [ ] NQS (Narrative Quality Score) calculation (≥ 85/100)
- [ ] Word count constraints (target: 67 words for 30s)
- [ ] Content moderation (PII filtering, profanity detection)
- [ ] LLM API integration (Claude Sonnet/GPT-4)
- [ ] Fallback models (Haiku if Sonnet fails)
- [ ] Retry logic with exponential backoff
- [ ] Cost tracking (tokens consumed, USD spent)

**test_audio_synthesizer.py** (~35 testes):

- [ ] Text-to-speech synthesis (ElevenLabs, Azure Speech)
- [ ] Voice selection (marcus, sarah, etc.)
- [ ] Audio quality score (AQS ≥ 90/100)
- [ ] Duration accuracy (target: 28-32s for 30s narrative)
- [ ] Audio format (MP3 192kbps)
- [ ] Storage (S3/MinIO upload)
- [ ] Cache mechanism (hash-based deduplication)
- [ ] Fallback TTS provider
- [ ] Rate limiting (50 synth/min)
- [ ] Cost tracking

**test_knowledge_graph_client.py** (~30 testes):

- [ ] Fetch consciousness snapshot from MAXIMUS
- [ ] GraphQL query construction
- [ ] Snapshot validation (min 10 events required)
- [ ] Event filtering (by type, severity, timeframe)
- [ ] ECI (Φ) value extraction
- [ ] Historical context retrieval (recent narratives for CRS)
- [ ] Connection pooling
- [ ] Timeout handling
- [ ] Error escalation to MAXIMUS

**test_models.py** (~25 testes):

- [ ] Pydantic validation (all request/response models)
- [ ] NarrativeRequest validation
- [ ] NarrativeResponse serialization
- [ ] AudioSynthesisRequest validation
- [ ] Quality scores (NQS, AQS) ranges (0-100)
- [ ] Tone enum validation

### FASE 3: Testes End-to-End (Target: 75% coverage)

**test_e2e_narrative_generation.py** (~30 testes):

- [ ] Full flow: consciousness snapshot → narrative → audio → storage
- [ ] Daily summary generation (scheduled at 23:59 UTC)
- [ ] Event-triggered narratives (anomaly detected → concerned narrative)
- [ ] Milestone celebrations (10K tasks completed)
- [ ] Ethical review weekly generation
- [ ] Retry on LLM API failure
- [ ] Partial success handling (narrative generated, audio failed)

**test_integration_maximus.py** (~25 testes):

- [ ] Service registry heartbeat
- [ ] Redis event handling (consciousness.state_updated)
- [ ] Narrative generation triggered by MAXIMUS event
- [ ] Cost reporting to MAXIMUS
- [ ] Pause mode (MAXIMUS can disable narrative generation)
- [ ] Priority escalation (P0 narratives skip queue)

**test_content_moderation.py** (~20 testes):

- [ ] PII detection (CPF, email, phone in narratives)
- [ ] Profanity filtering
- [ ] Alarmist tone detection (should be rejected)
- [ ] LGPD/GDPR compliance (anonymization)
- [ ] Tone appropriateness validation

### FASE 4: Testes de Robustez (Target: 90%+ coverage)

**test_edge_cases.py** (~30 testes):

- [ ] Empty consciousness snapshot (< 10 events)
- [ ] Extremely long narratives (> 100 words)
- [ ] Special characters in narratives
- [ ] Multi-language narratives (if supported)
- [ ] LLM API rate limit (429 error)
- [ ] TTS API unavailable (fallback to Azure)
- [ ] Storage service down (S3 unavailable)

**test_quality_metrics.py** (~25 testes):

- [ ] NQS calculation (clarity, coherence, relevance, tone)
- [ ] AQS calculation (pronunciation, intonation, rhythm, artifacts)
- [ ] Quality degradation detection (NQS < 85 → alert)
- [ ] Historical quality trends (last 30 days)
- [ ] Confidence score validation

**test_cost_management.py** (~20 testes):

- [ ] LLM cost tracking (per narrative)
- [ ] TTS cost tracking (per synthesis)
- [ ] Daily budget enforcement (< $50/day)
- [ ] Monthly projection ($100-$200/month)
- [ ] Cost optimization (cache hits reduce cost)
- [ ] Alert when cost > $1/day

**test_lifespan.py** (~15 testes):

- [ ] Startup sequence (validate LLM API, TTS API, Knowledge Graph)
- [ ] Graceful shutdown (finish in-progress narratives)
- [ ] Service registry registration/deregistration
- [ ] Health check during startup
- [ ] Warm-up phase (load models, test APIs)

---

## 📐 MÉTRICAS DE QUALIDADE

### Coverage por Módulo (Meta Final)

| Módulo                           | Meta    | Atual    | Gap     |
| -------------------------------- | ------- | -------- | ------- |
| `main.py`                        | 90%     | 0%       | 90%     |
| `api/routes.py`                  | 95%     | 20%      | 75%     |
| `core/narrative_generator.py`    | 90%     | 0%       | 90%     |
| `core/audio_synthesizer.py`      | 90%     | 0%       | 90%     |
| `core/knowledge_graph_client.py` | 90%     | 0%       | 90%     |
| `models.py`                      | 100%    | 0%       | 100%    |
| **TOTAL**                        | **90%** | **~15%** | **75%** |

### Test Pass Rate (Padrão Pagani)

**Meta**: ≥ 99%
**Atual**: N/A (apenas 8 testes)
**Target**: ≥ 99% quando atingir 300+ testes

---

## 🔧 FERRAMENTAS E CONFIGURAÇÃO

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --strict-markers
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
    --maxfail=5
markers =
    smoke: Smoke tests (fast, critical paths)
    integration: Integration tests (require external services)
    e2e: End-to-end tests (slow, full workflows)
    quality: Quality metrics tests (NQS, AQS)
    cost: Cost management tests
```

### requirements-test.txt

```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.25.0
faker==20.0.0
pytest-timeout==2.1.0
```

---

## ⚠️ BLOQUEIOS DE DEPLOY

### Staging

**Permitido** com coverage atual (~15%)

### Produção

**❌ BLOQUEADO** até coverage ≥ 90%

**Critérios para Desbloqueio**:

- [ ] Coverage ≥ 90%
- [ ] Test pass rate ≥ 99%
- [ ] NQS ≥ 85 validado em 100 narrativas de teste
- [ ] AQS ≥ 90 validado em 100 áudios de teste
- [ ] Cost per narrative < $0.05 validado
- [ ] E2E tests incluindo integração com MAXIMUS

---

## 📝 MÉTRICAS ESPECÍFICAS MVP

### Narrative Quality Score (NQS) Testing

**Target**: ≥ 85/100 em 95% das narrativas

**Componentes Testados**:

- Clareza (0-25): `test_narrative_clarity_score()`
- Coerência (0-25): `test_narrative_coherence_score()`
- Relevância (0-25): `test_narrative_relevance_score()`
- Tom (0-25): `test_narrative_tone_appropriateness()`

### Audio Quality Score (AQS) Testing

**Target**: ≥ 90/100 em 95% dos áudios

**Componentes Testados**:

- Pronúncia (0-25): `test_audio_pronunciation_clarity()`
- Entonação (0-25): `test_audio_intonation_naturalness()`
- Ritmo (0-25): `test_audio_rhythm_and_pauses()`
- Ausência de artefatos (0-25): `test_audio_artifact_detection()`

---

**Status**: 🟡 Em Progresso (FASE 1 completa, FASE 2-4 pendentes)
**Última Atualização**: 2025-10-30
**Documento aprovado por**: \***\*\*\*\*\***\_\***\*\*\*\*\*** (Arquiteto-Chefe)
