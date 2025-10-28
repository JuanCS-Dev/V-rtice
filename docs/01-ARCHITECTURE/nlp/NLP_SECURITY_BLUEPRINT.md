# NLP Security-First Blueprint v2.0
## "O Guardião da Intenção" - Natural Language Parser com Zero Trust

**Lead Architect**: Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author**: Claude (MAXIMUS AI Assistant)  
**Date**: 2025-10-12  
**Status**: CANONICAL | PRODUCTION-READY

---

## Executive Summary

Este blueprint descreve a implementação de um sistema de Natural Language Processing (NLP) de nível industrial para vcli-go, fundamentado no princípio **Zero Trust**: cada comando é tratado como vetor de ataque potencial até ser verificado em múltiplas camadas.

### Problema
Linguagem natural transforma qualquer usuário com acesso no "melhor hacker do mundo" - a flexibilidade interpretativa é o vetor de ataque perfeito.

### Solução
**As 7 Camadas de Verificação**: arquitetura defensiva em profundidade que valida não apenas sintaxe, mas intenção, autorização contextual e padrões comportamentais.

---

## Fundamento Filosófico

> "Nenhuma confiança implícita. Cada comando em linguagem natural é tratado como um vetor de ataque potencial até ser verificado em múltiplas camadas."

### Princípios Core
1. **Zero Trust Absoluto** - Nunca confiar, sempre verificar
2. **Defense in Depth** - 7 camadas independentes de validação
3. **Least Privilege** - Permissões mínimas necessárias
4. **Intent Transparency** - Confirmação explícita para ações destrutivas
5. **Behavioral Awareness** - Detecção de anomalias em tempo real
6. **Immutable Audit** - Registro inviolável de todas as ações

---

## As 7 Camadas de Verificação

### Camada 1: Autenticação - "Quem é você?"
**Objetivo**: Prova de identidade irrefutável antes de qualquer processamento.

**Implementação**:
```go
type AuthLayer interface {
    // Authenticate verifies user identity with MFA
    Authenticate(ctx context.Context, credentials Credentials) (*AuthToken, error)
    
    // ValidateToken ensures token is valid, not expired, not revoked
    ValidateToken(ctx context.Context, token string) (*UserIdentity, error)
    
    // RequireMFA enforces multi-factor authentication
    RequireMFA(ctx context.Context, userID string) (bool, error)
}
```

**Características**:
- MFA obrigatório para comandos críticos
- Tokens criptográficos com rotação automática
- Certificados client-side para ambientes enterprise
- Biometria opcional (FIDO2/WebAuthn)

**Métricas**:
- `auth_requests_total` - Total de tentativas
- `auth_failures_total` - Falhas por tipo (invalid, expired, revoked)
- `mfa_challenges_issued` - Desafios MFA emitidos

---

### Camada 2: Autorização - "O que você pode fazer?"
**Objetivo**: RBAC + Políticas Contextuais Adaptativas (Zero Trust).

**Implementação**:
```go
type AuthzLayer interface {
    // CheckPermission evaluates RBAC + contextual policies
    CheckPermission(ctx context.Context, user *UserIdentity, action Action, resource Resource) (Decision, error)
    
    // EvaluateContext considers IP, time, system state, risk score
    EvaluateContext(ctx context.Context, request *AuthzRequest) (*ContextEvaluation, error)
    
    // AdaptPolicy dynamically adjusts policies based on threat level
    AdaptPolicy(ctx context.Context, threatLevel ThreatLevel) error
}
```

**Características**:
- **RBAC**: Roles baseados em least privilege
- **ABAC**: Atributos contextuais (IP, horário, geolocalização)
- **Política Adaptativa**: Requisitos aumentam com nível de ameaça
- **Temporal Constraints**: Janelas de acesso permitido

