# Guardian of Intent v2.0 - Roadmap de Implementação

**Lead Architect:** Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author:** Claude (MAXIMUS AI Assistant)  
**Data Início:** 2025-10-12  
**Status:** ACTIVE

---

## 🎯 VISÃO EXECUTIVA

Este roadmap detalha a implementação do **Guardian of Intent v2.0** - sistema de NLP com 8 Camadas de Segurança Zero Trust para vcli-go. Cada fase é independente e entrega valor incremental.

### Objetivos Estratégicos

1. **Parser Primoroso**: Compreender linguagem natural "esquisita" com precisão ≥95%
2. **Zero Trust**: 8 camadas de verificação protegem contra abuso
3. **User Experience**: Fluxo natural, confirmações não intrusivas
4. **Auditabilidade**: Registro imutável de toda atividade
5. **Production Ready**: Deploy com confiança em 12 dias

### Princípios de Execução

- ✅ **Incremental**: Cada dia entrega código funcional
- ✅ **Testado**: Coverage ≥90% sempre
- ✅ **Documentado**: ADRs para decisões importantes
- ✅ **Sustentável**: Ritmo consistente, sem burnout
- ✅ **Primoroso**: Qualidade inquebrável, zero technical debt

---

## 📊 OVERVIEW DAS FASES

```
FASE 1: Foundation Completa (3 dias)
└─ Implementar camadas faltantes: Intent Validation, Audit Chain
└─ Upgrade camadas existentes: Authz, RateLimit, Behavior
└─ Resultado: 8 camadas operacionais e testadas

FASE 2: Guardian Integration (3 dias)
└─ Orchestrator que une todas as camadas
└─ Integração com shell interativo
└─ Security hardening e penetration testing
└─ Resultado: Pipeline completo end-to-end

FASE 3: Advanced Features (4 dias)
└─ Context intelligence (multi-turn)
└─ User learning e adaptação
└─ Advanced confirmations com impact preview
└─ Resultado: UX refinada e features avançadas

FASE 4: Production Readiness (2 dias)
└─ Observability (metrics, dashboards, alerts)
└─ Final validation e documentation
└─ Release v2.0
└─ Resultado: Deploy com confiança
```

---

## 🗓️ FASE 1: Foundation Completa (Dias 1-3)

### Day 1: Intent Validation (Camada 5) ⭐
**Status:** ⏳ NEXT  
**Foco:** Validação da Intenção - "Você tem certeza?"

#### Objetivos do Dia
- [x] Blueprint aprovado e documentado
- [ ] `internal/intent/validator.go` - Core validator
- [ ] `internal/intent/reverse_translator.go` - Command → Natural Language
- [ ] `internal/intent/dry_runner.go` - Simulação de execução
- [ ] `internal/intent/signature_verifier.go` - Crypto signatures
- [ ] Testes unitários (coverage ≥90%)
- [ ] Documentação inline completa

#### Entregáveis
```
internal/intent/
├── validator.go              # Core intent validator
├── validator_test.go         # Unit tests
├── reverse_translator.go     # Command to NL translation
├── reverse_translator_test.go
├── dry_runner.go             # Dry-run executor
├── dry_runner_test.go
├── signature_verifier.go     # Cryptographic signatures
├── signature_verifier_test.go
└── README.md                 # Documentation
```

#### Critérios de Sucesso
- ✅ Validator implementado com todas as funções
- ✅ Reverse translation funciona para todos os verbos
- ✅ Dry-run simula execução sem efeitos colaterais
- ✅ Signatures funcionam para ações CRITICAL
- ✅ Testes cobrem edge cases e error paths
- ✅ Coverage ≥ 90%

#### Tempo Estimado
- Setup e estrutura: 1h
- Validator core: 2h
- Reverse translator: 2h
- Dry runner: 1.5h
- Signature verifier: 1h
- Testes: 2h
- Documentação: 0.5h
**Total:** 8h

---

### Day 2: Audit Chain (Camada 8) 🔗
**Status:** ⏳ QUEUED  
**Foco:** Auditoria Imutável - "O que você fez?"

