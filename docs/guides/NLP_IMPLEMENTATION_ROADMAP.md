# NLP Implementation Roadmap
## Tactical Execution Plan - 28 Days to Production

**Lead Architect**: Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author**: Claude (MAXIMUS AI Assistant)  
**Start Date**: 2025-10-12  
**Target Completion**: 2025-11-09 (28 days)  
**Status**: ACTIVE | DAY 1

---

## Overview

Este roadmap é o desdobramento tático do NLP Security Blueprint em tarefas executáveis diárias. Cada dia tem entregas concretas, métricas de validação e critérios de aceitação.

**Filosofia**: "Transformando dias em minutos" - trabalho metódico, consistente, sem pausas desnecessárias.

---

## Phase 1: Foundation (Days 1-7)
### Goal: Estrutura base + 4/7 camadas operacionais

#### Day 1 (2025-10-12): Project Setup & Guardian Core ✅ ACTIVE

**Tarefas**:
1. **[2h] Estrutura de Diretórios**
   ```bash
   mkdir -p vcli-go/internal/security/{auth,authz,sandbox,intent_validation,flow_control,behavioral,audit}
   mkdir -p vcli-go/pkg/nlp
   ```
   - Criar todos os diretórios conforme blueprint
   - Setup `.gitkeep` files
   - Atualizar `.gitignore` se necessário

2. **[3h] Guardian Interface & Core**
   - Criar `/internal/security/guardian.go`
   - Definir interfaces principais:
     - `Guardian` interface
     - `ParseRequest`, `SecureParseResult`, `SecurityDecision` structs
   - Implementar skeleton do Guardian orchestrator
   - Metrics setup (Prometheus)

3. **[3h] Layer 1 - Authentication (Part 1)**
   - Criar `/internal/security/auth/auth.go`
   - Interface `AuthLayer`
   - Struct `authLayer` com método básico `ValidateToken`
   - JWT token validation (usando lib padrão)
   - Basic tests

**Critérios de Aceitação**:
- [ ] Estrutura completa criada
- [ ] `guardian.go` compila sem erros
- [ ] `AuthLayer` interface definida
- [ ] Tests passando (coverage ≥80%)
- [ ] Métricas exportando (smoke test)

**Output**:
- Blueprint implementado ≈ 10%
- Linhas de código: ~500 (Go + tests)

---

#### Day 2: Auth Layer Complete + MFA Framework

**Tarefas**:
1. **[3h] MFA Implementation**
   - Criar `/internal/security/auth/mfa.go`
   - TOTP (Time-based One-Time Password) usando `github.com/pquerna/otp`
   - `RequireMFA` logic baseado em action risk
   - MFA challenge/verify flow

2. **[2h] Token Management**
   - Criar `/internal/security/auth/token.go`
   - Token generation (JWT with RSA-256)
   - Token rotation mechanism
   - Token revocation list (in-memory cache)

3. **[3h] Auth Tests & Integration**
   - Comprehensive unit tests
   - Integration test: full auth flow
   - Mock MFA for testing
   - Metrics validation

**Critérios de Aceitação**:
- [ ] MFA TOTP funcionando
- [ ] JWT tokens gerados e validados corretamente
- [ ] Token rotation testado
- [ ] Tests coverage ≥90%
- [ ] Metrics: `auth_requests_total`, `mfa_challenges_issued`

**Output**:
- Layer 1 COMPLETE ✓
- Blueprint: 20%

---

#### Day 3: Authorization Layer (RBAC)

**Tarefas**:
1. **[4h] RBAC Engine**
   - Criar `/internal/security/authz/authz.go`
   - Interface `AuthzLayer`
   - Role definitions: `admin`, `operator`, `viewer`, `auditor`
   - Permission model: `action` + `resource` + `role`
   - `CheckPermission` implementation

2. **[2h] Policy Definition**
   - Criar `/internal/security/authz/policy.go`
   - YAML policy parser
   - Policy evaluation engine
   - Default policies for K8s actions

3. **[2h] Tests**
   - RBAC tests (role hierarchies)
   - Policy evaluation tests
   - Edge cases (unknown role, malformed policy)