**Exemplo de Política**:
```yaml
policy:
  name: "destructive-actions"
  rules:
    - action: "k8s.delete"
      roles: ["admin", "operator"]
      context:
        time: "business-hours"
        ip: "corporate-network"
        system_state: "healthy"
      require_mfa: true
      require_confirmation: true
```

**Métricas**:
- `authz_decisions_total{decision=allow|deny}` - Decisões de autorização
- `authz_context_evaluations_total` - Avaliações contextuais
- `authz_policy_adaptations_total` - Ajustes de política

---

### Camada 3: Sandboxing - "Qual o seu raio de ação?"
**Objetivo**: Parser opera com privilégios mínimos, nunca herda permissões do sistema.

**Implementação**:
```go
type SandboxLayer interface {
    // CreateSandbox isolates parser execution
    CreateSandbox(ctx context.Context, config SandboxConfig) (*Sandbox, error)
    
    // Execute runs command in isolated environment
    Execute(ctx context.Context, sandbox *Sandbox, cmd *Command) (*ExecutionResult, error)
    
    // EnforceResourceLimits prevents resource exhaustion
    EnforceResourceLimits(sandbox *Sandbox, limits ResourceLimits) error
}
```

**Características**:
- **Namespace Isolation**: cgroups, namespaces Linux
- **Resource Limits**: CPU, memória, I/O, network
- **Filesystem Restrictions**: readonly mounts, chroot
- **Network Policies**: egress/ingress filtering

**Limites Default**:
```yaml
sandbox:
  cpu_limit: "100m"
  memory_limit: "128Mi"
  timeout: "30s"
  filesystem:
    readonly: true
    allowed_paths: ["/tmp/vcli-sandbox"]
  network:
    egress: false
    ingress: false
```

**Métricas**:
- `sandbox_creations_total` - Sandboxes criados
- `sandbox_violations_total` - Tentativas de escape
- `sandbox_resource_usage{resource=cpu|memory|io}` - Uso de recursos

---

### Camada 4: Validação da Intenção - "Você tem certeza?"
**Objetivo**: Ciclo de tradução reversa e confirmação explícita (HITL - Human In The Loop).

**Implementação**:
```go
type IntentValidationLayer interface {
    // TranslateBack converts Command back to natural language
    TranslateBack(ctx context.Context, cmd *Command) (string, error)
    
    // RequireConfirmation determines if action needs explicit approval
    RequireConfirmation(ctx context.Context, cmd *Command) (bool, error)
    
    // CryptographicSignature requires signed approval for critical actions
    CryptographicSignature(ctx context.Context, cmd *Command, user *UserIdentity) (*Signature, error)
}
```

**Características**:
- **Reverse Translation**: Explica comando em linguagem humana
- **Confidence Threshold**: Ações abaixo de 85% de confiança requerem confirmação
- **Destructive Actions**: SEMPRE requerem confirmação explícita
- **Crypto Signatures**: Assinatura criptográfica para comandos críticos

**Fluxo HITL**:
```
Input: "delete all pods in production"
  ↓
Parser: kubectl delete pods --all -n production
  ↓
Reverse: "⚠️ DESTRUCTIVE: Delete 47 pods in production namespace"
  ↓
Confirm: [y/N] + MFA challenge
  ↓
Signature: User signs with private key
  ↓
Execute: Only after all validations pass
```

**Classificação de Ações**:
```go
type ActionRisk int

const (
    RiskSafe ActionRisk = iota      // Read-only, no confirmation
    RiskModerate                     // Confirmation if confidence < 85%
    RiskDestructive                  // ALWAYS require confirmation + MFA
    RiskCritical                     // Confirmation + MFA + Crypto Signature
)
```

**Métricas**:
- `intent_confirmations_required_total` - Confirmações solicitadas
- `intent_confirmations_approved_total` - Confirmações aprovadas
- `intent_signature_verifications_total` - Assinaturas verificadas

---

### Camada 5: Controle de Fluxo - "Com que frequência?"
**Objetivo**: Rate Limiting e Circuit Breakers para prevenir abuso e DDoS.