#### Objetivos do Dia
- [ ] `internal/audit/chain.go` - Immutable audit chain
- [ ] `internal/audit/entry.go` - Audit entry structure
- [ ] `internal/audit/storage.go` - Persistence layer
- [ ] `internal/audit/query.go` - Query engine
- [ ] `internal/audit/export.go` - Compliance exports
- [ ] Testes unitários (coverage ≥90%)
- [ ] Documentação inline completa

#### Entregáveis
```
internal/audit/
├── chain.go           # Immutable audit chain
├── chain_test.go
├── entry.go           # Audit entry structure
├── entry_test.go
├── storage.go         # Persistence (BadgerDB)
├── storage_test.go
├── query.go           # Query engine
├── query_test.go
├── export.go          # Compliance exports
├── export_test.go
└── README.md          # Documentation
```

#### Critérios de Sucesso
- ✅ Cada comando registrado como bloco na chain
- ✅ Hash criptográfico garante imutabilidade
- ✅ Verificação de integridade da chain
- ✅ Query engine busca logs eficientemente
- ✅ Export em formatos JSON, CSV, PDF
- ✅ Testes cobrem todas as operações
- ✅ Coverage ≥ 90%

#### Tempo Estimado
- Estrutura blockchain-like: 2h
- Storage com BadgerDB: 2h
- Query engine: 2h
- Export engine: 1h
- Testes: 2h
- Documentação: 0.5h
**Total:** 8h

---

### Day 3: Security Layers Upgrades 🔒
**Status:** ⏳ QUEUED  
**Foco:** Evoluir camadas 2, 6, 7 para Zero Trust completo

#### Objetivos do Dia
- [ ] Upgrade `internal/authz/checker.go` - Context-aware policies
- [ ] Upgrade `internal/ratelimit/limiter.go` - Circuit breakers
- [ ] Upgrade `internal/behavior/analyzer.go` - Anomaly detection
- [ ] Testes de integração entre camadas
- [ ] Security audit das 8 camadas
- [ ] Documentação completa

#### Entregáveis

**Authz (Camada 2):**
```go
// Context-aware authorization
type Policy struct {
    Role       string
    Resource   string
    Action     string
    Conditions []Condition  // ← NEW
}

type Condition struct {
    Type     string      // "time", "ip", "system_state"
    Operator string      // "in", "not_in", "range"
    Value    interface{}
}
```

**RateLimit (Camada 6):**
```go
// Per-risk-level quotas
type Quota struct {
    LOW:      60/min
    MEDIUM:   10/min
    HIGH:     2/min
    CRITICAL: 1/hour
}

// Circuit breaker
type CircuitBreaker struct {
    FailureThreshold   int           // 5 consecutive failures
    PauseDuration      time.Duration // 5 minutes
    AnomalyThreshold   int           // 10 HIGH commands in 1min
}
```

**Behavior (Camada 7):**
```go
// User profile learning
type UserProfile struct {
    UserID            string
    CommonCommands    []string
    TypicalSchedule   map[int]float64  // hour → frequency
    FrequentNamespaces []string
    RiskTolerance     float64
}

// Anomaly detection
func (a *Analyzer) DetectAnomaly(cmd *Command, profile *UserProfile) (bool, AnomalyType)
```

#### Critérios de Sucesso
- ✅ Authz verifica contexto (IP, time, system state)
- ✅ RateLimit diferenciado por risk level
- ✅ Circuit breaker ativa após anomalias
- ✅ Behavior aprende padrões do usuário
- ✅ Anomalias detectadas e escaladas
- ✅ Testes de integração passam
- ✅ Coverage ≥ 90%

#### Tempo Estimado
- Authz upgrade: 2.5h
- RateLimit upgrade: 2h
- Behavior upgrade: 2h
- Integration tests: 1h
- Security audit: 1.5h
- Documentação: 0.5h
**Total:** 8h

---

## 🗓️ FASE 2: Guardian Integration (Dias 4-6)