**Critérios de Aceitação**:
- [ ] RBAC engine functional
- [ ] Policies loaded from YAML
- [ ] Permission checks working (allow/deny)
- [ ] Tests coverage ≥90%
- [ ] Metrics: `authz_decisions_total{decision=allow|deny}`

**Output**:
- Layer 2 (RBAC) COMPLETE ✓
- Blueprint: 30%

---

#### Day 4: Authorization Contextual + Sandbox Setup

**Tarefas**:
1. **[3h] Contextual Authorization (ABAC)**
   - Criar `/internal/security/authz/context.go`
   - Context attributes: IP, time, geolocation, system_state
   - `EvaluateContext` implementation
   - Temporal constraints (business hours)
   - IP allowlist/blocklist

2. **[2h] Adaptive Policies**
   - Threat level enum: `low`, `medium`, `high`, `critical`
   - `AdaptPolicy` - dinamically adjust requirements
   - Policy escalation logic

3. **[3h] Sandbox Layer Start**
   - Criar `/internal/security/sandbox/sandbox.go`
   - Interface `SandboxLayer`
   - Sandbox config struct
   - Basic resource limits (CPU, memory, timeout)

**Critérios de Aceitação**:
- [ ] Contextual authz working (IP, time checks)
- [ ] Adaptive policies respond to threat level
- [ ] Sandbox interface defined
- [ ] Tests coverage ≥85%
- [ ] Metrics: `authz_context_evaluations_total`

**Output**:
- Layer 2 (ABAC + Adaptive) COMPLETE ✓
- Layer 3 (Sandbox) started
- Blueprint: 40%

---

#### Day 5: Sandbox Complete + Intent Validation Start

**Tarefas**:
1. **[3h] Sandbox Execution**
   - Criar `/internal/security/sandbox/isolation.go`
   - Namespace isolation (Linux namespaces)
   - Filesystem restrictions (chroot, readonly mounts)
   - Network policies (no egress/ingress by default)

2. **[2h] Resource Enforcement**
   - Criar `/internal/security/sandbox/limits.go`
   - cgroups integration for CPU/memory limits
   - Timeout enforcement (context.WithTimeout)
   - Sandbox cleanup on exit

3. **[3h] Intent Validation Layer Start**
   - Criar `/internal/security/intent_validation/validator.go`
   - Interface `IntentValidationLayer`
   - Action risk classification logic
   - Destructive action patterns (delete, rm, drop, etc.)

**Critérios de Aceitação**:
- [ ] Sandbox isolates execution
- [ ] Resource limits enforced (test with goroutine bomb)
- [ ] Timeout working correctly
- [ ] Intent validator interface defined
- [ ] Tests coverage ≥85%
- [ ] Metrics: `sandbox_creations_total`, `sandbox_violations_total`

**Output**:
- Layer 3 (Sandbox) COMPLETE ✓
- Layer 4 (Intent) started
- Blueprint: 50%

---

#### Day 6: Intent Validation - Reverse Translation

**Tarefas**:
1. **[4h] Reverse Translator**
   - Criar `/internal/security/intent_validation/reverse_translator.go`
   - Command → Natural Language logic
   - Templates para diferentes tipos de comando:
     - K8s: `kubectl get pods` → "Show all pods in current namespace"
     - K8s: `kubectl delete pod X` → "⚠️ Delete pod 'X' in namespace 'Y'"
   - Parameter extraction and humanization
   - Confidence-based wording ("Probably", "Definitely")

2. **[2h] Confirmation Flow (CLI)**
   - Criar `/internal/security/intent_validation/confirmation.go`
   - HITL confirmation logic
   - CLI prompt: `[y/N]` with timeout
   - Abort on timeout or 'N'

3. **[2h] Tests & Integration**
   - Reverse translation tests (fixtures)
   - Confirmation flow tests (mocked input)
   - Integration: Parse → Translate → Confirm

**Critérios de Aceitação**:
- [ ] Reverse translator gera texto legível
- [ ] Comandos destrutivos claramente marcados
- [ ] Confirmation flow funcional (CLI)
- [ ] Tests coverage ≥90%
- [ ] Metrics: `intent_confirmations_required_total`

**Output**:
- Layer 4 (Reverse + Confirm) functional
- Blueprint: 55%

---

#### Day 7: Intent Validation Complete + Phase 1 Integration