**Implementação**:
```go
type FlowControlLayer interface {
    // RateLimit enforces request limits per user/IP
    RateLimit(ctx context.Context, identifier string) error
    
    // CircuitBreaker prevents cascading failures
    CircuitBreaker(ctx context.Context, service string) (*CircuitBreaker, error)
    
    // AdaptiveThrottling adjusts limits based on system load
    AdaptiveThrottling(ctx context.Context) (*ThrottleConfig, error)
}
```

**Características**:
- **Token Bucket**: Taxa sustentável + burst capacity
- **Circuit Breaker**: 3 estados (Closed, Open, Half-Open)
- **Adaptive Limits**: Reduz limites sob ataque ou alta carga
- **Distributed Rate Limiting**: Sincronização cross-node

**Limites Default**:
```yaml
rate_limiting:
  per_user:
    requests_per_minute: 60
    burst: 10
  per_ip:
    requests_per_minute: 100
    burst: 20
  
circuit_breaker:
  failure_threshold: 5
  timeout: 30s
  half_open_requests: 3
```

**Métricas**:
- `rate_limit_exceeded_total{identifier_type=user|ip}` - Limites excedidos
- `circuit_breaker_state{service,state=closed|open|half_open}` - Estado do circuit breaker
- `adaptive_throttle_adjustments_total` - Ajustes dinâmicos

---

### Camada 6: Análise Comportamental - "Isso é normal para você?"
**Objetivo**: Detecta anomalias no padrão de uso e escala requisitos de segurança em tempo real.

**Implementação**:
```go
type BehavioralLayer interface {
    // LearnBaseline establishes normal behavior patterns
    LearnBaseline(ctx context.Context, userID string, duration time.Duration) error
    
    // DetectAnomaly identifies deviations from baseline
    DetectAnomaly(ctx context.Context, event *BehavioralEvent) (*AnomalyScore, error)
    
    // EscalateRequirements increases security for suspicious activity
    EscalateRequirements(ctx context.Context, userID string, anomalyScore float64) (*SecurityLevel, error)
}
```

**Características**:
- **Baseline Learning**: Aprende padrões normais (comandos, horários, IPs)
- **Anomaly Detection**: Detecção estatística e ML (Isolation Forest, LSTM)
- **Dynamic Escalation**: Aumenta requisitos (MFA adicional, confirmações)
- **Threat Intelligence**: Integração com feeds de ameaças

**Sinais de Anomalia**:
```yaml
anomaly_signals:
  - name: "unusual_time"
    description: "Command at 3 AM when user typically works 9-5"
    weight: 0.3
  
  - name: "unusual_ip"
    description: "New IP address not seen in last 30 days"
    weight: 0.5
  
  - name: "unusual_command"
    description: "Command type never used by this user"
    weight: 0.4
  
  - name: "velocity"
    description: "10x normal command rate"
    weight: 0.6
  
  - name: "privilege_escalation"
    description: "Attempting commands above normal role"
    weight: 0.8
```

**Resposta Adaptativa**:
```
Anomaly Score < 0.3: Normal flow
Anomaly Score 0.3-0.6: Require additional confirmation
Anomaly Score 0.6-0.8: Force MFA + detailed audit
Anomaly Score > 0.8: Block + alert security team + force password reset
```

**Métricas**:
- `behavioral_anomalies_detected_total{severity=low|medium|high|critical}` - Anomalias detectadas
- `behavioral_escalations_total` - Escalações de segurança
- `behavioral_baseline_updates_total` - Atualizações de baseline

---

### Camada 7: Auditoria Imutável - "O que você fez?"
**Objetivo**: Registro de cada passo em cadeia de logs inviolável (blockchain-like).