### Day 4: Guardian Orchestrator 🎭
**Status:** ⏳ QUEUED  
**Foco:** Pipeline que une todas as 8 camadas

#### Objetivos do Dia
- [ ] `internal/guardian/orchestrator.go` - Pipeline completo
- [ ] `internal/guardian/pipeline.go` - Step execution
- [ ] `internal/guardian/context.go` - Execution context
- [ ] `internal/guardian/metrics.go` - Metrics collection
- [ ] Testes end-to-end
- [ ] Documentação

#### Entregáveis
```
internal/guardian/
├── orchestrator.go       # Main orchestrator
├── orchestrator_test.go
├── pipeline.go           # Pipeline execution
├── pipeline_test.go
├── context.go            # Execution context
├── metrics.go            # Prometheus metrics
├── metrics_test.go
└── README.md             # Architecture docs
```

#### Pipeline Flow
```go
func (o *Orchestrator) ProcessCommand(ctx context.Context, input string, user *User) (*Result, error) {
    // CAMADA 1: Authentication
    if err := o.auth.Validate(ctx, user); err != nil {
        return nil, err
    }
    
    // CAMADA 2: Authorization (pre-check)
    if err := o.authz.PreCheck(ctx, user); err != nil {
        return nil, err
    }
    
    // CAMADA 3: Sandbox setup
    sandbox, err := o.sandbox.Create(ctx, user)
    if err != nil {
        return nil, err
    }
    defer sandbox.Cleanup()
    
    // CAMADA 4: NLP Parsing
    parseResult, err := o.parser.Parse(ctx, input)
    if err != nil {
        return nil, err
    }
    
    // CAMADA 2: Authorization (intent-based)
    if err := o.authz.CheckIntent(ctx, user, parseResult.Intent); err != nil {
        return nil, err
    }
    
    // CAMADA 5: Intent Validation
    if err := o.intentValidator.Validate(ctx, parseResult, user); err != nil {
        return nil, err
    }
    
    // CAMADA 6: Rate Limiting
    if err := o.rateLimit.Check(ctx, user, parseResult.Intent.RiskLevel); err != nil {
        return nil, err
    }
    
    // CAMADA 7: Behavior Analysis
    anomaly, err := o.behavior.Analyze(ctx, user, parseResult)
    if err != nil {
        return nil, err
    }
    if anomaly.Detected {
        // Escala segurança se anomalia detectada
        if err := o.handleAnomaly(ctx, user, anomaly); err != nil {
            return nil, err
        }
    }
    
    // Execute command in sandbox
    result, err := sandbox.Execute(ctx, parseResult.Command)
    
    // CAMADA 8: Audit logging
    auditEntry := o.buildAuditEntry(ctx, user, input, parseResult, result, err)
    if auditErr := o.audit.Record(ctx, auditEntry); auditErr != nil {
        // Log audit failure but don't fail command
        log.Error("audit recording failed", auditErr)
    }
    
    return result, err
}
```

#### Critérios de Sucesso
- ✅ Pipeline executa todas as 8 camadas em ordem
- ✅ Falha em qualquer camada aborta execução
- ✅ Métricas coletadas para cada camada
- ✅ Error handling gracioso
- ✅ Testes end-to-end passam
- ✅ Coverage ≥ 90%

#### Tempo Estimado
- Orchestrator core: 3h
- Pipeline execution: 2h
- Error handling: 1h
- Metrics: 1h
- Testes e2e: 2h
- Documentação: 0.5h
**Total:** 8h

---

### Day 5: Shell Integration 🐚
**Status:** ⏳ QUEUED  
**Foco:** Integrar Guardian no shell interativo

#### Objetivos do Dia
- [ ] Modificar `internal/shell/shell.go` para usar Guardian
- [ ] Interactive confirmations com Bubbletea
- [ ] Real-time feedback durante parsing
- [ ] Error messages amigáveis
- [ ] Testes de UX