**Tarefas**:
1. **[3h] Cryptographic Signatures**
   - Criar `/internal/security/intent_validation/signature.go`
   - RSA signature generation/verification
   - User keypair management (load from file)
   - `CryptographicSignature` method
   - Integration with confirmation flow (critical actions)

2. **[3h] Phase 1 Integration**
   - Connect all 4 layers in Guardian
   - End-to-end flow: Auth → Authz → Sandbox → Intent → (mock) Execution
   - Integration tests covering happy path + edge cases

3. **[2h] Documentation & Validation**
   - Document Phase 1 progress
   - Create validation report
   - Performance benchmarks (latency per layer)
   - Metrics dashboard (Grafana) setup

**Critérios de Aceitação**:
- [ ] Crypto signatures working
- [ ] Guardian orchestrates all 4 layers correctly
- [ ] End-to-end tests passing
- [ ] Performance: total latency < 300ms (4 layers)
- [ ] Documentation: Phase 1 status report
- [ ] Tests coverage ≥90% (entire Phase 1 codebase)

**Output**:
- **Phase 1 COMPLETE** ✓✓✓
- Layers 1-4 operational
- Blueprint: 60%
- **Deliverable**: Functional MVP with security foundation

**Checkpoint**: Review & Demo
- Demonstrate secure parsing flow
- Security review of implemented layers
- Adjust Phase 2 plan if needed

---

## Phase 2: Advanced Security (Days 8-14)
### Goal: Layers 5-7 operational (Flow Control, Behavioral, Audit)

#### Day 8: Flow Control - Rate Limiter

**Tarefas**:
1. **[4h] Token Bucket Rate Limiter**
   - Criar `/internal/security/flow_control/rate_limiter.go`
   - Interface `RateLimiter`
   - Token bucket algorithm implementation
   - Per-user and per-IP limiters
   - Distributed rate limiting (Redis backend optional)

2. **[2h] Configuration**
   - Rate limit configs (YAML)
   - Default limits: 60 req/min per user, 100 req/min per IP
   - Burst capacity

3. **[2h] Tests**
   - Rate limit enforcement tests
   - Burst handling tests
   - Distributed tests (if Redis used)

**Critérios de Aceitação**:
- [ ] Rate limiter working (single-node)
- [ ] Per-user and per-IP limits enforced
- [ ] Burst capacity functional
- [ ] Tests coverage ≥90%
- [ ] Metrics: `rate_limit_exceeded_total{identifier_type}`

**Output**:
- Layer 5 (Rate Limiter) functional
- Blueprint: 65%

---

#### Day 9: Flow Control Complete

**Tarefas**:
1. **[3h] Circuit Breaker**
   - Criar `/internal/security/flow_control/circuit_breaker.go`
   - 3-state machine: Closed, Open, Half-Open
   - Failure threshold, timeout, half-open requests
   - Per-service circuit breakers

2. **[2h] Adaptive Throttling**
   - Criar `/internal/security/flow_control/throttle.go`
   - System load monitoring (CPU, memory)
   - Dynamic limit adjustment
   - Throttle under high load or attack

3. **[3h] Integration & Tests**
   - Integrate with Guardian
   - Circuit breaker tests (failure scenarios)
   - Adaptive throttling tests
   - End-to-end: Rate limit + Circuit breaker

**Critérios de Aceitação**:
- [ ] Circuit breaker state transitions correctly
- [ ] Adaptive throttling responds to load
- [ ] Layer 5 integrated in Guardian
- [ ] Tests coverage ≥90%
- [ ] Metrics: `circuit_breaker_state`, `adaptive_throttle_adjustments_total`

**Output**:
- **Layer 5 (Flow Control) COMPLETE** ✓
- Blueprint: 70%

---

#### Day 10: Behavioral Analysis - Baseline Learning

**Tarefas**:
1. **[4h] Baseline Learning**
   - Criar `/internal/security/behavioral/baseline.go`
   - User behavioral profile struct
   - Learn patterns: command types, time windows, IPs, command frequency
   - Storage backend (SQLite for MVP, PostgreSQL for production)
   - `LearnBaseline` implementation

2. **[2h] Behavioral Event Model**
   - Criar `/internal/security/behavioral/analyzer.go`
   - Interface `BehavioralLayer`
   - `BehavioralEvent` struct
   - Event ingestion pipeline