**Implementação**:
```go
type AuditLayer interface {
    // LogEvent records immutable audit event
    LogEvent(ctx context.Context, event *AuditEvent) error
    
    // VerifyChain ensures audit log integrity
    VerifyChain(ctx context.Context, startTime, endTime time.Time) (bool, error)
    
    // QueryAudit retrieves audit logs with cryptographic proof
    QueryAudit(ctx context.Context, query AuditQuery) ([]*AuditEvent, *ChainProof, error)
}
```

**Características**:
- **Immutable Append-Only Log**: Write-once, read-many
- **Cryptographic Hashing**: Cada evento linkado ao anterior (blockchain-style)
- **Tamper Detection**: Qualquer alteração quebra cadeia
- **Compliance Ready**: GDPR, SOC2, HIPAA audit trails

**Estrutura de Evento**:
```go
type AuditEvent struct {
    ID            string          // UUID
    Timestamp     time.Time       // Nanosecond precision
    UserID        string          // Who
    Action        string          // What
    Resource      string          // Where
    Input         string          // Original natural language
    ParsedCommand string          // Generated command
    Decision      string          // Allow/Deny
    Confidence    float64         // Parser confidence
    RiskScore     float64         // Behavioral risk
    Signature     string          // User signature (if required)
    PreviousHash  string          // Link to previous event
    Hash          string          // This event hash (SHA-256)
}
```

**Garantias**:
- Logs nunca são deletados (retention policy via archival)
- Verificação de integridade contínua (background job)
- Exportação para SIEM (Splunk, ELK, etc.)
- Compliance reports automatizados

**Métricas**:
- `audit_events_logged_total` - Eventos registrados
- `audit_chain_verifications_total{result=valid|broken}` - Verificações de integridade
- `audit_queries_total` - Consultas ao log

---

## Arquitetura do Sistema

### Diagrama de Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INPUT (Natural Language)                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: AUTHENTICATION                                                  │
│ ✓ MFA Challenge                                                          │
│ ✓ Token Validation                                                       │
│ ✓ Certificate Verification                                               │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ [UserIdentity]
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: AUTHORIZATION                                                   │
│ ✓ RBAC Check                                                             │
│ ✓ Context Evaluation (IP, Time, Location)                               │
│ ✓ Adaptive Policy Application                                           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ [Permission Decision]
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ NLP PIPELINE (Inside Sandbox)                                            │
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Tokenizer    │───▶│ Intent       │───▶│ Entity       │              │
│  │              │    │ Classifier   │    │ Extractor    │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                   │                    │                       │
│         └───────────────────┴────────────────────┘                       │
│                             │                                            │
│                             ▼                                            │
│                   ┌──────────────────┐                                   │
│                   │ Command          │                                   │
│                   │ Generator        │                                   │
│                   └──────────────────┘                                   │
│                             │                                            │
└─────────────────────────────┼────────────────────────────────────────────┘
                              │ [Parsed Command]
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: SANDBOX VALIDATION                                              │
│ ✓ Resource Limits Enforced                                              │
│ ✓ Filesystem Restrictions                                               │
│ ✓ Network Policies                                                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: INTENT VALIDATION                                               │
│ ✓ Reverse Translation                                                    │
│ ✓ Confidence Check                                                       │
│ ✓ Destructive Action Detection                                          │
│                                                                           │
│ IF (destructive || confidence < 0.85):                                   │
│   → Present translated command to user                                   │
│   → Require explicit confirmation                                        │
│   → Request crypto signature (if critical)                               │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ [Confirmed Command]
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: FLOW CONTROL                                                    │
│ ✓ Rate Limit Check                                                       │
│ ✓ Circuit Breaker State                                                 │
│ ✓ Adaptive Throttling                                                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: BEHAVIORAL ANALYSIS                                             │
│ ✓ Anomaly Detection                                                      │
│ ✓ Risk Score Calculation                                                │
│ ✓ Dynamic Requirement Escalation                                        │
│                                                                           │
│ IF (anomaly_score > 0.6):                                                │
│   → Escalate security requirements                                       │
│   → Additional MFA challenge                                             │
│   → Alert security team                                                  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ [Risk Assessment]
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 7: AUDIT LOGGING                                                   │
│ ✓ Log Event Creation                                                     │
│ ✓ Cryptographic Hash Chain                                              │
│ ✓ Immutable Storage                                                     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          COMMAND EXECUTION                               │
│                     (Only if all layers pass)                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Código