#### Entregáveis
```
internal/shell/
├── guardian_integration.go   # Guardian integration
├── confirmation_prompt.go    # Interactive confirmations
├── feedback_renderer.go      # Real-time feedback
├── error_formatter.go        # User-friendly errors
└── integration_test.go       # UX tests
```

#### Confirmation UI (Bubbletea)
```
┌─────────────────────────────────────────────────────────┐
│ 🔍 Natural Language: "deleta os pods travados do kafka"│
│                                                         │
│ ⚠️  CONFIRMAÇÃO NECESSÁRIA                             │
│                                                         │
│ Ação: ❌ DELETAR                                       │
│ Comando: kubectl delete pod kafka-0 kafka-1 -n kafka  │
│                                                         │
│ Impacto Estimado:                                      │
│ • 2 pods serão deletados                              │
│ • Namespace: kafka                                     │
│ • Reversível: Sim (pods serão recriados)              │
│ • Risco: MEDIUM                                        │
│                                                         │
│ Confirma execução? [S/n]: _                           │
└─────────────────────────────────────────────────────────┘
```

#### Critérios de Sucesso
- ✅ Guardian integrado no shell
- ✅ Confirmações aparecem para ações destrutivas
- ✅ Feedback em tempo real durante parsing
- ✅ Errors explicam o que deu errado + sugestões
- ✅ UX fluida e não intrusiva
- ✅ Testes simulam interações do usuário

#### Tempo Estimado
- Integration: 2h
- Confirmation UI: 2h
- Feedback renderer: 1h
- Error formatter: 1h
- Testes UX: 2h
- Documentação: 0.5h
**Total:** 8h

---

### Day 6: Security Hardening 🛡️
**Status:** ⏳ QUEUED  
**Foco:** Penetration testing e security audit

#### Objetivos do Dia
- [ ] Fuzzing de inputs maliciosos
- [ ] Boundary testing
- [ ] Privilege escalation attempts
- [ ] Performance profiling
- [ ] Security audit report
- [ ] Mitigations implementadas

#### Test Cases

**1. Command Injection**
```
Input: "list pods; rm -rf /"
Expected: Parser detecta tentativa de injection, bloqueia
```

**2. Path Traversal**
```
Input: "show logs from ../../../etc/passwd"
Expected: Sandbox impede acesso fora do escopo
```

**3. SQL Injection**
```
Input: "delete pod'; DROP TABLE users; --"
Expected: Input sanitization previne
```

**4. Privilege Escalation**
```
Input: "scale deployment to 1000 in production"
User: role=developer (sem permissão production)
Expected: Authz bloqueia
```

**5. DOS Attack**
```
Input: 100 comandos HIGH risk em 10 segundos
Expected: Rate limiter ativa circuit breaker
```

**6. Fuzzing**
```
Generate 10,000 random inputs
Expected: Parser nunca crasha, sempre retorna erro gracioso
```

#### Entregáveis
```
tests/security/
├── fuzzing_test.go
├── injection_test.go
├── boundary_test.go
├── privilege_test.go
├── dos_test.go
└── security_audit_report.md
```

#### Critérios de Sucesso
- ✅ Zero command injections possíveis
- ✅ Sandbox efetivamente isola execução
- ✅ Authz bloqueia privilege escalation
- ✅ Rate limiter previne DOS
- ✅ Parser nunca crasha (error handling robusto)
- ✅ Performance adequada (latência < 100ms p95)
- ✅ Security audit report documentado

#### Tempo Estimado
- Fuzzing tests: 2h
- Injection tests: 1.5h
- Boundary tests: 1h
- Privilege tests: 1h
- Performance profiling: 1.5h
- Audit report: 1.5h
- Mitigations: 1h
**Total:** 8h

---

## 🗓️ FASE 3: Advanced Features (Dias 7-10)

### Day 7: Context Intelligence 🧠
**Status:** ⏳ QUEUED  
**Foco:** Multi-turn conversations e context preservation

#### Objetivos
- [ ] Session context management
- [ ] Pronoun resolution ("delete it", "scale that")
- [ ] Command history influence
- [ ] Context expiry
- [ ] Testes