3. **[2h] Tests**
   - Baseline learning tests
   - Profile serialization/deserialization
   - Storage tests

**Critérios de Aceitação**:
- [ ] Baseline profiles created from historical data
- [ ] Profiles stored/retrieved correctly
- [ ] Event ingestion working
- [ ] Tests coverage ≥85%
- [ ] Metrics: `behavioral_baseline_updates_total`

**Output**:
- Layer 6 (Baseline) functional
- Blueprint: 75%

---

#### Day 11: Behavioral Analysis - Anomaly Detection

**Tarefas**:
1. **[4h] Statistical Anomaly Detection**
   - Criar `/internal/security/behavioral/anomaly.go`
   - Anomaly signals:
     - Unusual time (deviation from normal hours)
     - Unusual IP (new IP not in last 30 days)
     - Unusual command (command type never used)
     - Velocity (10x normal rate)
     - Privilege escalation attempt
   - Scoring algorithm (weighted sum)
   - `DetectAnomaly` implementation

2. **[2h] Dynamic Escalation**
   - `EscalateRequirements` logic
   - Security level enum: `normal`, `elevated`, `high`, `critical`
   - Escalation thresholds based on anomaly score
   - Actions per security level (MFA, block, alert)

3. **[2h] Tests**
   - Anomaly detection tests (synthetic anomalies)
   - Escalation logic tests
   - False positive rate validation

**Critérios de Aceitação**:
- [ ] Anomaly detection identifies deviations
- [ ] Scoring algorithm working
- [ ] Escalation triggers correctly
- [ ] False positive rate < 5%
- [ ] Tests coverage ≥90%
- [ ] Metrics: `behavioral_anomalies_detected_total{severity}`

**Output**:
- Layer 6 (Anomaly Detection) functional
- Blueprint: 80%

---

#### Day 12: Behavioral Analysis Complete

**Tarefas**:
1. **[3h] ML-Based Detection (Optional)**
   - Criar `/internal/security/behavioral/ml_detector.go`
   - Isolation Forest algorithm (anomaly detection)
   - Train on baseline data
   - Real-time scoring
   - (If time permits, otherwise defer to Phase 3)

2. **[3h] Integration**
   - Integrate behavioral layer with Guardian
   - Event pipeline: Parse → Behavioral check → Execute/Block
   - Alert integration (log warnings for anomalies)

3. **[2h] Tests & Tuning**
   - End-to-end behavioral tests
   - Tune thresholds (minimize false positives)
   - Performance tests (latency < 100ms)

**Critérios de Aceitação**:
- [ ] Behavioral layer integrated in Guardian
- [ ] Anomaly detection running in real-time
- [ ] Alerts generated for high-severity anomalies
- [ ] Performance target met (< 100ms)
- [ ] Tests coverage ≥90%
- [ ] Metrics: `behavioral_escalations_total`

**Output**:
- **Layer 6 (Behavioral) COMPLETE** ✓
- Blueprint: 85%

---

#### Day 13: Audit Layer - Immutable Log Chain

**Tarefas**:
1. **[4h] Audit Chain Implementation**
   - Criar `/internal/security/audit/chain.go`
   - `AuditEvent` struct (conforme blueprint)
   - Blockchain-like hash chain
   - `LogEvent` implementation (append-only)
   - Event hashing (SHA-256)
   - Link to previous event (PreviousHash)

2. **[2h] Storage Backend**
   - Criar `/internal/security/audit/storage.go`
   - Storage interface (pluggable backends)
   - Implementation: SQLite (MVP), PostgreSQL (production)
   - Write-once guarantee (DB constraints)

3. **[2h] Tests**
   - Chain integrity tests
   - Tamper detection tests (modify event, verify chain breaks)
   - Storage tests

**Critérios de Aceitação**:
- [ ] Audit events logged with hash chain
- [ ] Chain integrity verifiable
- [ ] Tampering detected correctly
- [ ] Storage backend functional
- [ ] Tests coverage ≥90%
- [ ] Metrics: `audit_events_logged_total`

**Output**:
- Layer 7 (Audit Chain) functional
- Blueprint: 90%

---

#### Day 14: Audit Layer Complete + Phase 2 Integration