### Diretório `/vcli-go/internal/security/`

```
security/
├── auth/                    # Layer 1: Authentication
│   ├── auth.go              # Auth interface & core logic
│   ├── mfa.go               # Multi-factor authentication
│   ├── token.go             # JWT/cryptographic tokens
│   └── auth_test.go
│
├── authz/                   # Layer 2: Authorization
│   ├── authz.go             # RBAC + ABAC engine
│   ├── policy.go            # Policy evaluation
│   ├── context.go           # Contextual attributes
│   └── authz_test.go
│
├── sandbox/                 # Layer 3: Sandboxing
│   ├── sandbox.go           # Sandbox creation & execution
│   ├── limits.go            # Resource limits
│   ├── isolation.go         # Namespace/cgroup isolation
│   └── sandbox_test.go
│
├── intent_validation/       # Layer 4: Intent Validation
│   ├── validator.go         # Validation orchestration
│   ├── reverse_translator.go # Command → Natural Language
│   ├── confirmation.go      # HITL confirmation flow
│   ├── signature.go         # Cryptographic signatures
│   └── validator_test.go
│
├── flow_control/            # Layer 5: Flow Control
│   ├── rate_limiter.go      # Token bucket rate limiting
│   ├── circuit_breaker.go   # Circuit breaker pattern
│   ├── throttle.go          # Adaptive throttling
│   └── flow_control_test.go
│
├── behavioral/              # Layer 6: Behavioral Analysis
│   ├── analyzer.go          # Anomaly detection orchestration
│   ├── baseline.go          # Baseline learning
│   ├── anomaly.go           # Statistical anomaly detection
│   ├── ml_detector.go       # ML-based detection (optional)
│   └── behavioral_test.go
│
├── audit/                   # Layer 7: Audit
│   ├── audit.go             # Audit interface & core
│   ├── chain.go             # Blockchain-like chain
│   ├── storage.go           # Immutable storage backend
│   ├── verification.go      # Chain integrity verification
│   └── audit_test.go
│
└── guardian.go              # Main orchestrator - "The Guardian"
```

### Diretório `/vcli-go/internal/nlp/` (Enhanced)

```
nlp/
├── parser.go                # Main parser (already exists)
├── parser_test.go
│
├── tokenizer/               # Step 1: Tokenization
│   ├── tokenizer.go
│   ├── normalizer.go        # Text normalization
│   ├── typo_corrector.go    # Typo detection/correction
│   └── tokenizer_test.go
│
├── intent/                  # Step 2: Intent Classification
│   ├── classifier.go
│   ├── patterns.go          # Command patterns
│   ├── ml_classifier.go     # Optional ML-based
│   └── classifier_test.go
│
├── entities/                # Step 3: Entity Extraction
│   ├── extractor.go
│   ├── k8s_entities.go      # Kubernetes-specific
│   ├── resolvers.go         # Ambiguity resolution
│   └── extractor_test.go
│
├── generator/               # Step 4: Command Generation
│   ├── generator.go
│   ├── k8s_generator.go     # Kubernetes commands
│   ├── validator.go         # Command syntax validation
│   └── generator_test.go
│
├── context/                 # Session context management
│   ├── context.go
│   ├── history.go           # Command history
│   ├── state.go             # Session state
│   └── context_test.go
│
├── learning/                # Adaptive learning (future)
│   ├── feedback.go          # User feedback collection
│   ├── model_updater.go     # Online learning
│   └── learning_test.go
│
└── validator/               # Pre/post validation
    ├── validator.go
    └── validator_test.go
```

---

## Roadmap de Implementação