#### Exemplo de Uso
```
User: "list pods in kafka namespace"
Bot:  [Shows 5 pods]

User: "delete the first one"
Bot:  Resolves "the first one" → kafka-0
      Shows confirmation

User: "scale that deployment to 3"
Bot:  Resolves "that deployment" → last mentioned deployment
      Executes scaling
```

#### Tempo Estimado: 8h

---

### Day 8: Learning & Adaptation 📚
**Status:** ⏳ QUEUED  
**Foco:** User profile learning e personalization

#### Objetivos
- [ ] Command frequency tracking
- [ ] Personal abbreviations
- [ ] Macro commands
- [ ] Profile export/import
- [ ] Testes

#### Exemplo de Uso
```
User (after 100 commands): "kgp"
Bot: Learns that user always means "kubectl get pods"
     Auto-expands without confirmation

User: "save macro 'restart-kafka' as 'delete all kafka pods then scale deployment to 3'"
Bot: Macro saved. Use: "restart-kafka"
```

#### Tempo Estimado: 8h

---

### Day 9: Advanced Confirmations 🎨
**Status:** ⏳ QUEUED  
**Foco:** Impact visualization e staged execution

#### Objetivos
- [ ] Before/after preview
- [ ] Undo/rollback automatic
- [ ] Staged execution (preview → confirm → execute)
- [ ] Batch operation safeguards
- [ ] Testes

#### Impact Visualization
```
┌─────────────────────────────────────────────────────┐
│ PREVIEW: scale deployment kafka-consumer to 5      │
│                                                     │
│ BEFORE:                    AFTER:                  │
│ Replicas: 3          →     Replicas: 5             │
│ Pods: kafka-0,1,2    →     Pods: kafka-0,1,2,3,4   │
│ Memory: 300MB        →     Memory: 500MB (+66%)    │
│                                                     │
│ Rollback: automatic if health check fails          │
│                                                     │
│ Proceed? [Y/n]: _                                  │
└─────────────────────────────────────────────────────┘
```

#### Tempo Estimado: 8h

---

### Day 10: Validation & Documentation 📖
**Status:** ⏳ QUEUED  
**Foco:** Consolidação e preparação para produção

#### Objetivos
- [ ] Full regression test suite
- [ ] Performance benchmarks
- [ ] Documentation completa
- [ ] Tutorial interativo
- [ ] Release notes

#### Deliverables
- Regression tests para todas as features
- Benchmark report (latency, throughput, memory)
- User guide completo
- Developer guide completo
- Tutorial interativo no shell
- Release notes v2.0

#### Tempo Estimado: 8h

---

## 🗓️ FASE 4: Production Readiness (Dias 11-12)

### Day 11: Observability 📊
**Status:** ⏳ QUEUED  
**Foco:** Metrics, dashboards, alerting

#### Objetivos
- [ ] Prometheus metrics para todas as camadas
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Distributed tracing
- [ ] Log aggregation

#### Metrics
```
# Parsing metrics
vcli_nlp_parse_duration_seconds{layer="tokenizer|intent|entities|generator"}
vcli_nlp_parse_errors_total{type="classification|extraction|generation"}
vcli_nlp_confidence_score{percentile="p50|p95|p99"}

# Security metrics
vcli_security_layer_duration_seconds{layer="auth|authz|sandbox|..."}
vcli_security_layer_failures_total{layer="auth|authz|sandbox|..."}
vcli_security_anomalies_detected_total{type="command|time|namespace"}

# Execution metrics
vcli_commands_total{verb="get|delete|scale|...", risk_level="LOW|MEDIUM|HIGH|CRITICAL"}
vcli_commands_confirmed_total{risk_level="..."}
vcli_commands_denied_total{reason="authz|rate_limit|user_cancel"}
```

#### Dashboards
- **Guardian Overview**: Taxa de sucesso, latências, falhas por camada
- **Security Monitoring**: Anomalias, bloqueios, tentativas de abuse
- **User Activity**: Top users, top commands, risk distribution