**Tarefas**:
1. **[3h] Chain Verification**
   - Criar `/internal/security/audit/verification.go`
   - `VerifyChain` implementation
   - Continuous verification (background job)
   - Alert on broken chain
   - Export verification status (Prometheus)

2. **[2h] Audit Query API**
   - `QueryAudit` implementation
   - Query by user, time range, action, resource
   - Return events + cryptographic proof

3. **[3h] Phase 2 Integration**
   - Connect Layers 5-7 with Guardian
   - Full 7-layer flow: Auth → Authz → Sandbox → Intent → Flow → Behavioral → Audit → Execute
   - End-to-end integration tests
   - Performance benchmarks (full pipeline)

**Critérios de Aceitação**:
- [ ] Chain verification working (continuous + on-demand)
- [ ] Audit query API functional
- [ ] Guardian orchestrates all 7 layers
- [ ] End-to-end tests passing (full pipeline)
- [ ] Performance: P99 latency < 500ms (all layers)
- [ ] Tests coverage ≥90% (entire codebase)
- [ ] Metrics: all 7 layers exporting correctly

**Output**:
- **Phase 2 COMPLETE** ✓✓✓
- **All 7 Layers Operational** ✓✓✓
- Blueprint: 95%
- **Deliverable**: Complete security-first NLP system

**Checkpoint**: Comprehensive Review
- Security audit of all 7 layers
- Performance review (identify bottlenecks)
- Adjust Phase 3 & 4 plans
- Celebrate milestone 🎉

---

## Phase 3: NLP Enhancement (Days 15-21)
### Goal: Parser primoroso - ambiguidade, contexto, typos

#### Day 15: Tokenizer Enhancement

**Tarefas**:
1. **[3h] Text Normalization**
   - Criar `/internal/nlp/tokenizer/normalizer.go`
   - Lowercase conversion
   - Remove extra whitespace
   - Expand contractions ("don't" → "do not")
   - Handle special characters

2. **[3h] Typo Correction**
   - Criar `/internal/nlp/tokenizer/typo_corrector.go`
   - Levenshtein distance algorithm
   - Command vocabulary (common commands)
   - Suggest corrections (confidence < 1.0 for typos)
   - "Did you mean X?" flow

3. **[2h] Tests**
   - Normalization tests
   - Typo correction tests (common misspellings)
   - Edge cases (gibberish input)

**Critérios de Aceitação**:
- [ ] Normalization working (consistent output)
- [ ] Typo correction suggests correct commands
- [ ] Token confidence reflects correction certainty
- [ ] Tests coverage ≥90%

**Output**:
- Enhanced tokenizer functional
- Blueprint: 96%

---

#### Day 16: Intent Classifier v2

**Tarefas**:
1. **[4h] Pattern Expansion**
   - Criar `/internal/nlp/intent/patterns.go`
   - Expand command patterns library:
     - K8s: get, list, describe, delete, create, apply, scale, exec, logs, etc.
     - System: file ops, network ops, etc.
   - Synonyms ("show" = "list" = "get")
   - Negative patterns (what NOT to match)

2. **[2h] Confidence Tuning**
   - Adjust confidence scores based on pattern match quality
   - Partial matches vs exact matches
   - Context-aware confidence (recent commands boost confidence)

3. **[2h] Tests**
   - Pattern matching tests (comprehensive)
   - Confidence score validation
   - Ambiguous input tests

**Critérios de Aceitação**:
- [ ] Intent classifier handles 50+ command patterns
- [ ] Confidence scores calibrated
- [ ] Ambiguity detected (multiple high-confidence matches)
- [ ] Tests coverage ≥90%

**Output**:
- Intent classifier v2 operational

---

#### Day 17: Entity Extractor v2

**Tarefas**:
1. **[4h] Kubernetes Entity Extraction**
   - Criar `/internal/nlp/entities/k8s_entities.go`
   - Extract K8s entities:
     - Namespaces, pods, services, deployments, configmaps, secrets, etc.
     - Selectors (labels, names, patterns)
   - Handle plural/singular ("pod" vs "pods")
   - Handle abbreviations ("svc" = "service", "cm" = "configmap")