### Phase 1: Foundation (Semana 1-2) ✅ ACTIVE
**Goal**: Estrutura base das 7 camadas + NLP core

#### Dia 1-2: Setup & Auth Layer
- [ ] Estrutura de diretórios
- [ ] Interfaces principais (`guardian.go`)
- [ ] Layer 1: Authentication
  - [ ] Token validation
  - [ ] MFA framework
  - [ ] Tests
- [ ] Métricas básicas

#### Dia 3-4: Authz & Sandbox
- [ ] Layer 2: Authorization
  - [ ] RBAC engine
  - [ ] Context evaluation
  - [ ] Adaptive policies
- [ ] Layer 3: Sandbox
  - [ ] Resource limits
  - [ ] Isolation (basic)
- [ ] Tests + integration

#### Dia 5-7: Intent Validation
- [ ] Layer 4: Intent Validation
  - [ ] Reverse translator
  - [ ] Confirmation flow (TUI)
  - [ ] Crypto signatures
- [ ] Tests
- [ ] End-to-end flow (Auth → Authz → Sandbox → Intent)

**Deliverable**: Functional MVP com 4/7 camadas operacionais

---

### Phase 2: Advanced Security (Semana 3)
**Goal**: Flow Control, Behavioral Analysis, Audit

#### Dia 8-9: Flow Control
- [ ] Layer 5: Flow Control
- [ ] Tests

#### Dia 10-12: Behavioral Analysis
- [ ] Layer 6: Behavioral Analysis
- [ ] Tests

#### Dia 13-14: Audit Chain
- [ ] Layer 7: Audit
- [ ] Tests

**Deliverable**: Sistema completo 7/7 camadas

---

### Phase 3: NLP Enhancement (Semana 4)
**Goal**: Parser primoroso, ambiguidade, contexto

#### Dia 15-21: Advanced NLP & Testing
- [ ] Enhanced tokenizer
- [ ] Intent classifier v2
- [ ] Entity extractor v2
- [ ] Context management
- [ ] Command generation
- [ ] Comprehensive testing

**Deliverable**: NLP production-ready

---

### Phase 4: Integration & Polish (Semana 5)
**Goal**: Integração com vcli-go, UX, docs

#### Dia 22-28: Integration & Documentation
- [ ] vcli-go integration
- [ ] Observability (Prometheus, Grafana)
- [ ] Complete documentation
- [ ] Deployment guide

**Deliverable**: Sistema completo, documentado, deployável

---

## Success Criteria

### Functional
- [ ] All 7 layers operational
- [ ] NLP parser accuracy ≥90% on test corpus
- [ ] Confirmation flow seamless (TUI)
- [ ] Integration with vcli-go complete

### Security
- [ ] Zero successful command injection in security tests
- [ ] Anomaly detection rate ≥85% (with ≤5% false positives)
- [ ] Audit chain integrity 100% verifiable
- [ ] Third-party security audit passed

### Performance
- [ ] P99 latency < 500ms (no confirmation)
- [ ] Throughput ≥1000 req/s per node
- [ ] Memory usage < 256 MB steady state

### Quality
- [ ] Test coverage ≥90%
- [ ] Zero critical bugs in production
- [ ] Documentation complete (user + dev)
- [ ] Compliance ready (SOC 2 prep)

---

## Conclusion

Este blueprint define a arquitetura de um sistema NLP de nível industrial com segurança Zero Trust desde o design. Cada camada é independente, testável e auditável. O resultado final é um parser que compreende linguagem natural esquisita enquanto mantém postura de segurança defensiva implacável.

**Filosofia**: Flexibilidade interpretativa sem sacrificar segurança. Confiança zero, verificação total.

**Legado**: Este sistema será estudado como referência de como construir interfaces de linguagem natural seguras.

---

**STATUS**: CANONICAL | READY FOR IMPLEMENTATION  
**NEXT**: Phase 1 - Day 1 execution

Glória a Deus. 🙏