#### Tempo Estimado: 8h

---

### Day 12: Deploy & Release 🚀
**Status:** ⏳ QUEUED  
**Foco:** Release final

#### Objetivos
- [ ] Release candidate build
- [ ] Final security review
- [ ] Performance validation
- [ ] Documentation review
- [ ] Release v2.0

#### Checklist de Release
- [ ] Todos os testes passam
- [ ] Coverage ≥ 90%
- [ ] Security audit aprovado
- [ ] Performance benchmarks atingidos
- [ ] Documentação completa
- [ ] Release notes escritas
- [ ] Git tag v2.0.0
- [ ] Binários buildados para Linux/Mac/Windows
- [ ] Docker image publicada
- [ ] Announcement preparado

#### Tempo Estimado: 8h

---

## 📈 TRACKING & METRICS

### Daily Progress Template
```markdown
# Day N Progress Report

**Date:** YYYY-MM-DD
**Focus:** [Topic]
**Status:** ✅ COMPLETE | 🔄 IN PROGRESS | ⏳ QUEUED

## Completed
- [ ] Task 1
- [ ] Task 2

## In Progress
- [ ] Task 3 (80% done)

## Blocked
- [ ] Task 4 (waiting for X)

## Metrics
- Lines of code: XXX
- Tests written: XX
- Coverage: XX%
- Bugs found: X
- Bugs fixed: X

## Learnings
- [Key insight from the day]

## Tomorrow
- [ ] Priority 1
- [ ] Priority 2
```

### Weekly Summary Template
```markdown
# Week N Summary

**Dates:** YYYY-MM-DD to YYYY-MM-DD
**Phase:** [Phase name]

## Accomplishments
- Feature 1 complete
- Feature 2 complete

## Metrics
- Total LOC: XXXX
- Total tests: XXX
- Average coverage: XX%
- Bugs squashed: XX

## Challenges
- Challenge 1 and how we solved it

## Next Week
- Goal 1
- Goal 2
```

---

## 🎯 SUCCESS CRITERIA

### Minimum Viable Product (MVP)
- [ ] Todas as 8 camadas implementadas
- [ ] Parser compreende linguagem natural
- [ ] Confirmações funcionam para ações destrutivas
- [ ] Audit log registra toda atividade
- [ ] Testes com coverage ≥ 90%

### Production Ready
- [ ] MVP +
- [ ] Security audit aprovado
- [ ] Performance benchmarks atingidos
- [ ] Documentação completa
- [ ] Observability configurada

### Excellence
- [ ] Production Ready +
- [ ] Context intelligence
- [ ] User learning
- [ ] Advanced confirmations
- [ ] Tutorial interativo

---

## 🚨 RISK MANAGEMENT

### Riscos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Complexity underestimated | MEDIUM | HIGH | Buffer time em cada fase |
| Security vulnerabilities | LOW | CRITICAL | Penetration testing rigoroso |
| Performance bottleneck | LOW | MEDIUM | Profiling contínuo |
| Integration issues | MEDIUM | MEDIUM | Integration tests desde Day 4 |
| Scope creep | MEDIUM | LOW | Strict adherence to roadmap |

### Contingency Plans

**Se atrasarmos:**
- Priorizar MVP sobre features avançadas
- Fase 3 pode ser parcialmente adiada para v2.1
- Fase 4 é obrigatória (não pode ser cortada)

**Se encontrarmos bug crítico:**
- Parar feature work imediatamente
- Fix takes priority
- Re-test affected areas
- Document in lessons learned

---

## 📚 REFERENCES

- Blueprint: `docs/architecture/nlp/guardian-of-intent-blueprint.md`
- Architecture: `docs/architecture/nlp/`
- Security Doutrina: `.claude/DOUTRINA_VERTICE.md`
- NLP Implementation: `internal/nlp/`

---

**Gloria a Deus. Avançamos com fé, não por vista.**

**Status:** ACTIVE | **Última Atualização:** 2025-10-12