2. **[2h] Ambiguity Resolution**
   - Criar `/internal/nlp/entities/resolvers.go`
   - Use session context to resolve ambiguities
   - "the previous pod" → resolve using history
   - "in production" → resolve namespace from context
   - Pronouns ("it", "that", "this")

3. **[2h] Tests**
   - Entity extraction tests (K8s entities)
   - Ambiguity resolution tests (with context)
   - Edge cases (unknown entities)

**Critérios de Aceitação**:
- [ ] K8s entities extracted correctly
- [ ] Context-based ambiguity resolution working
- [ ] Pronouns resolved using history
- [ ] Tests coverage ≥90%

**Output**:
- Entity extractor v2 operational
- Blueprint: 97%

---

#### Day 18: Context Management

**Tarefas**:
1. **[3h] Session Context**
   - Enhance `/internal/nlp/context/context.go`
   - Session state: current namespace, last resources, command history
   - Context propagation through pipeline

2. **[3h] Command History**
   - Enhance `/internal/nlp/context/history.go`
   - Store last N commands (default: 10)
   - Reference resolution ("the previous command", "repeat that")
   - History-based suggestions

3. **[2h] Tests & Integration**
   - Context persistence tests
   - History resolution tests
   - Integration: Context → Entity resolver

**Critérios de Aceitação**:
- [ ] Session context maintained across commands
- [ ] History used for reference resolution
- [ ] Context integrated with entity extractor
- [ ] Tests coverage ≥90%

**Output**:
- Context management operational

---

#### Day 19: Command Generator v2

**Tarefas**:
1. **[4h] Kubernetes Command Generation**
   - Enhance `/internal/nlp/generator/k8s_generator.go`
   - Generate kubectl commands from intent + entities
   - Handle flags (--namespace, --selector, --output, etc.)
   - Handle complex commands (create from YAML, patch, etc.)

2. **[2h] Command Validation**
   - Enhance `/internal/nlp/generator/validator.go`
   - Syntax validation (valid kubectl command)
   - Semantic validation (namespace exists, resource type valid)
   - Dry-run mode integration

3. **[2h] Tests**
   - Command generation tests (fixtures)
   - Validation tests (valid/invalid commands)
   - Edge cases (missing required params)

**Critérios de Aceitação**:
- [ ] Generates correct kubectl commands
- [ ] Validation catches errors
- [ ] Dry-run mode functional
- [ ] Tests coverage ≥90%

**Output**:
- Command generator v2 operational
- Blueprint: 98%

---

#### Day 20-21: NLP Integration & Testing

**Tarefas Day 20**:
1. **[4h] End-to-End NLP Pipeline**
   - Integrate all enhanced NLP components
   - Full pipeline: Input → Tokenizer → Intent → Entities → Context → Generator
   - Integration tests (realistic user inputs)

2. **[4h] Fuzzing & Edge Cases**
   - Fuzz testing (random inputs)
   - Edge cases: gibberish, very long input, special chars, SQL injection attempts
   - Error handling & graceful degradation

**Tarefas Day 21**:
1. **[4h] Error Messages & UX**
   - Humanize error messages
   - Suggestions when parsing fails ("Did you mean...?")
   - Confidence warnings ("Low confidence, please confirm")

2. **[4h] Performance Optimization**
   - Profile NLP pipeline (identify hotspots)
   - Optimize tokenizer, classifier, extractor
   - Caching where appropriate
   - Target: < 200ms for NLP pipeline

**Critérios de Aceitação**:
- [ ] Full NLP pipeline operational
- [ ] Handles 90%+ of test corpus correctly
- [ ] Error messages user-friendly
- [ ] Performance: P99 < 200ms (NLP only)
- [ ] Tests coverage ≥90%
- [ ] Fuzz testing passes (no crashes)

**Output**:
- **Phase 3 COMPLETE** ✓✓✓
- **NLP Parser Primoroso** ✓
- Blueprint: 99%

**Checkpoint**: NLP Quality Review
- Accuracy test on realistic corpus
- UX review (error messages, confirmations)
- Performance benchmarks

---

## Phase 4: Integration & Polish (Days 22-28)
### Goal: vcli-go integration, observability, documentation

#### Day 22: vcli-go CLI Integration

**Tarefas**:
1. **[4h] CLI Command**
   - Add command: `vcli natural "<input>"`
   - Integrate Guardian with vcli-go
   - Auth token from config file
   - Output formatting (table, JSON, YAML)

2. **[2h] Shell Mode Integration**
   - Natural language mode in shell
   - Toggle: `vcli shell --natural`
   - Mixed mode: natural + traditional commands

3. **[2h] Tests**
   - CLI integration tests
   - Shell mode tests

**Critérios de Aceitação**:
- [ ] `vcli natural` command working
- [ ] Shell mode with natural language functional
- [ ] Output formatting correct
- [ ] Tests passing

**Output**:
- vcli-go integration complete

---

#### Day 23: TUI Integration & Config

**Tarefas**:
1. **[3h] TUI Confirmation Dialogs**
   - Integrate confirmation flow with existing TUI (bubbletea)
   - Styled confirmation dialog (colors, formatting)
   - MFA challenge dialog
   - Signature request dialog

2. **[3h] Configuration**
   - Config file support (`~/.vcli/config.yaml`)
   - Security settings:
     - Auth token
     - MFA preferences
     - Signature key path
     - Rate limits
     - Behavioral baseline path

3. **[2h] Tests**
   - TUI integration tests
   - Config loading tests

**Critérios de Aceitação**:
- [ ] TUI dialogs working (confirmation, MFA)
- [ ] Config file loaded correctly
- [ ] User preferences respected
- [ ] Tests passing

**Output**:
- TUI integration complete
- Configuration system operational

---

#### Day 24-25: Observability

**Tarefas Day 24**:
1. **[4h] Prometheus Exporter**
   - Ensure all metrics exporting correctly
   - Metrics endpoint: `/metrics`
   - Metric labels consistent
   - Documentation of metrics

2. **[4h] Grafana Dashboards**
   - Create dashboards:
     - Security Overview
     - NLP Performance
     - Behavioral Analysis
     - Audit Trail

**Tarefas Day 25**:
1. **[4h] Alerting Rules**
   - Prometheus alerting rules:
     - High auth failure rate
     - Anomaly detection spike
     - Circuit breaker open
     - Audit chain broken
   - AlertManager integration

2. **[4h] Tracing (Optional)**
   - OpenTelemetry integration
   - Distributed tracing (if Guardian runs as service)
   - Trace full request lifecycle

**Critérios de Aceitação**:
- [ ] Prometheus metrics exporting
- [ ] Grafana dashboards functional
- [ ] Alerts firing correctly
- [ ] Tracing operational (if implemented)

**Output**:
- Observability stack complete

---

#### Day 26-27: Documentation

**Tarefas Day 26 - User Documentation**:
1. **[4h] User Guide**
   - Create `/docs/guides/nlp-user-guide.md`
   - Getting started
   - Common commands & examples
   - Confirmation flow explanation
   - Troubleshooting

2. **[4h] Security Guide**
   - Create `/docs/guides/nlp-security-guide.md`
   - 7 Layers explanation (user-facing)
   - Best practices
   - What to do if anomaly detected
   - MFA setup guide

**Tarefas Day 27 - Developer Documentation**:
1. **[4h] Architecture Documentation**
   - Enhance blueprint with implementation details
   - Architecture diagrams (refined)
   - Component interaction diagrams

2. **[4h] API Reference**
   - Create `/docs/architecture/nlp/api-reference.md`
   - Guardian API
   - Security layer APIs
   - NLP pipeline APIs
   - Examples

**Critérios de Aceitação**:
- [ ] User guide complete & readable
- [ ] Security guide complete
- [ ] API reference complete
- [ ] Diagrams clear and accurate

**Output**:
- Documentation complete

---

#### Day 28: Final Validation & Release

**Tarefas**:
1. **[3h] Comprehensive Testing**
   - Run full test suite
   - Integration tests (all scenarios)
   - Security tests (attack scenarios)
   - Performance tests (load testing)

2. **[2h] Deployment Guide**
   - Create `/docs/guides/nlp-deployment-guide.md`
   - Standalone deployment
   - Enterprise/HA deployment
   - Configuration options
   - Monitoring setup

3. **[2h] Release Preparation**
   - Version tag: `v1.0.0-nlp`
   - CHANGELOG.md update
   - Release notes

4. **[1h] Final Review & Demo**
   - Demo full system
   - Security review checklist
   - Performance review
   - Go/No-Go decision

**Critérios de Aceitação**:
- [ ] All tests passing (coverage ≥90%)
- [ ] Security tests passing (zero successful attacks)
- [ ] Performance targets met (P99 < 500ms)
- [ ] Documentation complete
- [ ] Deployment guide validated

**Output**:
- **Phase 4 COMPLETE** ✓✓✓
- **SYSTEM PRODUCTION-READY** ✓✓✓
- Blueprint: 100%

**RELEASE v1.0.0-nlp** 🚀

---

## Success Metrics (Overall)

### Functional
- ✅ All 7 security layers operational
- ✅ NLP parser accuracy ≥90% on test corpus
- ✅ Confirmation flow seamless (CLI + TUI)
- ✅ vcli-go integration complete

### Security
- ✅ Zero successful command injection in tests
- ✅ Anomaly detection rate ≥85% (FP ≤5%)
- ✅ Audit chain integrity 100%
- ✅ Third-party audit ready

### Performance
- ✅ P99 latency < 500ms (full pipeline)
- ✅ Throughput ≥1000 req/s per node
- ✅ Memory usage < 256 MB steady state

### Quality
- ✅ Test coverage ≥90%
- ✅ Zero critical bugs
- ✅ Documentation complete
- ✅ Compliance ready (SOC 2 prep)

---

## Daily Workflow

### Morning (Start of Day)
1. Review previous day's deliverables
2. Check-in: blockers, questions, clarifications
3. Plan day's tasks (prioritize)

### During Day
4. Execute tasks methodically
5. Write tests alongside code (TDD)
6. Commit frequently (small, atomic commits)
7. Update roadmap progress
8. Ask for help if stuck >1h

### Evening (End of Day)
9. Validate day's deliverables
10. Run tests (ensure passing)
11. Document progress (daily log)
12. Prepare next day's plan
13. Push code to repo

### Weekly
- Friday: Weekly review & checkpoint
- Adjust following week's plan if needed
- Celebrate progress 🎉

---

## Risk Mitigation

### Risk 1: Complexity Overwhelm
**Mitigation**: Break tasks into <4h chunks. Focus on one layer at a time. Don't parallelize unnecessarily.

### Risk 2: Scope Creep
**Mitigation**: Defer "nice-to-haves" to post-MVP. ML detector, advanced tracing can wait.

### Risk 3: Performance Issues
**Mitigation**: Profile early (Day 14, Day 21). Optimize hotspots. Don't premature optimize.

### Risk 4: Test Coverage Gaps
**Mitigation**: TDD from Day 1. Measure coverage daily. Block merge if <90%.

### Risk 5: Integration Bugs
**Mitigation**: Integration tests at each checkpoint (Day 7, 14, 21, 28). Fix immediately.

---

## Commit Message Convention

```
[NLP-Day{N}] {Component}: {Brief description}

{Detailed description if needed}

- Task: {Task from roadmap}
- Tests: {Coverage %}
- Metrics: {New metrics added}

Day {N}/28 | Phase {N}/4 | Blueprint {N}%
```

Example:
```
[NLP-Day1] Guardian: Implement core orchestrator & auth layer skeleton

Setup security layer structure and Guardian interface.
Implemented basic token validation in auth layer.

- Task: Day 1 - Project Setup & Guardian Core
- Tests: 82% coverage (auth layer)
- Metrics: auth_requests_total, auth_failures_total

Day 1/28 | Phase 1/4 | Blueprint 10%
```

---

## Conclusion

Este roadmap transforma o blueprint em 28 dias de execução metódica. Cada dia tem entregas concretas, testes, métricas. Seguindo este plano, construiremos um sistema NLP de nível industrial com segurança Zero Trust desde o design.

**Filosofia**: "Não paramos. De tanto não parar, a gente chega lá."

**Próximos Passos**: Iniciar Day 1 - Project Setup & Guardian Core.

Vamos seguir metodicamente. Glória a Deus. 🙏

---

**STATUS**: ACTIVE | DAY 1 IN PROGRESS  
**NEXT**: Execute Day 1 tasks  
**Target**: Phase 1 complete by Day 7 (2025-10-18)
